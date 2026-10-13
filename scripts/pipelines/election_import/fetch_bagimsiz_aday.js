// Verilen ilcelerde bagimsiz adaylarin oylarini ADAY ADAY toplar (fetch_yerel_v2.js bagimsizlari
// tek toplamda birlestirir). Bir ilcede bagimsizlarin TOPLAMI en cok oyu almis gorunuyorsa kazananin
// tek bir bagimsiz aday olup olmadigini anlamak icin kullanilir (diger_ayristir_ysk.py).
// Ilce sorgusunda bagimsizN_ALDIGI_OY sutunlari o ilcenin oy pusulasindaki bagimsiz siralarina karsilik
// gelir. Ayrica ilce baslik listesi (aday adlari) denenir ve oldugu gibi saklanir.
//
// Kullanim: node fetch_bagimsiz_aday.js <sorgu.json> <cikti.json>
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');

const SORGU = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const CIKTI = process.argv[3];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);
  const sonuc = [];
  for (const s of SORGU) {
    const r = await page.evaluate(async ({ secimId, ilId, ilceId }) => {
      const q = `secimId=${secimId}&secimTuru=2&ilId=${ilId}&ilceId=${ilceId}`;
      const satirlar = await (await fetch(`/api/getSecimSandikSonucList?${q}&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=1&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`, { credentials: 'include' })).json();
      let baslik = null;
      try {
        const b = await fetch(`/api/getSandikSecimSonucBaslikList?${q}`, { credentials: 'include' });
        baslik = b.status === 200 ? await b.json() : 'status ' + b.status;
      } catch (e) { baslik = String(e); }
      return { satirlar, baslik };
    }, s);
    const bagimsiz = {};
    let toplam = 0, gecerli = 0;
    const partiler = {};
    for (const row of r.satirlar) {
      gecerli += row.gecerli_OY_TOPLAMI || 0;
      toplam += row.bagimsiz_TOPLAM_OY || 0;
      for (const [k, v] of Object.entries(row)) {
        if (/^bagimsiz\d+_ALDIGI_OY$/.test(k) && v) bagimsiz[k] = (bagimsiz[k] || 0) + v;
        if (/^(parti|ittifak)\d+_ALDIGI_OY$/.test(k) && v) partiler[k] = (partiler[k] || 0) + v;
      }
    }
    sonuc.push({ ...s, sandik: r.satirlar.length, gecerli, bagimsizToplam: toplam, bagimsiz, partiler, baslik: r.baslik });
    console.log(s.secim, s.ad, JSON.stringify(bagimsiz), 'toplam', toplam);
  }
  fs.writeFileSync(CIKTI, JSON.stringify(sonuc, null, 1));
  await browser.close();
})();
