"""
YSK acikveri il/ilce listesi (998 ilce, data/raw/ysk/acikveri-il-ilce-listesi.json)
ile projenin kendi ilceler listesini (973 ilce, data/normalized/genel_secimler.json
"2023" veya yerel_secimler.json "2024yerel" - ikisi de ayni, en guncel/tam
liste) plaka+isim bazinda eslestirir. Cikti: {"<ilId>-<ilceId>": "<geomId>"}.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402


ysk = json.loads((ROOT / "data" / "raw" / "ysk" / "acikveri-il-ilce-listesi.json").read_text(encoding="utf-8"))
proj_ilceler = load_election("2023")["ilceler"]

proj_index = {}
for row in proj_ilceler:
    key = (row["plaka"], fold(row["ad"]))
    proj_index[key] = row["geomId"]

# Bilinen isim varyantlari (YSK yazimi -> proje yazimi), (plaka, YSK_normu) -> (plaka, proje_normu)
MANUAL_ALIAS = {
    (55, fold("19 MAYIS")): (55, fold("Ondokuzmayıs")),
}

matched = {}
unmatched = []
for il_id_str, info in ysk.items():
    il_id = int(il_id_str)
    for ilce in info["ilceler"]:
        ilce_norm = fold(ilce["ilce_ADI"])
        il_norm = fold(info["il_ADI"])
        key = (il_id, ilce_norm)
        key = MANUAL_ALIAS.get(key, key)
        geomId = proj_index.get(key)
        if not geomId and ilce_norm == (il_norm + " MERKEZ"):
            geomId = proj_index.get((il_id, "MERKEZ"))
        if not geomId and ilce_norm == "MERKEZ":
            # bazi YSK kayitlarinda sadece "MERKEZ" olarak geciyor (il adi onekiz)
            geomId = proj_index.get((il_id, il_norm))
        if geomId:
            matched[f"{il_id}-{ilce['ilce_ID']}"] = geomId
        else:
            unmatched.append((il_id, info["il_ADI"], ilce["ilce_ID"], ilce["ilce_ADI"]))

print(f"eslesen: {len(matched)}, eslesmeyen: {len(unmatched)}")
for u in unmatched:
    print(" ", u)

out_path = ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json"
out_path.write_text(json.dumps(matched, ensure_ascii=False, indent=1), encoding="utf-8")
print("yazildi:", out_path)
