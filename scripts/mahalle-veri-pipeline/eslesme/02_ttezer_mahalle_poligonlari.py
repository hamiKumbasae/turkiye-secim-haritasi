import json
import glob
import os
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

WORKDIR = os.environ.get("MAHALLE_WORKDIR") or str(Path(__file__).resolve().parent.parent / ".work")
DIR = f"{WORKDIR}/ttezer_mahalle"

features_by_geomid = defaultdict(list)
type_counter = Counter()
bad_files = []
total = 0
for fn in glob.glob(f"{DIR}/files/*.geojson"):
    try:
        d = json.load(open(fn, encoding="utf-8"))
    except Exception as e:
        bad_files.append((fn, str(e)))
        continue
    for f in d.get("features", []):
        p = f["properties"]
        total += 1
        type_counter[p.get("type")] += 1
        geomId = p.get("district_id")
        if not geomId or not f.get("geometry"):
            continue
        features_by_geomid[geomId].append({
            "osm_id": "t" + p["id"],  # prefix to avoid collision with OSM 'r'/'w' ids
            "name": p.get("name"),
            "geometry": f["geometry"],
        })

print("total raw features:", total)
print("type distribution:", type_counter)
print("bad files:", len(bad_files), bad_files[:5])
print("districts covered:", len(features_by_geomid))
counts = sorted((len(v) for v in features_by_geomid.values()), reverse=True)
print("top 10 district mahalle counts:", counts[:10])
print("total mahalle features with valid geomId+geometry:", sum(counts))

json.dump({k: v for k, v in features_by_geomid.items()},
          open(f"{DIR}/ttezer_by_geomid.json", "w", encoding="utf-8"), ensure_ascii=False)
