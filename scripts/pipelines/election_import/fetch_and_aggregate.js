// YSK Acik Veri Portali'ndan (getSecimSandikSonucList) TUM il/ilce icin
// sandik-duzeyi veri cekip IL ve ILCE toplamlarina AGREGE eder. Mahalle
// pipeline'inin aksine poligon kisiti yok - Turkiye'deki TUM ~998 ilce
// sorgulanir (data/raw/ysk/acikveri-il-ilce-listesi.json).
//
// Kullanim:
//   node fetch_and_aggregate.js <label> <secimId> <secimTuru> <baslikFile>
//
// Cikti: .work/<label>_agregе.json - {iller: {ilId: {...}}, ilceler: {"ilId-ilceId": {...}}}
// Resumable: .work/<label>_progress.json her 20 ilcede bir yazilir.
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');
const {ballotVotes} = require('./ballot_votes');
const path = require('path');

const LABEL = process.argv[2];
const SECIM_ID = parseInt(process.argv[3]);
const SECIM_TURU = parseInt(process.argv[4]);
const BASLIK_FILE = process.argv[5];

const ROOT = path.join(__dirname, '..', '..', '..');
const IL_ILCE_LIST = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'raw', 'ysk', 'acikveri-il-ilce-listesi.json'), 'utf8'));
const BASLIK = JSON.parse(fs.readFileSync(BASLIK_FILE, 'utf8'));

const WORKDIR = path.join(__dirname, '.work');
fs.mkdirSync(WORKDIR, { recursive: true });
const OUT_FILE = path.join(WORKDIR, `${LABEL}_agrege.json`);
const PROGRESS_FILE = path.join(WORKDIR, `${LABEL}_progress.json`);

// column_NAME -> ad (parti/aday adi), sira_NO'ya gore tekilleştir (bazen
// ayni column_NAME birden fazla "ad" ile listeleniyor - degisiklik/coalition
// gecmisi olabilir, SON gorulen adi kullan).
const colToName = {};
for (const row of BASLIK) colToName[row.column_NAME] = row.ad;
const relevantCols = Object.keys(colToName);

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function emptyAgg() {
  return { secmen: 0, oyKullanan: 0, gecerli: 0, gecersiz: 0, oy: {} };
}
function addRow(agg, row) {
  agg.secmen += row.secmen_SAYISI || 0;
  agg.oyKullanan += row.oy_KULLANAN_SECMEN_SAYISI || 0;
  agg.gecerli += row.gecerli_OY_TOPLAMI || 0;
  agg.gecersiz += row.gecersiz_OY_TOPLAMI || 0;
  for (const [col,v] of Object.entries(ballotVotes(row,relevantCols,SECIM_TURU === 7 || SECIM_TURU === 9))) agg.oy[col] = (agg.oy[col] || 0) + v;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  // hedef ilce listesini duzlestir
  const targets = [];
  for (const [ilId, info] of Object.entries(IL_ILCE_LIST)) {
    for (const ilce of info.ilceler) {
      targets.push({ ilId: parseInt(ilId), ilAdi: info.il_ADI, ilceId: ilce.ilce_ID, ilceAdi: ilce.ilce_ADI });
    }
  }

  let startIdx = 0;
  const ilceAgg = {};
  const ilAgg = {};
  if (fs.existsSync(PROGRESS_FILE)) {
    const prog = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
    if(prog.aggregationVersion !== 2) throw new Error('Eski bağımsız oy hesabıyla üretilmiş progress dosyası: arşivleyip sorguyu baştan çalıştırın.');
    startIdx = prog.nextIdx;
    Object.assign(ilceAgg, prog.ilceAgg);
    Object.assign(ilAgg, prog.ilAgg);
    console.log(`devam ediliyor: ${startIdx}/${targets.length}`);
  }

  let errors = [];
  const t0 = Date.now();

  for (let i = startIdx; i < targets.length; i++) {
    const t = targets[i];
    const key = `${t.ilId}-${t.ilceId}`;
    let attempt = 0;
    let ok = false;
    while (attempt < 4 && !ok) {
      attempt++;
      try {
        const rows = await page.evaluate(async ({ secimId, secimTuru, ilId, ilceId }) => {
          const url = `/api/getSecimSandikSonucList?secimId=${secimId}&secimTuru=${secimTuru}&ilId=${ilId}&ilceId=${ilceId}&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=1&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`;
          const r = await fetch(url, { credentials: 'include' });
          if (r.status !== 200) return { error: 'status ' + r.status };
          return r.json();
        }, { secimId: SECIM_ID, secimTuru: SECIM_TURU, ilId: t.ilId, ilceId: t.ilceId });

        if (rows && rows.error) throw new Error(rows.error);
        if (!Array.isArray(rows)) throw new Error('not array: ' + JSON.stringify(rows).slice(0, 150));

        const agg = emptyAgg();
        for (const row of rows) addRow(agg, row);
        ilceAgg[key] = { ilId: t.ilId, ilAdi: t.ilAdi, ilceId: t.ilceId, ilceAdi: t.ilceAdi, sandikSayisi: rows.length, ...agg };

        if (!ilAgg[t.ilId]) ilAgg[t.ilId] = { ilId: t.ilId, ilAdi: t.ilAdi, ...emptyAgg() };
        addRow(ilAgg[t.ilId], { secmen_SAYISI: agg.secmen, oy_KULLANAN_SECMEN_SAYISI: agg.oyKullanan, gecerli_OY_TOPLAMI: agg.gecerli, gecersiz_OY_TOPLAMI: agg.gecersiz, ...agg.oy });

        ok = true;
      } catch (e) {
        if (attempt >= 4) {
          errors.push({ key, il: t.ilAdi, ilce: t.ilceAdi, error: String(e).slice(0, 200) });
          console.log('FAILED', key, t.ilAdi, t.ilceAdi, String(e).slice(0, 150));
        } else {
          await sleep(500 * attempt);
        }
      }
    }
    if ((i + 1) % 20 === 0 || i === targets.length - 1) {
      const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
      console.log(`[${LABEL}] ${i + 1}/${targets.length} ilce islendi (${errors.length} hata) - ${elapsed}s`);
      fs.writeFileSync(PROGRESS_FILE, JSON.stringify({ aggregationVersion: 2, nextIdx: i + 1, ilceAgg, ilAgg }));
    }
    await sleep(110);
  }

  fs.writeFileSync(OUT_FILE, JSON.stringify({ secimId: SECIM_ID, secimTuru: SECIM_TURU, colToName, iller: ilAgg, ilceler: ilceAgg, errors }, null, 1));
  console.log(`[${LABEL}] TAMAMLANDI. cikti: ${OUT_FILE}, hata sayisi: ${errors.length}`);
  if (errors.length) console.log('HATALAR:', JSON.stringify(errors.slice(0, 10)));

  await browser.close();
})();
