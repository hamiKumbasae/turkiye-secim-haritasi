"""
Birden cok eski ilceden kurulan ilcelerin (lineageStatus kanun_cok_kaynak) alanini
mahalle poligonlariyla eski ilceler arasinda bolustürür (Faz 4b, pilot: İstanbul).

Ornek: Arnavutköy (5747, 2008) = Gaziosmanpaşa'nın 26 + Çatalca'nın 18 + Küçükçekmece'nin
1 birimi. 2008 oncesi secimlerde Gaziosmanpaşa satiri Arnavutköy'ün dogusunu, Çatalca
satiri batisini kapsamali.

Yontem (tahmin yok; cikarim ayrica isaretli):
  1. Kanun ek listesindeki her birimin eski ilcesi (data/kaynaklar/resmi_gazete/ilce_kurulus/
     <kanun>.json; ilk kademe belediyesinin ilcesi DIE 2004).
  2. Guncel mahalle poligonu (geo/normalized/mahalle_geo.json) adiyla bir birime eslesir:
     ayni ad; belde "Merkez" mahallesi = belde adi; belde adini tasiyan guncel mahalle
     (Hadımköy, Durusu) = o beldenin (tek) ilcesi; ELLE_AD'daki yazim esleri.
  3. Adi eslesmeyen guncel mahalle ya da mahalle poligonlarinin kaplamadigi alan (gol,
     orman) parcasi: butun siniri TEK bir eski ilcenin mahalleleriyle cevriliyse ve ilcenin
     dis sinirina degmiyorsa o ilceye verilir (`cikarim: cevrelenmis`). Kanunda iki ilce
     arasinda paylasildigi yazan birimler (BELIRSIZ_BIRIM) cikarimla atanmaz.
  4. Kalan alan 'belirsiz' parcadir; haritada tarali, adaylariyla.
  6. Elle DONEMSEL tablosu olmayan cok kaynakli ilcelerde donemsel baglilik sayim dizininden
     (data/kaynaklar/tuik/nufus_sayimi/<yil>_koyler.json, extract_sayim_koyleri.py) otomatik:
     birimin (koy/belde) sayimdaki ilcesi kanundaki eski ilcesiyle (ya da onun kanunla ayrildigi
     ata ilceyle) ayniysa o sayimda ayni sayilir; bulunamazsa ya da farkliysa o donem belirsiz.
     Dizin OCR'dan okundugu icin hatalar yalniz belirsiz alani buyutur, yanlis ilceye atamaz.
  5. Donemsel baglilik (DONEMSEL): birimin ilcesi nufus sayimi idari bolunus kitaplarindan
     (DIE 1960, 1985, 1990) okunmussa, iki sayim arasindaki secimler icin birim ancak iki
     sayimda da ayni ilcedeyse atanir; arada ilce degistirmisse o donemde belirsizdir.
     Ilk sayimdan onceki secimlere bolusum uygulanmaz.
Parcalar ayriktir ve guncel ilce poligonunu tam boler (kirpma + sirali fark).

Cikti: geo/historical/idari/mahalle_bolusumu.json (atama raporu),
       geo/historical/idari/mahalle_bolusumu.geojson (PARCA-*/BELIRSIZ-* poligonlari).
apply_idari_merges.py bu parcalari eski ilcelerin sentetik birlesimlerine katar.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_mahalle_bolusumu.py
"""
import collections
import difflib
import json
import pathlib
import re
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.turkish_text import fold  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
OUT_JSON = IDARI / "mahalle_bolusumu.json"
OUT_GEO = IDARI / "mahalle_bolusumu.geojson"
EPS = 2e-4   # derece (~20 m): komsuluk/degme toleransi
MIN_ALAN = 1e-7  # bundan kucuk kirpma kirintilari atilir

# pilot: yeni ilce geomId -> kanun kaynak dosyasi ve ilce adi
ILCELER = {
    "TR-D-34-002": {"kanun": "5747", "ad": "Arnavutköy"},
    "TR-D-34-033": {"kanun": "5747", "ad": "Sultangazi"},
    "TR-D-34-018": {"kanun": "5747", "ad": "Esenyurt"},
    "TR-D-34-008": {"kanun": "5747", "ad": "Başakşehir"},
    # 1987 oncesi (Umraniye 3392 ile Uskudar ve Beykoz'dan kurulmadan once); 1991-2007'de
    # bu alan repodaki HIST-Istanbul-Umraniye/Kadikoy/Uskudar/Kartal birlesimlerinde
    "TR-D-34-016": {"kanun": "5747", "ad": "Çekmeköy"},
    "TR-D-34-029": {"kanun": "5747", "ad": "Sancaktepe"},
    "TR-D-34-003": {"kanun": "5747", "ad": "Ataşehir"},
}
# Donemsel baglilik: ilce -> {"anlar": [sayim tarihleri], "birimler": {birim: [ilce@anlar]}}.
# Son an kanunun tarihidir (deger kanun ek listesinden). 1960'ta Eyup'e bagli olup 309 sayili
# Kanunla (1963) Gaziosmanpasa'ya gecen koyler 'Gaziosmanpaşa' yazilir (zincir Eyup'e cikar).
BAHCESEHIR_NOT = ("Bahçeşehir beldesi: DİE 1994 yerel seçim kitabında yok; 1999 (0014361.pdf s. 348) ve 2004 "
                  "(0018169.pdf s. 316) kitaplarında Büyükçekmece'nin beldesi. Belde tek ilçe içinde kurulur; "
                  "1990–1999 arasında Büyükçekmece–Küçükçekmece sınır değişikliği kaydı yok. Çıkarım.")
_SAYIM_KAYNAK = {
    "1960-10-23": "DİE 1960 GNS İl, İlçe, Bucak ve Köyler (0015128.pdf) s. 347 (Bakırköy), 349 (Çatalca Büyükçekmece bucağı)",
    "1985-10-20": "DİE 1985 GNS İdari Bölünüş (0013062.pdf) s. 385 (Bakırköy), 386 (Çatalca Büyükçekmece bucağı)",
    "1990-10-21": "DİE 1990 GNS İdari Bölünüş (0013349.pdf) s. 331 (K.Çekmece, B.Çekmece)",
}
_UMRANIYE_KAYNAK = {
    "1960-10-23": "DİE 1960 GNS İl, İlçe, Bucak ve Köyler (0015128.pdf) s. 347 (Beykoz), 349 (Üsküdar), 350 (Kartal Şamandıra bucağı)",
    "1985-10-20": "DİE 1985 GNS İdari Bölünüş (0013062.pdf) s. 385 (Beykoz), 386 (Üsküdar, Kartal Şamandıra bucağı)",
    "1990-10-21": "DİE 1990 GNS İdari Bölünüş (0013349.pdf) s. 330 (Beykoz), 331 (Ümraniye, Kartal); "
                  "Ümraniye'nin 1990 köyleri 3392 (1987) ile Üsküdar ve Beykoz'dan geçti — ilçe ayrı satır "
                  "olmadan önceki seçimler için kaynak ilçe yazılır",
}
# ilce kurulmadan onceki secimlerde eski ilcenin satiri (5747 listesindeki 2007 geomId'si yerine)
_ESKI_GEOM_1987 = {"Üsküdar": "TR-D-34-038", "Beykoz": "TR-D-34-011", "Kartal": "HIST-Istanbul-Kartal8489",
                   "Kadıköy": "TR-D-34-023"}
_USK, _BEY, _KAR = ["Üsküdar"] * 3, ["Beykoz"] * 3, ["Kartal"] * 3
DONEMSEL = {
    "TR-D-34-016": {
        "anlar": ["1960-10-23", "1985-10-20", "1990-10-21"], "kaynaklar": _UMRANIYE_KAYNAK, "eskiGeom": _ESKI_GEOM_1987,
        # Alemdağ = Alemdar köyü; Çekmeköy = Çekme köyü; Taşdelen sayım kitaplarında yok
        "birimler": {"Çekmeköy": _USK, "Çekme": _USK, "Alemdağ": _USK, "Alemdar": _USK, "Reşadiye": _USK,
                     "Sultançiftliği": _USK, "Ömerli": _BEY, "Hüseyinli": _BEY, "Koçullu": _BEY, "Sırapınar": _BEY},
    },
    "TR-D-34-029": {
        "anlar": ["1960-10-23", "1985-10-20", "1990-10-21"], "kaynaklar": _UMRANIYE_KAYNAK, "eskiGeom": _ESKI_GEOM_1987,
        # Sarıgazi 1960 Kartal Şamandıra bucağı, 1985 Üsküdar; Yenidoğan 1960 listesinde yok
        "birimler": {"Samandıra": _KAR, "Paşaköy": _KAR, "Sarıgazi": ["Kartal", "Üsküdar", "Üsküdar"],
                     "Yenidoğan": [None, "Üsküdar", "Üsküdar"], "Çekmeköy": _USK},
    },
    "TR-D-34-003": {
        "anlar": ["1960-10-23", "1985-10-20", "1990-10-21"], "kaynaklar": _UMRANIYE_KAYNAK, "eskiGeom": _ESKI_GEOM_1987,
        # 2008'de hâlâ Kadıköy/Üsküdar'a bağlı mahalleler (bu ilçeler 1960'tan beri var); Samandıra
        # beldesi Kartal; 2008'de Ümraniye'nin olan mahallelerin 1987 öncesi ilçesi kaynakta yok
        "birimler": {"Kadıköy": ["Kadıköy"] * 3, "Üsküdar": _USK, "Samandıra": _KAR, "Ümraniye": [None] * 3},
    },

    # Buyukcekmece 1987'de Catalca'dan (3392; tarihsel birim, zincir Catalca'ya cikar);
    # 1960 Eksinoz = Esenyurt. Kucukcekmece 1987'de Bakirkoy'den (sayim_kaniti.json).
    "TR-D-34-018": {
        "anlar": ["1960-10-23", "1985-10-20", "1990-10-21", "2008-03-22"],
        "kaynaklar": {**_SAYIM_KAYNAK, "2008-03-22": "5747 (20) sayılı liste; belde ilçesi DİE 2004 Tablo 9"},
        # Bahçeşehir: 1994'te yok, 1999 ve 2004 DİE yerel seçim kitaplarında Büyükçekmece beldesi;
        # belde tek ilçe içinde kurulur, 1990-1999 arası B.Çekmece-K.Çekmece sınır değişikliği kaydı yok
        # (cikarim, BAHCESEHIR_NOT)
        "birimler": {b: ["Büyükçekmece"] * 4 for b in ("Esenyurt", "Kıraç", "Yakuplu", "Bahçeşehir")},
    },
    "TR-D-34-008": {
        "anlar": ["1960-10-23", "1985-10-20", "1990-10-21", "2008-03-22"],
        "kaynaklar": {**_SAYIM_KAYNAK, "2008-03-22": "5747 (17) sayılı liste; belde ilçesi DİE 2004 Tablo 9"},
        "birimler": {
            # 1960 ve 1985 Bakırköy (köy), 1990 K.Çekmece; Küçükçekmece beldesi 1960 Bakırköy
            **{b: ["Küçükçekmece"] * 4 for b in ("Kayabaşı", "Şamlar", "Küçükçekmece")},
            "Bahçeşehir": ["Büyükçekmece"] * 4,
            # Esenler 1960'ta Bakırköy köyü; 1990'da hangi ilçenin şehir alanında olduğu kitapta yok
            "Esenler": [None, None, None, "Esenler"],
        },
    },
    "TR-D-34-002": {
        "anlar": ["1960-10-23", "1985-10-20", "1990-10-21", "2008-03-22"],
        "kaynaklar": {
            "1960-10-23": "DİE 1960 Genel Nüfus Sayımı İl, İlçe, Bucak ve Köyler (kutuphane.tuik.gov.tr/pdf/0015128.pdf) s. 348 (Eyüp: Rami bucağı), 349–350 (Çatalca: Hadımköy ve Büyükçekmece bucakları)",
            "1985-10-20": "DİE 1985 Genel Nüfus Sayımı İdari Bölünüş (kutuphane.tuik.gov.tr/pdf/0013062.pdf) s. 385 (Gaziosmanpaşa Merkez bucağı), 386 (Çatalca Hadımköy bucağı)",
            "1990-10-21": "DİE 1990 Genel Nüfus Sayımı İdari Bölünüş (kutuphane.tuik.gov.tr/pdf/0013349.pdf) s. 330 (Gaziosmanpaşa Merkez bucağı), 332 (Çatalca Hadımköy bucağı)",
            "2008-03-22": "5747 (15) sayılı liste; belde ilçesi DİE 2004 Tablo 9",
        },
        "birimler": {
            # 1960 Eyüp (Rami bucağı) -> 1963 Gaziosmanpaşa (309; Taşoluk = Ayazma)
            **{b: ["Gaziosmanpaşa"] * 4 for b in ("Arnavutköy", "Boğazköy", "Bolluca", "Çilingir", "Hacımaşlı",
                                                    "Haraççı", "İmrahor", "Taşoluk")},
            "Tayakadın": ["Çatalca", "Gaziosmanpaşa", "Gaziosmanpaşa", "Gaziosmanpaşa"],
            "Yeniköy": ["Çatalca", "Çatalca", "Gaziosmanpaşa", "Gaziosmanpaşa"],
            # Durusu 1960'ta Terkos adıyla; Deliklikaya, Ömerli, Yeşilbayır 1960'ta Büyükçekmece bucağı
            **{b: ["Çatalca"] * 4 for b in ("Hadımköy", "Durusu", "Baklalı", "Balaban", "Boyalık", "Karaburun",
                                            "Sazlıbosna", "Dursunköy", "Yassıören", "Deliklikaya", "Ömerli", "Yeşilbayır")},
        },
    },
}
# kanundaki ad -> guncel mahalle adi (ayni birim, farkli yazim)
ELLE_AD = {"M. Fevzi Çakmak": "Mareşal Fevzi Çakmak"}
# kanunda iki eski ilce arasinda paylasildigi yazan birimler: guncel mahalle -> adaylar
BELIRSIZ_BIRIM = {
    # 5747 (22): Gaziosmanpaşa'nın Habipler mahallesi + Esenler'in 'Habipler' parsel parcasi;
    # guncel veride iki mahalle (ESKİ HABİPLER, HABİBLER) - hangisinin hangisi oldugu yazmiyor
    ("TR-D-34-033", "ESKİ HABİPLER MAH."): ["Gaziosmanpaşa", "Esenler"],
    ("TR-D-34-033", "HABİBLER MAH."): ["Gaziosmanpaşa", "Esenler"],
    # 5747 (20): Esenyurt'un Yeşilkent'i + Avcılar'ın Yeşilkent parçası
    ("TR-D-34-018", "YEŞİLKENT MAH."): ["Büyükçekmece", "Avcılar"],
    # 5747 (17): Küçükçekmece'nin Başakşehir mahallesi + Esenler'in 'Başakşehir' parçası
    ("TR-D-34-008", "BAŞAKŞEHİR MAH."): ["Küçükçekmece", "Esenler"],
}


SAYIM = {"1960-10-23": "1960", "1985-10-20": "1985", "1990-10-21": "1990"}
_SAYIM_DIZIN = {}


def sayim_dizini(yil):
    """{plaka: {fold(ad): [ilce, ...]}}"""
    if yil not in _SAYIM_DIZIN:
        p = ROOT / f"data/kaynaklar/tuik/nufus_sayimi/{yil}_koyler.json"
        d = collections.defaultdict(lambda: collections.defaultdict(list))
        if p.exists():
            for r in json.loads(p.read_text(encoding="utf-8"))["satirlar"]:
                d[r["plaka"]][norm(re.sub(r"\s*\(.*$", "", r["ad"]))].append(r["ilce"])
        _SAYIM_DIZIN[yil] = d
    return _SAYIM_DIZIN[yil]


def ata_adlari():
    """guncel ilce adi -> kanunla ayrildigi ata ilce adlari (tek kaynakli soy)"""
    lin = json.loads((IDARI / "district_lineage.json").read_text(encoding="utf-8"))
    ad_by = {l["geomId"]: l["ad"] for l in lin["districts"]}
    ata = collections.defaultdict(set)
    for l in lin["districts"]:
        k = l.get("kanunSoyu") or {}
        if l["lineageStatus"] == "kanun_tek_kaynak" and k.get("eskiIlceler") and k["eskiIlceler"][0]["ad"]:
            ata[norm(l["ad"])].add(norm(k["eskiIlceler"][0]["ad"]))
    for h in lin.get("historicalUnits", []):
        if h.get("tekKaynak") and h["eskiIlceler"][0]["ad"]:
            ata[norm(h["ad"])].add(norm(h["eskiIlceler"][0]["ad"]))
    sk = IDARI / "sayim_kaniti.json"
    if sk.exists():
        for b in json.loads(sk.read_text(encoding="utf-8"))["birimler"]:
            ata[norm(b["ad"])].add(norm(b["eskiIlce"]))
    # zincir
    for _ in range(4):
        for k in list(ata):
            for a in list(ata[k]):
                ata[k] |= ata.get(a, set())
    return ata


def ilce_esit(sayim_ilce, kanun_ilce, ata):
    a, b = norm(sayim_ilce), norm(kanun_ilce)
    adaylar = {b} | ata.get(b, set())
    return any(a == x or (len(a) > 3 and difflib.SequenceMatcher(None, a, x).ratio() >= 0.8) for x in adaylar)


def otomatik_donemsel(kayit, plaka, kanun_tarihi):
    """kanun listesindeki her birim icin [ilce@1960, @1985, @1990 (kanundan once olanlar), @kanun]"""
    anlar = [t for t in SAYIM if t < kanun_tarihi] + [kanun_tarihi]
    ata = ata_adlari()
    birimler, kanit = {}, {}
    for r in kayit["satirlar"]:
        if not r["eskiIlce"] or r["tur"] == "koy_kismi":
            continue
        adlar = [re.sub(r"\s*\(.*$", "", r["birim"]).strip(" '\".,")]
        if belediye_adi(r):
            adlar.append(belediye_adi(r))
        for ad in adlar:
            if not ad or norm(ad) in birimler:
                continue
            deger = []
            for t in anlar[:-1]:
                hits = sayim_dizini(SAYIM[t]).get(plaka, {}).get(norm(ad), [])
                if not hits:
                    deger.append(None)
                elif any(ilce_esit(h, r["eskiIlce"], ata) for h in hits):
                    deger.append(r["eskiIlce"])
                else:
                    deger.append(f"{hits[0]} (sayım)")
            birimler[norm(ad)] = deger + [r["eskiIlce"]]
            kanit[norm(ad)] = {SAYIM[t]: v for t, v in zip(anlar[:-1], deger)}
    return {"anlar": anlar, "birimler": birimler, "otomatik": True,
            "kaynaklar": {t: f"data/kaynaklar/tuik/nufus_sayimi/{SAYIM[t]}_koyler.json" for t in anlar[:-1]}}


def norm(s):
    return fold(re.sub(r"\s*MAH\.?$", "", s.strip())).replace(".", "").replace(" ", "")


def belediye_adi(r):
    b = r.get("eskiBelediye") or ""
    return re.sub(r" (İlk Kademe|İlçe) Belediyesi$", "", b)


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def bolustur(geom_id, cfg, mahalle_geo, ilce_poly, komsular):
    kanun = json.loads((ROOT / f"data/kaynaklar/resmi_gazete/ilce_kurulus/{cfg['kanun']}.json").read_text(encoding="utf-8"))
    kayit = next(i for i in kanun["ilceler"] if (i["yeniIlce"] or {}).get("geomId") == geom_id)
    birim, belde, ilce_geom = collections.defaultdict(set), collections.defaultdict(set), {}
    birim_belde = collections.defaultdict(set)
    for r in kayit["satirlar"]:
        if not r["eskiIlce"]:
            continue
        if r.get("tur") is None:
            r = dict(r, tur="koy", birim=re.sub(r"^[^A-Za-zÇĞİÖŞÜçğıöşü]+", "", r["birim"] or ""))
        ilce_geom[r["eskiIlce"]] = r.get("eskiIlceGeomId") or \
            next((e["geomId"] for e in kayit["eskiIlceler"] if e["ad"] == r["eskiIlce"]), None)
        if r["tur"] in ("mahalle", "koy"):
            ad = belediye_adi(r) if r["birim"] == "Merkez" and r.get("eskiBelediye") else r["birim"]
            if r["tur"] == "koy":
                ad = re.sub(r"\s*\(.*$", "", ad)   # 'Şamlar (Sazlıdere Baraj Gölünün ... kısımları)'
            ad = re.sub(r"\s+Mahallesinin\b.*$", "", ad)   # 'Ferhatpaşa Mahallesinin E-80 ... kısmı'
            birim[norm(ELLE_AD.get(ad, ad))].add(r["eskiIlce"])
            if belediye_adi(r):
                birim_belde[norm(ELLE_AD.get(ad, ad))].add(norm(belediye_adi(r)))
        if r["tur"] != "koy_kismi" and belediye_adi(r):
            belde[norm(belediye_adi(r))].add(r["eskiIlce"])
    # komsu guncel ilcelerle kaynaktaki ince ortusmeler (sliver) cikarilir: parcalar
    # eski ilcenin birlesimine katildiginda komsuyla ust uste binmesin
    C = temiz(ilce_poly)
    C = C.difference(unary_union([temiz(k) for k in komsular if k.intersects(C)]))
    atama, parca_geom = [], []
    for mid, m in sorted(mahalle_geo.get(geom_id, {}).items()):
        g = temiz(shape(m["geometry"])).intersection(C)
        if g.area < MIN_ALAN:
            continue
        n = norm(m["ad"])
        adaylar = BELIRSIZ_BIRIM.get((geom_id, m["ad"]))
        if adaylar:
            atama.append({"mahalle": m["ad"], "id": mid, "ilce": None, "adaylar": adaylar, "neden": "kanunda paylaşılmış birim"})
        elif len(birim.get(n, ())) == 1:
            # ayni ad iki beldede (Çamlık: Taşdelen ve Çekmeköy) -> belde belirsiz
            bb = birim_belde.get(n, set())
            atama.append({"mahalle": m["ad"], "id": mid, "ilce": next(iter(birim[n])), "neden": "ad",
                          "birim": n, "belde": next(iter(bb)) if len(bb) == 1 else None})
        else:
            hit = [b for b in belde if n.startswith(b) and len(belde[b]) == 1]
            if hit:
                atama.append({"mahalle": m["ad"], "id": mid, "ilce": next(iter(belde[hit[0]])), "neden": f"belde adı ({hit[0]})",
                              "birim": hit[0], "belde": hit[0]})
            else:
                atama.append({"mahalle": m["ad"], "id": mid, "ilce": None, "neden": "eşleşmedi"})
        parca_geom.append(g)
    # ayrik parcalar: sirayla fark
    dolu = None
    for a, g in zip(atama, parca_geom):
        if dolu is not None:
            g = g.difference(dolu)
        dolu = g if dolu is None else dolu.union(g)
        a["_geom"] = g
    bosluk = C.difference(dolu) if dolu is not None else C
    for i, p in enumerate(getattr(bosluk, "geoms", [bosluk])):
        if p.area >= MIN_ALAN:
            atama.append({"mahalle": None, "id": f"bosluk-{i}", "ilce": None, "neden": "mahalle poligonu yok", "_geom": p})
    son_ilce = {id(a): a["ilce"] for a in atama}
    ds = DONEMSEL.get(geom_id) or cfg.get("otomatikDonemsel")
    if ds:
        zaman = {k if ds.get("otomatik") else norm(k): v for k, v in ds["birimler"].items()}
        donemler = [(ds["anlar"][i], ds["anlar"][i + 1]) for i in range(len(ds["anlar"]) - 1)]
    else:
        zaman, donemler = {}, [(None, None)]
    toplam = C.area
    dis = C.exterior if C.geom_type == "Polygon" else unary_union([p.exterior for p in C.geoms])
    kilitli = unary_union([a["_geom"] for a in atama if a.get("adaylar")]) if any(a.get("adaylar") for a in atama) else None
    kod = geom_id.replace("TR-D-", "")
    features, donem_ozet, atama_donem = [], [], []
    for k, (bas, bit) in enumerate(donemler, 1):
        # bu donemde birimin ilcesi: iki sayimda ayni ise o, degilse belirsiz
        for a in atama:
            a["ilce"], a.pop("cikarim", None), a.pop("donemNotu", None)
            a["ilce"] = son_ilce[id(a)]
            if not ds or not a.get("birim"):
                continue
            t = zaman.get(a["birim"]) or zaman.get(a.get("belde") or "")
            if t is None:
                a["ilce"], a["donemNotu"] = None, "sayım kaydı yok"
                continue
            i0 = ds["anlar"].index(bas)
            if t[i0] is None or t[i0 + 1] is None:
                a["ilce"], a["donemNotu"] = None, f"{bas[:4]}–{bit[:4]} bağlılığı kaynakta yok"
            elif str(t[i0]).endswith("(sayım)") or str(t[i0 + 1]).endswith("(sayım)"):
                # sayim dizininde kanundakinden farkli ilce (gercek nakil ya da OCR): atanmaz
                a["ilce"], a["donemNotu"] = None, f"{bas[:4]}: {t[i0]}, {bit[:4]}: {t[i0 + 1]}"
            elif t[i0] != t[i0 + 1]:
                a["ilce"], a["donemNotu"] = None, f"{bas[:4]}: {t[i0]}, {bit[:4]}: {t[i0 + 1]}"
            else:
                a["ilce"] = t[i0]
        # cevrelenmis cikarimi: atanmamis alanin (eslesmeyen mahalle + mahalle disi) bagli
        # bilesenleri; dis sinira degmeyen ve yalniz TEK eski ilcenin parcalarina degen bilesen
        atanmamis = [a for a in atama if not a["ilce"] and not a.get("adaylar") and not a.get("donemNotu")]
        if atanmamis:
            U = unary_union([a["_geom"] for a in atanmamis]).buffer(EPS / 4).buffer(-EPS / 4)
            for comp in getattr(U, "geoms", [U]):
                if comp.distance(dis) < EPS or (kilitli is not None and comp.distance(kilitli) < EPS):
                    continue
                komsu = {b["ilce"] for b in atama if b["ilce"] and b["_geom"].distance(comp) < EPS}
                if len(komsu) != 1:
                    continue
                for a in atanmamis:
                    if a["_geom"].intersection(comp).area > 0.5 * a["_geom"].area:
                        a["ilce"], a["cikarim"] = next(iter(komsu)), "cevrelenmis"
        # liste tumleyeni: bu donemde kanun listesindeki birimlerin (kanunda paylasilmis birimler
        # haric) hepsi tek ilcedense, atanmamis alan (paylasilmis birime degmeyen) o ilceye
        if ds:
            birim_ilce = set()
            for r in kayit["satirlar"]:
                if r["tur"] == "koy_kismi" or not r["eskiIlce"]:
                    continue
                ad = belediye_adi(r) if r["birim"] == "Merkez" and r.get("eskiBelediye") else r["birim"]
                ad = re.sub(r"\s+Mahallesinin\b.*$", "", ad)
                key = norm(ELLE_AD.get(ad, ad))
                # kanunda paylasilmis birim ("Yeşilkent Mahallesinin ... kısmı" dahil) tumleyene katilmaz
                if any(key.startswith(norm(m)) for (g_, m) in BELIRSIZ_BIRIM if g_ == geom_id):
                    continue
                if r["eskiIlce"] != next(iter(birim.get(key, {r["eskiIlce"]}))) and len(birim.get(key, ())) > 1:
                    continue
                t = zaman.get(key) or zaman.get(norm(belediye_adi(r)) if belediye_adi(r) else "")
                i0 = ds["anlar"].index(bas)
                birim_ilce.add(None if t is None or t[i0] != t[i0 + 1] else t[i0])
            if len(birim_ilce) == 1 and None not in birim_ilce:
                X = next(iter(birim_ilce))
                for a in atama:
                    if a["ilce"] or a.get("adaylar") or a.get("donemNotu"):
                        continue
                    if kilitli is not None and a["_geom"].distance(kilitli) < EPS:
                        continue
                    a["ilce"], a["cikarim"] = X, "liste-tumleyeni"
        gruplar = collections.defaultdict(list)
        for a in atama:
            gruplar[a["ilce"]].append(a)
        ozet = {}
        for ilce, xs in gruplar.items():
            geom = unary_union([x["_geom"] for x in xs])
            if ilce:
                pid = f"PARCA-{kod}-{fold(ilce).replace(' ', '')}-D{k}"
                ozet[ilce] = {"parcaId": pid, "eskiIlceGeomId": (ds or {}).get("eskiGeom", {}).get(ilce) or ilce_geom[ilce], "alanPayi": round(geom.area / toplam, 4),
                              "mahalleler": sorted(x["mahalle"] for x in xs if x["mahalle"] and not x.get("cikarim")),
                              "cikarimla": sorted((x["mahalle"] or "mahalle dışı alan") for x in xs if x.get("cikarim"))}
            else:
                pid = f"BELIRSIZ-{kod}-D{k}"
                ozet["_belirsiz"] = {"parcaId": pid, "alanPayi": round(geom.area / toplam, 4),
                                     "adaylar": sorted({e["ad"] for e in kayit["eskiIlceler"] if e["ad"]}),
                                     "mahalleler": sorted(x["mahalle"] for x in xs if x["mahalle"]),
                                     "donemdeIlceDegistiren": sorted(f"{x['mahalle']} ({x['donemNotu']})" for x in xs
                                                                    if x.get("donemNotu") and x["mahalle"]),
                                     "mahalleDisiAlan": sum(1 for x in xs if not x["mahalle"])}
            features.append({"type": "Feature", "properties": {"id": pid, "plaka": int(kod.split("-")[0]), "ilce": geom_id,
                                                              "eskiIlce": ilce}, "geometry": mapping(geom)})
        donem_ozet.append({"donem": f"D{k}", "baslangic": bas, "bitis": bit, "parcalar": ozet})
        atama_donem.append({"donem": f"D{k}", "atama": [{kk: vv for kk, vv in a.items() if kk != "_geom"} for a in atama]})
    return {"ad": cfg["ad"], "kanun": cfg["kanun"], "listeNo": kayit["listeNo"],
            **({"donemselKaynaklar": ds["kaynaklar"]} if ds else {}),
            **({"cikarimNotu": BAHCESEHIR_NOT} if ds and "Bahçeşehir" in ds["birimler"] else {}),
            "donemler": donem_ozet, "atama": atama_donem}, features


def tr_ad(s):
    return " ".join(w[:1] + w[1:].replace("I", "ı").replace("İ", "i").lower() for w in s.split())


def main():
    mahalle_geo = json.loads((ROOT / "geo/normalized/mahalle_geo.json").read_text(encoding="utf-8"))
    modern = {f["properties"]["id"]: shape(f["geometry"])
              for f in json.loads((ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson").read_text(encoding="utf-8"))["features"]}
    rapor, features = {}, []
    lin = json.loads((IDARI / "district_lineage.json").read_text(encoding="utf-8"))["districts"]
    ilceler = dict(ILCELER)
    for l in lin:
        k = l.get("kanunSoyu") or {}
        if l["lineageStatus"] != "kanun_cok_kaynak" or l["geomId"] in ilceler or not mahalle_geo.get(l["geomId"]):
            continue
        dosya = ROOT / f"data/kaynaklar/resmi_gazete/ilce_kurulus/{k['kanun'].replace(' ', '_')}.json"
        if not dosya.exists():
            continue
        kd = json.loads(dosya.read_text(encoding="utf-8"))
        kayit = next((i for i in kd["ilceler"] if (i["yeniIlce"] or {}).get("geomId") == l["geomId"]), None)
        if not kayit:
            continue
        ilceler[l["geomId"]] = {"kanun": k["kanun"].replace(" ", "_"), "ad": tr_ad(l["ad"]),
                                "otomatikDonemsel": otomatik_donemsel(kayit, l["plaka"], kd["resmiGazete"]["tarih"])}
    for g, cfg in ilceler.items():
        pl = g.split("-")[2]
        komsu = [v for k, v in modern.items() if k != g and k.split("-")[2] == pl]
        r, f = bolustur(g, cfg, mahalle_geo, modern[g], komsu)
        rapor[g], features = r, features + f
    OUT_JSON.write_text(json.dumps({"not": "build_mahalle_bolusumu.py ile üretilir; elle düzenlenmez.",
                                    "yontem": __doc__.split("Yontem")[1].split("Cikti:")[0].strip(),
                                    "ilceler": rapor}, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_GEO.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False,
                                  separators=(",", ":")), encoding="utf-8")
    for g, r in rapor.items():
        for d in r["donemler"]:
            print(r["ad"], d["donem"], d["baslangic"], d["bitis"],
                  {k: (v["alanPayi"], v.get("cikarimla") or v.get("donemdeIlceDegistiren") or v.get("adaylar")) for k, v in d["parcalar"].items()})


if __name__ == "__main__":
    main()
