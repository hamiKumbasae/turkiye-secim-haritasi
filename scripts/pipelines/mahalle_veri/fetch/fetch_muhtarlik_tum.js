// YSK acik veri: verilen illerin her ilcesi icin sandik sonuclarini ceker ve MUHTARLIK duzeyinde toplar.
// fetch_muhtarlik_parti.js'den farki: BUTUN parti/ittifak sutunlari ayri tutulur (Diğer'e toplanmaz),
// bagimsizlar ballot_votes.js ile tek bagimsiz0 sutununda; muhtarligi olmayan sandiklar (muhtarlik_ID 0:
// cezaevi, gumruk vb.) ilce basina "_muhtarliksiz" altinda sayilir; hicbir sandik atilmaz.
//
// Kullanim: node fetch_muhtarlik_tum.js <etiket> <secimId> <secimTuru> <baslik.json> <plaka,plaka,...> <cikti.json>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { ballotVotes } = require('../../election_import/ballot_votes');

const [LABEL, SECIM_ID, SECIM_TURU, BASLIK_FILE, PLAKALAR, OUT_FILE] = process.argv.slice(2);
const ROOT = path.join(__dirname, '..', '..', '..', '..');
const IL_ILCE = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'raw', 'ysk', 'acikveri-il-ilce-listesi.json'), 'utf8'));
const BASLIK = JSON.parse(fs.readFileSync(BASLIK_FILE, 'utf8'));
const colToName = {};
for (const r of BASLIK) colToName[r.column_NAME] = r.ad;
const cols = Object.keys(colToName);
const plakalar = new Set(PLAKALAR.split(',').map(Number));
const bireysel = Number(SECIM_TURU) === 7 || Number(SECIM_TURU) === 9;
const sleep = ms => new Promise(r => setTimeout(r, ms));

function bos() { return { secmen: 0, oyKullanan: 0, gecerli: 0, gecersiz: 0, sandik: 0, oy: {} }; }
function ekle(a, row) {
  a.secmen += row.secmen_SAYISI || 0;
  a.oyKullanan += row.oy_KULLANAN_SECMEN_SAYISI || 0;
  a.gecerli += row.gecerli_OY_TOPLAMI || 0;
  a.gecersiz += row.gecersiz_OY_TOPLAMI || 0;
  a.sandik += 1;
  for (const [c, v] of Object.entries(ballotVotes(row, cols, bireysel))) a.oy[c] = (a.oy[c] || 0) + v;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);
  const out = { etiket: LABEL, secimId: Number(SECIM_ID), secimTuru: Number(SECIM_TURU), colToName, ilceler: {}, hatalar: [] };
  const hedef = [];
  for (const [ilId, info] of Object.entries(IL_ILCE)) {
    if (!plakalar.has(Number(ilId))) continue;
    for (const ilce of info.ilceler) hedef.push({ ilId: Number(ilId), ilAdi: info.il_ADI, ilceId: ilce.ilce_ID, ilceAdi: ilce.ilce_ADI });
  }
  const t0 = Date.now();
  for (let i = 0; i < hedef.length; i++) {
    const t = hedef[i];
    let rows = null;
    for (let deneme = 1; deneme <= 4 && !rows; deneme++) {
      try {
        const r = await page.evaluate(async ({ s, tur, il, ilce }) => {
          const u = `/api/getSecimSandikSonucList?secimId=${s}&secimTuru=${tur}&ilId=${il}&ilceId=${ilce}&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=1&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`;
          const x = await fetch(u, { credentials: 'include' });
          if (x.status !== 200) return { error: 'status ' + x.status };
          return x.json();
        }, { s: SECIM_ID, tur: SECIM_TURU, il: t.ilId, ilce: t.ilceId });
        if (!Array.isArray(r)) throw new Error(JSON.stringify(r).slice(0, 150));
        rows = r;
      } catch (e) {
        if (deneme === 4) out.hatalar.push({ ...t, hata: String(e).slice(0, 200) });
        else await sleep(800 * deneme);
      }
    }
    if (rows) {
      const m = {};
      for (const row of rows) {
        const mid = row.muhtarlik_ID ? String(row.muhtarlik_ID) : '_muhtarliksiz';
        if (!m[mid]) m[mid] = { ad: row.muhtarlik_ADI || null, ...bos() };
        ekle(m[mid], row);
      }
      out.ilceler[`${t.ilId}-${t.ilceId}`] = { ilId: t.ilId, ilAdi: t.ilAdi, ilceId: t.ilceId, ilceAdi: t.ilceAdi, sandik: rows.length, muhtarliklar: m };
    }
    if ((i + 1) % 25 === 0) console.log(`[${LABEL}] ${i + 1}/${hedef.length} ilce, ${out.hatalar.length} hata, ${((Date.now() - t0) / 1000).toFixed(0)} sn`);
    await sleep(120);
  }
  fs.writeFileSync(OUT_FILE, JSON.stringify(out));
  console.log(`[${LABEL}] BITTI: ${Object.keys(out.ilceler).length} ilce, ${out.hatalar.length} hata`);
  await browser.close();
})();
