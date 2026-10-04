"""
1961 genel seciminin ilce haritasi: bugunku ilce -> 1961'deki ilce esleme tablosu ve o tabloya gore
birlestirilmis (dissolve) 1961 ilce poligonlari.

Esas kaynak 1961 secim sonucudur (data/normalized/elections/genel/1961.json): 1961'de var olan
ilceler, o dosyanin ilce satirlaridir. Her bugunku ilce (geo/normalized/turkiye_ilce_sinirlari.geojson)
ya bir 1961 satirina baglanir ya da "belirsiz" kalir; tahmin yapilmaz.

Adimlar:
  tablo   geo/historical/idari/ilce_1961_eslesme.csv dosyasini uretir.
  uygula  CSV'yi okur; bir 1961 satirinin bugunku ilceleri, satirin su anki poligonunun
          kapsadigindan fazlaysa yeni birlesim poligonu (HIST1961-<plaka>-<ad>) uretir ve
          satirin geomId'sini ona cevirir. Oy/katilim degismez.
  kontrol 1961 satir/poligon/il tutarliligini denetler (tests/validate_elections.py de calistirir).
  (arguman yok: tablo + uygula + kontrol)

Esleme yontemleri (CSV -> yontem):
  kendi_satiri            Bugunku ilce 1961'de de ilceydi; satirin poligonu bugunku poligonudur.
  tarihsel_birlesim       Mevcut kaynakli birlesimin parcasi: apply_idari_merges.py (HISTK-*, kurulus
                          kanununun ek listesine gore tek kaynakli) ya da repoda dogrulanmis HIST-*.
  bolunmus_poligon        Bugunku poligon 1961'de iki ilce arasinda bolunmus (Eminonu/Fatih).
  istanbul_zinciri        build_istanbul_1961_1992.py -> ZINCIR (kanun ek listesi / sayim zinciri).
  ayni_1961_ilcesi        Kanun ek listesine gore birden cok eski ilceden kuruldu, ama bu eski
                          ilcelerin hepsi 1961'de ayni ilcenin parcasiydi (birimlerin %100'u).
  cogunluk                Ek listedeki birimlerin en az %70'i ayni 1961 ilcesinden; butunuyle ona
                          katilir (apply_idari_merges.py'deki Merkez cogunlugu kurali, her ilceye).
                          Yaklasik: kucuk diger kaynaklar 'not' sutununda ve haritada ipucunda.
  belirsiz                Soy kaynakta yok ya da tek bir 1961 ilcesi %70'e ulasmiyor. Poligon
                          tarali kalir (harita_notlari.json).

Sira: apply_idari_merges.py -> build_ilce_1961.py -> scripts/build.py -> checksum yenile.
apply_idari_merges.py harita_notlari.json'u yeniden yazdigi icin bu betik ondan sonra calismali.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_ilce_1961.py [tablo|uygula|kontrol]
"""
import collections
import csv
import json
import pathlib
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from build_istanbul_1961_1992 import ZINCIR  # noqa: E402
from common.election_io import election_path, load_election, save_election  # noqa: E402
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur  # noqa: E402

SECIM = "1961"
TARIH = "1961-10-15"
IDARI = ROOT / "geo/historical/idari"
CSV = IDARI / "ilce_1961_eslesme.csv"
KAYIT = IDARI / "ilce_1961.json"
LINEAGE = IDARI / "district_lineage.json"
PLAN = IDARI / "merge_plan.json"
NOTLAR = IDARI / "harita_notlari.json"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = ROOT / "geo/historical/district_splits.json"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
ONEK = "HIST1961-"
ESIK = 0.7
ALANLAR = ["guncel_geomId", "guncel_il", "guncel_ilce", "kurulus_tarihi", "kurulus_kanunu", "plaka_1961",
           "il_1961", "ilce_1961", "geomId_1961", "yontem", "guven", "kaynak", "not"]
GUVEN = {"kendi_satiri": "kesin", "tarihsel_birlesim": "kesin", "bolunmus_poligon": "kesin",
         "istanbul_zinciri": "kesin", "ayni_1961_ilcesi": "kesin", "cogunluk": "yaklasik", "belirsiz": ""}
LINEAGE_KAYNAK = "geo/historical/idari/district_lineage.json"
# belirsiz kalan ilcelerde repodaki kismi kanit (esleme icin yetmez, yalniz not)
KISMI_KANIT = {
    "TR-D-34-024": "1960 sayımı (data/raw/tuik/nufus-sayimi-idari-bolunus/1960_0015128_istanbul.pdf): Kâğıthane köyü "
                   "Şişli Merkez bucağında; 1987 ilçesinin mahallelerinin tamamının Şişli'den geldiği kaynakta yok",
    "TR-D-34-037": "1960 sayımı: Ümraniye, Alemdar, Çekme, Reşadiye, Sultançiftliği, Dudullu köyleri Üsküdar'da; "
                   "3392 listesindeki Beykoz köyleri ve 7 mahallenin eski ilçesi ayrı",
    "TR-D-68-008": "data/normalized/ek/beldeler/1963yerel.json: Sultanhanı beldesi Aksaray ilçesinde (Niğde); "
                   "ilçeye bağlanan köylerin eski ilçesi KHK 694 ekinde, repoda yok",
    "TR-D-30-005": "data/normalized/ek/beldeler/1999yerel.json–2014yerel.json: Derecik beldesi Şemdinli'de; "
                   "köylerin eski ilçesi 7148 ekinde, repoda yok",
}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def tr_baslik(s):
    return " ".join(w[:1] + w[1:].replace("I", "ı").replace("İ", "i").lower() for w in s.split())


def ascii_ad(ad):
    return ad.translate(str.maketrans("İıĞğÜüŞşÖöÇçÂâÎîÛû", "IiGgUuSsOoCcAaIiUu")).replace(" ", "")


def kapsam(splits):
    """sentetik id -> bugunku ilceler (district_splits.json hideIds)"""
    return {e["syntheticId"]: set(e["hideIds"]) for v in splits.values() for e in v}


def satir_kapsami(rec, hide):
    """(plaka, ad) -> satirin poligonunun kapsadigi bugunku ilceler"""
    return {(r["plaka"], r["ad"]): (set(hide.get(r["geomId"], {r["geomId"]})) if r.get("geomId") else set())
            for r in rec["ilceler"]}


def geri_al(rec, splits, hist):
    """onceki 'uygula'nin HIST1961 satirlarini ilk geomId'lerine dondur (idempotent)."""
    if KAYIT.exists():
        once = {(s["plaka"], s["ilce"]): s["oncekiGeomId"] for s in oku(KAYIT)["birlesimler"]}
        for r in rec["ilceler"]:
            if (r.get("geomId") or "").startswith(ONEK):
                r["geomId"] = once[(r["plaka"], r["ad"])]
    for pl in list(splits):
        splits[pl] = [e for e in splits[pl] if not e["syntheticId"].startswith(ONEK)]
        if not splits[pl]:
            del splits[pl]
    hist["features"] = [f for f in hist["features"] if not f["properties"]["id"].startswith(ONEK)]


# ---------------------------------------------------------------- tablo
def tablo():
    rec = load_election(SECIM)
    splits, hist = oku(SPLITS), oku(HIST_GEO)
    geri_al(rec, splits, hist)
    hide = kapsam(splits)
    lin = oku(LINEAGE)
    lineage = {l["geomId"]: l for l in lin["districts"]}
    # kanunSoyu'su olmayan ama kendisi kanunla kurulmus tarihsel birim olan ilce (Umraniye 1987)
    birim_soyu = {h["ad"]: h for h in lin.get("historicalUnits", [])}

    def soy(g):
        l = lineage[g]
        return l.get("kanunSoyu") or birim_soyu.get(guncel_ad.get(g) or tr_baslik(l["ad"])) or {}
    plan = oku(PLAN)["sentetikler"]
    modern_plaka = {f["properties"]["id"]: f["properties"]["plaka"] for f in oku(MODERN)["features"]}
    guncel = load_election("2023")
    guncel_ad = {r["geomId"]: r["ad"] for r in guncel["ilceler"] if r.get("geomId")}
    guncel_il = {i["plaka"]: i["ad"] for i in guncel["iller"]}
    il61 = {i["plaka"]: i["ad"] for i in rec["iller"]}
    satirlar = {(r["plaka"], r["ad"]): r for r in rec["ilceler"]}
    sk = satir_kapsami(rec, hide)

    bagli = collections.defaultdict(list)          # bugunku ilce -> [(plaka, ad)]
    for k, ids in sk.items():
        for g in ids:
            bagli[g].append(k)

    def ad(g):
        return guncel_ad.get(g) or tr_baslik(lineage[g]["ad"])

    satir = {}  # bugunku ilce -> dict

    def yaz(g, hedef, yontem, kaynak, not_=""):
        l = lineage[g]
        kur = l.get("kurulus") or {}
        satir[g] = {"guncel_geomId": g, "guncel_il": guncel_il[modern_plaka[g]], "guncel_ilce": ad(g),
                    "kurulus_tarihi": "" if kur.get("cumhuriyetOncesi") else (kur.get("tarih") or ""),
                    "kurulus_kanunu": kur.get("kanun") or "",
                    "plaka_1961": hedef[0] if hedef else "", "il_1961": il61[hedef[0]] if hedef else "",
                    "ilce_1961": hedef[1] if hedef else "", "geomId_1961": satirlar[hedef]["geomId"] if hedef else "",
                    "yontem": yontem, "guven": GUVEN[yontem], "kaynak": kaynak, "not": not_}

    # 1) su anki 1961 poligonlarinin kapsadiklari
    for g in sorted(modern_plaka):
        ks = bagli.get(g, [])
        if len(ks) > 1:
            yaz(g, None, "bolunmus_poligon", "scripts/pipelines/historical_geo/split_eminonu_fatih.py",
                "1961'de " + " ve ".join(k[1] for k in ks) + " arasında bölünmüş; her biri kendi HIST poligonuyla")
            satir[g].update(plaka_1961=ks[0][0], il_1961=il61[ks[0][0]], ilce_1961=" + ".join(k[1] for k in ks),
                            geomId_1961=" + ".join(satirlar[k]["geomId"] for k in ks))
            continue
        if not ks:
            continue
        k = ks[0]
        gid = satirlar[k]["geomId"]
        if gid == g:
            yaz(g, k, "kendi_satiri", "data/normalized/elections/genel/1961.json")
            l = lineage[g]
            if ((l.get("kurulus") or {}).get("tarih") or "") > TARIH:
                if l["lineageStatus"] == "merkez_ilce" or l.get("merkezIlceDonusumu"):
                    satir[g]["not"] = "1961'de il Merkez ilçesi; bugünkü adı sonradan (merkez ilçe dönüşümü)"
                else:
                    satir[g]["guven"] = "şüpheli"
                    satir[g]["not"] = ("Kuruluşu 1961'den sonra; 1961 verisindeki satır bu ilçe olamaz "
                                       "(idari/README.md → Bilinen boşluklar). Eşleşme korunuyor, doğrulanmalı")
            continue
        p = plan.get(gid)
        if p and g in p["katilanlar"]:
            l = lineage[g]
            if l["lineageStatus"] == "kanun_tek_kaynak":
                ek = l["kanunSoyu"]
                kaynak = f"{ek['kanun']} sayılı Kanun ek ({ek['listeNo']}) sayılı liste (RG {ek['resmiGazete']['tarih']})"
                eski = ek["eskiIlceler"][0]["ad"]
                not_ = f"Kuruluşta bütün birimleri {eski} ilçesinden"
            else:
                adlar = [a for a in p["adlar"] if a.startswith(tr_baslik(l["ad"]).split()[0]) or ad(g) in a]
                kaynak = "apply_idari_merges.py: " + "; ".join(p["kanunlar"]) + " sayılı Kanun"
                not_ = (adlar[0] if adlar else "") + (" — sayim_kaniti.json / historicalUnits" if adlar else "")
            yaz(g, k, "tarihsel_birlesim", kaynak, not_.strip(" —"))
        else:
            taban = p["taban"] if p else gid
            yaz(g, k, "tarihsel_birlesim", "geo/historical/district_splits.json (" + taban + ", repoda doğrulanmış birleşim)",
                "1961 satırı " + k[1] + " poligonu: " + taban)

    # 2) kapsanmayan bugunku ilceler: istanbul zinciri, kanun soyu (iteratif: soy zinciri)
    dagilim = {}  # bugunku ilce -> {(plaka, ad) ya da None: pay}
    for g in satir:
        if satir[g]["yontem"] != "bolunmus_poligon":
            dagilim[g] = {(int(satir[g]["plaka_1961"]), satir[g]["ilce_1961"]): 1.0}

    def eski_dagilim(gid):
        """eski ilce geomId (modern ya da HIST) -> 1961 satir dagilimi; bilinmiyorsa None"""
        if gid is None:
            return None
        if gid in dagilim:
            return dagilim[gid]
        for k, r in satirlar.items():   # dogrudan bir 1961 satirinin poligonu
            if r.get("geomId") == gid:
                return {k: 1.0}
        if gid in hide:                  # repodaki HIST poligonu: parcalarinin dagilimi ayni olmali
            ds = [dagilim.get(x) for x in sorted(hide[gid])]
            if all(ds) and all(d == ds[0] for d in ds):
                return ds[0]
        return None

    kalan = sorted(g for g in modern_plaka if g not in satir)
    for g in kalan:
        kod = g.split("-")[-1]
        if modern_plaka[g] == 34 and kod in ZINCIR:
            for bas, bit, il, dayanak in ZINCIR[kod]:
                if bas <= TARIH < bit:
                    k = (34, il)
                    assert k in satirlar, k
                    yaz(g, k, "istanbul_zinciri", dayanak, "build_istanbul_1961_1992.py → ZINCIR")
                    dagilim[g] = {k: 1.0}
    degisti = True
    while degisti:
        degisti = False
        for g in kalan:
            if g in dagilim:
                continue
            ek = soy(g).get("eskiIlceler") or []
            toplam = sum(e["birimSayisi"] for e in ek)
            if not toplam:
                continue
            payi = collections.Counter()
            bekle = False
            for e in ek:
                d = eski_dagilim(e.get("geomId"))
                if d is None and e.get("geomId") in kalan and e.get("geomId") not in dagilim:
                    bekle = True   # eski ilcenin kendisi henuz cozulmedi
                    break
                for k, v in (d or {None: 1.0}).items():
                    payi[k] += v * e["birimSayisi"] / toplam
            if bekle:
                continue
            dagilim[g] = dict(payi)
            degisti = True
    # cozulemeyen bekleyenler (eski ilcesi belirsiz kalan): bilinmeyen
    for g in kalan:
        if g in satir:
            continue
        l = lineage[g]
        ks = soy(g)
        ek = ks.get("eskiIlceler") or []
        kaynak = ((f"{ks['kanun']} sayılı Kanun ek ({ks['listeNo']}) sayılı liste" if ks.get("listeNo")
                   else f"{ks['kanun']} sayılı Kanun (ek listesiz, madde metni)") if ks else LINEAGE_KAYNAK)
        birim = ", ".join(f"{e['ad'] or 'kaynağı yazılmamış'} {e['birimSayisi']}" for e in ek)
        d = dagilim.get(g)
        if d:
            enbuyuk = max((k for k in d if k), key=lambda k: d[k], default=None)
            pay = d.get(enbuyuk, 0)
            digerleri = sorted(((k[1] if k else "bilinmiyor"), round(v, 3)) for k, v in d.items() if k != enbuyuk)
            if enbuyuk and pay > 0.9999:
                yaz(g, enbuyuk, "ayni_1961_ilcesi", kaynak,
                    f"Ek liste birimleri: {birim}; hepsi 1961'de {enbuyuk[1]} ilçesindeydi")
                continue
            if enbuyuk and pay >= ESIK:
                yaz(g, enbuyuk, "cogunluk", kaynak,
                    f"Ek liste birimleri: {birim}; 1961 ilçelerine göre %{round(pay * 100)} {enbuyuk[1]}, "
                    + ", ".join(f"%{round(v * 100)} {a}" for a, v in digerleri))
                satir[g]["_cogunluk"] = {"ana": enbuyuk[1], "pay": round(pay, 2),
                                         "digerleri": [[a, round(v, 2)] for a, v in digerleri]}
                continue
            if enbuyuk:
                neden = f"1961 ilçelerine göre en büyük pay %{round(pay * 100)} {enbuyuk[1]} (<%{round(ESIK * 100)})"
            elif all(not e["ad"] for e in ek):
                neden = "kanun ek listesinde birimlerin eski ilçesi yazılmamış"
            else:
                neden = "eski ilçelerin 1961'deki karşılığı bilinmiyor (" + \
                        ", ".join(sorted({e["ad"] or "kaynağı yazılmamış" for e in ek})) + " 1961'de yoktu ya da kendisi belirsiz)"
            yaz(g, None, "belirsiz", kaynak, f"Ek liste birimleri: {birim}; {neden}"
                + (f". {KISMI_KANIT[g]}" if g in KISMI_KANIT else ""))
            continue
        neden = {"unresolved": "kuruluş kanununun ek listesi repoda yok",
                 "kanun_kaynak_yazilmamis": "kanun ek listesinde birimlerin eski ilçesi yazılmamış",
                 }.get(l["lineageStatus"], l["lineageStatus"])
        yaz(g, None, "belirsiz", kaynak, neden + (f"; ek liste birimleri: {birim}" if birim else "")
            + (f". {KISMI_KANIT[g]}" if g in KISMI_KANIT else ""))

    satirlar_csv = [satir[g] for g in sorted(satir)]
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ALANLAR, lineterminator="\n")
        w.writeheader()
        for s in satirlar_csv:
            w.writerow({k: s[k] for k in ALANLAR})
    cogunluk = {g: s["_cogunluk"] for g, s in satir.items() if "_cogunluk" in s}
    print("tablo:", CSV.relative_to(ROOT), len(satirlar_csv), "satır;",
          dict(collections.Counter(s["yontem"] for s in satirlar_csv)))
    return cogunluk


# ---------------------------------------------------------------- uygula
def tablo_oku():
    with CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def uygula(cogunluk=None):
    rec = load_election(SECIM)
    splits, hist = oku(SPLITS), oku(HIST_GEO)
    geri_al(rec, splits, hist)
    hide = kapsam(splits)
    sk = satir_kapsami(rec, hide)
    satirlar = {(r["plaka"], r["ad"]): r for r in rec["ilceler"]}
    modern = {f["properties"]["id"]: f for f in oku(MODERN)["features"]}
    hist_by = {f["properties"]["id"]: f for f in hist["features"]}
    tab = tablo_oku()
    if cogunluk is None:
        cogunluk = oku(KAYIT).get("cogunluk", {}) if KAYIT.exists() else {}

    hedef = collections.defaultdict(set)
    for s in tab:
        if s["yontem"] in ("belirsiz", "bolunmus_poligon"):
            continue
        k = (int(s["plaka_1961"]), s["ilce_1961"])
        if k not in satirlar:
            raise SystemExit(f"HATA: {s['guncel_geomId']} -> {k}: 1961 sonuçlarında böyle bir ilçe yok")
        hedef[k].add(s["guncel_geomId"])

    lineage = {l["geomId"]: l for l in oku(LINEAGE)["districts"]}
    guncel_ad = {r["geomId"]: r["ad"] for r in load_election("2023")["ilceler"] if r.get("geomId")}
    ad = {g: guncel_ad.get(g) or tr_baslik(lineage[g]["ad"]) for g in modern}

    birlesimler, eklenen = [], set()
    for k, ids in sorted(hedef.items()):
        once = sk[k]
        # yalniz bugunku poligonun parcasi olanlar (Eminonu/Fatih gibi bolunmus HIST parcalari haric)
        if not once - ids <= {g for g in once if g not in modern}:
            raise SystemExit(f"HATA: {k} satırının poligonu tabloda başka satıra bağlı ilçeleri kapsıyor: {sorted(once - ids)}")
        yeni = sorted(ids - once)
        if not yeni:
            continue
        r = satirlar[k]
        taban_id = r["geomId"]
        taban = modern.get(taban_id) or hist_by.get(taban_id)
        geoms = [temiz(shape(taban["geometry"]))] + [temiz(shape(modern[g]["geometry"])) for g in yeni]
        icerik = once | set(yeni)
        u = unary_union(geoms)
        yabanci = unary_union([temiz(shape(f["geometry"])) for g, f in modern.items()
                               if g not in icerik and shape(f["geometry"]).intersects(u.envelope)])
        u = delikleri_doldur(u, bilesen_delikleri([temiz(shape(modern[g]["geometry"])) for g in icerik if g in modern]),
                             yabanci)
        sid = f"{ONEK}{k[0]:02d}-{ascii_ad(k[1])}"
        hist["features"].append({"type": "Feature", "properties": {"id": sid, "plaka": k[0]}, "geometry": mapping(u)})
        splits.setdefault(str(k[0]), []).append({"hideIds": sorted(icerik), "splitYear": 1962, "syntheticId": sid})
        r["geomId"] = sid
        eklenen |= set(yeni)
        birlesimler.append({"plaka": k[0], "ilce": k[1], "geomId": sid, "oncekiGeomId": taban_id,
                            "katilanlar": yeni, "katilanAdlar": [ad[g] for g in yeni],
                            "bugunkuIlceler": sorted(icerik)})
    hist["features"].sort(key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
    eski = json.loads(election_path(SECIM).read_text(encoding="utf-8"))
    if eski != rec:
        save_election(SECIM, rec)

    # harita notlari: artik kapsanan ilceler 1961'de taranmaz; birlesimlerin ipucu
    notlar = oku(NOTLAR)
    sec = notlar["secimler"].get(SECIM, {})
    for g in eklenen:
        sec.pop(g, None)
    notlar["secimler"][SECIM] = dict(sorted(sec.items()))
    for b in birlesimler:
        e = {"ilceler": sorted({ad[g] for g in b["bugunkuIlceler"] if g in modern})}
        cg = [dict(cogunluk[g], ad=ad[g]) for g in b["katilanlar"] if g in cogunluk]
        if cg:
            # ipucu bicimi 'digerleri: [ad, birim]'; burada pay (%)
            for c in cg:
                c["digerleri"] = [[a, f"%{round(v * 100)}"] for a, v in c["digerleri"]]
            e["cogunluk"] = cg
        notlar["birlesimler"][b["geomId"]] = e
    notlar["birlesimler"] = dict(sorted(notlar["birlesimler"].items()))
    NOTLAR.write_text(json.dumps(notlar, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    belirsiz = [{"geomId": s["guncel_geomId"], "il": s["guncel_il"], "ilce": s["guncel_ilce"], "not": s["not"]}
                for s in tab if s["yontem"] == "belirsiz"]
    geomsuz = [{"plaka": r["plaka"], "ilce": r["ad"]} for r in rec["ilceler"]
               if not r.get("geomId") or (r["geomId"] not in modern and r["geomId"] not in {f["properties"]["id"] for f in hist["features"]})]
    KAYIT.write_text(json.dumps({
        "not": "build_ilce_1961.py ile üretilir; elle düzenlenmez. Tablo: ilce_1961_eslesme.csv.",
        "ozet": {"birlesimPoligonu": len(birlesimler), "katilanIlce": len(eklenen), "belirsizIlce": len(belirsiz),
                 "geometrisizSatir": len(geomsuz),
                 "yontem": dict(collections.Counter(s["yontem"] for s in tab))},
        "birlesimler": birlesimler, "cogunluk": cogunluk, "belirsiz": belirsiz, "geometrisizSatir": geomsuz,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("uygula:", len(birlesimler), "birleşim poligonu,", len(eklenen), "bugünkü ilçe katıldı;",
          len(belirsiz), "belirsiz;", len(geomsuz), "geometrisiz satır")


# ---------------------------------------------------------------- kontrol
def kontrol(sessiz=False):
    """sorun listesi doner (bos: gecti)"""
    rec = load_election(SECIM)
    hide = kapsam(oku(SPLITS))
    modern = {f["properties"]["id"]: f["properties"]["plaka"] for f in oku(MODERN)["features"]}
    hist_ids = {f["properties"]["id"] for f in oku(HIST_GEO)["features"]}
    tab = {s["guncel_geomId"]: s for s in tablo_oku()}
    kayit = oku(KAYIT) if KAYIT.exists() else {"geometrisizSatir": []}
    izinli_geomsuz = {(x["plaka"], x["ilce"]) for x in kayit["geometrisizSatir"]}
    sorun = []
    if set(tab) != set(modern):
        sorun.append(f"tablo bugünkü ilçelerle eşleşmiyor: eksik {sorted(set(modern) - set(tab))[:5]}")
    kapsayan = collections.defaultdict(list)
    for r in rec["ilceler"]:
        g, k = r.get("geomId"), (r["plaka"], r["ad"])
        if not g or (g not in modern and g not in hist_ids):
            if k not in izinli_geomsuz:
                sorun.append(f"1961 {k}: poligonu yok")
            continue
        for x in hide.get(g, {g}):
            kapsayan[x].append(k)
        # tablo ile tutarlilik
        for x in hide.get(g, {g}):
            s = tab.get(x)
            if s and s["yontem"] not in ("belirsiz", "bolunmus_poligon") and (int(s["plaka_1961"]), s["ilce_1961"]) != k:
                sorun.append(f"{x}: tabloda {s['ilce_1961']}, haritada {k[1]}")
    for x, ks in kapsayan.items():
        if len(ks) > 1 and not (x in tab and tab[x]["yontem"] == "bolunmus_poligon"):
            sorun.append(f"{x}: birden çok 1961 satırında {ks}")
    for x, s in tab.items():
        if s["yontem"] == "belirsiz":
            if x in kapsayan:
                sorun.append(f"{x}: tabloda belirsiz ama {kapsayan[x]} satırına bağlı")
        elif x not in kapsayan:
            sorun.append(f"{x}: tabloda {s['ilce_1961']} ama hiçbir 1961 poligonunda yok")
    # il: her katilan bugunku ilce, haritada zaten cizildigi ilin (bugunku plaka) satirina katilir
    for b in kayit.get("birlesimler", []):
        for g in b["katilanlar"]:
            if modern[g] != b["plaka"]:
                sorun.append(f"{g}: il dışı birleşim ({modern[g]} -> {b['plaka']})")
    if not sessiz:
        print("kontrol:", "geçti" if not sorun else f"{len(sorun)} sorun")
        for s in sorun[:20]:
            print("  ", s)
    return sorun


if __name__ == "__main__":
    adim = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    if adim == "tablo":
        c = tablo()
        if KAYIT.exists():
            k = oku(KAYIT)
            k["cogunluk"] = c
            KAYIT.write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    elif adim == "uygula":
        uygula()
    elif adim == "kontrol":
        sys.exit(1 if kontrol() else 0)
    else:
        uygula(tablo())
        sys.exit(1 if kontrol() else 0)
