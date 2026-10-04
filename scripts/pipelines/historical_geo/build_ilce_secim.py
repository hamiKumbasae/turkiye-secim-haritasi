"""
Bir secimin ilce haritasi: bugunku ilce -> o secimdeki ilce esleme tablosu ve o tabloya gore
birlestirilmis (dissolve) ilce poligonlari. Amac haritanin genel olarak dogru gorunmesi: hicbir bugunku
ilce sonucsuz (tarali) kalmasin; tahmine dayanan atamalar 'guven' sutununda isaretli.

Esas kaynak secim sonucudur (data/normalized/elections/<tur>/<secim>.json): o tarihte var olan ilceler,
o dosyanin ilce satirlaridir. Her bugunku ilce (geo/normalized/turkiye_ilce_sinirlari.geojson) bir
satira baglanir; hicbir kural uymazsa "belirsiz" kalir.

Adimlar (secim anahtari ilk arguman: 1961, 1965, 1987referandum ...):
  tablo   geo/historical/idari/ilce_eslesme/<secim>.csv dosyasini uretir.
  uygula  CSV'yi okur; bir satirin bugunku ilceleri, satirin su anki poligonunun kapsadigindan
          fazlaysa yeni birlesim poligonu (HIST<secim>-<plaka>-<ad>) uretir ve satirin geomId'sini
          ona cevirir. Oy/katilim degismez. Kayit: ilce_eslesme/<secim>.json.
  kontrol satir/poligon/il tutarliligini denetler (tests/validate_elections.py de calistirir).
  (adim yok: tablo + uygula + kontrol)

Esleme yontemleri (CSV -> yontem, guven):
  kendi_satiri       kesin     Bugunku ilce o tarihte de ilceydi.
  tarihsel_birlesim  kesin     Mevcut kaynakli birlesimin parcasi: apply_idari_merges.py (HISTK-*, kurulus
                               kanununun ek listesine gore tek kaynakli) ya da repoda dogrulanmis HIST-*.
  bolunmus_poligon   kesin/~   Bugunku poligon iki ilce arasinda bolunmus (Eminonu/Fatih; Istanbul'da
                               mahalle duzeyinde, ornek 1961 Arnavutkoy: Eyup + Catalca).
  istanbul_mahalle   kesin/~   build_istanbul_1961_1992.py (mahalle tablosu ya da ZINCIR).
  istanbul_zinciri   kesin     build_istanbul_1961_1992.py -> ZINCIR.
  ayni_eski_ilce     kesin     Birden cok eski ilceden kuruldu, ama hepsi o tarihte ayni ilcedeydi.
  cogunluk           yaklasik  Kanun ek listesindeki birimlerin en az %70'i ayni ilceden.
  en_buyuk_pay       kaba      %70'e ulasan yok; en buyuk paya sahip ilceye.
  komsuluk           kaba      Soy bilgisi yok ya da eski ilceleri o tarihte belirsiz; en uzun sinirini
                               paylastigi satira (ayni ilde; il o secimde yoksa komsu ilin satirina).
  belirsiz                     Hicbiri uymadi; tarali kalir.

Sira: [prepare_istanbul_historical_assignments.py -> build_istanbul_1961_1992.py] ->
build_ilce_secim.py <secim> -> scripts/build.py -> checksum yenile.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_ilce_secim.py <secim> [tablo|uygula|kontrol]
"""
import collections
import csv
import json
import pathlib
import re
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from build_istanbul_1961_1992 import ZINCIR  # noqa: E402
import build_istanbul_1992_2008 as b9208  # noqa: E402
from common.election_io import election_path, load_election, save_election  # noqa: E402
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
ESLESME = IDARI / "ilce_eslesme"
# secim: ayarla() ile
SECIM = TARIH = CSV = KAYIT = ONEK = None
LINEAGE = IDARI / "district_lineage.json"
PLAN = IDARI / "merge_plan.json"
IST = IDARI / "istanbul_1961_1992.json"
IST_TABLO = IDARI / "istanbul_1961_1992_mahalle.json"
NOTLAR = IDARI / "harita_notlari.json"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = ROOT / "geo/historical/district_splits.json"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
ESIK = 0.7
BIZIM = re.compile(r"^HIST\d{4}[a-z]*-")
ALANLAR = ["guncel_geomId", "guncel_il", "guncel_ilce", "kurulus_tarihi", "kurulus_kanunu", "plaka_secim",
           "il_secim", "ilce_secim", "geomId_secim", "yontem", "guven", "kaynak", "not"]
GUVEN = {"kendi_satiri": "kesin", "tarihsel_birlesim": "kesin", "bolunmus_poligon": "kesin", "istanbul_mahalle": "kesin",
         "istanbul_zinciri": "kesin", "ayni_eski_ilce": "kesin", "cogunluk": "yaklasik", "en_buyuk_pay": "kaba",
         "komsuluk": "kaba", "belirsiz": ""}
LINEAGE_KAYNAK = "geo/historical/idari/district_lineage.json"
# repodaki kismi kanit (kaba atamalarin notuna eklenir)
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


def ayarla(secim):
    """secim anahtari (ornek '1961', '1987referandum') icin dosya adlari ve tarih"""
    global SECIM, TARIH, CSV, KAYIT, ONEK
    from build_idari_katman import secimler
    SECIM = secim
    TARIH = next(s["tarih"] for s in secimler() if s["anahtar"] == secim)
    CSV, KAYIT = ESLESME / f"{secim}.csv", ESLESME / f"{secim}.json"
    ONEK = f"HIST{secim}-"


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

    ist = oku(IST) if IST.exists() else {"secimler": {}}
    ist_ids = {v["geomId"] for v in ist["secimler"].get(SECIM, {}).get("satirlar", {}).values()}
    ist_tablo = oku(IST_TABLO)["ilceler"] if IST_TABLO.exists() else {}

    def ist_bilgi(g):
        """Istanbul bugunku ilcesinin 1961 atamasi: (guven, kaynak, not)"""
        for bas, bit, _, dayanak in ZINCIR.get(g[-3:], []) if modern_plaka[g] == 34 else []:
            if bas <= TARIH < bit:
                return ("yaklasik" if dayanak.startswith("Yaklaşık") else "kesin",
                        "build_istanbul_1961_1992.py → ZINCIR", dayanak)
        if g in ist_tablo:
            ds = [d for m in ist_tablo[g]["mahalleler"] for d in m["donemler"] if d["baslangic"] <= TARIH < d["bitis"]]
            say = collections.Counter(d["ilce"] for d in ds)
            yk = sum(1 for d in ds if d.get("yaklasik"))
            return ("yaklasik" if yk else "kesin", "geo/historical/idari/istanbul_1961_1992_mahalle.json",
                    "Mahalle düzeyinde: " + ", ".join(f"{a} {n}" for a, n in say.most_common())
                    + (f" ({yk} mahalle yaklaşık: 1960 sayımı / komşuluk)" if yk else ""))
        return "kesin", "build_istanbul_1961_1992.py", ""

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
                    "plaka_secim": hedef[0] if hedef else "", "il_secim": il61[hedef[0]] if hedef else "",
                    "ilce_secim": hedef[1] if hedef else "", "geomId_secim": satirlar[hedef]["geomId"] if hedef else "",
                    "yontem": yontem, "guven": GUVEN[yontem], "kaynak": kaynak, "not": not_}

    # 1) su anki 1961 poligonlarinin kapsadiklari
    for g in sorted(modern_plaka):
        ks = bagli.get(g, [])
        if len(ks) > 1:
            if g == "TR-D-34-020":
                yaz(g, None, "bolunmus_poligon", "scripts/pipelines/historical_geo/split_eminonu_fatih.py",
                    "Seçim tarihinde " + " ve ".join(k[1] for k in ks) + " arasında bölünmüş; her biri kendi HIST poligonuyla")
            else:
                gv, kaynak, not_ = ist_bilgi(g)
                yaz(g, None, "bolunmus_poligon", kaynak,
                    "Seçim tarihinde " + " ve ".join(k[1] for k in ks) + " arasında bölünmüş. " + not_)
                satir[g]["guven"] = gv
            satir[g].update(plaka_secim=ks[0][0], il_secim=il61[ks[0][0]], ilce_secim=" + ".join(k[1] for k in ks),
                            geomId_secim=" + ".join(satirlar[k]["geomId"] for k in ks))
            continue
        if not ks:
            continue
        k = ks[0]
        gid = satirlar[k]["geomId"]
        if gid == g:
            yaz(g, k, "kendi_satiri", str(election_path(SECIM).relative_to(ROOT)))
            l = lineage[g]
            if ((l.get("kurulus") or {}).get("tarih") or "") > TARIH:
                if l["lineageStatus"] == "merkez_ilce" or l.get("merkezIlceDonusumu"):
                    satir[g]["not"] = "Seçim tarihinde il Merkez ilçesi; bugünkü adı sonradan (merkez ilçe dönüşümü)"
                else:
                    satir[g]["guven"] = "şüpheli"
                    satir[g]["not"] = ("Kuruluşu seçimden sonra; seçim verisindeki satır bu ilçe olamaz "
                                       "(idari/README.md → Bilinen boşluklar). Eşleşme korunuyor, doğrulanmalı")
            continue
        if gid in ist_ids:
            gv, kaynak, not_ = ist_bilgi(g)
            yaz(g, k, "istanbul_mahalle", kaynak, not_ or f"Seçim satırı {k[1]} poligonu")
            satir[g]["guven"] = gv
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
                "Seçim satırı " + k[1] + " poligonu: " + taban)

    # 2) kapsanmayan bugunku ilceler: istanbul zinciri, kanun soyu (iteratif: soy zinciri)
    dagilim = {}  # bugunku ilce -> {(plaka, ad) ya da None: pay}
    for g in satir:
        if satir[g]["yontem"] != "bolunmus_poligon":
            dagilim[g] = {(int(satir[g]["plaka_secim"]), satir[g]["ilce_secim"]): 1.0}

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
    # Istanbul: ZINCIR ya da mahalle tablosundaki o tarihteki ilce -> o ilceyi bu secimde kapsayan satir
    # (yerel secimlerde ilce satiri yerine il merkezi belediyesi poligonu olabilir: 1963-1977 HISTY)
    ist_kod = {a: k for a, k in b9208.ILCELER.items() if k}

    def ist_satir(il):
        if (34, il) in satirlar:
            return (34, il)
        ks = bagli.get(f"TR-D-34-{ist_kod.get(il, '')}", [])
        return ks[0] if len(ks) == 1 else None

    ist_kaynak = {}
    for g in kalan:
        kod = g.split("-")[-1]
        if modern_plaka[g] != 34:
            continue
        say = collections.Counter()
        for bas, bit, il, dayanak in ZINCIR.get(kod, []):
            if bas <= TARIH < bit:
                say[il] += 1
                ist_kaynak[g] = ("build_istanbul_1961_1992.py → ZINCIR", dayanak)
        if not say and g in ist_tablo:
            say = collections.Counter(d["ilce"] for m in ist_tablo[g]["mahalleler"] for d in m["donemler"]
                                      if d["baslangic"] <= TARIH < d["bitis"] and d["ilce"])
            ist_kaynak[g] = ("geo/historical/idari/istanbul_1961_1992_mahalle.json",
                             "Mahalle düzeyinde: " + ", ".join(f"{a} {n}" for a, n in say.most_common()))
        if not say:
            continue
        pay = collections.Counter()
        for il, n in say.items():
            pay[ist_satir(il)] += n / sum(say.values())
        if None in pay:
            ist_kaynak.pop(g, None)
            continue
        if len(pay) == 1:
            k = next(iter(pay))
            kaynak, not_ = ist_kaynak.pop(g)
            yaz(g, k, "istanbul_zinciri", kaynak, not_ + ("" if k[1] in say else f" (bu seçimde {k[1]} satırında)"))
            satir[g]["guven"] = "yaklasik" if not_.startswith("Yaklaşık") else "kesin"
        dagilim[g] = dict(pay)
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
    # cozulemeyenler: soy payi (cogunluk / en buyuk pay) ya da komsuluk
    modern_geom = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in oku(MODERN)["features"]}
    hist_f = {f["properties"]["id"]: f for f in hist["features"]}
    satirli_il = {r["plaka"] for r in rec["ilceler"] if r.get("geomId")}
    satir_geom = {}
    for k, r in satirlar.items():
        gid = r.get("geomId")
        if gid in modern_geom:
            satir_geom[k] = [modern_geom[gid]]
        elif gid in hist_f:
            satir_geom[k] = [temiz(shape(hist_f[gid]["geometry"]))]

    def aday_mi(g, k):
        """bugunku ilce yalniz haritada cizildigi ilin satirina katilir; o il bu secimde yoksa komsu ile"""
        return k in satir_geom and (k[0] == modern_plaka[g] or modern_plaka[g] not in satirli_il)

    komsu = {}  # g -> (kaynak, not on eki)
    for g in kalan:
        if g in satir:
            continue
        l = lineage[g]
        ks = soy(g)
        ek = ks.get("eskiIlceler") or []
        kaynak = ((f"{ks['kanun']} sayılı Kanun ek ({ks['listeNo']}) sayılı liste" if ks.get("listeNo")
                   else f"{ks['kanun']} sayılı Kanun (ek listesiz, madde metni)") if ks else LINEAGE_KAYNAK)
        birim = ", ".join(f"{e['ad'] or 'kaynağı yazılmamış'} {e['birimSayisi']}" for e in ek)
        etiket = "Ek liste birimleri: "
        if g in ist_kaynak:
            (kaynak, birim), etiket = ist_kaynak[g], ""
        kanit = f". {KISMI_KANIT[g]}" if g in KISMI_KANIT else ""
        d = dagilim.get(g)
        if d:
            uygun = {k: v for k, v in d.items() if k and aday_mi(g, k)}
            enbuyuk = max(uygun, key=lambda k: uygun[k], default=None)
            pay = uygun.get(enbuyuk, 0)
            digerleri = sorted(((k[1] if k else "bilinmiyor"), round(v, 3)) for k, v in d.items() if k != enbuyuk)
            payli = ", ".join(f"%{round(v * 100)} {a}" for a, v in digerleri)
            if enbuyuk and pay > 0.9999:
                yaz(g, enbuyuk, "ayni_eski_ilce", kaynak,
                    f"{etiket}{birim}; hepsi seçim tarihinde {enbuyuk[1]} ilçesindeydi")
                continue
            if enbuyuk:
                yontem = "cogunluk" if pay >= ESIK else "en_buyuk_pay"
                yaz(g, enbuyuk, yontem, kaynak,
                    f"{etiket}{birim}; seçimdeki ilçelere göre %{round(pay * 100)} {enbuyuk[1]}"
                    + (", " + payli if payli else "") + kanit)
                satir[g]["_cogunluk"] = {"ana": enbuyuk[1], "pay": round(pay, 2),
                                         "digerleri": [[a, round(v, 2)] for a, v in digerleri]}
                continue
            komsu[g] = (kaynak, f"{etiket}{birim}; eski ilçelerin seçim tarihindeki karşılığı "
                                "bilinmiyor ya da başka ilde" + kanit)
            continue
        neden = {"unresolved": "kuruluş kanununun ek listesi repoda yok",
                 "kanun_kaynak_yazilmamis": "kanun ek listesinde birimlerin eski ilçesi yazılmamış",
                 }.get(l["lineageStatus"], l["lineageStatus"])
        komsu[g] = (kaynak, neden + (f"; ek liste birimleri: {birim}" if birim else "") + kanit)

    # komsuluk: en uzun sinirini paylastigi satira (iteratif; atananlar komsulari icin satirin parcasi olur)
    while komsu:
        enib = None
        for g in komsu:
            tampon = modern_geom[g].buffer(0.003)
            pay = {}
            for k, gs in satir_geom.items():
                if not aday_mi(g, k):
                    continue
                a = sum(tampon.intersection(x).area for x in gs if x.envelope.intersects(tampon))
                if a > 0:
                    pay[k] = a
            if pay:
                k = max(pay, key=pay.get)
                oran = pay[k] / sum(pay.values())
                if enib is None or oran > enib[0]:
                    enib = (oran, g, k)
        if enib is None:
            for g, (kaynak, not_) in komsu.items():
                yaz(g, None, "belirsiz", kaynak, not_ + "; komşu satır yok")
            break
        oran, g, k = enib
        kaynak, not_ = komsu.pop(g)
        yaz(g, k, "komsuluk", kaynak, f"{not_}. Komşuluk: sınırının %{round(oran * 100)} kadarı {k[1]} ile")
        satir_geom[k].append(modern_geom[g])

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
        k = (int(s["plaka_secim"]), s["ilce_secim"])
        if k not in satirlar:
            raise SystemExit(f"HATA: {s['guncel_geomId']} -> {k}: seçim sonuçlarında böyle bir ilçe yok")
        hedef[k].add(s["guncel_geomId"])

    lineage = {l["geomId"]: l for l in oku(LINEAGE)["districts"]}
    guncel_ad = {r["geomId"]: r["ad"] for r in load_election("2023")["ilceler"] if r.get("geomId")}
    ad = {g: guncel_ad.get(g) or tr_baslik(lineage[g]["ad"]) for g in modern}

    birlesimler, eklenen = [], set()
    for k, ids in sorted(hedef.items()):
        once = sk[k]
        # yalniz bugunku poligonun parcasi olanlar (Eminonu/Fatih gibi bolunmus HIST parcalari haric)
        bolunmus = {s["guncel_geomId"] for s in tab if s["yontem"] == "bolunmus_poligon"}
        if not once - ids <= {g for g in once if g not in modern} | bolunmus:
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
        for r2 in rec["ilceler"]:   # ayni adli birden cok satir (ornek 1991 Bakirkoy: iki secim cevresi)
            if (r2["plaka"], r2["ad"]) == k:
                r2["geomId"] = sid
        eklenen |= set(yeni)
        birlesimler.append({"plaka": k[0], "ilce": k[1], "geomId": sid, "oncekiGeomId": taban_id,
                            "katilanlar": yeni, "katilanAdlar": [ad[g] for g in yeni],
                            "bugunkuIlceler": sorted(icerik)})
    hist["features"].sort(key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # bu betigin girisleri (HIST<secim>-*) her ilde sona, kimlige gore sirali: secimler hangi sirayla
    # calistirilirsa calistirilsin ayni dosya
    for pl in splits:
        bizim = [e for e in splits[pl] if BIZIM.match(e["syntheticId"])]
        splits[pl] = [e for e in splits[pl] if not BIZIM.match(e["syntheticId"])] + \
            sorted(bizim, key=lambda e: e["syntheticId"])
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
    eski = json.loads(election_path(SECIM).read_text(encoding="utf-8"))
    if eski != rec:
        save_election(SECIM, rec)

    # harita notlari: artik kapsanan ilceler 1961'de taranmaz; birlesimlerin ipucu
    notlar = oku(NOTLAR)
    sec = notlar["secimler"].get(SECIM, {})
    kapsanan = set()
    for r in rec["ilceler"]:
        if r.get("geomId"):
            kapsanan |= {r["geomId"]} | set(kapsam(splits).get(r["geomId"], ()))
    for g in list(sec):
        if g in kapsanan:
            sec.pop(g)
    # Istanbul 1961 birlesimleri (build_istanbul_1961_1992.py): bugunku ilceler ve mahalle paylari
    if IST.exists():
        ist = oku(IST)
        for v in ist["secimler"].get(SECIM, {}).get("satirlar", {}).values():
            sid = v["geomId"]
            if sid in ist["sentetikler"] and len(v["bugunkuIlceler"]) > 1:
                b = {"ilceler": sorted(ad[g] for g in v["bugunkuIlceler"])}
                paylar = ist["sentetikler"][sid].get("paylar") or {}
                if paylar:
                    b["paylar"] = {ad[g]: pay for g, pay in sorted(paylar.items())}
                notlar["birlesimler"][sid] = b
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
        "not": f"build_ilce_secim.py ile üretilir; elle düzenlenmez. Tablo: ilce_eslesme/{SECIM}.csv.",
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
        # ayni ad ve poligonlu ikinci satir (secim cevresi bolunmesi, ornek 1991 Bakirkoy) tek ilce sayilir
        if any(x is not r and (x["plaka"], x["ad"], x.get("geomId")) == (r["plaka"], r["ad"], r.get("geomId"))
               for x in rec["ilceler"][:rec["ilceler"].index(r)]):
            continue
        g, k = r.get("geomId"), (r["plaka"], r["ad"])
        if not g or (g not in modern and g not in hist_ids):
            if k not in izinli_geomsuz:
                sorun.append(f"{SECIM} {k}: poligonu yok")
            continue
        for x in hide.get(g, {g}):
            kapsayan[x].append(k)
        # tablo ile tutarlilik
        for x in hide.get(g, {g}):
            s = tab.get(x)
            if s and s["yontem"] not in ("belirsiz", "bolunmus_poligon") and (int(s["plaka_secim"]), s["ilce_secim"]) != k:
                sorun.append(f"{x}: tabloda {s['ilce_secim']}, haritada {k[1]}")
    for x, ks in kapsayan.items():
        if len(ks) > 1 and not (x in tab and tab[x]["yontem"] == "bolunmus_poligon"):
            sorun.append(f"{x}: birden çok seçim satırında {ks}")
    for x, s in tab.items():
        if s["yontem"] == "belirsiz":
            if x in kapsayan:
                sorun.append(f"{x}: tabloda belirsiz ama {kapsayan[x]} satırına bağlı")
        elif x not in kapsayan:
            sorun.append(f"{x}: tabloda {s['ilce_secim']} ama hiçbir seçim poligonunda yok")
    # il: her katilan bugunku ilce, haritada zaten cizildigi ilin (bugunku plaka) satirina katilir
    satirli_il = {r["plaka"] for r in rec["ilceler"] if r.get("geomId")}
    for b in kayit.get("birlesimler", []):
        for g in b["katilanlar"]:
            if modern[g] != b["plaka"] and modern[g] in satirli_il:
                sorun.append(f"{g}: il dışı birleşim ({modern[g]} -> {b['plaka']})")
    if not sessiz:
        print("kontrol:", "geçti" if not sorun else f"{len(sorun)} sorun")
        for s in sorun[:20]:
            print("  ", s)
    return sorun


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("kullanım: build_ilce_secim.py <seçim> [tablo|uygula|kontrol]")
    ayarla(sys.argv[1])
    adim = sys.argv[2] if len(sys.argv) > 2 else "hepsi"
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
