import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from common.turkish_text import fold  # noqa: E402
WORKDIR = os.environ.get("MAHALLE_WORKDIR") or str(Path(__file__).resolve().parent.parent / ".work")
OUT = f"{WORKDIR}/osm_mahalle"

# project's authoritative ilce list (plaka, ad, geomId) from the CB 2023 2nd tur bundle
# — artik repo icinde, data/raw/legacy-preprocessed/'de snapshot'lanmis durumda
# (bkz. o klasorun PROVENANCE.md'si).
proj = json.load(open(REPO_ROOT / "data" / "raw" / "legacy-preprocessed" / "1950_2023_tam_veri_seti.json", encoding="utf-8"))
proj_ilceler = proj["secimler"]["2023cb2tur"]["ilceler"]
proj_index = {}
for row in proj_ilceler:
    key = (row["plaka"], fold(row["ad"]))
    proj_index[key] = row["geomId"]
print("project ilce count:", len(proj_ilceler), "unique keys:", len(proj_index))

# YSK numeric ilce list
ysk = json.load(open(f"{OUT}/ysk_ilceler.json", encoding="utf-8"))
print("YSK ilce count:", len(ysk))

matched = []
unmatched = []
for row in ysk:
    ilce_norm = fold(row["ilce_ADI"])
    il_norm = fold(row["il_ADI"])
    key = (row["il_ID"], ilce_norm)
    geomId = proj_index.get(key)
    if not geomId and ilce_norm == (il_norm + " MERKEZ"):
        geomId = proj_index.get((row["il_ID"], "MERKEZ"))
    if geomId:
        matched.append({**row, "geomId": geomId})
    else:
        unmatched.append(row)

print("matched:", len(matched), "unmatched:", len(unmatched))
print("--- sample unmatched (first 30) ---")
for u in unmatched[:30]:
    print(u["il_ID"], u["il_ADI"], "/", u["ilce_ADI"])

json.dump(matched, open(f"{OUT}/ysk_ilce_matched.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(unmatched, open(f"{OUT}/ysk_ilce_unmatched.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
