"""
geo/historical/metro_merkez_1961_1987.json'daki buyuksehir "Merkez" ilceleri
icin (Adana, Bursa, Gaziantep, Kayseri, Konya) sentetik HIST-<Il>-Merkez
poligonlarini, bolunme kanununun DOGRUDAN haleflerinin modern poligonlarinin
birlesimi olarak uretir ve geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson
+ district_splits.json'a yazar (diger kayitlara dokunmaz, idempotent).

Yontem apply_verified_district_merges.py'deki "whole child" modeliyle ayni:
yeni bir sinir cizilmez, sadece zaten var olan modern poligonlar birlestirilir.
Haleflerin sonradan bolunmus cocuklari (orn. Seyhan'dan Cukurova) bilerek
dahil edilmez - projenin 1987-2007 verisi de onlari ayri gostermiyor; alan
eksik kapsanir, asla fazla degil.

Gereksinim: shapely (sadece gelistirme sirasinda, build.py/CI gerektirmez).
Kullanim:
  python3 scripts/pipelines/historical_geo/build_metro_merkez.py
"""
import json
import pathlib

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
GEO_NORM = ROOT / "geo" / "normalized" / "turkiye_ilce_sinirlari.geojson"
HIST_GEO = ROOT / "geo" / "historical" / "turkiye_ilce_sinirlari_hist_splits.geojson"
DISTRICT_SPLITS = ROOT / "geo" / "historical" / "district_splits.json"
CONFIG = ROOT / "geo" / "historical" / "metro_merkez_1961_1987.json"


def main():
    entries = json.loads(CONFIG.read_text(encoding="utf-8"))
    modern = {f["properties"]["id"]: f for f in json.loads(GEO_NORM.read_text(encoding="utf-8"))["features"]}
    hist = json.loads(HIST_GEO.read_text(encoding="utf-8"))
    features = {f["properties"]["id"]: f for f in hist["features"]}
    splits = json.loads(DISTRICT_SPLITS.read_text(encoding="utf-8"))

    geo_changed = splits_changed = False
    for e in entries:
        for gid in e["successorGeomIds"]:
            if gid not in modern or modern[gid]["properties"].get("plaka") != e["plaka"]:
                raise SystemExit(f"HATA: {e['syntheticId']}: {gid} modern ilce listesinde yok ya da plakasi farkli")
        geoms = [shape(modern[g]["geometry"]) for g in e["successorGeomIds"]]
        merged = unary_union([g if g.is_valid else g.buffer(0) for g in geoms])
        feat = {"type": "Feature", "properties": {"id": e["syntheticId"], "plaka": e["plaka"]}, "geometry": mapping(merged)}
        old = features.get(e["syntheticId"])
        if old is None or json.dumps(old["geometry"], sort_keys=True) != json.dumps(feat["geometry"], sort_keys=True):
            features[e["syntheticId"]] = feat
            geo_changed = True
            print("geometri:", e["syntheticId"], "=", " + ".join(e["successorNames"]))

        want = {"hideIds": sorted(e["successorGeomIds"]), "splitYear": e["splitYear"], "syntheticId": e["syntheticId"]}
        lst = splits.setdefault(str(e["plaka"]), [])
        cur = next((x for x in lst if x["syntheticId"] == e["syntheticId"]), None)
        if cur != want:
            if cur is None:
                lst.append(want)
            else:
                cur.update(want)
            splits_changed = True
            print("district_splits:", e["syntheticId"], want["hideIds"])

    if geo_changed:
        hist["features"] = sorted(features.values(), key=lambda f: f["properties"]["id"])
        HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("yazildi:", HIST_GEO)
    if splits_changed:
        DISTRICT_SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
        print("yazildi:", DISTRICT_SPLITS)
    if not (geo_changed or splits_changed):
        print("degisiklik yok")


if __name__ == "__main__":
    main()
