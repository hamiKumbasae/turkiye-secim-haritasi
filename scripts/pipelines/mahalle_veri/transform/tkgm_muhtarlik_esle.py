"""
YSK muhtarlik sonuclarini (fetch_muhtarlik_tum.js) TKGM mahalle sinirlariyla (fetch_tkgm_mahalle.py)
eslestirip sitenin mahalle verisine yazar.

Eslestirme ayni ilce (geomId) icinde yapilir:
  1. mevcut poligon: ayni ilcenin mevcut (OSM/ttezer, guncel idari) poligonlarinda ad birebir ve tekse
     o kullanilir. TKGM birimleri kadastro mahallesidir; sehir merkezlerinde birkac idari mahalleyi
     kapsayabildigi icin mevcut sinir onceliklidir.
  2. TKGM birebir: ad_anahtari(YSK adi) == ad_anahtari(TKGM adi) (' Köyü', ' Mahalle' ekleri atilir)
  3. TKGM parca: 'Eski/Yeni', 'Eski-Yeni', 'Ad (Eski ad)', 'X Merkez' yazimlarindan bir parca birebir
  4. TKGM yakin: kalanlar icin ad benzerligi >= ESIK (difflib), bire bir; ilk harf farkliysa >= 0.93.
     Bolumlere ayrilmis birimlerin ('Büyüktatlar/Aliçli', '/Fatih' ...) birlesimi de aday olur.
  0. belediye acik verisi (data/raw/belediye/mahalle: Bursa, Sakarya): resmi guncel idari sinir; olan ilcede
     ilk sirada, eski poligonlar ancak bunlarla %25'ten az ortusurse kalir. Anahtar 'b<plaka>-<kimlik>'.
  1b. guncel OSM (data/raw/osm/mahalle, fetch_osm_mahalle.py): sitede olmayan idari mahalle sinirlari,
     2-4'teki ad kurallariyla; mevcut poligonlarla %25'ten fazla ortusen alinmaz. Anahtar 'r<osm_id>'.
  4b. OSM konumu (data/raw/osm/yer, fetch_osm_yer.py): adla eslesmeyen muhtarligin guncel adli OSM yer
     noktasi tek bir TKGM biriminin icine dusuyorsa o birim (TKGM bircok koyu eski adiyla tutuyor:
     Bismil 'Akbaş' ~ TKGM 'Alibociyan'). Yalniz bosta duran birime ve bire bir: birim adla baska muhtarliga
     eslesmisse, baska muhtarligin adini tasiyorsa ya da icine ikinci bir muhtarligin noktasi dusuyorsa
     alinmaz; ayrica noktanin eski/guncel adlarindan biri birimin adini tutmali (ad destegi). Belirsiz
     durumda muhtarlik bos kalir. Sinir cizilmez.
  5. Mevcut poligonlarla alaninin %25'inden fazlasi ortusen TKGM birimi cizilmez (ust uste binme).
  6. eslesmeyen muhtarliklar raporlanir (docs/rapor/mahalle_eslesme/<secim>.csv)
Partiler: ulke genelinde %ANA_ESIK ustu olanlar ve o mahallenin kazanani ayri, gerisi 'Diğer'.
Cumhurbaskanligi (secimTuru 9): sutunlar adaylardir (bagimsizN_ALDIGI_OY); her aday secim kaydindaki
adiyla ayri tutulur, hicbiri 'Bağımsız'/'Diğer'e toplanmaz.
Bir TKGM birimine birden cok muhtarlik duserse toplanir (raporda isaretlenir).

Yazilanlar (yalniz TKGM sinirlari olan ilceler icin; digerlerine dokunulmaz):
  - geo/normalized/mahalle_geo.json: <geomId>["k<tkgm_id>"] = {ad, geometry}; eski poligonlar korunur
    (diger secimler onlari kullanir; site her secimde yalniz verisi olan poligonlari cizer)
  - data/normalized/mahalle/<secim>.json: o ilcelerin butun kaydi "k<tkgm_id>" anahtarlariyla yeniden
    yazilir: {secmen, sandik, katilim, kazanan, oy{parti:{oy, oran}}, gecerliOy, oyKullanan}
    Partiler YSK sutunlarindan (Diğer'e toplanmadan), oran gecerli oya gore; kazanan en cok oy alan.

Kullanim (repo kokunden):
  python3 scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py [kontrol|uygula] <secim> [<secim> ...]
"""
import collections
import csv
import difflib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "pipelines" / "election_import"))
from common.election_io import load_election  # noqa: E402
from common.turkish_text import fold, fold_mahalle  # noqa: E402
from party_map_helper import build_party_mapping  # noqa: E402

TKGM_DIR = ROOT / "data" / "raw" / "tkgm" / "mahalle"
BELEDIYE_DIR = ROOT / "data" / "raw" / "belediye" / "mahalle"   # fetch_belediye_mahalle.py
OSM_DIR = ROOT / "data" / "raw" / "osm" / "mahalle"   # fetch_osm_mahalle.py (yoksa bu adim atlanir)
YER_DIR = ROOT / "data" / "raw" / "osm" / "yer"       # fetch_osm_yer.py (yoksa konum adimi atlanir)
ILCE_GEO = ROOT / "geo" / "normalized" / "turkiye_ilce_sinirlari.geojson"
MUHTARLIK_DIR = ROOT / "data" / "raw" / "ysk" / "muhtarlik"
GEO = ROOT / "geo" / "normalized" / "mahalle_geo.json"
MAHALLE = ROOT / "data" / "normalized" / "mahalle"
GEOMID_MAP = json.loads((ROOT / "data/raw/ysk/acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))
RAPOR = ROOT / "docs" / "rapor" / "mahalle_eslesme"
# Tarihsel ilceler: secim kaydi bugunku ilcelerin birlesimi olan sentetik bir kimlik kullanabilir
# (orn. 2009'da HIST-Kahramanmaraş-Merkez = Dulkadiroğlu + Onikişubat). Sitenin genel secimlerde
# kullandigi kayit: geo/historical/district_splits.json (syntheticId -> hideIds).
SENTETIK = {e["syntheticId"]: e["hideIds"]
            for v in json.loads((ROOT / "geo/historical/district_splits.json").read_text(encoding="utf-8")).values() for e in v}
ESIK = 0.85
ANA_ESIK = 1.5   # ulke geneli oy orani (%); altindaki partiler mahalle verisinde 'Diğer'e toplanir
# TKGM ilce adi projedekinden farkli yazilan ilceler (fold edilmis TKGM adi -> geomId)
ILCE_ALIAS = {"19 MAYIS": "TR-D-55-001",            # Samsun Ondokuzmayıs
              "KEMALPASA (ARTVIN)": "TR-D-08-006"}  # Artvin Kemalpaşa (İzmir Kemalpaşa ile karışmasın diye)
BAGIMSIZ = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def ad_anahtari(ad):
    """fold_mahalle + TKGM'nin 'Yeni Mahalle', 'X Köyü' gibi ekleri (paylasilan fold_mahalle 'MAHALLE'
    sozcugunu atmadigi icin burada)."""
    p = fold_mahalle(ad).split(" ")
    while len(p) > 1 and p[-1] in ("MAHALLE", "MAHALLESI", "KOYU", "KOY", "MAH"):
        p.pop()
    return " ".join(p)


def koysuz(anahtar):
    """YSK'nin bitisik yazdigi koy adi ('BESIKKOY', 'CIPKOY') -> 'BESIK'; degilse None."""
    if anahtar.endswith("KOY") and len(anahtar) > 5 and " " not in anahtar[-4:]:
        return anahtar[:-3].rstrip()
    return None


def koy_birimi(ft):
    return "KOY" in fold(ft["properties"].get("ad") or "")


def yuvarla4(o):
    if isinstance(o, (list, tuple)):
        if o and isinstance(o[0], (int, float)):
            return [round(o[0], 4), round(o[1], 4)]
        return [yuvarla4(x) for x in o]
    return o


def bolum_birlesimleri(birimler):
    """TKGM bazi mahalleleri kadastro bolumlerine ayiriyor ('Büyüktatlar/Aliçli', 'Büyüktatlar/Fatih').
    Ayni on ekli 2+ bolum icin birlesik bir aday birim uretilir (ad = on ek)."""
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    gruplar = collections.defaultdict(list)
    for ft in birimler:
        ad = ft["properties"]["ad"] or ""
        if "/" in ad:
            gruplar[ad.split("/")[0].strip()].append(ft)
    yeni = []
    for on, lst in gruplar.items():
        if len(lst) < 2:
            continue
        from shapely.validation import make_valid
        parca = [make_valid(shape(f["geometry"])).buffer(0) for f in lst if f.get("geometry")]
        if len(parca) < 2:
            continue
        g = unary_union(parca).simplify(0.0001, preserve_topology=True)
        if g.is_empty or g.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        m = mapping(g)
        yeni.append({"type": "Feature", "geometry": {"type": m["type"], "coordinates": yuvarla4(m["coordinates"])},
                     "properties": {**lst[0]["properties"], "ad": on, "tkgm_id": "b" + "-".join(str(f["properties"]["tkgm_id"]) for f in lst),
                                    "bolumler": [f["properties"]["tkgm_id"] for f in lst]}})
    return yeni


def tkgm_yukle():
    birimler = collections.defaultdict(list)   # geomId -> [feature]
    for f in sorted(TKGM_DIR.glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            g = ft["properties"].get("geomId") or ILCE_ALIAS.get(fold(ft["properties"].get("ilce")))
            ft["properties"]["geomId"] = g
            if g and ft.get("geometry"):
                birimler[g].append(ft)
    return birimler


# Bursa dosyasi EPSG:2320 (ED50 / TM30) etiketli ama koordinatlar TUREF (ITRF96 / TM30, EPSG:5254):
# 2320 olarak okununca ayni adli TKGM sinirlarina gore medyan ~180 m guneyde kaliyor, 5254 ile ortusuyor.
BELEDIYE_CRS_DUZELT = {16: 5254}


def belediye_yukle():
    """Belediye acik veri mahalle sinirlari (projeksiyonlu olabilir: crs alanina gore WGS84'e cevrilir),
    sadelestirilir; ilce adi (plaka icinde) projenin ilce kaydiyla eslenir. Anahtar 'b<plaka>-<kimlik>'."""
    if not BELEDIYE_DIR.exists():
        return {}
    from pyproj import Transformer
    from shapely.geometry import mapping, shape
    from shapely.ops import transform as donustur
    from shapely.validation import make_valid
    sec = json.loads((ROOT / "data/normalized/elections/genel/2023.json").read_text(encoding="utf-8"))
    ilce_id = {(r["plaka"], fold(r["ad"])): r["geomId"] for r in sec["ilceler"]}
    sonuc = collections.defaultdict(list)
    for f in sorted(BELEDIYE_DIR.glob("[0-9][0-9].geojson")):
        plaka = int(f.stem)
        d = json.loads(f.read_text(encoding="utf-8"))
        crs = ((d.get("crs") or {}).get("properties") or {}).get("name", "EPSG::4326")
        epsg = BELEDIYE_CRS_DUZELT.get(plaka, int(re.findall(r"(\d+)$", crs)[0]))
        tr = Transformer.from_crs(epsg, 4326, always_xy=True) if epsg != 4326 else None
        for i, ft in enumerate(d["features"]):
            p = {k.lower(): v for k, v in (ft.get("properties") or {}).items()}
            ad, ilce = p.get("ad"), p.get("ilce_adi") or p.get("ilce")
            g = ilce_id.get((plaka, fold(ilce or "")))
            if not (ad and g and ft.get("geometry")):
                continue
            geo_ = make_valid(shape(ft["geometry"]))
            if tr:
                geo_ = donustur(tr.transform, geo_)
            geo_ = geo_.simplify(0.0001, preserve_topology=True)
            if geo_.is_empty or geo_.geom_type not in ("Polygon", "MultiPolygon"):
                continue
            m = mapping(geo_)
            kimlik = p.get("kimlikno") or p.get("objectid") or i
            sonuc[g].append({"type": "Feature", "geometry": {"type": m["type"], "coordinates": yuvarla4(m["coordinates"])},
                             "properties": {"tkgm_id": f"b{plaka:02d}-{kimlik}", "ad": ad}})
    return sonuc


def osm_yukle():
    """Guncel OSM mahalle/koy poligonlari, ilceye (geomId) poligonun icindeki bir noktayla atanir.
    esle() ile ayni bicimde: properties {tkgm_id: 'r<osm_id>', ad}."""
    if not OSM_DIR.exists():
        return {}
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    ilceler = json.loads(ILCE_GEO.read_text(encoding="utf-8"))["features"]
    sekiller = [shape(f["geometry"]) for f in ilceler]
    agac = STRtree(sekiller)
    sonuc = collections.defaultdict(list)
    for f in sorted(OSM_DIR.glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            p = ft["properties"]
            if not p.get("ad") or not ft.get("geometry"):
                continue
            nokta = shape(ft["geometry"]).representative_point()
            for i in agac.query(nokta):
                if sekiller[i].contains(nokta):
                    sonuc[ilceler[i]["properties"]["id"]].append({"type": "Feature", "geometry": ft["geometry"], "properties": {
                        "tkgm_id": f"r{p['osm_id']}", "ad": p["ad"], "admin_level": p.get("admin_level")}})
                    break
    return sonuc


def yer_yukle():
    """OSM koy/mahalle yer noktalari (fetch_osm_yer.py), ilceye (geomId) ilce sinirlariyla atanir."""
    if not YER_DIR.exists():
        return {}
    from shapely.geometry import Point, shape
    from shapely.strtree import STRtree
    ilceler = json.loads(ILCE_GEO.read_text(encoding="utf-8"))["features"]
    sekiller = [shape(f["geometry"]) for f in ilceler]
    agac = STRtree(sekiller)
    sonuc = collections.defaultdict(list)
    for f in sorted(YER_DIR.glob("*.json")):
        for p in json.loads(f.read_text(encoding="utf-8")):
            nokta = Point(p["lon"], p["lat"])
            for i in agac.query(nokta):
                if sekiller[i].contains(nokta):
                    sonuc[ilceler[i]["properties"]["id"]].append(p)
                    break
    return sonuc


# OSM noktasinin YSK adiyla karsilastirilan (guncel) ad etiketleri; eski ad ve baska dillerdeki adlar degil
GUNCEL_AD = ("name", "name:tr", "official_name", "alt_name", "alt_name:tr", "short_name")


KONUM_AD_ESIK = 0.7


def ad_destegi(birim_adi, adlar):
    """Konumla bulunan birimin adi, noktanin adlarindan birine (';' ile ayrilmis coklu degerler dahil) ya da
    YSK adina benziyor mu (TKGM 'Eski (Yeni)', 'A/B' yazimlarinin parcalari da karsilastirilir)."""
    birim = {ad_anahtari(birim_adi)} | {ad_anahtari(x) for x in re.split(r"[()/]", birim_adi) if x.strip()}
    aday = {ad_anahtari(x) for v in adlar for x in v.split(";") if x.strip()}
    return any(difflib.SequenceMatcher(None, a, b).ratio() >= KONUM_AD_ESIK for a in aday for b in birim if a and b)


def konumla_esle(muhtarliklar, noktalar, birimler, es, tum_muh, mevcut):
    """muhtarliklar: adla eslesmeyenler {mid: kayit}; noktalar: ilcenin OSM yer noktalari; birimler: ilcenin
    TKGM birimleri; es: adla eslesmeler {mid: (feature, yontem)}; tum_muh: ilcenin butun muhtarliklari;
    mevcut: kullanilan mevcut poligonlarin birlesimi (ya da None). Doner {mid: (feature, osm kimligi)}.
    Kosullar (belirsizse eslesme yapilmaz, muhtarlik haritada bos kalir): muhtarligin adini tasiyan noktalarin
    hepsi ayni tek birimin icinde; birim adla baska bir muhtarliga eslesmemis ve baska bir muhtarligin adini
    tasimiyor; birime konumla tek bir muhtarlik dusuyor (ikinci bir nokta da dusuyorsa ikisi de alinmaz);
    birim mevcut poligonlarla alaninin %25'inden fazla ortusmuyor; ad destegi var: noktanin adlarindan biri
    (guncel, eski ya da baska dildeki) ya da YSK adi birimin adina (veya parantez/bolu ile ayrilmis bir
    parcasina) >= KONUM_AD_ESIK benziyor. Ad destegi olmayan konum (sehir icinde kadastro birimi birkac idari
    mahalleyi kapsayabilir) kabul edilmez."""
    if not muhtarliklar or not noktalar or not birimler:
        return {}
    from shapely.geometry import Point, shape
    from shapely.strtree import STRtree
    from shapely.validation import make_valid
    sekil = [make_valid(shape(ft["geometry"])).buffer(0) for ft in birimler]
    agac = STRtree(sekil)
    ysk_adlari = {ad_anahtari(m["ad"]) for m in tum_muh.values()}
    es_birim = {id(ft) for ft, _ in es.values()}
    anahtar_nokta = collections.defaultdict(list)
    for p in noktalar:
        anahtarlar = set()
        for etiket in GUNCEL_AD:
            if p["adlar"].get(etiket):
                k = ad_anahtari(p["adlar"][etiket])
                anahtarlar.update(x for x in (k, koysuz(k)) if x)
        for k in anahtarlar:
            anahtar_nokta[k].append(p)
    sonuc = {}
    birime_dusen = collections.Counter()
    for mid, m in muhtarliklar.items():
        k = ad_anahtari(m["ad"])
        adaylar = anahtar_nokta.get(k) or (anahtar_nokta.get(koysuz(k)) if koysuz(k) else None)
        if not adaylar:
            continue
        icinde = set()
        for p in adaylar:
            nokta = Point(p["lon"], p["lat"])
            ic = [i for i in agac.query(nokta) if sekil[i].contains(nokta)]
            icinde.add(ic[0] if len(ic) == 1 else None)
        if len(icinde) != 1 or None in icinde:
            continue
        i = icinde.pop()
        ft = birimler[i]
        birime_dusen[i] += 1
        if id(ft) in es_birim or ad_anahtari(ft["properties"]["ad"] or "") in ysk_adlari:
            continue
        if mevcut is not None and sekil[i].area and sekil[i].intersection(mevcut).area / sekil[i].area > 0.25:
            continue
        if not ad_destegi(ft["properties"]["ad"] or "", [m["ad"]] + [v for p in adaylar for v in p["adlar"].values()]):
            continue
        sonuc[mid] = (i, ft, f"{adaylar[0]['tur']}{adaylar[0]['osm']}")
    return {mid: (ft, osm) for mid, (i, ft, osm) in sonuc.items() if birime_dusen[i] == 1}


def esle(muhtarliklar, birimler):
    """muhtarliklar: {mid: kayit}; birimler: [feature]. Doner: {mid: (feature, yontem)}"""
    birlesik = bolum_birlesimleri(birimler)
    ad_birim = collections.defaultdict(list)
    for ft in birimler:
        ad_birim[ad_anahtari(ft["properties"]["ad"])].append(ft)
    for ft in birlesik:   # birlesik aday yalniz o adda tek bir birim yoksa kullanilir
        if not ad_birim.get(ad_anahtari(ft["properties"]["ad"])):
            ad_birim[ad_anahtari(ft["properties"]["ad"])].append(ft)
    sonuc, kalan = {}, {}
    for mid, m in muhtarliklar.items():
        aday = ad_birim.get(ad_anahtari(m["ad"]))
        if not aday:   # YSK "BEŞİKKÖY" ~ TKGM "Beşik Köyü" (yalniz koy birimine)
            k = koysuz(ad_anahtari(m["ad"]))
            aday = [ft for ft in ad_birim.get(k, []) if koy_birimi(ft)] if k else None
        if aday and len(aday) == 1:
            sonuc[mid] = (aday[0], "birebir")
        else:
            kalan[mid] = m
    # 1b. TKGM'nin "Eski köy/Yeni mahalle", "Eski-Yeni", "Ad (Belde)" yazimlari: parcalardan biri
    #     YSK adina birebir esitse ve o parca ilcede tek ise eslestir
    alt = collections.defaultdict(list)
    for ft in birimler:
        ad = ft["properties"]["ad"] or ""
        parcalar = set()
        if "/" in ad or "-" in ad:
            parcalar.update(x.strip() for x in re.split(r"[/-]", ad) if x.strip())
        if "(" in ad:
            parcalar.add(re.sub(r"\(.*?\)", " ", ad).strip())
            parcalar.update(re.findall(r"\((.*?)\)", ad))
        for x in parcalar:
            alt[ad_anahtari(x)].append(ft)
    kullanilan = {id(ft) for ft, _ in sonuc.values()}
    for ft in birimler:   # "Eyüp Merkez" ~ EYÜPSULTAN MERKEZ degil; yalniz "X Merkez" -> X
        k = ad_anahtari(ft["properties"]["ad"] or "")
        if k.endswith(" MERKEZ"):
            alt[k[:-7]].append(ft)
    for mid in list(kalan):
        k = ad_anahtari(kalan[mid]["ad"])
        aday = [ft for ft in alt.get(k, []) if id(ft) not in kullanilan]
        if not aday and k.endswith(" MERKEZ") and len(k) > 8:   # YSK "MURATBEY MERKEZ" -> TKGM "Muratbey"
            aday = [ft for ft in ad_birim.get(k[:-7], []) if id(ft) not in kullanilan]
            aday = aday if len(aday) == 1 and not any(ad_anahtari(m["ad"]) == k[:-7] for m in muhtarliklar.values()) else []
        if len(aday) == 1 and not ad_birim.get(ad_anahtari(kalan[mid]["ad"])):
            sonuc[mid] = (aday[0], "yakin parca")
            kullanilan.add(id(aday[0]))
            del kalan[mid]
    kullanilan_bolum = {b for ft, _ in sonuc.values() for b in ft["properties"].get("bolumler", [])}
    serbest = {ad_anahtari(ft["properties"]["ad"]): ft for ft in birimler
               if id(ft) not in kullanilan and ft["properties"]["tkgm_id"] not in kullanilan_bolum}
    for ft in birlesik:   # bolumlu birimin birlesimi de yakin eslesmeye aday ('Büyüktatlar' ~ BÜYÜKTATLI)
        if not any(b in kullanilan_bolum or b in {f["properties"]["tkgm_id"] for f, _ in sonuc.values()}
                   for b in ft["properties"]["bolumler"]):
            serbest.setdefault(ad_anahtari(ft["properties"]["ad"]), ft)
    # yakin eslesme: puana gore, bire bir
    adaylar = []
    for mid, m in kalan.items():
        a = ad_anahtari(m["ad"])
        a2 = koysuz(a)
        for ad, ft in serbest.items():
            p = difflib.SequenceMatcher(None, a, ad).ratio()
            if a2 and koy_birimi(ft):
                p = max(p, difflib.SequenceMatcher(None, a2, ad).ratio())
            # ilk harf farkliysa (Şanlıavşar / Kanlıavşar) cok daha yuksek benzerlik iste
            if p >= ESIK and (a[:1] == ad[:1] or p >= 0.93):
                adaylar.append((p, mid, ad))
    alinan_m, alinan_b = set(), set()
    for p, mid, ad in sorted(adaylar, reverse=True):
        if mid in alinan_m or ad in alinan_b:
            continue
        sonuc[mid] = (serbest[ad], f"yakin {p:.2f}")
        alinan_m.add(mid)
        alinan_b.add(ad)
    return sonuc


def aday_eslemesi(col_to_name, adaylar):
    """Cumhurbaskanligi: bagimsizN_ALDIGI_OY sutunu -> secim kaydindaki aday adi (fold ile)."""
    adlar = {fold(a): a for a in adaylar}
    out = {}
    for col, ad in col_to_name.items():
        if BAGIMSIZ.match(col):
            if fold(ad) in adlar:
                out[col] = adlar[fold(ad)]
                continue
            # YSK tam adi ('EKMELEDDİN MEHMET İHSANOĞLU') kayittakinden uzun olabilir: kayittaki adin
            # butun sozcukleri YSK adinda geciyorsa ve tek aday buysa o
            ysk = set(fold(ad).split())
            uyan = [a for f, a in adlar.items() if set(f.split()) <= ysk]
            if len(uyan) != 1:
                raise ValueError(f"aday eslesmedi: {col} {ad} (secim kaydi: {sorted(adaylar)})")
            out[col] = uyan[0]
        else:   # 'bagimsiz_ALDIGI_OY': oy pusulasinda olmayan (sira_NO 0) basvurular
            out[col] = "Diğer"
    return out


def kayit_yap(toplam, col_to_key, ana_partiler):
    """Ulke genelinde %ANA_ESIK ustu partiler ve o mahallenin kazanani ayri; gerisi 'Diğer'
    (sitenin onceki mahalle verisiyle ayni yogunluk). Kazanan toplanmamis oylara gore."""
    ham = collections.Counter()
    for col, v in toplam["oy"].items():
        if v:
            ham[col_to_key[col] if col in col_to_key else "Bağımsız" if BAGIMSIZ.match(col) else col_to_key[col]] += v
    kazanan = max(ham, key=ham.get) if ham else None
    oy = collections.Counter()
    for p_, v in ham.items():
        oy[p_ if (p_ in ana_partiler or p_ == kazanan) else "Diğer"] += v
    gecerli = toplam["gecerli"]
    return {
        "secmen": toplam["secmen"], "sandik": toplam["sandik"],
        "katilim": round(toplam["oyKullanan"] / toplam["secmen"] * 100, 2) if toplam["secmen"] else None,
        "kazanan": kazanan,
        "oy": {p_: {"oran": round(v / gecerli * 100, 2) if gecerli else None, "oy": v} for p_, v in sorted(oy.items())},
        "gecerliOy": gecerli, "oyKullanan": toplam["oyKullanan"],
    }


def topla(liste):
    t = {"secmen": 0, "oyKullanan": 0, "gecerli": 0, "gecersiz": 0, "sandik": 0, "oy": collections.Counter()}
    for m in liste:
        for k in ("secmen", "oyKullanan", "gecerli", "gecersiz", "sandik"):
            t[k] += m[k]
        t["oy"].update(m["oy"])
    return t


def ilce_hedefleri(ham, secim):
    """YSK ilce kaydi -> o secimin site kaydindaki ilce kimligi. Bugunku kimlik (GEOMID_MAP) o secimde
    kullaniliyorsa o; o secimde onu kapsayan sentetik bir ilce kullaniliyorsa o sentetik kimlik; bugune
    eslenmeyen eski ilceler (2009 'X MERKEZ') icin ayni ildeki, baska YSK kaydina gitmeyen ve secmen
    sayisi birebir tutan secim kaydi (Aydın Merkez -> Efeler, Kahramanmaraş Merkez -> HIST-...-Merkez)."""
    kimlikler = {r["geomId"] for r in secim["ilceler"]}
    gizleyen = {h: S for S in kimlikler & SENTETIK.keys() for h in SENTETIK[S]}
    hedef, bos = {}, []
    for key, ilce in ham["ilceler"].items():
        g0 = GEOMID_MAP.get(key)
        if g0 in kimlikler:
            hedef[key] = g0
        elif g0 in gizleyen:
            hedef[key] = gizleyen[g0]
        else:
            hedef[key] = g0
            bos.append(key)
    dolu = {key for key, ilce in ham["ilceler"].items() if any(m["secmen"] for m in ilce["muhtarliklar"].values())}
    kullanilan = {g for key, g in hedef.items() if key in dolu}   # o yil henuz kurulmamis (bos) ilceler sayilmaz
    for key in bos:
        ilce = ham["ilceler"][key]
        top = sum(m["secmen"] for m in ilce["muhtarliklar"].values())
        if not top:
            continue
        aday = [r["geomId"] for r in secim["ilceler"]
                if r["plaka"] == int(ilce["ilId"]) and r["geomId"] not in kullanilan and r.get("secmen") == top]
        if len(aday) == 1:
            hedef[key] = aday[0]
            kullanilan.add(aday[0])
    return hedef


def isle(anahtar, birimler, geo, uygula, osm=None, bel=None, yer=None):
    ham = json.loads((MUHTARLIK_DIR / f"{anahtar}.json").read_text(encoding="utf-8"))
    secim = load_election(anahtar)
    mevcut = set()
    for lv in ("iller", "ilceler"):
        for r in secim[lv]:
            mevcut.update(r["oy"])
    aday_bazli = ham.get("secimTuru") in (7, 9)   # halkoylamasi (Evet/Hayır) ve cumhurbaskanligi: sutunlar aday/secenek
    if aday_bazli:
        col_to_key = aday_eslemesi(ham["colToName"], mevcut)
    else:
        col_to_key = build_party_mapping(ham["colToName"], mevcut - {"Diğer", "Bağımsız"}, {})
    ulke = collections.Counter()
    for r in secim["iller"]:
        for p_, v in r["oy"].items():
            ulke[p_] += v["oy"] if isinstance(v, dict) else v
    ulke_top = sum(ulke.values()) or 1
    ana_partiler = {p_ for p_, v in ulke.items() if v / ulke_top * 100 >= ANA_ESIK and p_ not in ("Diğer", "Bağımsız")}
    if aday_bazli:
        ana_partiler = set(col_to_key.values())
    print(f"   {anahtar} ayrı tutulan partiler: {sorted(ana_partiler)}")
    yol = MAHALLE / f"{anahtar}.json"
    veri = json.loads(yol.read_text(encoding="utf-8"))

    sayac = collections.Counter()
    il_sayac = collections.defaultdict(collections.Counter)
    rapor = []
    yeni_ilceler = {}
    hedefler = ilce_hedefleri(ham, secim)
    for key, ilce in ham["ilceler"].items():
        g = hedefler.get(key)
        havuz = SENTETIK.get(g, [g])
        if g in SENTETIK and any(h in birimler for h in havuz):
            # sentetik ilce: halef ilcelerin butun sinir kaynaklari tek havuzda (ayni adli mahalle iki halefte
            # varsa ad eslemesi tek olmadigi icin eslesmez)
            birimler[g] = [ft for h in havuz for ft in birimler.get(h, [])]
            for kaynak in (osm, bel):
                if kaynak is not None:
                    kaynak[g] = [ft for h in havuz for ft in kaynak.get(h, [])]
            hedef_geo = geo.setdefault(g, {})
            for h in havuz:
                for pid, pv in geo.get(h, {}).items():
                    hedef_geo.setdefault(pid, pv)
        muh = {mid: m for mid, m in ilce["muhtarliklar"].items() if mid != "_muhtarliksiz"}
        s_ilce = sum(m["secmen"] for m in ilce["muhtarliklar"].values())
        il = ilce["ilAdi"]
        il_sayac[il]["secmen"] += s_ilce
        sayac["secmen"] += s_ilce
        if "_muhtarliksiz" in ilce["muhtarliklar"]:
            s = ilce["muhtarliklar"]["_muhtarliksiz"]["secmen"]
            sayac["muhtarliksiz_secmen"] += s
            il_sayac[il]["muhtarliksiz"] += s
        if not g or g not in birimler:   # sentetik ilcede birimler[g] yukarida halef havuzundan kuruldu
            sayac["sinirsiz_ilce_secmen"] += s_ilce
            il_sayac[il]["sinirsiz"] += s_ilce
            for mid, m in muh.items():
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"], "ilçenin TKGM sınırı yok", ""])
            continue
        # 1) mevcut (OSM/ttezer) poligon adla birebir ve tekse o kullanilir: bunlar guncel idari mahalle
        #    sinirlari; TKGM birimleri ise kadastro mahallesi (sehir merkezlerinde birkac idari mahalleyi
        #    kapsayabilir). 2) kalan muhtarliklar TKGM'ye eslenir; mevcut poligonlarla %25'ten fazla
        #    ortusen TKGM birimi cizilmez (ust uste binme olmasin).
        from shapely.geometry import shape
        from shapely.ops import unary_union
        from shapely.validation import make_valid
        gruplar = collections.defaultdict(list)
        eski_gruplar = collections.defaultdict(list)
        osm_yeni = {}   # yeni eklenen (belediye/OSM) poligonlar: pid -> (feature, muhtarlik)
        tkgm_aday = {}
        # 0) belediyenin resmi acik verisi varsa (Bursa, Sakarya) o ilcede once o kullanilir: guncel idari
        #    sinir. Sitedeki eski poligonlar yalniz belediye sinirlariyla %25'ten fazla ortusmuyorsa kalir.
        kalan, bel_birlesik = dict(muh), None
        bel_ft = (bel or {}).get(g, [])
        if bel_ft:
            for mid, (ft, yontem) in esle(muh, bel_ft).items():
                pid = ft["properties"]["tkgm_id"]
                m = kalan.pop(mid)
                eski_gruplar[pid].append(m)
                osm_yeni[pid] = (ft, m)
                sayac["eslesen_belediye"] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"],
                              "Belediye sınırı" if yontem == "birebir" else "Belediye sınırı, yakın ad",
                              ft["properties"]["ad"] + ("" if yontem == "birebir" else f" ({yontem})")])
            if osm_yeni:
                bel_birlesik = unary_union([make_valid(shape(ft["geometry"])).buffer(0) for ft, _ in osm_yeni.values()])
        eski = collections.defaultdict(list)
        for pid, pv in geo.get(g, {}).items():
            if not pid.startswith(("k", "b")):
                eski[ad_anahtari(pv.get("ad"))].append(pid)
        for mid, m in kalan.items():
            if len(eski.get(ad_anahtari(m["ad"]), [])) == 1:
                pid = eski[ad_anahtari(m["ad"])][0]
                if bel_birlesik is not None:
                    eg = make_valid(shape(geo[g][pid]["geometry"])).buffer(0)
                    if eg.area and eg.intersection(bel_birlesik).area / eg.area > 0.25:
                        tkgm_aday[mid] = m
                        continue
                eski_gruplar[pid].append(m)
                sayac["eslesen_eski"] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
            else:
                tkgm_aday[mid] = m
        # 1b) guncel OSM (fetch_osm_mahalle.py): sitede henuz olmayan idari mahalle sinirlari; ad eslemesi
        #     TKGM ile ayni kurallarla. Mevcut poligonlarla %25'ten fazla ortusen OSM sinirlari alinmaz.
        for kaynak_adi, kaynak in (("OSM", osm),):
            aday_ft = [ft for ft in (kaynak or {}).get(g, []) if ft["properties"]["tkgm_id"] not in geo.get(g, {})]
            if not (aday_ft and tkgm_aday):
                continue
            es_k = esle(tkgm_aday, aday_ft)
            mevcut_birlesik = unary_union([make_valid(shape((geo[g][pid] if pid in geo.get(g, {}) else osm_yeni[pid][0])["geometry"])).buffer(0)
                                           for pid in eski_gruplar]) if eski_gruplar else None
            alinan = set()
            for mid, (ft, yontem) in sorted(es_k.items(), key=lambda x: x[1][1] != "birebir"):
                pid = ft["properties"]["tkgm_id"]
                if pid in alinan:
                    continue
                og = make_valid(shape(ft["geometry"])).buffer(0)
                if mevcut_birlesik is not None and og.area and og.intersection(mevcut_birlesik).area / og.area > 0.25:
                    continue
                alinan.add(pid)
                m = tkgm_aday.pop(mid)
                eski_gruplar[pid].append(m)
                osm_yeni[pid] = (ft, m)
                sayac["eslesen_" + kaynak_adi.lower()] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"],
                              f"{kaynak_adi} sınırı" if yontem == "birebir" else f"{kaynak_adi} sınırı, yakın ad",
                              ft["properties"]["ad"] + ("" if yontem == "birebir" else f" ({yontem})")])
        es = esle(tkgm_aday, birimler[g])
        eski_birlesik = None
        if eski_gruplar:
            eski_birlesik = unary_union([make_valid(shape((geo[g][pid] if pid in geo.get(g, {}) else osm_yeni[pid][0])["geometry"])).buffer(0)
                                         for pid in eski_gruplar])
        # 1c) OSM yer noktasi: adla eslesmeyen muhtarligin guncel adli OSM noktasi bosta duran tek bir TKGM
        #     biriminin icine dusuyorsa o birim kullanilir (TKGM bircok koyu eski adiyla tutuyor). Yalniz bire
        #     bir; belirsiz durumda muhtarlik bos kalir.
        konum = konumla_esle({mid: m for mid, m in tkgm_aday.items() if mid not in es},
                             [p for h in havuz for p in (yer or {}).get(h, [])], birimler[g], es, muh, eski_birlesik)
        for mid, m in tkgm_aday.items():
            if mid in konum:
                ft, osm_id = konum[mid]
                gruplar[ft["properties"]["tkgm_id"]].append((m, ft, "konum"))
                sayac["eslesen_konum"] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"], "TKGM sınırı, OSM konumu",
                              f"{ft['properties']['ad']} (OSM {osm_id})"])
                continue
            if mid in es and eski_birlesik is not None:
                from shapely.geometry import shape
                from shapely.validation import make_valid
                tg = make_valid(shape(es[mid][0]["geometry"])).buffer(0)
                if tg.area and tg.intersection(eski_birlesik).area / tg.area > 0.25:
                    sayac["cakisan"] += 1
                    sayac["eslesmeyen_secmen"] += m["secmen"]
                    il_sayac[il]["eslesmeyen"] += m["secmen"]
                    rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"], "TKGM sınırı mevcut poligonlarla çakışıyor, çizilmedi", es[mid][0]["properties"]["ad"]])
                    continue
            if mid in es:
                ft, yontem = es[mid]
                gruplar[ft["properties"]["tkgm_id"]].append((m, ft, yontem))
                sayac["eslesen_" + yontem.split()[0]] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"],
                              "TKGM sınırı" if yontem == "birebir" else "TKGM sınırı, yakın ad", ft["properties"]["ad"] + ("" if yontem == "birebir" else f" ({yontem})")])
            else:
                sayac["eslesmeyen"] += 1
                sayac["eslesmeyen_secmen"] += m["secmen"]
                il_sayac[il]["eslesmeyen"] += m["secmen"]
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"], "eşleşmedi", ""])
        ilce_kayit = {}
        for tid, lst in gruplar.items():
            ft = lst[0][1]
            k = f"k{tid}"
            if len(lst) > 1:
                sayac["birlesen_birim"] += 1
                rapor.append([anahtar, il, ilce["ilceAdi"], " + ".join(m["ad"] for m, _, _ in lst), sum(m["secmen"] for m, _, _ in lst),
                              "birden çok muhtarlık tek sınıra düştü (toplandı)", ft["properties"]["ad"]])
            ilce_kayit[k] = kayit_yap(topla([m for m, _, _ in lst]), col_to_key, ana_partiler)
            if uygula:
                ad = lst[0][0]["ad"] if len(lst) == 1 else ft["properties"]["ad"]
                geo.setdefault(g, {})[k] = {"ad": ad, "geometry": ft["geometry"]}
        for pid, lst in eski_gruplar.items():
            ilce_kayit[pid] = kayit_yap(topla(lst), col_to_key, ana_partiler)
            if uygula and pid in osm_yeni:
                geo.setdefault(g, {})[pid] = {"ad": osm_yeni[pid][1]["ad"], "geometry": osm_yeni[pid][0]["geometry"]}
        yeni_ilceler.setdefault(g, {}).update(ilce_kayit)   # ayni ilceye iki YSK kaydi dusebilir (19 Mayis, Caglayancerit)
    eski_secmen = sum((r.get("secmen") or 0) for g in yeni_ilceler for r in veri.get(g, {}).values())
    yeni_secmen = sum(r["secmen"] for k in yeni_ilceler.values() for r in k.values())
    if uygula:
        for g, k in yeni_ilceler.items():
            if k:
                veri[g] = k
        # o secimin haritasinda olmayan ilce kimlikleri (orn. 2009'da sentetik ilceye giden veri eskiden
        # bugunku kimlige yaziliyordu) cizilmez: kaldirilir
        kimlikler = {r["geomId"] for r in secim["ilceler"]}
        for g in [g for g in veri if g not in kimlikler]:
            del veri[g]
        yol.write_text(json.dumps(veri, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        RAPOR.mkdir(parents=True, exist_ok=True)
        with open(RAPOR / f"{anahtar}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["secim", "il", "ilce", "ysk_muhtarlik", "secmen", "durum", "tkgm_birimi"])
            w.writerows(sorted(rapor, key=lambda r: (r[1], r[2], r[3] or "")))
    return sayac, il_sayac, eski_secmen, yeni_secmen


def main():
    uygula = sys.argv[1] == "uygula"
    secimler = sys.argv[2:]
    birimler = tkgm_yukle()
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    print("TKGM: ilçe", len(birimler), "birim", sum(len(v) for v in birimler.values()))
    osm = osm_yukle()
    print("OSM: ilçe", len(osm), "poligon", sum(len(v) for v in osm.values()))
    bel = belediye_yukle()
    print("Belediye: ilçe", len(bel), "poligon", sum(len(v) for v in bel.values()))
    yer = yer_yukle()
    print("OSM yer noktası: ilçe", len(yer), "nokta", sum(len(v) for v in yer.values()))
    for anahtar in secimler:
        s, il_s, eski, yeni = isle(anahtar, birimler, geo, uygula, osm, bel, yer)
        T = s["secmen"]
        print(f"\n{anahtar}: YSK seçmeni {T:,} | haritaya bağlanan {yeni:,} (%{yeni / T * 100:.1f}); önceki {eski:,} (%{eski / T * 100:.1f})")
        print(f"   birebir {s['eslesen_birebir']}, yakın {s['eslesen_yakin']}, mevcut poligon {s['eslesen_eski']}, yeni belediye {s['eslesen_belediye']}, yeni OSM {s['eslesen_osm']}, OSM konumuyla {s['eslesen_konum']}, çakışma nedeniyle çizilmeyen {s['cakisan']}, eşleşmeyen {s['eslesmeyen']} muhtarlık "
              f"({s['eslesmeyen_secmen']:,} seçmen), muhtarlıksız sandık seçmeni {s['muhtarliksiz_secmen']:,}, "
              f"TKGM sınırı olmayan ilçelerde {s['sinirsiz_ilce_secmen']:,}, birleşen birim {s['birlesen_birim']}")
        kotu = sorted(il_s.items(), key=lambda x: x[1]["eslesen_secmen"] / max(x[1]["secmen"], 1))[:8]
        print("   en düşük iller:", ", ".join(f"{il} %{v['eslesen_secmen'] / max(v['secmen'], 1) * 100:.1f}" for il, v in kotu))
    if uygula:
        # sentetik ilcelere halef havuzundan kopyalanan poligonlardan yalniz bir secimin kullandiklari kalir
        kullanilan = collections.defaultdict(set)
        for f in MAHALLE.glob("*.json"):
            for g, kayit in json.loads(f.read_text(encoding="utf-8")).items():
                if g in SENTETIK:
                    kullanilan[g].update(kayit)
        for g in [g for g in geo if g in SENTETIK]:
            geo[g] = {pid: v for pid, v in geo[g].items() if pid in kullanilan[g]}
            if not geo[g]:
                del geo[g]
        GEO.write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        print("\nyazıldı:", GEO)
    else:
        print("\n(kontrol: hiçbir dosya yazılmadı)")


if __name__ == "__main__":
    main()
