const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
// test edilen site: python3 site/build.py ciktisi (site/dist/)
const root = path.resolve(__dirname, '..', 'dist');
let browser;
before(async () => { browser = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE || undefined}); });
after(async () => { await browser?.close(); });

// Serve the real built page/data locally through routing. No third-party network or server needed.
async function setup(t, intercept = async () => false){
  const context = await browser.newContext();
  t.after(() => context.close());
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const requests = [], errors = [];
  page.on('pageerror', e => errors.push(e.message));
  t.after(() => assert.deepEqual(errors, [], 'no uncaught browser errors'));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if(url.hostname !== 'atlas.test') return route.abort();
    const name = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
    requests.push(name);
    const serve = async () => route.fulfill({
      status: 200,
      contentType: name.endsWith('.html') ? 'text/html; charset=utf-8' : 'application/json',
      body: await fs.readFile(path.join(root, name)),
    });
    if(await intercept(name, route, serve)) return;
    await serve();
  });
  await page.goto('http://atlas.test/');
  return {page, requests};
}
const ready = page => page.locator('#results[aria-busy="false"]').waitFor();
const year = (page, label) => page.locator('#yearPicker button').filter({hasText: new RegExp('^'+label+'$')}).click();
const activeYear = page => page.locator('#yearPicker .active').textContent();
const tick = page => page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));

test('initial load excludes neighborhood geometry and votes', async t => {
  const {page, requests} = await setup(t);
  await ready(page);
  assert.equal(await activeYear(page), '2023');
  assert(!requests.some(x => x.startsWith('geo/mahalle/')));
  // ilce sinirlari ilk cizimi beklemez: arka planda sonradan iner
  assert(!requests.slice(0, requests.indexOf('data/elections/2023.json') + 1).includes('geo/ilce_sinirlari.geojson'));
  assert(!requests.some(x => x.startsWith('data/mahalle_votes/')));
 });

test('startup network failure can be retried without reloading', async t => {
  let attempts = 0;
  const {page} = await setup(t, async (name, route) => {
    if(name === 'data/parties.json' && ++attempts === 1){ await route.abort('internetdisconnected'); return true; }
  });
  await page.locator('#retryLoad').waitFor();
  assert.equal(await page.locator('#results').getAttribute('aria-busy'), 'true');
  await page.locator('#retryLoad').click();
  await ready(page);
  assert.equal(attempts, 2);
 });

test('failed election request is evicted and retries recover', async t => {
  let attempts = 0;
  const {page} = await setup(t, async (name, route) => {
    if(name === 'data/elections/2018.json' && ++attempts === 1){ await route.abort('internetdisconnected'); return true; }
  });
  await ready(page); await year(page, '2018');
  await page.locator('#retryLoad').waitFor();
  assert.equal(await page.locator('#results').evaluate(el => el.inert), true);
  await page.locator('#retryLoad').click(); await ready(page);
  assert.equal(await activeYear(page), '2018'); assert.equal(attempts, 2);
 });

test('late historical geometry cannot overwrite the selected modern year', async t => {
  let release;
  const {page} = await setup(t, async (name, route, serve) => {
    if(name === 'geo/eras/era1950.geojson'){
      await new Promise(resolve => { release = resolve; }); await serve(); return true;
    }
  });
  await ready(page); await year(page, '1950');
  while(!release) await tick(page);
  await year(page, '2023'); await ready(page);
  const finished = page.waitForEvent('requestfinished', request => request.url().includes('era1950.geojson'));
  release(); await finished; await tick(page);
  // A subsequent render catches stale shared GEO even if the old request did not redraw immediately.
  await year(page, '2018'); await ready(page);
  assert.equal(await activeYear(page), '2018');
  assert.equal(await page.locator('#mapSvg path.geo-path').count(), 81);
 });

test('two years in the same era share an in-flight geometry request safely', async t => {
  let release, attempts = 0;
  const {page} = await setup(t, async (name, route, serve) => {
    // 1961 ve 1965 ayni il donemi (era1957_1965: Kaynarca Kocaeli'de)
    if(name === 'geo/eras/era1957_1965.geojson'){
      attempts++; await new Promise(resolve => { release = resolve; }); await serve(); return true;
    }
  });
  await ready(page); await year(page, '1961');
  while(!release) await tick(page);
  await year(page, '1965'); release(); await ready(page);
  assert.equal(await activeYear(page), '1965');
  assert.equal(await page.locator('#mapSvg path.geo-path').count(), 67);
  assert.equal(attempts, 1);
 });

test('district drilldown loads neighborhood geometry on demand and retries failures', async t => {
  let attempts = 0;
  const {page, requests} = await setup(t, async (name, route) => {
    if(name === 'geo/mahalle/TR-D-01-001.json' && ++attempts === 1){ await route.fulfill({status:503, body:'unavailable'}); return true; }
  });
  await ready(page);
  await page.locator('#mapSvg path[data-plaka="1"]').click();
  await page.locator('#dDistrictList [data-geom-id="TR-D-01-001"]').click();
  await page.locator('#retryLoad').waitFor();
  await page.locator('#retryLoad').click();
  await page.locator('#mapSvg path[data-mahalle-id]').first().waitFor();
  assert.equal(attempts, 2);
  assert(requests.includes('data/mahalle_votes/2023.json'));
 });

test('late neighborhood response cannot replace a newly selected election', async t => {
  let release;
  const {page, requests} = await setup(t, async (name, route, serve) => {
    if(name === 'data/mahalle_votes/2023.json'){
      await new Promise(resolve => { release = resolve; }); await serve(); return true;
    }
  });
  await ready(page);
  await page.locator('#mapSvg path[data-plaka="1"]').click();
  await page.locator('#dDistrictList [data-geom-id="TR-D-01-001"]').click();
  while(!release) await tick(page);
  await year(page, '2018'); await ready(page);
  release();
  await page.waitForResponse('**/geo/mahalle/TR-D-01-001.json*');
  await tick(page);
  assert.equal(await activeYear(page), '2018');
  assert.equal(await page.locator('#mapSvg path[data-mahalle-id]').count(), 0);
 });

test('failed historical geometry is requested again on retry', async t => {
  let attempts = 0;
  const {page} = await setup(t, async (name, route) => {
    if(name === 'geo/eras/era1950.geojson' && ++attempts === 1){ await route.abort(); return true; }
  });
  await ready(page); await year(page, '1950');
  await page.locator('#retryLoad').waitFor();
  await page.locator('#retryLoad').click(); await ready(page);
  assert.equal(await activeYear(page), '1950');
  assert.equal(await page.locator('#mapSvg path.geo-path').count(), 63);
  assert.equal(attempts, 2);
});

test('switching election type updates year choices while loading', async t => {
  let release;
  const {page} = await setup(t, async (name, route, serve) => {
    if(name === 'data/elections/2024yerel.json'){
      await new Promise(resolve => { release = resolve; }); await serve(); return true;
    }
  });
  await ready(page); await page.locator('#btnTurYerel').click();
  while(!release) await tick(page);
  assert.equal(await page.locator('#yearPicker button').first().textContent(), '2024');
  await year(page, '2019'); await ready(page);
  release(); await tick(page);
  assert.equal(await activeYear(page), '2019');
  assert.match(await page.locator('#tableTitle').textContent(), /2019/);
});

test('mobile viewport exposes retry and preserves controls after recovery', async t => {
  let attempts = 0;
  const {page} = await setup(t, async (name, route) => {
    if(name === 'data/elections/2018.json' && ++attempts === 1){ await route.abort(); return true; }
  });
  await page.setViewportSize({width:390, height:844});
  await ready(page); await year(page, '2018');
  await page.locator('#retryLoad').click(); await ready(page);
  assert.equal(await activeYear(page), '2018');
  assert.equal(await page.locator('#results').evaluate(el => el.inert), false);
});

test('district boundaries load in the background and recover when the first request fails', async t => {
  let attempts = 0;
  const {page} = await setup(t, async (name, route) => {
    if(name === 'geo/ilce_sinirlari.geojson' && ++attempts === 1){ await route.abort('internetdisconnected'); return true; }
  });
  await ready(page);
  while(attempts < 1) await tick(page);
  await page.locator('#mapSvg path[data-plaka="6"]').click();
  await page.locator('#mapSvg path[data-geom-id]').first().waitFor();
  assert.equal(attempts, 2);
  assert(await page.locator('#mapSvg path[data-geom-id]').count() > 20);
});

test('change mode compares with the previous election of the same type', async t => {
  const {page, requests} = await setup(t);
  await ready(page);
  await page.locator('#modeGroup button[data-mode="degisim"]').click();
  await page.locator('#seqNote:not([hidden])').waitFor();
  assert(requests.includes('data/elections/2018.json'));
  assert.match(await page.locator('#seqNote').textContent(), /2018 → 2023/);
  const fills = await page.locator('#mapSvg path.geo-path').evaluateAll(els => els.map(el => el.getAttribute('fill')));
  assert(fills.filter(f => f && f.startsWith('hsl(')).length > 70);
  // the oldest election has nothing to compare with
  await year(page, '1950'); await ready(page);
  assert.equal(await page.locator('#modeGroup button[data-mode="degisim"]').isHidden(), true);
});

test('the address keeps the view and a shared link opens it again', async t => {
  const {page} = await setup(t);
  await ready(page);
  await year(page, '1977'); await ready(page);
  await page.locator('#modeGroup button[data-mode="parti"]').click();
  await page.locator('#partySelect').selectOption('CHP');
  await page.locator('#mapSvg path[data-plaka="6"]').click();
  await page.locator('#mapSvg path[data-geom-id]').first().waitFor();
  const hash = new URL(page.url()).hash;
  assert.match(hash, /secim=1977/); assert.match(hash, /il=6/); assert.match(hash, /mod=parti/); assert.match(hash, /parti=CHP/);

  const other = page; // ayni yonlendirmeyle sifirdan ac
  await other.goto('about:blank');
  await other.goto('http://atlas.test/' + hash);
  await other.locator('#results[aria-busy="false"]').waitFor();
  await other.locator('#mapSvg path[data-geom-id]').first().waitFor();
  assert.equal(await other.locator('#yearPicker .active').textContent(), '1977');
  assert.equal(await other.locator('#partySelect').inputValue(), 'CHP');
  assert.equal(await other.locator('#modeGroup button.active').getAttribute('data-mode'), 'parti');
  assert.match(await other.locator('#mapBreadcrumbName').textContent(), /Ankara/);
});

test('CSV download contains province and district rows of the open election', async t => {
  const {page} = await setup(t);
  await ready(page);
  await page.locator('#btnTableView').click();
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#btnCsv').click()]);
  assert.equal(download.suggestedFilename(), 'secim_2023.csv');
  const text = await fs.readFile(await download.path(), 'utf8');
  assert(text.startsWith('\ufeff'), 'UTF-8 BOM for Excel');
  const lines = text.slice(1).trimEnd().split('\r\n');
  assert.match(lines[0], /^seçim,düzey,plaka,il,ilçe,/);
  assert.equal(lines.filter(l => l.startsWith('2023,il,')).length, 81);
  assert(lines.filter(l => l.startsWith('2023,ilçe,')).length > 900);
});

test('map regions are keyboard accessible and a colour-blind palette can be switched on', async t => {
  const {page} = await setup(t);
  await ready(page); await tick(page);
  const ankara = page.locator('#mapSvg path[data-plaka="6"]');
  assert.equal(await ankara.getAttribute('tabindex'), '0');
  assert.match(await ankara.getAttribute('aria-label'), /^Ankara: .+ önde$/);
  await ankara.focus(); await page.keyboard.press('Enter');
  await page.locator('#mapSvg path[data-geom-id]').first().waitFor();
  assert.match(await page.locator('#mapBreadcrumbName').textContent(), /Ankara/);
  await page.locator('#btnBackCountry').click();
  const before = await page.locator('#mapSvg path[data-plaka="6"]').getAttribute('fill');
  await page.locator('#btnRenkKoru').click();
  assert.equal(await page.locator('#btnRenkKoru').getAttribute('aria-pressed'), 'true');
  const after = await page.locator('#mapSvg path[data-plaka="6"]').getAttribute('fill');
  assert.notEqual(after, before);
  assert.match(after, /^#(E69F00|0072B2|009E73|D55E00|56B4E9|CC79A7|F0E442|9a9a9a)$/);
});

test('phone width has no horizontal page scroll', async t => {
  const {page} = await setup(t);
  await page.setViewportSize({width:390, height:844});
  await ready(page);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 390);
});

test('council votes have an accurate national chart and no mayor fallback in 1984', async t => {
  const {page,requests}=await setup(t); await ready(page); await page.locator('#btnTurYerel').click(); await ready(page);
  await page.locator('#oylamaToggle [data-oylama="bm"]').click(); await ready(page);
  assert.equal(await page.locator('#seatbarTitle').textContent(),'Belediye Meclisleri Oy Dağılımı');
  assert(!/başkanlığı/.test(await page.locator('#majoritySub').textContent()));
  await year(page,'1984'); await ready(page);
  assert.equal(await page.locator('#modeGroup [data-mode="degisim"]').isHidden(),true);
  assert(!requests.includes('data/elections/1977yerel.json'));
});

test('district council tooltips and accessible palette retain council seats', async t => {
  const {page}=await setup(t); await ready(page); await page.locator('#btnTurYerel').click(); await ready(page);
  await page.locator('#mapSvg path[data-plaka="6"]').dispatchEvent('click');
  await page.locator('#detailViewToggle [data-view="meclis"]').click();
  await page.locator('#dDistrictList .district-row[data-geom-id="TR-D-06-001"]').click();
  const polygon=page.locator('#mapSvg path[data-geom-id="TR-D-06-001"]');
  await polygon.dispatchEvent('mousemove',{clientX:300,clientY:300});
  assert.match(await page.locator('#tooltip').textContent(),/22 \/ 30 sandalye/);
  assert(!/oy|başkan/.test(await page.locator('#tooltip').textContent()));
  await page.locator('#btnRenkKoru').click();
  assert.equal(await page.locator('#modeGroup').isHidden(),true);
  await polygon.dispatchEvent('mousemove',{clientX:300,clientY:300});
  assert.match(await page.locator('#tooltip').textContent(),/22 \/ 30 sandalye/);
});

test('unresolved vote totals do not show invented percentages', async t => {
  const {page}=await setup(t,async(name,route)=>{
    if(name!=='data/elections/2023.json') return false;
    const d=JSON.parse(await fs.readFile(path.join(root,name),'utf8'));
    const r=d.iller.find(x=>x.plaka===1); r.gecerliOy+=100000;
    await route.fulfill({contentType:'application/json',body:JSON.stringify(d)}); return true;
  });
  await ready(page); await page.locator('#mapSvg path[data-plaka="1"]').dispatchEvent('click');
  assert.match(await page.locator('#dInfoNote').textContent(),/uyuşmuyor/);
  assert(!/%\d/.test(await page.locator('#dParties').textContent()));
});

test('council comparison fails closed if the matching ballot file is absent', async t=>{
 const {page}=await setup(t,async(name,route)=>{
  if(name!=='data/meclis_harita/2019yerel_bm.json') return false;
  await route.fulfill({status:404,body:'missing'});return true;
 });
 await ready(page);await page.locator('#btnTurYerel').click();await ready(page);
 await page.locator('#oylamaToggle [data-oylama="bm"]').click();await ready(page);
 await page.locator('#modeGroup [data-mode="degisim"]').click();
 assert.equal(await page.locator('#modeGroup button.active').getAttribute('data-mode'),'winner');
 await page.waitForFunction(()=>document.querySelector('#loadMessage').textContent.includes('bulunamadı'));
 assert.match(await page.locator('#loadMessage').textContent(),/bulunamadı/);
});

test('a late change comparison cannot override a newer winner-mode selection', async t=>{
 let release;
 const {page}=await setup(t,async(name,route,serve)=>{
  if(name!=='data/elections/2018.json') return false;
  await new Promise(resolve=>release=resolve);await serve();return true;
 });
 await ready(page);await page.locator('#modeGroup [data-mode="degisim"]').click();
 while(!release) await tick(page);
 await page.locator('#modeGroup [data-mode="winner"]').click();release();await tick(page);await tick(page);
 assert.equal(await page.locator('#modeGroup button.active').getAttribute('data-mode'),'winner');
});

test('records that do not match their source carry a visible warning', async t => {
  const {page} = await setup(t);
  await page.goto('about:blank');
  await page.goto('http://atlas.test/#secim=1961&il=6');
  await ready(page);
  const cubuk = page.locator('#mapSvg path[data-geom-id="HIST1961-06-Cubuk"]');
  await cubuk.waitFor();
  await cubuk.hover();
  assert.match(await page.locator('#tooltip .tip-uyari').textContent(), /⚠ Kaynakla tam tutmuyor/);
  await cubuk.click();
  assert.match(await page.locator('#dInfoNote').textContent(), /Kaynakla tam tutmuyor/);
  // a record whose votes add up shows no warning
  await page.goto('about:blank'); await page.goto('http://atlas.test/#secim=2023&il=6'); await ready(page);
  await page.locator('#mapSvg path[data-geom-id]').first().hover();
  assert.doesNotMatch(await page.locator('#tooltip').textContent(), /Kaynakla tam tutmuyor/);
});
