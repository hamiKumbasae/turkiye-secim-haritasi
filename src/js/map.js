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

  // ---------------- tarihsel idari sinirlar (sonradan il olan ilceler) ----------------
  // Ardahan/Igdir (1992), Aksaray/Bayburt/Karaman/Kirikkale/Batman/Sirnak/Bartin (1989-91),
  // Karabuk/Kilis/Yalova (1995), Osmaniye (1996), Sakarya/Adiyaman/Nevsehir (1954),
  // Usak (1954) ve Duzce (1999) o yillarda henuz bagimsiz il degildi - o donemin secim
  // haritasinda bos/gri gorunmemeleri icin kendi donemlerinde ait olduklari ile
  // birlestirilmis ozel bir GeoJSON kullaniliyor (bkz. build_historical_geo.py).
  const GEO_ERAS = [ // [esik_yili, dosya_eki] - yil < esik_yili ise bu era kullanilir
    [1954, 'era1950'], [1957, 'era1954'], [1991, 'era1957_1987'],
    [1995, 'era1991'], [1999, 'era1995'], [2002, 'era1999'],
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
      GEO = eras[suffix];
      geoEraCache[suffix] = GEO;
    }
    countryProject = computeProjection(GEO.features, PAD);
  }

  const MECLIS_PROVINCES = new Set([34,35,6,16]);
  function setMeclisOptionVisible(visible){
    $('#optMeclis').hidden = !visible;
    if(!visible && $('#mapMode').value==='meclis2024'){ $('#mapMode').value='winner'; }
  }

  function renderCountryMap(){
    view = {level:'country', plaka:null};
    setMeclisOptionVisible(false);
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
      el.addEventListener('click', ()=>drillIntoProvince(plaka));
      svg.appendChild(el);
      pathByPlaka[plaka]=el;
    }
    $('#mapBreadcrumb').style.display='none';
    $('#mapTitleCountry').style.display='block';
    $('#searchBox').placeholder='İl ara…';
    applyMapMode();
  }

  function mahalleDataForDistrict(geomId){
    const geoRows = MAHALLE_GEO[geomId];
    const voteRows = (MAHALLE_VOTES[currentYear]||{})[geomId];
    if(!geoRows || !voteRows) return null;
    const rows = [];
    for(const osmId in voteRows){
      const g = geoRows[osmId]; if(!g) continue;
      const v = voteRows[osmId];
      rows.push({id:osmId, ad:g.ad, geometry:g.geometry, secmen:v.secmen, sandik:v.sandik, katilim:v.katilim, kazanan:v.kazanan, oy:v.oy});
    }
    return rows.length ? rows : null;
  }

  function renderProvinceMap(plaka){
    view = {level:'province', plaka};
    setMeclisOptionVisible(MECLIS_PROVINCES.has(plaka));
    const feats = districtFeaturesForProvince(plaka);
    const fallbackFeats = GEO.features.filter(f=>f.properties.plaka===plaka);
    const project = computeProjection(feats.length?feats:fallbackFeats, PAD);
    svg.innerHTML = '';
    pathByPlaka = {}; pathByGeomId = {};
    if(!feats.length){
      // Bu yil icin ilce verisi yok (bkz. YEARS_IL_ONLY) - il sinirini tek parca olarak,
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
    for(const f of feats){
      const geomId = f.properties.id;
      const el = document.createElementNS(NS,'path');
      el.setAttribute('d', geomToPath(project, f.geometry));
      el.setAttribute('class','il-path');
      el.dataset.geomId = geomId;
      el.addEventListener('mousemove', e=>showTooltip(e, {kind:'ilce', plaka, geomId}));
      el.addEventListener('mouseleave', hideTooltip);
      el.addEventListener('click', ()=>{
        if($('#mapMode').value==='meclis2024') renderMeclisIlceMap(plaka, geomId);
        else if(mahalleDataForDistrict(geomId)) drillIntoDistrict(plaka, geomId);
        else highlightDistrictRow(geomId);
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

  // ---------------- mahalle (ilce icinde ucuncu seviye) ----------------
  let currentMahalleRows = [];
  let pathByMahalleId = {};
  function drillIntoDistrict(plaka, geomId){
    renderMahalleMap(plaka, geomId);
  }

  function renderMahalleMap(plaka, geomId){
    const rows = mahalleDataForDistrict(geomId) || [];
    if(!rows.length) return;
    setMeclisOptionVisible(false);
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
  function applyMapMode(){
    const mode = $('#mapMode').value;
    $('#seqLegendWrap').style.display = (mode==='winner' || mode==='meclis2024') ? 'none' : 'flex';
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
          if(!districtByGeomId[gid]) el.setAttribute('fill','var(--map-empty)');
        }
      }
      return;
    }
    if(mode==='meclis2024'){
      for(const [gid, el] of Object.entries(pathByGeomId)){
        const m = MECLIS_2024[gid];
        el.setAttribute('fill', m ? partyColor(m.kazanan) : 'var(--map-empty)');
      }
      return;
    }
    let key, hue;
    const isRef = DATA.tur === 'referandum';
    const isCB = DATA.tur === 'cumhurbaskanligi';
    if(mode==='akp'){ key = isRef ? 'Evet' : (isCB ? MAJOR[0] : 'AK Parti'); hue=32; }
    else if(mode==='chp'){ key = isRef ? 'Hayır' : (isCB ? MAJOR[1] : 'CHP'); hue=355; }
    else { key=null; hue=210; }
    const noKatilimData = !key && entities.every(e => e.katilim==null);
    let vals = entities.map(e => key ? (e.oy[key]?e.oy[key].oran:0) : (e.katilim!=null?e.katilim:0));
    const vmin = Math.min(...vals), vmax = Math.max(...vals);
    $('#seqMin').textContent = noKatilimData ? '—' : (vmin||0).toFixed(2)+'%';
    $('#seqMax').textContent = noKatilimData ? '—' : (vmax||0).toFixed(2)+'%';
    $('#seqRamp').style.background = 'linear-gradient(90deg,'+seqColor(0,hue)+','+seqColor(1,hue)+')';
    for(const e of entities){
      const el = pathFor(e); if(!el) continue;
      if(noKatilimData){ el.setAttribute('fill','var(--map-empty)'); continue; }
      const v = key ? (e.oy[key]?e.oy[key].oran:0) : (e.katilim!=null?e.katilim:0);
      const t = vmax>vmin ? (v-vmin)/(vmax-vmin) : 0.5;
      el.setAttribute('fill', seqColor(t,hue));
    }
    if(view.level==='province'){
      for(const [gid, el] of Object.entries(pathByGeomId)){
        if(!districtByGeomId[gid]) el.setAttribute('fill','var(--map-empty)');
      }
    }
  }

