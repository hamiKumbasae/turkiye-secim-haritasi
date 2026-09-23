"""
fetch_yerel_v2.js ciktisini data/normalized/yerel_secimler.json'a isler.
DOGRU model: "il" kaydi buyuksehir illerde secimTuru=6 agregesi, digerlerinde
"<Il> MERKEZ" ilcesinin kendi secimTuru=2 sonucu (agrege.iller[ilId] zaten
bu ayrimi yapip dogru veriyi tasiyor - bkz. fetch_yerel_v2.js). "ilceler"
HER ilcenin kendi ayri secimTuru=2 sonucu.

Kullanim: python3 merge_yerel_v2.py <key orn 2019yerel> <v2_agrege.json>
"""
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from party_map_helper import build_auto_map, build_party_mapping  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402
from common.hist_geomid import resolve_historical_merkez  # noqa: E402

GEOMID_MAP_PATH = ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json"
_GENEL2023 = load_election("2023")
IL_ADI_BY_PLAKA = {i["plaka"]: i["ad"] for i in _GENEL2023["iller"]}
ILCE_ADI_BY_GEOMID = {i["geomId"]: i["ad"] for i in _GENEL2023["ilceler"]}

BAGIMSIZ_COL_RE = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")  # diger 3 merge script'iyle tutarli (YSK sutunlari her zaman numarali)


def build_record(ad, plaka, agg, col_to_key, major):
    oy = {}
    diger_oy = 0
    bagimsiz_oy = 0
    for col, v in agg.get("oy", {}).items():
        if not v:
            continue
        if BAGIMSIZ_COL_RE.match(col):
            bagimsiz_oy += v
            continue
        key = col_to_key.get(col)
        if key is None:
            diger_oy += v
            continue
        if key in major:
            oy.setdefault(key, {"oy": 0})
            oy[key]["oy"] += v
        else:
            diger_oy += v
    if bagimsiz_oy:
        if "Bağımsız" in major:
            oy.setdefault("Bağımsız", {"oy": 0})
            oy["Bağımsız"]["oy"] += bagimsiz_oy
        else:
            diger_oy += bagimsiz_oy
    if diger_oy:
        oy["Diğer"] = {"oy": diger_oy}

    total = sum(v["oy"] for v in oy.values())
    for k in oy:
        oy[k]["oran"] = round(oy[k]["oy"] / total * 100, 2) if total else None
    kazanan = max(oy.items(), key=lambda kv: kv[1]["oy"])[0] if oy else None

    return {
        "ad": ad,
        "gecerliOy": agg.get("gecerli", 0),
        "ilceSayisi": 0,
        "katilim": round(agg["oyKullanan"] / agg["secmen"] * 100, 2) if agg.get("secmen") else None,
        "kazanan": kazanan,
        "oy": oy,
        "plaka": plaka,
        "sandik": agg.get("sandikSayisi", 0),
        "secmen": agg.get("secmen", 0),
        "toplamVekil": 0,
        "vekil": {},
    }


def main():
    key = sys.argv[1]
    agrege = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    extra_alias = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) > 3 else {}
    geomid_map = json.loads(GEOMID_MAP_PATH.read_text(encoding="utf-8"))

    secim = load_election(key)
    major = set(secim["majorPartiler"])

    existing_keys = set()
    for il in secim["iller"]:
        existing_keys.update(il["oy"].keys())
    existing_keys.discard("Bağımsız")
    existing_keys.discard("Diğer")

    col_to_key = build_party_mapping(agrege["colToName"], existing_keys, extra_alias)

    old_ilce_sayisi = {i["plaka"]: i["ilceSayisi"] for i in secim["iller"]}

    new_iller = []
    kind_summary = {}
    for il_id_str, agg in agrege["iller"].items():
        plaka = int(il_id_str)
        ad = IL_ADI_BY_PLAKA.get(plaka, agg.get("ilAdi", "").title())
        rec = build_record(ad, plaka, agg, col_to_key, major)
        rec["ilceSayisi"] = old_ilce_sayisi.get(plaka, 0)
        new_iller.append(rec)
        kind_summary[agg.get("kind", "?")] = kind_summary.get(agg.get("kind", "?"), 0) + 1
    new_iller.sort(key=lambda x: x["plaka"])

    secim_yili = int(re.match(r"\d{4}", key).group())
    ilceler_by_geomid = {}
    unmatched_ilce = []
    hist_used = []
    for ilce_key, agg in agrege["ilceler"].items():
        geomId = geomid_map.get(ilce_key)
        if not geomId:
            hist_id = resolve_historical_merkez(agg["ilId"], agg["ilceAdi"], secim_yili)
            if hist_id and agg.get("sandikSayisi", 0) > 0:
                geomId = hist_id
                hist_used.append((agg["ilAdi"], agg["ilceAdi"], hist_id))
        if not geomId:
            if agg.get("sandikSayisi", 0) > 0:
                unmatched_ilce.append((agg["ilAdi"], agg["ilceAdi"], agg["sandikSayisi"]))
            continue
        if geomId.startswith("HIST-"):
            ad = geomId.replace("HIST-", "").replace("-", " ")
        else:
            ad = ILCE_ADI_BY_GEOMID.get(geomId) or agg["ilceAdi"].title()
        existing = ilceler_by_geomid.get(geomId)
        if existing is not None and existing.get("sandik", 0) > 0 and agg.get("sandikSayisi", 0) == 0:
            continue
        rec = build_record(ad, agg["ilId"], agg, col_to_key, major)
        rec["geomId"] = geomId
        ilceler_by_geomid[geomId] = rec
    new_ilceler = list(ilceler_by_geomid.values())
    new_ilceler.sort(key=lambda x: (x["plaka"], x["ad"]))

    secim["iller"] = new_iller
    secim["ilceler"] = new_ilceler
    save_election(key, secim)

    print(f"{key}: {len(new_iller)} il, {len(new_ilceler)} ilce guncellendi.")
    print("il turu dagilimi:", kind_summary)
    if hist_used:
        print(f"{len(hist_used)} ilce tarihsel HIST-geomId ile eklendi.")
    if unmatched_ilce:
        print(f"UYARI: {len(unmatched_ilce)} ilce eslenemedi:")
        for u in unmatched_ilce:
            print("  ", u)


if __name__ == "__main__":
    main()
