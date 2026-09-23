"""
YSK'nin 1983-2007 il-bazli PDF'lerini (Seçim Çevresine Göre Milletvekili
Genel Secimi Sonuclari) yapisal JSON'a cevirir. pdfplumber ile hucre
konumuna gore okur (duz metin akisi degil), bos hucreler '' olarak gelir.

Format, pipelines/genel_1950_1977'dekiyle BENZER ama AYNI DEGIL:
- Bu PDF'ler cok sayfali (parti sayisi fazla oldugundan parti tablosu
  sayfalara bolunuyor); OZET tablosu HER sayfada TEKRARLANIYOR (ayni
  icerikle) - sadece ILK sayfadaki ozet kullanilmali, sonraki sayfalarin
  tekrar eden ozet tablosu ATLANMALI.
- Ozet tablosunda etiket sutunu YOK (dogrudan 7 yil x deger) - eski
  formatta da boyleydi.
- Ozet 7 satir: kayitli_secmen, oy_kullanan, katilim_orani, gecerli_oy
  (gumruk haric), gumruk_kapilari_gecerli_oy, TOPLAM_gecerli_oy (gumruk
  dahil), milletvekili_sayisi. "gecerli_oy" olarak TOPLAM (gumruk dahil)
  kullanilir - cunku parti oylari toplaminin esit oldugu rakam bu (dogrulandi:
  Ankara 2007 icin parti oylari toplami 2.459.587 = Toplam gecerli oy,
  2.442.927 (gumruksuz) DEGIL).
"""
import json
import pathlib
import sys

import pdfplumber

YEARS = ["2007", "2002", "1999", "1995", "1991", "1987", "1983"]

PDF_DIR = pathlib.Path(sys.argv[1])
OUT_PATH = pathlib.Path(sys.argv[2])


def to_int(s):
    s = (s or "").replace(".", "").strip()
    return int(s) if s else None


def to_float(s):
    s = (s or "").replace(",", ".").strip()
    return float(s) if s else None


def dedupe_doubled(s: str) -> str:
    """Bazi il PDF'lerinde parti etiketleri font/render hatasiyla her karakter
    2 kere basilmis sekilde geliyor (orn. 'DP' -> 'DDPP'). Sayisal hucreler
    etkilenmiyor, sadece bu metin sutunu."""
    def fix_word(w):
        if len(w) % 2 != 0 or len(w) < 2:
            return w
        if all(w[i] == w[i + 1] for i in range(0, len(w), 2)):
            return w[0::2]
        return w
    return " ".join(fix_word(w) for w in s.replace("\n", " ").split())


def parse_province_pdf(path: pathlib.Path):
    with pdfplumber.open(path) as pdf:
        first_page_tables = pdf.pages[0].extract_tables()
        if len(first_page_tables) != 2:
            raise ValueError(f"{path.name}: ilk sayfada beklenmeyen tablo sayisi {len(first_page_tables)}")
        summary = first_page_tables[0]
        if len(summary) != 7:
            raise ValueError(f"{path.name}: summary tablo 7 satir degil ({len(summary)})")

        parties_table = list(first_page_tables[1])
        for page in pdf.pages[1:]:
            tables = page.extract_tables()
            if len(tables) != 2:
                raise ValueError(f"{path.name}: sayfa {page.page_number}'de beklenmeyen tablo sayisi {len(tables)}")
            parties_table.extend(tables[1])

        kayitli, oy_kullanan, katilim, _gecerli_oy_gumruksuz, _gumruk, toplam_gecerli_oy, mv_sayisi = summary

        by_year = {}
        for i, year in enumerate(YEARS):
            by_year[year] = {
                "kayitli_secmen": to_int(kayitli[i]),
                "oy_kullanan": to_int(oy_kullanan[i]),
                "katilim_orani": to_float(katilim[i]),
                "gecerli_oy": to_int(toplam_gecerli_oy[i]),
                "milletvekili_sayisi": to_int(mv_sayisi[i]),
                "partiler": {},
            }

        current_party = None
        i = 0
        rows = parties_table
        while i < len(rows):
            row = rows[i]
            label0 = (row[0] or "").strip()
            if label0:
                label0 = dedupe_doubled(label0)
                if "(" in label0 and label0.endswith(")"):
                    current_party = label0.split("(")[-1].rstrip(")").strip()
                else:
                    current_party = label0.strip()
            stat = (row[1] or "").strip()
            values = row[2:2 + 7]
            if stat == "Alınan oy sayısı":
                oy_row = values
                oran_row = rows[i + 1][2:2 + 7]
                mv_row = rows[i + 2][2:2 + 7]
                for j, year in enumerate(YEARS):
                    oy = to_int(oy_row[j]) if j < len(oy_row) else None
                    if oy is None:
                        continue
                    by_year[year]["partiler"][current_party] = {
                        "oy": oy,
                        "oran": to_float(oran_row[j]) if j < len(oran_row) else None,
                        "mv": (to_int(mv_row[j]) if j < len(mv_row) else 0) or 0,
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
