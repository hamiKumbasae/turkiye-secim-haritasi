# DİE — Mahalli İdareler Seçimi Sonuçları (taranmış kitaplar)

| Dosya | Yayın | Sayfa | Tablolar |
|---|---|---|---|
| `0012953.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 25.3.1984* (yayın no. 1109) | 162 | 1 İGM (ilçe) s.10-35 · 2 Büyükşehir (bağlı ilçe) s.38-39 · 3 Belediye başkanlığı (belediye) s.42-93 · 4 Belediye meclisi (belediye) s.96-147 · 5 Muhtarlık (kullanılmadı) |
| `0013623.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 27.3.1994* | 686 | 2 İGM il+ilçe+şehir/köy s.30-251 · 3 Büyükşehir s.252-261 · 4 Belediye başkanlığı s.262-473 · 5 Belediye meclisi s.474-685 |
| `0014361.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 18.4.1999* | 696 | 2 İGM s.38-239 · 3 Büyükşehir s.242-251 · 4 Belediye başkanlığı s.254-473 · 5 Belediye meclisi s.476-695 |
| `0018169.pdf` | DİE, *Mahalli İdareler Seçimi 28.03.2004* (yayın no. 2935, 2005) — **dijital dizgi, OCR değil** | 653 | 7 İGM il+ilçe+kent/kır s.110-253 · 8 Büyükşehir s.255-260 · 9 Belediye başkanlığı s.262-389 · 10 Belediye meclisi s.391-594 · Ek: kazanan başkanların listesi s.595- (henüz kullanılmadı) |
| `0013280.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 26.3.1989* | 300 | 1 İGM il 1984/1989 (kullanılmadı) · 2 İGM il+ilçe+şehir/köy s.17-115 · 3 Büyükşehir s.118-119 · 4 Belediye başkanlığı s.122-209 · 5 Belediye meclisi s.212-299 |

**Kaynak:** TÜİK Kütüphanesi (yordam kataloğu), `https://kutuphane.tuik.gov.tr/pdf/<demirbaş>.pdf`.
**İndirilme tarihi:** 2026-09-25. Dosyalar değiştirilmeden saklandı (checksum'lı).

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
- 1984 OCR'i zayıf: yüzdelerde ondalık noktası düşmüş ('4 1 3' = 41,3), '*' = 4, bazı tireler kayıp.
  Her satır parti toplamı = geçerli oy ve yüzde kısıtlarıyla doğrulanır; tutmayanlar `kontrol.durum = tutarsiz`.
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
