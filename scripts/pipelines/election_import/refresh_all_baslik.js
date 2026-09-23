// TUM 15 secim icin TAZE (canli) parti/aday sutun listesini ceker, eski
// (bazilari eksik cikan) parti-sutun-eslemeleri/baslik_*.json dosyalarinin
// UZERINE yazar. Hangi dosyalarin satir sayisi DEGISTI (yani eskiden eksikti)
// raporlanir.
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const BASLIK_DIR = path.join(__dirname, '..', 'mahalle_veri', 'parti-sutun-eslemeleri');

const TARGETS = [
  ['2011', 7468, 8], ['2015Haziran', 13884, 8], ['2015Kasim', 14868, 8], ['2018', 16300, 8], ['genel_2023', 20230, 8],
  ['2009yerel', 4290, 2], ['2014yerel', 11979, 2], ['2019yerel', 16400, 2], ['yerel_2024', 20260, 2],
  ['2014cb', 13340, 9], ['2018cb', 16300, 9], ['2023cb1tur', 20230, 9], ['2023cb2tur', 20240, 9],
  ['2010referandum', 6522, 7], ['2017referandum', 15575, 7],
];

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  for (const [label, secimId, secimTuru] of TARGETS) {
    const filePath = path.join(BASLIK_DIR, `baslik_${label}.json`);
    let oldCount = 0;
    if (fs.existsSync(filePath)) {
      try { oldCount = JSON.parse(fs.readFileSync(filePath, 'utf8')).length; } catch (e) {}
    }
    const data = await page.evaluate(async ({ secimId, secimTuru }) => {
      const r = await fetch(`/api/getSandikSecimSonucBaslikList?secimId=${secimId}&secimTuru=${secimTuru}`, { credentials: 'include' });
      return r.json();
    }, { secimId, secimTuru });
    fs.writeFileSync(filePath, JSON.stringify(data, null, 1));
    const changed = data.length !== oldCount;
    console.log(`${label}: eski=${oldCount} yeni=${data.length}${changed ? '  <<< DEGISTI' : ''}`);
    await sleep(200);
  }

  await browser.close();
})();
