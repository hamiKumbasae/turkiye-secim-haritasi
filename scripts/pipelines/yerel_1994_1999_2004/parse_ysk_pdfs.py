"""
YSK'nin 1994/1999/2004 il-bazli "Belediye Baskanligi Secimi Sonuclari"
(normal iller) ve "Buyuksehir Belediye Baskanligi" (buyuksehir statusundeki
iller) PDF'lerini yapisal JSON'a cevirir.

Format (BelediyeBaskanligi, normal il):
  tek tablo, sutunlar: İlçe | Belediye | Sandık sayısı | Kayıtlı seçmen sayısı
  | Oy kullanan seçmen sayısı ve oranı (%) | Gecerli oy sayısı | <parti 1..N>
  Her "birim" (Turkiye / Il / Ilce-Merkez / her belde) 2 SATIR: deger satiri
  + oran satiri (oran satirinda ilk 6 sutun bos, sadece katilim%+parti%'leri
  var). Ilk 2 satir=Turkiye (ilce/belediye etiketi BOS), sonraki 2 satir=Il
  toplami (etiket yine BOS), 3. cift ("Ilce" sutunu ilk kez DOLU, deger =
  "Merkez") = il MERKEZININ kendi yarisi - bizim aradigimiz kayit budur.

Format (Buyuksehir):
  tek tablo, sutunlar: Belediye | Sandık sayısı | ... | <parti 1..N>.
  Ilk 2 satir (deger+oran, "Belediye" etiketi BOS) = BUYUKSEHIR TOPLAMI -
  bizim aradigimiz kayit budur (sonraki satirlar ilce kirilimini veriyor,
  bu turda kullanilmiyor).
"""
import json
import pathlib
import sys

import pdfplumber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from common.tr_numbers import to_int, to_float  # noqa: E402


def parse_belediye_pdf(path: pathlib.Path):
    """Normal (buyuksehir olmayan) il - 'Merkez' satirini doner."""
    with pdfplumber.open(path) as pdf:
        rows = []
        header = None
        for page in pdf.pages:
            for t in page.extract_tables():
                if not t:
                    continue
                if header is None:
                    header = t[0]
                    rows.extend(t[1:])
                else:
                    # tekrarlanan header'i atla (varsa)
                    body = t[1:] if t[0] == header else t
                    rows.extend(body)
        if header is None:
            raise ValueError(f"{path.name}: tablo bulunamadi")

        party_cols = header[6:]  # ilk 6 sutun: İlçe,Belediye,Sandık,Seçmen,OyKullanan,GecerliOy

        # Pozisyona (kacinci satir cifti) GUVENME - bazi yillarin PDF'lerinde
        # Turkiye/Il toplami satirlari arasinda degisken sayida bos ayrac
        # satiri var (sayfa gecisi kaynakli gibi gorunuyor). Bunun yerine
        # dogrudan "İlçe" sutunu "Merkez" ile BASLAYAN satiri ara - bu, il
        # merkezinin kendi yarisi (aradigimiz kayit). Hemen altindaki satir
        # o birimin oran satiridir.
        merkez_idx = None
        for idx, r in enumerate(rows):
            label = (r[0] or "").strip()
            if label.startswith("Merkez"):
                merkez_idx = idx
                break
        if merkez_idx is None or merkez_idx + 1 >= len(rows):
            raise ValueError(f"{path.name}: 'Merkez' ile baslayan satir bulunamadi")

        merkez_val, merkez_oran = rows[merkez_idx], rows[merkez_idx + 1]
        return extract_record(merkez_val, merkez_oran, party_cols)


def parse_buyuksehir_pdf(path: pathlib.Path):
    """Buyuksehir - ilk (toplam) satir ciftini doner."""
    with pdfplumber.open(path) as pdf:
        rows = []
        header = None
        for page in pdf.pages:
            for t in page.extract_tables():
                if not t:
                    continue
                if header is None:
                    header = t[0]
                    rows.extend(t[1:])
                else:
                    body = t[1:] if t[0] == header else t
                    rows.extend(body)
        if header is None:
            raise ValueError(f"{path.name}: tablo bulunamadi")
        party_cols = header[5:]  # Belediye,Sandık,Seçmen,OyKullanan,GecerliOy sonrasi
        if len(rows) < 2:
            raise ValueError(f"{path.name}: satir yetersiz")
        val_row, oran_row = rows[0], rows[1]
        return extract_record(val_row, oran_row, party_cols, offset=5)


def extract_record(val_row, oran_row, party_cols, offset=6):
    sandik = to_int(val_row[offset - 4])
    secmen = to_int(val_row[offset - 3])
    gecerli_oy = to_int(val_row[offset - 1])
    katilim = to_float(oran_row[offset - 2])

    partiler = {}
    for j, pname in enumerate(party_cols):
        pname = (pname or "").strip().replace("\n", " ")
        if not pname:
            continue
        oy = to_int(val_row[offset + j]) if offset + j < len(val_row) else None
        oran = to_float(oran_row[offset + j]) if offset + j < len(oran_row) else None
        if oy is None and oran is None:
            continue
        partiler[pname] = {"oy": oy or 0, "oran": oran}

    return {
        "sandik": sandik,
        "secmen": secmen,
        "gecerli_oy": gecerli_oy,
        "katilim_orani": katilim,
        "partiler": partiler,
    }


def main():
    year = sys.argv[1]
    mapping_path = pathlib.Path(sys.argv[2])
    pdf_root = pathlib.Path(sys.argv[3])
    out_path = pathlib.Path(sys.argv[4])

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))[year]

    result = {}
    errors = []
    for ad, info in mapping.items():
        kind = info["type"]
        fname = info["file"]
        subdir = "BelediyeBaskanligi" if kind == "belediye" else "Buyuksehir"
        path = pdf_root / year / subdir / f"{fname}.pdf"
        try:
            if kind == "belediye":
                result[ad] = parse_belediye_pdf(path)
            else:
                result[ad] = parse_buyuksehir_pdf(path)
            result[ad]["plaka"] = info.get("plaka")
            result[ad]["kind"] = kind
        except Exception as e:
            errors.append(f"{ad} ({path.name}): {e}")

    if errors:
        print(f"{len(errors)} HATA:")
        for e in errors:
            print(" ", e)
        raise SystemExit(1)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazildi: {out_path} ({len(result)} il)")


if __name__ == "__main__":
    main()
