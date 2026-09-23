"""
parse_ysk_pdfs.py'nin urettigi yapisal JSON'u data/normalized/yerel_secimler.json
icine isler. 1994yerel, 1999yerel, 2004yerel yillarinin IL kayitlarini
(sadece il merkezi - ilceler bu depoda zaten var, DOKUNULMUYOR) YSK resmi
il-bazli PDF arsivinden GUNCELLER.

Guvenlik kontrolu: parti oylari toplami resmi 'gecerli oy sayisi'ndan
%2'den fazla sapan bir il/yil YAZILMAZ (pdfplumber'in bazi PDF'lerde
gorulen nadir sutun-hizalama sorununa karsi - bkz. PROVENANCE.md, Gümüşhane
1994 ornegi).

Kullanim:
  python3 merge_into_normalized.py <yil> <parsed.json>
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
DATA_NORM = ROOT / "data" / "normalized"
PARTILER_PATH = DATA_NORM / "partiler.json"

sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

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


def map_party(ysk_code):
    if ysk_code not in STATIC_MAP:
        raise KeyError(f"Bilinmeyen YSK parti kodu: {ysk_code!r}")
    return STATIC_MAP[ysk_code]


def main():
    year = sys.argv[1]
    parsed_path = pathlib.Path(sys.argv[2])
    parsed = json.loads(parsed_path.read_text(encoding="utf-8"))

    key = f"{year}yerel"
    secim = load_election(key)
    partiler = json.loads(PARTILER_PATH.read_text(encoding="utf-8"))
    major = set(secim["majorPartiler"])

    updated = 0
    skipped_no_match = []
    skipped_sapma = []
    unmapped = set()

    for ad, info in parsed.items():
        il = next((x for x in secim["iller"] if x["ad"] == ad), None)
        if il is None:
            skipped_no_match.append(ad)
            continue

        party_sum = sum(p["oy"] for p in info["partiler"].values())
        official = info["gecerli_oy"]
        if official and abs(party_sum - official) > official * MAX_GECERLI_OY_SAPMA:
            skipped_sapma.append((ad, party_sum, official))
            continue

        bad_codes = [c for c in info["partiler"] if c not in STATIC_MAP]
        if bad_codes:
            unmapped.update(bad_codes)
            continue

        oy = {}
        diger_oy = 0
        diger_oran = 0.0
        for ysk_code, pinfo in info["partiler"].items():
            proj_key = map_party(ysk_code)
            if proj_key in major:
                oy[proj_key] = {"oy": pinfo["oy"], "oran": pinfo["oran"]}
            else:
                diger_oy += pinfo["oy"]
                diger_oran += pinfo["oran"] or 0
        if diger_oy:
            oy["Diğer"] = {"oy": diger_oy, "oran": round(diger_oran, 2)}

        kazanan_code = max(info["partiler"].items(), key=lambda kv: kv[1]["oy"])[0]
        kazanan_key = map_party(kazanan_code)

        il["katilim"] = info["katilim_orani"]
        il["secmen"] = info["secmen"]
        il["sandik"] = info["sandik"]
        il["gecerliOy"] = info["gecerli_oy"]
        il["oy"] = oy
        il["kazanan"] = kazanan_key
        updated += 1

    if unmapped:
        print(f"BILINMEYEN PARTI KODLARI (hicbir sey yazilmadi): {sorted(unmapped)}")
        raise SystemExit(1)

    if skipped_sapma:
        print(f"{len(skipped_sapma)} il GUVENLIK KONTROLU nedeniyle ATLANDI (parti toplami resmi geçerli oydan %2+ sapiyor, muhtemelen sutun hizalama sorunu):")
        for ad, s, o in skipped_sapma:
            print(f"   {ad}: parti_toplami={s} resmi={o}")

    if skipped_no_match:
        print(f"UYARI: {len(skipped_no_match)} il eslesmedi: {skipped_no_match}")

    save_election(key, secim)
    PARTILER_PATH.write_text(
        json.dumps(partiler, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8"
    )
    print(f"{year}: guncellenen il sayisi: {updated}")


if __name__ == "__main__":
    main()
