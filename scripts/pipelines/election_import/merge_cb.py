"""
fetch_and_aggregate.js ciktisini data/normalized/cumhurbaskanligi.json'a
isler. CB secimlerinde bagimsizN_ALDIGI_OY sutunlari ULUSAL/SABIT (her N
ayni aday, genel secimin aksine il-basina degismiyor) - baslik dosyasindaki
ad dogrudan adayin tam adi.

Kullanim: python3 merge_cb.py <key orn 2018cb> <agrege.json>
"""
import json
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402
from common.hist_geomid import resolve_historical_merkez  # noqa: E402

GEOMID_MAP_PATH = ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json"
_GENEL2023 = load_election("2023")
IL_ADI_BY_PLAKA = {i["plaka"]: i["ad"] for i in _GENEL2023["iller"]}
ILCE_ADI_BY_GEOMID = {i["geomId"]: i["ad"] for i in _GENEL2023["ilceler"]}


def proper_case_tr(s: str) -> str:
    """YSK'nin TUM BUYUK isimlerini projenin kullandigi Turkce Baslik Harfli
    forma cevirir (orn. 'RECEP TAYYİP ERDOĞAN' -> 'Recep Tayyip Erdoğan')."""
    tr_lower_map = str.maketrans("İIŞĞÜÇÖ", "iışğüçö")
    words = s.split(" ")
    out = []
    for w in words:
        if not w:
            continue
        first, rest = w[0], w[1:]
        rest_lower = rest.translate(tr_lower_map).lower()
        first_upper = {"i": "İ"}.get(first.lower(), first.upper())
        out.append(first_upper + rest_lower)
    return " ".join(out)


BAGIMSIZ_NUMBERED_RE = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def build_record(ad, plaka, agg, col_to_name, name_alias):
    oy = {}
    diger = 0
    for col, v in agg["oy"].items():
        if not v:
            continue
        if not BAGIMSIZ_NUMBERED_RE.match(col):
            # "bagimsiz_ALDIGI_OY" (numarasiz) gibi birden fazla kisiye
            # karisik atanmis / belirsiz sutunlar - kisiye ATFETMEDEN Diger'e.
            diger += v
            continue
        raw_name = col_to_name.get(col)
        if raw_name is None:
            diger += v
            continue
        name = name_alias.get(raw_name, proper_case_tr(raw_name))
        oy[name] = oy.get(name, 0) + v
    if diger:
        oy["Diğer"] = oy.get("Diğer", 0) + diger
    total = sum(oy.values())
    oy_with_oran = {k: {"oy": v, "oran": round(v / total * 100, 2) if total else None} for k, v in oy.items()}
    kazanan = max(oy.items(), key=lambda kv: kv[1])[0] if oy else None
    return {
        "ad": ad,
        "digerOy": 0,
        "digerOran": 0.0,
        "gecerliOy": agg["gecerli"],
        "ilceSayisi": 0,
        "katilim": round(agg["oyKullanan"] / agg["secmen"] * 100, 2) if agg.get("secmen") else None,
        "kazanan": kazanan,
        "oy": oy_with_oran,
        "plaka": plaka,
        "sandik": agg.get("sandikSayisi", 0),
        "secmen": agg["secmen"],
        "toplamVekil": 0,
        "vekil": {},
    }


def main():
    key = sys.argv[1]
    agrege = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    name_alias_path = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
    name_alias = json.loads(name_alias_path.read_text(encoding="utf-8")) if name_alias_path else {}
    geomid_map = json.loads(GEOMID_MAP_PATH.read_text(encoding="utf-8"))

    secim = load_election(key)
    col_to_name = agrege["colToName"]

    old_ilce_sayisi = {i["plaka"]: i["ilceSayisi"] for i in secim["iller"]}
    sandik_by_il = {}
    for agg in agrege["ilceler"].values():
        sandik_by_il[agg["ilId"]] = sandik_by_il.get(agg["ilId"], 0) + agg.get("sandikSayisi", 0)

    new_iller = []
    for il_id_str, agg in agrege["iller"].items():
        plaka = int(il_id_str)
        ad = IL_ADI_BY_PLAKA.get(plaka, agg["ilAdi"].title())
        rec = build_record(ad, plaka, agg, col_to_name, name_alias)
        rec["ilceSayisi"] = old_ilce_sayisi.get(plaka, 0)
        rec["sandik"] = sandik_by_il.get(plaka, 0)
        new_iller.append(rec)
    new_iller.sort(key=lambda x: x["plaka"])

    secim_yili = int(re.match(r"\d{4}", key).group())
    ilceler_by_geomid = {}
    unmatched_ilce = []
    hist_used = []
    for ilce_key, agg in agrege["ilceler"].items():
        geomId = geomid_map.get(ilce_key)
        if not geomId:
            hist_id = resolve_historical_merkez(agg["ilId"], agg["ilceAdi"], secim_yili)
            if hist_id and agg["sandikSayisi"] > 0:
                geomId = hist_id
                hist_used.append((agg["ilAdi"], agg["ilceAdi"], hist_id))
        if not geomId:
            if agg["sandikSayisi"] > 0:
                unmatched_ilce.append((agg["ilAdi"], agg["ilceAdi"], agg["sandikSayisi"]))
            continue
        if geomId.startswith("HIST-"):
            ad = geomId.replace("HIST-", "").replace("-", " ")
        else:
            ad = ILCE_ADI_BY_GEOMID.get(geomId) or agg["ilceAdi"].title()
        existing = ilceler_by_geomid.get(geomId)
        if existing is not None and existing.get("sandik", 0) > 0 and agg.get("sandikSayisi", 0) == 0:
            continue
        rec = build_record(ad, agg["ilId"], agg, col_to_name, name_alias)
        rec["geomId"] = geomId
        ilceler_by_geomid[geomId] = rec
    new_ilceler = sorted(ilceler_by_geomid.values(), key=lambda x: (x["plaka"], x["ad"]))

    secim["iller"] = new_iller
    secim["ilceler"] = new_ilceler
    save_election(key, secim)

    all_names = set()
    for i in new_iller:
        all_names.update(i["oy"].keys())
    print(f"{key}: {len(new_iller)} il, {len(new_ilceler)} ilce guncellendi.")
    print("adaylar:", sorted(all_names))
    if hist_used:
        print(f"{len(hist_used)} ilce tarihsel HIST-geomId ile eklendi.")
    if unmatched_ilce:
        print(f"UYARI: {len(unmatched_ilce)} ilce eslenemedi:")
        for u in unmatched_ilce:
            print("  ", u)


if __name__ == "__main__":
    main()
