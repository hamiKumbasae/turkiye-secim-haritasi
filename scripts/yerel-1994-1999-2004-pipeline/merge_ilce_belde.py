"""
parse_ilce_belde.py'nin urettigi bucket'lari (gomId -> agrege oy/secmen)
data/normalized/yerel_secimler.json'daki ilgili yilin "ilceler" listesine
isler. SADECE bucket'i olan (yani YSK PDF'inden cozulebilen) gomId'ler
GUNCELLENIR - cozulemeyenler (bkz. PROVENANCE.md: Aydin/Denizli/Mugla/Ordu/
Tekirdag/Trabzon'un "Merkez" ilcesi + bir avuc kucuk buyuksehir beldesi)
eski (Wikipedia kaynakli) kaydiyla OLDUGU GIBI kalir - kismi, dogru ve
belgelenmis bir yukseltme.

Guvenlik kontrolu: parti oylari toplami resmi 'gecerli oy'dan %2'den fazla
sapan bir bucket YAZILMAZ (mevcut il-bazli merge script'iyle ayni kural).

Kullanim: python3 merge_ilce_belde.py <yil> <parsed.json>
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA_NORM = ROOT / "data" / "normalized"
YEREL_PATH = DATA_NORM / "yerel_secimler.json"

STATIC_MAP = {
    "ANAP": "ANAP", "BAĞIMSIZLAR": "Bağımsız", "BBP": "BBP", "BP": "BP",
    "CHP": "CHP", "DP": "DP", "DSP": "DSP", "DYP": "DYP", "MHP": "MHP",
    "MİLLET PARTİSİ": "MP92", "RP": "RP", "SBP": "SBP", "SHP": "SHP",
    "YDP": "YDP", "İP": "İP", "DBP": "DBP99", "DEHAP": "DEHAP",
    "DEPAR": "DEPAR", "DTP": "DEMTP", "EMEP": "EMEP", "FP": "FP",
    "HADEP": "HADEP", "LDP": "LDP", "SİP": "SİP", "ÖDP": "ÖDP",
    "AK PARTİ": "AK Parti", "ATP": "ATP", "BTP": "BTP", "GENÇ PARTİ": "GP",
    "SAADET PARTİSİ": "SP", "TKP": "TKP", "YTP": "YTP02",
}

MAX_GECERLI_OY_SAPMA = 0.02  # %2

_GENEL2023 = json.loads((DATA_NORM / "genel_secimler.json").read_text(encoding="utf-8"))["2023"]
AD_BY_GEOMID_PLAKA = {i["geomId"]: i["plaka"] for i in _GENEL2023["ilceler"]}


def main():
    year = sys.argv[1]
    parsed = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    buckets = parsed["buckets"]

    yerel = json.loads(YEREL_PATH.read_text(encoding="utf-8"))
    key = f"{year}yerel"
    secim = yerel[key]
    major = set(secim["majorPartiler"])

    by_geomid = {i["geomId"]: i for i in secim["ilceler"]}

    updated = 0
    new_count = [0]
    skipped_sapma = []
    unmapped = set()
    for gid, b in buckets.items():
        bad_codes = [c for c in b["partiler"] if c not in STATIC_MAP]
        if bad_codes:
            unmapped.update(bad_codes)
            continue

        party_sum = sum(b["partiler"].values())
        official = b["gecerli"]
        if official and abs(party_sum - official) > official * MAX_GECERLI_OY_SAPMA:
            skipped_sapma.append((b["ad"], party_sum, official))
            continue

        oy = {}
        diger_oy = 0
        for code, v in b["partiler"].items():
            if not v:
                continue
            key_ = STATIC_MAP[code]
            if key_ in major:
                oy[key_] = oy.get(key_, {"oy": 0})
                oy[key_]["oy"] += v
            else:
                diger_oy += v
        if diger_oy:
            oy["Diğer"] = {"oy": diger_oy}

        total = sum(v["oy"] for v in oy.values())
        for k in oy:
            oy[k]["oran"] = round(oy[k]["oy"] / total * 100, 2) if total else None
        kazanan = max(oy.items(), key=lambda kv: kv[1]["oy"])[0] if oy else None

        rec = by_geomid.get(gid)
        if rec is None:
            if b["ad"] == "Merkez":
                # il kaydi zaten il merkezinin kendi yarisini tasiyor - bu
                # bucket onunla AYNI oylari tekrar eder, ayri ilce kaydi
                # olarak EKLENMEZ (cift sayim olur).
                continue
            rec = {
                "ad": b["ad"], "gecerliOy": 0, "geomId": gid, "katilim": None,
                "kazanan": None, "oy": {}, "plaka": None, "sandik": 0,
                "secmen": 0, "toplamVekil": 0, "vekil": {},
            }
            secim["ilceler"].append(rec)
            by_geomid[gid] = rec
            new_count[0] += 1
        rec["ad"] = b["ad"] or rec["ad"]
        rec["gecerliOy"] = official
        rec["katilim"] = round(b["katilan"] / b["secmen"] * 100, 2) if b.get("secmen") else None
        rec["kazanan"] = kazanan
        rec["oy"] = oy
        rec["plaka"] = rec["plaka"] or AD_BY_GEOMID_PLAKA.get(gid)
        rec["sandik"] = b["sandik"]
        rec["secmen"] = b["secmen"]
        updated += 1

    if unmapped:
        print(f"BILINMEYEN PARTI KODLARI (hicbir sey yazilmadi): {sorted(unmapped)}")
        raise SystemExit(1)

    if skipped_sapma:
        print(f"{len(skipped_sapma)} ilce GUVENLIK KONTROLU nedeniyle ATLANDI (parti toplami resmi gecerli oydan %2+ sapiyor):")
        for ad, s, o in skipped_sapma:
            print(f"   {ad}: parti_toplami={s} resmi={o}")

    secim["ilceler"].sort(key=lambda x: (x["plaka"] or 0, x["ad"]))
    YEREL_PATH.write_text(
        json.dumps(yerel, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8"
    )
    print(f"{year}: guncellenen ilce sayisi: {updated} / {len(secim['ilceler'])} (bunun {new_count[0]} tanesi YENI eklendi)")


if __name__ == "__main__":
    main()
