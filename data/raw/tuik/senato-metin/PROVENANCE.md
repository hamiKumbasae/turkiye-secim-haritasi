# DİE Cumhuriyet Senatosu seçim kitapları — sayfa metinleri

Kitaplar TÜİK kütüphanesinde tarandı ve OCR'lı PDF olarak duruyor
(`https://kutuphane.tuik.gov.tr/pdf/<demirbaş>.pdf`). 7-218 MB oldukları için
(GitHub 100 MB sınırı) depoya konmadı; her birinin sha256'sı ilgili kaynak
katmanı dosyasında (`data/kaynaklar/tuik/senato/<seçim>.json` → `pdfSha256`).
Bu klasörde yalnızca kullanılan tablo sayfalarının ham OCR metni var
(`<demirbaş>/<sayfa>.txt`); sayılar metinden değil **kelime koordinatlarından**
okundu (`scripts/pipelines/tuik_arsiv/die_tablo.py`), metin iz ve kontrol içindir.

| Demirbaş | Yayın | Kullanılan sayfalar |
|---|---|---|
| 0015213 | DİE, Cumhuriyet Senatosu Üyeleri Kısmi Seçim Sonuçları, 5 Haziran 1966 (1967) | 31-37 (senato), 38 (Hatay milletvekili ara seçimi) |
| 0015265 | DİE, Cumhuriyet Senatosu Üyeleri Kısmi Seçim Sonuçları, 2 Haziran 1968 (1969) | 20-25 |

## Doğrulama (her seçimin kaynak katmanı dosyasında ayrıntılı)

| Seçim | İl | İlçe | Wikipedia il sonucuyla birebir | İlçe toplamı ≠ il toplamı (alan) |
|---|---|---|---|---|
| 1966senato | 23 | 220 | 20 / 22 karşılaştırılabilir il | 19 |
| 1968senato | 24 | 235 | 24 / 24 | 9 |

- Satır içi kontrol (partiler + bağımsız = muteber) tutmayan satırlar düzeltilmedi,
  `kaynakIciTutarsizlik` ile işaretli. Örneğin 1966 Ankara'daki 51 oyluk fark
  Wikipedia'da da aynı; yani kaynağın kendisinde var.
- İlçe toplamı il toplamını tutmayan alanlar, il kaydının `dogrulanamayanAlanlar`
  listesinde (OCR ya da kaynak hatası; ayırt edilemedi).
- OCR'ın bozduğu ilçe adları aynı ilin bilinen ilçe adlarına en yakın eşleşmeyle
  ya da açık eşlemeyle düzeltildi; kaynaktaki yazım `adKaynakta`, düzeltme `adDuzeltme`.
