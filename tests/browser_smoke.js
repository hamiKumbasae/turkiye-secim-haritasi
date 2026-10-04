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

const IST_1991 = Object.values(require('../geo/historical/idari/istanbul_1961_1992.json').secimler['1991'].satirlar).map((r) => r.geomId).filter((id) => id.startsWith('HIST-'));

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

// 1992-2008 (3806 ile 5747 arasi) Istanbul'un 32 ilcesi: bugunku ilcelerden bosluksuz kurulan
// poligonlar (scripts/pipelines/historical_geo/build_istanbul_1992_2008.py)
const IST_9208 = ['Buyukcekmece', 'Catalca', 'Esenler', 'Eyup', 'Gaziosmanpasa', 'Kadikoy', 'Kartal',
  'Kucukcekmece', 'Umraniye', 'Uskudar'].map((ad) => 'HIST-Istanbul-' + ad + '-9208');

async function scenario_istanbul1994geometri(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    const found = await clickYear(page, '1994');
    check('1994 yerel: yıl seçilebildi', found);
    await page.waitForTimeout(500);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);
    // 2008 sonrasi kurulan ilceler (Ataşehir, Sancaktepe, Arnavutköy ...) 1994'te yoktu; alanlari
    // 1992-2008 ilcelerine paylastirildigi icin "veri yok" poligonu kalmamali.
    const nodataIds = await page.$$eval('.il-path-nodata', (els) => els.map((e) => e.dataset.geomId));
    check('1994 yerel İstanbul: "veri yok" ilçe kalmadı (2008 ilçeleri 1994 sınırlarına paylaştırıldı)',
      nodataIds.length === 0, JSON.stringify(nodataIds));

    // Buyukcekmece (Beylikduzu'nun eski, tek-ebeveynli hali) ve Umraniye
    // (Cekmekoy'un eski hali) icin gercek tarihsel birlesim poligonu var
    // (bkz. scripts/pipelines/election_import/apply_verified_district_merges.py) -
    // hem sentetik HIST- poligon render edilmeli HEM DE ust uste binen eski
    // modern (kucuk) sekilleri AYRICA "veri yok" olarak cizilmemeli.
    const histIds = await page.$$eval('path.il-path[data-geom-id]', (els) =>
      els.map((e) => e.dataset.geomId)
        // apply_idari_merges: HIST-* birlesimi sonradan eklenen parcalarla HISTK-<HIST-id>-* olabilir
        .map((id) => id.replace(/^HISTK-(HIST-.+)-[0-9a-f]{6}$/, '$1')).filter((id) => id.startsWith('HIST-')));
    const expectedHist = IST_9208;
    check('1994 yerel İstanbul: 1992-2008 sınırlı ilçe poligonlarının tümü çiziliyor',
      expectedHist.every((id) => histIds.includes(id)), JSON.stringify(histIds));
    // Ataşehir (TR-D-34-003) 4 ebeveyne (Kadıköy/Üsküdar/Ümraniye/Kartal) TAM
    // dağıtıldığı için (16/16 mahalle, kalıntı yok) artık ayrıca "veri yok"
    // gösterilmemeli - bkz. geo/historical/district_mahalle_merges.yaml.
    const staleDuplicates = await page.$$eval(
      ['TR-D-34-014', 'TR-D-34-037', 'TR-D-34-012', 'TR-D-34-016',
        'TR-D-34-003', 'TR-D-34-023', 'TR-D-34-038', 'TR-D-34-025',
        'TR-D-34-002', 'TR-D-34-008', 'TR-D-34-018', 'TR-D-34-033', 'TR-D-34-021', 'TR-D-34-015']
        .map((id) => `path.il-path[data-geom-id="${id}"]`).join(', '),
      (els) => els.length);
    check('1994 yerel İstanbul: birleşimin parçası olan eski modern şekiller ayrıca (üst üste) çizilmiyor', staleDuplicates === 0, 'count=' + staleDuplicates);

    // Tarihsel (HIST-*) bir ilçeye tıklamak, o ilçenin KENDİ (genişletilmiş)
    // gerçek oy verisini göstermeli - sentetik geomId'ye geçiş sadece haritayı
    // etkilemeli, panel/veri akışını bozmamalı.
    await page.click('path.il-path[data-geom-id="HIST-Istanbul-Kadikoy-9208"]');
    await page.waitForTimeout(400);
    const histDName = await page.$eval('#dName', (el) => el.textContent);
    const histDSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
    check('1994 yerel: tarihsel Kadıköy poligonuna tıklama doğru ilçeyi ve gerçek veriyi gösteriyor',
      histDName === 'Kadıköy' && histDSecmen !== '—' && histDSecmen !== '',
      'dName=' + histDName + ' dSecmen=' + histDSecmen);
  });
  check('1994 yerel İstanbul geometrisi: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// 1994 disinda 1999/2004 yerel de (5747'nin split_year'i 2008 oldugu icin)
// AYNI 5 tarihsel birlesimi kullanmali - sadece 1994'u test edip digerlerini
// varsaymak riskli (bkz. son inceleme: "tıklanan tarihsel ilçe doğru 1994/
// 1999/2004 verisini göstermeli").
async function scenario_istanbul19992004Gecmisi(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    const expectedHist = IST_9208;
    for (const year of ['1999', '2004']) {
      const found = await clickYear(page, year);
      check(year + ' yerel: yıl seçilebildi', found);
      await page.waitForTimeout(400);
      await page.click('path[data-plaka="34"]');
      await page.waitForTimeout(400);
      const histIds = await page.$$eval('path.il-path[data-geom-id]', (els) =>
        els.map((e) => e.dataset.geomId)
        // apply_idari_merges: HIST-* birlesimi sonradan eklenen parcalarla HISTK-<HIST-id>-* olabilir
        .map((id) => id.replace(/^HISTK-(HIST-.+)-[0-9a-f]{6}$/, '$1')).filter((id) => id.startsWith('HIST-')));
      check(year + ' yerel İstanbul: tarihsel birleşim poligonlarının tümü çiziliyor',
        expectedHist.every((id) => histIds.includes(id)), JSON.stringify(histIds));
      await page.click('#btnBackCountry').catch(() => {});
    }
  });
  check('1999/2004 yerel İstanbul geometrisi: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// Ataşehir/Beylikdüzü/Çekmeköy icin dogrulanmis tarihsel geometri onceki
// oturumda SADECE 1994/1999/2004 yerel'e baglanmisti - genel secimlerde
// (1991, 1995-2007, Istanbul'un ilce-duzeyinde veri icerdigi TEK genel
// secim yillari) ayni 5 eski-ilce satiri hala kendi modern (yanlis, kucuk)
// geomId'sine düşüyordu, boylece bu 5 ilce o secimlerde de "veri yok" gibi
// görünüyordu - bkz. audit_district_coverage tarzi denetim. Duzeltme sadece
// affected_years listesini genisletti (apply_verified_district_merges.py +
// district_mahalle_merges.yaml), yeni geometri URETMEDI.
// Sancaktepe (2008'de Umraniye+Kartal'dan kuruldu) daha once TAMAMEN "veri
// yok" gorunuyordu - kanunun (21) sayili listesindeki isim cakismalari/
// eksik isimler yuzunden script hicbir zaman islemiyordu. 19 mahallenin
// 18'i (Hilal/Sarigazi/Yenidogan icin yapisal+cografi cikarim, Pasakoy icin
// GEOMETRIK cakisma testinin ortaya cikardigi duzeltme) artik cozuldu -
// bkz. district_mahalle_merges.yaml'daki "verified_full_coverage_inferred"
// girisi. Bu test hem Sancaktepe'nin artik "veri yok" OLMADIGINI hem de
// komsu HIST-Umraniye/HIST-Kartal poligonlarinin UST USTE BINMEDIGINI
// (validate_elections.py'nin yakaladigi bir regresyonun bir daha
// olmayacagini) tarayicida da dogruluyor.
// 3806 sayili Kanun (1992) ile Bakirkoy'den Bagcilar/Bahcelievler/Gungoren,
// Kartal'dan Maltepe/Sultanbeyli, Kucukcekmece'den Avcilar, Pendik'ten
// Tuzla ayrildi - 2008 dalgasindan TAMAMEN FARKLI/DAHA ESKI bir donem, resmi
// kaymakamlik tarihce sayfalariyla dogrulandi (bkz. apply_verified_district_merges.py
// yorumu). Bu test 1991 genel'de bu 7 ilcenin artik "veri yok" OLMADIGINI,
// sadece hala gercekten arastirilmamis/bloke olanlarin (Arnavutkoy/Basaksehir/
// Esenler/Esenyurt/Sultangazi) kaldigini dogruluyor.
// Izmir: ayni 3806 sayili Kanun (Istanbul ile) Cigli/Gaziemir/Balcova/
// Narlidere/Guzelbahce'yi (1992, Konak+Karsiyaka'dan), 5747 sayili Kanun
// Bayrakli/Karabaglar'i (2008), ayrica Beydag/Buca/Menderes'i (1987-88,
// ayri kucuk kanunlar) kurdu - resmi kaymakamlik tarihce sayfalariyla
// dogrulandi (bkz. apply_verified_district_merges.py). Konak UC farkli
// donem sentetigine sahip (Kartal'daki AYNI desen): bu test hem 1991
// genel'de (Konak1991/Karsiyaka1991 kullanilmali) hem 1995'te (kucuk
// Konak/Karsiyaka, Buca/Menderes/Beydag/Cigli/Gaziemir/Balcova/Guzelbahce
// artik kendi gercek satirlariyla var oldugu icin) dogru sentetiklerin
// secildigini kontrol ediyor.
async function scenario_izmirDalgalariCozumu(browser) {
  const errors = await withPage(browser, async (page) => {
    for (const [year, expectedHist] of [
      ['1991', ['HIST-Izmir-Konak1991', 'HIST-Izmir-Karsiyaka1991']],
      ['1995', ['HIST-Izmir-Konak', 'HIST-Izmir-Karsiyaka']],
    ]) {
      const found = await clickYear(page, year);
      check(year + ' genel: yıl seçilebildi (İzmir testi)', found);
      await page.waitForTimeout(400);
      // ulke goruniminde Izmir/Manisa pikselde cok yakin/ust uste - normal
      // koordinat-tabanli tiklama Manisa'yi "intercept" edebiliyor (bu test/
      // gecerli veriyle ilgisiz, kucuk haritanin genel bir ozelligi) - DOM
      // click() ile dogrudan tetikleyip piksel-hit-testini atliyoruz.
      await page.$eval('path[data-plaka="35"]', (el) => el.dispatchEvent(new MouseEvent('click', { bubbles: true })));
      await page.waitForTimeout(400);
      const histIds = await page.$$eval('path.il-path[data-geom-id]', (els) =>
        els.map((e) => e.dataset.geomId)
        // apply_idari_merges: HIST-* birlesimi sonradan eklenen parcalarla HISTK-<HIST-id>-* olabilir
        .map((id) => id.replace(/^HISTK-(HIST-.+)-[0-9a-f]{6}$/, '$1')).filter((id) => id.startsWith('HIST-')));
      check(year + ' genel İzmir: doğru sentetik poligonlar çiziliyor',
        expectedHist.every((id) => histIds.includes(id)) && !histIds.some((id) => id.startsWith('HIST-Izmir') && !expectedHist.includes(id)),
        JSON.stringify(histIds));

      await page.$eval(`path.il-path[data-geom-id="${expectedHist[0]}"]`,
        (el) => el.dispatchEvent(new MouseEvent('click', { bubbles: true })));
      await page.waitForTimeout(300);
      const dName = await page.$eval('#dName', (el) => el.textContent);
      const dSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
      check(year + ' genel: ' + expectedHist[0] + ' tıklanınca gerçek veri gösteriyor',
        dName === 'Konak' && dSecmen !== '—' && dSecmen !== '', 'dName=' + dName + ' dSecmen=' + dSecmen);

      await page.click('#btnBackCountry').catch(() => {});
    }
  });
  check('İzmir dalgaları çözümü: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_1992DalgasiCozumu(browser) {
  const errors = await withPage(browser, async (page) => {
    const found = await clickYear(page, '1991');
    check('1991 genel: yıl seçilebildi (1992 dalgası testi)', found);
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);

    const nodataIds = await page.$$eval('.il-path-nodata', (els) => els.map((e) => e.dataset.geomId));
    check('1991 genel İstanbul: tarihî bölüşüm sonrası veri yok poligonu kalmadı',
      nodataIds.length === 0, JSON.stringify(nodataIds));

    for (const [histId, adi] of [['HIST-Istanbul-Bakirkoy', 'Bakırköy'], ['HIST-Istanbul-Kucukcekmece', 'Küçükçekmece'], ['HIST-Istanbul-Pendik', 'Pendik']]) {
      await page.click(`path.il-path[data-geom-id^="${histId}-"]`);
      await page.waitForTimeout(300);
      const dName = await page.$eval('#dName', (el) => el.textContent);
      const dSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
      check(`1991 genel: ${histId} tıklanınca gerçek veri gösteriyor`,
        dName === adi && dSecmen !== '—' && dSecmen !== '', 'dName=' + dName + ' dSecmen=' + dSecmen);
    }
  });
  check('1992 dalgası çözümü: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_sancaktepeCozumu(browser) {
  const errors = await withPage(browser, async (page) => {
    const found = await clickYear(page, '1995');
    check('1995 genel: yıl seçilebildi (Sancaktepe testi)', found);
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);

    const nodataIds = await page.$$eval('.il-path-nodata', (els) => els.map((e) => e.dataset.geomId));
    check('1995 genel İstanbul: Sancaktepe (TR-D-34-029) artık "veri yok" değil',
      !nodataIds.includes('TR-D-34-029'), JSON.stringify(nodataIds));
    check('1995 genel İstanbul: "veri yok" ilçe kalmadı (Arnavutköy/Başakşehir/Esenyurt/Sultangazi dahil)',
      nodataIds.length === 0, JSON.stringify(nodataIds));

    await page.click('path.il-path[data-geom-id="HIST-Istanbul-Umraniye-9208"]');
    await page.waitForTimeout(400);
    const dName = await page.$eval('#dName', (el) => el.textContent);
    const dSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
    check('1995 genel: HIST-Istanbul-Umraniye-9208 (Sancaktepe\'nin bir kısmını içerir) tıklanınca gerçek veri gösteriyor',
      dName === 'Ümraniye' && dSecmen !== '—' && dSecmen !== '', 'dName=' + dName + ' dSecmen=' + dSecmen);
  });
  check('Sancaktepe çözümü: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function scenario_istanbulGenelGecmisi(browser) {
  const errors = await withPage(browser, async (page) => {
    const baseHist = ['HIST-Istanbul-Buyukcekmece', 'HIST-Istanbul-Umraniye',
      'HIST-Istanbul-Kadikoy', 'HIST-Istanbul-Uskudar'];
    // 1991'de Kartal'ın sentetiği Maltepe/Sultanbeyli'yi de içeren "Kartal1991"
    // (apply_verified_district_merges.py); 1995-2007'de 1992-2008 sınırları (IST_9208).
    for (const year of ['1991', '1995', '1999', '2002', '2007']) {
      // 1995-2007: 1992-2008 sinirlari (IST_9208); 1991: onceki birlesimler
      const expectedHist = year === '1991' ? IST_1991 : IST_9208;
      const found = await clickYear(page, year);
      check(year + ' genel: yıl seçilebildi', found);
      await page.waitForTimeout(400);
      await page.click('path[data-plaka="34"]');
      await page.waitForTimeout(400);
      const histIds = await page.$$eval('path.il-path[data-geom-id]', (els) =>
        els.map((e) => e.dataset.geomId)
        // apply_idari_merges: HIST-* birlesimi sonradan eklenen parcalarla HISTK-<HIST-id>-* olabilir
        .map((id) => id.replace(/^HISTK-(HIST-.+)-[0-9a-f]{6}$/, '$1')).filter((id) => id.startsWith('HIST-')));
      check(year + ' genel İstanbul: tarihsel birleşim poligonlarının tümü çiziliyor',
        expectedHist.every((id) => histIds.includes(id)), JSON.stringify(histIds));
      if (year !== '1991') {
        const nodataIds = await page.$$eval('.il-path-nodata', (els) => els.map((e) => e.dataset.geomId));
        check(year + ' genel İstanbul: "veri yok" ilçe kalmadı', nodataIds.length === 0, JSON.stringify(nodataIds));
      }

      await page.click(year === '1991'
        ? 'path.il-path[data-geom-id^="HIST-Istanbul-Buyukcekmece-"]'
        : 'path.il-path[data-geom-id="HIST-Istanbul-Buyukcekmece-9208"]');
      await page.waitForTimeout(400);
      const dName = await page.$eval('#dName', (el) => el.textContent);
      const dSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
      check(year + ' genel: tarihsel Büyükçekmece poligonuna tıklama doğru ilçeyi ve gerçek veriyi gösteriyor',
        dName === 'Büyükçekmece' && dSecmen !== '—' && dSecmen !== '',
        'dName=' + dName + ' dSecmen=' + dSecmen);

      await page.click('#btnBackCountry').catch(() => {});
    }
  });
  check('1991/1995-2007 genel İstanbul geometrisi: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// Bir secimde HIC ilce-duzeyi veri yoksa (orn. 1957 genel - sadece il
// duzeyinde kaynak var; 1961-1987 artik TUIK ilce verisiyle geliyor), "ilce gorunumu"ne HIC GECILMEMELI - ne 39 parcaya
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
    const found1957 = await clickYear(page, '1957');
    check('1957 genel: yıl seçilebildi', found1957);
    await page.waitForTimeout(400);
    await page.fill('#searchBox', 'İstanbul');
    await page.waitForTimeout(300);
    let nodata = await page.$$eval('.il-path-nodata', (els) => els.length);
    let countryPaths = await page.$$eval('path.il-path[data-plaka]', (els) => els.length);
    let breadcrumbHidden = await page.$eval('#mapBreadcrumb', (el) => getComputedStyle(el).display === 'none');
    let dName = await page.$eval('#dName', (el) => el.textContent);
    let selectedPlaka = await page.$eval('path.il-path.selected', (el) => el.dataset.plaka).catch(() => null);
    check('1957 genel (hiç ilçe verisi yok): "ilçe" alt katmanı/parçalaması yok', nodata === 0, 'nodata=' + nodata);
    check('1957 genel (hiç ilçe verisi yok): harita ülke görünümünde kaldı (tek ile zoom yapmadı)', countryPaths > 1, 'countryPaths=' + countryPaths);
    check('1957 genel (hiç ilçe verisi yok): "İlçe Sonuçları" breadcrumb\'ı hiç açılmadı', breadcrumbHidden);
    check('1957 genel (hiç ilçe verisi yok): sağ panelde il doğru seçili', dName === 'İstanbul' && selectedPlaka === '34', 'dName=' + dName + ' selectedPlaka=' + selectedPlaka);

    const districtsHidden = await page.$eval('#dDistrictsLabel', (el) => getComputedStyle(el).display === 'none')
      && await page.$eval('#districtSearch', (el) => getComputedStyle(el).display === 'none')
      && await page.$eval('#dDistrictList', (el) => getComputedStyle(el).display === 'none');
    check('1957 genel (hiç ilçe verisi yok): "İlçeler" başlığı/arama/listesi hiç gösterilmiyor', districtsHidden);

    // Katilim/Parti moduna gecince de (bkz. onceki bug: bos entity listesi
    // yuzunden "Infinity%" gibi bozuk bir legend olusuyordu) hata olmamali -
    // artik province-view'a hic girilmedigi icin bu sorun tasarim geregi yok.
    await page.click('#modeGroup button[data-mode="katilim"]').catch(() => {});
    await page.waitForTimeout(200);
    const seqMinText = await page.$eval('#seqMin', (el) => el.textContent);
    check('1957 genel (hiç ilçe verisi yok): Katılım moduna geçince legend bozulmuyor (Infinity/NaN yok)', !/Infinity|NaN/.test(seqMinText), seqMinText);
    await page.click('#modeGroup button[data-mode="winner"]').catch(() => {});

    // 1977 yerel ve 1961-1988 referandumlari artik ilce duzeyinde (2026-09-24) -
    // hala il-only olan bir secim: 1954 genel.
    await page.click('#btnTurGenel');
    await page.waitForTimeout(400);
    const found1954 = await clickYear(page, '1954');
    check('1954 genel: yıl seçilebildi', found1954);
    await page.waitForTimeout(400);
    await page.fill('#searchBox', 'İstanbul');
    await page.waitForTimeout(300);
    nodata = await page.$$eval('.il-path-nodata', (els) => els.length);
    countryPaths = await page.$$eval('path.il-path[data-plaka]', (els) => els.length);
    breadcrumbHidden = await page.$eval('#mapBreadcrumb', (el) => getComputedStyle(el).display === 'none');
    dName = await page.$eval('#dName', (el) => el.textContent);
    check('1954 genel (hiç ilçe verisi yok): "ilçe" alt katmanı/parçalaması yok, ülke görünümünde kaldı, breadcrumb açılmadı',
      nodata === 0 && countryPaths > 1 && breadcrumbHidden && dName === 'İstanbul',
      'nodata=' + nodata + ' countryPaths=' + countryPaths + ' breadcrumbHidden=' + breadcrumbHidden + ' dName=' + dName);
  });
  check('il-only yıllar: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// 1950-1977 yerel secimleri (2026-09-24, ikinci oturum): ilce belediye
// baskanliklari Wikipedia il sayfalarinin "İlçeler" bolumlerinden. 1963-1977
// aday/oy bazli; 1950/1955 yalnizca kazanan parti (oy yok) - bu satirlar
// haritada kazanan rengiyle boyanmali ve oy alani "—" gostermeli.
async function scenario_yerelIlce1950_1977(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(400);
    check('1968 yerel: yıl seçilebildi', await clickYear(page, '1968'));
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="1"]');
    await page.waitForTimeout(500);
    const ids = await page.$$eval('path.il-path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1968 yerel Adana: ilçe haritası çiziliyor', ids.length > 5, 'n=' + ids.length);
    const ceyhan = await page.$$eval('path.il-path[data-geom-id]', (els) => {
      const e = els.find((x) => x.dataset.geomId === 'TR-D-01-002'); return e ? e.getAttribute('fill') : null; });
    check('1968 yerel Adana: Ceyhan boyalı (veri var)', !!ceyhan && !/map-empty/.test(ceyhan), String(ceyhan));
    if (ceyhan) {
      await page.click('path.il-path[data-geom-id="TR-D-01-002"]');
      await page.waitForTimeout(400);
      const dName = await page.$eval('#dName', (el) => el.textContent);
      const body = await page.$eval('#detailPanel', (el) => el.textContent).catch(() => '');
      check('1968 yerel Ceyhan: tıklanınca kendi oyları (CHP 6.173)', dName === 'Ceyhan' && /6\.173/.test(body), 'dName=' + dName);
    }
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);

    check('1950 yerel: yıl seçilebildi', await clickYear(page, '1950'));
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="1"]');
    await page.waitForTimeout(500);
    const ids50 = await page.$$eval('path.il-path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1950 yerel Adana: sadece-kazanan ilçeler haritada çiziliyor', ids50.length > 3, 'n=' + ids50.length);
    const labels = await page.$$eval('#legend, #seqMin, #seqMax', (els) => els.map((e) => e.textContent).join(' ')).catch(() => '');
    check('1950 yerel: legend bozulmuyor (Infinity/NaN yok)', !/Infinity|NaN/.test(labels), labels.slice(0, 120));
  });
  check('1950-1977 yerel ilçe: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// 1961-1988 referandumlari (2026-09-24): ilce duzeyi TUIK "Halk Oylaması
// Sonuçları" (2008). Evet/Hayır ilce haritasi cizilmeli, Konya 1982'de Merkez
// tarihsel poligonla.
async function scenario_referandumIlce(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurReferandum');
    await page.waitForTimeout(400);
    for (const [y, plaka, hist] of [['1961', '1', 'HIST-Adana-Merkez'], ['1982', '42', 'HIST-Konya-Merkez'], ['1988', '34', null]]) {
      check(y + ' referandum: yıl seçilebildi', await clickYear(page, y));
      await page.waitForTimeout(400);
      await page.click('path[data-plaka="' + plaka + '"]');
      await page.waitForTimeout(500);
      const ids = await page.$$eval('path.il-path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
      check(y + ' referandum: ilçe haritası çiziliyor (' + plaka + ')', ids.length > 3, 'n=' + ids.length);
      if (hist) check(y + ' referandum: ' + hist + ' çiziliyor',
        ids.some((i) => i === hist || i.startsWith('HISTK-' + hist + '-')), JSON.stringify(ids.slice(0, 8)));
      await page.click('#btnBackCountry').catch(() => {});
      await page.waitForTimeout(300);
    }
  });
  check('1961-1988 referandum ilçe: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// 1961-1987 genel secimleri (2026-09-24): TUIK'ten gelen ilce duzeyi.
// Buyuksehir "Merkez"leri sentetik HIST-<Il>-Merkez poligonlariyla (bolunme
// kanununun halefleri) ciziliyor ve o haleflerin modern poligonlari ayrica
// "veri yok" olarak cizilmiyor; Ankara Merkez (guvenilir siniri yok) listede
// var ama haritada yok; Istanbul'da Eminonu/Fatih ayri tarihsel poligonlar.
async function scenario_1961_1987Ilce(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurGenel');
    await page.waitForTimeout(400);
    for (const [year, plaka, hist, hidden] of [
      ['1965', '42', 'HIST-Konya-Merkez', ['TR-D-42-022', 'TR-D-42-024', 'TR-D-42-026']],
      ['1977', '1', 'HIST-Adana-Merkez', ['TR-D-01-012', 'TR-D-01-015']],
      ['1987', '16', 'HIST-Bursa-Merkez', ['TR-D-16-012', 'TR-D-16-015', 'TR-D-16-017']],
    ]) {
      const found = await clickYear(page, year);
      check(year + ' genel: yıl seçilebildi', found);
      await page.waitForTimeout(400);
      await page.click('path[data-plaka="' + plaka + '"]');
      await page.waitForTimeout(500);
      const ids = await page.$$eval('path.il-path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
      check(year + ' genel: ilçe haritası çiziliyor (' + plaka + ')', ids.length > 3, 'n=' + ids.length);
      // apply_idari_merges.py: sonradan kurulan ilceler (orn. 1990'da Gursu/Kestel)
      // o donemde Merkez'e bagliysa poligon HISTK-<hist>-* birlesimi olur.
      const histId = ids.find((i) => i === hist || i.startsWith('HISTK-' + hist + '-'));
      check(year + ' genel: ' + hist + ' çiziliyor', !!histId, JSON.stringify(ids));
      const nodata = await page.$$eval('.il-path-nodata', (els) => els.map((e) => e.dataset.geomId));
      check(year + ' genel: Merkez halefleri ayrıca "veri yok" olarak çizilmiyor',
        hidden.every((h) => !nodata.includes(h) && !ids.includes(h)), JSON.stringify(nodata));
      await page.click('path.il-path[data-geom-id="' + histId + '"]');
      await page.waitForTimeout(400);
      const dName = await page.$eval('#dName', (el) => el.textContent);
      const dSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
      check(year + ' genel: ' + hist + ' tıklanınca Merkez\'in gerçek verisi', dName === 'Merkez' && dSecmen !== '—' && dSecmen !== '',
        'dName=' + dName + ' dSecmen=' + dSecmen);
      await page.click('#btnBackCountry').catch(() => {});
      await page.waitForTimeout(300);
    }

    await clickYear(page, '1973');
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(500);
    const ist = await page.$$eval('path.il-path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1973 genel İstanbul: Eminönü ve Fatih ayrı tarihsel poligonlarla, modern Fatih çizilmeden',
      ist.includes('HIST-Istanbul-Eminonu') && ist.includes('HIST-Istanbul-Fatih') && !ist.includes('TR-D-34-020'), JSON.stringify(ist));
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    // Koprubasi 20.05.1990'da (3644) Surmene'den ayrildi: 1973'te Surmene satiri
    // Surmene+Koprubasi birlesimine (HISTK-61-014-*) boyanir, Koprubasi ayrica cizilmez.
    await page.click('path[data-plaka="61"]');
    await page.waitForTimeout(500);
    const trb = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1973 genel Trabzon: Sürmene, Köprübaşı ile birleşik (HISTK) çiziliyor',
      trb.some((i) => i.startsWith('HISTK-61-014-')) && !trb.includes('TR-D-61-010') && !trb.includes('TR-D-61-014'), JSON.stringify(trb));
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    // 1995'te Arnavutkoy ayri ilce degildi; alani Gaziosmanpasa ve Catalca arasinda mahalle
    // duzeyinde paylastirildi (build_istanbul_1992_2008.py): bugunku Arnavutkoy cizilmez,
    // Gaziosmanpasa'nin ipucu bugunku ilcelerden aldigi paylari yazar
    await clickYear(page, '1995');
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(500);
    const ist95 = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1995 genel İstanbul: Arnavutköy ayrıca çizilmiyor, Gaziosmanpaşa ve Çatalca 1992-2008 sınırlarıyla',
      !ist95.includes('TR-D-34-002') && ist95.includes('HIST-Istanbul-Gaziosmanpasa-9208') && ist95.includes('HIST-Istanbul-Catalca-9208'),
      JSON.stringify(ist95));
    const gopTip = await page.$eval('path[data-geom-id="HIST-Istanbul-Gaziosmanpasa-9208"]', (el) => {
      const r = el.getBoundingClientRect();
      el.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2}));
      return document.querySelector('#tooltip').textContent;
    });
    check('1995 genel İstanbul: Gaziosmanpaşa ipucu bugünkü Arnavutköy ve Sultangazi paylarını yazıyor',
      /Arnavutköy \(%\d+\)/.test(gopTip) && /Sultangazi \(%\d+\)/.test(gopTip), gopTip);
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    // Merkez cogunlugu: Konyaalti (12 birim Merkez, 1 Kemer) ve Aksu 2008 oncesi Antalya Merkez'e
    // butunuyle katilir; ipucu bugunku ilceleri ve kucuk diger kaynagi yazar
    await page.$eval('path[data-plaka="7"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(500);
    const ant = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    const antMerkez = ant.find((i) => i.startsWith('HISTK-HIST-Antalya-Merkez-'));
    check('1995 genel Antalya: Merkez; Konyaaltı ve Aksu ile birleşik, ayrıca "veri yok" çizilmiyor',
      !!antMerkez && !ant.includes('TR-D-07-014') && !ant.includes('TR-D-07-002'), JSON.stringify(ant));
    const antTip = await page.$eval('path[data-geom-id="' + antMerkez + '"]', (el) => {
      const r = el.getBoundingClientRect();
      el.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2}));
      return document.querySelector('#tooltip').textContent;
    }).catch((e) => 'yok: ' + e);
    check('1995 genel Antalya: Merkez ipucu bugünkü ilçeleri ve Konyaaltı\'nın Kemer köyünü yazıyor',
      /Bugünkü sınırlarla/.test(antTip) && /Konyaaltı/.test(antTip) && /Kemer/.test(antTip), antTip);
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    // Buyukcekmece 1987'de Catalca'dan kuruldu (3392, tek kaynak): 1987 oncesi Catalca poligonu
    await clickYear(page, '1983');
    await page.waitForTimeout(400);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(500);
    const ist83 = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1983 genel İstanbul: Çatalca, Büyükçekmece ile birleşik (HISTK) çiziliyor',
      ist83.some((i) => i.startsWith('HISTK-34-015-')) && !ist83.includes('TR-D-34-014') && !ist83.includes('TR-D-34-012'), JSON.stringify(ist83));
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    await page.click('path[data-plaka="6"]');
    await page.waitForTimeout(500);
    const districtNames = await page.$$eval('#dDistrictList *', (els) => els.map((e) => e.textContent));
    check('1973 genel Ankara: Merkez (haritasız) ilçe listesinde yine de var',
      districtNames.some((t) => /Merkez/.test(t)), JSON.stringify(districtNames.slice(0, 5)));
    // 1991-2007 ilce duzeyi TUIK'e yukseltildi (2026-09-24): Eminonu artik ayri satir
    for (const y of ['1995', '2007']) {
      await page.click('#btnBackCountry').catch(() => {});
      await page.waitForTimeout(300);
      await clickYear(page, y);
      await page.waitForTimeout(400);
      await page.click('path[data-plaka="34"]');
      await page.waitForTimeout(500);
      const ids = await page.$$eval('path.il-path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
      check(y + ' genel İstanbul (TÜİK): Eminönü ve Fatih ayrı, modern Fatih çizilmeden',
        ids.includes('HIST-Istanbul-Eminonu') && ids.includes('HIST-Istanbul-Fatih') && !ids.includes('TR-D-34-020'), JSON.stringify(ids.slice(0, 8)));
    }
  });
  check('1961-1987 genel ilçe: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// Eski yerel secimlerde il merkezi belediyesinin sonucu (il satiri) merkez ilcenin o donemki
// sinirlariyla cizilir (ekle_il_merkezi_satirlari.py); buyuksehir yillarinda uretilmez.
async function scenario_yerelIlMerkezi(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(400);
    check('1977 yerel: yıl seçilebildi', await clickYear(page, '1977'));
    await page.waitForTimeout(500);
    await page.$eval('path[data-plaka="1"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(600);
    const ada = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1977 yerel Adana: Merkez (il merkezi belediyesi) poligonu çiziliyor',
      ada.some((i) => i.startsWith('HISTK-HIST-Adana-Merkez-') || i === 'HIST-Adana-Merkez') && !ada.includes('TR-D-01-012'), JSON.stringify(ada));
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    await page.$eval('path[data-plaka="6"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(600);
    const ank = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1977 yerel Ankara: şehir (Altındağ/Çankaya/Yenimahalle) tek il merkezi poligonu',
      ank.some((i) => i.includes('HISTY-06-1977yerel')) && !ank.includes('TR-D-06-007'), JSON.stringify(ank));
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    check('1989 yerel: yıl seçilebildi', await clickYear(page, '1989'));
    await page.waitForTimeout(500);
    await page.$eval('path[data-plaka="35"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(600);
    const izm = await page.$$eval('path[data-geom-id]', (els) => els.map((e) => e.dataset.geomId));
    check('1989 yerel İzmir (büyükşehir): Konak kendi satırıyla, ek Merkez yok',
      izm.some((i) => i.includes('Konak1991')) && !izm.some((i) => i.includes('Konak84')), JSON.stringify(izm));
  });
  check('yerel il merkezi: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// 1994-2004 yerel: ilce rengi ilce belediye baskaninin partisi (YSK ilce toplami degil).
// 1994 Cal (Denizli): YSK satiri merkez+belde toplami SHP; DIE ilce belediyesi DYP.
async function scenario_ilceBelediyesi(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(400);
    check('1994 yerel: yıl seçilebildi', await clickYear(page, '1994'));
    await page.waitForTimeout(600);
    await page.$eval('path[data-plaka="20"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(700);
    await page.$eval('path[data-geom-id="TR-D-20-008"]', (el) => el.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, clientX: 300, clientY: 300})));
    await page.waitForTimeout(200);
    const tip = await page.textContent('#tooltip');
    check('1994 yerel Çal: ilçe belediye başkanlığı DYP', tip.includes('Çal') && tip.includes('DYP önde'), tip);
    // 1994 il genel meclisi Izmir: DIE il satiri baska ile aitti; il toplami YSK kesin sonucundan (DYP)
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    await page.click('#oylamaToggle button[data-oylama="igm"]');
    await page.waitForTimeout(700);
    await page.$eval('path[data-plaka="35"]', (el) => el.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, clientX: 300, clientY: 300})));
    await page.waitForTimeout(200);
    const tip2 = await page.textContent('#tooltip');
    check('1994 il genel meclisi İzmir: YSK il toplamı (DYP)', tip2.includes('İzmir') && tip2.includes('DYP önde'), tip2);
    await page.click('#oylamaToggle button[data-oylama="baskan"]');
    await page.waitForTimeout(500);
  });
  check('ilçe belediyesi: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// Yerel secimde oylama turu: belediye baskani / il genel meclisi / belediye meclisi.
// 2024 il genel meclisi: buyuksehirlerde (Istanbul) secim yok -> bos ve notlu; Adiyaman'da var.
async function scenario_yerelOylama(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurYerel');
    await page.waitForTimeout(500);
    check('yerel: oylama sekmeleri görünüyor', await page.$eval('#oylamaToggle', (e) => !e.hidden));
    await page.click('#oylamaToggle button[data-oylama="igm"]');
    await page.waitForTimeout(700);
    const baslik = await page.textContent('#pageTitle');
    check('2024 il genel meclisi: başlıkta oylama adı', baslik.includes('İl Genel Meclisi'), baslik);
    const fill = async (pl) => page.$eval('path[data-plaka="' + pl + '"]', (e) => e.getAttribute('fill'));
    const ist = await fill(34), adi = await fill(2);
    check('2024 il genel meclisi: İstanbul boş (büyükşehir), Adıyaman renkli',
      ist === 'var(--map-empty)' && adi && adi !== 'var(--map-empty)', ist + ' / ' + adi);
    await page.$eval('path[data-plaka="34"]', (el) => el.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, clientX: 300, clientY: 300})));
    await page.waitForTimeout(200);
    const tip = await page.textContent('#tooltip');
    check('2024 il genel meclisi: İstanbul ipucunda 6360 notu', tip.includes('6360'), tip);
    await page.click('#oylamaToggle button[data-oylama="bm"]');
    await page.waitForTimeout(700);
    const ist2 = await fill(34);
    check('2024 belediye meclisi: İstanbul renkli', ist2 && ist2 !== 'var(--map-empty)', ist2);
    await page.$eval('path[data-plaka="2"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(600);
    const ilce = await page.$$eval('path[data-geom-id]', (els) => els.filter((e) => e.getAttribute('fill') && e.getAttribute('fill') !== 'var(--map-empty)').length);
    check('2024 belediye meclisi Adıyaman: ilçeler renkli', ilce >= 8, String(ilce));
    await page.click('#btnBackCountry').catch(() => {});
    await page.waitForTimeout(300);
    check('1989 yerel: yıl seçilebildi', await clickYear(page, '1989'));
    await page.waitForTimeout(600);
    await page.click('#oylamaToggle button[data-oylama="igm"]');
    await page.waitForTimeout(700);
    const b89 = await page.textContent('#pageTitle');
    const renkli89 = await page.$$eval('path[data-plaka]', (els) => els.filter((e) => e.getAttribute('fill') && e.getAttribute('fill') !== 'var(--map-empty)').length);
    check('1989 il genel meclisi (DİE): başlık ve renkli iller', b89.includes('İl Genel Meclisi') && renkli89 >= 60, b89 + ' / ' + renkli89);
    check('1977 yerel: yıl seçilebildi', await clickYear(page, '1977'));
    await page.waitForTimeout(600);
    const durum = await page.$$eval('#oylamaToggle button', (bs) => bs.map((b) => b.dataset.oylama + (b.disabled ? ':kapali' : '') + (b.classList.contains('active') ? ':aktif' : '')));
    check('1977 yerel: meclis sekmeleri pasif, başkanlık seçili',
      JSON.stringify(durum) === JSON.stringify(['baskan:aktif', 'igm:kapali', 'bm:kapali']), JSON.stringify(durum));
    await page.click('#btnTurGenel');
    await page.waitForTimeout(500);
    check('genel seçim: oylama sekmeleri gizli', await page.$eval('#oylamaToggle', (e) => e.hidden));
  });
  check('yerel oylama: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

// 1950-1957 genel secimleri cogunluk usulu: il kazanani vekil sayisina gore (esitlikte oy orani).
// 1950 Mardin: YSK'da Bagimsizlar 47.771 'oy' (birden cok adayin toplami, %7,6) ama vekil
// CHP 3, DP 3, Bagimsiz 1 ve oran CHP %49,7 -> harita ve panel CHP.
async function scenario_1950cogunluk(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurGenel');
    await page.waitForTimeout(400);
    check('1950 genel: yıl seçilebildi', await clickYear(page, '1950'));
    await page.waitForTimeout(500);
    const renk = await page.$$eval('path[data-plaka="47"], path[data-plaka="52"]', (els) => els.map((e) => e.getAttribute('fill')));
    check('1950 genel: Mardin ve Ordu aynı (CHP) renginde', renk.length === 2 && renk[0] === renk[1], JSON.stringify(renk));
    await page.$eval('path[data-plaka="47"]', (el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true})));
    await page.waitForTimeout(500);
    const ilk = await page.$eval('#dParties', (el) => el.textContent.trim().slice(0, 40));
    check('1950 genel Mardin: panelde ilk parti CHP', /^CHP/.test(ilk), ilk);
  });
  check('1950 çoğunluk: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
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

// 2007referandum'da Eminönü ve Fatih (2008'de Eminönü kaldırılıp Fatih'e
// katılmadan once) AYNI modern geomId'ye (TR-D-34-020) düşüyordu - ikisi de
// gerçek, farklı oy verisiyle kayıtlıydı ama harita sadece birini
// gösterebiliyordu (digeri sessizce eziliyordu). Kalıcı regresyon testi.
async function scenario_2007referandumEminonuFatih(browser) {
  const errors = await withPage(browser, async (page) => {
    await page.click('#btnTurReferandum');
    await page.waitForTimeout(500);
    const found = await clickYear(page, '2007');
    check('2007 referandum: yıl seçilebildi', found);
    await page.waitForTimeout(500);
    await page.click('path[data-plaka="34"]');
    await page.waitForTimeout(400);

    const histIds = await page.$$eval('path.il-path[data-geom-id]', (els) =>
      els.map((e) => e.dataset.geomId)
        // apply_idari_merges: HIST-* birlesimi sonradan eklenen parcalarla HISTK-<HIST-id>-* olabilir
        .map((id) => id.replace(/^HISTK-(HIST-.+)-[0-9a-f]{6}$/, '$1')).filter((id) => id.startsWith('HIST-')));
    check('2007 referandum İstanbul: Eminönü/Fatih ayrı tarihsel poligonlarla çiziliyor',
      histIds.includes('HIST-Istanbul-Eminonu') && histIds.includes('HIST-Istanbul-Fatih'), JSON.stringify(histIds));

    await page.click('path.il-path[data-geom-id="HIST-Istanbul-Eminonu"]');
    await page.waitForTimeout(300);
    const eminonuName = await page.$eval('#dName', (el) => el.textContent);
    const eminonuSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
    check('2007 referandum: Eminönü kendi (25.771 seçmenlik) verisini gösteriyor',
      eminonuName === 'Eminönü' && eminonuSecmen === '25.771', 'dName=' + eminonuName + ' dSecmen=' + eminonuSecmen);

    await page.click('path.il-path[data-geom-id="HIST-Istanbul-Fatih"]');
    await page.waitForTimeout(300);
    const fatihName = await page.$eval('#dName', (el) => el.textContent);
    const fatihSecmen = await page.$eval('#dSecmen', (el) => el.textContent);
    check('2007 referandum: Fatih kendi (292.980 seçmenlik) verisini gösteriyor - Eminönü ile karışmıyor',
      fatihName === 'Fatih' && fatihSecmen === '292.980', 'dName=' + fatihName + ' dSecmen=' + fatihSecmen);

    const staleModern = await page.$$eval('path.il-path[data-geom-id="TR-D-34-020"]', (els) => els.length);
    check('2007 referandum: eski/modern Fatih şekli ayrıca (üst üste) çizilmiyor', staleModern === 0, 'count=' + staleModern);
  });
  check('2007 referandum Eminönü/Fatih: konsol hatası yok', errors.length === 0, JSON.stringify(errors));
}

async function main() {
  const browser = await chromium.launch(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {});
  try {
    await scenario_2023genel(browser);
    await scenario_istanbul1994geometri(browser);
    await scenario_istanbul19992004Gecmisi(browser);
    await scenario_istanbulGenelGecmisi(browser);
    await scenario_sancaktepeCozumu(browser);
    await scenario_1992DalgasiCozumu(browser);
    await scenario_izmirDalgalariCozumu(browser);
    await scenario_ilOnlyYearsTekParca(browser);
    await scenario_1961_1987Ilce(browser);
    await scenario_yerelIlce1950_1977(browser);
    await scenario_referandumIlce(browser);
    await scenario_1950yerel(browser);
    await scenario_1955yerel(browser);
    await scenario_2024meclis(browser);
    await scenario_referandum(browser);
    await scenario_2007referandumEminonuFatih(browser);
    await scenario_1950cogunluk(browser);
    await scenario_yerelIlMerkezi(browser);
    await scenario_yerelOylama(browser);
    await scenario_ilceBelediyesi(browser);
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
