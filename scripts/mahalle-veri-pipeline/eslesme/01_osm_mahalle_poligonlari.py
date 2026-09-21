import csv
import json

# Load the curated mahalle index (osm_id, parent_osm_id, name, ...) from osadikoglu/turkey-admin-units-osm
mahalle_rows = {}
ilce_names = {}
il_names = {}
with open("admin-tr.csv", newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        if row["level"] == "mahalle":
            mahalle_rows[row["osm_id"]] = row
        elif row["level"] == "ilce":
            ilce_names[row["osm_id"]] = row
        elif row["level"] == "il":
            il_names[row["osm_id"]] = row

print("mahalle index size:", len(mahalle_rows))

raw = json.load(open("mahalle_raw.geojson", encoding="utf-8"))
print("raw features:", len(raw["features"]))

matched = {}
for feat in raw["features"]:
    props = feat["properties"]
    if props.get("@type") != "relation":
        continue
    osm_id = "r" + str(props["@id"])
    row = mahalle_rows.get(osm_id)
    if not row:
        continue
    # some relations could theoretically appear twice (shouldn't, but be safe)
    matched[osm_id] = feat

print("matched relations:", len(matched))
missing = set(mahalle_rows) - set(matched)
print("missing (in index but no polygon found):", len(missing))

out_features = []
for osm_id, feat in matched.items():
    row = mahalle_rows[osm_id]
    ilce = ilce_names.get(row["parent_osm_id"])
    il = il_names.get(ilce["parent_osm_id"]) if ilce else None
    out_features.append({
        "type": "Feature",
        "properties": {
            "osm_id": osm_id,
            "name": row["name"],
            "alt_names": row["alt_names"],
            "ilce_adi": ilce["name"] if ilce else None,
            "il_adi": il["name"] if il else None,
        },
        "geometry": feat["geometry"],
    })

out = {"type": "FeatureCollection", "features": out_features}
with open("mahalle_matched.geojson", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print("wrote", len(out_features), "features")

# quick size report
import os
print("output size bytes:", os.path.getsize("mahalle_matched.geojson"))

# sample a few missing ones to understand why (if any)
if missing:
    sample = list(missing)[:10]
    for osm_id in sample:
        row = mahalle_rows[osm_id]
        print("MISSING:", osm_id, row["name"])
