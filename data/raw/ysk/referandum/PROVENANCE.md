# 1961/1982/1987/1988 referandumları — YSK resmi il-bazlı PDF'leri

**Kaynak:** `https://www.ysk.gov.tr/tr/halkoylamasi-arsivi/2648` — her yılın
kendi doğrudan indirilebilir PDF'i (Angular sayfa değil, statik dosya).
2026-09-22'de indirildi.

- `1961.pdf` → `https://www.ysk.gov.tr/doc/dosyalar/docs/1961Referandum/9-Temmuz-1961-Halk-Oylamas%C4%B1.pdf`
- `1982.pdf` → `https://www.ysk.gov.tr/doc/dosyalar/docs/1982Referandum/7-Kas%C4%B1m-1982-Halk-Oylamas%C4%B1.pdf`
- `1987.pdf` → `https://www.ysk.gov.tr/doc/dosyalar/docs/1987Referandum/6-Eylul-1987-Halkoylamas%C4%B1.pdf`
- `1988.pdf` → `https://www.ysk.gov.tr/doc/dosyalar/docs/1988Referandum/25-Eylul-1988-Halk-Oylamas%C4%B1.pdf`
  (ayrıca 4 gümrük/sınır kapısı satırı içeriyor, `1988_parsed.json`'daki
  `gumruk` anahtarında — projeye entegre edilmedi, sadece referans)

Her biri tek, düz bir İL tablosu (67 satır — o dönemin il sayısı):
sandık sayısı, kayıtlı seçmen, katılan, geçerli/geçersiz oy, Evet/Hayır.
Sütun SIRASI yıldan yıla değişiyor (bkz. `../../../../scripts/
referandum-pipeline/parse_ysk_referandum_pdfs.py` — başlık adına göre okur,
sabit sütun indeksine güvenmez).

`*_parsed.json`: `parse_ysk_referandum_pdfs.py`'nin yapısal çıktısı.

## Doğrulama sonucu (2026-09-22)

`verify_and_merge_old_referandum.py`, projenin **önceden Wikipedia kaynaklı**
`data/normalized/referandumlar.json` kayıtlarını bu YSK PDF'leriyle
karşılaştırdı: **4 yıl × 67 il = 268 karşılaştırmanın tamamı** (seçmen,
geçerli oy, Evet, Hayır) **birebir eşleşti** — hiçbir değer değişmedi.
Eksik olan `sandik`/`gecersizOy` alanları (268 alan) YSK'den eklendi.
Bu, mevcut Wikipedia verisinin bu 4 yıl için zaten YSK kalitesinde
olduğunu doğruluyor — asıl kazanım kaynağın artık doğrudan, checksum'lı,
canlı bağımlılık olmayan YSK PDF'i olması.

## Bütünlük

`checksums.sha256` — 2026-09-22.
