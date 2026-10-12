  // ---------------- iki secimi yan yana karsilastirma ----------------
  // "Karşılaştır" acikken harita ikiye bolunur: solda acik secim (her zamanki harita), sagda ayni
  // turden ikinci bir secim. Yakinlastirma senkronize: sol harita ile inildiginde sag da ayni ile
  // iner ve il duzeyinde iki harita AYNI izdusumle cizilir (renderProvinceMap ortak sinir kutusunu
  // karsiOrtakSinir ile alir), boylece donem sinirlari farkli olsa da (1977 Adana, Osmaniye dahil)
  // ayni yer ayni konumda durur. Mahalle duzeyinde sag harita ili gosterir, acik ilce isaretli.
  // Il/ilce secimi .geo-path seciciyle iki haritada birlikte isaretlenir. Renk modu soldakini izler
  // (Kazanan, Parti, Katilim); Degisim modunda sag harita kazanani gosterir. Parti/Katilim
  // olcegi her haritanin kendi en dusuk-en yuksek degeridir (alttaki aralik yazisi).
  const svg2 = $('#mapSvg2');
  const KARSI = {acik: false, yil: null, kayit: null, geo: null, tur: null, oylama: null,
    ilByPlaka: {}, districtsByPlaka: {}};
  let karsiBileti = 0;
  let ilProjeksiyonu = null; // renderProvinceMap'in son izdusumu (karsilastirma aciksa ortak)

  function karsiEtiket(y){ return (TUR_LABELS[currentTur] || {})[y] || y; }
  function karsiOylama(){ return (DATA && DATA.oylama) || 'baskan'; }
  function karsiUygunYillar(){
    const yillar = (TUR_YEARS[currentTur] || []).filter(y => y !== currentYear);
    return karsiOylama() === 'baskan' ? yillar : yillar.filter(y => OYLAMA_YILLARI.has(y));
  }
  // varsayilan: ayni turdeki bir onceki secim (Degisim moduyla ayni)
  function karsiVarsayilan(){
    const sira = TUR_YEARS[currentTur] || [], uygun = karsiUygunYillar();
    return sira.slice(sira.indexOf(currentYear) + 1).find(y => uygun.includes(y)) || uygun[0] || null;
  }
  function karsiTutarli(){
    return !!KARSI.kayit && KARSI.tur === currentTur && KARSI.yil !== currentYear && KARSI.oylama === karsiOylama();
  }

  async function karsiYukle(yil){
    const bilet = ++karsiBileti;
    const tur = currentTur, oylama = karsiOylama();
    $('#karsiNot').textContent = 'Yükleniyor…';
    const [geo, veri] = await Promise.all([ensureGeoForYear(yil), fetchElection(yil)]);
    const kayit = await oylamaKaydi(yil, veri, oylama, true);
    if(bilet !== karsiBileti) return false;
    if(!kayit){ $('#karsiNot').textContent = 'Bu seçimde aynı oylama yok.'; return false; }
    Object.assign(KARSI, {yil, kayit, geo, tur, oylama, districtsByPlaka: {},
      ilByPlaka: Object.fromEntries(kayit.iller.map(p => [p.plaka, p]))});
    for(const d of kayit.ilceler) (KARSI.districtsByPlaka[d.plaka] ||= []).push(d);
    $('#karsiNot').textContent = '';
    return true;
  }

  // Karsilastirilan secimin bir ildeki poligonlari: sonuclu ilceler (o donemin poligonlariyla),
  // sonucu olmayan bugunku ilceler ve ilce verisi hic yoksa ilin tek parca siniri.
  function karsiIlOgeleri(plaka){
    const gorulen = new Set(), veri = [];
    for(const d of KARSI.districtsByPlaka[plaka] || []){
      if(!d.geomId || gorulen.has(d.geomId) || !districtHasRealData(d)) continue;
      const f = geoFeatureById[d.geomId];
      if(f){ gorulen.add(d.geomId); veri.push({f, d}); }
    }
    const gizli = hiddenModernIdsForProvince(plaka, gorulen);
    const sonuclu = veri.filter(x => !gizli.has(x.f.properties.id));
    const idler = new Set(sonuclu.map(x => x.f.properties.id));
    const bos = sonuclu.length && GEO_ILCE
      ? GEO_ILCE.features.filter(f => f.properties.plaka === plaka && !idler.has(f.properties.id) && !gizli.has(f.properties.id)) : [];
    const tekParca = sonuclu.length ? [] : KARSI.geo.features.filter(f => f.properties.plaka === plaka);
    return {sonuclu, bos, tekParca};
  }
  // renderProvinceMap izdusumu bu kutudan kurar: iki secimin poligonlarinin birlesimi
  function karsiOrtakSinir(feats, plaka){
    if(!KARSI.acik || !karsiTutarli() || !GEO_ILCE) return feats;
    const o = karsiIlOgeleri(plaka);
    return feats.concat(o.sonuclu.map(x => x.f), o.bos, o.tekParca);
  }

  function karsiSeciciDoldur(secili){
    const s = $('#karsiYil'), yillar = karsiUygunYillar();
    const imza = currentTur + '|' + yillar.join(',');
    if(s.dataset.imza !== imza){
      s.innerHTML = yillar.map(y => '<option value="' + y + '">' + escapeHtml(karsiEtiket(y)) + '</option>').join('');
      s.dataset.imza = imza;
    }
    if(secili) s.value = secili;
  }

  // applyMapMode her cizimde ve her mod degisikliginde bunu cagirir
  function karsiCiz(){
    const goster = KARSI.acik && view.level !== 'meclis-ilce';
    $('#karsiSag').hidden = !goster;
    $('#karsiSolBaslik').hidden = !goster;
    $('#haritaCift').classList.toggle('acik', goster);
    if(!goster) return;
    $('#karsiSolBaslik').textContent = karsiEtiket(currentYear);
    if(!karsiTutarli()){
      const istenen = KARSI.tur === currentTur && karsiUygunYillar().includes(KARSI.yil) ? KARSI.yil : karsiVarsayilan();
      if(!istenen){ svg2.innerHTML = ''; $('#winnerLegend2').innerHTML = ''; $('#karsiNot').textContent = 'Karşılaştırılacak başka seçim yok.'; return; }
      karsiSeciciDoldur(istenen);
      karsiYukle(istenen).then(tamam => { if(tamam) karsiYenile(); })
        .catch(() => { $('#karsiNot').textContent = 'Seçim yüklenemedi.'; });
      return;
    }
    karsiSeciciDoldur(KARSI.yil);
    karsiCizSag();
  }
  // il duzeyinde ortak izdusum icin sol harita da yeniden cizilir
  function karsiYenile(){
    if(view.level === 'province') renderProvinceMap(view.plaka);
    else karsiCiz();
    durumuYaz();
  }

  function karsiYol(project, f, sinif){
    const el = document.createElementNS(NS, 'path');
    el.setAttribute('d', geomToPath(project, f.geometry));
    el.setAttribute('class', 'geo-path karsi-path' + (sinif ? ' ' + sinif : ''));
    return el;
  }
  function karsiOlaylar(el, kayit, tikla){
    el.addEventListener('mousemove', e => karsiIpucu(e, kayit));
    el.addEventListener('mouseleave', hideTooltip);
    if(tikla) el.addEventListener('click', tikla);
  }

  function karsiCizSag(){
    svg2.innerHTML = '';
    const varliklar = []; // [kayit, path]
    if(view.level === 'country'){
      for(const f of KARSI.geo.features){
        const plaka = f.properties.plaka, p = KARSI.ilByPlaka[plaka];
        const el = karsiYol(countryProject, f);
        el.dataset.plaka = plaka;
        karsiOlaylar(el, p, ilByPlaka[plaka] ? () => goToProvince(plaka) : null);
        svg2.appendChild(el);
        if(p) varliklar.push([p, el]); else el.setAttribute('fill', 'var(--map-empty)');
      }
      if(selectedPlaka) for(const el of svg2.querySelectorAll('path')) el.classList.toggle('selected', +el.dataset.plaka === selectedPlaka);
    } else {
      const plaka = view.plaka, o = karsiIlOgeleri(plaka);
      const tum = [...o.sonuclu.map(x => x.f), ...o.bos, ...o.tekParca];
      const project = view.level === 'province' && ilProjeksiyonu ? ilProjeksiyonu : computeProjection(tum, PAD);
      for(const f of o.bos){
        const el = karsiYol(project, f, 'geo-path-nodata');
        el.setAttribute('fill', 'var(--map-empty)');
        el.dataset.geomId = f.properties.id;
        karsiOlaylar(el, null, null);
        svg2.appendChild(el);
      }
      for(const f of o.tekParca){
        const p = KARSI.ilByPlaka[plaka], el = karsiYol(project, f);
        el.dataset.plaka = plaka;
        karsiOlaylar(el, p, null);
        svg2.appendChild(el);
        if(p) varliklar.push([p, el]); else el.setAttribute('fill', 'var(--map-empty)');
      }
      for(const {f, d} of o.sonuclu){
        const id = f.properties.id, el = karsiYol(project, f);
        el.dataset.geomId = id;
        karsiOlaylar(el, d, districtByGeomId[id] ? () => openDistrict(plaka, id) : null);
        svg2.appendChild(el);
        varliklar.push([d, el]);
      }
      const secili = view.level === 'mahalle' ? view.geomId : seciliIlce;
      if(secili) for(const el of svg2.querySelectorAll('path')) el.classList.toggle('selected', el.dataset.geomId === secili);
    }
    karsiBoya(varliklar);
  }

  function karsiBoya(varliklar){
    let mod = currentMapMode, not = '';
    if(mod === 'degisim'){ mod = 'winner'; not = 'Değişim modunda sağdaki harita kazananı gösterir.'; }
    if(mod === 'parti' && !varliklar.some(([e]) => e.oy && e.oy[currentMapParty])){
      mod = 'winner'; not = partyShort(currentMapParty) + ' bu seçimde yok; kazanan gösteriliyor.';
    }
    const lejant = $('#winnerLegend2');
    if(mod === 'winner'){
      const sayi = {};
      for(const [e, el] of varliklar){
        el.setAttribute('fill', e.kazanan ? partyColor(e.kazanan) : 'var(--map-empty)');
        if(e.kazanan) sayi[e.kazanan] = (sayi[e.kazanan] || 0) + 1;
      }
      lejant.innerHTML = Object.keys(sayi).sort((a, b) => sayi[b] - sayi[a]).map(n =>
        '<span class="wl-item"><span class="swatch" style="background:' + partyColor(n) + '"></span>' + escapeHtml(partyShort(n)) + '</span>').join('');
    } else {
      const key = mod === 'parti' ? currentMapParty : null;
      const hue = key ? colorToHue(partyColor(key)) : 210;
      const deger = e => key ? (resultPercent(e.oy[key]) ?? 0) : e.katilim;
      const degerler = varliklar.map(([e]) => deger(e)).filter(v => v != null);
      const vmin = Math.min(...degerler), vmax = Math.max(...degerler);
      for(const [e, el] of varliklar){
        const v = deger(e);
        el.setAttribute('fill', v == null ? 'var(--map-empty)' : seqColor(vmax > vmin ? (v - vmin) / (vmax - vmin) : 0.5, hue));
      }
      lejant.innerHTML = degerler.length ? '<div class="seq-legend karsi-seq"><span>' + vmin.toFixed(2) + '%</span><div class="seq-ramp" style="background:linear-gradient(90deg,' +
        seqColor(0, hue) + ',' + seqColor(1, hue) + ')"></div><span>' + vmax.toFixed(2) + '%</span></div>' : '';
      if(degerler.length && !not) not = 'Renk ölçeği her haritanın kendi en düşük ve en yüksek değeridir.';
    }
    $('#karsiNot').textContent = not;
  }

  function karsiIpucu(ev, e){
    if(!e){ tip.innerHTML = '<b>Bu dönem için veri yok</b>'; positionTip(ev); return; }
    let satir;
    if(currentMapMode === 'parti' && e.oy && e.oy[currentMapParty]){
      satir = [partyShort(currentMapParty), resultPercentLabel(e.oy[currentMapParty])];
    } else if(currentMapMode === 'katilim'){
      satir = ['Katılım', e.katilim != null ? '%' + e.katilim.toFixed(2) : '—'];
    } else {
      satir = [e.kazanan ? partyShort(e.kazanan) + ' önde' : 'Kazanan yok', e.kazanan ? resultPercentLabel(e.oy[e.kazanan]) : ''];
    }
    tip.innerHTML = '<b>' + escapeHtml(e.ad) + '</b><div class="row"><span>' + escapeHtml(karsiEtiket(KARSI.yil)) + '</span></div>' +
      '<div class="row"><span>' + escapeHtml(satir[0]) + '</span><span>' + escapeHtml(satir[1]) + '</span></div>';
    positionTip(ev);
  }

  function karsiAcKapa(acik){
    KARSI.acik = acik;
    $('#btnKarsi').classList.toggle('active', acik);
    $('#btnKarsi').setAttribute('aria-pressed', String(acik));
  }
  $('#btnKarsi').addEventListener('click', () => {
    karsiAcKapa(!KARSI.acik);
    if(view.level === 'province') renderProvinceMap(view.plaka); // ortak izdusume gec ya da don
    else karsiCiz();
    durumuYaz();
  });
  $('#karsiYil').addEventListener('change', e => {
    KARSI.yil = e.target.value;
    KARSI.kayit = null;
    karsiCiz();
  });
