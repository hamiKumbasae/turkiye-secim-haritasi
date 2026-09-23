"""
parse_ysk_pdfs.py'nin urettigi yapisal JSON'u data/normalized/genel_secimler.json
icine isler. 1950,1954,1957,1961,1965,1969,1973,1977 yillarinin il kayitlarini
YSK (TUIK kaynakli) veriyle GUNCELLER: katilim, secmen, gecerliOy, oy, vekil,
toplamVekil, kazanan. Sadece bu 8 yil etkilenir, digerleri dokunulmaz.

majorPartiler listesi DEGISTIRILMEZ (UI/renk davranisini bozmamak icin) -
o yilin majorPartiler'inda olmayan partiler 'Diger' anahtaninda toplanir,
mevcut projenin zaten kullandigi kalip.

Kullanim:
  python3 merge_into_normalized.py <parsed.json> <filename_to_label.txt>

<filename_to_label.txt>: "Etiket|dosyaadi.pdf" formatinda, parse_ysk_pdfs.py'nin
kullandigi dosya-stem'lerini (orn. "Adiyaman", ASCII, Turkce karaktersiz)
gercek il etiketine (orn. "Adıyaman") cevirmek icin — PDF dosya adlari
YSK'nin kendi sitesinde ASCII, projenin il adlari degil.
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA_NORM = ROOT / "data" / "normalized"
PARTILER_PATH = DATA_NORM / "partiler.json"

sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

YEARS = ["1950", "1954", "1957", "1961", "1965", "1969", "1973", "1977"]

# secim_tarihi_data.json'da SEÇİM seviyesinde (il degil) 'toplamSandalye' alani
# var — bu ayrica dolduruluyor, il kayitlarindan hesaplanmiyor. YSK'nin kendi
# "Türkiye Geneli Seçim Sonuçları" sayfasindaki resmi ulusal rakamlar (bkz.
# PROVENANCE.md). Sadece bu 4 yil (1965+ zaten dolu). 1957/1961'de Sakarya
# eksik oldugu icin il-bazli toplam bundan biraz dusuk cikacak — bilerek,
# resmi rakam kullaniliyor (Sakarya verisi uydurulmuyor).
NATIONAL_TOTAL_SEATS = {"1950": 487, "1954": 541, "1957": 610, "1961": 450}

# YSK PDF'lerindeki parti kisa kodu -> projenin kendi parti anahtari.
# Ayni kisaltmanin farkli donemlerde farkli partilere ait olabilecegi
# durumlarda (orn. "Millet Partisi" 1950 ve 1965+, "Demokrat Parti" ile
# "Demokratik Parti" farkli partiler) projenin var olan donem-bazli sonek
# kuralina uyuldu (bkz. data/normalized/partiler.json).
STATIC_MAP = {
    "DP": "DP", "CHP": "CHP", "BĞMZ": "Bağımsız", "CMP": "CMP", "KP": "TKöyP",
    "HÜRRİYET PARTİSİ": "HP57", "AP": "AP", "CKMP": "CKMP", "YTP": "YTP61",
    "TİP": "TİP", "MHP": "MHP", "GP": "GP", "CGP": "CGP", "MSP": "MSP",
    "VP": "VP57", "BİRLİK PARTİSİ": "BP69", "DEMOKRATİK PARTİ": "DEMP73",
    "TBP": "TBP73",
}

# Bu 4 yeni parti icin partiler.json'a renk eklenmesi gerekiyor (bkz. asagi).
NEW_PARTY_COLORS = {
    "VP57": {"short": "VP", "light": "#7a5230", "dark": "#a67c52"},
    "BP69": {"short": "BP", "light": "#4a7856", "dark": "#6fa87f"},
    "DEMP73": {"short": "DEMOKRATİK P.", "light": "#8a6d3b", "dark": "#c2a76b"},
    "TBP73": {"short": "TBP", "light": "#5c5470", "dark": "#8b82a3"},
}

# YSK'nin 66 illik listesindeki isim, projenin kullandigi guncel/tarihsel
# isimle farkli oldugunda eslesme. Sakarya YSK listesinde HIC YOK (bilinen
# bir bosluk, bkz. PROVENANCE.md) - o il bu guncellemeden etkilenmiyor,
# eski (Wikipedia kaynakli) verisiyle kaliyor.
PROVINCE_RENAME = {"İçel": "Mersin", "Afyon": "Afyonkarahisar", "Kutahya": "Kütahya"}


def map_party(ysk_code, year):
    if ysk_code == "MİLLET PARTİSİ":
        return "MP50" if year == "1950" else "MP62"
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
            if sum(vekil.values()) != total_mv:
                integrity_errors.append(
                    f"{year}/{proj_name}: vekil toplami {sum(vekil.values())} != "
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
            # NOT: digerOy/digerOran alanlarina DOKUNULMUYOR — bu donemin
            # kayitlarinda zaten yok (kucuk partiler oy['Diğer'] anahtarinda
            # toplaniyor, detail-panel.js'in 'extra'/collapsible mekanizmasi
            # bunu zaten dogru gosteriyor, bkz. PROVENANCE.md).
            updated[year] += 1

    if integrity_errors:
        print(f"{len(integrity_errors)} BUTUNLUK HATASI (vekil toplami tutmadi):")
        for e in integrity_errors[:20]:
            print(" ", e)
        raise SystemExit(1)

    if skipped_no_match:
        print(f"UYARI: {len(skipped_no_match)} il/yil eslesmedi (isim farki olabilir):")
        for y, n in skipped_no_match[:20]:
            print(" ", y, n)

    for year, total in NATIONAL_TOTAL_SEATS.items():
        genel[year]["toplamSandalye"] = total

    for year in YEARS:
        save_election(year, genel[year])
    PARTILER_PATH.write_text(
        json.dumps(partiler, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8"
    )
    print("guncellenen il sayisi (yil basina):", updated)


if __name__ == "__main__":
    main()
