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
| 0015450 | DİE, Milletvekili ve Cumhuriyet Senatosu Üyeleri Seçimi Sonuçları, 14 Ekim 1973 (1973) | 74-87 (karşılıklı sayfalar) |
| 0015631 | DİE, 5 Haziran 1977 Milletvekili Genel ve Cumhuriyet Senatosu Üyeleri Üçtebir Yenileme Seçimi Sonuçları (1977) | 82-93 (karşılıklı sayfalar) |

## Doğrulama (her seçimin kaynak katmanı dosyasında ayrıntılı)

| Seçim | İl | İlçe | Wikipedia il sonucuyla birebir | İlçe toplamı ≠ il toplamı (alan) |
|---|---|---|---|---|
| 1966senato | 23 | 220 | 20 / 22 karşılaştırılabilir il | 19 |
| 1968senato | 24 | 235 | 24 / 24 | 9 |
| 1973senato | 27 | 257 | 23 / 26 | 157 |
| 1977senato | 22 | 213 | 19 / 21 | 124 |

1973 ve 1977'de ilçe toplamının il toplamını tutmaması büyük ölçüde kaynağın
kendi özelliği: il toplamları Resmî Gazete ilanından, ilçeler birleştirme
tutanaklarından (1961-1987 TÜİK genel seçim verisinde de aynı durum var). Bu
iki yılın tablolarında partiler iki sayfaya bölünmüş; sağ sayfanın adsız
satırları sol sayfayla sırayla eşlendi. Basılı yüzdelerle iki kısıtı birden
sağlayan tek değerli OCR düzeltmeleri `ocrDuzeltme` alanında (okunan/düzeltilen).
Birkaç satırda basılı yüzdelerin toplamı %100'ü aşıyor (örn. 1973 Manavgat
%107); bunlar kaynak hatası olarak işaretli, düzeltilmedi.

- Satır içi kontrol (partiler + bağımsız = muteber) tutmayan satırlar düzeltilmedi,
  `kaynakIciTutarsizlik` ile işaretli. Örneğin 1966 Ankara'daki 51 oyluk fark
  Wikipedia'da da aynı; yani kaynağın kendisinde var.
- İlçe toplamı il toplamını tutmayan alanlar, il kaydının `dogrulanamayanAlanlar`
  listesinde (OCR ya da kaynak hatası; ayırt edilemedi).
- OCR'ın bozduğu ilçe adları aynı ilin bilinen ilçe adlarına en yakın eşleşmeyle
  ya da açık eşlemeyle düzeltildi; kaynaktaki yazım `adKaynakta`, düzeltme `adDuzeltme`.
