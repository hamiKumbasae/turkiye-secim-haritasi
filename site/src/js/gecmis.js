  // ---------------- secim gecmisi (detay paneli) ----------------
  // Genel secim goruntulenirken secilen ilin ya da ilcenin 1950-2023 genel secimlerindeki parti
  // oy oranlarini cizgi grafikle gosterir. Veri: data/gecmis/genel.json (scripts/gecmis.py uretir;
  // ilce serisi bugunku ilceye gore, tarihsel eslemeyle). Grafik elle cizilen SVG'dir
  // (seatbar.js gibi); dis kutuphane yok.
  const GECMIS_YOL = 'data/gecmis/genel.json';
  const GECMIS_ESIK = 10;   // bir parti, bu yerde en az bir kez bu orana ulastiysa cizilir
  const GECMIS_EN_COK = 7;  // en fazla bu kadar parti cizgisi
  let gecmisBileti = 0;
  const SVGNS = 'http://www.w3.org/2000/svg';
  // Gorunum: parti (her parti kendi cizgisi) | soy | gelenek (data/parti_soy.yml, gecmis.py'nin
  // urettigi veri.soy). Tercih tarayicida hatirlanir.
  const GECMIS_GORUNUMLER = ['parti', 'soy', 'gelenek'];
  let gecmisGorunum = 'parti';
  try{ const g = localStorage.getItem('gecmisGorunum'); if(GECMIS_GORUNUMLER.includes(g)) gecmisGorunum = g; }catch(error){ /* depolama kapali */ }
  let gecmisSon = null; // son cizim: gorunum degisince yeniden cizmek icin {veri, seri, notlar}

  function gecmisGizle(){
    gecmisBileti++;
    gecmisSon = null;
    const kutu = $('#dGecmis');
    if(kutu) kutu.hidden = true;
  }

  function svgEl(ad, oz){
    const el = document.createElementNS(SVGNS, ad);
    for(const [k, v] of Object.entries(oz || {})) el.setAttribute(k, v);
    return el;
  }

  function gecmisNot(metin){
    $('#dGecmisNot').textContent = metin || '';
    $('#dGecmisNot').hidden = !metin;
  }

  // hedef: {tur:'il', plaka} | {tur:'ilce', geomId}
  async function gecmisGoster(hedef){
    const kutu = $('#dGecmis');
    if(!kutu) return;
    if(!DATA || DATA.tur !== 'genel'){ gecmisGizle(); return; }
    const bilet = ++gecmisBileti;
    let veri;
    try{ veri = await fetchJSON(GECMIS_YOL); }
    catch(e){ if(bilet === gecmisBileti) gecmisGizle(); return; }
    if(bilet !== gecmisBileti) return; // bu arada baska bir yer secildi

    let seri = null, notlar = [];
    if(hedef.tur === 'il'){
      seri = veri.il[String(hedef.plaka)];
      notlar.push('Her nokta, ilin o seçimdeki sınırlarına aittir; sonradan ayrılan iller eski seçimlerde bağlı oldukları ilin içinde sayılır.');
    } else {
      let g = hedef.geomId;
      if(g && !veri.ilce[g] && veri.tarihsel[g]){
        const bugun = veri.tarihsel[g];
        notlar.push('Grafik, bugünkü ' + veri.adlar[bugun] + ' ilçesinin sınırlarına göre.');
        g = bugun;
      }
      if(g && !veri.ilce[g] && veri.parcalar[g]){
        const adlar = veri.parcalar[g].map(x => veri.adlar[x]).filter(Boolean);
        gecmisSon = null;
        $('#dGecmisGrafik').innerHTML = '';
        $('#dGecmisLejant').innerHTML = '';
        $('#dGecmisGorunum').hidden = true;
        $('#dGecmisSoyNot').hidden = true;
        gecmisNot('Bu ilçe bugün birden çok ilçeye bölünmüş durumda: ' + adlar.join(', ') +
          '. Geçmişlerini görmek için güncel bir seçimde bu ilçelere tıklayın.');
        kutu.hidden = false;
        return;
      }
      seri = g ? veri.ilce[g] : null;
      const ustler = [...new Set((seri || []).filter(n => n[2]).map(n => n[2]))];
      if(ustler.length) notlar.push('İçi boş noktalar: ilçe o seçimde henüz ayrı değildi, bağlı olduğu ilçenin (' + ustler.join(', ') + ') sonucu gösterilir.');
      notlar.push('1950–1957 genel seçimlerinde ilçe verisi yok.');
    }
    if(!seri || seri.length < 2){ gecmisGizle(); return; }
    gecmisSon = {veri, seri, notlar};
    gecmisCiz();
    kutu.hidden = false;
  }

  function gecmisCiz(){
    if(!gecmisSon) return;
    const {veri, seri, notlar} = gecmisSon;
    const soyVar = !!veri.soy;
    const gorunum = soyVar ? gecmisGorunum : 'parti';
    $('#dGecmisGorunum').hidden = !soyVar;
    for(const b of document.querySelectorAll('#dGecmisGorunum button')){
      const secili = b.dataset.gorunum === gorunum;
      b.classList.toggle('active', secili);
      b.setAttribute('aria-pressed', secili ? 'true' : 'false');
    }
    cizGecmis(veri.secimler, gorunumSerisi(veri, seri, gorunum));
    gecmisNot(notlar.join(' '));
    const soyNot = $('#dGecmisSoyNot');
    soyNot.hidden = gorunum === 'parti';
    if(gorunum !== 'parti') $('#dGecmisSoyNotMetin').textContent = veri.soy[gorunum].aciklama +
      ' Bağımsızlar ve “Diğer” hiçbir çizgiye eklenmez; AK Parti kendi çizgisindedir.';
  }

  for(const b of document.querySelectorAll('#dGecmisGorunum button'))
    b.addEventListener('click', () => gecmisGorunumSec(b.dataset.gorunum));

  function gecmisGorunumSec(g){
    if(!GECMIS_GORUNUMLER.includes(g) || g === gecmisGorunum) return;
    gecmisGorunum = g;
    try{ localStorage.setItem('gecmisGorunum', g); }catch(error){ /* depolama kapali */ }
    gecmisCiz();
  }

  // Seriyi secilen gorunume cevirir. Donen yapi: {seri, kisa(k), renk(k), uyeler(n, k)}; seri noktalari
  // [secim, {anahtar: oran}, ust ilce adi ya da 0, {anahtar: [o secimdeki parti adlari]}].
  // Soy/gelenek gruplarinin anahtari '~' ile baslar (parti anahtarlariyla karismaz).
  function gorunumSerisi(veri, seri, gorunum){
    if(gorunum === 'parti') return {seri, kisa: partyShort, renk: partyColor, uyeler: () => null};
    const kt = veri.soy[gorunum];
    const grup = Object.fromEntries(kt.gruplar.map(g => ['~' + g.id, g]));
    const yeni = seri.map(n => {
      const uye = kt.uye[n[0]] || {};
      const oranlar = {}, kimler = {};
      for(const [p, v] of Object.entries(n[1])){
        const gid = uye[p];
        if(!gid){ oranlar[p] = v; continue; }
        const k = '~' + gid;
        oranlar[k] = (oranlar[k] || 0) + v;
        (kimler[k] = kimler[k] || []).push(p);
      }
      // gecmis.py'nin ham orandan hesapladigi toplam (esigin altinda kalan uye varsa)
      const toplam = gorunum === 'gelenek' ? n[3] : null;
      if(toplam) for(const [gid, v] of Object.entries(toplam)){
        const k = '~' + gid;
        oranlar[k] = v;
        kimler[k] = Object.keys(uye).filter(p => uye[p] === gid);
      }
      for(const k of Object.keys(kimler)) oranlar[k] = Math.round(oranlar[k] * 10) / 10;
      return [n[0], oranlar, n[2] || 0, kimler];
    });
    return {
      seri: yeni,
      kisa: k => grup[k] ? grup[k].kisa : partyShort(k),
      // renk korlugu modunda gruplar sirayla Okabe-Ito paletini alir (bkz. erisim.js)
      renk: k => !grup[k] ? partyColor(k) : renkKoruModu ? RENK_KORU_PALET[kt.gruplar.indexOf(grup[k]) % RENK_KORU_PALET.length] : partyColor(grup[k].renk),
      uyeler: (n, k) => grup[k] ? (n[3][k] || []) : null,
    };
  }

  function cizGecmis(secimler, gs){
    const seri = gs.seri;
    // Partiler: bu yerde en yuksek orani GECMIS_ESIK'i gecenler
    // ve toplam agirligi (butun secimlerdeki oranlarin toplami) en cok olanlar: uzun omurlu
    // partiler (CHP, AP, AK Parti) tek secimlik buyuk partilerin onune gecer.
    const enYuksek = {}, toplam = {};
    for(const [, oranlar] of seri)
      for(const [p, v] of Object.entries(oranlar)){
        enYuksek[p] = Math.max(enYuksek[p] || 0, v);
        toplam[p] = (toplam[p] || 0) + v;
      }
    let partiler = Object.keys(enYuksek).filter(p => enYuksek[p] >= GECMIS_ESIK)
      .sort((a, b) => toplam[b] - toplam[a]).slice(0, GECMIS_EN_COK);
    if(!partiler.length) partiler = Object.keys(enYuksek).sort((a, b) => enYuksek[b] - enYuksek[a]).slice(0, 3);

    const W = 320, H = 176, sol = 30, sag = 10, ust = 10, alt = 22;
    const t0 = Math.floor(secimler[seri[0][0]].t / 10) * 10;
    const t1 = 2025;
    const yMax = Math.min(100, Math.max(30, Math.ceil(Math.max(...partiler.map(p => enYuksek[p])) / 10) * 10));
    const X = t => sol + (t - t0) / (t1 - t0) * (W - sol - sag);
    const Y = v => ust + (1 - v / yMax) * (H - ust - alt);

    const svg = svgEl('svg', {viewBox: `0 0 ${W} ${H}`, class: 'gecmis-svg', role: 'img',
      'aria-label': 'Genel seçimlerde parti oy oranları, ' + secimler[seri[0][0]].ad.split(' ').pop() + '–2023'});
    // y ekseni: yatay kilavuz cizgileri
    const adim = yMax > 60 ? 20 : 10;
    for(let v = 0; v <= yMax; v += adim){
      svg.appendChild(svgEl('line', {x1: sol, x2: W - sag, y1: Y(v), y2: Y(v), class: v === 0 ? 'gx-eksen' : 'gx-izgara'}));
      const tx = svgEl('text', {x: sol - 5, y: Y(v) + 3.5, class: 'gx-etiket', 'text-anchor': 'end'});
      tx.textContent = v === yMax ? '%' + v : String(v);
      svg.appendChild(tx);
    }
    // x ekseni: on yillar
    for(let t = t0; t <= 2020; t += 10){
      const tx = svgEl('text', {x: X(t), y: H - 6, class: 'gx-etiket', 'text-anchor': 'middle'});
      tx.textContent = String(t);
      svg.appendChild(tx);
    }
    // goruntulenen secim
    const simdiki = secimler.findIndex(s => s.k === currentYear);
    if(simdiki >= 0){
      svg.appendChild(svgEl('line', {x1: X(secimler[simdiki].t), x2: X(secimler[simdiki].t), y1: ust, y2: H - alt, class: 'gx-simdi'}));
    }
    // parti cizgileri: yalniz ardisik iki secimde de bulunan noktalar birlesir (parti girmediyse kopar)
    for(const p of partiler.slice().reverse()){
      const renk = gs.renk(p);
      const noktalar = seri.filter(n => n[1][p] != null);
      let parca = [];
      const bitir = () => {
        if(parca.length > 1) svg.appendChild(svgEl('polyline', {points: parca.map(n => X(secimler[n[0]].t) + ',' + Y(n[1][p])).join(' '), class: 'gx-cizgi', stroke: renk}));
        parca = [];
      };
      noktalar.forEach((n, j) => {
        const onceki = noktalar[j - 1];
        if(onceki && n[0] !== onceki[0] + 1) bitir();
        parca.push(n);
      });
      bitir();
      for(const n of noktalar){
        const s = secimler[n[0]];
        const c = svgEl('circle', {cx: X(s.t), cy: Y(n[1][p]), r: n[2] ? 2.6 : 2.4, class: n[2] ? 'gx-nokta bos' : 'gx-nokta',
          fill: n[2] ? 'var(--surface-1)' : renk, stroke: renk});
        const baslik = svgEl('title');
        const uyeler = gs.uyeler(n, p);
        baslik.textContent = (YEAR_LABEL[s.k] || s.k) + ' · ' + gs.kisa(p) +
          (uyeler && uyeler.length ? ' (' + uyeler.map(partyShort).join(' + ') + ')' : '') +
          ': %' + n[1][p].toLocaleString('tr-TR') +
          (n[2] ? ' (' + n[2] + ' ilçesinin sonucu)' : '');
        c.appendChild(baslik);
        svg.appendChild(c);
      }
    }
    const grafik = $('#dGecmisGrafik');
    grafik.innerHTML = '';
    grafik.appendChild(svg);

    // lejant: parti adi + son secimdeki orani
    const son = seri[seri.length - 1];
    $('#dGecmisLejant').innerHTML = '<span class="gx-son-baslik">' + escapeHtml(YEAR_LABEL[secimler[son[0]].k] || secimler[son[0]].k) + '</span>' + partiler.map(p =>
      '<span class="gx-lejant"><span class="dot" style="background:' + gs.renk(p) + '"></span>' +
      escapeHtml(gs.kisa(p)) + (son[1][p] != null ? ' <span class="gx-son">%' + son[1][p].toLocaleString('tr-TR') + '</span>' : '') + '</span>'
    ).join('');
  }
