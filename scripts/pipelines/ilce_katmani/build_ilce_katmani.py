"""
Guncel il/ilce katmanini (geo/normalized/turkiye_ilce_sinirlari.geojson, turkiye_il_sinirlari.geojson)
ham kaynaktan, topolojiyi koruyarak yeniden uretir (2026-11-01).

Kaynaklar
  - HDX COD-AB-TUR (OCHA; CC BY-IGO), ttezer/turkiye-harita-verisi deposundaki pinlenmis kopyasi
    (commit 83eeb7a1, dist/geojson/districts.geojson, 973 ilce, 663.098 nokta; kimlikler TR-D-<plaka>-<sira>).
    Ham dosya depoda yok (buyuk); --ham ile yolu verilir, sha256 asagidaki HAM_SHA ile sinanir.
  - OpenStreetMap ilce sinirlari (admin_level=6; data/raw/osm/ilce/, ODbL): TKGM birimleriyle en az HDX
    kadar uyumlu olan ilcelerde. Hangi ilcenin OSM'den alindigi geo/normalized/ilce_duzeltme.json'da (kural
    ve olculer: ilce_duzeltme_sec.py).
  - Istanbul (plaka 34) ilceleri: mevcut dosyadaki geometri AYNEN korunur. Tarihsel Istanbul katmanlari
    (HIST-Istanbul-*, ortusmeleri_temizle.py) bu sinirlara gore temizlendi; uretim betikleri mahalle
    verisindeki son degisikliklerle calismadigi icin (prepare_istanbul_historical_assignments.py) yeniden
    uretilmedi. Komsu Kocaeli/Tekirdag ilceleri ortak siniri Istanbul'dan alir.

Yontem
  1. Aday poligonlar: her ilce icin HDX (ya da OSM duzeltmesi, ya da korunan Istanbul).
  2. Duzlemsel bolumleme: butun aday ve HDX sinirlari dugumlenir (union_all), yuzlere ayrilir (polygonize). Yuz
     tek adayin icindeyse ve HDX de ayni ilceye veriyorsa onun; Istanbul adayi her zaman once gelir. Kaynaklar
     yuzu farkli ilcelere veriyorsa (iki aday, ya da OSM adayi ile HDX sahibi) hakem TKGM'dir:
     yuzun en az yarisi bir adayin TKGM birimleriyle kapliysa (ve otekinden 0,25 fazla) o aday; degilse
     oncelik (HDX'te kalan, OSM'nin TKGM ile daha kotu oldugu ilce 4 > OSM 3 > eslesmesiz HDX 1;
     ilce_duzeltme_sec.py). Hicbir adayin kapsamadigi yuz ayni kuralla TKGM'ye, sonra HDX sahibine (o alani
     OSM ile birakmamissa), sonra en uzun ortak sinirli komsuya, komsusu yoksa (ada) HDX sahibine verilir.
     Ilceler arasinda bosluk/ortusme olmaz.
     TKGM yalniz hakemdir (lisansi acik degil): sinir cizgileri HDX ya da OSM'den gelir.
  3. Ortak yay sadelestirme (TopoJSON gibi): bolumlemenin sinir aglari yaylara ayrilir (line_merge), her yay
     uclari sabit Douglas-Peucker ile TOLERANS derece (~100 m) sadelestirilir; Istanbul ilcelerine degen yaylar
     sadelestirilmez. Kucuk halkalar kaybolacaksa sadelestirilmez. Yaylar 4 ondalik basamaga yuvarlanir,
     yeniden dugumlenir, yuzler tam cozunurluklu bolumlemedeki sahibine verilir ve ilce ilce birlestirilir.
     Komsu ilceler ayni yayi paylastigi icin dikis boslugu ya da ortusme olmaz.
  4. Il katmani = ilcelerin il il birlesimi (il/ilce sinirlari birebir ayni).
  Ozellikler degismez: ilce {id, plaka}, il {plaka}; sira mevcut dosyalardaki gibi.

Kullanim (repo kokunden):
  python3 scripts/pipelines/ilce_katmani/build_ilce_katmani.py --ham <districts.geojson>
"""
import argparse
import collections
import hashlib
import json
import pathlib
import time

import numpy as np
import shapely
from shapely.geometry import mapping, shape
from shapely.strtree import STRtree
from shapely.validation import make_valid

ROOT = pathlib.Path(__file__).resolve().parents[3]
GEO = ROOT / "geo" / "normalized"
ILCE = GEO / "turkiye_ilce_sinirlari.geojson"
IL = GEO / "turkiye_il_sinirlari.geojson"
DUZELTME = GEO / "ilce_duzeltme.json"
OSM_ILCE = ROOT / "data" / "raw" / "osm" / "ilce"
TKGM = ROOT / "data" / "raw" / "tkgm" / "mahalle"
HAM_SHA = "16fb6b98e6ce800b43334326a7d737d172beb1c2fecb4dca71a61c5d2af067ad"   # districts.geojson, ttezer 83eeb7a1
KORUNAN_IL = {34}
TOLERANS = 0.001      # derece; ~110 m (enlem), ~85 m (boylam)
ONDALIK = 4


def T(t0):
    return f"{time.time() - t0:5.0f} sn"


def poligonal(g):
    if g is None or g.is_empty:
        return shapely.Polygon()
    if not g.is_valid:
        g = make_valid(g)
    parca = [p for p in shapely.get_parts(shapely.get_parts(g)) if p.geom_type == "Polygon" and p.area > 0]
    return shapely.union_all(parca) if parca else shapely.Polygon()


def oku(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def kapsama(y, t):
    """y yuzunun t (TKGM birlesimi) ile kaplanan payi."""
    if t is None or not t.intersects(y):
        return 0.0
    return t.intersection(y).area / y.area


def bolumle(adaylar, oncelik, ulke, hdx, korunan, tkgm):
    """adaylar: {id: poligon}; oncelik: {id: sayi}; ulke: kapsanacak alan; hdx: {id: HDX poligonu};
    korunan: Istanbul kimlikleri; tkgm: {id: TKGM birimlerinin birlesimi} (hakem). Donus: ({id: poligon}, sayac)."""
    ids = sorted(adaylar)
    sira = {i: n for n, i in enumerate(ids)}
    sinir = shapely.union_all([adaylar[i].boundary for i in ids] + [hdx[i].boundary for i in sorted(hdx)] + [ulke.boundary])
    yuzler = [y for y in shapely.get_parts(shapely.polygonize(shapely.get_parts(sinir))) if y.area > 0]
    noktalar = [y.point_on_surface() for y in yuzler]
    shapely.prepare(ulke)
    a_list = [adaylar[i] for i in ids]
    agac = STRtree(a_list)
    h_ids = sorted(hdx)
    h_agac = STRtree([hdx[i] for i in h_ids])
    t_ids = sorted(tkgm)
    t_agac = STRtree([tkgm[i] for i in t_ids])
    for g in tkgm.values():
        shapely.prepare(g)
    sayac = collections.Counter()
    sahip = [None] * len(yuzler)
    sahipsiz = []
    for k, (y, n) in enumerate(zip(yuzler, noktalar)):
        if not ulke.contains(n):
            continue
        aday = [ids[j] for j in agac.query(n, predicate="within")]
        ist = [i for i in aday if i in korunan]
        h = [h_ids[j] for j in h_agac.query(n, predicate="within") if h_ids[j] not in korunan]
        iddia = sorted(set(aday) | set(h[:1])) if aday else []
        if ist:
            sahip[k] = min(ist)
        elif len(iddia) == 1:
            sahip[k] = aday[0]
        elif aday:
            # kaynaklar ayni alani farkli ilcelere veriyor (iki aday, ya da aday ile HDX sahibi): TKGM birimleri
            # hangisinin ilcesindeyse (alanin >= yarisi ve ikinciden en az 0,25 fazla) o; TKGM karar veremiyorsa
            # adaylar arasinda oncelik
            kap = sorted(((kapsama(y, tkgm.get(i)), i) for i in iddia), reverse=True)
            if kap[0][0] >= 0.5 and kap[0][0] - kap[1][0] >= 0.25:
                sahip[k] = kap[0][1]
                sayac["cakisma: TKGM"] += 1
            else:
                sahip[k] = max(aday, key=lambda i: (oncelik[i], -sira[i]))
                sayac["cakisma: oncelik"] += 1
        else:
            sahipsiz.append(k)
    # hicbir adayin kapsamadigi yuz: TKGM birimleri bir ilcedeyse o (Istanbul haric); yoksa HDX sahibi (o alani
    # OSM ile birakmamissa); yoksa en uzun ortak sinirli komsu. Istanbul'un HDX alani olup korunan Istanbul
    # poligonlarinin disinda kalan (kiyi seridi, Istanbul ilceleri arasindaki eski bosluk) alinmaz.
    birakan = {i for i in ids if oncelik[i] == 3}
    kalan = []
    for k in sahipsiz:
        h = [h_ids[j] for j in h_agac.query(noktalar[k], predicate="within")]
        if h and h[0] in korunan:
            continue
        kap = sorted(((kapsama(yuzler[k], tkgm[t_ids[j]]), t_ids[j]) for j in t_agac.query(yuzler[k], predicate="intersects")
                      if t_ids[j] not in korunan), reverse=True)
        if kap and kap[0][0] >= 0.5 and (len(kap) == 1 or kap[0][0] - kap[1][0] >= 0.25):
            sahip[k] = kap[0][1]
            sayac["bosluk: TKGM"] += 1
        elif h and h[0] not in birakan:
            sahip[k] = h[0]
            sayac["bosluk: HDX"] += 1
        else:
            kalan.append(k)
    y_agac = STRtree(yuzler)
    for _ in range(50):
        if not kalan:
            break
        sonraki = []
        for k in kalan:
            uzun = collections.Counter()
            for j in y_agac.query(yuzler[k], predicate="intersects"):
                if j != k and sahip[j] is not None and sahip[j] not in korunan:
                    uzun[sahip[j]] += yuzler[k].boundary.intersection(yuzler[j].boundary).length
            uzun = {i: v for i, v in uzun.items() if v > 0}
            if uzun:
                sahip[k] = max(uzun, key=lambda i: (uzun[i], i))
                sayac["bosluk: komsu"] += 1
            else:
                sonraki.append(k)
        if len(sonraki) == len(kalan):
            break
        kalan = sonraki
    # komsusu olmayan (ada) ya da yalniz bosluklarla cevrili yuz: tek iddia HDX'inki; OSM'nin almadigi ada (Urla
    # Uzunada ...) HDX sahibinde kalir
    for k in kalan:
        h = [h_ids[j] for j in h_agac.query(noktalar[k], predicate="within")]
        if h and h[0] not in korunan:
            sahip[k] = h[0]
            sayac["ada: HDX"] += 1
        else:
            sayac["sahipsiz kalan"] += 1
    sonuc = collections.defaultdict(list)
    for k, s in enumerate(sahip):
        if s is not None:
            sonuc[s].append(yuzler[k])
    return {i: shapely.union_all(v) for i, v in sonuc.items()}, dict(sayac)


def yuvarla(c):
    return np.round(c, ONDALIK)


def yay_sadelestir(bolum, korunan_ids):
    """Bolumlemenin sinir agini yaylara ayirir, sadelestirir, yuvarlar; yeniden yuzlere ayirip sahiplere verir."""
    ids = sorted(bolum)
    ag = shapely.union_all([bolum[i].boundary for i in ids])
    yaylar = list(shapely.get_parts(shapely.line_merge(ag)))
    korunan_sinir = shapely.union_all([bolum[i].boundary for i in ids if i in korunan_ids]) if korunan_ids else None
    if korunan_sinir is not None:
        korunan_tampon = korunan_sinir.buffer(1e-9)
        shapely.prepare(korunan_tampon)
    yeni = []
    for y in yaylar:
        if korunan_sinir is not None and korunan_tampon.intersects(y) and korunan_tampon.contains(y):
            s = y
        else:
            s = shapely.simplify(y, TOLERANS, preserve_topology=False)
            if y.is_closed and (shapely.get_num_coordinates(s) < 4 or shapely.Polygon(s.coords).area < 0.5 * abs(shapely.Polygon(y.coords).area)):
                s = y
        yeni.append(shapely.transform(s, yuvarla))
    ag2 = shapely.union_all(yeni)
    yuzler = [y for y in shapely.get_parts(shapely.polygonize(shapely.get_parts(ag2))) if y.area > 0]
    b_list = [bolum[i] for i in ids]
    agac = STRtree(b_list)
    sahip = [None] * len(yuzler)
    for k, y in enumerate(yuzler):
        # yuz, tam cozunurluklu bolumlemede alaninin cogu hangi ilcedeyse onun (sadelestirme yuzu kaydirabilir)
        j = agac.query(y, predicate="intersects")
        if len(j):
            alan = {x: b_list[x].intersection(y).area for x in j}
            en = max(alan, key=lambda x: (alan[x], -x))
            if alan[en] > 0.5 * y.area:
                sahip[k] = ids[en]
    # kalan (sadelestirmenin actigi ince) yuzler en uzun ortak sinirli komsuya
    kalan = [k for k, s in enumerate(sahip) if s is None]
    bos = len(kalan)
    y_agac = STRtree(yuzler)
    for _ in range(20):
        if not kalan:
            break
        sonraki = []
        for k in kalan:
            uzun = collections.Counter()
            for j in y_agac.query(yuzler[k], predicate="intersects"):
                if j != k and sahip[j] is not None:
                    uzun[sahip[j]] += yuzler[k].boundary.intersection(yuzler[j].boundary).length
            uzun = {i: v for i, v in uzun.items() if v > 0}
            if uzun:
                sahip[k] = max(uzun, key=lambda i: (uzun[i], i))
            else:
                sonraki.append(k)
        kalan = sonraki
    # komsusuyla yalniz noktada degen yuzler: sadelestirmenin kiyida actigi ilmekler ya da kucuk adalar.
    # Tam cozunurluklu bolumlemeyle ortusuyorsa en cok ortustugu ilceye, hic ortusmuyorsa (ulke disi) atilir.
    atilan = 0.0
    for k in kalan:
        j = agac.query(yuzler[k], predicate="intersects")
        alan = {x: b_list[x].intersection(yuzler[k]).area for x in j}
        alan = {x: v for x, v in alan.items() if v > 0}
        if alan:
            sahip[k] = ids[max(alan, key=lambda x: (alan[x], -x))]
        else:
            atilan += yuzler[k].area
    sonuc = collections.defaultdict(list)
    for k, s in enumerate(sahip):
        if s is not None:
            sonuc[s].append(yuzler[k])
    return {i: shapely.union_all(v) for i, v in sonuc.items()}, len(yaylar), (bos, len([1 for x in sahip if x is None]), atilan)


def tkgm_birlesim(kimlikler):
    """TKGM ham birimlerinin (data/raw/tkgm/mahalle; ilcesi TKGM'nin kendi kaydindan) ilce ilce birlesimi.
    Yalniz hakem: cakisan/bosta kalan yuzun hangi ilceye ait oldugunu soyler; sinir TKGM'den cizilmez."""
    tk = collections.defaultdict(list)
    for f in sorted(TKGM.glob("[0-9][0-9].geojson")):
        for ft in oku(f)["features"]:
            g = ft["properties"].get("geomId")
            if ft.get("geometry") and g in kimlikler:
                tk[g].append(poligonal(shape(ft["geometry"])))
    return {g: shapely.union_all(v) for g, v in sorted(tk.items())}


def geojson_geom(g):
    g = shapely.transform(g, yuvarla)
    if not g.is_valid:
        g = poligonal(make_valid(g))
    g = shapely.orient_polygons(g)
    m = mapping(g)
    return {"type": m["type"], "coordinates": json.loads(json.dumps(m["coordinates"]))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ham", required=True, help="ttezer dist/geojson/districts.geojson (HDX COD-AB)")
    ap.add_argument("--duzeltme", default=str(DUZELTME))
    a = ap.parse_args()
    t0 = time.time()
    ham_bayt = pathlib.Path(a.ham).read_bytes()
    sha = hashlib.sha256(ham_bayt).hexdigest()
    if sha != HAM_SHA:
        raise SystemExit(f"ham dosyanin sha256'si beklenen degil: {sha}")
    ham = {f["properties"]["id"]: poligonal(shape(f["geometry"])) for f in json.loads(ham_bayt)["features"]}
    mevcut = oku(ILCE)["features"]
    sira = [f["properties"]["id"] for f in mevcut]
    plaka = {f["properties"]["id"]: f["properties"]["plaka"] for f in mevcut}
    if set(sira) != set(ham):
        raise SystemExit("ham ile mevcut ilce kimlikleri farkli")
    korunan_json = {f["properties"]["id"]: f["geometry"] for f in mevcut if plaka[f["properties"]["id"]] in KORUNAN_IL}
    korunan = {g: poligonal(shape(j)) for g, j in korunan_json.items()}
    duz = oku(a.duzeltme) if pathlib.Path(a.duzeltme).exists() else {"ilceler": {}}
    osm = {}
    if duz["ilceler"]:
        osm_geo = {}
        for f in sorted(OSM_ILCE.glob("[0-9][0-9].geojson")):
            for ft in oku(f)["features"]:
                osm_geo[ft["properties"]["osm_id"]] = ft["geometry"]
        for gid, d in duz["ilceler"].items():
            osm[gid] = poligonal(shape(osm_geo[d["osm_id"]]))
    hdx_once = set(duz.get("hdx_oncelikli", {}))
    adaylar, oncelik = {}, {}
    for gid in sira:
        if gid in hdx_once:
            adaylar[gid], oncelik[gid] = ham[gid], 4
        elif gid in osm:
            adaylar[gid], oncelik[gid] = osm[gid], 3
        elif gid in korunan:
            adaylar[gid], oncelik[gid] = korunan[gid], 2
        else:
            adaylar[gid], oncelik[gid] = ham[gid], 1
    ulke = shapely.union_all(list(ham.values()) + list(korunan.values()))
    print(f"{T(t0)} okundu: {len(ham)} ilce, OSM duzeltmesi {len(osm)}, korunan {len(korunan)}", flush=True)
    tkgm = tkgm_birlesim(set(sira))
    print(f"{T(t0)} TKGM hakem birlesimleri: {len(tkgm)} ilce", flush=True)
    bolum, sayac = bolumle(adaylar, oncelik, ulke, ham, set(korunan), tkgm)
    print(f"{T(t0)} bolumleme: {len(bolum)} ilce; {sayac}", flush=True)
    son, nyay, bos = yay_sadelestir(bolum, set(korunan))
    print(f"{T(t0)} sadelestirme: {nyay} yay, sahibi komsudan belirlenen ince yuz {bos[0]}, ulke disi atilan {bos[1]} yuz ({bos[2]:.2e} derece2)", flush=True)
    eksik = [g for g in sira if g not in son]
    if eksik:
        raise SystemExit(f"poligonu kalmayan ilce: {eksik}")
    # korunan Istanbul ilceleri mevcut dosyadaki geometriyle AYNEN yazilir (komsular ortak siniri ondan aldi)
    feats = [{"type": "Feature", "properties": {"id": g, "plaka": plaka[g]},
              "geometry": korunan_json[g] if g in korunan_json else geojson_geom(son[g])} for g in sira]
    il_sira = [f["properties"]["plaka"] for f in oku(IL)["features"]]
    il_g = collections.defaultdict(list)
    for g in sira:
        il_g[plaka[g]].append(shape(feats[sira.index(g)]["geometry"]))
    il_feats = [{"type": "Feature", "properties": {"plaka": p}, "geometry": geojson_geom(shapely.union_all(il_g[p]))} for p in il_sira]
    yaz = lambda p, fs: p.write_text(json.dumps({"type": "FeatureCollection", "features": fs}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    yaz(ILCE, feats)
    yaz(IL, il_feats)
    npt = sum(shapely.get_num_coordinates(shape(f["geometry"])) for f in feats)
    print(f"{T(t0)} yazildi: {ILCE.relative_to(ROOT)} ({npt} nokta, {ILCE.stat().st_size} bayt), {IL.relative_to(ROOT)} ({IL.stat().st_size} bayt)")


if __name__ == "__main__":
    main()
