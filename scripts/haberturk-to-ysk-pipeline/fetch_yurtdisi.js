// Yurtdisi (temsilcilik) sandik verisini YSK'nin resmi API'sinden ceker -
// Haberturk'un yerine gecer.
//
// yurtIciDisi=2 + bos filtrelerle sorgulanan "ULKELER SANDIKLAR TOPLAMI"
// hazir-agrege satiri: gecerli_OY_TOPLAMI, oy_KULLANAN_SECMEN_SAYISI ve
// parti/ittifak sutunlari GUVENILIR (mevcut Haberturk rakamlariyla 2018
// icin birebir dogrulandi). BU satirin secmen_SAYISI alani ise YANILTICI -
// gercek kayitli seçmen sayisi degil, oy_KULLANAN_SECMEN_SAYISI ile ayni
// deger (yani bos/anlamsiz doldurulmus). disTemsilcilikId bazinda gercek
// sandik satirlarini tek tek cekip toplayarak dogru secmen sayisini elde
// etmeye calisildi, ama bu sorgu yolu farkli ID'lerde MASSIF (onlarca
// milyon) ve tutarsiz sonuclar verdi - YSK'nin arka ucunda bu spesifik
// filtre kombinasyonu icin bir veri kalitesi sorunu (muhtemelen bir JOIN
// duplikasyonu). Bu yuzden secmen/katilim/sandik alanlari ESKI (Habertürk)
// kaynaginda BIRAKILDI - sadece gecerliOy/kullanilanOy/parti oylari
// (guvenilir agrege satirdan) YSK'ye tasindi. Ayrinti: PROVENANCE.md.
//
// Kullanim: node fetch_yurtdisi.js <cikti.json>
const { chromium } = require('../mahalle-veri-pipeline/node_modules/playwright');
const fs = require('fs');

const ELECTIONS = [
  { key: '2015Haziran', secimId: 13884, secimTuru: 8 },
  { key: '2015Kasim', secimId: 14868, secimTuru: 8 },
  { key: '2018', secimId: 16300, secimTuru: 8 },
  { key: '2023', secimId: 20230, secimTuru: 8 },
  { key: '2017referandum', secimId: 15575, secimTuru: 7 },
  { key: '2018cb', secimId: 16300, secimTuru: 9 },
  { key: '2023cb1tur', secimId: 20230, secimTuru: 9 },
  { key: '2023cb2tur', secimId: 20240, secimTuru: 9 },
];

async function fetchAggregate(page, secimId, secimTuru) {
  return page.evaluate(async ({ secimId, secimTuru }) => {
    const url = `/api/getSecimSandikSonucList?secimId=${secimId}&secimTuru=${secimTuru}&ilId=&ilceId=&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=2&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`;
    const r = await fetch(url, { credentials: 'include' });
    if (r.status !== 200) return null;
    return r.json();
  }, { secimId, secimTuru });
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  const out = {};
  for (const el of ELECTIONS) {
    const rows = await fetchAggregate(page, el.secimId, el.secimTuru);
    const ulkeler = Array.isArray(rows) ? rows.find(r => r.il_ADI === 'ÜLKELER SANDIKLAR TOPLAMI') : null;
    const gumrukAgg = Array.isArray(rows) ? rows.find(r => r.il_ADI === 'GÜMRÜK KAPILARI SANDIKLAR TOPLAMI') : null;
    if (!ulkeler || !ulkeler.secmen_SAYISI) {
      console.log(`[${el.key}] agrege satir bos/yok - ATLANDI (eski kaynakta kalacak).`);
      out[el.key] = null;
      continue;
    }
    console.log(`[${el.key}] gecerli=${ulkeler.gecerli_OY_TOPLAMI} kullanan=${ulkeler.oy_KULLANAN_SECMEN_SAYISI}`);
    out[el.key] = { ulkeler, gumrukAgg };
  }

  fs.writeFileSync(process.argv[2], JSON.stringify(out, null, 1));
  console.log('yazildi:', process.argv[2]);
  await browser.close();
})();
