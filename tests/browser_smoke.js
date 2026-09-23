// index.html'i gercek bir tarayicida (Chromium/Playwright) acip birkac temel
// akisin JS hatasiz calistigini ve dogru veriyi gosterdigini dogrular.
// scripts/validate.py / tests/validate_elections.py'nin (Python, veri/yapi
// dogrulamasi) TERSINE - burada ON YUZ (DOM/JS) dogrulanir. build.py'ye
// gomulu DEGIL, ayri/CI'da calistirilir.
//
// Kullanim:
//   cd tests && npm install && npx playwright install --with-deps chromium
//   node browser_smoke.js

const path = require('path');
const { chromium } = require('playwright');

const INDEX_HTML = 'file://' + path.resolve(__dirname, '..', 'index.html');

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok, detail });
  console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (!ok && detail ? '  (' + detail + ')' : ''));
}

async function withPage(browser, fn) {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message));
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push('CONSOLE: ' + msg.text()); });
  await page.goto(INDEX_HTML);
  await page.waitForTimeout(1000);
  await fn(page, errors);
  await page.close();
  return errors;
}

async function clickYear(page, label) {
  const items = await page.$$('.year-item');
  for (const item of items) {
    const t = (await item.textContent()).trim();
    if (t === label) { await item.click(); return true; }
  }
  return false;
}

async function scenario_2023genel(browser) {
  const errors = await withPage(browser, async (page) => {
    const title = await page.$eval('#pageTitle', (el) => el.textContent);
    const activeYear = await page.$eval('.year-item.active', (el) => el.textContent.trim());
    const nsCount = await page.$$eval('.ns-item', (els) => els.length);
    check('2023 genel: varsayılan yıl 2023', activeYear === '2023', 'active=' + activeYear);
    check('2023 genel: başlıkta "2023" geçiyor', title.includes('2023'), title);
    check('2023 genel: ulusal özet dolu (>=4 kalem)', nsCount >= 4, 'count=' + nsCount);
  });
  check('2023 genel: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_1950yerel(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    const found = await clickYear(page, '1950');
    check('1950 yerel: yıl seçilebildi', found);
    await page.waitForTimeout(500);
    const path1 = await page.$('path.il-path[data-plaka]');
    if (path1) await path1.click();
    await page.waitForTimeout(400);
    const noteVisible = await page.$eval('#dInfoNote', (el) => getComputedStyle(el).display !== 'none');
    check('1950 yerel: dolaylı-seçim bilgi notu görünüyor', noteVisible);
    const partiHidden = await page.$eval('#modeGroup button[data-mode="parti"]', (el) => el.hidden);
    check('1950 yerel: Parti harita modu gizli', partiHidden);
  });
  check('1950 yerel: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_1955yerel(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    const found = await clickYear(page, '1955');
    check('1955 yerel: yıl seçilebildi', found);
    await page.waitForTimeout(500);
    // Adana: 1955'te gerçek oy verisi olan (heroSeatBased=false) bir il -
    // dolaylı-seçim notu, seat-based olmayan illerde de görünmeli (bkz. son inceleme).
    await page.fill('#searchBox', 'Adana');
    await page.waitForTimeout(400);
    const noteVisible = await page.$eval('#dInfoNote', (el) => getComputedStyle(el).display !== 'none');
    check('1955 yerel: gerçek-oy-verili ilde de bilgi notu görünüyor (contestType regresyonu yok)', noteVisible);
    const heroLabel = await page.$eval('#dHeroLabel', (el) => el.textContent);
    check('1955 yerel: hero etiketi "Kazanan" değil', heroLabel !== 'Kazanan', heroLabel);
  });
  check('1955 yerel: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_2024meclis(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    const found = await clickYear(page, '2024');
    check('2024 yerel: yıl seçilebildi', found);
    await page.waitForTimeout(500);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);
    const toggleVisible = await page.$eval('#detailViewToggle', (el) => getComputedStyle(el).display !== 'none');
    check('2024 yerel: İstanbul için İlçe Meclisi sekmesi görünüyor', toggleVisible);
    if (toggleVisible) {
      await page.click('#detailViewToggle button[data-view="meclis"]');
      await page.waitForTimeout(400);
      const rowCount = await page.$$eval('.district-row', (els) => els.length);
      check('2024 yerel: ilçe meclisi listesi dolu', rowCount > 0, 'rows=' + rowCount);
      const row = await page.$('.district-row');
      if (row) await row.click();
      await page.waitForTimeout(400);
      const qtyTexts = await page.$$eval('#dParties .party-row .oy', (els) => els.map((e) => e.textContent));
      const allSeats = qtyTexts.length > 0 && qtyTexts.every((t) => t.includes('meclis sandalyesi'));
      check('2024 yerel: meclis üye sayıları "oy" değil "meclis sandalyesi" gösteriyor', allSeats, JSON.stringify(qtyTexts));
    }
  });
  check('2024 yerel meclis: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_referandum(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurReferandum');
    await page.waitForTimeout(500);
    const activeYear = await page.$eval('.year-item.active', (el) => el.textContent.trim());
    check('referandum: bir yıl otomatik seçili', !!activeYear, activeYear);
    const path1 = await page.$('path.il-path[data-plaka]');
    if (path1) await path1.click();
    await page.waitForTimeout(400);
    const heroName = await page.$eval('#dHeroName', (el) => el.textContent);
    check('referandum: il seçilince sonuç (Evet/Hayır) gösteriliyor', heroName === 'Evet' || heroName === 'Hayır', heroName);
    await page.click('#btnTableView');
    await page.waitForTimeout(400);
    const tableRows = await page.$$eval('#ilTableBody tr', (els) => els.length);
    check('referandum: tablo görünümü dolu', tableRows > 0, 'rows=' + tableRows);
  });
  check('referandum akışı: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function main() {
  const browser = await chromium.launch();
  try {
    await scenario_2023genel(browser);
    await scenario_1950yerel(browser);
    await scenario_1955yerel(browser);
    await scenario_2024meclis(browser);
    await scenario_referandum(browser);
  } finally {
    await browser.close();
  }

  const failed = results.filter((r) => !r.ok);
  console.log('');
  if (failed.length) {
    console.log(failed.length + '/' + results.length + ' kontrol BAŞARISIZ: ' + failed.map((r) => r.name).join(', '));
    process.exit(1);
  }
  console.log('Tüm kontroller geçti (' + results.length + '/' + results.length + ').');
}

main();
