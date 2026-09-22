"""
2007 referandumunun YSK "Ilce Bazinda Il Sonuclari" PDF'lerini (81 il,
her biri gercek imzali "Birlestirme Tutanagi") ilce-duzeyi yapisal JSON'a
cevirir.

ONEMLI: Bu PDF'lerin fontunda Turkce Ğ/İ/Ş karakterleri BOZUK cikiyor
(bazen bosluga, bazen hicbir seye donusuyor — orn. "KARAİSALI" -> "KARA SALI",
"KARATAŞ" -> "KARATA", "ALADAĞ" -> "ALADA "). Sayisal hucreler ETKILENMIYOR.
Ilce adlarini duzeltmek yerine, Ğ/İ/Ş/bosluk SILINMIS haliyle projenin
GUVENILIR ilce listesiyle (scripts/mahalle-veri-pipeline/eslesme/
ysk_ilce_matched.json, YSK API'sinden gelen temiz isimler) eslestiriyoruz —
iki tarafta da ayni harfler silindigi icin sonuc tutarli.

Kullanim:
  python3 parse_2007_ilce_pdfs.py <pdf_dizini> <cikti.json>
"""
import json
import pathlib
import re
import sys
import unicodedata

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ILCE_MATCH_PATH = ROOT / "scripts" / "mahalle-veri-pipeline" / "eslesme" / "ysk_ilce_matched.json"
DISTRICT_SPLITS_PATH = ROOT / "geo" / "historical" / "district_splits.json"

HEADER_MARKERS = ["İlçenin Adı", "Ilçenin Adı", "lçenin Ad"]

# 2007 PDF'inde gecen isim, YSK'nin CANLI API'siyle (getIlceList) DOGRULANMIS
# guncel/gercek adina eslenir — tahmin degil, tek tek sorgulanip teyit edildi
# (bkz. proje ilerleme kaydi, 2026-09-22). Sadece bu 7 durum: isim degisikligi
# (Eyup->Eyupsultan gibi) veya PDF'teki kisaltma/yazim farki (Mustafa K.Pasa).
KNOWN_RENAMES = {
    "KAZAN": "KAHRAMANKAZAN",
    "SAMANDAĞI": "SAMANDAĞ",
    "YAYLADAĞ": "YAYLADAĞI",
    "ÇAĞLIYANCERİT": "ÇAĞLAYANCERİT",
    "EYÜP": "EYÜPSULTAN",
    "MUSTAFA K.PAŞA": "MUSTAFAKEMALPAŞA",
    "BAHŞİLİ": "BAHŞILI",  # YSK API'sinin kendi verisinde boyle (dotless I) - kaynagin kendi tutarsizligi
}


def strip_corrupt_chars(s: str) -> str:
    """PDF'te kaybolan/bozulan karakterleri (Ğ,İ,Ş ve onlarin yerine gelen
    bosluklari) HER IKI taraftan da silerek karsilastirilabilir hale getirir.
    Python'un varsayilan .upper()'i Turkce i/I ayrimini bilmedigi icin
    (orn. "Siirt" -> "SIIRT" degil "SİİRT" olmali) elle donusturuluyor —
    aksi halde "İ" stripping'i bu kelimelerde hic calismaz."""
    s = s.replace("i", "İ").replace("ı", "I").upper()
    for ch in "ĞİŞ":
        s = s.replace(ch, "")
    s = re.sub(r"\s+", "", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def to_int(s):
    if s is None:
        return None
    s = s.replace(".", "").strip()
    return int(s) if s and s.lstrip("-").isdigit() else None


def load_merkez_synthetic_ids():
    """plaka (str) -> "HIST-<Il>-Merkez" gibi sentetik geomId. 2007, bu
    ilcelerin BOLUNMESINDEN (splitYear, hepsi >=2008) ONCE oldugu icin bu
    birlesik/tarihsel geometri dogru secim — bkz. geo/historical/
    district_splits.json + turkiye_ilce_sinirlari_hist_splits.geojson."""
    splits = json.loads(DISTRICT_SPLITS_PATH.read_text(encoding="utf-8"))
    return {plaka: entries[0]["syntheticId"] for plaka, entries in splits.items() if entries}


def load_ilce_lookup():
    """il_ADI (fold edilmis) -> [(strip_corrupt_chars(ilce_ADI), ilce_ADI, ilce_ID, geomId), ...]
    ve il_ADI (fold edilmis) -> il_ID (plaka) eslemesi."""
    entries = json.loads(ILCE_MATCH_PATH.read_text(encoding="utf-8"))
    by_il = {}
    il_id_by_il = {}
    for e in entries:
        key = strip_corrupt_chars(e["il_ADI"])
        by_il.setdefault(key, []).append(
            (strip_corrupt_chars(e["ilce_ADI"]), e["ilce_ADI"], e["ilce_ID"], e["geomId"])
        )
        il_id_by_il[key] = e["il_ID"]
    return by_il, il_id_by_il


def parse_file(path: pathlib.Path, il_adi_hint: str, lookup: dict, il_id_by_il: dict, merkez_synthetic: dict):
    stripped_il = strip_corrupt_chars(il_adi_hint)
    candidates = lookup.get(stripped_il, [])
    if not candidates:
        raise KeyError(f"{path.name}: il '{il_adi_hint}' ysk_ilce_matched.json'da yok")
    il_id = il_id_by_il.get(stripped_il)
    merkez_geom_id = merkez_synthetic.get(str(il_id)) if il_id is not None else None

    rows_out = []
    unmatched = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                header_idx = next(
                    (i for i, row in enumerate(table)
                     if row and row[0] and any(m in str(row[0]) for m in HEADER_MARKERS)),
                    None,
                )
                if header_idx is None:
                    continue
                for row in table[header_idx + 1:]:
                    ilce_raw = row[0]
                    if not ilce_raw or not ilce_raw.strip():
                        continue
                    if "TOPLAM" in ilce_raw.upper():
                        continue
                    values = [to_int(c) for c in row[1:8]]
                    if all(v is None for v in values):
                        continue
                    # "GÖLBAŞI/ADIYAMAN" gibi ayni-adli ilceleri il ekiyle
                    # ayirt eden satirlarda, sadece "/" ONCESINI (gercek ilce
                    # adini) eslestirmede kullan.
                    ilce_name_only = ilce_raw.split("/")[0].strip()
                    ilce_name_only = KNOWN_RENAMES.get(ilce_name_only, ilce_name_only)
                    stripped = strip_corrupt_chars(ilce_name_only)
                    matches = [c for c in candidates if c[0] == stripped]
                    if len(matches) != 1:
                        # "X MERKEZ" satirlari icin, o il buyuksehir-Merkez
                        # bolunmesi gecirmisse (splitYear >= 2008, 2007'den
                        # SONRA) tarihsel/birlesik sentetik geometriyi kullan.
                        if stripped.endswith("MERKEZ") and merkez_geom_id:
                            real_name, ilce_id, geom_id = "Merkez", None, merkez_geom_id
                        else:
                            unmatched.append((ilce_raw, stripped, len(matches)))
                            continue
                    else:
                        _, real_name, ilce_id, geom_id = matches[0]
                    sandik, kayitli, katilan, gecerli, gecersiz, evet, hayir = (values + [None] * 7)[:7]
                    rows_out.append({
                        "ilce_ADI": real_name, "ilce_ID": ilce_id, "geomId": geom_id,
                        "sandik": sandik, "kayitli_secmen": kayitli, "katilan": katilan,
                        "gecerli_oy": gecerli, "gecersiz_oy": gecersiz, "evet": evet, "hayir": hayir,
                    })
    return rows_out, unmatched


def main():
    pdf_dir = pathlib.Path(sys.argv[1])
    out_path = pathlib.Path(sys.argv[2])
    filenames_txt = pdf_dir.parent / "2007_ilce_filenames.txt" if len(sys.argv) < 4 else pathlib.Path(sys.argv[3])

    label_by_fname = {}
    for line in filenames_txt.read_text(encoding="utf-8").splitlines():
        if "|" not in line:
            continue
        label, fname = line.split("|", 1)
        label_by_fname[fname.strip()] = label.strip()

    lookup, il_id_by_il = load_ilce_lookup()
    merkez_synthetic = load_merkez_synthetic_ids()
    result = {}
    total_unmatched = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        label = label_by_fname.get(pdf_path.name)
        if label is None or label == "Gümrükler":
            continue
        try:
            rows, unmatched = parse_file(pdf_path, label, lookup, il_id_by_il, merkez_synthetic)
        except KeyError as e:
            print("HATA:", e)
            continue
        result[label] = rows
        if unmatched:
            total_unmatched.append((label, unmatched))

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    total_ilce = sum(len(v) for v in result.values())
    print(f"{len(result)} il, {total_ilce} ilçe -> {out_path}")
    if total_unmatched:
        print(f"\n{sum(len(u) for _, u in total_unmatched)} EŞLEŞMEYEN SATIR:")
        for il, rows in total_unmatched:
            for raw, stripped, n in rows:
                print(f"  {il}: {raw!r} (stripped={stripped!r}, {n} aday eşleşme)")


if __name__ == "__main__":
    main()
