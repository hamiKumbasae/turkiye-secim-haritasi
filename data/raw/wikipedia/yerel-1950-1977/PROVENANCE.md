# 1950-1977 yerel seçimleri — il merkezi, Türkçe Wikipedia

`data/normalized/yerel_secimler.json`'daki `1950yerel`, `1955yerel`,
`1963yerel`, `1968yerel`, `1973yerel`, `1977yerel` anahtarlarının **ham**
kaynağı — 2026-09-22'de eklendi (bkz. [`../../../../SECIM_TAKVIMI.md`](../../../../SECIM_TAKVIMI.md)).

## Ne bu dosyalar

Her `yerel_<yıl>.json`, o yılın **il merkezlerinin** (Adana, Ankara, ... —
ilçeler DEĞİL) kendi belediye başkanlığı yarışı sonuçlarını, Türkçe
Wikipedia'nın il-bazlı alt makalelerinden (`<İl>'da <yıl> Türkiye yerel
seçimleri`, MediaWiki API'den ham wikitext olarak çekildi) çıkarılmış hâliyle
tutar — `data/normalized/yerel_secimler.json`'a işlenmeden ÖNCEKİ hâli
(her kayıtta `kaynak_url` ve varsa özel durum notları `not` alanında).

## Neden PDF değil de bu JSON'lar "raw"

YSK'nin 1950-1977 GENEL seçim arşivinin aksine (bkz.
`data/raw/ysk/1950-1977/`), YSK'nin bu dönem için MAHALLİ İDARELER
seçimlerinde sadece ULUSAL toplam PDF'i var (`data/raw/ysk/mahalli-1963-1977/`),
il-bazlı PDF yok — doğrulandı, bkz. aşağı. Tek il-bazlı kaynak Wikipedia,
ki bu **değişebilir** (statik bir PDF değil) — bu yüzden 2026-09-22'de
çekildiği hâliyle bir anlık görüntü (snapshot) burada saklanıyor, gelecekte
Wikipedia'nın kendisi değişse bile bu depodaki sayının nereden geldiği
yeniden üretilebilir kalsın diye.

## Yöntem özeti

1. `data/secim_takvimi.json` için 1950-2024 arası TÜM Türkiye seçimlerinin
   tam takvimi çıkarılırken, `yerel_secimler.json`'un 1984 öncesini hiç
   kapsamadığı (6 seçim: 1950/1955/1963/1968/1973/1977) tespit edildi.
2. YSK'nin resmi arşivi kontrol edildi
   (`www.ysk.gov.tr/tr/mahalli-idareler-genel-secimleri-arsivi/2650`,
   Playwright ile render edilerek): 1963/1968/1973/1977 için "Kesin Seçim
   Sonuçları" PDF'leri VAR ama sadece ULUSAL toplam (il kırılımı yok) —
   indirilip `data/raw/ysk/mahalli-1963-1977/`'e kondu. 1950/1955 için bu
   arşivde hiçbir PDF yok.
3. Türkçe Wikipedia'nın ana yıl makaleleri (`1963/1968/1973/1977 Türkiye
   yerel seçimleri`) il-bazlı "hangi parti kazandı" KARŞILAŞTIRMA
   tablosu içeriyor (67 il, iki ardışık yıl yan yana) — bu, 4 arka plan
   ajanının kendi il-alt-makale çıkarımını çapraz kontrol etmesi için
   kullanıldı (`sources.yml`'deki `verification` alanlarına bakın).
   1950/1955 ana makalelerinde böyle bir tablo YOK (sadece ulusal toplam).
4. Her yıl için ayrı bir arka plan ajanı, o yılın ~63-67 il alt makalesini
   MediaWiki API'sinden (`action=query&prop=revisions&...&titles=A|B|C...`,
   toplu istekle, ~2 çağrıda tüm iller) ham wikitext olarak çekti, kendi
   yazdığı bir Python parser ile `==<İl> Merkez==` başlığı altındaki
   İL MERKEZİNİN kendi tablosunu ayrıştırdı (diğer ilçelerin tabloları
   kasıtlı olarak atlandı — kapsam dışı, `ilceler` boş bırakıldı).
5. Çıkan 6 JSON, bu klasöre kopyalanıp (ham hâliyle, değiştirilmeden)
   `data/normalized/yerel_secimler.json`'a işlendi (parti anahtarları
   `partiler.json`'a eşlendi, 4 yeni parti — TSİP/SDP/MKP/KARMA — eklendi).

## Bilinen sınırlar (her dosyanın kendi içindeki `not`/`log` alanlarında da var)

- **Sadece il merkezi** — ilçeler (örn. Adıyaman'ın Besni'si) bu 6 yılda YOK.
  1984+ verisinde ilçeler var, çünkü o dönemin il alt makaleleri de tarandı
  (farklı bir oturumda) — bu 6 yıl için henüz yapılmadı.
- **1950/1955**: Belediye başkanı halk tarafından doğrudan değil, meclisin
  kendi içinden seçiliyordu — çoğu ilde gerçek oy sayısı yerine meclis
  sandalye dağılımı var (`oy`/`oran` null, `sandalye`/`oranSandalye` dolu).
- **1963 İstanbul**: Bilinen bir diskalifiye vakası (AP adayı en çok oyu
  aldı ama usulden diskalifiye edildi, mazbata CHP'ye verildi) —
  `kazanan`=CHP (resmi/nihai), ham oy sayıları orijinal (iptal edilmemiş).
- Katılım oranı (`katilim`) hemen hiçbir ilde kaynakta açık verilmediği
  için neredeyse tamamen `null`.
- Kaynak Wikipedia'nın kendi iç tutarsızlıkları (birkaç ilde parti oyları
  toplamı ile sayfanın "Toplam" satırı arasında küçük farklar) düzeltilmedi,
  sadece ilgili kaydın `not` alanında belgelendi.

## Doğrulama durumu

`sources.yml`'nin YSK/TÜİK birincil kaynakla **henüz** çapraz doğrulanmadığı
bir katman — projenin geri kalanındaki (`data/raw/ysk/1950-1977/` gibi)
resmi PDF-kaynaklı verilerle AYNI titizlik seviyesinde değil. İleride resmi
bir kaynak bulunursa (örn. YSK'nin il-bazlı bir arşivi ortaya çıkarsa) bu
veri onunla çapraz kontrol edilip gerekirse değiştirilmeli.
