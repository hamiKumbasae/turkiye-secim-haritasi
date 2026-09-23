"""
parse_ysk_pdfs.py'nin urettigi yapisal JSON'u data/normalized/genel_secimler.json
icine isler. 1983,1987,1991,1995,1999,2002,2007 yillarinin il kayitlarini
YSK resmi (il-bazli) veriyle GUNCELLER: katilim, secmen, gecerliOy, oy, vekil,
toplamVekil, kazanan. Sadece bu 7 yil etkilenir, digerleri dokunulmaz.

pipelines/genel_1950_1977/merge_into_normalized.py ile AYNI mantik/desende:
majorPartiler DEGISTIRILMEZ, major-disi partiler 'Diger' altinda toplanir,
vekil toplami YSK'nin kendi milletvekili_sayisi'yla TAM eslesmezse o il/yil
YAZILMAZ (butunluk hatasi olarak raporlanir, script durur).

Kullanim:
  python3 merge_into_normalized.py <parsed.json> <filename_to_label.txt>
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
DATA_NORM = ROOT / "data" / "normalized"
PARTILER_PATH = DATA_NORM / "partiler.json"

sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

YEARS = ["2007", "2002", "1999", "1995", "1991", "1987", "1983"]

# YSK PDF'lerindeki parti kisa kodu -> projenin kendi parti anahtari.
# Bu mapping, HER yil icin projenin ONCEDEN (Wikipedia kaynakli) kullandigi
# anahtarlarla TEK TEK karsilastirilarak kuruldu (bkz. oturum notlari) - amac
# deger DEGISTIRMEDEN sadece kaynagi/saglamligi yukseltmek, parti kimligi
# atamasini YENIDEN YORUMLAMAMAK. Iki YENI parti (MÇP, YENP95) bu turda ilk
# kez ayri izleniyor (eskiden 'Diger'e karisiyordu) - major degiller, yine
# 'Diger'e dusecekler (majorPartiler degismiyor), ama kendi renkleriyle
# partiler.json'a eklendi.
STATIC_MAP = {
    "AK PARTİ": "AK Parti", "ANAP": "ANAP", "ATP": "ATP", "BBP": "BBP",
    "BP": "BP", "BTP": "BTP", "BĞMZ": "Bağımsız", "CHP": "CHP",
    "DBP": "DBP99", "DEHAP": "DEHAP", "DEPAR": "DEPAR", "DP": "DP",
    "DSP": "DSP", "DTP": "DEMTP", "DYP": "DYP", "EMEP": "EMEP", "FP": "FP",
    "GENÇ PARTİ": "GP", "HADEP": "HADEP", "HP": "HP", "HYP": "HYP",
    "IDP": "IDP", "LDP": "LDP", "MDP": "MDP", "MHP": "MHP",
    "MİLLET PARTİSİ": "MP92", "MÇP": "MÇP", "RP": "RP",
    "SAADET PARTİSİ": "SP", "SHP": "SHP", "SİP": "SİP", "SP": "SosP",
    "TKP": "TKP", "YDH": "YDH", "YDP": "YDP", "YENİ PARTİ": "YENP95",
    "YP": "YP", "YTP": "YTP02", "ÖDP": "ÖDP", "İP": "İP",
}

NEW_PARTY_COLORS = {
    "MÇP": {"short": "MÇP", "light": "#7f1d3a", "dark": "#c2456e"},
    "YENP95": {"short": "YENİ P.", "light": "#a16207", "dark": "#eab308"},
}

# YSK dosya-adi (ASCII, plaka sirali) -> projenin il adi. Bu turda TUM 81 il
# YSK arsivinde var (1950-1977'nin aksine Sakarya da dahil) - rename gerekmiyor
# (probe asamasinda dogrudan projenin guncel isimleriyle eslesti).
PROVINCE_RENAME = {}


# Bilinen tek istisna: YSK'nin Bingöl PDF'inde 1983 icin ozet satiri
# "Milletvekili sayisi: 3" diyor ama parti tablosundaki tek satir (ANAP: 2 mv,
# HP/MDP: 0) toplami 2. Bu depoya ONCEDEN (Wikipedia kaynagindan, BAGIMSIZ
# bir kaynaktan) girilmis olan veri de toplamVekil=2/vekil={"ANAP":2}
# diyordu - yani iki BAGIMSIZ kaynak (Wikipedia ve YSK'nin KENDI parti
# tablosu) 2'de birlesiyor, sadece YSK PDF'inin OZET SATIRI 3 diyor. Bu
# tek il/yil icin ozet degil, parti-tablosu-toplami esas alindi (bkz.
# PROVENANCE.md).
KNOWN_SUMMARY_MISMATCH = {("Bingöl", "1983")}

def map_party(ysk_code, year):
    if ysk_code not in STATIC_MAP:
        raise KeyError(f"Bilinmeyen YSK parti kodu: {ysk_code!r} (yil {year})")
    return STATIC_MAP[ysk_code]


def load_filename_to_label(path: pathlib.Path) -> dict:
    mapping = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "|" not in line:
            continue
        label, fname = line.split("|", 1)
        mapping[pathlib.Path(fname).stem] = label
    return mapping


def main():
    parsed_path = pathlib.Path(sys.argv[1])
    parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
    filename_to_label = load_filename_to_label(pathlib.Path(sys.argv[2]))

    genel = {y: load_election(y) for y in YEARS}
    partiler = json.loads(PARTILER_PATH.read_text(encoding="utf-8"))

    for key, color in NEW_PARTY_COLORS.items():
        partiler.setdefault(key, color)

    updated = {y: 0 for y in YEARS}
    skipped_no_match = []
    integrity_errors = []

    for ysk_stem, by_year in parsed.items():
        ysk_name = filename_to_label.get(ysk_stem, ysk_stem)
        proj_name = PROVINCE_RENAME.get(ysk_name, ysk_name)
        for year in YEARS:
            info = by_year.get(year)
            if not info or info.get("milletvekili_sayisi") is None:
                continue  # bu il o yil henuz kurulmamis / veri yok

            secim = genel[year]
            major = set(secim["majorPartiler"])
            il = next((x for x in secim["iller"] if x["ad"] == proj_name), None)
            if il is None:
                skipped_no_match.append((year, ysk_name))
                continue

            oy = {}
            vekil = {}
            diger_oy = 0
            diger_oran = 0.0
            diger_mv = 0
            for ysk_code, pinfo in info["partiler"].items():
                proj_key = map_party(ysk_code, year)
                if proj_key in major:
                    oy[proj_key] = {"oy": pinfo["oy"], "oran": pinfo["oran"]}
                    if pinfo["mv"]:
                        vekil[proj_key] = pinfo["mv"]
                else:
                    diger_oy += pinfo["oy"]
                    diger_oran += pinfo["oran"] or 0
                    diger_mv += pinfo["mv"]
            if diger_oy:
                oy["Diğer"] = {"oy": diger_oy, "oran": round(diger_oran, 2)}
            if diger_mv:
                vekil["Diğer"] = diger_mv

            total_mv = info["milletvekili_sayisi"]
            vekil_sum = sum(vekil.values())
            if vekil_sum != total_mv:
                if (proj_name, year) in KNOWN_SUMMARY_MISMATCH:
                    total_mv = vekil_sum
                else:
                    integrity_errors.append(
                        f"{year}/{proj_name}: vekil toplami {vekil_sum} != "
                        f"YSK milletvekili_sayisi {total_mv}"
                    )
                    continue

            kazanan = max(info["partiler"].items(), key=lambda kv: kv[1]["oy"])[0]
            kazanan_key = map_party(kazanan, year)

            il["katilim"] = info["katilim_orani"]
            il["secmen"] = info["kayitli_secmen"]
            il["gecerliOy"] = info["gecerli_oy"]
            il["oy"] = oy
            il["vekil"] = vekil
            il["toplamVekil"] = total_mv
            il["kazanan"] = kazanan_key
            updated[year] += 1

    if integrity_errors:
        print(f"{len(integrity_errors)} BUTUNLUK HATASI (vekil toplami tutmadi):")
        for e in integrity_errors[:30]:
            print(" ", e)
        raise SystemExit(1)

    if skipped_no_match:
        print(f"UYARI: {len(skipped_no_match)} il/yil eslesmedi (isim farki olabilir):")
        for y, n in skipped_no_match[:20]:
            print(" ", y, n)

    for year in YEARS:
        save_election(year, genel[year])
    PARTILER_PATH.write_text(
        json.dumps(partiler, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8"
    )
    print("guncellenen il sayisi (yil basina):", updated)


if __name__ == "__main__":
    main()
