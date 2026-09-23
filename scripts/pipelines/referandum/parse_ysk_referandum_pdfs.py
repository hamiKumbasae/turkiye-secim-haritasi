"""
YSK'nin eski (1961/1982/1987/1988) halkoylamasi PDF'lerini (data/raw/ysk/
referandum/*.pdf) il-bazli yapisal JSON'a cevirir. Bu PDF'ler genel secim
arsivinden farkli/daha basit bir bicimde: TEK bir duz tablo (67 il satiri),
yil-basina tekrar eden sutunlar yok. Sutun SIRASI yildan yila degisiyor
(orn. 1961/1982: GECERLI once GECERSIZ sonra; 1987/1988: tersi) — bu yuzden
sabit indeks yerine BASLIK ADINA gore okunuyor.

Kullanim:
  python3 parse_ysk_referandum_pdfs.py <pdf_yolu> <yil>
  (or dogrudan import edip parse_file(path) cagirin)
"""
import json
import pathlib
import sys

import pdfplumber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from common.tr_numbers import to_int as _to_int  # noqa: E402

def to_int(s):
    return _to_int(s, strict=False)

COL_ALIASES = {
    "il_kodu": ["İL KODU"],
    "il_adi": ["İL ADI", "GÜMRÜK ADI"],
    "sandik": ["İLİN SANDIK SAYISI", "GÜMRÜK SANDIK\nSAYISI"],
    "kayitli_secmen": ["SANDIK SEÇMEN\nLİSTESİNDE KAYITLI\nOLANLARIN SAYISI"],
    "katilan": ["HALK OYLAMASINA\nKATILANLARIN SAYISI"],
    "gecerli_oy": ["GEÇERLİ OY"],
    "gecersiz_oy": ["GEÇERSİZ OY"],
    "evet": ['"EVET" OYU\nVERENLERİN SAYISI'],
    "hayir": ['"HAYIR" OYU\nVERENLERİN SAYISI'],
}


def find_col(header_row, aliases):
    for i, cell in enumerate(header_row):
        if cell and cell.strip() in aliases:
            return i
    return None


def parse_file(path: pathlib.Path) -> dict:
    provinces = {}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                header_idx = next((i for i, row in enumerate(table) if row and row[0] == "İL KODU"), None)
                if header_idx is None:
                    continue
                header = table[header_idx]
                col = {key: find_col(header, aliases) for key, aliases in COL_ALIASES.items()}
                if col["il_adi"] is None:
                    continue
                is_gumruk = col["il_kodu"] is not None and header[0] and "GÜMRÜK" not in str(header[0])
                for row in table[header_idx + 1:]:
                    il_adi = row[col["il_adi"]] if col["il_adi"] is not None else None
                    if not il_adi or not il_adi.strip():
                        continue
                    if "TOPLAM" in il_adi or "GÜMRÜK" == il_adi.strip():
                        continue  # ozet/toplam satiri, gercek il/gumruk noktasi degil
                    entry = {
                        "sandik": to_int(row[col["sandik"]]) if col["sandik"] is not None else None,
                        "kayitli_secmen": to_int(row[col["kayitli_secmen"]]) if col["kayitli_secmen"] is not None else None,
                        "katilan": to_int(row[col["katilan"]]) if col["katilan"] is not None else None,
                        "gecerli_oy": to_int(row[col["gecerli_oy"]]) if col["gecerli_oy"] is not None else None,
                        "gecersiz_oy": to_int(row[col["gecersiz_oy"]]) if col["gecersiz_oy"] is not None else None,
                        "evet": to_int(row[col["evet"]]) if col["evet"] is not None else None,
                        "hayir": to_int(row[col["hayir"]]) if col["hayir"] is not None else None,
                    }
                    # GUMRUK (yurtdisi sinir kapisi) satirlari il tablosuyla AYNI basligi
                    # paylasiyor (1988) ama il adi yerine "ANKARA-ESENBOGA" gibi bir
                    # gumruk adi tasiyor — gercek il adlarinda "-" olmaz, bu yuzden ayirt edici.
                    key = "gumruk" if "-" in il_adi else "iller"
                    provinces.setdefault(key, {})[il_adi.strip()] = entry
    return provinces.get("iller", {}), provinces.get("gumruk", {})


def main():
    pdf_path = pathlib.Path(sys.argv[1])
    year = sys.argv[2]
    iller, gumruk = parse_file(pdf_path)
    out = {"iller": iller, "gumruk": gumruk}
    out_path = pdf_path.parent / f"{year}_parsed.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{year}: {len(iller)} il, {len(gumruk)} gümrük noktası -> {out_path}")


if __name__ == "__main__":
    main()
