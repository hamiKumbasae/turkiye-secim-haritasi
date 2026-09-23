import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"))
from common.turkish_text import fold, fold_mahalle  # noqa: E402

WORKDIR = os.environ.get("MAHALLE_WORKDIR") or str(Path(__file__).resolve().parent.parent / ".work")
OSM = f"{WORKDIR}/osm_mahalle"
TTZ = f"{WORKDIR}/ttezer_mahalle"
ROOT = WORKDIR

def votes_to_row(osm_id, ad, geometry, v):
    gecerli = v["gecerli"] or 1
    oy = {}
    for name, n in v["major"].items():
        oy[name] = {"oy": n, "oran": round(n / gecerli * 100, 2)}
    if v["diger"] > 0:
        oy["Diğer"] = {"oy": v["diger"], "oran": round(v["diger"] / gecerli * 100, 2)}
    all_named = {**v["major"], "Diğer": v["diger"]}
    kazanan = max(all_named, key=all_named.get) if any(all_named.values()) else None
    katilim = round(v["oyKullanan"] / v["secmen"] * 100, 2) if v["secmen"] else None
    return {
        "id": osm_id, "ad": ad, "geometry": geometry,
        "secmen": v["secmen"], "sandik": None, "katilim": katilim,
        "kazanan": kazanan, "oy": oy,
    }

def build(votes_file, year_key):
    votes = json.load(open(votes_file, encoding="utf-8"))
    print(f"[{year_key}] districts with votes:", len(votes))

    ttz_orig = json.load(open(f"{TTZ}/ttezer_all.geojson", encoding="utf-8"))
    ttz_simp = json.load(open(f"{TTZ}/ttezer_simplified.geojson", encoding="utf-8"))
    ttezer_by_geomid = defaultdict(list)
    for o, s in zip(ttz_orig["features"], ttz_simp["features"]):
        p = o["properties"]
        ttezer_by_geomid[p["geomId"]].append({
            "osm_id": p["osm_id"], "fold": fold_mahalle(p["name"]), "geometry": s["geometry"],
        })

    osm_orig = json.load(open(f"{OSM}/mahalle_matched.geojson", encoding="utf-8"))
    osm_simp = json.load(open(f"{OSM}/mahalle_simplified.geojson", encoding="utf-8"))
    ilce_by_name = {}
    for row in json.load(open(f"{OSM}/ysk_ilce_matched.json", encoding="utf-8")):
        key = (fold(row["il_ADI"]), fold(row["ilce_ADI"]))
        ilce_by_name[key] = row["geomId"]
    osm_by_geomid = defaultdict(list)
    for o, s in zip(osm_orig["features"], osm_simp["features"]):
        p = o["properties"]
        key = (fold(p["il_adi"]), fold(p["ilce_adi"]))
        geomId = ilce_by_name.get(key)
        if not geomId:
            continue
        osm_by_geomid[geomId].append({
            "osm_id": p["osm_id"], "fold": fold_mahalle(p["name"]), "geometry": s["geometry"],
        })

    ttezer_geomids = set(ttezer_by_geomid.keys())
    osm_only_geomids = set(osm_by_geomid.keys()) - ttezer_geomids

    final = {}
    stats = {"ttezer_total": 0, "ttezer_matched": 0, "osm_total": 0, "osm_matched": 0}

    def process(geomids, geom_source, key):
        for geomId in geomids:
            mv_list = votes.get(geomId, [])
            osm_list = geom_source[geomId]
            by_fold = defaultdict(list)
            for m in osm_list:
                by_fold[m["fold"]].append(m)
            rows = []
            for mv in mv_list:
                stats[f"{key}_total"] += 1
                mf = fold_mahalle(mv["muhtarlik_ADI"])
                cands = by_fold.get(mf)
                if not cands:
                    continue
                stats[f"{key}_matched"] += 1
                m = cands[0]
                rows.append(votes_to_row(m["osm_id"], mv["muhtarlik_ADI"], m["geometry"], mv))
            if rows:
                final[geomId] = rows

    process(ttezer_geomids, ttezer_by_geomid, "ttezer")
    process(osm_only_geomids, osm_by_geomid, "osm")

    print(f"[{year_key}] stats:", stats)
    total_rows = sum(len(v) for v in final.values())
    print(f"[{year_key}] final districts:", len(final), "final rows:", total_rows)
    return final

if __name__ == "__main__":
    votes_file = sys.argv[1]
    year_key = sys.argv[2]
    result = build(votes_file, year_key)
    out_path = f"{ROOT}/mahalle_{year_key}.json"
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    print("wrote", out_path)
