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
  5b. Konum kurali (Konum): alaninin yarisindan fazlasi ilcenin 2 km bandi disinda kalan aday (TKGM, OSM,
     belediye, mevcut poligon) alinmaz; ilcenin kapsami = ilce poligonu + o ilcenin kendisi bantta duran TKGM
     birimleri (sadelestirilmis ilce sinirinin yanlis oldugu yerlerde TKGM ikinci bagimsiz sinirdir). Poligon
     olmayan ya da alani sifir aday da alinmaz. Muhtarlik baska adaya gecer ya da bos kalir.
  5c. Ayni secimde ayni ilcede ayni sinira (IoU >= %95) dusen TKGM birimleri tek kayitta toplanir (ad: muhtarlik
     adlari ' + ' ile).
  6. eslesmeyen muhtarliklar raporlanir (docs/rapor/mahalle_eslesme/<secim>.csv)
Son adim (yalniz uygula, butun secimlerin verisiyle; geometri_son_islem):
  - TKGM x TKGM ortusmesi: ayni ilcede en az bir secimde birlikte cizilen ve anlamli ortusen (>= 1 ha ve kucugun
    >= %1'i) iki TKGM biriminde ortusme kucuk birime kalir, buyukten cikarilir (ic ice birimde icteki korunur,
    kismi ortusmede kucuk olan alir; esit alanda kucuk kimlik). Ham TKGM sinirindan her calistirmada yeniden
    hesaplanir (tekrarlanabilir).
  - Butun poligonlar make_valid + 1e-4 (4 ondalik) izgaraya oturtulur, dis halka saat yonu tersi / delik saat
    yonu yazilir; poligon olmayan parca atilir.
  - Hicbir secimde kullanilmayan poligon silinir (Istanbul TR-D-34-* haric: tarihsel Istanbul betikleri onlari
    okur).
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
KONUM_RAPOR = RAPOR / "konum_kurali.csv"   # 5b: kapsam disi adaylar (alinmayan / dogrulanip alinan)
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


def tkgm_yukle(konum=None):
    """konum (Konum) verilirse ilcesinin kapsami disinda kalan birimler atilir (TKGM ham verisinde baska
    yerin sinirini tasiyan birimler var: Mazgirt 'Ayvatlı' Kayseri Pınarbaşı'nda)."""
    birimler = collections.defaultdict(list)   # geomId -> [feature]
    for f in sorted(TKGM_DIR.glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            g = ft["properties"].get("geomId") or ILCE_ALIAS.get(fold(ft["properties"].get("ilce")))
            ft["properties"]["geomId"] = g
            if g and ft.get("geometry"):
                birimler[g].append(ft)
    if konum is not None:
        konum.tkgm_ekle(birimler)
        for g in list(birimler):
            birimler[g] = [ft for ft in birimler[g]
                           if konum.uygun(g, ft["geometry"], ("TKGM", ft["properties"]["tkgm_id"]), ft["properties"].get("ad"))]
    return birimler


# ---------------------------------------------------------------- konum kurali (5b)
IZDUSUM = "+proj=aea +lat_0=39 +lon_0=35 +lat_1=37 +lat_2=41 +ellps=GRS80 +units=m +no_defs"
KONUM_BANT_M = 2000      # ilce katmani ~%8 noktaya sadelestirildi: siniri 1-2 km sapabiliyor
KONUM_DISI_ESIK = 0.5    # alaninin bundan fazlasi kapsam disindaysa aday alinmaz
DOGRULAMA_IOU = 0.5      # baska kaynagin ayni ilceye verdigi ayni adli poligonla bu kadar ortusen aday dogrulanmis sayilir


def poligonal(g):
    """make_valid edilmis, yalniz poligon parcali geometri (bos olabilir)."""
    import shapely
    from shapely.validation import make_valid
    if g is None or g.is_empty:
        return shapely.Polygon()
    if not g.is_valid:
        g = make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parca = [p for p in shapely.get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(parca) if parca else shapely.Polygon()


class Konum:
    """Bir poligonun ilcesinde durup durmadigi. Kapsam(g) = ilce poligonu ve g'nin (ilce poligonunun 2 km
    bandinda duran) TKGM birimlerinin birlesimi, 2 km tamponla. Aday alaninin > KONUM_DISI_ESIK'i kapsam
    disindaysa uygun degil. Sentetik (tarihsel) ilcede kapsam halef ilcelerin birlesimidir. Ilce katmaninda
    olmayan kimlikte kural uygulanmaz."""

    def __init__(self, ilce_geo=None):
        import numpy as np
        import shapely
        from pyproj import Transformer
        from shapely.geometry import shape
        tr = Transformer.from_crs("EPSG:4326", IZDUSUM, always_xy=True)
        self._izd = lambda g: shapely.transform(g, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
        feats = json.loads((ilce_geo or ILCE_GEO).read_text(encoding="utf-8"))["features"]
        self.ilce = {f["properties"]["id"]: poligonal(self._izd(shape(f["geometry"]))) for f in feats}
        self._bant = {}
        self._kapsam = {}
        self._tkgm = {}
        self._dog = {}
        self.reddedilen = []   # (geomId, kaynak, kimlik, kapsam disi pay)
        self.dogrulanan = []   # kapsam disinda ama baska kaynakca dogrulanan

    def izd(self, geom_json):
        from shapely.geometry import shape
        try:
            return poligonal(self._izd(shape(geom_json)))
        except Exception:   # noqa: BLE001 - bozuk geometri: poligon degil sayilir
            import shapely
            return shapely.Polygon()

    def bant(self, g):
        if g not in self._bant:
            parca = [self.ilce[h] for h in SENTETIK.get(g, [g]) if h in self.ilce]
            import shapely
            self._bant[g] = shapely.union_all(parca).buffer(KONUM_BANT_M) if parca else None
        return self._bant[g]

    def tkgm_ekle(self, birimler):
        """Kapsami genisleten TKGM birimleri: kendi ilcesinin bandinda duranlar (birim basina ham sinir).
        Butun birimler ayrica dogrulayici olarak kaydedilir (ilce kimligi TKGM'nin kendi kaydindan)."""
        import shapely
        for g, lst in birimler.items():
            b = self.bant(g)
            ic = []
            for ft in lst:
                p = self.izd(ft["geometry"])
                self.dogrulayici_ekle(g, "TKGM", ft["properties"].get("ad"), p)
                if b is not None and p.area and p.difference(b).area / p.area <= KONUM_DISI_ESIK:
                    ic.append(p)
            self._tkgm[g] = shapely.union_all(ic).simplify(100) if ic else None

    def dogrulayici_ekle(self, g, kaynak, ad, p):
        """Bir kaynagin kendi kaydinda g ilcesine verdigi poligon: yalniz ham kaynaklar (TKGM birimi, belediye
        siniri; her calistirmada aynidir, tekrarlanabilirlik icin mahalle_geo.json'daki poligonlar sayilmaz).
        Bagimsiz iki kaynak ayni adli ayni sekli ayni ilceye veriyorsa ilce katmani o yerde yanlistir; aday
        kapsam disinda olsa da alinir."""
        if p.is_empty or not p.area:
            return
        self._dog.setdefault(g, []).append((kaynak, ad_anahtari(ad or ""), p))

    def dogrulanir(self, g, kaynak, ad, p):
        a = ad_anahtari(ad or "")
        if not a:
            return False
        for h in SENTETIK.get(g, [g]):
            for k2, a2, q in self._dog.get(h, []):
                if k2 == kaynak or difflib.SequenceMatcher(None, a, a2).ratio() < 0.85 or not q.intersects(p):
                    continue
                if q.intersection(p).area / (q.union(p).area or 1) >= DOGRULAMA_IOU:
                    return True
        return False

    def kapsam(self, g):
        if g not in self._kapsam:
            import shapely
            b = self.bant(g)
            if b is None:
                self._kapsam[g] = None
            else:
                ek = [self._tkgm[h] for h in SENTETIK.get(g, [g]) if self._tkgm.get(h) is not None]
                self._kapsam[g] = shapely.union_all([b] + [e.buffer(KONUM_BANT_M) for e in ek]) if ek else b
        return self._kapsam[g]

    def disi_pay(self, g, geom_json):
        """Kapsam disi alan payi; poligon degilse/alani yoksa None; kapsam yoksa 0."""
        p = self.izd(geom_json)
        if p.is_empty or p.area <= 1:
            return None
        k = self.kapsam(g)
        if k is None:
            return 0.0
        b = self.bant(g)
        if p.difference(b).area / p.area <= KONUM_DISI_ESIK:   # hizli yol: ilce bandinda
            return p.difference(b).area / p.area
        return p.difference(k).area / p.area

    def uygun(self, g, geom_json, kimlik=None, ad=None):
        """kimlik: (kaynak, anahtar); kaynak 'TKGM' | 'OSM' | 'Belediye' | 'ttezer'. Kapsam disindaki aday,
        baska bir kaynak ayni adli ayni sekli (IoU >= DOGRULAMA_IOU) ayni ilceye veriyorsa yine alinir."""
        pay = self.disi_pay(g, geom_json)
        ok = pay is not None and pay <= KONUM_DISI_ESIK
        if not ok and pay is not None and kimlik is not None and ad is not None \
                and self.dogrulanir(g, kimlik[0], ad, self.izd(geom_json)):
            self.dogrulanan.append((g, kimlik[0], str(kimlik[1]), round(pay, 3)))
            return True
        if not ok and kimlik is not None:
            self.reddedilen.append((g, kimlik[0], str(kimlik[1]), None if pay is None else round(pay, 3)))
        return ok


# Bursa dosyasi EPSG:2320 (ED50 / TM30) etiketli ama koordinatlar TUREF (ITRF96 / TM30, EPSG:5254):
# 2320 olarak okununca ayni adli TKGM sinirlarina gore medyan ~180 m guneyde kaliyor, 5254 ile ortusuyor.
BELEDIYE_CRS_DUZELT = {16: 5254}
# Bursa dosyasinda Harmancık ve Keles'in ilce_adi alani yer degistirmis: 'HARMANCIK' etiketli 42 sinirin
# 42'si de adiyla Keles muhtarligi ve Keles'te duruyor, 'KELES' etiketli 31'in 31'i Harmancık (2023 YSK
# muhtarlik adlariyla; 2026-10-31 geometri duzeltmesi). (plaka, fold edilmis ilce_adi) -> dogru ilce adi
BELEDIYE_ILCE_DUZELT = {(16, "HARMANCIK"): "KELES", (16, "KELES"): "HARMANCIK"}


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
            ilce_f = fold(ilce or "")
            g = ilce_id.get((plaka, BELEDIYE_ILCE_DUZELT.get((plaka, ilce_f), ilce_f)))
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


AYNI_SINIR_IOU = 0.95


def ayni_sinirlilari_birlestir(gruplar):
    """gruplar: {tkgm_id: [(muhtarlik, feature, yontem)]}. Sinirlari neredeyse ayni (IoU >= AYNI_SINIR_IOU)
    birimlerin listeleri en kucuk kimlikli (str) birimde toplanir. Doner (yeni gruplar, birlesen kimlikler)."""
    if len(gruplar) < 2:
        return gruplar, set()
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    tids = sorted(gruplar, key=str)
    sekil = [poligonal(shape(gruplar[t][0][1]["geometry"])) for t in tids]
    agac = STRtree(sekil)
    ata = {t: t for t in tids}

    def kok(t):
        while ata[t] != t:
            t = ata[t]
        return t
    for i, a in enumerate(sekil):
        if a.is_empty:
            continue
        for j in agac.query(a):
            if j <= i or sekil[j].is_empty:
                continue
            b = sekil[j]
            ic = a.intersection(b).area
            if ic and ic / (a.union(b).area or 1) >= AYNI_SINIR_IOU:
                ri, rj = kok(tids[i]), kok(tids[j])
                if ri != rj:
                    ata[max(ri, rj, key=str)] = min(ri, rj, key=str)
    yeni, birlesen = {}, set()
    for t in tids:
        r = kok(t)
        yeni.setdefault(r, []).extend(gruplar[t])
        if r != t:
            birlesen.add(r)
    return yeni, birlesen


def konum_uygun_onbellek(konum, g, pid, pv):
    """Mevcut (mahalle_geo.json) poligon icin konum kurali; secimler arasinda onbellekli."""
    on = konum.__dict__.setdefault("_mevcut", {})
    if (g, pid) not in on:
        kaynak = {"t": "ttezer", "r": "OSM"}.get(pid[:1], "diğer")
        on[(g, pid)] = konum.uygun(g, pv["geometry"], (kaynak, pid), pv.get("ad"))
    return on[(g, pid)]


def isle(anahtar, birimler, geo, uygula, osm=None, bel=None, yer=None, kural=None):
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
                # 5b: ilcesinin kapsami disinda duran (ve baska kaynakca dogrulanmayan) mevcut poligon kullanilmaz
                if kural is not None and not konum_uygun_onbellek(kural, g, pid, pv):
                    continue
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
            # yalniz bu secimde zaten kullanilan sinirlar dislanir: onceki bir calistirmada eklenmis OSM siniri
            # yeniden aday olabilmeli (yoksa ayni adli baska mahallesi olan ilcede ikinci calistirmada adla
            # eslesemeyip duser; betik tekrar calistirilinca ayni sonucu vermeli)
            aday_ft = [ft for ft in (kaynak or {}).get(g, []) if ft["properties"]["tkgm_id"] not in eski_gruplar]
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
                # daha once bir muhtarliga verilmis OSM siniri yalniz ayni adli muhtarliga verilir (2009'da koy
                # oldugu icin listede olmayan BOYALI'nin siniri yakin adla BOYALICA'ya gecip sonraki secimlere
                # tasinmasin)
                if pid in geo.get(g, {}) and ad_anahtari(geo[g][pid].get("ad") or "") != ad_anahtari(tkgm_aday[mid]["ad"]):
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
        # 5c) ayni secimde ayni sinira (IoU >= AYNI_SINIR_IOU) dusen TKGM birimleri tek kayitta toplanir
        gruplar, ayni_sinir = ayni_sinirlilari_birlestir(gruplar)
        ilce_kayit = {}
        for tid, lst in gruplar.items():
            ft = lst[0][1]
            k = f"k{tid}"
            if tid in ayni_sinir:
                sayac["ayni_sinir_birlesen"] += 1
                rapor.append([anahtar, il, ilce["ilceAdi"], " + ".join(m["ad"] for m, _, _ in lst), sum(m["secmen"] for m, _, _ in lst),
                              "aynı sınırlı TKGM birimleri tek kayıtta toplandı",
                              " = ".join(sorted({f["properties"]["ad"] for _, f, _ in lst}))])
            elif len(lst) > 1:
                sayac["birlesen_birim"] += 1
                rapor.append([anahtar, il, ilce["ilceAdi"], " + ".join(m["ad"] for m, _, _ in lst), sum(m["secmen"] for m, _, _ in lst),
                              "birden çok muhtarlık tek sınıra düştü (toplandı)", ft["properties"]["ad"]])
            ilce_kayit[k] = kayit_yap(topla([m for m, _, _ in lst]), col_to_key, ana_partiler)
            if uygula:
                if tid in ayni_sinir:
                    ad = " + ".join(sorted(m["ad"] for m, _, _ in lst))
                else:
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


ANLAMLI_M2, ANLAMLI_PAY = 10_000, 0.01    # 'anlamli ortusme' (geometri denetimiyle ayni): >= 1 ha ve kucugun >= %1'i
KORUNAN_ONEK = ("TR-D-34-",)   # kullanilmasa da silinmez: tarihsel Istanbul betikleri (build_istanbul_*) okur


def ham_tkgm_dizini(birimler):
    """'k<tkgm_id>' -> ham TKGM geometrisi (bolumlu birimlerin birlesimi 'kb...' dahil)."""
    d = {}
    for g in sorted(birimler):
        lst = birimler[g]
        for ft in lst:
            d.setdefault(f"k{ft['properties']['tkgm_id']}", ft["geometry"])
        for ft in bolum_birlesimleri(lst):
            d.setdefault(f"k{ft['properties']['tkgm_id']}", ft["geometry"])
    return d


def _json_geo(g):
    from shapely.geometry import mapping
    m = mapping(g)
    return {"type": m["type"], "coordinates": yuvarla4(m["coordinates"])}


def onar(g):
    """make_valid + 1e-4 izgara (4 ondalik; GEOS hassasiyet indirgemesi gecerli cikti verir) + delikler dis
    halkanin tersi yonde. Poligon olmayan parcalar atilir; bos donebilir."""
    import shapely
    g = poligonal(g)
    if g.is_empty:
        return g
    g = poligonal(shapely.set_precision(g, 1e-4))
    return shapely.orient_polygons(g) if not g.is_empty else g


def onarim_gerekli(gj):
    """Gecersiz, poligon olmayan ya da deligi dis halkayla ayni yonde yazilmis geometri mi?"""
    from shapely.geometry import shape
    if gj.get("type") not in ("Polygon", "MultiPolygon"):
        return True
    try:
        g = shape(gj)
    except Exception:   # noqa: BLE001
        return True
    if g.is_empty or not g.is_valid or g.area <= 0:
        return True
    for p in getattr(g, "geoms", [g]):
        if p.interiors and any(h.is_ccw == p.exterior.is_ccw for h in p.interiors):
            return True
    return False


def tkgm_ortusmelerini_coz(geo, ham, kullanim):
    """Ayni ilcede en az bir secimde birlikte cizilen ve anlamli ortusen iki TKGM biriminde ortusme kucuk birime
    kalir: buyugun sinirindan cikarilir (esit alanda buyuk kimlikliden). Ham sinirdan hesaplanir. Kalan alani
    %1'in altina inen birim ham haliyle birakilir (sayilir). Doner sayac."""
    import numpy as np
    import shapely
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.strtree import STRtree
    tr = Transformer.from_crs("EPSG:4326", IZDUSUM, always_xy=True)
    izd = lambda g: shapely.transform(g, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))  # noqa: E731
    sayac = collections.Counter()
    for g in sorted(geo):
        secimler = kullanim.get(g, {})
        anahtarlar = sorted(k for k in geo[g] if k.startswith("k") and any(k in v for v in secimler.values()))
        if len(anahtarlar) < 2:
            continue
        taban = {k: poligonal(shape(ham.get(k) or geo[g][k]["geometry"])) for k in anahtarlar}
        anahtarlar = [k for k in anahtarlar if not taban[k].is_empty]
        sekil = [taban[k] for k in anahtarlar]
        m2 = {k: izd(taban[k]).area for k in anahtarlar}
        agac = STRtree(sekil)
        cikar = collections.defaultdict(list)
        for i, a in enumerate(anahtarlar):
            for j in agac.query(sekil[i]):
                if j <= i:
                    continue
                b = anahtarlar[j]
                if not any(a in v and b in v for v in secimler.values()):
                    continue
                ic = sekil[i].intersection(sekil[j])
                if ic.is_empty:
                    continue
                ic_m2 = izd(ic).area
                if ic_m2 < ANLAMLI_M2 or ic_m2 < ANLAMLI_PAY * min(m2[a], m2[b]):
                    continue
                kucuk, buyuk = sorted((a, b), key=lambda k: (m2[k], k))
                cikar[buyuk].append(kucuk)
                sayac["ortusen_cift"] += 1
        for k in anahtarlar:
            if k in cikar:
                kalan = onar(taban[k].difference(shapely.union_all([taban[x] for x in cikar[k]])))
                if kalan.is_empty or izd(kalan).area < 0.01 * m2[k]:
                    sayac["kalan_cok_kucuk_ham_birakildi"] += 1
                    yeni = taban[k]
                else:
                    sayac["kirpilan_birim"] += 1
                    yeni = kalan
                geo[g][k]["geometry"] = _json_geo(onar(yeni))
            elif ham.get(k):
                geo[g][k]["geometry"] = ham[k]   # onceki calistirmada kirpilmis olabilir: ham sinira don
    return sayac


def geometri_son_islem(geo, ham):
    """Butun secimlerin verisiyle (data/normalized/mahalle/*.json): kullanilmayan poligonlari sil (KORUNAN_ONEK
    haric), TKGM x TKGM ortusmesini coz, gecersiz / poligon olmayan / delik yonu ters geometriyi onar."""
    kullanim = collections.defaultdict(dict)   # geomId -> secim -> {anahtar}
    for f in sorted(MAHALLE.glob("*.json")):
        for g, kayit in json.loads(f.read_text(encoding="utf-8")).items():
            kullanim[g][f.stem] = set(kayit)
    sayac = collections.Counter()
    for g in list(geo):
        kul = set().union(*kullanim.get(g, {}).values()) if kullanim.get(g) else set()
        if not g.startswith(KORUNAN_ONEK):
            for pid in [p for p in geo[g] if p not in kul]:
                del geo[g][pid]
                sayac["silinen_kullanilmayan"] += 1
        if not geo[g]:
            del geo[g]
    sayac.update(tkgm_ortusmelerini_coz(geo, ham, kullanim))
    from shapely.geometry import shape
    for g in sorted(geo):
        for pid in sorted(geo[g]):
            gj = geo[g][pid]["geometry"]
            if not onarim_gerekli(gj):
                continue
            try:
                yeni = onar(shape(gj))
            except Exception:   # noqa: BLE001 - shapely okuyamadi
                yeni = None
            if yeni is None or yeni.is_empty:
                sayac["onarilamayan"] += 1
                continue
            geo[g][pid]["geometry"] = _json_geo(yeni)
            sayac["onarilan"] += 1
    return dict(sorted(sayac.items()))


def main():
    uygula = sys.argv[1] == "uygula"
    secimler = sys.argv[2:]
    konum = Konum()
    bel = belediye_yukle()
    for g, lst in bel.items():   # belediye siniri dogrulayicidir (once), sonra kendisi de kurala tabi
        for ft in lst:
            konum.dogrulayici_ekle(g, "Belediye", ft["properties"]["ad"], konum.izd(ft["geometry"]))
    birimler = tkgm_yukle(konum)
    bel = {g: [ft for ft in lst if konum.uygun(g, ft["geometry"], ("Belediye", ft["properties"]["tkgm_id"]), ft["properties"]["ad"])]
           for g, lst in bel.items()}
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    print("TKGM: ilçe", len(birimler), "birim", sum(len(v) for v in birimler.values()))
    osm = osm_yukle()
    osm = {g: [ft for ft in lst if konum.uygun(g, ft["geometry"], ("OSM", ft["properties"]["tkgm_id"]), ft["properties"]["ad"])]
           for g, lst in osm.items()}
    print("OSM: ilçe", len(osm), "poligon", sum(len(v) for v in osm.values()))
    print("Belediye: ilçe", len(bel), "poligon", sum(len(v) for v in bel.values()))
    yer = yer_yukle()
    print("OSM yer noktası: ilçe", len(yer), "nokta", sum(len(v) for v in yer.values()))
    for anahtar in secimler:
        s, il_s, eski, yeni = isle(anahtar, birimler, geo, uygula, osm, bel, yer, konum)
        T = s["secmen"]
        print(f"\n{anahtar}: YSK seçmeni {T:,} | haritaya bağlanan {yeni:,} (%{yeni / T * 100:.1f}); önceki {eski:,} (%{eski / T * 100:.1f})")
        print(f"   birebir {s['eslesen_birebir']}, yakın {s['eslesen_yakin']}, mevcut poligon {s['eslesen_eski']}, yeni belediye {s['eslesen_belediye']}, yeni OSM {s['eslesen_osm']}, OSM konumuyla {s['eslesen_konum']}, çakışma nedeniyle çizilmeyen {s['cakisan']}, eşleşmeyen {s['eslesmeyen']} muhtarlık "
              f"({s['eslesmeyen_secmen']:,} seçmen), muhtarlıksız sandık seçmeni {s['muhtarliksiz_secmen']:,}, "
              f"TKGM sınırı olmayan ilçelerde {s['sinirsiz_ilce_secmen']:,}, birleşen birim {s['birlesen_birim']}, "
              f"aynı sınırlı birleşen {s['ayni_sinir_birlesen']}")
        kotu = sorted(il_s.items(), key=lambda x: x[1]["eslesen_secmen"] / max(x[1]["secmen"], 1))[:8]
        print("   en düşük iller:", ", ".join(f"{il} %{v['eslesen_secmen'] / max(v['secmen'], 1) * 100:.1f}" for il, v in kotu))
    print(f"\nkonum kuralı: kapsam dışı alınmayan aday {len(konum.reddedilen)}, kapsam dışı ama başka kaynakça doğrulanan {len(konum.dogrulanan)}")
    KONUM_RAPOR.parent.mkdir(parents=True, exist_ok=True)
    if uygula:
        with open(KONUM_RAPOR, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["geomId", "kaynak", "anahtar", "kapsam_disi_pay", "karar"])
            w.writerows(sorted({(*r, "alınmadı") for r in konum.reddedilen} | {(*r, "doğrulandı, alındı") for r in konum.dogrulanan},
                               key=lambda r: (r[0], r[1], r[2])))
        ozet = geometri_son_islem(geo, ham_tkgm_dizini(birimler))
        print("son işlem:", ", ".join(f"{k} {v}" for k, v in ozet.items()))
        GEO.write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        print("\nyazıldı:", GEO)
    else:
        print("\n(kontrol: hiçbir dosya yazılmadı)")


if __name__ == "__main__":
    main()
