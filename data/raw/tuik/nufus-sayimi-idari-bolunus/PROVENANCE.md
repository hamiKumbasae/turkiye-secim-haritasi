# DİE genel nüfus sayımı idari bölünüş kitapları (İstanbul sayfaları)

Kaynak: TÜİK (eski DİE) dijital kütüphanesi, `https://kutuphane.tuik.gov.tr/pdf/<no>.pdf`.
İndirilme: 2026-09-27. Kitapların tamamı depoya konmadı (toplam ~150 MB); aşağıdaki
dosyalar asıl PDF'ten `qpdf --pages` ile çıkarılan sayfalardır (kapak + İstanbul). Asıl
dosya URL'den indirilip SHA-256 ile doğrulanabilir.

| Dosya | Asıl yayın | Asıl PDF | Asıl SHA-256 | Alınan sayfalar (asıl PDF) |
|---|---|---|---|---|
| `1960_0015128_istanbul.pdf` | 23 Ekim 1960 Genel Nüfus Sayımı — İl, İlçe, Bucak ve Köyler | 0015128.pdf (658 s., 37.764.428 B) | `3e38c8d66e0bbfc7f07924a26c23b41b9ca1c17349428ef508ebd78c65060362` | 1, 345–351 |
| `1985_0013062_istanbul.pdf` | Genel Nüfus Sayımı İdari Bölünüş, 20.10.1985 | 0013062.pdf (724 s., 60.777.408 B) | `feb485f5f062cb24636f27f1791369bbce7dc252383a3bf4d28c059e67101ca7` | 1, 5, 383–388 |
| `1990_0013349_istanbul.pdf` | Genel Nüfus Sayımı İdari Bölünüş, 21.10.1990 | 0013349.pdf (628 s., 53.891.779 B) | `f4003db9584ddf4faa26519c8cc88139e54d4f4b9ef2c9f1eed50fcab99eab85` | 1, 328–333 |

İçerik: ilçe → bucak → köy muhtarlığı (ve belde, "(B)"; bucak merkezi "(BM)") nüfusları.
Şehir (il/ilçe merkezi belediyesi) içindeki mahalleler listelenmez.

Kullanım: `scripts/pipelines/historical_geo/build_mahalle_bolusumu.py` → `DONEMSEL`
(Arnavutköy'ün kaynak birimlerinin 1960, 1985, 1990 ilçe bağlılığı). Bulgular:
- Tayakadın 1960'ta Çatalca (Hadımköy bucağı), 1985'te Gaziosmanpaşa.
- Yeniköy 1960 ve 1985'te Çatalca (Hadımköy bucağı), 1990'da Gaziosmanpaşa.
- Arnavutköy, Boğazköy, Bolluca, Çilingir, Hacımaşlı, Haraççı, İmrahor, Ayazma (= Taşoluk,
  309 sayılı Kanun) 1960'ta Eyüp (Rami bucağı); 1985 ve 1990'da Gaziosmanpaşa.
- Hadımköy, Terkos (1985'te Durusu), Baklalı, Balaban(burun), Boyalık, Karaburun,
  Sazlıbosna, Dursunbey/Dursunköy, Yassıviran/Yassıören, Deliklikaya, Ömerli, Yeşilbayır:
  her üç sayımda Çatalca.

Tarama OCR metin katmanlı; kitap numaraları kütüphane PDF'lerinin ilk sayfa metni
okunarak (ilk ~300 KB, doğrusallaştırılmış PDF) bulundu.
