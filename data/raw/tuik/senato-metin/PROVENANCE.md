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
| 0015147 | DİE, Milletvekili ve Senato Üyesi Seçimi Sonuçları, 15.10.1961 — İl, ilçe ve sandık bölgeleri itibariyle (1964) | 9-18 |
| 0015169 | DİE, Kısmi Senato Üyeleri Seçimi Sonuçları, 7 Haziran 1964 | 9-708 (özet tablo yok; sandık listelerinin "Toplam" / "İl Genel Toplamı" satırları; yalnız bu satırların sayfaları kaydedildi) |
| 0015213 | DİE, Cumhuriyet Senatosu Üyeleri Kısmi Seçim Sonuçları, 5 Haziran 1966 (1967) | 31-37 (senato), 38 (Hatay milletvekili ara seçimi) |
| 0015265 | DİE, Cumhuriyet Senatosu Üyeleri Kısmi Seçim Sonuçları, 2 Haziran 1968 (1969) | 20-25 |
| 0015450 | DİE, Milletvekili ve Cumhuriyet Senatosu Üyeleri Seçimi Sonuçları, 14 Ekim 1973 (1973) | 74-87 (karşılıklı sayfalar) |
| 0015581 | DİE, Cumhuriyet Senatosu Üyeleri ve Milletvekili Ara Seçim Sonuçları, 12 Ekim 1975 (1976) | 26-39 (karşılıklı sayfalar) |
| 0015789 | DİE, Cumhuriyet Senatosu Üyeleri Üçtebir Yenileme ve Milletvekili Ara Seçimi Sonuçları, 14 Ekim 1979 (1980) | 20-33 (karşılıklı sayfalar) |
| 0015631 | DİE, 5 Haziran 1977 Milletvekili Genel ve Cumhuriyet Senatosu Üyeleri Üçtebir Yenileme Seçimi Sonuçları (1977) | 82-93 (karşılıklı sayfalar) |

## Doğrulama (her seçimin kaynak katmanı dosyasında ayrıntılı)

| Seçim | İl | İlçe | Wikipedia il sonucuyla birebir | İlçe toplamı ≠ il toplamı (alan) |
|---|---|---|---|---|
| 1961senato | 52 tanındı (19'unun il değeri çözüldü) | 476 tanındı, 237'si çözüldü | 16 / 51 | — |
| 1964senato | 26 | 233 (145'i ek dosyada, bkz. aşağı) | 19 / 25 | 85 |
| 1966senato | 23 | 220 | 20 / 22 karşılaştırılabilir il | 19 |
| 1968senato | 24 | 235 | 24 / 24 | 9 |
| 1973senato | 27 | 257 | 23 / 26 | 157 |
| 1975senato | 25 | 257 | 23 / 23 | 116 |
| 1977senato | 22 | 213 | 19 / 21 | 124 |
| 1979senato | 25 | 241 | 21 / 25 | 101 |

1973 ve 1977'de ilçe toplamının il toplamını tutmaması büyük ölçüde kaynağın
kendi özelliği: il toplamları Resmî Gazete ilanından, ilçeler birleştirme
tutanaklarından (1961-1987 TÜİK genel seçim verisinde de aynı durum var). Bu
dönemin (1973-1979) tablolarında partiler iki sayfaya bölünmüş; sağ sayfanın
adsız satırları sol sayfayla sırayla eşlendi (satır sayıları tutmayan sayfalarda
sırayı koruyan, satır atlayabilen hizalama). Basılı yüzdelerle iki kısıtı birden
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

### 1964 özel durumu

1964 kitabında özet tablo yok. İlçe toplamı satırının adı yalnızca "Toplam",
hangi ilçeye ait olduğu sayfadaki başlıktan ("DİYADİN (Merkez)") anlaşılıyor ve
OCR bu başlıkların bir kısmını okuyamıyor. Ad iki yolla belirlendi: (1) ildeki
"Toplam" sayısı TÜİK 1965 ilçe sayısına eşitse DİE sırası (Merkez önce, sonra
alfabetik) ile, okunabilen başlıkların en az %80'i aynı sırayla uyuşuyorsa;
(2) başlığı okunup ilde tekil kalan satırlar. Bu yolla adı güvenle belli olan
145 ilçe `ek/senato/1964senato.json`'a girdi. Kalan 88 satır yalnızca kaynak
katmanında (`adGuvenli: false`). İl başlığı okunamayan il (Muş) ilçe adlarından
bulundu (`ilIlcelerdenBulundu`).

### 1961 özel durumu

1961 tablosunda milletvekili ve Senato sonuçları aynı satırda ve OCR bu kitapta
belirgin şekilde kötü (örn. "1 123" → "I 123"). Satırın kimliği etiketten değil,
ilk sayısının (seçmen) TÜİK 1961 kaynak katmanındaki DİE il/ilçe seçmen
sayısıyla eşleşmesinden bulundu. Milletvekili kısmı bilinen değerlerle tüketildi,
kalan Senato kısmı "partiler + bağımsız = muteber" kısıtıyla tek anlamlı bölündü
(fark en fazla 10 oy ya da %0,5 ise en yakın tek çözüm kabul edildi, fark
`kaynakIciTutarsizlik`'te). Bu yolla 237 ilçe güvenle çözüldü ve ek dosyaya girdi;
çözülemeyen 239 ilçe yalnızca kaynak katmanında. İl toplamlarının çoğu
çözülemediği için 1961 il sonuçlarında Wikipedia kaydı esas alınmalı.
