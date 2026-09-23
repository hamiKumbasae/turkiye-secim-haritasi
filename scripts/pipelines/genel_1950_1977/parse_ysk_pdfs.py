"""
YSK'nin 1950-1977 il-bazli PDF'lerini (Seçim Çevresine Göre Milletvekili
Genel Secimi Sonuclari) yapisal JSON'a cevirir. pdfplumber ile hucre
konumuna gore okur (duz metin akisi degil), bos hucreler '' olarak gelir.
"""
import json
import pathlib
import sys

import pdfplumber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from common.tr_numbers import to_int, to_float  # noqa: E402

YEARS = ["1977", "1973", "1969", "1965", "1961", "1957", "1954", "1950"]

PDF_DIR = pathlib.Path(sys.argv[1])
OUT_PATH = pathlib.Path(sys.argv[2])


def dedupe_doubled(s: str) -> str:
    """Bazi il PDF'lerinde parti etiketleri font/render hatasiyla her karakter
    2 kere basilmis sekilde geliyor (orn. 'DP' -> 'DDPP', 'DEMOKRATİK PARTİ' ->
    'DDEEMMOOKKRRAATTİİKK PPAARRTTİİ'). Sayisal hucreler etkilenmiyor, sadece
    bu metin sutunu. Her kelimeyi ayri kontrol et: karakterler tam ikili
    (s[0]==s[1], s[2]==s[3], ...) ise yariya indir."""
    def fix_word(w):
        if len(w) % 2 != 0 or len(w) < 2:
            return w
        if all(w[i] == w[i + 1] for i in range(0, len(w), 2)):
            return w[0::2]
        return w
    # newline de bir "kelime ayraci" gibi davranmali - PDF'te tek (ikizlenmemis)
    # geliyor, boslukla ayni muamele edilmezse kelime eslemesi bozuluyor.
    return " ".join(fix_word(w) for w in s.replace("\n", " ").split())


def parse_province_pdf(path: pathlib.Path):
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        if len(tables) != 2:
            raise ValueError(f"{path.name}: beklenmeyen tablo sayisi {len(tables)}")
        summary, parties_table = tables

        # summary: 5 satir x 8 yil (kayitli, oy_kullanan, katilim, gecerli_oy, mv_sayisi)
        if len(summary) != 5:
            raise ValueError(f"{path.name}: summary tablo 5 satir degil ({len(summary)})")
        kayitli, oy_kullanan, katilim, gecerli_oy, mv_sayisi = summary

        by_year = {}
        for i, year in enumerate(YEARS):
            by_year[year] = {
                "kayitli_secmen": to_int(kayitli[i]),
                "oy_kullanan": to_int(oy_kullanan[i]),
                "katilim_orani": to_float(katilim[i]),
                "gecerli_oy": to_int(gecerli_oy[i]),
                "milletvekili_sayisi": to_int(mv_sayisi[i]),
                "partiler": {},
            }

        # parti tablosu: her parti 3 satir (Alinan oy sayisi / Oy orani / Kazandigi MV sayisi),
        # parti adi (kisa kod parantez icinde) sadece ilk satirin 0. hucresinde
        current_party = None
        i = 0
        rows = parties_table
        while i < len(rows):
            row = rows[i]
            label0 = (row[0] or "").strip()
            if label0:
                label0 = dedupe_doubled(label0)
                # "Adalet Partisi\n(AP)" -> kisa kod
                if "(" in label0 and label0.endswith(")"):
                    current_party = label0.split("(")[-1].rstrip(")").strip()
                else:
                    current_party = label0.strip()
            stat = (row[1] or "").strip()
            values = row[2:2 + 8]
            if stat == "Alınan oy sayısı":
                oy_row = values
                oran_row = rows[i + 1][2:2 + 8]
                mv_row = rows[i + 2][2:2 + 8]
                for j, year in enumerate(YEARS):
                    oy = to_int(oy_row[j])
                    if oy is None:
                        continue
                    by_year[year]["partiler"][current_party] = {
                        "oy": oy,
                        "oran": to_float(oran_row[j]),
                        "mv": to_int(mv_row[j]) or 0,
                    }
                i += 3
            else:
                i += 1

        return by_year


def main():
    result = {}
    errors = []
    for path in sorted(PDF_DIR.glob("*.pdf")):
        if path.stem == "Turkiye":
            continue
        try:
            result[path.stem] = parse_province_pdf(path)
        except Exception as e:
            errors.append(f"{path.name}: {e}")

    if errors:
        print(f"{len(errors)} HATA — cikti dosyasi YAZILMADI:")
        for e in errors:
            print(" ", e)
        raise SystemExit(1)

    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazildi: {OUT_PATH} ({len(result)} il)")


if __name__ == "__main__":
    main()
