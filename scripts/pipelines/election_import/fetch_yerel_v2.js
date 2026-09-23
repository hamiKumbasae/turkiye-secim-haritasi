// YEREL secimler icin DOGRU model: "il" kaydi = (a) buyuksehir statusundeki
// iller icin secimTuru=6 (Buyuksehir Belediye Baskanligi) ilceId=BLANK
// sorgusu (39 ilce-kirilimli satiri TOPLANARAK) - bos donerse buyuksehir
// DEGIL demektir; (b) buyuksehir OLMAYAN iller icin secimTuru=2, sadece
// "<Il> MERKEZ" ilcesinin kendi sorgusu (butun ilceleri TOPLAMAK YANLIS -
// her ilcenin kendi ayri yarisi var, 1950-1977/1994-2004 pipeline'larindaki
// "il kaydi = merkezin kendi yarisi" kuraliyla AYNI).
//
// "ilceler": HER il icin, o ile ait TUM ilcelerin kendi secimTuru=2 (yerel/
// ilce duzeyi) sonucu - buyuksehir olsun olmasin, ilceler kendi ayri
// yarislarini temsil ediyor, il kaydiyla CAKISMIYOR (il kaydi ayri bir
// sorgudan geliyor).
//
// Kullanim: node fetch_yerel_v2.js <label> <secimId> <baslikFile>
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const LABEL = process.argv[2];
const SECIM_ID = parseInt(process.argv[3]);
const BASLIK_FILE = process.argv[4];
const SECIM_TURU_ILCE = 2;
const SECIM_TURU_BUYUKSEHIR = 6;

const ROOT = path.join(__dirname, '..', '..');
const IL_ILCE_LIST = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'raw', 'ysk', 'acikveri-il-ilce-listesi.json'), 'utf8'));
const BASLIK = JSON.parse(fs.readFileSync(BASLIK_FILE, 'utf8'));

const WORKDIR = path.join(__dirname, '.work');
fs.mkdirSync(WORKDIR, { recursive: true });
const OUT_FILE = path.join(WORKDIR, `${LABEL}_v2_agrege.json`);
const PROGRESS_FILE = path.join(WORKDIR, `${LABEL}_v2_progress.json`);

const colToName = {};
for (const row of BASLIK) colToName[row.column_NAME] = row.ad;
const relevantCols = Object.keys(colToName);

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function emptyAgg() { return { secmen: 0, oyKullanan: 0, gecerli: 0, gecersiz: 0, oy: {} }; }
function addRow(agg, row) {
  agg.secmen += row.secmen_SAYISI || 0;
  agg.oyKullanan += row.oy_KULLANAN_SECMEN_SAYISI || 0;
  agg.gecerli += row.gecerli_OY_TOPLAMI || 0;
  agg.gecersiz += row.gecersiz_OY_TOPLAMI || 0;
  for (const col of relevantCols) {
    const v = row[col];
    if (v) agg.oy[col] = (agg.oy[col] || 0) + v;
  }
}

async function queryList(page, secimTuru, ilId, ilceId) {
  return page.evaluate(async ({ secimId, secimTuru, ilId, ilceId }) => {
    const url = `/api/getSecimSandikSonucList?secimId=${secimId}&secimTuru=${secimTuru}&ilId=${ilId}&ilceId=${ilceId}&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=1&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`;
    const r = await fetch(url, { credentials: 'include' });
    if (r.status !== 200) return { error: 'status ' + r.status };
    return r.json();
  }, { secimId: SECIM_ID, secimTuru, ilId, ilceId: ilceId || '' });
}

async function withRetry(fn, label) {
  let attempt = 0;
  while (attempt < 4) {
    attempt++;
    try {
      const rows = await fn();
      if (rows && rows.error) throw new Error(rows.error);
      if (!Array.isArray(rows)) throw new Error('not array: ' + JSON.stringify(rows).slice(0, 150));
      return rows;
    } catch (e) {
      if (attempt >= 4) { console.log('FAILED', label, String(e).slice(0, 150)); return null; }
      await sleep(500 * attempt);
    }
  }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  const ilList = Object.entries(IL_ILCE_LIST).map(([ilId, info]) => ({ ilId: parseInt(ilId), ilAdi: info.il_ADI, ilceler: info.ilceler }));

  let startIdx = 0;
  const ilResults = {};
  const ilceResults = {};
  if (fs.existsSync(PROGRESS_FILE)) {
    const prog = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
    startIdx = prog.nextIdx;
    Object.assign(ilResults, prog.ilResults);
    Object.assign(ilceResults, prog.ilceResults);
    console.log(`devam ediliyor: il ${startIdx}/${ilList.length}`);
  }

  const t0 = Date.now();
  for (let i = startIdx; i < ilList.length; i++) {
    const il = ilList[i];

    // 1) buyuksehir denemesi
    const bsRows = await withRetry(() => queryList(page, SECIM_TURU_BUYUKSEHIR, il.ilId, ''), `${il.ilAdi} buyuksehir`);
    let ilAgg, kind;
    if (bsRows && bsRows.length > 0) {
      ilAgg = emptyAgg();
      let sandik = 0;
      for (const row of bsRows) { addRow(ilAgg, row); sandik += 1; }
      ilAgg.sandikSayisi = bsRows.length;
      kind = 'buyuksehir';
    } else {
      // 2) buyuksehir degil - "<Il> MERKEZ" ilcesini bul
      const merkez = il.ilceler.find(x => x.ilce_ADI === `${il.ilAdi} MERKEZ` || x.ilce_ADI === 'MERKEZ')
        || il.ilceler.find(x => x.ilce_ADI.endsWith('MERKEZ'));
      if (!merkez) {
        console.log('UYARI: Merkez ilce bulunamadi:', il.ilAdi, il.ilceler.map(x => x.ilce_ADI));
        ilAgg = emptyAgg();
        ilAgg.sandikSayisi = 0;
        kind = 'merkez_bulunamadi';
      } else {
        const mRows = await withRetry(() => queryList(page, SECIM_TURU_ILCE, il.ilId, merkez.ilce_ID), `${il.ilAdi} merkez`);
        ilAgg = emptyAgg();
        for (const row of (mRows || [])) addRow(ilAgg, row);
        ilAgg.sandikSayisi = (mRows || []).length;
        kind = 'merkez:' + merkez.ilce_ADI;
      }
    }
    ilAgg.ilAdi = il.ilAdi;
    ilAgg.kind = kind;
    ilResults[il.ilId] = ilAgg;

    // 3) ilceler: HER ilce icin kendi secimTuru=2 sonucu
    for (const ilce of il.ilceler) {
      const key = `${il.ilId}-${ilce.ilce_ID}`;
      const rows = await withRetry(() => queryList(page, SECIM_TURU_ILCE, il.ilId, ilce.ilce_ID), key);
      const agg = emptyAgg();
      for (const row of (rows || [])) addRow(agg, row);
      agg.sandikSayisi = (rows || []).length;
      agg.ilAdi = il.ilAdi;
      agg.ilceAdi = ilce.ilce_ADI;
      agg.ilId = il.ilId;
      agg.ilceId = ilce.ilce_ID;
      ilceResults[key] = agg;
      await sleep(90);
    }

    const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
    console.log(`[${LABEL}] il ${i + 1}/${ilList.length} (${il.ilAdi}, ${kind}) - ${elapsed}s`);
    fs.writeFileSync(PROGRESS_FILE, JSON.stringify({ nextIdx: i + 1, ilResults, ilceResults }));
  }

  fs.writeFileSync(OUT_FILE, JSON.stringify({ secimId: SECIM_ID, colToName, iller: ilResults, ilceler: ilceResults }, null, 1));
  console.log(`[${LABEL}] TAMAMLANDI: ${OUT_FILE}`);

  await browser.close();
})();
