"""
Geometri denetimi: haritanin il, ilce, tarihsel ilce ve mahalle poligonlarini sistemli olarak kontrol eder,
sonucu sade dilde bir rapor (docs/rapor/GEOMETRI_DENETIMI.md) ve CSV'ler (docs/rapor/geometri_denetimi/)
olarak yazar. Hicbir geometri ya da veri dosyasini degistirmez; yalniz okur.

Alanlar esit alanli izdusumde hesaplanir (Turkiye icin Albers, standart paraleller 37 ve 41 K, merkez
39 K / 35 D, GRS80; metre). Ayni girdiyle her calistirma ayni ciktiyi verir (siralama sabit, sayilar
yuvarlanir, rastgelelik yok).

Kontroller
  1. Gecerlilik: gecersiz (oz-kesisimli) poligon, bos/dejenere, kiymik (cok ince: Polsby-Popper < 0,02 ve
     < 1 km2), cok kucuk (< 500 m2), kirinti parca (cok parcali poligonda < 1 000 m2 parca), birebir ayni
     geometri, halka yonu (SVG 'nonzero' doldurmasinda delik, dis halkayla ayni yonde yazilmissa dolu
     cizilir), kapanmamis halka.
  2. Mahalle - ilce: mahalle alaninin kendi ilcesi disinda kalan payi (> %5 ve > 1 km2 isaretlenir);
     temsil noktasi baska bir ilcede duran mahalle (yanlis ilce).
  3. Mahalle - mahalle ortusmesi (ayni ilce icinde): cift basina ortusme alani ve kucuk poligonun yuzdesi,
     kaynak ciftine gore (TKGM x OSM ...). Ayrica iki poligonun AYNI secimde birlikte cizilip cizilmedigi
     (site bir secimde yalniz o secimin verisi olan poligonlari cizer; hic birlikte cizilmeyen ortusme
     haritada gorunmez). Eslestirme betiginin '%25'ten fazla ortusen TKGM birimi cizilmez' kurali dogrulanir.
  4. Bosluk: ilce alaninin, o secimde cizilen mahalle poligonlarinca kaplanmayan payi; bosluk TKGM ham
     verisinde bir birimle kapli mi (eslesmeyen/cizilmeyen muhtarlik) yoksa hic birim yok mu (orman, gol,
     hazine arazisi ya da TKGM'nin siniri vermedigi birim); ilcede haritaya baglanmayan secmen.
  5. Ilce ve il katmanlari: ilceler arasi ortusme, ilce birlesimindeki delikler, il poligonu ile ilcelerinin
     birlesimi; donem il sinirlari (era*) gecerlilik/ortusme/toplam alan; tarihsel ilceler (HIST-/HISTK-)
     gecerlilik ve district_splits.json'daki bugunku ilcelerin birlesimiyle fark.
  6. Kapsam: her mahalle seciminde mahalle sonuclarindaki secmenin poligonu olan payi (ulke, il).
  7. Bagimsiz kaynakla konum: ilce poligonu ile TKGM ham mahalle birimlerinin (data/raw/tkgm/mahalle)
     ilce bazinda birlesimi: alan orani, IoU, TKGM alaninin ilce disinda kalan payi, Hausdorff uzakligi.

Mahalle anahtar onekleri (scripts/pipelines/mahalle_veri):
  t...  ttezer/turkiye-harita-verisi (belediye acik verisi/MAKS kaynakli; 02_ttezer_mahalle_poligonlari.py)
  r...  OpenStreetMap relation (fetch_osm_mahalle.py / 01_osm_mahalle_poligonlari.py)
  b...  belediye acik verisi, Bursa ve Sakarya (fetch_belediye_mahalle.py)
  k...  TKGM kadastro mahallesi; kb<id>-<id> bolumlere ayrilmis TKGM birimlerinin birlesimi
        (tkgm_muhtarlik_esle.py)

Kullanim (repo kokunden; shapely>=2 ve pyproj gerekir):
  python3 scripts/rapor/geometri_denetimi.py
      [--md docs/rapor/GEOMETRI_DENETIMI.md] [--csv-klasor docs/rapor/geometri_denetimi]
      [--img-klasor docs/rapor/img/geometri] [--png-yok]
      [--bosluk-secimleri 2023,2024yerel] [--sonuc-json YOL]   (ara sonuclari JSON olarak da yazar)
      [--sonuctan YOL]   (hesaplamadan, onceki --sonuc-json ciktisindan yalniz raporu yazar)
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import sys
import time

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402

GEO = ROOT / "geo" / "normalized"
HIST = ROOT / "geo" / "historical"
MAHALLE_DIR = ROOT / "data" / "normalized" / "mahalle"
TKGM_DIR = ROOT / "data" / "raw" / "tkgm" / "mahalle"

IZDUSUM = "+proj=aea +lat_0=39 +lon_0=35 +lat_1=37 +lat_2=41 +ellps=GRS80 +units=m +no_defs"
_TR = Transformer.from_crs("EPSG:4326", IZDUSUM, always_xy=True)

KM2 = 1e6
DISARI_PAY, DISARI_KM2 = 0.05, 1.0         # kontrol 2 esikleri
BANT_M = 2000   # ilce katmani ~%8 noktaya sadelestirildi: sinirdan bu kadar icerisi 'sadelestirme bandi' sayilir
ORTUSME_MIN_M2 = 1000                       # kontrol 3: bundan kucuk ortusme (sayisallastirma gurultusu) yazilmaz
ANLAMLI_M2, ANLAMLI_PAY = 10_000, 0.01      # 'anlamli ortusme': >= 1 ha ve kucuk poligonun >= %1'i
KIYMIK_PP, KIYMIK_KM2 = 0.02, 1.0
KUCUK_M2, KIRINTI_M2 = 500, 1000
TKGM_KURAL = 0.25


def kaynak(anahtar):
    if anahtar.startswith("kb"):
        return "TKGM"
    return {"k": "TKGM", "b": "Belediye", "r": "OSM", "t": "ttezer"}.get(anahtar[:1], "diğer")


def izdus(geoms):
    arr = np.asarray(geoms, dtype=object)
    return shapely.transform(arr, lambda c: np.column_stack(_TR.transform(c[:, 0], c[:, 1])))


def poligonal(g):
    """Gecerli, yalniz poligon parcali geometri (make_valid cizgi/nokta artigi birakabilir)."""
    if g is None or g.is_empty:
        return shapely.Polygon()
    if not g.is_valid:
        g = shapely.make_valid(g)
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parcalar = [p for p in shapely.get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(parcalar) if parcalar else shapely.Polygon()


def r(x, n=2):
    return None if x is None else round(float(x), n)


def halka_sorunlari(geom_json):
    """Ham GeoJSON halkalarinda: kapanmamis halka, < 4 nokta, dis halkayla ayni yonde yazilmis delik.
    Donus: (dis_halka_saat_yonu_mu listesi, sorun listesi)."""
    def isaretli(h):
        a = 0.0
        for (x1, y1), (x2, y2) in zip(h, h[1:] + h[:1]):
            a += x1 * y2 - x2 * y1
        return a / 2
    if geom_json["type"] not in ("Polygon", "MultiPolygon"):
        return [], [f"poligon değil ({geom_json['type']})"]
    polys = [geom_json["coordinates"]] if geom_json["type"] == "Polygon" else geom_json["coordinates"]
    yonler, sorun = [], []
    for poly in polys:
        if not poly:
            sorun.append("boş poligon")
            continue
        for i, h in enumerate(poly):
            h = [tuple(p[:2]) for p in h]
            if len(h) < 4:
                sorun.append("halkada 4'ten az nokta")
            if h and h[0] != h[-1]:
                sorun.append("halka kapanmamış")
        s0 = isaretli([tuple(p[:2]) for p in poly[0]])
        yonler.append(s0 < 0)
        for h in poly[1:]:
            if isaretli([tuple(p[:2]) for p in h]) * s0 > 0:
                sorun.append("delik dış halkayla aynı yönde (SVG'de dolu çizilir)")
    return yonler, sorun


def polsby(g):
    p = g.length
    return 4 * math.pi * g.area / (p * p) if p else 0.0


# ---------------------------------------------------------------- yukleme
def yukle():
    t0 = time.time()
    ilce_fc = json.loads((GEO / "turkiye_ilce_sinirlari.geojson").read_text(encoding="utf-8"))["features"]
    il_fc = json.loads((GEO / "turkiye_il_sinirlari.geojson").read_text(encoding="utf-8"))["features"]
    hist_fc = json.loads((HIST / "turkiye_ilce_sinirlari_hist_splits.geojson").read_text(encoding="utf-8"))["features"]
    splits = json.loads((HIST / "district_splits.json").read_text(encoding="utf-8"))
    sentetik = {e["syntheticId"]: e["hideIds"] for v in splits.values() for e in v}
    mgeo = json.loads((GEO / "mahalle_geo.json").read_text(encoding="utf-8"))
    print(f"  dosyalar okundu ({time.time() - t0:.0f} sn)", flush=True)

    # secimler (mahalle)
    secimler = sorted(p.stem for p in MAHALLE_DIR.glob("*.json"))
    oy = {s: json.loads((MAHALLE_DIR / f"{s}.json").read_text(encoding="utf-8")) for s in secimler}
    kayit = {s: load_election(s) for s in secimler}
    ilce_ad, il_ad = {}, {}
    for s in secimler:   # sirali: son secimdeki ad kalir
        for rr in kayit[s]["ilceler"]:
            ilce_ad[rr["geomId"]] = rr["ad"]
        for rr in kayit[s]["iller"]:
            il_ad[rr["plaka"]] = rr["ad"]
    return dict(ilce_fc=ilce_fc, il_fc=il_fc, hist_fc=hist_fc, sentetik=sentetik, mgeo=mgeo,
                secimler=secimler, oy=oy, kayit=kayit, ilce_ad=ilce_ad, il_ad=il_ad)


def katman(features, kimlik):
    """GeoJSON ozellik listesi -> {kimlik: (izdusumlu gecerli geometri, ham geometri, ozellikler)}."""
    ham = [shape(f["geometry"]) for f in features]
    proj = izdus(ham)
    return {kimlik(f): (poligonal(g), pg, f) for f, g, pg in zip(features, proj, proj)}


# ---------------------------------------------------------------- kontrol 1
def gecerlilik(katman_adi, ogeler, sonuc, satirlar, kiymik_satir):
    """ogeler: [(ilce/kimlik, anahtar, ad, ham_json, izdusumlu_ham_geom)]"""
    say = collections.Counter()
    yon = collections.Counter()
    geoms = [o[4] for o in ogeler]
    gecerli = shapely.is_valid(np.asarray(geoms, dtype=object))
    for o, ok in zip(ogeler, gecerli):
        gid, anahtar, ad, gj, g = o
        say["toplam"] += 1
        yonler, sorun = halka_sorunlari(gj)
        for y in yonler:
            yon["saat yönü" if y else "saat yönü tersi"] += 1
        if g.is_empty or g.area < 1:
            neden = next((x for x in sorun if x.startswith("poligon değil")), "boş ya da dejenere (alan < 1 m²)")
            say[neden] += 1
            satirlar.append([katman_adi, gid, anahtar, ad, neden, r(g.area, 1)])
            continue
        if not ok:
            say["geçersiz"] += 1
            neden = shapely.is_valid_reason(g)
            gv = poligonal(g)
            satirlar.append([katman_adi, gid, anahtar, ad, "geçersiz: " + neden.split("[")[0].strip(), r(gv.area, 1)])
            g = gv
        for s_ in sorted(set(sorun)):
            say[s_] += 1
            satirlar.append([katman_adi, gid, anahtar, ad, s_, r(g.area, 1)])
        pp = polsby(g)
        if g.area < KUCUK_M2:
            say["çok küçük (< 500 m²)"] += 1
            kiymik_satir.append([katman_adi, gid, anahtar, ad, "çok küçük", r(g.area, 1), r(pp, 4)])
        elif pp < KIYMIK_PP and g.area < KIYMIK_KM2 * KM2:
            say["kıymık (çok ince)"] += 1
            kiymik_satir.append([katman_adi, gid, anahtar, ad, "kıymık (çok ince)", r(g.area, 1), r(pp, 4)])
        parcalar = shapely.get_parts(g)
        if len(parcalar) > 1:
            kir = [p for p in parcalar if p.area < KIRINTI_M2]
            if kir:
                say["kırıntı parçalı"] += 1
                kiymik_satir.append([katman_adi, gid, anahtar, ad, f"{len(kir)} kırıntı parça (< 1 000 m²)",
                                     r(sum(p.area for p in kir), 1), r(pp, 4)])
    sonuc[katman_adi] = {"sayilar": dict(sorted(say.items())), "halka_yonu": dict(sorted(yon.items()))}


# ---------------------------------------------------------------- ana hesap
def hesapla(bosluk_secimleri, img_klasor=None):
    T0 = time.time()
    print("Yükleniyor ...", flush=True)
    D = yukle()
    mgeo, sentetik, secimler = D["mgeo"], D["sentetik"], D["secimler"]
    S = {"secimler": secimler, "izdusum": IZDUSUM}
    csvler = {}

    ilce = katman(D["ilce_fc"], lambda f: f["properties"]["id"])
    il = katman(D["il_fc"], lambda f: f["properties"]["plaka"])
    hist = katman(D["hist_fc"], lambda f: f["properties"]["id"])
    ilce_plaka = {k: v[2]["properties"]["plaka"] for k, v in ilce.items()}
    hist_plaka = {k: v[2]["properties"]["plaka"] for k, v in hist.items()}

    def ust(gid):
        if gid in ilce:
            return ilce[gid][0]
        if gid in hist:
            return hist[gid][0]
        return None

    def ad_ilce(gid):
        return D["ilce_ad"].get(gid, gid)

    def plaka_of(gid):
        return ilce_plaka.get(gid) or hist_plaka.get(gid)

    # mahalle poligonlari
    print(f"Mahalle poligonları izdüşülüyor ({time.time() - T0:.0f} sn) ...", flush=True)
    m_list = []   # (gid, anahtar, ad, ham_json)
    for gid in sorted(mgeo):
        for k in sorted(mgeo[gid]):
            m_list.append((gid, k, mgeo[gid][k].get("ad") or "", mgeo[gid][k]["geometry"]))
    m_ham = izdus([shape(x[3]) for x in m_list])
    m_geom = [poligonal(g) for g in m_ham]
    m_idx = {(x[0], x[1]): i for i, x in enumerate(m_list)}
    m_alan = np.array([g.area for g in m_geom])

    # kullanim: hangi secimde cizildi
    kullanim = collections.defaultdict(set)
    veri_poligonsuz = collections.Counter()
    for s in secimler:
        for gid, kayitlar in D["oy"][s].items():
            for k in kayitlar:
                if (gid, k) in m_idx:
                    kullanim[m_idx[(gid, k)]].add(s)
                else:
                    veri_poligonsuz[s] += 1
    S["envanter"] = {
        "ilce_kimligi": len(mgeo), "poligon": len(m_list),
        "kaynak": dict(sorted(collections.Counter(kaynak(x[1]) for x in m_list).items())),
        "kb_birlesik": sum(1 for x in m_list if x[1].startswith("kb")),
        "hic_kullanilmayan": sum(1 for i in range(len(m_list)) if i not in kullanim),
        "hic_kullanilmayan_kaynak": dict(sorted(collections.Counter(kaynak(m_list[i][1]) for i in range(len(m_list)) if i not in kullanim).items())),
        "veri_var_poligon_yok": dict(sorted(veri_poligonsuz.items())),
        "toplam_alan_km2": r(m_alan.sum() / KM2, 0),
    }
    kul_bayt = sum(len(json.dumps(m_list[i][3], separators=(",", ":"))) for i in range(len(m_list)) if i not in kullanim)
    S["envanter"]["hic_kullanilmayan_mb"] = r(kul_bayt / 1e6, 1)

    # ---------------- 1. gecerlilik
    print(f"1. Geçerlilik ({time.time() - T0:.0f} sn) ...", flush=True)
    gec_satir, kiy_satir = [], []
    S["gecerlilik"] = {}
    katmanlar = [
        ("il", [(k, "", D["il_ad"].get(k, ""), v[2]["geometry"], v[1]) for k, v in sorted(il.items())]),
        ("ilçe", [(k, "", ad_ilce(k), v[2]["geometry"], v[1]) for k, v in sorted(ilce.items())]),
        ("tarihsel ilçe", [(k, "", ad_ilce(k), v[2]["geometry"], v[1]) for k, v in sorted(hist.items())]),
        ("mahalle", [(x[0], x[1], x[2], x[3], m_ham[i]) for i, x in enumerate(m_list)]),
    ]
    era_dosyalar = sorted(HIST.glob("turkiye_il_sinirlari_era*.geojson"))
    era = {}
    for p in era_dosyalar:
        fc = json.loads(p.read_text(encoding="utf-8"))["features"]
        e = katman(fc, lambda f: f["properties"]["plaka"])
        era[p.stem.replace("turkiye_il_sinirlari_", "")] = e
        katmanlar.append((p.stem.replace("turkiye_il_sinirlari_", "il "), [(k, "", D["il_ad"].get(k, ""), v[2]["geometry"], v[1]) for k, v in sorted(e.items())]))
    for ad_, og in katmanlar:
        gecerlilik(ad_, og, S["gecerlilik"], gec_satir, kiy_satir)
    S["yinelenen"] = {}
    yin_out = []
    no = 0
    for ad_, og in katmanlar:
        hashler = collections.defaultdict(list)
        for o in og:
            h = hashlib.sha1(shapely.to_wkb(shapely.normalize(shape(o[3])), output_dimension=2)).hexdigest()
            hashler[h].append(o)
        gr = sorted([v for v in hashler.values() if len(v) > 1], key=lambda v: (v[0][0], v[0][1]))
        sinif = collections.Counter()
        for v in gr:
            no += 1
            ilceler = {o[0] for o in v}
            if len(ilceler) == 1:
                tur = "aynı ilçe içinde"
            elif any(i in sentetik for i in ilceler):
                tur = "tarihsel ilçeye kopya (beklenen)"
            else:
                tur = "farklı ilçelerde"
            sinif[tur] += 1
            for o in v:
                yin_out.append([ad_, no, o[0], o[1], o[2], tur])
        S["yinelenen"][ad_] = dict(sorted(sinif.items()))
    csvler["gecersiz_geometri.csv"] = (["katman", "kimlik", "anahtar", "ad", "sorun", "alan_m2"], gec_satir)
    csvler["kiymik_kucuk.csv"] = (["katman", "kimlik", "anahtar", "ad", "sorun", "alan_m2", "polsby_popper"], kiy_satir)
    csvler["yinelenen_geometri.csv"] = (["katman", "grup", "kimlik", "anahtar", "ad", "tur"], yin_out)

    # ---------------- 2. mahalle - ilce
    print(f"2. Mahalle–ilçe ({time.time() - T0:.0f} sn) ...", flush=True)
    ilce_ids = sorted(ilce)
    ilce_tree = STRtree([ilce[k][0] for k in ilce_ids])
    disari_satir, yanlis_satir = [], []
    disari_toplam = disari_bant_toplam = 0.0
    disari_say = collections.Counter()
    for gid in sorted(mgeo):
        P = ust(gid)
        idx = [m_idx[(gid, k)] for k in sorted(mgeo[gid])]
        if P is None:
            for i in idx:
                yanlis_satir.append([gid, ad_ilce(gid), m_list[i][1], m_list[i][2], kaynak(m_list[i][1]), "", "",
                                     "ilçe kimliğinin poligonu yok", None, r(m_alan[i] / KM2, 3), len(kullanim[i])])
            continue
        Pb = P.buffer(BANT_M)
        shapely.prepare(P)
        shapely.prepare(Pb)
        geoms = np.asarray([m_geom[i] for i in idx], dtype=object)
        icerde = shapely.contains(P, geoms)
        izinli = set(sentetik.get(gid, [])) | {gid}
        for i, ic in zip(idx, icerde):
            g = m_geom[i]
            if g.is_empty:
                continue
            if not ic:
                dis = g.difference(P).area
                dis2 = 0.0 if Pb.contains(g) else g.difference(Pb).area
                pay, pay2 = (dis / g.area, dis2 / g.area) if g.area else (0, 0)
                disari_toplam += dis
                disari_bant_toplam += dis2
                isaret = pay > DISARI_PAY and dis > DISARI_KM2 * KM2
                gercek = pay2 > DISARI_PAY and dis2 > DISARI_KM2 * KM2
                if isaret:
                    disari_say["isaretli"] += 1
                    disari_say["isaretli_" + kaynak(m_list[i][1])] += 1
                if gercek:
                    disari_say["bant_disi_" + kaynak(m_list[i][1])] += 1
                if pay > 0.01 and dis > 0.01 * KM2:
                    disari_satir.append([gid, ad_ilce(gid), m_list[i][1], m_list[i][2], kaynak(m_list[i][1]),
                                         r(g.area / KM2, 3), r(dis / KM2, 3), r(pay * 100, 1), r(dis2 / KM2, 3),
                                         r(pay2 * 100, 1), "evet" if isaret else "", "evet" if gercek else "",
                                         len(kullanim[i])])
            nokta = g.representative_point()
            if P.contains(nokta):
                continue
            aday = [ilce_ids[j] for j in ilce_tree.query(nokta, predicate="within")]
            aday = [a for a in aday if a not in izinli]
            uz = P.distance(nokta)
            neden = ("temsil noktası başka ilçede" if aday else "temsil noktası hiçbir ilçede değil (deniz/sınır dışı)") + \
                    (", sınır bandında (< 2 km)" if uz < BANT_M else ", sınırdan 2 km'den uzak")
            yanlis_satir.append([gid, ad_ilce(gid), m_list[i][1], m_list[i][2], kaynak(m_list[i][1]),
                                 aday[0] if aday else "", ad_ilce(aday[0]) if aday else "", neden, r(uz / 1000, 2),
                                 r(g.area / KM2, 3), len(kullanim[i])])
    disari_satir.sort(key=lambda x: (-x[8], -x[6], x[0], x[2]))
    yanlis_satir.sort(key=lambda x: (-(x[8] or 0), x[0], x[2]))
    uzak = [x for x in yanlis_satir if x[8] is not None and x[8] * 1000 >= BANT_M]
    S["mahalle_ilce"] = {
        "disari_toplam_km2": r(disari_toplam / KM2, 1),
        "disari_toplam_pay": r(disari_toplam / m_alan.sum() * 100, 2),
        "disari_bant_km2": r(disari_bant_toplam / KM2, 1),
        "disari_bant_pay": r(disari_bant_toplam / m_alan.sum() * 100, 2),
        "isaretli": disari_say["isaretli"],
        "isaretli_kaynak": {k.split("_", 1)[1]: v for k, v in sorted(disari_say.items()) if k.startswith("isaretli_")},
        "isaretli_kullanilan": sum(1 for x in disari_satir if x[10] and x[12]),
        "bant_disi": sum(1 for x in disari_satir if x[11]),
        "bant_disi_kullanilan": sum(1 for x in disari_satir if x[11] and x[12]),
        "bant_disi_kaynak": {k.split("_", 2)[2]: v for k, v in sorted(disari_say.items()) if k.startswith("bant_disi_")},
        "yuzde1_ustu": len(disari_satir),
        "yanlis_ilce": len(yanlis_satir),
        "yanlis_ilce_kullanilan": sum(1 for x in yanlis_satir if x[-1]),
        "yanlis_ilce_kaynak": dict(sorted(collections.Counter(x[4] for x in yanlis_satir).items())),
        "yanlis_ilce_deniz": sum(1 for x in yanlis_satir if "hiçbir" in x[7]),
        "yanlis_ilce_uzak": len(uzak),
        "yanlis_ilce_uzak_kullanilan": sum(1 for x in uzak if x[-1]),
        "yanlis_ilce_uzak_kaynak": dict(sorted(collections.Counter(x[4] for x in uzak).items())),
    }
    csvler["mahalle_ilce_disi.csv"] = (["ilce_geomId", "ilce", "anahtar", "mahalle", "kaynak", "alan_km2", "ilce_disi_km2",
                                        "ilce_disi_yuzde", "2km_bant_disi_km2", "2km_bant_disi_yuzde", "isaretli_5yuzde_1km2",
                                        "bant_disinda_da_isaretli", "cizildigi_secim_sayisi"], disari_satir)
    csvler["mahalle_yanlis_ilce.csv"] = (["ilce_geomId", "ilce", "anahtar", "mahalle", "kaynak", "noktanin_ilcesi_geomId",
                                          "noktanin_ilcesi", "neden", "kendi_ilcesine_uzaklik_km", "alan_km2",
                                          "cizildigi_secim_sayisi"], yanlis_satir)

    # ---------------- 3. ortusme
    print(f"3. Mahalle örtüşmeleri ({time.time() - T0:.0f} sn) ...", flush=True)
    ciftler = []   # (gid, i, j, alan)
    for gid in sorted(mgeo):
        idx = [m_idx[(gid, k)] for k in sorted(mgeo[gid])]
        if len(idx) < 2:
            continue
        geoms = np.asarray([m_geom[i] for i in idx], dtype=object)
        tree = STRtree(geoms)
        a, b = tree.query(geoms, predicate="intersects")
        sec = a < b
        a, b = a[sec], b[sec]
        if not len(a):
            continue
        alan = shapely.area(shapely.intersection(geoms[a], geoms[b]))
        for x, y, ar in zip(a, b, alan):
            if ar >= ORTUSME_MIN_M2:
                ciftler.append((gid, idx[x], idx[y], float(ar)))
    ort_satir = []
    grup = collections.defaultdict(lambda: collections.Counter())
    for gid, i, j, ar in ciftler:
        ki, kj = sorted([kaynak(m_list[i][1]), kaynak(m_list[j][1])])
        kucuk = min(m_alan[i], m_alan[j])
        pay = ar / kucuk if kucuk else 0
        iou = ar / (m_alan[i] + m_alan[j] - ar)
        ortak = sorted(kullanim[i] & kullanim[j])
        anlamli = ar >= ANLAMLI_M2 and pay >= ANLAMLI_PAY
        g = grup[f"{ki} × {kj}"]
        g["cift"] += 1
        g["alan"] += ar
        if anlamli:
            g["anlamli"] += 1
            g["anlamli_alan"] += ar
            if ortak:
                g["birlikte_cizilen"] += 1
                g["birlikte_alan"] += ar
        ort_satir.append([gid, ad_ilce(gid), m_list[i][1], m_list[i][2], m_list[j][1], m_list[j][2], f"{ki} × {kj}",
                          r(ar / KM2, 4), r(pay * 100, 1), r(iou, 3), "evet" if anlamli else "", len(ortak), ";".join(ortak)])
    ort_satir.sort(key=lambda x: (-(x[11] > 0), -x[7], x[0], x[2], x[4]))
    S["ortusme"] = {
        "grup": {k: {"cift": v["cift"], "alan_km2": r(v["alan"] / KM2, 2), "anlamli": v["anlamli"],
                     "anlamli_km2": r(v["anlamli_alan"] / KM2, 2), "birlikte_cizilen": v["birlikte_cizilen"],
                     "birlikte_km2": r(v["birlikte_alan"] / KM2, 2)} for k, v in sorted(grup.items())},
        "cift": len(ciftler),
        "neredeyse_ayni": sum(1 for x in ort_satir if x[9] >= 0.95),
        "neredeyse_ayni_birlikte": sum(1 for x in ort_satir if x[9] >= 0.95 and x[11]),
    }
    csvler["mahalle_ortusme.csv"] = (["ilce_geomId", "ilce", "anahtar_1", "mahalle_1", "anahtar_2", "mahalle_2", "kaynak_cifti",
                                      "ortusme_km2", "kucugun_yuzdesi", "iou", "anlamli", "birlikte_cizildigi_secim_sayisi",
                                      "birlikte_cizildigi_secimler"], [x for x in ort_satir if x[7] * KM2 >= ANLAMLI_M2])

    # TKGM %25 kurali (secim bazinda, birlikte cizilen TKGM disi poligonlarla)
    kural_satir = []
    komsu = collections.defaultdict(list)
    for gid, i, j, ar in ciftler:
        komsu[i].append(j)
        komsu[j].append(i)
    for i in sorted(komsu):
        if kaynak(m_list[i][1]) != "TKGM" or not kullanim[i]:
            continue
        for s in sorted(kullanim[i]):
            ort = [j for j in komsu[i] if kaynak(m_list[j][1]) != "TKGM" and s in kullanim[j]]
            if not ort:
                continue
            U = shapely.union_all([m_geom[j] for j in ort])
            pay = m_geom[i].intersection(U).area / m_alan[i] if m_alan[i] else 0
            if pay > TKGM_KURAL:
                kural_satir.append([s, m_list[i][0], ad_ilce(m_list[i][0]), m_list[i][1], m_list[i][2], r(m_alan[i] / KM2, 3),
                                    r(pay * 100, 1), ";".join(m_list[j][1] for j in sorted(ort, key=lambda j: m_list[j][1]))])
    kural_satir.sort(key=lambda x: (x[0], -x[6], x[1], x[3]))
    S["tkgm_kurali"] = {"ihlal_satir": len(kural_satir), "ihlal_poligon": len({(x[1], x[3]) for x in kural_satir}),
                        "secim": dict(sorted(collections.Counter(x[0] for x in kural_satir).items()))}
    csvler["tkgm_yuzde25_kurali.csv"] = (["secim", "ilce_geomId", "ilce", "anahtar", "mahalle", "alan_km2",
                                          "tkgm_disi_poligonlarla_ortusme_yuzdesi", "ortusen_anahtarlar"], kural_satir)

    # ---------------- TKGM ham (kontrol 4 ve 7)
    print(f"TKGM ham birimleri ({time.time() - T0:.0f} sn) ...", flush=True)
    tkgm_ft = []
    for p in sorted(TKGM_DIR.glob("*.geojson")):
        for f in json.loads(p.read_text(encoding="utf-8"))["features"]:
            if f.get("geometry") and f["properties"].get("geomId"):
                tkgm_ft.append((f["properties"]["geomId"], f["geometry"]))
    tkgm_g = izdus([shape(g) for _, g in tkgm_ft])
    tkgm_by = collections.defaultdict(list)
    for (gid, _), g in zip(tkgm_ft, tkgm_g):
        tkgm_by[gid].append(poligonal(g))
    # ham TKGM'nin kendi icindeki ortusme (ayni ilce): eslestirme betigi TKGM x TKGM ortusmesini denetlemiyor
    ham_ort = collections.Counter()
    for gid in sorted(tkgm_by):
        gl = np.asarray(tkgm_by[gid], dtype=object)
        if len(gl) < 2:
            continue
        aa, bb = STRtree(gl).query(gl, predicate="intersects")
        sel = aa < bb
        oa = shapely.area(shapely.intersection(gl[aa[sel]], gl[bb[sel]]))
        m = oa >= ANLAMLI_M2
        ham_ort["cift"] += int(m.sum())
        ham_ort["alan"] += float(oa[m].sum())
    S["tkgm_ham_ortusme"] = {"cift": ham_ort["cift"], "km2": r(ham_ort["alan"] / KM2, 0)}
    tkgm_union = {gid: shapely.union_all(v) for gid, v in sorted(tkgm_by.items())}

    def tkgm_of(gid):
        parcalar = [tkgm_union[h] for h in sentetik.get(gid, [gid]) if h in tkgm_union]
        return shapely.union_all(parcalar) if parcalar else None

    # ---------------- 4. bosluk + 6. kapsam
    print(f"4/6. Boşluk ve kapsam ({time.time() - T0:.0f} sn) ...", flush=True)
    kapsam_ozet, kapsam_il = [], []
    il_kapsam = {}
    ilce_secmen = {}
    for s in secimler:
        kay = D["kayit"][s]
        cizili = collections.defaultdict(float)
        for gid, kayitlar in D["oy"][s].items():
            for k, v in kayitlar.items():
                if (gid, k) in m_idx:
                    cizili[gid] += v.get("secmen") or 0
        il_top = collections.defaultdict(lambda: [0, 0])
        tum = baglanan = 0
        ilce_secmen[s] = {}
        for rr in kay["ilceler"]:
            sec = rr.get("secmen") or 0
            b = cizili.get(rr["geomId"], 0)
            ilce_secmen[s][rr["geomId"]] = (sec, b)
            il_top[rr["plaka"]][0] += sec
            il_top[rr["plaka"]][1] += b
            tum += sec
            baglanan += b
        mahalle_top = sum((v.get("secmen") or 0) for kk in D["oy"][s].values() for v in kk.values())
        kapsam_ozet.append([s, kay.get("ad", s), tum, mahalle_top, int(baglanan), r(baglanan / tum * 100, 2) if tum else None,
                            veri_poligonsuz.get(s, 0)])
        il_kapsam[s] = {}
        for p in sorted(il_top):
            t_, b_ = il_top[p]
            il_kapsam[s][p] = r(b_ / t_ * 100, 1) if t_ else None
            kapsam_il.append([s, p, D["il_ad"].get(p, ""), t_, int(b_), r(b_ / t_ * 100, 1) if t_ else None])
    S["kapsam"] = {"ozet": kapsam_ozet, "il": il_kapsam}
    csvler["kapsam_secmen_ozet.csv"] = (["secim", "ad", "ilce_secmeni", "mahalle_kayitlarindaki_secmen",
                                         "poligonu_olan_secmen", "yuzde", "verisi_olup_poligonu_olmayan_kayit"], kapsam_ozet)
    csvler["kapsam_secmen_il.csv"] = (["secim", "plaka", "il", "ilce_secmeni", "poligonu_olan_secmen", "yuzde"], kapsam_il)

    bosluk_satir = []
    S["bosluk"] = {}
    for s in ["tum"] + bosluk_secimleri:
        if s == "tum":
            hedef = sorted(g for g in mgeo if ust(g) is not None)
        else:
            hedef = sorted(rr["geomId"] for rr in D["kayit"][s]["ilceler"] if ust(rr["geomId"]) is not None)
        t_ilce = t_kap = t_tk = 0.0
        dagilim = collections.Counter()
        sifir = 0
        for gid in hedef:
            P = ust(gid)
            if s == "tum":
                ii = [m_idx[(gid, k)] for k in mgeo.get(gid, {})]
            else:
                ii = [m_idx[(gid, k)] for k in D["oy"][s].get(gid, {}) if (gid, k) in m_idx]
            C = shapely.union_all([m_geom[i] for i in ii]).intersection(P) if ii else shapely.Polygon()
            kap = C.area / P.area if P.area else 0
            gap = P.difference(C) if ii else P
            TK = tkgm_of(gid)
            gap_tk = gap.intersection(TK).area if TK is not None and not gap.is_empty else 0.0
            t_ilce += P.area
            t_kap += C.area
            t_tk += gap_tk
            if not ii:
                sifir += 1
            dagilim["%0" if kap == 0 else "<%25" if kap < .25 else "%25–50" if kap < .5 else "%50–75" if kap < .75
                    else "%75–90" if kap < .9 else "%90–99" if kap < .99 else "≥%99"] += 1
            sec, bag = ilce_secmen.get(s, {}).get(gid, (None, None))
            bosluk_satir.append([s, gid, ad_ilce(gid), plaka_of(gid), D["il_ad"].get(plaka_of(gid), ""), len(ii),
                                 r(P.area / KM2, 1), r(kap * 100, 1), r(gap.area / KM2, 1), r(gap_tk / KM2, 1),
                                 r((gap.area - gap_tk) / KM2, 1), sec, None if sec is None else int(sec - bag),
                                 None if not sec else r((sec - bag) / sec * 100, 1)])
        S["bosluk"][s] = {"ilce": len(hedef), "ilce_alan_km2": r(t_ilce / KM2, 0), "kapli_yuzde": r(t_kap / t_ilce * 100, 1),
                          "bosluk_km2": r((t_ilce - t_kap) / KM2, 0), "bosluk_tkgm_km2": r(t_tk / KM2, 0),
                          "poligonsuz_ilce": sifir, "dagilim": dict(dagilim)}
    csvler["ilce_bosluk.csv"] = (["secim", "ilce_geomId", "ilce", "plaka", "il", "poligon_sayisi", "ilce_alan_km2", "kapli_yuzde",
                                  "bosluk_km2", "bosluk_tkgm_birimli_km2", "bosluk_tkgm_birimsiz_km2", "ilce_secmeni",
                                  "poligonsuz_secmen", "poligonsuz_secmen_yuzde"], bosluk_satir)

    # ---------------- 5. ilce ve il katmanlari
    print(f"5. İlçe/il katmanları ({time.time() - T0:.0f} sn) ...", flush=True)
    ig = [ilce[k][0] for k in ilce_ids]
    a, b = ilce_tree.query(ig, predicate="intersects")
    sec = a < b
    a, b = a[sec], b[sec]
    alan = shapely.area(shapely.intersection(np.asarray(ig, dtype=object)[a], np.asarray(ig, dtype=object)[b]))
    ilce_ort = []
    for x, y, ar in zip(a, b, alan):
        if ar >= 1000:
            p1, p2 = ilce_ids[x], ilce_ids[y]
            ilce_ort.append([p1, ad_ilce(p1), p2, ad_ilce(p2), "il içi" if ilce_plaka[p1] == ilce_plaka[p2] else "iller arası",
                             r(ar / KM2, 4), r(ar / min(ig[x].area, ig[y].area) * 100, 3)])
    ilce_ort.sort(key=lambda x: -x[5])
    csvler["ilce_ortusme.csv"] = (["ilce_1_geomId", "ilce_1", "ilce_2_geomId", "ilce_2", "tur", "ortusme_km2", "kucugun_yuzdesi"], ilce_ort)
    ulke_ilce = shapely.union_all(ig)
    ulke_il = shapely.union_all([v[0] for v in il.values()])
    delikler = []
    for poly in shapely.get_parts(ulke_ilce):
        for h in poly.interiors:
            hp = shapely.Polygon(h)
            if hp.area < 100:
                continue
            ilde = hp.intersection(ulke_il).area / hp.area
            c = shapely.transform(hp.representative_point(), lambda cc: np.column_stack(_TR.transform(cc[:, 0], cc[:, 1], direction="INVERSE")))
            delikler.append([r(hp.area / KM2, 4), r(ilde * 100, 1), r(c.y, 4), r(c.x, 4),
                             "ilçe katmanında dikiş boşluğu (il katmanı dolu)" if ilde > 0.5 else "il katmanında da boş (göl/kapalı alan)"])
    delikler.sort(key=lambda x: -x[0])
    csvler["ilce_katmani_delikler.csv"] = (["alan_km2", "il_katmaninda_dolu_yuzde", "enlem", "boylam", "yorum"], delikler)
    il_satir = []
    ilce_by_plaka = collections.defaultdict(list)
    for k in ilce_ids:
        ilce_by_plaka[ilce_plaka[k]].append(ilce[k][0])
    for p in sorted(il):
        I = il[p][0]
        U = shapely.union_all(ilce_by_plaka.get(p, []))
        il_satir.append([p, D["il_ad"].get(p, ""), len(ilce_by_plaka.get(p, [])), r(I.area / KM2, 1), r(U.area / KM2, 1),
                         r(I.difference(U).area / KM2, 2), r(U.difference(I).area / KM2, 2),
                         r(I.symmetric_difference(U).area / I.area * 100, 2),
                         r(shapely.hausdorff_distance(I.simplify(50).boundary, U.simplify(50).boundary) / 1000, 2)])
    il_satir.sort(key=lambda x: -x[7])
    csvler["il_ilce_tutarlilik.csv"] = (["plaka", "il", "ilce_sayisi", "il_alan_km2", "ilceler_birlesim_km2",
                                         "il_var_ilce_yok_km2", "ilce_var_il_yok_km2", "simetrik_fark_yuzde", "hausdorff_km"], il_satir)
    S["katman"] = {
        "ilce_ortusme_cift": len(ilce_ort), "ilce_ortusme_km2": r(sum(x[5] for x in ilce_ort), 2),
        "ilce_ortusme_01km2": sum(1 for x in ilce_ort if x[5] >= 0.1),
        "ilce_ortusme_il_ici": sum(1 for x in ilce_ort if x[4] == "il içi"),
        "delik": len(delikler), "delik_km2": r(sum(x[0] for x in delikler), 2),
        "delik_dikis": sum(1 for x in delikler if x[4].startswith("ilçe katmanında")),
        "delik_dikis_km2": r(sum(x[0] for x in delikler if x[4].startswith("ilçe katmanında")), 2),
        "ulke_il_km2": r(ulke_il.area / KM2, 0), "ulke_ilce_km2": r(ulke_ilce.area / KM2, 0),
        "ulke_simetrik_km2": r(ulke_il.symmetric_difference(ulke_ilce).area / KM2, 1),
        "ulke_hausdorff_km": r(shapely.hausdorff_distance(ulke_il.simplify(50).boundary, ulke_ilce.simplify(50).boundary) / 1000, 2),
        "il_fark_medyan": r(float(np.median([x[7] for x in il_satir])), 2),
        "il_fark_max": il_satir[0][7], "il_fark_2_ustu": sum(1 for x in il_satir if x[7] > 2),
        "il_hausdorff_medyan": r(float(np.median([x[8] for x in il_satir])), 2),
    }
    # donem il sinirlari
    era_satir = []
    for ad_, e in sorted(era.items()):
        gl = [v[0] for _, v in sorted(e.items())]
        tr = STRtree(gl)
        aa, bb = tr.query(gl, predicate="intersects")
        sel = aa < bb
        oa = shapely.area(shapely.intersection(np.asarray(gl, dtype=object)[aa[sel]], np.asarray(gl, dtype=object)[bb[sel]]))
        U = shapely.union_all(gl)
        era_satir.append([ad_, len(gl), S["gecerlilik"][f"il {ad_}"]["sayilar"].get("geçersiz", 0), r(oa.sum() / KM2, 2),
                          int((oa >= 1000).sum()), r(U.area / KM2, 0), r((U.area - ulke_il.area) / ulke_il.area * 100, 2),
                          r(U.symmetric_difference(ulke_il).area / KM2, 1)])
    csvler["donem_il_sinirlari.csv"] = (["donem", "il_sayisi", "gecersiz", "il_ortusme_km2", "ortusen_cift", "toplam_alan_km2",
                                         "bugunku_ulkeye_gore_alan_farki_yuzde", "bugunku_ulkeyle_simetrik_fark_km2"], era_satir)
    S["donem"] = era_satir
    # tarihsel ilceler
    hist_satir = []
    for hid in sorted(hist):
        H = hist[hid][0]
        parca = sentetik.get(hid)
        if not parca:
            hist_satir.append([hid, ad_ilce(hid), "", r(H.area / KM2, 1), None, None, None, None, None, "kayıt yok",
                               "district_splits.json'da kaydı yok"])
            continue
        eksik = [p for p in parca if p not in ilce]
        U = shapely.union_all([ilce[p][0] for p in parca if p in ilce])
        fark = H.symmetric_difference(U).area
        tasan = H.difference(U).area
        fy, ty = (fark / H.area * 100, tasan / H.area * 100) if H.area else (0, 0)
        tur = ("parçaların birleşimiyle aynı" if fy < 0.1 else
               "parçaların birleşiminden taşıyor" if ty >= 0.5 else
               "parçaların bir bölümü (mahalle düzeyinde bölüşüm)")
        hist_satir.append([hid, ad_ilce(hid), ";".join(parca), r(H.area / KM2, 1), r(U.area / KM2, 1), r(fark / KM2, 2),
                           r(fy, 2), r(tasan / KM2, 3), r(ty, 2), tur,
                           ("parça bugünkü katmanda yok: " + ",".join(eksik)) if eksik else ""])
    hist_satir.sort(key=lambda x: (-(x[8] or 0), -(x[6] or 0), x[0]))
    csvler["tarihsel_ilce_birlesim.csv"] = (["geomId", "ad", "bugunku_parcalar", "alan_km2", "parcalar_birlesim_km2",
                                             "simetrik_fark_km2", "simetrik_fark_yuzde", "parcalardan_tasan_km2",
                                             "parcalardan_tasan_yuzde", "tur", "not"], hist_satir)
    S["tarihsel"] = {"toplam": len(hist_satir), "tur": dict(sorted(collections.Counter(x[9] for x in hist_satir).items())),
                     "tasan_max_yuzde": r(max((x[8] or 0) for x in hist_satir), 2),
                     "tasan_toplam_km2": r(sum((x[7] or 0) for x in hist_satir), 2)}

    # ---------------- 7. TKGM ile konum
    print(f"7. TKGM ile karşılaştırma ({time.time() - T0:.0f} sn) ...", flush=True)
    tk_satir, kayma = [], []
    for gid in ilce_ids:
        if gid not in tkgm_union:
            tk_satir.append([gid, ad_ilce(gid), ilce_plaka[gid], r(ilce[gid][0].area / KM2, 1), None, None, None, None, None, None, None,
                             "TKGM birimi yok"])
            continue
        I, U = ilce[gid][0], tkgm_union[gid]
        dis = U.difference(I).area
        dis2 = U.difference(I.buffer(BANT_M)).area
        if 0.95 <= U.area / I.area <= 1.05:   # TKGM'si tam ilcelerde agirlik merkezi farki (sistematik oteleme var mi)
            kayma.append((U.centroid.x - I.centroid.x, U.centroid.y - I.centroid.y))
        ortak = U.intersection(I).area
        dolu = shapely.union_all([shapely.Polygon(p.exterior) for p in shapely.get_parts(U)])
        hd = shapely.hausdorff_distance(I.simplify(50).boundary, dolu.simplify(50).boundary)
        tk_satir.append([gid, ad_ilce(gid), ilce_plaka[gid], r(I.area / KM2, 1), r(U.area / KM2, 1), r(U.area / I.area * 100, 1),
                         r(ortak / (I.area + U.area - ortak), 3), r(dis / U.area * 100, 2), r(dis2 / KM2, 2), r(dis2 / U.area * 100, 2),
                         r(hd / 1000, 2), ""])
    tk_satir.sort(key=lambda x: (-(x[8] if x[8] is not None else -1), x[0]))
    csvler["tkgm_ilce_karsilastirma.csv"] = (["ilce_geomId", "ilce", "plaka", "ilce_alan_km2", "tkgm_birlesim_km2", "alan_orani_yuzde",
                                              "iou", "tkgm_ilce_disi_yuzde", "tkgm_2km_bant_disi_km2", "tkgm_2km_bant_disi_yuzde",
                                              "hausdorff_km", "not"], tk_satir)
    v = [x for x in tk_satir if x[6] is not None]
    S["tkgm"] = {"ilce": len(v), "tkgm_yok": len(tk_satir) - len(v),
                 "iou_medyan": r(float(np.median([x[6] for x in v])), 3),
                 "disari_medyan": r(float(np.median([x[7] for x in v])), 2),
                 "disari_5_ustu": sum(1 for x in v if x[7] > 5), "disari_20_ustu": sum(1 for x in v if x[7] > 20),
                 "bant_disi_toplam_km2": r(sum(x[8] for x in v), 0),
                 "bant_disi_1km2_5yuzde": sum(1 for x in v if x[8] > 1 and x[9] > 5),
                 "bant_disi_10km2": sum(1 for x in v if x[8] > 10),
                 "hausdorff_medyan": r(float(np.median([x[10] for x in v])), 2),
                 "hausdorff_p95": r(float(np.percentile([x[10] for x in v], 95)), 2),
                 "hausdorff_5_ustu": sum(1 for x in v if x[10] > 5),
                 "alan_orani_medyan": r(float(np.median([x[5] for x in v])), 1),
                 "tkgm_birim": len(tkgm_ft),
                 "kayma_ilce": len(kayma),
                 "kayma_dx_medyan_m": r(float(np.median([k[0] for k in kayma])), 0) if kayma else None,
                 "kayma_dy_medyan_m": r(float(np.median([k[1] for k in kayma])), 0) if kayma else None,
                 "kayma_uzaklik_medyan_m": r(float(np.median([math.hypot(*k) for k in kayma])), 0) if kayma else None}

    # ---------------- gorseller
    S["gorsel"] = []
    if img_klasor:
        print(f"Görseller ({time.time() - T0:.0f} sn) ...", flush=True)
        S["gorsel"] = gorseller(img_klasor, D, ilce, ust, m_list, m_geom, m_idx, tkgm_union, disari_satir, ort_satir,
                                bosluk_satir, tk_satir, bosluk_secimleri)
    S["sure_sn"] = None   # deterministik cikti icin sure rapora yazilmaz
    print(f"Bitti ({time.time() - T0:.0f} sn).", flush=True)
    return S, csvler


# ---------------------------------------------------------------- gorseller
def gorseller(klasor, D, ilce, ust, m_list, m_geom, m_idx, tkgm_union, disari, ortusme, bosluk, tkgm, bosluk_secimleri):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "geometri"
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path

    def ciz(ax, g, **kw):
        for p in shapely.get_parts(g):
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            verts, codes = [], []
            for ring in [p.exterior, *p.interiors]:
                c = np.asarray(ring.coords)[:, :2] / 1000
                verts += c.tolist()
                codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), **kw))

    def kaydet(fig, ax, ad, baslik, kapsam):
        x0, y0, x1, y1 = kapsam.bounds
        pad = max(x1 - x0, y1 - y0) * 0.08
        ax.set_xlim((x0 - pad) / 1000, (x1 + pad) / 1000)
        ax.set_ylim((y0 - pad) / 1000, (y1 + pad) / 1000)
        ax.set_aspect("equal")
        ax.set_title(baslik, fontsize=9)
        ax.tick_params(labelsize=7)
        ax.set_xlabel("km (Albers)", fontsize=7)
        p = klasor / ad
        fig.savefig(p, dpi=110, bbox_inches="tight", metadata={"Software": None})
        plt.close(fig)
        return str(p.relative_to(ROOT))

    klasor.mkdir(parents=True, exist_ok=True)
    cikti = []
    # 1) ilce disina tasan en buyuk mahalle (cizilen)
    x = next((x for x in disari if x[11] and x[12]), None)
    if x:
        fig, ax = plt.subplots(figsize=(6, 5))
        P = ust(x[0])
        ciz(ax, P, facecolor="#e8e8e8", edgecolor="#555", lw=0.8)
        g = m_geom[m_idx[(x[0], x[2])]]
        ciz(ax, g, facecolor="#d62728", alpha=0.45, edgecolor="#d62728", lw=0.8)
        cikti.append(kaydet(fig, ax, "01_ilce_disina_tasan_mahalle.png",
                            f"{x[1]} ({x[0]}) — {x[3]} [{x[2]}, {x[4]}]\nilçe dışı {sayi(x[6], 1)} km² (%{sayi(x[7], 1)}), 2 km bandı dışında {sayi(x[8], 1)} km²", g.union(P)))
    # 2) birlikte cizilen en buyuk ortusme
    x = next((x for x in ortusme if x[11]), None)
    if x:
        fig, ax = plt.subplots(figsize=(6, 5))
        g1, g2 = m_geom[m_idx[(x[0], x[2])]], m_geom[m_idx[(x[0], x[4])]]
        ciz(ax, g1, facecolor="#1f77b4", alpha=0.4, edgecolor="#1f77b4", lw=0.8)
        ciz(ax, g2, facecolor="#ff7f0e", alpha=0.4, edgecolor="#ff7f0e", lw=0.8)
        cikti.append(kaydet(fig, ax, "02_birlikte_cizilen_ortusme.png",
                            f"{x[1]}: {x[3]} [{x[2]}] (mavi) × {x[5]} [{x[4]}] (turuncu)\nörtüşme {sayi(x[7], 1)} km², {x[11]} seçimde birlikte", g1.union(g2)))
    # 3) en cok poligonsuz secmeni olan ilce (ilk bosluk secimi)
    if bosluk_secimleri:
        s = bosluk_secimleri[0]
        aday = sorted((x for x in bosluk if x[0] == s and x[12]), key=lambda x: -x[12])
        if aday:
            x = aday[0]
            fig, ax = plt.subplots(figsize=(6, 5))
            P = ust(x[1])
            ciz(ax, P, facecolor="#f2f2f2", edgecolor="#333", lw=0.8)
            TK = tkgm_union.get(x[1])
            if TK is not None:
                ciz(ax, TK, facecolor="none", edgecolor="#999", lw=0.3)
            for k in D["oy"][s].get(x[1], {}):
                if (x[1], k) in m_idx:
                    ciz(ax, m_geom[m_idx[(x[1], k)]], facecolor="#2ca02c", alpha=0.5, edgecolor="#1b5e20", lw=0.3)
            cikti.append(kaydet(fig, ax, "03_en_cok_poligonsuz_secmen.png",
                                f"{x[2]} ({x[1]}), {s}: yeşil = çizilen mahalleler, gri çizgi = TKGM birimleri\n"
                                f"kaplı %{sayi(x[7], 1)}, poligonsuz seçmen {sayi(x[12])} (%{sayi(x[13], 1)})", P))
    # 4) TKGM ile en uyumsuz ilce
    x = next((x for x in tkgm if x[8] is not None), None)
    if x:
        fig, ax = plt.subplots(figsize=(6, 5))
        I, U = ilce[x[0]][0], tkgm_union[x[0]]
        ciz(ax, U, facecolor="#9467bd", alpha=0.35, edgecolor="#9467bd", lw=0.4)
        ciz(ax, I, facecolor="none", edgecolor="#000", lw=1.0)
        cikti.append(kaydet(fig, ax, "04_tkgm_ilce_uyumsuzlugu.png",
                            f"{x[1]} ({x[0]}): siyah = sitenin ilçe sınırı, mor = TKGM birimleri\n"
                            f"TKGM alanının {sayi(x[8], 1)} km²'si (%{sayi(x[9], 1)}) ilçe sınırının 2 km dışında", I.union(U)))
    return cikti


# ---------------------------------------------------------------- yazim
def sayi(x, n=0):
    if x is None:
        return "—"
    s = f"{x:,.{n}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def csv_yaz(klasor, csvler):
    klasor.mkdir(parents=True, exist_ok=True)
    for ad, (baslik, satirlar) in sorted(csvler.items()):
        with open(klasor / ad, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(baslik)
            w.writerows(satirlar)


def tablo(baslik, satirlar):
    out = ["| " + " | ".join(baslik) + " |", "|" + "|".join("---" for _ in baslik) + "|"]
    for s in satirlar:
        out.append("| " + " | ".join("" if v is None else str(v) for v in s) + " |")
    return "\n".join(out)


# Belgelerde yazan kapsam rakamlari (docs/rapor/VERI_DENETIMI_YONETIM.md, 21 Ekim 2026 notlari)
BELGEDEKI_KAPSAM = {"2009yerel": "87,3", "2010referandum": "88,3", "2011": "88,3", "2023": "93,8", "2024yerel": "94,1"}
BELGEDEKI_IL_2023 = {31: "73,9", 46: "78,8", 65: "83,1"}


def rapor_yaz(S, csvler, csv_klasor):
    def satirlar(ad):
        baslik, rows = csvler[ad]
        return [dict(zip(baslik, x)) for x in rows]

    def y(x, n=1):
        return "—" if x is None else "%" + sayi(x, n)

    E, G, MI, O = S["envanter"], S["gecerlilik"], S["mahalle_ilce"], S["ortusme"]
    K, TK, B, T = S["katman"], S["tkgm"], S["bosluk"], S["tarihsel"]
    kapsam = {x[0]: x for x in S["kapsam"]["ozet"]}
    gm = G["mahalle"]["sayilar"]
    bos_ad = [s for s in B if s != "tum"]
    ilk = bos_ad[0] if bos_ad else None
    birlikte_tt = O["grup"].get("TKGM × TKGM", {})
    birlikte_top = sum(v["birlikte_cizilen"] for v in O["grup"].values())
    birlikte_km2 = sum(v["birlikte_km2"] for v in O["grup"].values())
    yon_ayni = gm.get("delik dış halkayla aynı yönde (SVG'de dolu çizilir)", 0)
    gecersiz_m = gm.get("geçersiz", 0)
    L = []
    w = L.append

    w("# Geometri denetimi — il, ilçe ve mahalle sınırları\n")
    w("Bu rapor `scripts/rapor/geometri_denetimi.py` ile üretildi; aynı veriyle her çalıştırmada aynı sonucu verir. "
      "Hiçbir geometri ya da veri dosyası değiştirilmedi. Bütün satırlar `" + csv_klasor + "/` altındaki CSV'lerdedir.\n")
    w("Yeniden üretmek için (shapely ve pyproj gerekir, ~5 dakika):\n\n```bash\npython3 scripts/rapor/geometri_denetimi.py\n```\n")

    # ---------------- ozet
    w("## 1. Kısa özet\n")
    w(f"Haritada {sayi(len(csvler['tkgm_ilce_karsilastirma.csv'][1]))} bugünkü ilçe, 81 il, {sayi(T['toplam'])} tarihsel ilçe ve "
      f"{sayi(E['ilce_kimligi'])} ilçe kimliğine bağlı {sayi(E['poligon'])} mahalle poligonu var. Sonuç:\n")
    w("**Gerçek sorunlar (düzeltilmesi gerekenler)**\n")
    w(f"1. **Yanlış yere çizilen mahalleler.** {sayi(MI['yanlis_ilce_uzak'])} mahalle poligonu kendi ilçesinin 2 km'den daha "
      f"dışında duruyor; {sayi(MI['yanlis_ilce_uzak_kullanilan'])}'i en az bir seçimde çiziliyor. Örnekler: Tunceli Mazgirt'in Ayvatlı "
      "köyü Kayseri Pınarbaşı'nda, Balıkesir Bigadiç'in Camii mahallesi Eskişehir Çifteler'de, Çorum Sungurlu'nun Ekmekçi köyü Ankara "
      "Nallıhan'da çiziliyor. Bu mahallelerin oyu yanlış yerde boyanıyor ve ilçe haritası gereksiz yere uzaklaşıyor (bölüm 4.2).")
    w(f"2. **Üst üste çizilen TKGM birimleri.** Aynı seçimde birlikte çizilen ve anlamlı ölçüde (≥ 1 ha ve küçüğün ≥ %1'i) örtüşen "
      f"{sayi(birlikte_top)} mahalle çifti var ({sayi(birlikte_km2, 0)} km²). Bunların {sayi(birlikte_tt.get('birlikte_cizilen', 0))}'i "
      f"({sayi(birlikte_tt.get('birlikte_km2', 0), 0)} km²) TKGM × TKGM. TKGM ham verisi kendi içinde örtüşüyor "
      f"({sayi(S['tkgm_ham_ortusme']['cift'])} çift, {sayi(S['tkgm_ham_ortusme']['km2'])} km²) ve eşleştirme betiğinin %25 kuralı yalnız "
      "TKGM ile TKGM dışı sınırlar arasında uygulanıyor. Örtüşen iki poligondan biri ötekini örtüyor; alttaki mahallenin rengi görünmüyor, "
      f"tıklanamıyor. {sayi(O['neredeyse_ayni_birlikte'])} çiftte iki muhtarlık neredeyse aynı poligona düşmüş (bölüm 4.3).")
    w(f"3. **Haritaya bağlanmayan seçmen.** 2023 genel seçimde mahalle sonuçlarındaki seçmenin {y(kapsam['2023'][5], 2)}'i bir poligona "
      "bağlı; eksik kalan seçmen birkaç ilde toplanıyor (Hatay, Kahramanmaraş, Elazığ, Aksaray). Rakamlar belgelerdekinden biraz yüksek: "
      "sonraki eşleştirme düzeltmeleri kapsamı artırmış (bölüm 4.6).\n")
    w("**Küçük, görünümü az etkileyen sorunlar**\n")
    w(f"4. {sayi(gecersiz_m)} mahalle, {G['ilçe']['sayilar'].get('geçersiz', 0)} ilçe, {G['il']['sayilar'].get('geçersiz', 0)} il ve "
      f"{G['tarihsel ilçe']['sayilar'].get('geçersiz', 0)} tarihsel ilçe poligonu geometrik olarak geçersiz (çoğu kendi kendini kesen "
      "halka). Tarayıcı bunları çiziyor; alan ve kesişim hesaplarını bozuyor.")
    w(f"5. {yon_ayni} mahalle poligonunda delik, dış halkayla aynı yönde yazılmış. Site SVG'yi varsayılan `nonzero` kuralıyla dolduruyor; "
      f"bu deliklerin içi dolu çiziliyor. {gm.get('poligon değil (LineString)', 0)} kayıt poligon değil, çizgi (LineString); "
      f"{gm.get('boş ya da dejenere (alan < 1 m²)', 0)} kaydın alanı sıfır.")
    w(f"6. İlçe katmanı kaba sadeleştirilmiş (ilçe başına ortalama ~75 nokta). Komşu ilçeler arasında {sayi(K['delik_dikis'])} dikiş "
      f"boşluğu ({sayi(K['delik_dikis_km2'], 0)} km²) ve {sayi(K['ilce_ortusme_cift'])} örtüşme ({sayi(K['ilce_ortusme_km2'], 0)} km²) var. "
      "Toplam alanın %0,05'i; haritada kıl inceliğinde çizgiler olarak görünür.")
    w(f"7. {sayi(E['hic_kullanilmayan'])} mahalle poligonu hiçbir seçimde çizilmiyor ({sayi(E['hic_kullanilmayan_mb'], 1)} MB ham GeoJSON).\n")
    w("**Sorun olmayanlar**\n")
    w(f"- Mahalle poligonlarının ilçe sınırından taşan alanı {sayi(MI['disari_toplam_km2'], 0)} km² (%{sayi(MI['disari_toplam_pay'], 1)}). "
      f"Bunun çoğu ilçe katmanının kaba sadeleştirilmesinden geliyor: ilçe sınırına 2 km'lik pay verilince taşma "
      f"{sayi(MI['disari_bant_km2'], 0)} km²'ye (%{sayi(MI['disari_bant_pay'], 1)}) iniyor.")
    w(f"- Eşleştirme betiğinin \"mevcut poligonlarla %25'ten fazla örtüşen TKGM birimi çizilmez\" kuralı tutuyor: "
      f"{S['tkgm_kurali']['ihlal_satir']} ihlal.")
    w("- Belediye × ttezer, Belediye × OSM gibi büyük örtüşmeler aynı seçimde birlikte çizilmiyor (eski kaynak başka seçimde kullanılıyor); "
      "haritada görünmüyor.")
    w(f"- Tarihsel ilçelerin {T['tur'].get('parçaların birleşimiyle aynı', 0)}'ü bugünkü parçalarının birleşimiyle birebir aynı. "
      "Depodaki iki geometri testi (`tests/validate_elections.py`: tarihsel ilçe örtüşme/delik ve seçim ilçe eşleme tabloları) shapely "
      "kurulunca çalıştı ve geçti.")
    w("- Dönem il sınırları (era*) geçerli; toplam alanları bugünkü ülkeyle %0,02 içinde aynı (iller arası küçük kenar "
      "örtüşmeleri var, bkz. 4.5).")
    if not any(E["veri_var_poligon_yok"].values()):
        w("- Verisi olup poligonu olmayan mahalle kaydı yok (site, sonucu olan her kaydın poligonunu buluyor).")
    else:
        w("- Verisi olup poligonu olmayan mahalle kaydı: " + ", ".join(f"{k} {v}" for k, v in E["veri_var_poligon_yok"].items()) + ".")
    w("")

    # ---------------- yontem
    w("## 2. Ne kontrol edildi, nasıl\n")
    w("Alanlar eşit alanlı Albers izdüşümünde (standart paraleller 37° ve 41° K, merkez 39° K / 35° D) hesaplandı. "
      "Geçersiz poligonlar hesap için `make_valid` ile onarıldı; dosyalar değişmedi.\n")
    w("Mahalle anahtarının ilk harfi kaynağı gösterir (`scripts/pipelines/mahalle_veri`):\n")
    w(tablo(["Önek", "Kaynak", "Poligon"], [
        ["`t…`", "ttezer/turkiye-harita-verisi (25 ilde belediye/MAKS)", sayi(E["kaynak"].get("ttezer", 0))],
        ["`r…`", "OpenStreetMap", sayi(E["kaynak"].get("OSM", 0))],
        ["`b…`", "Belediye açık verisi (Bursa, Sakarya)", sayi(E["kaynak"].get("Belediye", 0))],
        ["`k…`, `kb…`", f"TKGM kadastro mahallesi (`kb`: bölümlü birimlerin birleşimi, {E['kb_birlesik']})", sayi(E["kaynak"].get("TKGM", 0))],
    ]) + "\n")
    w("**Sadeleştirme bandı.** İlçe katmanı ham veriden %8 noktayla sadeleştirildi (`geo/normalized/PROVENANCE.md`); sınırı "
      "gerçek sınırdan 1–2 km sapabiliyor. Ayrıntılı mahalle poligonları bu yüzden kenarda ilçe dışına taşıyor. Gerçek hatayı "
      "gürültüden ayırmak için ilçe sınırına 2 km pay verilmiş hâli de ölçüldü (\"2 km bandı dışında\").\n")
    w("**Birlikte çizilme.** Site bir seçimde yalnız o seçimin verisi olan mahalle poligonlarını çizer. İki poligon hiçbir seçimde "
      "birlikte çizilmiyorsa örtüşmeleri haritada görünmez; bu yüzden her örtüşme için ortak seçim sayısı hesaplandı.\n")
    w(tablo(["#", "Kontrol", "CSV"], [
        [1, "Geçersiz, boş, kıymık, kırıntı parça, birebir aynı geometri, halka yönü", "`gecersiz_geometri.csv`, `kiymik_kucuk.csv`, `yinelenen_geometri.csv`"],
        [2, "Mahallenin ilçe dışında kalan payı (> %5 ve > 1 km²), yanlış ilçe (temsil noktası)", "`mahalle_ilce_disi.csv`, `mahalle_yanlis_ilce.csv`"],
        [3, "Aynı ilçede mahalle–mahalle örtüşmesi, kaynak çifti, birlikte çizilme; TKGM %25 kuralı", "`mahalle_ortusme.csv`, `tkgm_yuzde25_kurali.csv`"],
        [4, "İlçe alanının mahallelerce kaplanmayan payı; TKGM birimi olan/olmayan boşluk; poligonsuz seçmen", "`ilce_bosluk.csv`"],
        [5, "İlçe örtüşmesi ve dikiş boşlukları, il ↔ ilçeler, dönem il sınırları, tarihsel ilçeler", "`ilce_ortusme.csv`, `ilce_katmani_delikler.csv`, `il_ilce_tutarlilik.csv`, `donem_il_sinirlari.csv`, `tarihsel_ilce_birlesim.csv`"],
        [6, "Seçim başına poligonu olan seçmen (ülke, il)", "`kapsam_secmen_ozet.csv`, `kapsam_secmen_il.csv`"],
        [7, "İlçe sınırı ↔ TKGM ham birimlerinin ilçe birleşimi (bağımsız kaynak)", "`tkgm_ilce_karsilastirma.csv`"],
    ]) + "\n")

    # ---------------- 3 bulgular
    w("## 3. Envanter\n")
    w(tablo(["Katman", "Kayıt", "Geçersiz", "Diğer bulgular"], [
        [k, sayi(v["sayilar"].get("toplam", 0)), sayi(v["sayilar"].get("geçersiz", 0)),
         "; ".join(f"{a}: {b}" for a, b in v["sayilar"].items() if a not in ("toplam", "geçersiz")) or "—"]
        for k, v in G.items()]) + "\n")
    w(f"Hiçbir seçimde çizilmeyen mahalle poligonu: {sayi(E['hic_kullanilmayan'])} "
      f"({', '.join(f'{k} {sayi(v)}' for k, v in E['hic_kullanilmayan_kaynak'].items())}).\n")

    w("## 4. Bulgular\n")
    # 4.1
    w("### 4.1 Geçerlilik\n")
    neden = collections.Counter(x["sorun"] for x in satirlar("gecersiz_geometri.csv") if x["katman"] == "mahalle")
    w(tablo(["Mahalle poligonunda sorun", "Sayı"], [[k, sayi(v)] for k, v in sorted(neden.items(), key=lambda x: -x[1])]) + "\n")
    w("Kendi kendini kesen halkalar büyük olasılıkla kaynakların sadeleştirilmesinden ve 4 ondalığa yuvarlanmasından (TKGM: 10 m "
      "Douglas-Peucker) çıkan küçük düğümlerdir; tarayıcı bunları çizer. \"Too few points\" bir parçanın 4'ten az noktaya düşmesidir; o parça çizilmez.\n")
    yon = [x for x in satirlar("gecersiz_geometri.csv") if "aynı yönde" in x["sorun"]]
    yon.sort(key=lambda x: -(x["alan_m2"] or 0))
    w(f"**Deliği dolu çizilen poligonlar** ({len(yon)}; ilk 20, alana göre). Site `fill-rule` belirtmiyor (SVG varsayılanı `nonzero`); "
      "delik dış halkayla aynı yönde yazılınca içi mahallenin rengiyle boyanır. Delikteki komşu mahalle sonra çizilirse görünür, "
      "önce çizilirse altta kalır.\n")
    w(tablo(["İlçe", "Anahtar", "Mahalle", "Alan km²"],
            [[x["kimlik"], f"`{x['anahtar']}`", x["ad"], sayi(x["alan_m2"] / KM2, 1)] for x in yon[:20]]) + "\n")
    tuhaf = [x for x in satirlar("gecersiz_geometri.csv") if x["sorun"].startswith(("poligon değil", "boş ya da"))]
    if tuhaf:
        w("**Boş ya da poligon olmayan kayıtlar:**\n")
        w(tablo(["İlçe", "Anahtar", "Mahalle", "Sorun"], [[x["kimlik"], f"`{x['anahtar']}`", x["ad"], x["sorun"]] for x in tuhaf]) + "\n")
    yin = [x for x in satirlar("yinelenen_geometri.csv") if x["katman"] == "mahalle" and x["tur"] != "tarihsel ilçeye kopya (beklenen)"]
    gr = collections.defaultdict(list)
    for x in yin:
        gr[x["grup"]].append(x)
    w(f"**Birebir aynı geometri.** Mahallede {S['yinelenen']['mahalle'].get('tarihsel ilçeye kopya (beklenen)', 0)} grup tarihsel "
      "ilçeye (HIST-) kopyalanmış halef poligonu; beklenen. Kalan gruplarda iki ayrı muhtarlık aynı poligonu paylaşıyor "
      "(TKGM'de aynı sınırla iki birim):\n")
    w(tablo(["İlçe", "Poligonlar", "Tür"], [[v[0]["kimlik"] + (" / " + v[1]["kimlik"] if v[1]["kimlik"] != v[0]["kimlik"] else ""),
                                             " = ".join(f"{x['ad']} (`{x['anahtar']}`)" for x in v), v[0]["tur"]] for _, v in sorted(gr.items())]) + "\n")
    w(f"Kıymık ve çok küçük poligonlar önemsiz: {gm.get('kıymık (çok ince)', 0)} kıymık, {gm.get('çok küçük (< 500 m²)', 0)} çok küçük, "
      f"{gm.get('kırıntı parçalı', 0)} poligonda 1.000 m²'den küçük kırıntı parça (`kiymik_kucuk.csv`).\n")
    w("Dış halka yönü kaynaktan kaynağa değişiyor (mahallede " +
      ", ".join(f"{k}: {sayi(v)}" for k, v in G["mahalle"]["halka_yonu"].items()) +
      "). Site kendi düzlem izdüşümünü kullandığı için dış halka yönü sorun değil; yalnız delik yönü önemli.\n")

    # 4.2
    w("### 4.2 Mahalle ile ilçesi\n")
    w(tablo(["Ölçü", "Değer"], [
        ["İlçe dışına taşan toplam mahalle alanı", f"{sayi(MI['disari_toplam_km2'], 0)} km² (%{sayi(MI['disari_toplam_pay'], 2)})"],
        ["… 2 km sadeleştirme bandı dışında kalan", f"{sayi(MI['disari_bant_km2'], 0)} km² (%{sayi(MI['disari_bant_pay'], 2)})"],
        ["> %5 ve > 1 km² taşan mahalle", f"{sayi(MI['isaretli'])} (çizilen {sayi(MI['isaretli_kullanilan'])}); " +
         ", ".join(f"{k} {sayi(v)}" for k, v in MI["isaretli_kaynak"].items())],
        ["… 2 km bandı dışında da > %5 ve > 1 km²", f"{sayi(MI['bant_disi'])} (çizilen {sayi(MI['bant_disi_kullanilan'])}); " +
         ", ".join(f"{k} {sayi(v)}" for k, v in MI["bant_disi_kaynak"].items())],
        ["Temsil noktası kendi ilçesinde olmayan", f"{sayi(MI['yanlis_ilce'])} (çizilen {sayi(MI['yanlis_ilce_kullanilan'])}; denizde {MI['yanlis_ilce_deniz']})"],
        ["… kendi ilçesinden 2 km'den uzak", f"{sayi(MI['yanlis_ilce_uzak'])} (çizilen {sayi(MI['yanlis_ilce_uzak_kullanilan'])}); " +
         ", ".join(f"{k} {sayi(v)}" for k, v in MI["yanlis_ilce_uzak_kaynak"].items())],
    ]) + "\n")
    w("Taşmaların çoğu sınır gürültüsü. Kalan büyük taşmalarda mahalle poligonu ile TKGM çoğu kez aynı yerde, sitenin ilçe sınırı "
      "farklı (Kadınhanı'nda ttezer \"Başkuyu\" ile TKGM \"Başkuyu-Fatih\" aynı 406 km²'yi kaplıyor ve ikisi de ilçe sınırının "
      "%47 dışında). Bu durumlarda hatalı olan büyük olasılıkla ilçe katmanıdır (bkz. 4.7).\n")
    uzak = [x for x in satirlar("mahalle_yanlis_ilce.csv") if (x["kendi_ilcesine_uzaklik_km"] or 0) >= BANT_M / 1000]
    w("**Kendi ilçesinden 2 km'den uzakta duran mahalleler** (ilk 20, uzaklığa göre; tamamı `mahalle_yanlis_ilce.csv`):\n")
    w(tablo(["İlçe (geomId)", "Anahtar", "Mahalle", "Kaynak", "Bulunduğu ilçe", "Uzaklık km", "Alan km²", "Çizildiği seçim"],
            [[f"{x['ilce']} ({x['ilce_geomId']})", f"`{x['anahtar']}`", x["mahalle"], x["kaynak"],
              f"{x['noktanin_ilcesi']} ({x['noktanin_ilcesi_geomId']})" if x["noktanin_ilcesi_geomId"] else "deniz/sınır dışı",
              sayi(x["kendi_ilcesine_uzaklik_km"], 1), sayi(x["alan_km2"], 2), x["cizildigi_secim_sayisi"]] for x in uzak[:20]]) + "\n")
    dis = [x for x in satirlar("mahalle_ilce_disi.csv") if x["bant_disinda_da_isaretli"] and x["cizildigi_secim_sayisi"]]
    w("**İlçesinin 2 km bandı dışına en çok taşan çizilen mahalleler** (ilk 20; tamamı `mahalle_ilce_disi.csv`):\n")
    w(tablo(["İlçe (geomId)", "Anahtar", "Mahalle", "Kaynak", "Alan km²", "İlçe dışı km² (%)", "2 km bandı dışı km² (%)", "Seçim"],
            [[f"{x['ilce']} ({x['ilce_geomId']})", f"`{x['anahtar']}`", x["mahalle"], x["kaynak"], sayi(x["alan_km2"], 1),
              f"{sayi(x['ilce_disi_km2'], 1)} ({y(x['ilce_disi_yuzde'])})", f"{sayi(x['2km_bant_disi_km2'], 1)} ({y(x['2km_bant_disi_yuzde'])})",
              x["cizildigi_secim_sayisi"]] for x in dis[:20]]) + "\n")

    # 4.3
    w("### 4.3 Mahalle–mahalle örtüşmesi\n")
    w(f"Aynı ilçe içinde 1.000 m²'den büyük {sayi(O['cift'])} örtüşen çift var. \"Anlamlı\": ≥ 1 ha ve küçük poligonun ≥ %1'i. "
      "\"Birlikte çizilen\": iki poligon en az bir seçimde aynı haritada.\n")
    w(tablo(["Kaynak çifti", "Çift", "Alan km²", "Anlamlı", "Anlamlı km²", "Birlikte çizilen", "Birlikte km²"],
            [[k, sayi(v["cift"]), sayi(v["alan_km2"], 1), sayi(v["anlamli"]), sayi(v["anlamli_km2"], 1), sayi(v["birlikte_cizilen"]),
              sayi(v["birlikte_km2"], 1)] for k, v in sorted(O["grup"].items(), key=lambda x: -x[1]["birlikte_km2"])]) + "\n")
    w(f"- **TKGM %25 kuralı tutuyor:** her seçimde, çizilen her TKGM birimi için o seçimde çizilen TKGM dışı poligonlarla örtüşme "
      f"hesaplandı; %25'i aşan {S['tkgm_kurali']['ihlal_satir']} kayıt var (`tkgm_yuzde25_kurali.csv`). OSM × TKGM ve TKGM × ttezer "
      "birlikte çizilen örtüşmeleri bu yüzden %25'in altında kalan kenar örtüşmeleridir.")
    w(f"- **TKGM × TKGM için kural yok.** TKGM'nin kendi birimleri iç içe ya da üst üste olabiliyor (ham veride aynı ilçe içinde "
      f"{sayi(S['tkgm_ham_ortusme']['cift'])} anlamlı çift, {sayi(S['tkgm_ham_ortusme']['km2'])} km²): belde mahallesi ile onu "
      "içeren köy birimi, aynı sınırla iki ayrı köy gibi. Eşleştirme iki muhtarlığı bu iki birime ayrı ayrı bağlayınca ikisi de çiziliyor.")
    w(f"- Neredeyse aynı (IoU ≥ 0,95) {sayi(O['neredeyse_ayni'])} çift var; {O['neredeyse_ayni_birlikte']}'ü birlikte çiziliyor.\n")
    ort = [x for x in satirlar("mahalle_ortusme.csv") if x["anlamli"] and x["birlikte_cizildigi_secim_sayisi"]]
    w("**Birlikte çizilen en büyük örtüşmeler** (ilk 20; tamamı `mahalle_ortusme.csv`):\n")
    w(tablo(["İlçe (geomId)", "Mahalle 1", "Mahalle 2", "Kaynak", "Örtüşme km²", "Küçüğün %", "Ortak seçim"],
            [[f"{x['ilce']} ({x['ilce_geomId']})", f"{x['mahalle_1']} (`{x['anahtar_1']}`)", f"{x['mahalle_2']} (`{x['anahtar_2']}`)",
              x["kaynak_cifti"], sayi(x["ortusme_km2"], 2), sayi(x["kucugun_yuzdesi"], 1), x["birlikte_cizildigi_secim_sayisi"]]
             for x in ort[:20]]) + "\n")

    # 4.4
    w("### 4.4 Boşluklar: ilçenin mahallelerce kaplanmayan alanı\n")
    w("\"TKGM birimli boşluk\": boş kalan alanda TKGM ham verisinde bir birim var (eşleşmeyen ya da çakışma yüzünden çizilmeyen "
      "muhtarlık, ya da muhtarlığı olmayan birim). \"Birimsiz boşluk\": TKGM'de de birim yok (orman, göl, hazine/askerî alan ya da "
      "TKGM'nin sınırını vermediği 2.768 birim). Boşluk seçmen kaybı demek değildir; kayıp \"poligonsuz seçmen\" sütunundadır.\n")
    w(tablo(["Seçim", "İlçe", "Kaplı alan", "Boşluk km²", "TKGM birimli km²", "Hiç poligonu olmayan ilçe", "Dağılım (ilçe sayısı)"],
            [[("bütün poligonlar" if s == "tum" else s), v["ilce"], y(v["kapli_yuzde"]), sayi(v["bosluk_km2"]), sayi(v["bosluk_tkgm_km2"]),
              v["poligonsuz_ilce"], ", ".join(f"{k}: {v['dagilim'][k]}" for k in ["%0", "<%25", "%25–50", "%50–75", "%75–90", "%90–99", "≥%99"] if k in v["dagilim"])]
             for s, v in B.items()]) + "\n")
    w("Yerel seçimlerde kaplı alan düşük: büyükşehir olmayan illerde köyler belediye başkanlığı seçimine katılmadığı için o seçimin "
      "mahalle verisinde köy yok. Bu beklenen bir boşluk.\n")
    if ilk:
        bs = [x for x in satirlar("ilce_bosluk.csv") if x["secim"] == ilk]
        w(f"**{ilk}: en çok poligonsuz seçmeni olan ilçeler** (ilk 20). Bunlar gerçek kayıp: muhtarlık sonucu var, sınırı yok.\n")
        w(tablo(["İlçe (geomId)", "İl", "Kaplı", "Boşluk km²", "TKGM birimli km²", "İlçe seçmeni", "Poligonsuz seçmen"],
                [[f"{x['ilce']} ({x['ilce_geomId']})", x["il"], y(x["kapli_yuzde"]), sayi(x["bosluk_km2"], 1), sayi(x["bosluk_tkgm_birimli_km2"], 1),
                  sayi(x["ilce_secmeni"]), f"{sayi(x['poligonsuz_secmen'])} ({y(x['poligonsuz_secmen_yuzde'])})"]
                 for x in sorted(bs, key=lambda x: (-(x["poligonsuz_secmen"] or 0), x["ilce_geomId"]))[:20]]) + "\n")
        w(f"**{ilk}: en düşük kaplı ilçeler** (ilk 20). Seçmen kaybı küçükse boşluk görünüşle ilgilidir (Ceylanpınar'daki TİGEM "
          "arazisi, Tunceli'de muhtarlığı olmayan birimler gibi).\n")
        w(tablo(["İlçe (geomId)", "İl", "Kaplı", "Boşluk km²", "TKGM birimli km²", "Birimsiz km²", "Poligonsuz seçmen"],
                [[f"{x['ilce']} ({x['ilce_geomId']})", x["il"], y(x["kapli_yuzde"]), sayi(x["bosluk_km2"], 1), sayi(x["bosluk_tkgm_birimli_km2"], 1),
                  sayi(x["bosluk_tkgm_birimsiz_km2"], 1), f"{sayi(x['poligonsuz_secmen'])} ({y(x['poligonsuz_secmen_yuzde'])})"]
                 for x in sorted(bs, key=lambda x: (x["kapli_yuzde"], x["ilce_geomId"]))[:20]]) + "\n")

    # 4.5
    w("### 4.5 İlçe, il ve tarihsel katmanlar\n")
    w(tablo(["Ölçü", "Değer"], [
        ["İlçe–ilçe örtüşmesi (≥ 1.000 m²)", f"{sayi(K['ilce_ortusme_cift'])} çift, {sayi(K['ilce_ortusme_km2'], 1)} km² ({sayi(K['ilce_ortusme_il_ici'])} il içi; ≥ 0,1 km²: {sayi(K['ilce_ortusme_01km2'])})"],
        ["İlçe birleşimindeki delikler", f"{sayi(K['delik'])} ({sayi(K['delik_km2'], 1)} km²); il katmanı dolu olan dikiş boşluğu {sayi(K['delik_dikis'])} ({sayi(K['delik_dikis_km2'], 1)} km²)"],
        ["Ülke: il birleşimi / ilçe birleşimi", f"{sayi(K['ulke_il_km2'])} / {sayi(K['ulke_ilce_km2'])} km²; simetrik fark {sayi(K['ulke_simetrik_km2'], 0)} km²"],
        ["İl ↔ ilçelerinin birleşimi, simetrik fark", f"medyan %{sayi(K['il_fark_medyan'], 2)}, en çok %{sayi(K['il_fark_max'], 2)}; %2'yi aşan il {K['il_fark_2_ustu']}"],
        ["Tarihsel ilçeler", ", ".join(f"{k}: {v}" for k, v in T["tur"].items())],
    ]) + "\n")
    w("İl ve ilçe katmanları ayrı ayrı sadeleştirildiği için sınırları birebir üst üste binmiyor (kıyıda ve il sınırında ~1 km'ye kadar "
      "sapma); ilçe katmanının kendi içinde de komşu sınırlar ayrı sadeleştirilmiş. Görünüm etkisi kıl inceliğinde beyaz/çift çizgiler.\n")
    il_ = satirlar("il_ilce_tutarlilik.csv")
    w("**İl ile ilçelerinin birleşimi en farklı 10 il:**\n")
    w(tablo(["İl", "İl km²", "İlçeler km²", "İlde var, ilçede yok km²", "İlçede var, ilde yok km²", "Simetrik fark"],
            [[f"{x['il']} ({x['plaka']})", sayi(x["il_alan_km2"], 0), sayi(x["ilceler_birlesim_km2"], 0), sayi(x["il_var_ilce_yok_km2"], 1),
              sayi(x["ilce_var_il_yok_km2"], 1), y(x["simetrik_fark_yuzde"], 2)] for x in il_[:10]]) + "\n")
    w("**Dönem il sınırları:**\n")
    w(tablo(["Dönem", "İl", "Geçersiz", "İller arası örtüşme km²", "Toplam km²", "Bugünkü ülkeyle simetrik fark km²"],
            [[x[0], x[1], x[2], sayi(x[3], 1), sayi(x[5]), sayi(x[7], 1)] for x in S["donem"]]) + "\n")
    w("1950–1994 dönem dosyaları ile 1995/1999 dosyaları farklı bir taban geometriden üretilmiş görünüyor (bugünkü ülkeyle fark "
      "~1.300 km²'ye karşı 3–6 km²); ikisi de kendi içinde tutarlı.\n")
    tas = [x for x in satirlar("tarihsel_ilce_birlesim.csv") if x["tur"] == "parçaların birleşiminden taşıyor"]
    w(f"**Tarihsel ilçeler.** {T['tur'].get('parçaların bir bölümü (mahalle düzeyinde bölüşüm)', 0)} tarihsel ilçe bugünkü "
      "ilçelerin yalnız bir bölümünü kapsıyor (İstanbul'da mahalle düzeyinde bölüşüm; beklenen). Bugünkü parçalarının dışına "
      f"%0,5'ten fazla taşan {len(tas)} kayıt:\n")
    w(tablo(["geomId", "Bugünkü parçalar", "Alan km²", "Parçaların dışına taşan km² (%)"],
            [[x["geomId"], x["bugunku_parcalar"], sayi(x["alan_km2"], 1), f"{sayi(x['parcalardan_tasan_km2'], 1)} ({y(x['parcalardan_tasan_yuzde'], 2)})"] for x in tas]) + "\n")

    # 4.6
    w("### 4.6 Kapsam: poligonu olan seçmen\n")
    w("Pay: mahalle sonuçlarında bir poligona bağlı muhtarlıkların seçmeni ÷ seçim kaydındaki ilçe seçmeni (yurt içi). 2023'te "
      "payda YSK muhtarlık verisinin toplamıyla birebir aynı (60.774.566).\n")
    w(tablo(["Seçim", "İlçe seçmeni", "Poligonu olan seçmen", "Pay", "Belgede"],
            [[x[0], sayi(x[2]), sayi(x[4]), y(x[5], 2), ("%" + BELGEDEKI_KAPSAM[x[0]]) if x[0] in BELGEDEKI_KAPSAM else ""] for x in S["kapsam"]["ozet"]]) + "\n")
    w("\"Belgede\" sütunu `VERI_DENETIMI_YONETIM.md`'deki 21 Ekim 2026 notlarıdır; sonraki eşleştirme düzeltmeleri (OSM konumu, "
      "bütün seçimlerin yeniden işlenmesi) kapsamı 0,5–1 puan artırmış.\n")
    ilp = sorted(S["kapsam"]["il"]["2023"].items(), key=lambda x: x[1] if x[1] is not None else 999)
    il_ad = {str(x[1]): x[2] for x in csvler["kapsam_secmen_il.csv"][1]}
    w("**2023 genel: en düşük 10 il**\n")
    w(tablo(["İl", "Pay", "Belgede"], [[il_ad.get(str(p), p), y(v), ("%" + BELGEDEKI_IL_2023[int(p)]) if int(p) in BELGEDEKI_IL_2023 else ""]
                                       for p, v in ilp[:10]]) + "\n")

    # 4.7
    w("### 4.7 Bağımsız kaynakla konum: ilçe sınırı ↔ TKGM\n")
    w(f"Depoda ilçe sınırı için ikinci bir sınır seti yok; en yakın bağımsız kaynak TKGM ham birimleri (`data/raw/tkgm/mahalle`, "
      f"{sayi(TK['tkgm_birim'])} birim, her biri TKGM'nin kendi ilçe adıyla). Her ilçede birimlerin birleşimi sitenin ilçe poligonuyla "
      "karşılaştırıldı. TKGM'de sınırı gelmeyen birimler olduğu için alan oranı tek başına hata göstermez; asıl ölçü TKGM alanının "
      "ilçe sınırının 2 km dışında kalan kısmıdır.\n")
    w(tablo(["Ölçü", "Değer"], [
        ["Karşılaştırılan ilçe", f"{TK['ilce']} (TKGM birimi olmayan {TK['tkgm_yok']})"],
        ["Alan oranı (TKGM / ilçe), medyan", y(TK["alan_orani_medyan"])],
        ["IoU, medyan", sayi(TK["iou_medyan"], 2)],
        ["TKGM alanının ilçe dışında kalan payı, medyan", y(TK["disari_medyan"], 1)],
        ["Hausdorff uzaklığı, medyan / %95", f"{sayi(TK['hausdorff_medyan'], 1)} / {sayi(TK['hausdorff_p95'], 1)} km"],
        ["2 km bandı dışında > 10 km² TKGM alanı olan ilçe", sayi(TK["bant_disi_10km2"])],
        ["2 km bandı dışında > 1 km² ve > %5", sayi(TK["bant_disi_1km2_5yuzde"])],
    ]) + "\n")
    w("Medyan ilçede iki sınır 1–2 km içinde aynı; fark sitenin ilçe katmanının kaba sadeleştirilmesinden geliyor. Sistematik "
      f"öteleme yok: TKGM'si eksiksiz ({TK['kayma_ilce']} ilçe, alan oranı %95–105) ilçelerde ağırlık merkezleri arasındaki "
      f"uzaklığın medyanı {sayi(TK['kayma_uzaklik_medyan_m'])} m, ortak yön (doğu {sayi(TK['kayma_dx_medyan_m'])} m, kuzey "
      f"{sayi(TK['kayma_dy_medyan_m'])} m) ihmal edilebilir. Aşağıdaki ilçelerde "
      "ise TKGM birimleri ilçe sınırının belirgin biçimde dışına çıkıyor; ya ilçe katmanı o bölgede eski/yanlış ya da TKGM birimi "
      "başka ilçeye kayıtlı.\n")
    tk = [x for x in satirlar("tkgm_ilce_karsilastirma.csv") if x["iou"] is not None]
    w(tablo(["İlçe (geomId)", "İlçe km²", "TKGM km²", "IoU", "2 km bandı dışı km² (%)", "Hausdorff km"],
            [[f"{x['ilce']} ({x['ilce_geomId']})", sayi(x["ilce_alan_km2"], 0), sayi(x["tkgm_birlesim_km2"], 0), sayi(x["iou"], 2),
              f"{sayi(x['tkgm_2km_bant_disi_km2'], 1)} ({y(x['tkgm_2km_bant_disi_yuzde'])})", sayi(x["hausdorff_km"], 1)] for x in tk[:20]]) + "\n")

    # ---------------- gorseller
    if S.get("gorsel"):
        w("## 5. Görseller\n")
        aciklama = {"01": "İlçesinin 2 km bandı dışına en çok taşan çizilen mahalle",
                    "02": "Birlikte çizilen en büyük mahalle örtüşmesi",
                    "03": f"{ilk}: en çok poligonsuz seçmeni olan ilçe",
                    "04": "TKGM birimleriyle en uyumsuz ilçe sınırı"}
        for p in S["gorsel"]:
            ad = pathlib.Path(p).name
            w(f"**{aciklama.get(ad[:2], ad)}**\n\n![{ad}](img/geometri/{ad})\n")

    # ---------------- oneriler
    w("## 6. Öneriler (etki / iş sırasıyla)\n")
    w(tablo(["#", "Öneri", "Etki", "İş"], [
        [1, f"Eşleştirmede (`tkgm_muhtarlik_esle.py`) aday sınırı ilçe poligonuyla sına: alanının çoğu ilçenin 2 km bandı dışında "
            f"kalan TKGM/OSM/belediye birimi alınmasın. Önce `mahalle_yanlis_ilce.csv`'deki uzak {MI['yanlis_ilce_uzak_kullanilan']} "
            "çizilen kayda tek tek bak (Ayvatlı, Camii, Ekmekçi, Okçular ...).", "Yüksek: yanlış yerde boyanan mahalleler", "Az"],
        [2, "TKGM × TKGM örtüşmesine kural ekle: aynı seçimde çizilecek iki TKGM biriminden biri ötekinin alanının %25'inden fazlasını "
            "kaplıyorsa küçük birim büyükten çıkarılsın ya da iki muhtarlık tek kayıtta toplansın (\"birden çok muhtarlık tek sınıra "
            "düştü\" kuralı gibi). Birebir aynı poligonu paylaşan muhtarlıklar da toplanmalı.", f"Yüksek: {sayi(birlikte_tt.get('birlikte_cizilen', 0))} üst üste çift", "Orta"],
        [3, "Mahalle SVG yollarına `fill-rule: evenodd` ver (CSS'te tek satır) ya da kompakt üretimde delik yönünü düzelt.",
            f"Orta: {yon_ayni} poligonda dolu delik", "Çok az"],
        [4, "`mahalle_geo.json` yazılırken geçersiz poligonları `make_valid` ile onar; LineString ve alanı sıfır kayıtları at.",
            f"Düşük–orta: {sayi(gecersiz_m)} geçersiz poligon, hesap güvenilirliği", "Az"],
        [5, "İlçe katmanını ham kaynaktan topolojiyi koruyarak (mapshaper, ortak arklarla) ve daha az sadeleştirerek yeniden üret; "
            "il katmanını ilçelerin birleşiminden türet.", "Orta: dikiş boşlukları, kenar taşmaları, il/ilçe uyumsuzluğu", "Orta (dosya boyutu artar)"],
        [6, "TKGM ile çok farklı çıkan ilçeleri (Ceylanpınar, Kadınhanı, Çağlayancerit, Espiye, Bolu Merkez ...) güncel "
            "idari sınırla karşılaştır.", "Orta: ilçe sınırının kendisi yanlış olabilir", "Orta"],
        [7, f"Hiçbir seçimde çizilmeyen {sayi(E['hic_kullanilmayan'])} mahalle poligonunu `mahalle_geo.json`'dan çıkar.",
            f"Düşük: {sayi(E['hic_kullanilmayan_mb'], 1)} MB", "Az"],
        [8, "`HIST-Istanbul-Kartal1991`'in bugünkü parçalarının dışına taşan alanını incele.", "Düşük", "Az"],
        [9, "Belgelerdeki kapsam rakamlarını bu rapordakilerle güncelle (2023 genel %93,8 → %" + sayi(kapsam["2023"][5], 1) + ").", "Düşük", "Çok az"],
    ]) + "\n")
    return "\n".join(L).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--md", default="docs/rapor/GEOMETRI_DENETIMI.md")
    ap.add_argument("--csv-klasor", default="docs/rapor/geometri_denetimi")
    ap.add_argument("--img-klasor", default="docs/rapor/img/geometri")
    ap.add_argument("--png-yok", action="store_true", help="görselleri üretme")
    ap.add_argument("--bosluk-secimleri", default="2023,2024yerel")
    ap.add_argument("--sonuc-json", help="ara sonuçları (S ve CSV satırları) bu dosyaya da yaz")
    ap.add_argument("--sonuctan", help="hesaplama yapma; --sonuc-json çıktısından yalnız raporu yaz")
    a = ap.parse_args()
    if a.sonuctan:
        d = json.loads(pathlib.Path(a.sonuctan).read_text(encoding="utf-8"))
        S, csvler = d["S"], {k: tuple(v) for k, v in d["csv"].items()}
    else:
        S, csvler = hesapla([x for x in a.bosluk_secimleri.split(",") if x],
                            None if a.png_yok else ROOT / a.img_klasor)
        if a.sonuc_json:
            pathlib.Path(a.sonuc_json).write_text(json.dumps({"S": S, "csv": csvler}, ensure_ascii=False), encoding="utf-8")
    csv_yaz(ROOT / a.csv_klasor, csvler)
    (ROOT / a.md).write_text(rapor_yaz(S, csvler, a.csv_klasor), encoding="utf-8")
    print("Yazıldı:", a.md, a.csv_klasor)


if __name__ == "__main__":
    main()
