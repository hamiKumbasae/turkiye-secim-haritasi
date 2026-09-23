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

    // Il -> ilce tiklamasi il'in DEGIL, tiklanan ilcenin KENDI verisini
    // gostermeli (bkz. regresyon: bir donem ilce tiklamasi eski/il-genel
    // veriyi degistirmeden birakiyordu).
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);
    const provinceSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
    await page.click('path.il-path[data-geom-id="TR-D-34-001"]'); // Adalar
    await page.waitForTimeout(400);
    const dName = await page.$eval('#dName', (el) => el.textContent);
    const districtSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
    check('2023 genel: ilçe tıklaması kendi adını gösteriyor', dName === 'Adalar', dName);
    check('2023 genel: ilçe tıklaması il-geneli değil kendi seçmen sayısını gösteriyor',
      districtSecmen !== provinceSecmen, 'il=' + provinceSecmen + ' ilçe=' + districtSecmen);
  });
  check('2023 genel: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_istanbul1994geometri(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    const found = await clickYear(page, '1994');
    check('1994 yerel: yıl seçilebildi', found);
    await page.waitForTimeout(500);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);
    // 2008 sonrasi kurulan ilceler (Ataşehir, Sancaktepe vb.) 1994'te veri
    // satırı olarak yok - haritada "delik" birakmak yerine notr/tiklanamaz
    // gosterilmeli (bkz. son inceleme: İstanbul'un değişen ilçe sınırları).
    const nodataCount = await page.$$eval('.il-path-nodata', (els) => els.length);
    check('1994 yerel İstanbul: veri olmayan ilçeler nötr/tıklanamaz gösteriliyor (harita deliksiz)', nodataCount > 0, 'count=' + nodataCount);
    const nodataCursor = nodataCount > 0
      ? await page.$eval('.il-path-nodata', (el) => getComputedStyle(el).cursor)
      : null;
    check('1994 yerel İstanbul: veri olmayan ilçe tıklanabilir görünmüyor (cursor=default)', nodataCursor === 'default', 'cursor=' + nodataCursor);

    // Buyukcekmece (Beylikduzu'nun eski, tek-ebeveynli hali) ve Umraniye
    // (Cekmekoy'un eski hali) icin gercek tarihsel birlesim poligonu var
    // (bkz. scripts/haberturk-to-ysk-pipeline/apply_verified_district_merges.py) -
    // hem sentetik HIST- poligon render edilmeli HEM DE ust uste binen eski
    // modern (kucuk) sekilleri AYRICA "veri yok" olarak cizilmemeli.
    const histIds = await page.$$eval('path.il-path[data-geom-id]', (els) =>
      els.map((e) => e.dataset.geomId).filter((id) => id.startsWith('HIST-')));
    const expectedHist = ['HIST-Istanbul-Buyukcekmece', 'HIST-Istanbul-Umraniye',
      'HIST-Istanbul-Kadikoy', 'HIST-Istanbul-Uskudar', 'HIST-Istanbul-Kartal'];
    check('1994 yerel İstanbul: tarihsel birleşim poligonlarının tümü çiziliyor (Büyükçekmece/Ümraniye/Kadıköy/Üsküdar/Kartal)',
      expectedHist.every((id) => histIds.includes(id)), JSON.stringify(histIds));
    // Ataşehir (TR-D-34-003) 4 ebeveyne (Kadıköy/Üsküdar/Ümraniye/Kartal) TAM
    // dağıtıldığı için (16/16 mahalle, kalıntı yok) artık ayrıca "veri yok"
    // gösterilmemeli - bkz. geo/historical/district_mahalle_merges.yaml.
    const staleDuplicates = await page.$$eval(
      ['TR-D-34-014', 'TR-D-34-037', 'TR-D-34-012', 'TR-D-34-016',
        'TR-D-34-003', 'TR-D-34-023', 'TR-D-34-038', 'TR-D-34-025']
        .map((id) => `path.il-path[data-geom-id="${id}"]`).join(', '),
      (els) => els.length);
    check('1994 yerel İstanbul: birleşimin parçası olan eski modern şekiller ayrıca (üst üste) çizilmiyor', staleDuplicates === 0, 'count=' + staleDuplicates);
  });
  check('1994 yerel İstanbul geometrisi: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// Bir secimde HIC ilce-duzeyi veri yoksa (orn. 1965 genel - sadece il
// duzeyinde kaynak var), "ilce gorunumu"ne HIC GECILMEMELI - ne 39 parcaya
// bolup "veri yok" katmani cizmek, ne de zoom yapip tek-parca-il gosterip
// sahte bir "İlçe Sonuçları" alt seviyesi sunmak. Harita ULKE goruminde
// KALMALI, sag panel sadece ilin kendi sonucunu gostermeli ve "İlçeler"
// basligi/arama/liste bolumu hic gorunmemeli (bkz. son inceleme: bir onceki
// turda "tek parca" fallback dogruydu ama cevresindeki UI hala sahte bir
// ilce-seviyesi gorunumu gibi davraniyordu).
async function scenario_ilOnlyYearsTekParca(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurGenel');
    await page.waitForTimeout(400);
    const found1965 = await clickYear(page, '1965');
    check('1965 genel: yıl seçilebildi', found1965);
    await page.waitForTimeout(400);
    await page.fill('#searchBox', 'İstanbul');
    await page.waitForTimeout(300);
    let nodata = await page.$$eval('.il-path-nodata', (els) => els.length);
    let countryPaths = await page.$$eval('path.il-path[data-plaka]', (els) => els.length);
    let breadcrumbHidden = await page.$eval('#mapBreadcrumb', (el) => getComputedStyle(el).display === 'none');
    let dName = await page.$eval('#dName', (el) => el.textContent);
    let selectedPlaka = await page.$eval('path.il-path.selected', (el) => el.dataset.plaka).catch(() => null);
    check('1965 genel (hiç ilçe verisi yok): "ilçe" alt katmanı/parçalaması yok', nodata === 0, 'nodata=' + nodata);
    check('1965 genel (hiç ilçe verisi yok): harita ülke görünümünde kaldı (tek ile zoom yapmadı)', countryPaths > 1, 'countryPaths=' + countryPaths);
    check('1965 genel (hiç ilçe verisi yok): "İlçe Sonuçları" breadcrumb\'ı hiç açılmadı', breadcrumbHidden);
    check('1965 genel (hiç ilçe verisi yok): sağ panelde il doğru seçili', dName === 'İstanbul' && selectedPlaka === '34', 'dName=' + dName + ' selectedPlaka=' + selectedPlaka);

    const districtsHidden = await page.$eval('#dDistrictsLabel', (el) => getComputedStyle(el).display === 'none')
      && await page.$eval('#districtSearch', (el) => getComputedStyle(el).display === 'none')
      && await page.$eval('#dDistrictList', (el) => getComputedStyle(el).display === 'none');
    check('1965 genel (hiç ilçe verisi yok): "İlçeler" başlığı/arama/listesi hiç gösterilmiyor', districtsHidden);

    // Katilim/Parti moduna gecince de (bkz. onceki bug: bos entity listesi
    // yuzunden "Infinity%" gibi bozuk bir legend olusuyordu) hata olmamali -
    // artik province-view'a hic girilmedigi icin bu sorun tasarim geregi yok.
    await page.click('#modeGroup button[data-mode="katilim"]').catch(() => {});
    await page.waitForTimeout(200);
    const seqMinText = await page.$eval('#seqMin', (el) => el.textContent);
    check('1965 genel (hiç ilçe verisi yok): Katılım moduna geçince legend bozulmuyor (Infinity/NaN yok)', !/Infinity|NaN/.test(seqMinText), seqMinText);
    await page.click('#modeGroup button[data-mode="winner"]').catch(() => {});

    await page.click('#btnTurYerel');
    await page.waitForTimeout(400);
    const found1977 = await clickYear(page, '1977');
    check('1977 yerel: yıl seçilebildi', found1977);
    await page.waitForTimeout(400);
    await page.fill('#searchBox', 'İstanbul');
    await page.waitForTimeout(300);
    nodata = await page.$$eval('.il-path-nodata', (els) => els.length);
    countryPaths = await page.$$eval('path.il-path[data-plaka]', (els) => els.length);
    breadcrumbHidden = await page.$eval('#mapBreadcrumb', (el) => getComputedStyle(el).display === 'none');
    dName = await page.$eval('#dName', (el) => el.textContent);
    check('1977 yerel (hiç ilçe verisi yok): "ilçe" alt katmanı/parçalaması yok, ülke görünümünde kaldı, breadcrumb açılmadı',
      nodata === 0 && countryPaths > 1 && breadcrumbHidden && dName === 'İstanbul',
      'nodata=' + nodata + ' countryPaths=' + countryPaths + ' breadcrumbHidden=' + breadcrumbHidden + ' dName=' + dName);
  });
  check('il-only yıllar: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
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
    await scenario_istanbul1994geometri(browser);
    await scenario_ilOnlyYearsTekParca(browser);
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
