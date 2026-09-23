const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
// Varsayilan calisma dizini: repo icinde, .gitignore'da (bu script'in ciktisi
// aracidir — asil hedef data/normalized/mahalle/<yil>.json'a elle/import
// script'iyle tasinir, bkz. ../README.md).
const OUT = process.env.MAHALLE_WORKDIR || path.join(__dirname, '..', '.work');
fs.mkdirSync(OUT, { recursive: true });

const SECIM_ID = process.argv[2] ? parseInt(process.argv[2]) : 20240;
const OUT_FILE = process.argv[3] || `${OUT}/muhtarlik_votes_${SECIM_ID}.json`;
const TARGETS_FILE = process.argv[4] || `${OUT}/fetch_targets.json`;
const SECIM_TURU = process.argv[5] ? parseInt(process.argv[5]) : 9;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  const targets = JSON.parse(fs.readFileSync(TARGETS_FILE, 'utf8'));
  // executablePath verilmezse Playwright'in kendi indirdigi Chromium'u kullanir
  // (bkz. package.json — `npx playwright install chromium`).
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  const results = {}; // geomId -> [{muhtarlik_ID, muhtarlik_ADI, secmen, gecerli, gecersiz, oyKullanan, candidates:{aday_SIRA_NO: oy}}]
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

        // aggregate by muhtarlik_ID
        const agg = {};
        for (const row of rows) {
          const mid = row.muhtarlik_ID;
          if (mid === 0 || mid === null || mid === undefined) continue; // skip ilce-level rollup or ungrouped
          if (!agg[mid]) {
            agg[mid] = { muhtarlik_ID: mid, muhtarlik_ADI: row.muhtarlik_ADI, secmen: 0, gecerli: 0, gecersiz: 0, oyKullanan: 0, cand: {} };
          }
          const a = agg[mid];
          a.secmen += row.secmen_SAYISI || 0;
          a.gecerli += row.gecerli_OY_TOPLAMI || 0;
          a.gecersiz += row.gecersiz_OY_TOPLAMI || 0;
          a.oyKullanan += row.oy_KULLANAN_SECMEN_SAYISI || 0;
          for (let i = 1; i <= 10; i++) {
            const v = row['bagimsiz' + i + '_ALDIGI_OY'] || 0;
            a.cand[i] = (a.cand[i] || 0) + v;
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
