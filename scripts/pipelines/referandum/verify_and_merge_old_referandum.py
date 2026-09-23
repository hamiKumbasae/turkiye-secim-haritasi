"""
1961/1982/1987/1988 halkoylamalarinin data/normalized/referandumlar.json'daki
KAYITLARINI (Wikipedia kaynakli) YSK'nin resmi il-bazli PDF'leriyle (bkz.
data/raw/ysk/referandum/parse_ysk_referandum_pdfs.py ciktisi) karsilastirir.

Deger DEGISTIRMEZ (bu 4 yil icin mevcut verinin zaten YSK ile birebir
ayni oldugu dogrulandi) — sadece:
  1. Her il/yil icin tam eslesme olup olmadigini raporlar (yoksa DURUR).
  2. Eksik olan 'sandik'/'gecersizOy' alanlarini YSK'den ekler.

Kullanim:
  python3 verify_and_merge_old_referandum.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

YSK_DIR = ROOT / "data" / "raw" / "ysk" / "referandum"

YEARS = {"1961referandum": "1961", "1982referandum": "1982", "1987referandum": "1987", "1988referandum": "1988"}


def turkish_upper(s: str) -> str:
    # Python'un varsayilan .upper()'i Turkce'ye ozgu i/I ayrimini bilmiyor
    # (orn. "izmir".upper() -> "IZMIR" degil "İZMİR" olmali) — YSK'nin
    # PDF'lerindeki il adlariyla eslesmek icin elle cevriliyor.
    return s.replace("i", "İ").replace("ı", "I").upper()


def main():
    secimler = {k: load_election(k) for k in YEARS}
    all_ok = True
    updated_fields = 0

    for proj_key, ysk_year in YEARS.items():
        parsed_path = YSK_DIR / f"{ysk_year}_parsed.json"
        ysk = json.loads(parsed_path.read_text(encoding="utf-8"))["iller"]

        secim = secimler[proj_key]
        for il in secim["iller"]:
            ysk_il = ysk.get(turkish_upper(il["ad"]))
            if ysk_il is None:
                print(f"UYARI {proj_key}: '{il['ad']}' YSK PDF'inde bulunamadı")
                all_ok = False
                continue

            # deger karsilastirma (degistirmiyoruz, sadece dogruluyoruz)
            checks = [
                ("secmen", il.get("secmen"), ysk_il["kayitli_secmen"]),
                ("gecerliOy", il.get("gecerliOy"), ysk_il["gecerli_oy"]),
                ("evet", il["oy"].get("Evet", {}).get("oy"), ysk_il["evet"]),
                ("hayir", il["oy"].get("Hayır", {}).get("oy"), ysk_il["hayir"]),
            ]
            for field, ours, ysk_val in checks:
                if ours != ysk_val:
                    print(f"FARK {proj_key}/{il['ad']}/{field}: bizim={ours} YSK={ysk_val}")
                    all_ok = False

            # eksik alanlari ekle (deger degistirmiyor, sadece daha once
            # projede olmayan sandik/gecersizOy alanlarini YSK'den dolduruyor)
            if il.get("sandik") != ysk_il["sandik"] and ysk_il["sandik"] is not None:
                il["sandik"] = ysk_il["sandik"]
                updated_fields += 1
            if "gecersizOy" not in il and ysk_il["gecersiz_oy"] is not None:
                il["gecersizOy"] = ysk_il["gecersiz_oy"]
                updated_fields += 1

    if not all_ok:
        print("\nBAZI FARKLAR VAR — yukarida listelendi. Hicbir sey yazilmadi.")
        sys.exit(1)

    for proj_key in YEARS:
        save_election(proj_key, secimler[proj_key])
    print(f"\nTüm 4 yıl × 67 il TAM EŞLEŞTİ (secmen/gecerliOy/evet/hayir). "
          f"{updated_fields} alan (sandik/gecersizOy) YSK'den eklendi/güncellendi.")


if __name__ == "__main__":
    main()
