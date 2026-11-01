"""
HDX ilce sinirinin TKGM ile belirgin bicimde uyusmadigi ilcelerde OpenStreetMap ilce sinirinin (admin_level=6)
kullanilip kullanilmayacagini secer; sonucu geo/normalized/ilce_duzeltme.json'a ve
docs/rapor/ilce_katmani/ilce_karsilastirma.csv'ye yazar. build_ilce_katmani.py bu listeyi okur.

Iki bagimsiz kaynak: TKGM idari yapi servisinin mahalle/koy birimleri (data/raw/tkgm/mahalle; her birimin
ilcesi TKGM'nin kendi kaydindan) ve OSM ilce iliskileri (data/raw/osm/ilce). TKGM birimleri ilce siniri
vermez (bazi birimler eksik, bazilari birbiriyle ortusuyor); bu yuzden TKGM yalniz hakem olarak kullanilir,
sinirin kendisi OSM'den alinir.

Olcu: TKGM disi(K, g) = g ilcesinin TKGM birimlerinin birlesiminin, K katmanindaki g poligonunun 2 km
tamponu disinda kalan alani (km2). (geometri_denetimi.py 4.7 ile ayni.)

Kural (ilce ilce; tahmin yok, her karar iki bagimsiz kaynaga dayanir)
  1. OSM eslesmesi: g'nin HDX poligonuyla en cok ortusen OSM iliskisi (IoU >= 0,5 ya da adi ayni ve
     IoU >= 0,2); bir iliski tek ilceye. Eslesmeyen ilce HDX'te kalir (oncelik 1).
  2. TKGM disi(OSM) <= TKGM disi(HDX) + TOLERANS_KM2 ise sinir OSM'den alinir (oncelik 3): OSM, TKGM ile
     en az HDX kadar uyumlu. Ilk denemede yalniz belirgin farkli ilceler (TKGM disi(HDX) >= 10 km2 ve OSM'de
     yarisindan az) degistirildi; komsulari da degistirmek gerekti (OSM siniri komsunun HDX alanina 1 km2'den
     fazla taşiyordu) ve yayilma 973 ilcenin 773'une ulasti. Yamali bir katman yerine kural butun ilcelere
     ayni uygulanir.
  3. TKGM disi(OSM) > TKGM disi(HDX) + TOLERANS_KM2 ise HDX kalir ve ortak sinirda once gelir (oncelik 4):
     TKGM o ilcede HDX sinirini destekliyor; OSM'den alinan komsu o alani birakir.
  Istanbul (plaka 34) bu secime girmez (build_ilce_katmani.py: korunur).

Kullanim (repo kokunden): python3 scripts/pipelines/ilce_katmani/ilce_duzeltme_sec.py --ham <districts.geojson>
"""
import argparse
import collections
import csv
import difflib
import json
import pathlib
import sys
import unicodedata

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_ilce_katmani import HAM_SHA, poligonal, oku  # noqa: E402

OSM_ILCE = ROOT / "data/raw/osm/ilce"
TKGM = ROOT / "data/raw/tkgm/mahalle"
CIKTI = ROOT / "geo/normalized/ilce_duzeltme.json"
CSV = ROOT / "docs/rapor/ilce_katmani/ilce_karsilastirma.csv"
IZDUSUM = "+proj=aea +lat_0=39 +lon_0=35 +lat_1=37 +lat_2=41 +ellps=GRS80 +units=m +no_defs"
BANT_M = 2000
TOLERANS_KM2 = 1.0
KORUNAN_IL = {34}

_tr = Transformer.from_crs("EPSG:4326", IZDUSUM, always_xy=True)


def izd(g):
    return shapely.transform(g, lambda c: np.column_stack(_tr.transform(c[:, 0], c[:, 1])))


def fold(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower()
    s = unicodedata.normalize("NFKD", s.replace("ı", "i"))
    return "".join(ch for ch in s if ch.isalnum())


def main():
    import hashlib
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ham", required=True)
    a = ap.parse_args()
    b = pathlib.Path(a.ham).read_bytes()
    if hashlib.sha256(b).hexdigest() != HAM_SHA:
        raise SystemExit("ham dosyanin sha256'si beklenen degil")
    hdx = {f["properties"]["id"]: poligonal(izd(shape(f["geometry"]))) for f in json.loads(b)["features"]}
    sec = oku(ROOT / "data/normalized/elections/genel/2023.json")
    ad = {r["geomId"]: r["ad"] for r in sec["ilceler"]}
    plaka = {g: int(g.split("-")[2]) for g in hdx}

    osm, osm_ad = {}, {}
    for f in sorted(OSM_ILCE.glob("[0-9][0-9].geojson")):
        for ft in oku(f)["features"]:
            p = ft["properties"]
            if p["osm_id"] not in osm:
                osm[p["osm_id"]] = poligonal(izd(shape(ft["geometry"])))
                osm_ad[p["osm_id"]] = p.get("ad")
    o_ids = sorted(osm)
    o_agac = STRtree([osm[i] for i in o_ids])

    eslesme = {}
    for g in sorted(hdx):
        en = None
        for j in o_agac.query(hdx[g], predicate="intersects"):
            o = o_ids[j]
            iou = hdx[g].intersection(osm[o]).area / hdx[g].union(osm[o]).area
            ad_ayni = difflib.SequenceMatcher(None, fold(ad.get(g)), fold(osm_ad[o])).ratio() >= 0.8
            if (iou >= 0.5 or (ad_ayni and iou >= 0.2)) and (en is None or iou > en[1]):
                en = (o, iou, ad_ayni)
        if en:
            eslesme[g] = en
    # ayni OSM iliskisi iki ilceye eslenmesin: IoU'su buyuk olan alir
    sahip = {}
    for g, (o, iou, _) in sorted(eslesme.items(), key=lambda x: -x[1][1]):
        if o in sahip:
            del eslesme[g]
        else:
            sahip[o] = g

    tk = collections.defaultdict(list)
    for f in sorted(TKGM.glob("[0-9][0-9].geojson")):
        for ft in oku(f)["features"]:
            if ft.get("geometry") and ft["properties"].get("geomId") in hdx:
                tk[ft["properties"]["geomId"]].append(poligonal(izd(shape(ft["geometry"]))))
    tku = {g: shapely.union_all(v) for g, v in tk.items()}

    def disi(g, p):
        return tku[g].difference(p.buffer(BANT_M)).area / 1e6 if g in tku else 0.0

    olcu = {}
    for g in sorted(hdx):
        dh = disi(g, hdx[g])
        if g in eslesme:
            o = eslesme[g][0]
            do = disi(g, osm[o])
            olcu[g] = {"hdx": dh, "osm": do, "osm_id": o, "iou": eslesme[g][1],
                       "fark_km2": hdx[g].symmetric_difference(osm[o]).area / 1e6}
        else:
            olcu[g] = {"hdx": dh, "osm": None, "osm_id": None, "iou": None, "fark_km2": None}

    secilen, hdx_kalan = {}, {}
    for g in sorted(hdx):
        m = olcu[g]
        if plaka[g] in KORUNAN_IL:
            continue
        if m["osm"] is None:
            hdx_kalan[g] = "OSM eslesmesi yok"
        elif m["osm"] <= m["hdx"] + TOLERANS_KM2:
            secilen[g] = "OSM, TKGM ile en az HDX kadar uyumlu"
        else:
            hdx_kalan[g] = "OSM TKGM ile daha kotu; HDX ortak sinirda once gelir"

    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["geomId", "ad", "plaka", "osm_id", "osm_ad", "iou_hdx_osm", "hdx_osm_simetrik_fark_km2",
                    "tkgm_2km_disi_hdx_km2", "tkgm_2km_disi_osm_km2", "karar"])
        for g in sorted(hdx):
            m = olcu[g]
            karar = ("OSM: " + secilen[g]) if g in secilen else ("HDX: " + hdx_kalan[g] if g in hdx_kalan else "korunan (Istanbul)")
            w.writerow([g, ad.get(g, ""), plaka[g], m["osm_id"] or "", osm_ad.get(m["osm_id"], "") if m["osm_id"] else "",
                        "" if m["iou"] is None else round(m["iou"], 4),
                        "" if m["fark_km2"] is None else round(m["fark_km2"], 1),
                        round(m["hdx"], 1), "" if m["osm"] is None else round(m["osm"], 1), karar])
    out = {"aciklama": "OSM ilce siniriyla degistirilen ilceler (ilce_duzeltme_sec.py; kural betigin basinda). "
                       "Olculer km2: TKGM birimlerinin ilce poligonunun 2 km tamponu disinda kalan alani.",
           "ilceler": {g: {"ad": ad.get(g, ""), "osm_id": olcu[g]["osm_id"], "osm_ad": osm_ad[olcu[g]["osm_id"]],
                           "neden": secilen[g], "tkgm_2km_disi_hdx": round(olcu[g]["hdx"], 1),
                           "tkgm_2km_disi_osm": round(olcu[g]["osm"], 1), "iou_hdx_osm": round(olcu[g]["iou"], 4)}
                       for g in sorted(secilen)},
           "hdx_oncelikli": {g: {"ad": ad.get(g, ""), "osm_id": olcu[g]["osm_id"], "neden": hdx_kalan[g],
                                 "tkgm_2km_disi_hdx": round(olcu[g]["hdx"], 1), "tkgm_2km_disi_osm": round(olcu[g]["osm"], 1)}
                             for g in sorted(hdx_kalan) if olcu[g]["osm"] is not None}}
    CIKTI.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    top_h = sum(m["hdx"] for m in olcu.values())
    top_s = sum((m["osm"] if g in secilen else m["hdx"]) for g, m in olcu.items())
    print(f"OSM eslesen {len(eslesme)}/{len(hdx)}; OSM'den {len(secilen)}, HDX oncelikli "
          f"{sum(1 for g in hdx_kalan if olcu[g]['osm'] is not None)}, eslesmesiz {sum(1 for g in hdx_kalan if olcu[g]['osm'] is None)}; "
          f"TKGM 2 km disi toplam {top_h:.0f} -> {top_s:.0f} km2 (ongorulen)")


if __name__ == "__main__":
    main()
