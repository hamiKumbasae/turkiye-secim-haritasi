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
  5. Mevcut poligonlarla alaninin %25'inden fazlasi ortusen TKGM birimi cizilmez (ust uste binme).
  6. eslesmeyen muhtarliklar raporlanir (docs/rapor/mahalle_eslesme/<secim>.csv)
Partiler: ulke genelinde %ANA_ESIK ustu olanlar ve o mahallenin kazanani ayri, gerisi 'Diğer'.
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
MUHTARLIK_DIR = ROOT / "data" / "raw" / "ysk" / "muhtarlik"
GEO = ROOT / "geo" / "normalized" / "mahalle_geo.json"
MAHALLE = ROOT / "data" / "normalized" / "mahalle"
GEOMID_MAP = json.loads((ROOT / "data/raw/ysk/acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))
RAPOR = ROOT / "docs" / "rapor" / "mahalle_eslesme"
ESIK = 0.85
ANA_ESIK = 1.5   # ulke geneli oy orani (%); altindaki partiler mahalle verisinde 'Diğer'e toplanir
# TKGM ilce adi projedekinden farkli yazilan ilceler (fold edilmis TKGM adi -> geomId)
ILCE_ALIAS = {"19 MAYIS": "TR-D-55-001"}   # Samsun Ondokuzmayıs
BAGIMSIZ = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def ad_anahtari(ad):
    """fold_mahalle + TKGM'nin 'Yeni Mahalle', 'X Köyü' gibi ekleri (paylasilan fold_mahalle 'MAHALLE'
    sozcugunu atmadigi icin burada)."""
    p = fold_mahalle(ad).split(" ")
    while len(p) > 1 and p[-1] in ("MAHALLE", "MAHALLESI", "KOYU", "KOY", "MAH"):
        p.pop()
    return " ".join(p)


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
        for ad, ft in serbest.items():
            p = difflib.SequenceMatcher(None, a, ad).ratio()
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


def kayit_yap(toplam, col_to_key, ana_partiler):
    """Ulke genelinde %ANA_ESIK ustu partiler ve o mahallenin kazanani ayri; gerisi 'Diğer'
    (sitenin onceki mahalle verisiyle ayni yogunluk). Kazanan toplanmamis oylara gore."""
    ham = collections.Counter()
    for col, v in toplam["oy"].items():
        if v:
            ham["Bağımsız" if BAGIMSIZ.match(col) else col_to_key[col]] += v
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


def isle(anahtar, birimler, geo, uygula):
    ham = json.loads((MUHTARLIK_DIR / f"{anahtar}.json").read_text(encoding="utf-8"))
    secim = load_election(anahtar)
    mevcut = set()
    for lv in ("iller", "ilceler"):
        for r in secim[lv]:
            mevcut.update(r["oy"])
    col_to_key = build_party_mapping(ham["colToName"], mevcut - {"Diğer", "Bağımsız"}, {})
    ulke = collections.Counter()
    for r in secim["iller"]:
        for p_, v in r["oy"].items():
            ulke[p_] += v["oy"] if isinstance(v, dict) else v
    ulke_top = sum(ulke.values()) or 1
    ana_partiler = {p_ for p_, v in ulke.items() if v / ulke_top * 100 >= ANA_ESIK and p_ not in ("Diğer", "Bağımsız")}
    print(f"   {anahtar} ayrı tutulan partiler: {sorted(ana_partiler)}")
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
        # 1) mevcut (OSM/ttezer) poligon adla birebir ve tekse o kullanilir: bunlar guncel idari mahalle
        #    sinirlari; TKGM birimleri ise kadastro mahallesi (sehir merkezlerinde birkac idari mahalleyi
        #    kapsayabilir). 2) kalan muhtarliklar TKGM'ye eslenir; mevcut poligonlarla %25'ten fazla
        #    ortusen TKGM birimi cizilmez (ust uste binme olmasin).
        eski = collections.defaultdict(list)
        for pid, pv in geo.get(g, {}).items():
            if not pid.startswith("k"):
                eski[ad_anahtari(pv.get("ad"))].append(pid)
        gruplar = collections.defaultdict(list)
        eski_gruplar = collections.defaultdict(list)
        tkgm_aday = {}
        for mid, m in muh.items():
            if len(eski.get(ad_anahtari(m["ad"]), [])) == 1:
                eski_gruplar[eski[ad_anahtari(m["ad"])][0]].append(m)
                sayac["eslesen_eski"] += 1
                il_sayac[il]["eslesen_secmen"] += m["secmen"]
            else:
                tkgm_aday[mid] = m
        es = esle(tkgm_aday, birimler[g])
        eski_birlesik = None
        if eski_gruplar and es:
            from shapely.geometry import shape
            from shapely.ops import unary_union
            from shapely.validation import make_valid
            eski_birlesik = unary_union([make_valid(shape(geo[g][pid]["geometry"])).buffer(0) for pid in eski_gruplar])
        for mid, m in tkgm_aday.items():
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
        print(f"   birebir {s['eslesen_birebir']}, yakın {s['eslesen_yakin']}, mevcut poligon {s['eslesen_eski']}, çakışma nedeniyle çizilmeyen {s['cakisan']}, eşleşmeyen {s['eslesmeyen']} muhtarlık "
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
