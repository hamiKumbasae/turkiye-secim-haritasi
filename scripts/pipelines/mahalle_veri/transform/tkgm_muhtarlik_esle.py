"""
YSK muhtarlik sonuclarini (fetch_muhtarlik_tum.js) TKGM mahalle sinirlariyla (fetch_tkgm_mahalle.py)
eslestirip sitenin mahalle verisine yazar.

Eslestirme ayni ilce (geomId) icinde yapilir:
  1. birebir: fold_mahalle(YSK muhtarlik adi) == fold_mahalle(TKGM adi)
  2. yakin: kalanlar icin ad benzerligi >= ESIK (difflib), en iyi aday tek ve karsiliksiz olmali
  3. eslesmeyen muhtarlik ve TKGM birimi raporlanir (docs/rapor/mahalle_eslesme/<secim>.csv)
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
from common.turkish_text import fold_mahalle  # noqa: E402
from party_map_helper import build_party_mapping  # noqa: E402

TKGM_DIR = ROOT / "data" / "raw" / "tkgm" / "mahalle"
MUHTARLIK_DIR = ROOT / "data" / "raw" / "ysk" / "muhtarlik"
GEO = ROOT / "geo" / "normalized" / "mahalle_geo.json"
MAHALLE = ROOT / "data" / "normalized" / "mahalle"
GEOMID_MAP = json.loads((ROOT / "data/raw/ysk/acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))
RAPOR = ROOT / "docs" / "rapor" / "mahalle_eslesme"
ESIK = 0.85
BAGIMSIZ = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def tkgm_yukle():
    birimler = collections.defaultdict(list)   # geomId -> [feature]
    for f in sorted(TKGM_DIR.glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            g = ft["properties"].get("geomId")
            if g and ft.get("geometry"):
                birimler[g].append(ft)
    return birimler


def esle(muhtarliklar, birimler):
    """muhtarliklar: {mid: kayit}; birimler: [feature]. Doner: {mid: (feature, yontem)}"""
    ad_birim = collections.defaultdict(list)
    for ft in birimler:
        ad_birim[fold_mahalle(ft["properties"]["ad"])].append(ft)
    sonuc, kalan = {}, {}
    for mid, m in muhtarliklar.items():
        aday = ad_birim.get(fold_mahalle(m["ad"]))
        if aday and len(aday) == 1:
            sonuc[mid] = (aday[0], "birebir")
        else:
            kalan[mid] = m
    kullanilan = {id(ft) for ft, _ in sonuc.values()}
    serbest = {fold_mahalle(ft["properties"]["ad"]): ft for ft in birimler if id(ft) not in kullanilan}
    # yakin eslesme: puana gore, bire bir
    adaylar = []
    for mid, m in kalan.items():
        a = fold_mahalle(m["ad"])
        for ad, ft in serbest.items():
            p = difflib.SequenceMatcher(None, a, ad).ratio()
            if p >= ESIK:
                adaylar.append((p, mid, ad))
    alinan_m, alinan_b = set(), set()
    for p, mid, ad in sorted(adaylar, reverse=True):
        if mid in alinan_m or ad in alinan_b:
            continue
        sonuc[mid] = (serbest[ad], f"yakin {p:.2f}")
        alinan_m.add(mid)
        alinan_b.add(ad)
    return sonuc


def kayit_yap(toplam, col_to_key):
    oy = collections.Counter()
    for col, v in toplam["oy"].items():
        if not v:
            continue
        oy["Bağımsız" if BAGIMSIZ.match(col) else col_to_key[col]] += v
    gecerli = toplam["gecerli"]
    r = {
        "secmen": toplam["secmen"], "sandik": toplam["sandik"],
        "katilim": round(toplam["oyKullanan"] / toplam["secmen"] * 100, 2) if toplam["secmen"] else None,
        "kazanan": max(oy, key=oy.get) if oy else None,
        "oy": {p: {"oran": round(v / gecerli * 100, 2) if gecerli else None, "oy": v} for p, v in sorted(oy.items())},
        "gecerliOy": gecerli, "oyKullanan": toplam["oyKullanan"],
    }
    return r


def topla(liste):
    t = {"secmen": 0, "oyKullanan": 0, "gecerli": 0, "gecersiz": 0, "sandik": 0, "oy": collections.Counter()}
    for m in liste:
        for k in ("secmen", "oyKullanan", "gecerli", "gecersiz", "sandik"):
            t[k] += m[k]
        t["oy"].update(m["oy"])
    return t


def isle(anahtar, birimler, geo, uygula):
    ham = json.loads((MUHTARLIK_DIR / f"{anahtar}.json").read_text(encoding="utf-8"))
    secim = load_election(anahtar)
    mevcut = set()
    for lv in ("iller", "ilceler"):
        for r in secim[lv]:
            mevcut.update(r["oy"])
    col_to_key = build_party_mapping(ham["colToName"], mevcut - {"Diğer", "Bağımsız"}, {})
    yol = MAHALLE / f"{anahtar}.json"
    veri = json.loads(yol.read_text(encoding="utf-8"))

    sayac = collections.Counter()
    il_sayac = collections.defaultdict(collections.Counter)
    rapor = []
    yeni_ilceler = {}
    for key, ilce in ham["ilceler"].items():
        g = GEOMID_MAP.get(key)
        muh = {mid: m for mid, m in ilce["muhtarliklar"].items() if mid != "_muhtarliksiz"}
        s_ilce = sum(m["secmen"] for m in ilce["muhtarliklar"].values())
        il = ilce["ilAdi"]
        il_sayac[il]["secmen"] += s_ilce
        sayac["secmen"] += s_ilce
        if "_muhtarliksiz" in ilce["muhtarliklar"]:
            s = ilce["muhtarliklar"]["_muhtarliksiz"]["secmen"]
            sayac["muhtarliksiz_secmen"] += s
            il_sayac[il]["muhtarliksiz"] += s
        if not g or g not in birimler:
            sayac["sinirsiz_ilce_secmen"] += s_ilce
            il_sayac[il]["sinirsiz"] += s_ilce
            for mid, m in muh.items():
                rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"], "ilçenin TKGM sınırı yok", ""])
            continue
        es = esle(muh, birimler[g])
        gruplar = collections.defaultdict(list)
        for mid, m in muh.items():
            if mid in es:
                ft, yontem = es[mid]
                gruplar[ft["properties"]["tkgm_id"]].append((m, ft, yontem))
                sayac["eslesen_" + yontem.split()[0]] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
                if yontem != "birebir":
                    rapor.append([anahtar, il, ilce["ilceAdi"], m["ad"], m["secmen"], "yakın eşleşme", ft["properties"]["ad"] + f" ({yontem})"])
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
            ilce_kayit[k] = kayit_yap(topla([m for m, _, _ in lst]), col_to_key)
            if uygula:
                ad = lst[0][0]["ad"] if len(lst) == 1 else ft["properties"]["ad"]
                geo.setdefault(g, {})[k] = {"ad": ad, "geometry": ft["geometry"]}
        yeni_ilceler[g] = ilce_kayit
    eski_secmen = sum((r.get("secmen") or 0) for g in yeni_ilceler for r in veri.get(g, {}).values())
    yeni_secmen = sum(r["secmen"] for k in yeni_ilceler.values() for r in k.values())
    if uygula:
        for g, k in yeni_ilceler.items():
            if k:
                veri[g] = k
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
    for anahtar in secimler:
        s, il_s, eski, yeni = isle(anahtar, birimler, geo, uygula)
        T = s["secmen"]
        print(f"\n{anahtar}: YSK seçmeni {T:,} | haritaya bağlanan {yeni:,} (%{yeni / T * 100:.1f}); önceki {eski:,} (%{eski / T * 100:.1f})")
        print(f"   birebir {s['eslesen_birebir']}, yakın {s['eslesen_yakin']}, eşleşmeyen {s['eslesmeyen']} muhtarlık "
              f"({s['eslesmeyen_secmen']:,} seçmen), muhtarlıksız sandık seçmeni {s['muhtarliksiz_secmen']:,}, "
              f"TKGM sınırı olmayan ilçelerde {s['sinirsiz_ilce_secmen']:,}, birleşen birim {s['birlesen_birim']}")
        kotu = sorted(il_s.items(), key=lambda x: x[1]["eslesen_secmen"] / max(x[1]["secmen"], 1))[:8]
        print("   en düşük iller:", ", ".join(f"{il} %{v['eslesen_secmen'] / max(v['secmen'], 1) * 100:.1f}" for il, v in kotu))
    if uygula:
        GEO.write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        print("\nyazıldı:", GEO)
    else:
        print("\n(kontrol: hiçbir dosya yazılmadı)")


if __name__ == "__main__":
    main()
