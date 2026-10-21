  const $ = (s,el=document) => el.querySelector(s);
  const $$ = (s,el=document) => [...el.querySelectorAll(s)];
  const fmt = n => n==null ? '—' : n.toLocaleString('tr-TR');
  // Veri kaynagi (YSK/TUIK/vb.) su an her zaman temiz (< > & " icermiyor,
  // dogrulandi), ama isim/parti alanlarini innerHTML'e gomerken yine de
  // kacis uygulanir - veri kaynagi ileride degisirse bu tek satir korur.
  const ESCAPE_MAP = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ESCAPE_MAP[c]);

  // Veri ayri statik JSON dosyalari olarak fetch() ile okunuyor. Yollar
  // sayfaya gore (relative, basinda / yok) - boylece hem yerelde hem GitHub
  // Pages'in bir alt dizin (repo-adi) altinda servis etmesiyle de calisir.
  // VERI_SURUMU: build.py'nin data/ + geo/ iceriginden hesapladigi ozet. Her istege ?v= olarak
  // eklenir: GitHub Pages dosyalari max-age=600 ile verdigi icin, yeni yayindan sonra sayfa
  // yenilendiginde tarayici eski (onbellekteki) veriyi kullanmasin.
  const VERI_SURUMU = '__VERI_SURUMU__';
  // Tek dosya surumu (turkiye-secim-haritasi/scripts/build.py) ayni dosyalari sayfaya gomer:
  // window.__EMBEDDED_GZ__ = {"data/elections/2023.json": "<gzip+base64>", ...}. Varsa veri fetch
  // yerine oradan acilir; boylece index.html file:// ile cift tiklayinca da calisir.
  const GOMULU_VERI = window.__EMBEDDED_GZ__ || null;
  async function gomuluAc(b64){
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }
  const FETCH_CACHE = {};
  function fetchJSON(path, fallback){
    if(!(path in FETCH_CACHE)){
      FETCH_CACHE[path] = (async () => {
        if(GOMULU_VERI){
          if(path in GOMULU_VERI) return gomuluAc(GOMULU_VERI[path]);
          if(fallback !== undefined) return fallback;
          throw new Error('Veri bulunamadı: '+path);
        }
        const res = await fetch(path + '?v=' + VERI_SURUMU);
        if(!res.ok){
          if(res.status === 404 && fallback !== undefined) return fallback;
          throw new Error('Veri alınamadı: '+path+' ('+res.status+')');
        }
        return res.json();
      })().catch(error => {
        delete FETCH_CACHE[path]; // A failed request must be retryable.
        throw error;
      });
    }
    return FETCH_CACHE[path];
  }

  // Shared status UI also works before the rest of the app has initialized.
  function showLoadStatus(message, retry = null){
    const box = $('#loadStatus');
    box.hidden = false;
    box.dataset.state = retry ? 'error' : 'loading';
    $('#loadMessage').textContent = message;
    $('#retryLoad').hidden = !retry;
    $('#retryLoad').onclick = retry;
  }
  function clearLoadStatus(){
    $('#loadStatus').hidden = true;
    $('#retryLoad').onclick = null;
  }
  function setResultsBusy(busy){
    $('#results').inert = busy;
    $('#results').setAttribute('aria-busy', String(busy));
  }

  // Ilce sinirlari (GEO_ILCE, GEO_ILCE_HIST; ~1MB sikistirilmis) acilista indirilmez: ulke haritasi
  // yalniz il sinirlari ve secim verisiyle cizilir, ilce sinirlari ardindan arka planda ya da
  // ilk ile inildiginde yuklenir (ensureIlceGeo).
  let BUNDLE, GEO, GEO_ILCE = null, GEO_ILCE_HIST = null, MECLIS_2024, MAHALLE_COVERAGE, DISTRICT_SPLITS, HARITA_NOTLARI;
  setResultsBusy(true);
  // Keep initialization retryable without reloading the page or attaching handlers twice.
  while(!BUNDLE){
    showLoadStatus('Harita verileri yükleniyor…');
    try{
      const [partiler, il, meclis, mahalleCoverage, districtSplits, haritaNotlari] = await Promise.all([
        fetchJSON("data/parties.json"),
        fetchJSON("geo/il_sinirlari.geojson"),
        fetchJSON("geo/meclis_2024.json", {}),
        fetchJSON("geo/mahalle_coverage.json", {}),
        fetchJSON("geo/district_splits.json", {}),
        fetchJSON("geo/harita_notlari.json", {}),
      ]);
      GEO = il;
      MECLIS_2024 = meclis; MAHALLE_COVERAGE = mahalleCoverage; DISTRICT_SPLITS = districtSplits; HARITA_NOTLARI = haritaNotlari;
      BUNDLE = {partiler, secimler: {}};
    }catch(error){
      await new Promise(resolve => showLoadStatus('Harita verileri yüklenemedi. Bağlantınızı kontrol edip yeniden deneyin.', () => {
        $('#retryLoad').onclick = null;
        resolve();
      }));
    }
  }
  // Mahalle yayin dosyalari kompakt (scripts/kompakt.py): oy dosyasi satir dizisi, sinirlar TopoJSON.
  // Burada mantiksal bicime ({mahalle: {secmen, katilim, oy: {parti: {oy, oran}}}} ve
  // {mahalle: {ad, geometry}}) acilir; harita kodu ayni kalir. Oran ve katilim kaynakta da
  // oy/gecerliOy ve oyKullanan/secmen'in 2 ondaliga yuvarlanmisi (yazarken denetlenir).
  // Python round(x, 2) ile ayni: tam ortadaki (ikili gosterimde tam ...5 olan, orn. 243/480 -> 50.625)
  // degerler cifte yuvarlanir; toFixed bunlari yukari yuvarlardi.
  function yuvarla2(x){
    const s3 = x.toFixed(3);
    if(s3.endsWith('5') && /\.\d\d50*$/.test(x.toFixed(60)) && Number(s3[s3.length-2]) % 2 === 0) return Number(s3.slice(0, -1));
    return Number(x.toFixed(2));
  }
  const yuzde2 = (pay, payda) => payda && pay!=null ? yuvarla2(pay/payda*100) : null;
  function mahalleOyAc(k){
    if(!k || k.bicim !== 'mahalle-oy/1') return k || {};
    const P = k.partiler, out = {};
    for(const g in k.ilceler){
      const satirlar = k.ilceler[g], o = out[g] = {};
      for(const m in satirlar){
        const s = satirlar[m], oy = {};
        for(let i = 5; i < s.length; i++) if(s[i] != null) oy[P[i-5]] = {oy: s[i], oran: yuzde2(s[i], s[2])};
        o[m] = {secmen: s[0], oyKullanan: s[1], gecerliOy: s[2], sandik: s[3],
                kazanan: s[4]==null ? null : P[s[4]], katilim: yuzde2(s[1], s[0]), oy};
      }
    }
    return out;
  }
  function topoAc(t){
    if(!t || t.type !== 'Topology') return t;
    // koordinatlar 1e-4 derecelik tamsayi + delta: bolme tek adimda yapilir, kaynaktaki sayinin aynisi cikar
    const tx = Math.round(t.transform.translate[0]*1e4), ty = Math.round(t.transform.translate[1]*1e4);
    const arcs = t.arcs.map(a => { let x = 0, y = 0; return a.map(([dx, dy]) => [((x += dx) + tx)/1e4, ((y += dy) + ty)/1e4]); });
    const cizgi = idx => {
      const pts = [];
      for(const i of idx){
        const a = i >= 0 ? arcs[i] : arcs[~i].slice().reverse();
        for(let j = pts.length ? 1 : 0; j < a.length; j++) pts.push(a[j]);
      }
      return pts;
    };
    const out = {};
    for(const g of t.objects.mahalle.geometries){
      const c = g.type === 'Polygon' ? g.arcs.map(cizgi) : g.type === 'MultiPolygon' ? g.arcs.map(p => p.map(cizgi)) : cizgi(g.arcs);
      out[g.id] = {ad: g.properties.ad, geometry: {type: g.type, coordinates: c}};
    }
    return out;
  }
  // acilmis hali onbellege alinir; ham dosya acildiktan sonra bellekte tutulmaz
  const ACIK_CACHE = {};
  function fetchAcik(path, ac, fallback){
    if(!(path in ACIK_CACHE)){
      ACIK_CACHE[path] = fetchJSON(path, fallback).then(ham => { delete FETCH_CACHE[path]; return ac(ham); })
        .catch(error => { delete ACIK_CACHE[path]; throw error; });
    }
    return ACIK_CACHE[path];
  }
  // Mahalle poligonlari ilce basina ayri dosyada: yalniz inilen ilcenin poligonlari indirilir.
  function loadMahalleGeometry(geomId){
    return fetchAcik("geo/mahalle/"+encodeURIComponent(geomId)+".json", topoAc);
  }
  function prepareElection(data){
    if(!data || data._validated) return data;
    const geomCounts = {};
    for(const row of data.ilceler||[]) if(row.geomId) geomCounts[row.geomId]=(geomCounts[row.geomId]||0)+1;
    for(const row of [...(data.iller||[]), ...(data.ilceler||[])]){
      const values = Object.values(row.oy||{});
      const total = values.reduce((s,v)=>s+(v.oy||0),0);
      if(row.gecerliOy && values.length && values.every(v=>v.oy!=null) &&
         Math.abs(total-row.gecerliOy)>Math.max(1,row.gecerliOy*0.0001)){
        row.veriNotu = [row.veriNotu, 'Parti oyları toplamı ('+fmt(total)+') ile geçerli oy ('+fmt(row.gecerliOy)+') uyuşmuyor. Yüzdeler ve değişim karşılaştırması doğrulanana kadar gösterilmiyor.'].filter(Boolean).join(' ');
        row.yuzdeDogrulanmadi = true;
        for(const result of values) result.yuzdeDogrulanmadi = true;
      }
      if(row.gecerliOy && values.length && values.every(v=>v.oy!=null) &&
         Math.abs(total-row.gecerliOy)<=Math.max(1,row.gecerliOy*0.0001) &&
         values.some(v=>v.oran!=null && Math.abs(v.oran-v.oy/row.gecerliOy*100)>0.11)){
        row.veriNotu = [row.veriNotu,'Kaynak yüzdeleri oy sayımlarına uymuyor; yüzdeler doğrulama bekliyor.'].filter(Boolean).join(' ');
        row.yuzdeDogrulanmadi=true;
        for(const result of values) result.yuzdeDogrulanmadi=true;
      }
      if(row.geomId && geomCounts[row.geomId]>1){
        row.veriNotu = [row.veriNotu,'Aynı harita bölgesine birden fazla kayıt eşleşiyor; yüzdeler doğrulama bekliyor.'].filter(Boolean).join(' ');
        for(const result of values) result.yuzdeDogrulanmadi=true;
        row.yuzdeDogrulanmadi=true;
      }
      if(row.ilceGeneliSonuc) row.veriNotu = [row.veriNotu, 'Belediye kapsamı doğrulanmadı: '+row.ilceGeneliSonuc].filter(Boolean).join(' ');
      if(row.secmen && row.gecerliOy>row.secmen){
        row.veriNotu = [row.veriNotu, 'Geçerli oy seçmen sayısını aşıyor; sayımlar kaynak doğrulaması bekliyor. Katılım gösterilmiyor.'].filter(Boolean).join(' ');
        row.katilim = null;
      }
    }
    data._validated = true;
    return data;
  }
  async function fetchElection(year){
    if(!(year in BUNDLE.secimler)) BUNDLE.secimler[year] = await fetchJSON("data/elections/"+year+".json");
    return prepareElection(BUNDLE.secimler[year]);
  }
  function loadMahalleVotesForYear(year){
    // Mahalle verisi olmayan yillarda (ornegin 1968 yerel) istek hic atilmaz.
    if(!(year in MAHALLE_COVERAGE)) return Promise.resolve({});
    return fetchAcik("data/mahalle_votes/"+year+".json", mahalleOyAc, {});
  }
  const geoFeatureById = {};
  let ilceGeoPromise = null;
  function ensureIlceGeo(){
    if(!ilceGeoPromise){
      ilceGeoPromise = Promise.all([
        fetchJSON("geo/ilce_sinirlari.geojson"),
        fetchJSON("geo/ilce_sinirlari_hist.geojson"),
      ]).then(([ilce, ilceHist]) => {
        if(!GEO_ILCE){
          for(const f of ilce.features){ geoFeatureById[f.properties.id] = f; }
          for(const f of ilceHist.features){ geoFeatureById[f.properties.id] = f; }
          GEO_ILCE = ilce; GEO_ILCE_HIST = ilceHist;
        }
      }).catch(error => {
        ilceGeoPromise = null; // basarisiz istek yeniden denenebilmeli
        throw error;
      });
    }
    return ilceGeoPromise;
  }

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
  function loadOylama(year, kisa){
    return fetchJSON("data/meclis_harita/"+year+"_"+kisa+".json", null).then(prepareElection);
  }
