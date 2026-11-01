// YSK Acik Veri Portali'ndaki secim listesini (getSecimDetayList) yazar ve verilen metne uyan
// secimleri (ornek: 2009 yenileme) secer. Portal yalniz GitHub Actions'tan acilir.
//
// Kullanim: node secim_listesi.js <cikti.json> [desen]
//   cikti.json: {liste: <ham yanit>, eslesen: [{secimId, ...}]}
//   desen (RegExp, buyuk/kucuk harf duyarsiz): eslesen secimlerin herhangi bir alaninda aranir.
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');

const [OUT, DESEN] = process.argv.slice(2);
const re = DESEN ? new RegExp(DESEN, 'i') : null;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 90000 });
  const api = (u) => page.evaluate(async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    const t = await r.text();
    try { return { status: r.status, json: JSON.parse(t) }; } catch (e) { return { status: r.status, text: t.slice(0, 500) }; }
  }, u);
  const denenen = ['/api/getSecimDetayList', '/api/getSecimList', '/api/getSecimTuruList'];
  const sonuc = {};
  for (const u of denenen) {
    sonuc[u] = await api(u);
    const j = sonuc[u].json;
    console.log(u, sonuc[u].status, Array.isArray(j) ? `${j.length} satir` : JSON.stringify(sonuc[u]).slice(0, 200));
  }
  const satirlar = [];
  const gez = (x) => {
    if (Array.isArray(x)) x.forEach(gez);
    else if (x && typeof x === 'object') {
      if (Object.keys(x).some((k) => /secim.?id/i.test(k))) satirlar.push(x);
      Object.values(x).forEach((v) => (typeof v === 'object' ? gez(v) : null));
    }
  };
  Object.values(sonuc).forEach((s) => gez(s.json));
  const eslesen = re ? satirlar.filter((s) => re.test(JSON.stringify(s))) : satirlar;
  for (const s of eslesen.slice(0, 40)) console.log('ESLESEN', JSON.stringify(s));
  fs.writeFileSync(OUT, JSON.stringify({ cekildi: new Date().toISOString(), liste: sonuc, eslesen }, null, 1));
  await browser.close();
})();
