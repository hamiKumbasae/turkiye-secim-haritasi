// YSK Acik Veri Portali'ndan (getSecimSandikSonucList) bir secimi TUM ilcelerde
// (ya da verilen illerde) sandik duzeyinde ceker ve (il, ilce, belde) bazinda
// toplar. fetch_and_aggregate.js'ten farki: belde sandiklari ilce toplamina
// KARISMAZ (belde_ID ayri anahtar) - meclis secimlerinde ve mahalli ara /
// yenileme secimlerinde ayni ilcede birden fazla belediye yarisi olabilir.
//
// Kullanim:
//   node fetch_belde_agrege.js <label> <secimId> <secimTuru> [--iller 34,6] [--ham]
//
//   --ham   bos olmayan sandik satirlarini da (sifir alanlar atilarak) yazar;
//           yalnizca kucuk secimler (ara / yenileme) icin.
//
// Cikti: data/raw/ysk/acikveri-belde-agrege/<label>.json
//        {secimId, secimTuru, baslik, cekildi, birimler: {"il-ilce-belde": {...}}, hatalar, ham?}
// Kaldigi yerden devam: .work/<label>_belde_progress.json
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const [LABEL, SECIM_ID, SECIM_TURU] = [args[0], parseInt(args[1]), parseInt(args[2])];
const ilArg = args.indexOf('--iller') >= 0 ? args[args.indexOf('--iller') + 1].split(',').map(Number) : null;
const HAM = args.includes('--ham');

const ROOT = path.join(__dirname, '..', '..', '..');
const IL_ILCE = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'raw', 'ysk', 'acikveri-il-ilce-listesi.json'), 'utf8'));
const OUT_DIR = path.join(ROOT, 'data', 'raw', 'ysk', 'acikveri-belde-agrege');
const WORK = path.join(__dirname, '.work');
fs.mkdirSync(OUT_DIR, { recursive: true });
fs.mkdirSync(WORK, { recursive: true });
const PROGRESS = path.join(WORK, `${LABEL}_belde_progress.json`);

const SAY = /^(secmen_SAYISI|oy_KULLANAN_SECMEN_SAYISI|gecerli_OY_TOPLAMI|gecersiz_OY_TOPLAMI|bagimsiz_TOPLAM_OY|parti\d+_ALDIGI_OY|bagimsiz\d+_ALDIGI_OY)$/;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 90000 });
  const api = (u) => page.evaluate(async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    if (r.status !== 200) return { error: 'status ' + r.status };
    return r.json();
  }, u);

  const baslik = await api(`/api/getSandikSecimSonucBaslikList?secimId=${SECIM_ID}&secimTuru=${SECIM_TURU}`);
  const targets = [];
  for (const [ilId, info] of Object.entries(IL_ILCE)) {
    if (ilArg && !ilArg.includes(parseInt(ilId))) continue;
    for (const c of info.ilceler) targets.push({ ilId: parseInt(ilId), ilAdi: info.il_ADI, ilceId: c.ilce_ID, ilceAdi: c.ilce_ADI });
  }
  let st = { next: 0, birimler: {}, hatalar: [], ham: [] };
  if (fs.existsSync(PROGRESS)) st = JSON.parse(fs.readFileSync(PROGRESS, 'utf8'));
  const t0 = Date.now();
  for (let i = st.next; i < targets.length; i++) {
    const t = targets[i];
    const u = `/api/getSecimSandikSonucList?secimId=${SECIM_ID}&secimTuru=${SECIM_TURU}&ilId=${t.ilId}&ilceId=${t.ilceId}&beldeId=&birimId=&muhtarlikId=&cezaeviId=&sandikTuru=&sandikNoIlk=&sandikNoSon=&ulkeId=&disTemsilcilikId=&gumrukId=&yurtIciDisi=1&sandikRumuzIlk=&sandikRumuzSon=&secimCevresiId=&sandikId=&sorguTuru=`;
    let rows = null;
    for (let a = 1; a <= 5 && rows === null; a++) {
      try {
        const r = await api(u);
        if (!Array.isArray(r)) throw new Error(JSON.stringify(r).slice(0, 120));
        rows = r;
      } catch (e) {
        if (a === 5) st.hatalar.push({ ilId: t.ilId, ilceId: t.ilceId, ilce: t.ilceAdi, hata: String(e).slice(0, 160) });
        await sleep(800 * a);
      }
    }
    for (const row of rows || []) {
      const key = `${t.ilId}-${t.ilceId}-${row.belde_ID || 0}`;
      const b = st.birimler[key] ||= { ilId: t.ilId, ilAdi: t.ilAdi, ilceId: t.ilceId, ilceAdi: t.ilceAdi,
        beldeId: row.belde_ID || 0, beldeAdi: row.belde_ADI || null, sandik: 0, toplam: {} };
      b.sandik += 1;
      for (const [k, v] of Object.entries(row)) if (SAY.test(k) && v) b.toplam[k] = (b.toplam[k] || 0) + v;
      if (HAM) {
        const c = {};
        for (const [k, v] of Object.entries(row)) if (v !== 0 && v !== null && v !== '') c[k] = v;
        st.ham.push(c);
      }
    }
    if ((i + 1) % 25 === 0 || i === targets.length - 1) {
      st.next = i + 1;
      fs.writeFileSync(PROGRESS, JSON.stringify(st));
      console.log(`[${LABEL}] ${i + 1}/${targets.length} ilce, ${Object.keys(st.birimler).length} birim, ${st.hatalar.length} hata - ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    await sleep(100);
  }
  const out = { secimId: SECIM_ID, secimTuru: SECIM_TURU, label: LABEL, kaynak: 'acikveri.ysk.gov.tr getSecimSandikSonucList (sandik duzeyi, il/ilce/belde bazinda toplandi)',
    cekildi: new Date().toISOString().slice(0, 10), baslik, birimler: st.birimler, hatalar: st.hatalar };
  if (HAM) out.hamSandik = st.ham;
  fs.writeFileSync(path.join(OUT_DIR, `${LABEL}.json`), JSON.stringify(out, null, HAM ? 0 : 1));
  fs.rmSync(PROGRESS, { force: true });
  console.log(`[${LABEL}] TAMAM: ${Object.keys(st.birimler).length} birim, ${st.hatalar.length} hata`);
  await browser.close();
})();
