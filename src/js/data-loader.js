  const $ = (s,el=document) => el.querySelector(s);
  const $$ = (s,el=document) => [...el.querySelectorAll(s)];
  const fmt = n => n==null ? '—' : n.toLocaleString('tr-TR');
  const ESCAPE_MAP = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ESCAPE_MAP[c]);
  const fmt1 = n => n==null ? '—' : n.toLocaleString('tr-TR',{maximumFractionDigits:1,minimumFractionDigits:1});

  // Gomulu veri window.__EMBEDDED_GZ__ altinda gzip+base64 olarak tutuluyor (boyutu
  // ~5 kat kucultmek icin) - DecompressionStream (tum modern tarayicilarda var) ile aciliyor.
  async function loadEmbedded(key, fallback){
    const b64 = window.__EMBEDDED_GZ__ && window.__EMBEDDED_GZ__[key];
    if(!b64) return fallback;
    const bytes = Uint8Array.from(atob(b64), c=>c.charCodeAt(0));
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    const text = await new Response(stream).text();
    return JSON.parse(text);
  }
  const EMBEDDED_CACHE = {};
  async function loadEmbeddedCached(key, fallback){
    if(!(key in EMBEDDED_CACHE)) EMBEDDED_CACHE[key] = await loadEmbedded(key, fallback);
    return EMBEDDED_CACHE[key];
  }

  // Acilista yalniz gosterilen secim (fetchElection) ve harita sinirlari cozulur; mahalle poligonlari
  // (MAHALLE_GEO, ~17MB acik) ilk mahalleye inilince (loadMahalleGeo).
  let BUNDLE, PARTILER, GEO, GEO_ILCE, GEO_ILCE_HIST, MAHALLE_GEO_IDS, MECLIS_2024, MAHALLE_COVERAGE, DISTRICT_SPLITS, HARITA_NOTLARI;
  try{
    // mahalle oylari (mahalle_votes_<yil>.json) ve poligonlari (mahalle_geo.json) da
    // yalniz kullanici bir ilcenin mahallelerine inince lazy-load edilir (bkz. map.js:
    // mahalleDataForDistrict).
    [PARTILER, GEO, GEO_ILCE, GEO_ILCE_HIST, MAHALLE_GEO_IDS, MECLIS_2024, MAHALLE_COVERAGE, DISTRICT_SPLITS, HARITA_NOTLARI] = await Promise.all([
      loadEmbeddedCached("partiler.json"),
      loadEmbeddedCached("turkiye_il_sinirlari.geojson"),
      loadEmbeddedCached("turkiye_ilce_sinirlari.geojson"),
      loadEmbeddedCached("turkiye_ilce_sinirlari_hist_splits.geojson"),
      loadEmbeddedCached("mahalle_geo_ids.json", []).then(ids => new Set(ids)),
      loadEmbeddedCached("meclis_2024.json", {}),
      loadEmbeddedCached("mahalle_coverage.json", {}),
      loadEmbeddedCached("district_splits.json", {}),
      loadEmbeddedCached("harita_notlari.json", {})
    ]);
  }catch(e){
    document.body.innerHTML = '<div class="wrap"><p>Veri yüklenemedi: '+e+'</p></div>';
    return;
  }
  BUNDLE = {partiler: PARTILER, secimler: {}};
  async function fetchElection(year){
    if(!(year in BUNDLE.secimler)) BUNDLE.secimler[year] = await loadEmbeddedCached("secim_"+year+".json");
    return BUNDLE.secimler[year];
  }
  function loadMahalleGeo(){
    return loadEmbeddedCached("mahalle_geo.json", {});
  }
  function loadMahalleVotesForYear(year){
    return loadEmbeddedCached("mahalle_votes_"+year+".json", {});
  }
  const geoFeatureById = {};
  for(const f of GEO_ILCE.features){ geoFeatureById[f.properties.id] = f; }
  for(const f of GEO_ILCE_HIST.features){ geoFeatureById[f.properties.id] = f; }

  // Ilcenin gosterilecegi poligon, o ilcenin BUGUNKU plaka koduna gore degil, o secim
  // yilinda DATA.ilceler'de kayitli gercek idari bagliliga (plaka) ve o kaydin geomId'sine
  // gore bulunur. Orn. Kirikkale/Karaman/Bartin/Ardahan/Safranbolu gibi sonradan il olan ya
  // da baska bir ile baglanan ilceler, o donemde baska bir ile bagliyken (1984/89'da
  // Kirikkale Ankara'ya, Safranbolu Zonguldak'a bagliydi) o eski ilin haritasinda kendi
  // (dogru sekilli) modern poligonuyla gosterilir - bugunku plaka koduna gore filtrelemek
  // bu ilceleri (ve Antalya Merkez gibi sonradan bolunen ilceleri) haritadan tamamen
  // dusuruyordu, oysa veri seti zaten dogru donemin ilce/geomId eslesmesini iceriyor.
  function districtFeaturesForProvince(plaka){
    const rows = districtsByPlaka[plaka] || [];
    const feats = [];
    const seen = new Set();
    for(const d of rows){
      if(!d.geomId || seen.has(d.geomId)) continue;
      const f = geoFeatureById[d.geomId];
      if(f){ seen.add(d.geomId); feats.push(f); }
    }
    return feats;
  }
  // yerel secim meclis kayitlari (il genel meclisi / belediye meclisi): bkz. election-config.js
  async function loadOylama(year, kisa){
    const m = await loadEmbeddedCached("meclis_harita.json", {});
    return m[year+'_'+kisa] || null;
  }
