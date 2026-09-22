  const $ = (s,el=document) => el.querySelector(s);
  const $$ = (s,el=document) => [...el.querySelectorAll(s)];
  const fmt = n => n.toLocaleString('tr-TR');
  const fmt1 = n => n.toLocaleString('tr-TR',{maximumFractionDigits:1,minimumFractionDigits:1});

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

  let BUNDLE, GEO, GEO_ILCE, GEO_ILCE_HIST, MAHALLE_GEO, MECLIS_2024;
  try{
    // mahalle_votes.json ARTIK burada YOK: 15 yilin tamami acik haliyle ~75MB,
    // her sayfa acilisinda (kullanici mahalle seviyesine hic inmese bile)
    // hepsini decompress etmek gereksizdi. Yil basina ayri gomulu anahtar
    // olarak (mahalle_votes_<yil>.json) sadece kullanici o yilin bir ilcesine
    // tikladiginda lazy-load edilir (bkz. map.js: mahalleDataForDistrict).
    // mahalle_geo.json (poligonlar, ~5MB) yillar arasi paylasimli ve nispeten
    // kucuk oldugu icin hala eager yukleniyor.
    [BUNDLE, GEO, GEO_ILCE, GEO_ILCE_HIST, MAHALLE_GEO, MECLIS_2024] = await Promise.all([
      loadEmbeddedCached("secim_tarihi_data.json"),
      loadEmbeddedCached("turkiye_il_sinirlari.geojson"),
      loadEmbeddedCached("turkiye_ilce_sinirlari.geojson"),
      loadEmbeddedCached("turkiye_ilce_sinirlari_hist_splits.geojson"),
      loadEmbeddedCached("mahalle_geo.json", {}),
      loadEmbeddedCached("meclis_2024.json", {})
    ]);
  }catch(e){
    document.body.innerHTML = '<div class="wrap"><p>Veri yüklenemedi: '+e+'</p></div>';
    return;
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

