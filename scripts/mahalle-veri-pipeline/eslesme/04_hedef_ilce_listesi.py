import json
import os
from pathlib import Path

WORKDIR = os.environ.get("MAHALLE_WORKDIR") or str(Path(__file__).resolve().parent.parent / ".work")
OUT = f"{WORKDIR}/osm_mahalle"

matched_ilce = json.load(open(f"{OUT}/ysk_ilce_matched.json", encoding="utf-8"))
counts = json.load(open(f"{OUT}/ilce_mahalle_counts.json", encoding="utf-8"))

targets = []
for row in matched_ilce:
    if row["geomId"] in counts:
        targets.append({
            "il_ID": row["il_ID"], "il_ADI": row["il_ADI"],
            "ilce_ID": row["ilce_ID"], "ilce_ADI": row["ilce_ADI"],
            "geomId": row["geomId"], "mahalleCount": counts[row["geomId"]],
        })

print("targets:", len(targets))
json.dump(targets, open(f"{OUT}/fetch_targets.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
