  // ---------------- map projection ----------------
  const VB_W = 900, VB_H = 420, PAD = 14;
  const NS='http://www.w3.org/2000/svg';

  function computeProjection(features, pad){
    let lonMin=1e9,lonMax=-1e9,latMin=1e9,latMax=-1e9;
    function walk(coords, depth){
      if(depth===1){
        const [lon,lat]=coords;
        if(lon<lonMin)lonMin=lon; if(lon>lonMax)lonMax=lon;
        if(lat<latMin)latMin=lat; if(lat>latMax)latMax=lat;
      } else { for(const c of coords) walk(c, depth-1); }
    }
    for(const f of features){
      const depth = f.geometry.type==='Polygon' ? 3 : 4;
      walk(f.geometry.coordinates, depth);
    }
    const latMid = (latMin+latMax)/2 * Math.PI/180;
    const cosLat = Math.cos(latMid);
    const lonSpan = Math.max((lonMax-lonMin)*cosLat, 1e-6), latSpan = Math.max(latMax-latMin, 1e-6);
    const availW = VB_W-2*pad, availH = VB_H-2*pad;
    const scale = Math.min(availW/lonSpan, availH/latSpan);
    const usedW = lonSpan*scale, usedH = latSpan*scale;
    const offX = pad + (availW-usedW)/2, offY = pad + (availH-usedH)/2;
    function project([lon,lat]){
      const x = offX + (lon-lonMin)*cosLat*scale;
      const y = offY + (latMax-lat)*scale;
      return [x.toFixed(2), y.toFixed(2)];
    }
    return project;
  }
  function ringToPath(project, ring){ return ring.map((pt,i)=> (i===0?'M':'L')+project(pt).join(',')).join('')+'Z'; }
  function geomToPath(project, geom){
    if(geom.type==='Polygon') return geom.coordinates.map(r=>ringToPath(project,r)).join(' ');
    return geom.coordinates.map(poly=>poly.map(r=>ringToPath(project,r)).join(' ')).join(' ');
  }

  const svg = $('#mapSvg');
  let countryProject = computeProjection(GEO.features, PAD);
  let pathByPlaka = {};
  let pathByGeomId = {};
  let view = {level:'country', plaka:null};
  let currentMapMode = 'winner'; // 'winner' | 'katilim' | 'parti'
  let currentMapParty = null;

  // ---------------- tarihsel idari sinirlar (sonradan il olan ilceler) ----------------
  // Ardahan/Igdir (1992), Aksaray/Bayburt/Karaman/Kirikkale/Batman/Sirnak/Bartin (1989-91),
  // Karabuk/Kilis/Yalova (1995), Osmaniye (1996), Sakarya/Adiyaman/Nevsehir (1954),
  // Usak (1954) ve Duzce (1999) o yillarda henuz bagimsiz il degildi - o donemin secim
  // haritasinda bos/gri gorunmemeleri icin kendi donemlerinde ait olduklari ile
  // birlestirilmis ozel bir GeoJSON kullaniliyor (bkz. build_historical_geo.py).
  // era1957_1965/era1957_1987/era1991/era1994: secim verisindeki ilce-il bagliligindan
  // (scripts/pipelines/historical_geo/build_il_sinirlari.py); 1957 ilce verisi olmadigi icin
  // era1957_1987'de, 1958-1965 Kaynarca'nin Kocaeli'de oldugu era1957_1965'te.
  const GEO_ERAS = [ // [esik_yili, dosya_eki] - yil < esik_yili ise (ilk eslesen) bu era kullanilir
    [1954, 'era1950'], [1957, 'era1954'], [1958, 'era1957_1987'], [1966, 'era1957_1965'],
    [1991, 'era1957_1987'], [1994, 'era1991'], [1995, 'era1994'], [1999, 'era1995'], [2002, 'era1999'],
  ];
  function eraSuffixForYear(year){
    const y = parseInt(String(year).match(/^\d{4}/)[0], 10);
    for(const [threshold, suffix] of GEO_ERAS){ if(y < threshold) return suffix; }
    return null; // 2002+ -> modern (GEO_MODERN), birlestirme gerekmiyor
  }
  const GEO_MODERN = GEO;
  const geoEraCache = {};
  let currentGeoEra = null;
  async function ensureGeoForYear(year){
    const suffix = eraSuffixForYear(year);
    if(suffix === currentGeoEra) return;
    currentGeoEra = suffix;
    if(suffix === null){
      GEO = GEO_MODERN;
    } else if(geoEraCache[suffix]){
      GEO = geoEraCache[suffix];
    } else {
      const eras = await loadEmbeddedCached("eras", {});
      geoEraCache[suffix] = eras[suffix];
      if(currentGeoEra !== suffix) return; // bu arada baska donem secildi
      GEO = eras[suffix];
    }
    countryProject = computeProjection(GEO.features, PAD);
  }

  // 2024 yerel seciminde ilce meclisi verisi olan 4 buyuksehir - artik bir
  // harita modu degil, sag paneldeki "İlçe Meclisi" gorunum sekmesinin hangi
  // illerde gorunecegini belirlemek icin detail-panel.js tarafindan kullaniliyor.
  const MECLIS_PROVINCES = new Set([34,35,6,16]);

  // ---------------- harita modu / parti secici ----------------
  function populatePartySelect(){
    const sel = $('#partySelect'); sel.innerHTML='';
    for(const name of MAJOR){
      const opt = document.createElement('option');
      opt.value = name; opt.textContent = PARTY[name] ? PARTY[name].short : name;
      sel.appendChild(opt);
    }
    currentMapParty = MAJOR[0] || null;
    sel.value = currentMapParty;
  }
  async function setMapMode(mode){
    if(mode==='degisim' && !(await ensureOnceki())) return;
    currentMapMode = mode;
    $$('#modeGroup button').forEach(b=>b.classList.toggle('active', b.dataset.mode===mode));
    $('#partySelect').style.display = (mode==='parti' || mode==='degisim') ? '' : 'none';
    applyMapMode();
  }
  // council_seats/mixed (1950/1955 yerel): oy oranlari ile sandalye paylari
  // AYNI renk skalasinda karsilastirilamaz (biri gercek oy yuzdesi, digeri
  // meclis sandalye payi) - v1 icin bu sadece "Parti" modunu bu yillarda
  // gizler (bkz. son inceleme), yeni bir "Meclis Payı" modu EKLEMEZ.
  function partiModeAvailable(){
    return DATA.resultBasis !== 'council_seats' && DATA.resultBasis !== 'mixed';
  }
  function resetMapModeUI(){
    populatePartySelect();
    $('#modeGroup button[data-mode="parti"]').hidden = !partiModeAvailable();
    ONCEKI = null;
    $('#modeGroup button[data-mode="degisim"]').hidden = !partiModeAvailable() || !oncekiSecimAnahtari();
    setMapMode('winner');
  }
  $$('#modeGroup button').forEach(b=>{
    b.addEventListener('click', ()=> setMapMode(b.dataset.mode));
  });
  $('#partySelect').addEventListener('change', e=>{ currentMapParty = e.target.value; applyMapMode(); });

  // hex/renk stringini hue'ya cevirir (parti oran gradyani icin) - canvas
  // normalizasyonu kullanir, boylece partiler.json'daki her renk formati
  // (hex, rgb, isim) guvenilir sekilde HSL hue'ya donusur.
  let _hueCanvasCtx = null;
  function colorToHue(colorStr){
    if(!_hueCanvasCtx) _hueCanvasCtx = document.createElement('canvas').getContext('2d');
    _hueCanvasCtx.fillStyle = '#000'; _hueCanvasCtx.fillStyle = colorStr;
    const norm = _hueCanvasCtx.fillStyle;
    if(!norm.startsWith('#') || norm.length<7) return 210;
    const r = parseInt(norm.slice(1,3),16)/255, g = parseInt(norm.slice(3,5),16)/255, b = parseInt(norm.slice(5,7),16)/255;
    const max=Math.max(r,g,b), min=Math.min(r,g,b);
    let h=0;
    if(max!==min){
      const d = max-min;
      if(max===r) h = ((g-b)/d + (g<b?6:0));
      else if(max===g) h = (b-r)/d + 2;
      else h = (r-g)/d + 4;
      h *= 60;
    }
    return Math.round(h);
  }

  function renderWinnerLegend(entities){
    const counts = {};
    for(const e of entities){ if(e.kazanan) counts[e.kazanan] = (counts[e.kazanan]||0)+1; }
    const names = Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
    const wrap = $('#winnerLegend');
    if(!names.length){ wrap.innerHTML=''; return; }
    wrap.innerHTML = names.map(n=>
      '<span class="wl-item"><span class="swatch" style="background:'+partyColor(n)+'"></span>'+(PARTY[n]?PARTY[n].short:n)+'</span>'
    ).join('');
  }

  function renderCountryMap(){
    view = {level:'country', plaka:null};
    svg.innerHTML = '';
    pathByPlaka = {}; pathByGeomId = {};
    for(const f of GEO.features){
      const plaka = f.properties.plaka;
      const el = document.createElementNS(NS,'path');
      el.setAttribute('d', geomToPath(countryProject, f.geometry));
      el.setAttribute('class','il-path');
      el.dataset.plaka = plaka;
      el.addEventListener('mousemove', e=>showTooltip(e, {kind:'il', plaka}));
      el.addEventListener('mouseleave', hideTooltip);
      el.addEventListener('click', ()=>goToProvince(plaka));
      svg.appendChild(el);
      pathByPlaka[plaka]=el;
    }
    $('#mapBreadcrumb').style.display='none';
    $('#mapTitleCountry').style.display='block';
    $('#searchBox').placeholder='İl ara…';
    applyMapMode();
  }

  // Ucuz, senkron on-kontrol: bu ilcenin HIC mahalle poligonu var mi (yildan
  // bagimsiz, MAHALLE_GEO_IDS hep eager yuklu). Gercek oy verisi (yil bazli,
  // lazy) icin mahalleDataForDistrict'i await edin.
  function mahalleGeoExistsForDistrict(geomId){
    return MAHALLE_GEO_IDS.has(geomId);
  }

  async function mahalleDataForDistrict(geomId){
    if(!MAHALLE_GEO_IDS.has(geomId) || DATA.oylama) return null; // mahalle oylari yalniz baskanlik secimi icin var
    const votesForYear = await loadMahalleVotesForYear(currentYear);
    const voteRows = votesForYear[geomId];
    if(!voteRows) return null;
    // poligonlar yalniz bu yil/ilce icin gercekten mahalle oyu varsa cozulur
    const geoRows = (await loadMahalleGeo())[geomId];
    if(!geoRows) return null;
    const rows = [];
    for(const osmId in voteRows){
      const g = geoRows[osmId]; if(!g) continue;
      const v = voteRows[osmId];
      rows.push({id:osmId, ad:g.ad, geometry:g.geometry, secmen:v.secmen, sandik:v.sandik, katilim:v.katilim, kazanan:v.kazanan, oy:v.oy});
    }
    return rows.length ? rows : null;
  }

  // Bir kac secili (simdilik SADECE tek-ebeveynli, yuksek-guven arastirmayla
  // dogrulanmis) ilce icin gercek tarihsel poligon birlesimi var (bkz.
  // geo/historical/district_splits.json + turkiye_ilce_sinirlari_hist_splits.geojson,
  // orn. HIST-Istanbul-Buyukcekmece = Buyukcekmece+Beylikduzu). Bu secimde
  // o birlesik (sentetik) id GERCEKTEN kullanildiysa (veri satirinin geomId'si
  // ona esitse), birlesimin PARCASI olan modern id'leri (orn. Beylikduzu'nun
  // kendi modern poligonu) AYRICA "veri yok" katmaninda gostermiyoruz -
  // yoksa ayni alan iki kez (bir kere dogru renkli birlesim, bir kere de
  // notr/gri kendi parcasi olarak) cizilmis olur.
  function hiddenModernIdsForProvince(plaka, dataGeomIds){
    const hidden = new Set();
    const splits = DISTRICT_SPLITS[String(plaka)] || [];
    for(const entry of splits){
      if(dataGeomIds.has(entry.syntheticId)){
        for(const hid of entry.hideIds) hidden.add(hid);
      }
    }
    return hidden;
  }

  // 'Veri yok' kalan modern ilce o secimde henuz ayri ilce degilse (kurulus kanunu,
  // kaynak ilceler: geo/historical/idari/harita_notlari.json) taranir ve nedeni yazilir.
  function gecisNotu(geomId){
    const secim = ((HARITA_NOTLARI && HARITA_NOTLARI.secimler) || {})[currentYear];
    if(!secim || !(geomId in secim)) return null;
    const n = HARITA_NOTLARI.ilceler[geomId];
    return n ? Object.assign({girmedi: secim[geomId] === 1}, n) : null;
  }
  function gecisNotuHtml(n){
    // kisa: kurulus yili + kanun, tek cumlelik neden
    const yil = n.tarih ? n.tarih.slice(0, 4) : '';
    const kanun = n.kanun ? (/^KHK/.test(n.kanun) ? n.kanun : 'Kanun ' + n.kanun) : '';
    const adlar = (n.kaynaklar || []).map(k => k[0]);
    let neden;
    if(n.durum === 'kanun_cok_kaynak' && adlar.length) neden = 'Ayrıldığı ilçeler: ' + adlar.join(', ');
    else if(n.durum === 'kanun_tek_kaynak' && adlar.length) neden = 'O dönem bağlı olduğu ilçe: ' + adlar[0];
    else if(n.durum === 'merkez_ilce') neden = 'Eski Merkez ilçenin devamı';
    else neden = 'Hangi ilçeden ayrıldığı bilinmiyor';
    const kurulus = 'Kuruluş: ' + yil + (kanun ? ' (' + kanun + ')' : '') + (n.girmedi ? ' · bu seçime ayrı girmedi' : ' · bu seçimde henüz yoktu');
    return '<b>' + n.ad + '</b>' + '<div class="row"><span>' + kurulus + '</span></div><div class="row"><span>' + neden + '</span></div>';
  }


  function renderProvinceMap(plaka){
    view = {level:'province', plaka};
    const allDataFeats = districtFeaturesForProvince(plaka);
    // Sadece GERCEKTEN sonucu olan ilceler tiklanabilir/etkilesimli olsun (bkz.
    // son inceleme: veri olmayan yerde yaniltici bir "tiklama alani" gorunmemeli).
    const dataFeats = allDataFeats.filter(f => districtHasRealData(districtByGeomId[f.properties.id]));
    const dataGeomIds = new Set(dataFeats.map(f=>f.properties.id));
    const hiddenByMerge = hiddenModernIdsForProvince(plaka, dataGeomIds);
    // Bu ilin GUNCEL (modern) tum ilce sinirlari - SADECE bu il/yil icin
    // GERCEKTEN kismi ilce verisi varsa (dataFeats.length>0, yani bazi
    // ilceler biliniyor bazilari bilinmiyor) devreye girer: bilinmeyenleri
    // notr/TIKLANAMAZ bir alt katman olarak gosterir (orn. 2008 oncesi
    // Istanbul'da Ataşehir/Sancaktepe vb.) - BILEREK gercek tarihsel
    // sinirlari "uydurmuyor". Eger bu il/yil icin HIC ilce verisi yoksa
    // (dataFeats bos - orn. 1950/1954/1957 genel, sadece il-duzeyi
    // kaynak), bu katman HIC HESAPLANMAZ/GOSTERILMEZ - asagidaki "tek
    // parca il" fallback'i kullanilir (bkz. son inceleme: bilmedigimiz
    // bir seyi 39 parcaya bolup "veri yok" diye gostermek de yaniltici -
    // sadece GERCEKTEN KISMEN bildigimiz durumlarda parcali gosterim yapilir).
    const modernFeats = dataFeats.length ? GEO_ILCE.features.filter(f=>f.properties.plaka===plaka) : [];
    const noDataFeats = modernFeats.filter(f=>!dataGeomIds.has(f.properties.id) && !hiddenByMerge.has(f.properties.id));
    const fallbackFeats = GEO.features.filter(f=>f.properties.plaka===plaka);
    const allFeats = dataFeats.length ? [...dataFeats, ...noDataFeats] : fallbackFeats;
    const project = computeProjection(allFeats.length?allFeats:fallbackFeats, PAD);
    svg.innerHTML = '';
    pathByPlaka = {}; pathByGeomId = {};
    if(noDataFeats.some(f=>gecisNotu(f.properties.id))){
      const defs = document.createElementNS(NS,'defs');
      defs.innerHTML = '<pattern id="hatchGecis" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        + '<rect width="6" height="6"/><line x1="0" y1="0" x2="0" y2="6"/></pattern>';
      svg.appendChild(defs);
    }
    if(!dataFeats.length){
      // Bu yil icin ilce verisi hic yok - il sinirini tek parca olarak,
      // ilin kendi kazanan rengiyle goster.
      const p = ilByPlaka[plaka];
      for(const f of fallbackFeats){
        const el = document.createElementNS(NS,'path');
        el.setAttribute('d', geomToPath(project, f.geometry));
        el.setAttribute('class','il-path');
        el.setAttribute('fill', p && p.kazanan ? partyColor(p.kazanan) : 'var(--map-empty)');
        el.dataset.plaka = plaka;
        el.addEventListener('mousemove', e=>showTooltip(e, {kind:'il', plaka}));
        el.addEventListener('mouseleave', hideTooltip);
        svg.appendChild(el);
        pathByPlaka[plaka]=el;
      }
    }
    for(const f of noDataFeats){
      const geomId = f.properties.id;
      const el = document.createElementNS(NS,'path');
      el.setAttribute('d', geomToPath(project, f.geometry));
      const not = gecisNotu(geomId);
      el.setAttribute('class', not ? 'il-path il-path-nodata il-path-gecis' : 'il-path il-path-nodata');
      el.setAttribute('fill', not ? 'url(#hatchGecis)' : 'var(--map-empty)');
      el.dataset.geomId = geomId;
      el.addEventListener('mousemove', e=>{
        if(not){ tip.innerHTML = gecisNotuHtml(not); positionTip(e); return; }
        let d = districtByGeomId[geomId];
        if(!d){ // tarihsel birlesim poligonunun parcasi: birlesimin satirindaki not
          const e = (DISTRICT_SPLITS[String(plaka)] || []).find(x => x.hideIds.includes(geomId) && districtByGeomId[x.syntheticId]);
          if(e) d = districtByGeomId[e.syntheticId];
        }
        tip.innerHTML = '<b>'+(d?d.ad:'')+'</b><div class="row"><span>'+((d && d.not) || 'Bu dönem için veri yok')+'</span></div>';
        positionTip(e);
      });
      el.addEventListener('mouseleave', hideTooltip);
      svg.appendChild(el);
      pathByGeomId[geomId]=el;
    }
    for(const f of dataFeats){
      const geomId = f.properties.id;
      const el = document.createElementNS(NS,'path');
      el.setAttribute('d', geomToPath(project, f.geometry));
      el.setAttribute('class','il-path');
      el.dataset.geomId = geomId;
      el.addEventListener('mousemove', e=>showTooltip(e, {kind:'ilce', plaka, geomId}));
      el.addEventListener('mouseleave', hideTooltip);
      el.addEventListener('click', async ()=>{
        const d = districtByGeomId[geomId];
        // Mahalle haritasina inerken bile once ilcenin KENDI verisini panelde
        // goster (bkz. son inceleme: tiklama, eski/genel veriyi degil TIKLANAN
        // yerin verisini gostermeli) - kullanici sonra istedigi mahalleye
        // tiklayip daha da detaya inebilir.
        if(d) selectDistrict(d, plaka);
        if(mahalleGeoExistsForDistrict(geomId)){
          const rows = await mahalleDataForDistrict(geomId);
          if(rows){ renderMahalleMap(plaka, geomId, rows); return; }
        }
      });
      svg.appendChild(el);
      pathByGeomId[geomId]=el;
    }
    const p = ilByPlaka[plaka];
    $('#mapBreadcrumb').style.display='flex';
    $('#btnBackProvince').style.display='none';
    $('#mapTitleCountry').style.display='none';
    $('#mapBreadcrumbName').textContent = p ? (p.ad+' — İlçe Sonuçları') : '';
    $('#searchBox').value='';
    $('#searchBox').placeholder='İlçe ara…';
    applyMapMode();
  }

  function drillIntoProvince(plaka){
    renderProvinceMap(plaka);
    selectProvince(plaka);
  }

  // Tiklanan/aranan ile HANGI gorunume gidilecegini tek yerden karar verir:
  // ilce verisi varsa normal ilce-haritasina in (drillIntoProvince); yoksa
  // (o il/yil icin hic ilce-duzeyi veri bilmiyorsak) HARITA ulke goruminde
  // KALIR - olmayan bir "ilce gorunumu"ne (39/81 parcali ya da tek-parca-il
  // gosterip "İlçe Sonuçları" baslikli sahte bir alt seviye) hic gecilmez,
  // sadece sag panelde ilin kendi sonucu gosterilir (bkz. son inceleme).
  function goToProvince(plaka){
    if(provinceHasDistrictData(plaka)){
      drillIntoProvince(plaka);
    } else {
      if(view.level!=='country') renderCountryMap();
      selectProvince(plaka);
    }
  }

  // ---------------- mahalle (ilce icinde ucuncu seviye) ----------------
  let currentMahalleRows = [];
  let pathByMahalleId = {};

  // rows: mahalleDataForDistrict(geomId)'nin (async, cagiran yerde await
  // edilmis) sonucu — burada tekrar hesaplanmiyor, cagri yerinde (renderProvinceMap'in
  // click handler'i) zaten cozulmus olarak veriliyor.
  function renderMahalleMap(plaka, geomId, rows){
    if(!rows || !rows.length) return;
    view = {level:'mahalle', plaka, geomId};
    currentMahalleRows = rows;
    const feats = rows.map(r=>({geometry:r.geometry}));
    const project = computeProjection(feats, PAD);
    svg.innerHTML = '';
    pathByMahalleId = {};
    for(const r of rows){
      const el = document.createElementNS(NS,'path');
      el.setAttribute('d', geomToPath(project, r.geometry));
      el.setAttribute('class','il-path');
      el.dataset.mahalleId = r.id;
      el.addEventListener('mousemove', e=>showTooltip(e, {kind:'mahalle', mahalleId:r.id}));
      el.addEventListener('mouseleave', hideTooltip);
      el.addEventListener('click', ()=>selectMahalle(r, plaka, geomId));
      svg.appendChild(el);
      pathByMahalleId[r.id]=el;
    }
    const d = districtByGeomId[geomId];
    const p = ilByPlaka[plaka];
    $('#mapBreadcrumb').style.display='flex';
    $('#btnBackProvince').style.display='inline-flex';
    $('#mapTitleCountry').style.display='none';
    $('#mapBreadcrumbName').textContent = (p?p.ad:'')+' — '+(d?d.ad:'')+' — Mahalle Sonuçları';
    $('#searchBox').value='';
    $('#searchBox').placeholder='Mahalle ara…';
    applyMapMode();
  }

  // ---------------- map coloring modes ----------------
  function seqColor(t, hue){
    // t in [0,1] -> light..dark single-hue ramp
    const dark = document.documentElement.getAttribute('data-theme')==='dark' ||
      (document.documentElement.getAttribute('data-theme')!=='light' && matchMedia('(prefers-color-scheme: dark)').matches);
    const l = dark ? (78 - t*45) : (92 - t*52);
    const s = dark ? 55 : 60;
    return 'hsl('+hue+' '+s+'% '+l+'%)';
  }
  // oy satiri olmayan ilce poligonu: henuz ayri ilce degilse tarali, degilse notr
  function bosDolgu(geomId){ return gecisNotu(geomId) ? 'url(#hatchGecis)' : 'var(--map-empty)'; }
  function applyMapMode(){
    const mode = currentMapMode;
    $('#seqLegendWrap').style.display = (mode==='winner') ? 'none' : 'flex';
    $('#seqNote').hidden = mode!=='degisim';
    const entities = view.level==='country' ? DATA.iller : (view.level==='mahalle' ? currentMahalleRows : (districtsByPlaka[view.plaka]||[]));
    const pathFor = view.level==='country' ? (e=>pathByPlaka[e.plaka])
      : (view.level==='mahalle' ? (e=>pathByMahalleId[e.id]) : (e=>e.geomId && pathByGeomId[e.geomId]));

    if(mode==='winner'){
      for(const e of entities){
        const el = pathFor(e); if(!el) continue;
        el.setAttribute('fill', e.kazanan ? partyColor(e.kazanan) : 'var(--map-empty)');
      }
      // districts with geometry but no matched vote row -> neutral fill
      if(view.level==='province'){
        for(const [gid, el] of Object.entries(pathByGeomId)){
          if(!districtByGeomId[gid]) el.setAttribute('fill', bosDolgu(gid));
        }
      }
      renderWinnerLegend(entities);
      return;
    }
    $('#winnerLegend').innerHTML='';
    if(mode==='degisim'){ applyDegisim(entities, pathFor); return; }
    let key, hue;
    if(mode==='parti'){ key = currentMapParty; hue = key ? colorToHue(partyColor(key)) : 210; }
    else { key=null; hue=210; }
    const noKatilimData = !key && entities.every(e => e.katilim==null);
    let vals = entities.map(e => key ? (resultPercent(e.oy[key]) ?? 0) : (e.katilim!=null?e.katilim:0));
    const vmin = Math.min(...vals), vmax = Math.max(...vals);
    $('#seqMin').textContent = noKatilimData ? '—' : (vmin||0).toFixed(2)+'%';
    $('#seqMax').textContent = noKatilimData ? '—' : (vmax||0).toFixed(2)+'%';
    $('#seqRamp').style.background = 'linear-gradient(90deg,'+seqColor(0,hue)+','+seqColor(1,hue)+')';
    for(const e of entities){
      const el = pathFor(e); if(!el) continue;
      if(noKatilimData){ el.setAttribute('fill','var(--map-empty)'); continue; }
      const v = key ? (resultPercent(e.oy[key]) ?? 0) : (e.katilim!=null?e.katilim:0);
      const t = vmax>vmin ? (v-vmin)/(vmax-vmin) : 0.5;
      el.setAttribute('fill', seqColor(t,hue));
    }
    if(view.level==='province'){
      for(const [gid, el] of Object.entries(pathByGeomId)){
        if(!districtByGeomId[gid]) el.setAttribute('fill', bosDolgu(gid));
      }
    }
  }

  // ---------------- degisim: onceki secime gore oy orani farki ----------------
  // Ayni turdeki bir onceki secim (TUR_YEARS yeniden eskiye sirali). Il duzeyinde ayni plaka,
  // ilce duzeyinde ayni poligon (geomId; tarihsel birlesimler kendi kimligini tasir, yani sinir
  // degistiyse eslesmez) karsilastirilir.
  let ONCEKI = null; // {year, data, ilByPlaka, ilceByGeomId}
  let oncekiTicket = 0;
  function oncekiSecimAnahtari(){
    const order = TUR_YEARS[currentTur] || [];
    const i = order.indexOf(currentYear);
    return i >= 0 && i + 1 < order.length ? order[i + 1] : null;
  }
  // true: ONCEKI hazir; false: onceki secim yok, yuklenemedi ya da bu arada secim degisti
  async function ensureOnceki(){
    const year = oncekiSecimAnahtari();
    if(!year) return false;
    const oylama = DATA.oylama || 'baskan';
    if(ONCEKI && ONCEKI.year === year && ONCEKI.oylama === oylama) return true;
    const ticket = ++oncekiTicket, yearTicket = loadYearTicket;
    const stillCurrent = () => ticket === oncekiTicket && yearTicket === loadYearTicket;
    // oylamaKaydi currentOylama'yi degistirebildigi icin burada dogrudan: onceki secimde ayni
    // meclis oylamasi yoksa baskanlik kaydi kullanilir
    const ham = await fetchElection(year);
    const kayit = (ham.tur === 'yerel' && oylama !== 'baskan' && OYLAMA_YILLARI.has(year) && await loadOylama(year, oylama)) || ham;
    if(!stillCurrent()) return false;
    const ilceByGeomId = {};
    for(const d of kayit.ilceler || []){ if(d.geomId) ilceByGeomId[d.geomId] = d; }
    ONCEKI = {year, oylama: kayit.oylama || 'baskan', data: kayit, ilceByGeomId,
              ilByPlaka: Object.fromEntries(kayit.iller.map(p => [p.plaka, p]))};
    return true;
  }
  function oncekiKarsiligi(e){
    if(!ONCEKI) return null;
    if(view.level === 'country') return ONCEKI.ilByPlaka[e.plaka] || null;
    if(view.level === 'province') return (e.geomId && ONCEKI.ilceByGeomId[e.geomId]) || null;
    return null; // mahalle duzeyinde karsilastirma yok
  }
  // yuzde puan farki; parti ya da yer onceki secimde yoksa null
  function degisimDegeri(e, key){
    const o = oncekiKarsiligi(e);
    if(!o || !o.oy || !e.oy) return null;
    const a = resultPercent(e.oy[key]), b = resultPercent(o.oy[key]);
    return a == null || b == null ? null : a - b;
  }
  function divColor(t, hueArti, hueEksi){
    // t in [-1,1]: eksi taraf zit renk, arti taraf parti rengi, 0 acik notr
    const dark = document.documentElement.getAttribute('data-theme')==='dark' ||
      (document.documentElement.getAttribute('data-theme')!=='light' && matchMedia('(prefers-color-scheme: dark)').matches);
    const m = Math.min(1, Math.abs(t));
    const l = dark ? (30 + (1 - m) * 40) : (94 - m * 54);
    return 'hsl(' + (t < 0 ? hueEksi : hueArti) + ' ' + Math.round(m * 65) + '% ' + l + '%)';
  }
  function puan(v){ return (v > 0 ? '+' : v < 0 ? '−' : '±') + Math.abs(v).toFixed(1).replace('.', ',') + ' puan'; }
  function applyDegisim(entities, pathFor){
    const key = currentMapParty;
    const hue = key ? colorToHue(partyColor(key)) : 210, hueEksi = (hue + 180) % 360;
    const vals = new Map();
    for(const e of entities){ const v = key ? degisimDegeri(e, key) : null; if(v != null) vals.set(e, v); }
    const m = Math.max(1, ...[...vals.values()].map(Math.abs));
    $('#seqMin').textContent = '−' + m.toFixed(1).replace('.', ',');
    $('#seqMax').textContent = '+' + m.toFixed(1).replace('.', ',');
    $('#seqRamp').style.background = 'linear-gradient(90deg,' + divColor(-1, hue, hueEksi) + ',' + divColor(0, hue, hueEksi) + ',' + divColor(1, hue, hueEksi) + ')';
    for(const e of entities){
      const el = pathFor(e); if(!el) continue;
      el.setAttribute('fill', vals.has(e) ? divColor(vals.get(e) / m, hue, hueEksi) : 'var(--map-empty)');
    }
    if(view.level==='province'){
      for(const [gid, el] of Object.entries(pathByGeomId)){
        if(!districtByGeomId[gid]) el.setAttribute('fill', bosDolgu(gid));
      }
    }
    const once = ONCEKI ? TUR_LABELS[currentTur][ONCEKI.year] : '';
    let not = escapeHtml(partyShort(key || '')) + ': ' + escapeHtml(once) + ' → ' + escapeHtml(TUR_LABELS[currentTur][currentYear]) + ' oy oranı farkı (yüzde puan).';
    if(view.level === 'mahalle') not = 'Mahalle düzeyinde önceki seçimle karşılaştırma yok.';
    else if(!vals.size) not += ' Bu parti önceki seçimde yoktu ya da sonuçları eşleşmiyor.';
    else if(view.level === 'country' && eraSuffixForYear(ONCEKI.year) !== eraSuffixForYear(currentYear))
      not += ' İki seçim arasında il sınırları değişti; yeni kurulan illerin ayrıldığı illerde fark kısmen sınır değişikliğindendir.';
    else if(view.level === 'province') not += ' Sınırı değişen ilçeler (gri) karşılaştırılmaz.';
    $('#seqNote').innerHTML = not;
  }
