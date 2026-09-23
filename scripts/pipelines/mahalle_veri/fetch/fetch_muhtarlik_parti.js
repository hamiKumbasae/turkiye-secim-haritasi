const { chromium } = require('playwright');
const fs = require('fs');

// usage: node fetch_muhtarlik_parti.js <secimId> <secimTuru> <outFile> <targetsFile> <majorMapJson>
const SECIM_ID = parseInt(process.argv[2]);
const SECIM_TURU = parseInt(process.argv[3]);
const OUT_FILE = process.argv[4];
const TARGETS_FILE = process.argv[5];
const MAJOR_MAP = JSON.parse(process.argv[6]); // {"AK Parti":"parti9_ALDIGI_OY", ...}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const ALL_COL_RE = /^(parti|bagimsiz|ittifak)\d+_ALDIGI_OY$/;
const BAGIMSIZ_RE = /^bagimsiz\d+_ALDIGI_OY$/;
const majorCols = new Set(Object.values(MAJOR_MAP).filter(v => v !== 'SUM_BAGIMSIZ'));
const sumBagimsizNames = Object.entries(MAJOR_MAP).filter(([,v]) => v === 'SUM_BAGIMSIZ').map(([k]) => k);

(async () => {
  const targets = JSON.parse(fs.readFileSync(TARGETS_FILE, 'utf8'));
  // executablePath verilmezse Playwright'in kendi indirdigi Chromium'u kullanir
  // (bkz. package.json — `npx playwright install chromium`).
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  const results = {};
  let done = 0, errors = 0;
  const t0 = Date.now();

  for (const t of targets) {
    let attempt = 0;
    while (attempt < 3) {
      attempt++;
      try {
        const rows = await page.evaluate(async ({secimId, secimTuru, ilId, ilceId}) => {
          const url = `/api/getSecimSandikSonucList?secimId=${secimId}&secimTuru=${secimTuru}&ilId=${ilId}&ilceId=${ilceId}&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=1&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`;
          const r = await fetch(url, { credentials: 'include' });
          if (r.status !== 200) return { error: 'status ' + r.status };
          return r.json();
        }, { secimId: SECIM_ID, secimTuru: SECIM_TURU, ilId: t.il_ID, ilceId: t.ilce_ID });

        if (rows && rows.error) throw new Error(rows.error);
        if (!Array.isArray(rows)) throw new Error('not array: ' + JSON.stringify(rows).slice(0,200));

        const agg = {};
        for (const row of rows) {
          const mid = row.muhtarlik_ID;
          if (mid === 0 || mid === null || mid === undefined) continue;
          if (!agg[mid]) {
            agg[mid] = { muhtarlik_ID: mid, muhtarlik_ADI: row.muhtarlik_ADI, secmen: 0, gecerli: 0, gecersiz: 0, oyKullanan: 0, major: {}, diger: 0 };
          }
          const a = agg[mid];
          a.secmen += row.secmen_SAYISI || 0;
          a.gecerli += row.gecerli_OY_TOPLAMI || 0;
          a.gecersiz += row.gecersiz_OY_TOPLAMI || 0;
          a.oyKullanan += row.oy_KULLANAN_SECMEN_SAYISI || 0;
          for (const [name, col] of Object.entries(MAJOR_MAP)) {
            if (col === 'SUM_BAGIMSIZ') continue;
            a.major[name] = (a.major[name] || 0) + (row[col] || 0);
          }
          let bagimsizSum = 0;
          for (const key of Object.keys(row)) {
            if (BAGIMSIZ_RE.test(key)) bagimsizSum += row[key] || 0;
          }
          for (const name of sumBagimsizNames) {
            a.major[name] = (a.major[name] || 0) + bagimsizSum;
          }
          for (const key of Object.keys(row)) {
            if (!ALL_COL_RE.test(key)) continue;
            if (majorCols.has(key)) continue;
            if (BAGIMSIZ_RE.test(key) && sumBagimsizNames.length) continue;
            a.diger += row[key] || 0;
          }
        }
        results[t.geomId] = Object.values(agg);
        done++;
        break;
      } catch (e) {
        if (attempt >= 3) {
          errors++;
          console.log('FAILED', t.geomId, t.il_ADI, t.ilce_ADI, String(e).slice(0,150));
        } else {
          await sleep(500 * attempt);
        }
      }
    }
    if (done % 25 === 0) {
      const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
      console.log(`progress: ${done}/${targets.length} ilce (${errors} errors) in ${elapsed}s`);
      fs.writeFileSync(OUT_FILE, JSON.stringify(results));
    }
    await sleep(120);
  }

  fs.writeFileSync(OUT_FILE, JSON.stringify(results));
  console.log('DONE. total ilce with data:', Object.keys(results).length, 'errors:', errors);
  await browser.close();
})();
