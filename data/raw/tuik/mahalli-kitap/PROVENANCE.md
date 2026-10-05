# DİE — Mahalli İdareler Seçimi Sonuçları (taranmış kitaplar)

| Dosya | Yayın | Sayfa | Tablolar |
|---|---|---|---|
| `0012953.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 25.3.1984* (yayın no. 1109) | 162 | 1 İGM (ilçe) s.10-35 · 2 Büyükşehir (bağlı ilçe) s.38-39 · 3 Belediye başkanlığı (belediye) s.42-93 · 4 Belediye meclisi (belediye) s.96-147 · 5 Muhtarlık (kullanılmadı) |
| `0013623.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 27.3.1994* | 686 | 2 İGM il+ilçe+şehir/köy s.30-251 · 3 Büyükşehir s.252-261 · 4 Belediye başkanlığı s.262-473 · 5 Belediye meclisi s.474-685 |
| `0014361.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 18.4.1999* | 696 | 2 İGM s.38-239 · 3 Büyükşehir s.242-251 · 4 Belediye başkanlığı s.254-473 · 5 Belediye meclisi s.476-695 |
| `0018169.pdf` | DİE, *Mahalli İdareler Seçimi 28.03.2004* (yayın no. 2935, 2005) — **dijital dizgi, OCR değil** | 653 | 7 İGM il+ilçe+kent/kır s.110-253 · 8 Büyükşehir s.255-260 · 9 Belediye başkanlığı s.262-389 · 10 Belediye meclisi s.391-594 · Ek: kazanan başkanların listesi s.595- (henüz kullanılmadı) |
| `0013280.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 26.3.1989* | 300 | 1 İGM il 1984/1989 (kullanılmadı) · 2 İGM il+ilçe+şehir/köy s.17-115 · 3 Büyükşehir s.118-119 · 4 Belediye başkanlığı s.122-209 · 5 Belediye meclisi s.212-299 |
| `0015160.pdf.parca0` + `.parca1` | DİE, *Mahalli Seçimler Sonuçları 17 Kasım 1963* (yayın no. 474, 1965) — **iki parçaya bölünmüş**, aşağıya bakın | 1796 | İl fasikülleri (sayfa no. `<il>/<sayfa>`, sürekli değil): A belediye başkanlığı · B belediye meclisi · C il genel meclisi · D muhtarlık. Ad/sandık/seçmen ve sonuçlar karşılıklı sayfalarda |
| `0015244.pdf` | DİE, *Mahalli Seçimler Sonuçları 2 Haziran 1968* (yayın no. 555, 1969) | 1512 | İl fasikülleri: A il genel meclisi · B belediye başkanlığı · C belediye meclisi · D muhtarlık; s.8-10 il toplamları |
| `0015468.pdf` | DİE, *Mahalli Seçimler Sonuçları 9 Aralık 1973* (yayın no. 716, 1974) | 224 | İGM (il, ilçe) · 3 belediye başkanlığı il toplamları s.44 · 4 belediye başkanlığı (belediye; kazanan başkanın adı) PDF s.52-133 · belediye meclisi. Muhtarlık ayrı yayında (depoda yok) |
| `0015740.pdf` | DİE, *Yerel Seçim Sonuçları 11 Aralık 1977* (1979) | 236 | 1 İGM (ilçe) s.1 · 2 belediye başkanlığı (belediye) s.39 · 3 belediye meclisi s.121 · 4 muhtarlık (ilçe) s.203 |

**Kaynak:** TÜİK Kütüphanesi (yordam kataloğu), `https://kutuphane.tuik.gov.tr/pdf/<demirbaş>.pdf`.
**İndirilme tarihi:** 2026-09-25 (1984–2004); 2026-10-05 (1963–1977, kullanıcının tarayıcısından; bağlantılar
Vikipedi il sayfalarının kaynakçasından). Dosyalar değiştirilmeden saklandı (checksum'lı).

### 1963–1977 kitapları (2026-10-05)

| Demirbaş | SHA-256 (bütün dosya) |
|---|---|
| 0015160 | `69a3a5cc06e8c44d1e14d74a6d33a1534f7a592fdead659acd356a7a0a231255` |
| 0015244 | `410b0907431e12225421a200c9e02855e7d617959a584c8bcdb15ab5bf92442e` |
| 0015468 | `c743edf57d2084625b9f78a30553f0eacbe42a4d7f484003a33a04cd92ef2e02` |
| 0015740 | `ff79d033b9b564f8d6f799e80cf71c94a84f3599b40aa0baeb6bc89d2199215b` |

- **1963 kitabı 120,7 MB**, GitHub'ın 100 MB dosya sınırını aşıyor. Bayt bayt iki parçaya bölündü
  (`split -b 90000000 -d -a 1`); içerik değişmedi. Birleştirmek ve SHA-256'yı doğrulamak için:
  `python3 scripts/pipelines/tuik_arsiv/kitap_birlestir.py` → `.cache/tuik/0015160.pdf`
  (elle: `cat 0015160.pdf.parca0 0015160.pdf.parca1 > 0015160.pdf`).
- Dört kitapta da taramanın metin katmanı var (ABBYY FineReader, 2009). Dört kitabın açıklaması da parti
  oyları toplamının geçerli oyla her yerde tutmadığını, DİE'nin birleştirme tutanaklarını düzeltmeden
  bastığını söylüyor.
- 1950 ve 1955 yerel seçimleri için DİE kitabı yok; Vikipedi sayfaları Başbakanlık Cumhuriyet Arşivi
  belgelerine (Fon 030.01, Yer No 52.312.7 / 51.309.3 / 51.309.8) ve gazetelere dayanıyor.
- Kullanım: depodaki 1963–1977 belediye başkanlığı kayıtları (Vikipedi) bu kitaplarla karşılaştırıldı —
  `scripts/pipelines/tuik_arsiv/kitap_dogrula_1963_1977.py` → `docs/rapor/KITAP_DOGRULAMA_1963_1977.md`.
  Belediye meclisi ve il genel meclisi tabloları henüz okunmadı.

Kitabın açıklamasına göre ilçe/belediye düzeyi değerler ilçe seçim kurullarının
DİE'ye gönderdiği birleştirme tutanaklarından değiştirilmeden alınmış; Türkiye
toplamları Resmî Gazete'deki YSK ilanından (1984: 26.5.1984/18412).

## Okuma

PDF'lerde taramanın OCR metin katmanı var (tesseract gerekmedi). Her tablo iki
yüzlü: sol sayfa (ad, sandık, seçmen, oy kullanan, katılım %, geçerli oy, ilk
partiler), sağ sayfa (kalan partiler, etiketsiz). Okuyucu:
`scripts/pipelines/tuik_arsiv/extract_mahalli.py` → `data/kaynaklar/tuik/yerel/<seçim>/<tablo>.json`.

Bilinen tarama kusurları:
- 1989 Tablo 2'nin ilk yaprakları karışık sırada taranmış: s.20+s.17, s.18+s.21 (script'te sabit).
- 1989'da kalın puntolu satırlarda OCR her karakteri iki kez yazmış ('776655' = 765) — geri çevrildi.
- 1984 OCR'i zayıf: yüzdelerde ondalık noktası düşmüş ('4 1 3' = 41,3), '*' = 4, bazı tireler kayıp,
  rakamlar yanlış ('386' → '366'); bazı sağ yüzler eğik/bükük taranmış (sağ altta sütun kayması 14 pt'ye çıkıyor).
  1984 artık ayrı okuyucuyla okunur — aşağıdaki "1984 — üç okumalı doğrulama" bölümü.
- 1984 belediye başkanlığı tablosunda Şanlıurfa'nın il satırı taramada yok (il sınırı ikinci MERKEZ satırından çıkarıldı).
- 2004 kitabı dijital: satır tipi etiket girintisinden (il kalın ~87, ilçe ~95, belde ~108; sayfanın
  'Municipality' başlığına göre), iki yüz satırları dikey ofsetle eşlenir. Türkçe harflerin bir kısmı
  metin katmanında yok ('Abdio lu') — ad eşlemesi bu yüzden benzerlikle yapılır.

## 1994 / 1999 (taranmış, iki satırlı kayıt) — doğrulamalı okuma

Okuyucu: `scripts/pipelines/tuik_arsiv/ocr_tablo.py` (genel) + `extract_mahalli_ocr.py` (kitap
ayarları, kimlik). Her kayıt sayı satırı + altındaki yüzde satırı. Kurallar:

- **Tahmin yok.** Okunamayan ya da doğrulanamayan hücre boş/işaretli kalır; toplamdan geri hesap yazılmaz.
- Alan bazında `dogrulama`: `katilim` (oy kullanan / seçmen = kitaptaki katılım %), `yuzde` (parti oyu /
  geçerli = kitaptaki %), `toplam` (parti oyları toplamı = geçerli). Satır durumu `tutarli` ancak hepsi tutarsa.
- Sütun kenarları sayfa başına değil **kitap şablonundan** + yatay ofset. İki şablon (sayı-sonu
  histogramı; düzenli sayfaların medyanı) her sayfa çiftinde denenir, kendi kısıtlarını sağlayan satırı
  çok olan okuma seçilir (seçim iç ölçüte dayanır; satırda `sablon`). Reddedilen: sayfa başlıklarının x'i
  (1999'da birkaç px sapıp değeri komşu sütuna itiyordu — YSK ölçümüyle görüldü).
- Yüzde/toplam kısıtları bir sütun kaymasını yakalayamıyor (değer ve yüzdesi birlikte kayar). Sağ kenarı
  sütun kenarından sütun aralığının %40'ından fazla uzak hücre `konumSupheli`; böyle satır `tutarli`
  sayılmaz (1999'da YSK'ye göre yanlış olan 4 tutarlı satırın 4'ünü de yakaladı).
- **Kimlik** (hangi belediye): YSK il arşivinde (sandık, seçmen) + oy kullanan ya da geçerli birebir;
  il bağlamı dışında dört alan birden; meclis tablosu başkanlık tablosuyla aynı sırada/seçmende;
  İGM'de şehir satırı ilçe merkezi belediyesidir; yazılı ad bilinen bir adla birebir. Hiçbiri yoksa
  `kimlik.yontem = cozulemedi` ve satır haritaya işlenmez.
- **Ölçüm:** başkanlık tablosu YSK'de de var; `tutarli` işaretli satırların tamamı YSK ile birebir —
  1994: 1668/1668 (20.854 alan), 1999: 1815/1815 (25.444 alan), 0 fark
  (bkz. `data/kaynaklar/tuik/yerel/<seçim>/dogrulama_raporu.json`).
- Sayfa kenarındaki bilinen tarama kusurları: kalın satırlarda karakterler iki kez ('KKüüççüükk'),
  tireler nokta/madde işareti olarak okunmuş, belde adlarının bir kısmı metin katmanında hiç yok.

## 1984 — üç okumalı doğrulama (2026-09-25)

Okuyucu: `scripts/pipelines/tuik_arsiv/extract_mahalli_1984.py`. Önceki okuma (`extract_mahalli.py`)
tek bir parti hücresi tutmayınca değeri toplamdan geri hesaplıyordu (`ocrDuzeltme`, 1984'te 328 satır
"tutarlı" işaretliydi); yeni okumayla karşılaştırıldığında bunların 75'i yanlıştı (ör. Savaştepe ANAP
1476 → 1478, Bakırköy SODEP 104648 → 104848). Yeni okuma:

- **Üç bağımsız okuma**, her hücre için aday: metin katmanı (ızgara, hücre dizgisi ve eski okuyucunun
  yapısal ayrıştırması), macOS Vision (`vision_ocr.swift`) ve tesseract (rakam beyaz listesi). Görüntü
  3 sütun genişliğinde, üst üste binen kısa karolara bölünerek okunur. Okumalar
  `data/kaynaklar/tuik/yerel/1984yerel/ocr/` altında saklı; okuyucu macOS/tesseract olmadan bunlardan
  aynı çıktıyı üretir.
- **Sütun sınırları sayfa başına çarpıklık modeliyle** (x, y'ye göre çift doğrusal) yerel; satır konumu
  satır grubunun medyan yüksekliği.
- **Tahmin yok:** hiçbir değer hesaplanmaz; çözüm yalnızca okunmuş adaylardan kurulur.
- **`tutarli`**: parti toplamı = geçerli oy, oyu olan her partinin kitaptaki yüzdesi (±0,1), katılım ve
  geçerli % (±0,05) tutuyor; öncü alanlardan biri satırın kendi metin katmanı ızgarasından; ve sıfır
  olmayan oy alanlarından (geçerli + partiler) **en fazla biri** tek okumaya dayanıyor (diğerleri iki
  motorla okunmuş ya da okunan yüzdeleriyle tek değere sabitlenmiş). Bu son kural, iki yanlış okumanın
  birbirini dengelediği çözümleri dışlar (ör. 1984 Van meclis: geçerli ve ANAP ikisi de 2000 eksik
  okunmuş, toplam tutuyordu). `teyitsiz` = kısıtlar sağlanıyor ama bu kural sağlanmıyor; `belirsiz` =
  birden çok çözüm; `tutarsiz` = çözüm yok. Yalnızca `tutarli` satırlar haritaya işlenir.
- **Karşılaştırma:** önceki okumanın (geri hesapsız) toplamla doğruladığı satırlardan yeniyle de
  tutarlı olan 1.867 satırın 1.866'sı birebir aynı; tek fark (Van) yeni okumada doğru. Örneklem sayfa
  görüntüsüyle gözle doğrulandı (12 satır, hepsi birebir).
- Sonuç (satır / tutarlı): İGM 711 / 552, büyükşehir 27 / 21, belediye başkanlığı 1759 / 1027,
  belediye meclisi 1760 / 1044.

## 1999 il genel meclisi — parti sütunu düzeltmesi (2026-09-27)

Tablonun sağ yüzünde DEHAP sütunu yok (15 sütun: DSP, DTP, DYP, DEPAR, EMEP, FP, HADEP, İP, LDP, MP,
MHP, ÖDP, SİP, YDP, Bağımsız; s.39 başlığı). Okuyucu belediye tablolarının 16 etiketli listesini
kullandığı için DSP oyları DEMTP, DTP oyları DYP, DYP oyları DEHAP diye yazılmıştı. YSK 1999 kesin
sonuç il toplamlarıyla karşılaştırmada 72/72 ilde aynı kayma görüldü; `extract_mahalli_ocr.py`'ye
tabloya özel sütun listesi eklenip tablo yeniden okundu (değerler aynı, 2.997/3.000 satır birebir;
yalnız etiketler ve 5 satırın doğrulama durumu değişti). Düzeltmeden sonra YSK ile 72/72 il birebir.
