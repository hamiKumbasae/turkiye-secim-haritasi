"""
Istanbul'un 1992-2008 arasindaki (32 ilceli) ilce sinirlarini bosluksuz ve ust uste binmeden kurar
ve bu donemin secimlerini o sinirlara baglar.

Donem: 3806 sayili Kanun (RG 03.06.1992; Avcilar, Bagcilar, Bahcelievler, Esenler, Gungoren,
Maltepe, Sultanbeyli, Tuzla) ile 5747 sayili Kanun (RG 22.03.2008) arasi. Bu arada Istanbul'da
ilce kurulmadi ya da kaldirilmadi; ayni sinirlar su secimlerde gecerli: 1994/1999/2004 yerel,
1995/1999/2002/2007 genel, 2007 referandumu.

Yontem (tahmin degil, her atama kaynakli; cikarimlar ayrica isaretli):
  1. Bugunku her ilce ya butunuyle tek bir 1992-2008 ilcesine aittir (BUTUN; Beylikduzu,
     Esenyurt, Cekmekoy ...), ya da mahalle mahalle paylastirilir (MAHALLE). Mahalle atamasinin
     dayanagi 5747'nin ek listeleri (data/kaynaklar/resmi_gazete/ilce_kurulus/5747.json);
     ilk kademe belediyesinin (belde) ilcesi DIE 2004 Tablo 9. Listede adi olmayan bugunku
     mahalleler icin dayanak satirda yazilidir (cevrelenmis, belde merkezi, komsuluk).
  2. Paylastirilan bir ilcede mahalle poligonlari (OSM muhtarlik) ilce poligonunu tam kaplamaz
     (gol, orman, askeri alan, sayisallastirma farki). Mahalle poligonlari ilce poligonuna
     kirpilir; kalan bosluk en yakin mahallenin ilcesine verilir (mahalle sinirlarindan
     orneklenen noktalarin Voronoi hucreleri). Boylece parcalarin birlesimi bugunku ilce
     poligonuna esittir: delik ve cift cizim yoktur.
  3. 1992-2008 ilcesinin poligonu = ona ait butun bugunku ilceler + paylastirilan ilcelerden
     ona dusen parcalar. Poligonu tek bir bugunku ilceye esit olan ilceler (Adalar, Avcilar ...)
     bugunku id'sini korur; digerleri HIST-Istanbul-<Ad>-9208 alir (Eminonu/Fatih: eski
     HIST-Istanbul-Eminonu/-Fatih, 1961-2007 icin ayni sinir).

Bilinen ve bilerek birakilan kucuk sapmalar (mahalle-alti; yol/parsel sinirli parcalar, bugunku
mahalle poligonlariyla ayrilamiyor) KISMI_NOTLAR'da, cikti dosyasinda ve ipucunda yazilidir.

Ciktilar:
  geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson (HIST-*-9208, Eminonu, Fatih)
  geo/historical/district_splits.json (hideIds)
  geo/historical/idari/istanbul_1992_2008.json (atama tablosu, alanlar, notlar)
  data/normalized/elections + meclis_harita (Istanbul satirlarinin geomId'si; oy degismez)

Sonra: apply_idari_merges.py (HISTK ve harita notlari), scripts/build.py.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_istanbul_1992_2008.py
"""
import json
import math
import pathlib
import sys

import shapely
from shapely.geometry import MultiPoint, mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from common.election_io import load_election, save_election  # noqa: E402
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur  # noqa: E402

MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
MAHALLE_GEO = ROOT / "geo/normalized/mahalle_geo.json"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = ROOT / "geo/historical/district_splits.json"
KAYIT = ROOT / "geo/historical/idari/istanbul_1992_2008.json"
MECLIS = ROOT / "data/normalized/meclis_harita"

SECIMLER = ["1994yerel", "1995", "1999", "1999yerel", "2002", "2004yerel", "2007", "2007referandum"]
MECLIS_KAYITLARI = [f"{y}yerel_{o}" for y in (1994, 1999, 2004) for o in ("bm", "igm")]
SPLIT_YEAR = 2008
PLAKA = 34

# 1992-2008 ilceleri ve bugunku govdeleri (adi ayni olan bugunku ilce). Eminonu'nun bugun govdesi
# yok (Fatih'in icinde).
ILCELER = {
    "Adalar": "001", "Avcılar": "004", "Bağcılar": "005", "Bahçelievler": "006", "Bakırköy": "007",
    "Bayrampaşa": "009", "Beşiktaş": "010", "Beykoz": "011", "Beyoğlu": "013", "Büyükçekmece": "014",
    "Çatalca": "015", "Esenler": "017", "Eyüp": "019", "Fatih": "020", "Gaziosmanpaşa": "021",
    "Güngören": "022", "Kadıköy": "023", "Kağıthane": "024", "Kartal": "025", "Küçükçekmece": "026",
    "Maltepe": "027", "Pendik": "028", "Sarıyer": "030", "Silivri": "031", "Sultanbeyli": "032",
    "Şile": "034", "Şişli": "035", "Tuzla": "036", "Ümraniye": "037", "Üsküdar": "038",
    "Zeytinburnu": "039", "Eminönü": None,
}
SABIT_ID = {"Eminönü": "HIST-Istanbul-Eminonu", "Fatih": "HIST-Istanbul-Fatih"}

K5747 = "5747 ek ({}) sayılı liste"
DIE = "belde ilçesi DİE 2004 Tablo 9"

# 2008'de kurulan ve tamami tek bir eski ilceden gelen ilceler
BUTUN = {
    "012": ("Büyükçekmece", "5747 (18) sayılı liste: Beylikdüzü, Gürpınar, Yakuplu beldeleri; " + DIE),
    "016": ("Ümraniye", "5747 (19) sayılı liste: Çekmeköy, Taşdelen, Alemdağ, Ömerli beldeleri ve köyler; " + DIE),
    "018": ("Büyükçekmece", "5747 (20) sayılı liste: Esenyurt, Kıraç beldeleri ve Yakuplu'nun Güzelyurt'u; " + DIE),
}

GOP, CAT, KC, ESN, BC, EYP = "Gaziosmanpaşa", "Çatalca", "Küçükçekmece", "Esenler", "Büyükçekmece", "Eyüp"

# bugunku ilce -> {bugunku mahalle: (1992-2008 ilcesi, dayanak)}
MAHALLE = {
    # Atasehir (5747 ek 16)
    "003": {
        **{m: ("Kadıköy", K5747.format(16)) for m in [
            "YENİSAHRA MAH.", "İÇERENKÖY MAH.", "İNÖNÜ MAH.", "KAYIŞDAĞI MAH.", "BARBAROS MAH.",
            "KÜÇÜKBAKKALKÖY MAH.", "ATATÜRK MAH."]},
        **{m: ("Üsküdar", K5747.format(16)) for m in ["FETİH MAH.", "ESATPAŞA MAH.", "ÖRNEK MAH."]},
        **{m: ("Ümraniye", K5747.format(16)) for m in [
            "YENİ ÇAMLICA MAH.", "YENİŞEHİR MAH.", "MİMAR SİNAN MAH.", "MEVLANA MAH.", "MUSTAFA KEMAL MAH."]},
        "FERHATPAŞA MAH.": ("Kartal", K5747.format(16) + " (Samandıra beldesi); " + DIE),
    },
    # Sancaktepe (5747 ek 21); cikarimlar geo/historical/district_mahalle_merges.yaml'da gerekceli
    "029": {
        **{m: ("Ümraniye", K5747.format(21) + " (Sarıgazi/Yenidoğan beldeleri); " + DIE) for m in [
            "MECLİS MAH.", "İNÖNÜ MAH.", "EMEK MAH.", "KEMAL TÜRKLER MAH.", "ATATÜRK MAH.", "YUNUS EMRE MAH.",
            "SAFA MAH.", "MEVLANA MAH.", "MERVE MAH."]},
        "SARIGAZİ MAH.": ("Ümraniye", "çıkarım: Sarıgazi beldesinin merkez mahallesi (listede 'Merkez')"),
        "YENİDOĞAN MAH.": ("Ümraniye", "çıkarım: Yenidoğan beldesinin merkez mahallesi"),
        "HİLAL MAH.": ("Ümraniye", "çıkarım: listede yok; yalnız Ümraniye kaynaklı mahallelere komşu"),
        "PAŞAKÖY MAH.": ("Ümraniye", "çıkarım: liste Kartal (Paşaköy köyünün yol güneyi) diyor; bugünkü "
                                     "poligon Ümraniye tarafına oturuyor (district_mahalle_merges.yaml)"),
        **{m: ("Kartal", K5747.format(21) + " (Samandıra beldesi); " + DIE) for m in [
            "ABDURRAHMANGAZİ MAH.", "AKPINAR MAH.", "OSMANGAZİ MAH.", "VEYSEL KARANİ MAH.", "EYÜP SULTAN MAH.",
            "FATİH MAH."]},
    },
    # Arnavutkoy (5747 ek 15)
    "002": {
        **{m: (GOP, K5747.format(15) + "; " + DIE) for m in [
            "ARNAVUTKÖY MERKEZ MAH.", "İMRAHOR MAH.", "İSLAMBEY MAH.", "YAVUZ SELİM MAH.",  # Arnavutköy beldesi
            "BOĞAZKÖY İSTİKLAL MAH.",  # Boğazköy beldesi
            "BOLLUCA MAH.", "HİCRET MAH.", "MAVİGÖL MAH.",  # Bolluca beldesi
            "HARAÇÇI MAH.", "KARLIBAYIR MAH.",  # Haraççı beldesi
            "TAŞOLUK MAH.", "ADNAN MENDERES MAH.", "FATİH MAH.", "MAREŞAL FEVZİ ÇAKMAK MAH.",
            "MEHMET AKİF ERSOY MAH.", "ÇİLİNGİR MAH."]},  # Taşoluk beldesi
        **{m: (GOP, K5747.format(15) + " köy cetveli (Gaziosmanpaşa Merkez bucağı)") for m in [
            "HACIMAŞLI MAH.", "YENİKÖY MAH.", "TAYAKADIN MAH."]},
        **{m: (GOP, "çıkarım: listede yok; çevresi yalnız Gaziosmanpaşa kaynaklı mahalleler (Arnavutköy/"
                    "Taşoluk beldeleri arasında, sonradan bölünmüş)") for m in [
            "ANADOLU MAH.", "MUSTAFA KEMAL PAŞA MAH.", "YUNUS EMRE MAH."]},
        **{m: (CAT, K5747.format(15) + "; " + DIE) for m in [
            "HADIMKÖY MAH.", "SAZLIBOSNA MAH.", "HASTANE MAH.", "YEŞİLBAYIR MAH.", "DELİKLİKAYA MAH.",
            "ÖMERLİ MAH.", "DURSUNKÖY MAH.",  # Hadımköy beldesi
            "DURUSU MAH."]},  # Durusu beldesi
        **{m: (CAT, K5747.format(15) + " köy cetveli (Çatalca, Boyalık bucağı)") for m in [
            "BAKLALI MAH.", "BOYALIK MAH.", "YASSIÖREN MAH.", "KARABURUN MAH."]},
        "TERKOS MAH.": (CAT, "çıkarım: listede yok; Terkos Gölü kıyısı, Durusu (eski adı Terkos) ve Çatalca "
                             "köyleri Baklalı/Karaburun'a komşu"),
    },
    # Basaksehir (5747 ek 17 + madde 2/3)
    "008": {
        **{m: (KC, K5747.format(17)) for m in [
            "KAYABAŞI MAH.", "ZİYA GÖKALP MAH.", "GÜVERCİNTEPE MAH.", "ALTINŞEHİR MAH."]},
        "ŞAMLAR MAH.": (KC, K5747.format(17) + " köy cetveli: Şamlar (Küçükçekmece)"),
        "BAŞAKŞEHİR MAH.": (KC, K5747.format(17) + ": 'Başakşehir' Küçükçekmece'den; bugünkü mahalle yalnız "
                                "Küçükçekmece kaynaklı mahallelere komşu"),
        "BAŞAK MAH.": (ESN, K5747.format(17) + ": ikinci 'Başakşehir' Esenler'den + madde 2/3 Esenler askerî "
                           "alanının Proje Yolu kuzeyi; bugünkü Başak Esenler'e bitişik tek Başakşehir mahallesi "
                           "(çıkarım: iki aynı adlı birimden hangisi olduğu)"),
        **{m: (BC, K5747.format(17) + " (Bahçeşehir beldesi); " + DIE) for m in [
            "BAHÇEŞEHİR 1. KISIM MAH.", "BAHÇEŞEHİR 2. KISIM MAH."]},
    },
    # Sultangazi (5747 ek 22)
    "033": {
        **{m: (GOP, K5747.format(22)) for m in [
            "SULTANÇİFTLİĞİ MAH.", "50. YIL MAH.", "UĞUR MUMCU MAH.", "CUMHURİYET MAH.", "CEBECİ MAH.",
            "MALKOÇOĞLU MAH.", "HABİBLER MAH.", "ZÜBEYDE HANIM MAH.", "GAZİ MAH.", "ESENTEPE MAH.",
            "75. YIL MAH.", "YUNUS EMRE MAH."]},
        "ESKİ HABİPLER MAH.": (GOP, K5747.format(22) + ": Habipler (Gaziosmanpaşa); Esenler'in parsel "
                                    "düzeyi Habipler parçası ayrılamıyor"),
        "YAYLA MAH.": (EYP, K5747.format(22) + ": Yayla (Eyüp)"),
    },
}

# Fatih: Eminonu'nun 33 mahallesi (split_eminonu_fatih.py ile ayni liste), kalan 24'u Fatih
EMINONU = [
    "ALEMDAR MAH.", "BALABANAĞA MAH.", "BİNBİRDİREK MAH.", "BEYAZIT MAH.", "CANKURTARAN MAH.",
    "DEMİRTAŞ MAH.", "EMİN SİNAN MAH.", "HACI KADIN MAH.", "HOBYAR MAH.", "HOCA GIYASETTİN MAH.",
    "HOCAPAŞA MAH.", "KALENDERHANE MAH.", "KATİP KASIM MAH.", "KEMALPAŞA MAH.", "KÜÇÜK AYASOFYA MAH.",
    "MİMAR HAYRETTİN MAH.", "MİMAR KEMALETTİN MAH.", "MERCAN MAH.", "MESİHPAŞA MAH.", "MOLLA FENARİ MAH.",
    "MOLLA HÜSREV MAH.", "MUHSİNE HATUN MAH.", "NİŞANCA MAH.", "ŞEHSUVAR BEY MAH.", "RÜSTEMPAŞA MAH.",
    "SARAÇ İSHAK MAH.", "SARIDEMİR MAH.", "SÜLEYMANİYE MAH.", "SULTAN AHMET MAH.", "SURURİ MAH.",
    "TAHTAKALE MAH.", "TAYA HATUN MAH.", "YAVUZ SİNAN MAH.",
]
FATIH_DAYANAK = "5747 madde 2/2 (Eminönü mahalleleriyle Fatih'e katıldı); Eminönü'nün 33 mahallesi"

# Mahalle poligonlariyla ayrilamayan kucuk kanun parcalari (bilerek birakildi)
KISMI_NOTLAR = [
    "Kadıköy'ün Atatürk ve Barbaros mahallelerinin E-80/O4 kuzeyi 2008'de Ümraniye'ye geçti (5747 m. 2/3); "
    "bugünkü Ümraniye'de ayrı mahalle değil, Ümraniye'de gösteriliyor.",
    "Esenler askerî alanının Proje Yolu güneyi Bağcılar'a geçti (5747 m. 2/3); Bağcılar'da gösteriliyor.",
    "Sultangazi'deki Habipler'in Esenler'den gelen parsel düzeyi parçası (5747 ek 22) Gaziosmanpaşa'da "
    "gösteriliyor.",
    "Esenyurt'taki Yeşilkent'in O3-D100 bağlantı yolu batısındaki Avcılar parçası (5747 ek 20) Büyükçekmece'de "
    "gösteriliyor.",
    "Bahçeşehir 1. Kısım'ın Avcılar'a katılan bir kısmı ve Ömerli'nin Pendik'e (Kurtdoğmuş) katılan tepeleri "
    "(5747 m. 2/4) bugünkü Avcılar ve Pendik'te gösteriliyor.",
    "Arnavutköy'deki Hacımaşlı'ya katılan Şamlar'ın baraj gölü kuzeyi (Küçükçekmece, 5747 ek 15) Gaziosmanpaşa'da "
    "gösteriliyor.",
]

MAHALLE["020"] = {}  # Fatih: mahalle_geo'dan doldurulur (main)

# km2 icin kaba cevrim (yalniz rapor)
KM2 = 111.32 ** 2 * math.cos(math.radians(41.0))


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    g = g if g.is_valid else make_valid(g)
    if g.geom_type == "GeometryCollection":
        g = unary_union([x for x in g.geoms if x.geom_type in ("Polygon", "MultiPolygon")])
    return g


def poligonsal(g):
    if g.is_empty:
        return g
    if g.geom_type == "GeometryCollection":
        return unary_union([x for x in g.geoms if x.geom_type in ("Polygon", "MultiPolygon")])
    return g if g.geom_type in ("Polygon", "MultiPolygon") else shapely.Polygon()


def paylastir(ilce, atama):
    """ilce poligonunu atama gruplarina boler: {grup: poligon}; birlesim = ilce."""
    parcalar = {}
    alinan = shapely.Polygon()
    for ad, (grup, geom) in atama.items():  # sira sabit: once gelen mahalle cakismayi alir
        p = poligonsal(geom.intersection(ilce).difference(alinan))
        if p.is_empty:
            continue
        alinan = alinan.union(p)
        parcalar[grup] = parcalar.get(grup, shapely.Polygon()).union(p)
    kalan = poligonsal(ilce.difference(alinan))
    if len(parcalar) > 1 and not kalan.is_empty:
        noktalar, etiket = [], []
        for grup, g in parcalar.items():
            sinir = shapely.segmentize(g.boundary, 0.0005)
            for x, y in shapely.get_coordinates(sinir):
                noktalar.append((round(x, 6), round(y, 6)))
                etiket.append(grup)
        tekil = {}
        for n, e in zip(noktalar, etiket):
            tekil.setdefault(n, e)
        pts = list(tekil)
        hucreler = shapely.voronoi_polygons(MultiPoint(pts), extend_to=ilce.envelope.buffer(0.05), ordered=True)
        by_grup = {}
        for h, n in zip(hucreler.geoms, pts):
            by_grup.setdefault(tekil[n], []).append(h)
        for grup, hs in by_grup.items():
            ek = poligonsal(unary_union(hs).intersection(kalan))
            parcalar[grup] = parcalar[grup].union(ek)
    elif not kalan.is_empty:
        (tek,) = parcalar
        parcalar[tek] = parcalar[tek].union(kalan)
    return parcalar


def main():
    modern = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in oku(MODERN)["features"]
              if f["properties"]["id"].startswith("TR-D-34-")}
    mahalle_geo = oku(MAHALLE_GEO)

    fatih = {v["ad"] for v in mahalle_geo["TR-D-34-020"].values()}
    assert set(EMINONU) <= fatih, set(EMINONU) - fatih
    MAHALLE["020"] = {m: ("Eminönü" if m in EMINONU else "Fatih", FATIH_DAYANAK) for m in sorted(fatih)}

    kayit_ilceler = {}
    parcalar = {ad: [] for ad in ILCELER}  # 1992-2008 ilcesi -> [(bugunku id, poligon)]
    for mid, g in sorted(modern.items()):
        kod = mid[-3:]
        if kod in MAHALLE:
            atama = MAHALLE[kod]
            mevcut = {v["ad"]: temiz(shape(v["geometry"])) for v in mahalle_geo[mid].values()}
            eksik, fazla = set(mevcut) - set(atama), set(atama) - set(mevcut)
            if eksik or fazla:
                raise SystemExit(f"HATA {mid}: atanmamis mahalle {sorted(eksik)}, bulunamayan {sorted(fazla)}")
            bol = paylastir(g, {m: (atama[m][0], mevcut[m]) for m in atama})
            kontrol = unary_union(list(bol.values()))
            fark = kontrol.symmetric_difference(g).area / g.area
            assert fark < 1e-6, (mid, fark)
            for grup, p in bol.items():
                parcalar[grup].append((mid, p))
            kayit_ilceler[mid] = {
                "tur": "mahalle",
                "parcalar": {grup: {"alanKm2": round(p.area * KM2, 2), "pay": round(p.area / g.area, 4)}
                             for grup, p in sorted(bol.items())},
                "mahalleler": {m: {"ilce": a[0], "dayanak": a[1]} for m, a in sorted(atama.items())},
            }
        elif kod in BUTUN:
            grup, dayanak = BUTUN[kod]
            parcalar[grup].append((mid, g))
            kayit_ilceler[mid] = {"tur": "butun", "ilce": grup, "dayanak": dayanak}
        else:
            grup = next(a for a, k in ILCELER.items() if k == kod)
            parcalar[grup].append((mid, g))

    hist = oku(HIST_GEO)
    feats = {f["properties"]["id"]: f for f in hist["features"]}
    splits = oku(SPLITS)
    sp34 = [e for e in splits[str(PLAKA)] if not e["syntheticId"].endswith("-9208")]
    atama_id, kayit_yeni = {}, {}
    for ad, ps in parcalar.items():
        ids = sorted({m for m, _ in ps})
        govde = ILCELER[ad]
        if len(ps) == 1 and govde and ids == [f"TR-D-34-{govde}"] and ad not in SABIT_ID:
            continue  # bugunku poligonuyla ayni
        sid = SABIT_ID.get(ad) or "HIST-Istanbul-{}-9208".format(
            ad.translate(str.maketrans("İıĞğÜüŞşÖöÇç", "IiGgUuSsOoCc")))
        g = unary_union([p for _, p in ps])
        yabanci = unary_union([v for k, v in modern.items() if k not in ids])
        g = delikleri_doldur(g, bilesen_delikleri([modern[i] for i in ids]), yabanci)
        g = shapely.set_precision(g, 1e-5)
        feats[sid] = {"type": "Feature", "properties": {"id": sid, "plaka": PLAKA}, "geometry": mapping(g)}
        if sid in SABIT_ID.values():
            for e in sp34:
                if e["syntheticId"] == sid:
                    e["hideIds"] = ids
        else:
            sp34.append({"hideIds": ids, "splitYear": SPLIT_YEAR, "syntheticId": sid})
        atama_id[ad] = sid
        kayit_yeni[ad] = {"id": sid, "bugunkuIlceler": ids, "alanKm2": round(g.area * KM2, 1)}
        print(f"{sid}: {', '.join(i[-3:] for i in ids)}  ({g.area * KM2:.1f} km2)")

    hist["features"] = sorted(feats.values(), key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    splits[str(PLAKA)] = sp34
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")

    # secim satirlari: Istanbul satiri adiyla 1992-2008 ilcesine baglanir
    for anahtar in SECIMLER + MECLIS_KAYITLARI:
        meclis = anahtar in MECLIS_KAYITLARI
        p = MECLIS / f"{anahtar}.json"
        rec = oku(p) if meclis else load_election(anahtar)
        degisen = []
        for r in rec["ilceler"]:
            if r.get("plaka") != PLAKA or r["ad"] not in ILCELER:
                continue
            if r["ad"] == "Fatih" and not any(x["ad"] == "Eminönü" and x.get("plaka") == PLAKA for x in rec["ilceler"]):
                continue  # Eminonu satiri olmayan kayitta Fatih bugunku poligonunda kalir (Eminonu alani bos kalmasin)
            yeni = atama_id.get(r["ad"], f"TR-D-34-{ILCELER[r['ad']]}")
            if r.get("geomId") != yeni:
                degisen.append(f"{r['ad']}: {r.get('geomId')} -> {yeni}")
                r["geomId"] = yeni
        if degisen:
            if meclis:
                p.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
            else:
                save_election(anahtar, rec)
        print(anahtar, degisen or "degisiklik yok")

    KAYIT.write_text(json.dumps({
        "not": "build_istanbul_1992_2008.py ile üretilir; elle düzenlenmez.",
        "donem": {"baslangic": "1992-06-03", "bitis": "2008-03-22",
                  "kanunlar": ["3806 (RG 03.06.1992)", "5747 (RG 22.03.2008, mükerrer 26824)"]},
        "secimler": SECIMLER + MECLIS_KAYITLARI,
        "yontem": __doc__.split("Yontem")[1].split("Bilinen")[0].strip(),
        "ilceler": kayit_yeni,
        "bugunkuIlceler": kayit_ilceler,
        "kismiNotlar": KISMI_NOTLAR,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi:", KAYIT.relative_to(ROOT))


if __name__ == "__main__":
    main()
