# Türkiye Seçimleri (1950-2024) - Genel Seçim, Referandum, Yerel Seçim, Cumhurbaşkanlığı Veri Seti

## Harita: tarihsel idari sınırlar (2026-09-20 güncellemesi)

İnteraktif haritadaki (Artifact) il sınırları artık her seçim yılının **gerçek idari yapısını**
yansıtıyor. Sonradan il olan ilçeler — Uşak (1954), Sakarya/Adıyaman/Nevşehir (1954/1957),
Aksaray/Bayburt/Karaman/Kırıkkale/Batman/Şırnak/Bartın (1989–91), Ardahan/Iğdır/Karabük/Kilis/
Yalova (1992/1995), Osmaniye (1996), Düzce (1999) — o tarihlerden ÖNCEKİ seçim haritalarında ayrı/
boş bir bölge olarak görünmüyor; o dönem hangi ile bağlıysa (örn. Ardahan ve Iğdır 1992 öncesi
Kars'a bağlıydı) o ilin sınırına geometrik olarak birleştirilmiş gösteriliyor — zaten oy verisi
kaynakta bu şekilde (ana ile dahil) geldiği için bu, haritayı veriyle tutarlı hale getiriyor.
Bu düzeltme sadece **il (ülke) haritası** içindir; ilçe düzeyinde tarihsel sınır değişiklikleri
çok daha sık/karmaşık olduğu için kapsam dışı bırakıldı (ilçe haritaları güncel sınırları kullanır
— zaten 1950-1987 gibi ilçe verisi olmayan yıllarda ilçe haritası hiç gösterilmiyor).

Ayrı ana/yavru il eşleştirmesi (build_historical_geo.py'de tanımlı, web araştırmasıyla
doğrulandı): Uşak←Kütahya, Sakarya←Kocaeli, Adıyaman←Malatya, Nevşehir←Niğde, Aksaray←Niğde,
Bayburt←Gümüşhane, Karaman←Konya, Kırıkkale←Ankara, Batman←Siirt, Şırnak←Siirt, Bartın←Zonguldak,
Ardahan←Kars, Iğdır←Kars, Karabük←Zonguldak, Kilis←Gaziantep, Yalova←İstanbul, Osmaniye←Adana,
Düzce←Bolu.

**Düzeltildi (2026-09-20, 4. güncelleme):** 1954 genel seçim verisinde **Bilecik eksikti**
(63 il yerine gerçekte 64 olmalıydı — kaynak Wikipedia tablosunda satırı atlanmış). Bilecik'in
1954 sonucu (DP %54,6 - 35.346 oy, CHP %39,7 - 25.678, CMP %2,6 - 1.686, Bağımsız %3,1 - 2.659,
toplam 65.369 oy, 4 milletvekili) ayrı bir Wikipedia tablosundan (Bilecik ili genel seçim
sonuçları) bulunup eklendi.

**İlçe düzeyinde de aynı düzeltme (2026-09-20, 2. ve 3. güncelleme):** İl haritasındaki
birleştirmeye ek olarak, ilçe verisinde de aynı sorun vardı — örneğin 1991 genel seçiminde
(Ardahan/Iğdır henüz Kars'a bağlıyken) kaynak veri "Ardahan", "Göle", "Iğdır" gibi ilçeleri
doğru şekilde Kars'ın altında listeliyordu, ama modern ilçe-sınır kaydı bu ilçeleri artık
Ardahan/Iğdır illerinin plaka koduyla eşleştirdiği için harita eşleşmesi başarısız oluyordu.

Bunu iki katmanla düzelttim (historical_geo.py + build_ilce_historical_geo.py):
1. **İsim değişikliği / il değiştirme / eski-ana-il fallback'i**: Kazan→Kahramankazan, Eyüp→
   Eyüpsultan, Sincanlı→Sinanpaşa, Yenihisar→Didim, Akköy→Pamukkale, Kale→Demre, Aydınlar→
   Tillo, Devrakani→Devrekani (kaynak yazım hatası), İzmir Merkez→Konak, M.Kemalpaşa→
   Mustafakemalpaşa gibi saf ad değişiklikleri; Cizre/Silopi/İdil (Mardin'den), Uludere/
   Beytüşşebap/Güçlükonak (Hakkari/Siirt'ten) → Şırnak'a (1990), Gercüş (Mardin'den) →
   Batman'a (1990), Eskipazar/Ovacık (Çankırı'dan) → Karabük'e (1995), Cumaova→Cumayeri
   (1993) → Düzce'ye (1999) gibi il-değiştirmeler.
2. **Gerçek bölünmeler (poligon birleştirme, shapely ile)**: Kemalpaşa'nın 2017'de Hopa'dan
   ayrılması dahil, 12 ilin büyükşehir "Merkez" ilçesinin 2008-2014 arasında 2-4 ayrı ilçeye
   bölünmesi (Antalya→Muratpaşa+Kepez, Diyarbakır→Bağlar+Kayapınar+Sur+Yenişehir, Mersin→
   Akdeniz+Mezitli+Toroslar+Yenişehir, Samsun→Atakum+Canik+İlkadım+Tekkeköy, Şanlıurfa→
   Eyyübiye+Haliliye+Karaköprü, Erzurum→Yakutiye+Palandöken, Balıkesir/Eskişehir/Manisa/
   Malatya/Kahramanmaraş/Van'ın ikişer ilçesi) — bu yıllardan ÖNCEKİ haritalarda artık modern
   parça ilçeler yerine TEK birleşik bir poligon (`turkiye_ilce_sinirlari_hist_splits.geojson`)
   gösteriliyor, tıpkı il haritasındaki mantığın ilçe karşılığı gibi.

**Düzeltildi (2026-09-20, 4. güncelleme):** Erzurum'un **Ilıca** ilçesi 1990/91'de Merkez'den
ayrılmış, 2008'de (5747 sayılı kanun) Dadaşkent ile birleşip **Aziziye** adını almıştı — bu saf
ad değişikliği olarak eklendi. Geriye kalan Erzurum Merkez ise aynı kanunla **Yakutiye +
Palandöken** olarak ikiye bölündü — bu da yukarıdaki 12. bölünme olarak eklendi. Ayrıca
Hatay'ın **Samandağı** kaydı (kaynaktaki hal eki farkı — 1948'den beri var olan gerçek ilçe adı
"Samandağ") basit bir ad eşleştirmesiyle düzeltildi. İkisi de idari bir değişiklik değil, saf
kaynak/eşleştirme sorunuydu ve 1991-2007 arası genel seçimlerin ilçe eşleşmesini %100'e
çıkardı.

**Sonuç:** Tüm veri setindeki ilçe geometri eşleşmesi %92-96 aralığından **%99,85'e** çıktı
(21.876 ilçe kaydından sadece 33'ü eşleşmedi — kalanlar çoğunlukla 2010/2011 referandum ve
genel seçimindeki gümrük kapısı/havalimanı gibi zaten poligonu olmayan noktalar, ve Siirt'in
"Aydınlar/Tillo" ilçesi için kaynak coğrafi veride hiç sınır bulunmaması). İstanbul'un
**Eminönü/Fatih** sorunu da düzeltildi: 2008'de Eminönü'nün tüzel kişiliği kaldırılıp Fatih'e
katıldığı için, önceden ikisi de aynı (Fatih'in) poligonunu kullanıp görsel olarak üst üste
biniyordu; artık `merge_eminonu_fatih.py` ile 2008 öncesi yıllarda (1991-2007 genel, 1984-2004
yerel) Eminönü + Fatih oy verileri (oy/sandık/seçmen/katılım) TEK bir "Fatih" kaydında
birleştiriliyor, böylece hem harita hem de oy verisi tutarlı.

## Yurtdışı seçmen sonuçları (haritaya dahil değil)

- **yurtdisi_secmen_sonuclari.csv** — Konsolosluklarda kullanılan (hiçbir ile bağlı olmayan)
  oyların ayrı ulusal özeti. **Önemli:** yukarıdaki tüm il/ilçe dosyaları ve
  `1950_2023_tam_veri_seti.json`'daki `iller` listeleri SADECE yurt içi sonuçlardır — yurtdışı
  oylar hiçbir ile atanamadığı için (plaka/coğrafi karşılığı yok) haritaya/il toplamlarına HİÇ
  dahil edilmemiştir. Bu CSV o boşluğu ayrıca dolduruyor.
- Kapsam: yurtdışı konsolosluk oylaması sadece 2014'ten (ilk büyük ölçekli kullanım 2015'te)
  itibaren var ve sadece **milletvekili genel seçimi, referandum ve cumhurbaşkanlığı**
  seçimlerinde kullanılabiliyor — yerel seçimlerde YOK (ikamet adresine bağlı olduğu için).
  Veri seti 8 seçimi kapsıyor: 2015 Haziran, 2015 Kasım, 2018 ve 2023 genel seçim; 2017
  referandumu; 2018, 2023 (1. ve 2. tur) cumhurbaşkanlığı. 2011 ve öncesi genel seçimlerde
  henüz konsolosluk oylaması yoktu (sadece göçmen işçilerin gümrük kapılarında oy kullanması
  vardı, ihmal edilebilir düzeyde).
- **Ölçek:** 2023'te 3.416.086 kayıtlı yurtdışı seçmen (%49,58 katılım) — Türkiye'nin toplam
  seçmen sayısının ~%5'i. Yurtdışı oylar tarihsel olarak AK Parti/Erdoğan lehine yurt içine
  göre belirgin şekilde daha yüksek çıkıyor (örn. 2023 cumhurbaşkanlığı 1. turda Erdoğan
  yurtdışında %57,47 alırken yurt içi dahil resmi sonuç %49,52'ydi). Bu yüzden haritadaki/
  tablodaki "ulusal toplam" oranları her zaman **sadece yurt içi** olup resmî nihai sonuçtan
  (yurtdışı dahil) genelde AK Parti/Erdoğan aleyhine çok hafif (~0,2-0,5 puan) sapabilir.
  Sandık/geçerli-geçersiz oy dahil gerçek rakamlar kullanılmıştır, tahmin yoktur.
- **Kaynak:** secim.haberturk.com'un ayrı "Yurtdışı" sayfaları (genel seçimde `sehir/
  yurtdisi-251`, cumhurbaşkanlığı/referandumda `.../yurtdisi`).

## Cumhurbaşkanlığı seçimleri: 2014, 2018, 2023 (1. ve 2. tur)

- **2014_2018_2023_cumhurbaskanligi_il_sonuclari.csv** — Her adayın il bazında oyu, oranı ve
  kazanıp kazanmadığı. İlçe verisi (2018, 2023 için; 2014'te yok) tam JSON'da
  `secimler["2023cb2tur"].ilceler` vb. altında.
- 2023 1. tur: Erdoğan, Kılıçdaroğlu, Oğan, İnce (seçimden önce çekilmiş ama oyu sayılmış).
  2023 2. tur: sadece Erdoğan-Kılıçdaroğlu. 2018: Erdoğan, İnce, Akşener, Demirtaş,
  Karamollaoğlu, Perinçek. 2014: Erdoğan, İhsanoğlu, Demirtaş.
- 2014'te habertürk'te artık tam il/ilçe verisi yok (sadece harita üzerinde kısmi bilgi),
  o yüzden il bazında Türkçe Wikipedia'nın YSK kaynaklı tablosu kullanıldı — ilçe verisi
  bu yıl için mevcut değil.

## Yerel seçimler: 1984, 1989, 1994, 1999, 2004, 2009, 2014, 2019, 2024 (9 seçim)

- **1984_2024_yerel_secim_il_sonuclari.csv** — Her ilin (büyükşehirse büyükşehir, değilse
  il merkezi ilçesi) belediye başkanlığı yarışında yarışan her adayın oyu, oranı, partisi ve
  kazanıp kazanmadığı. İlçe bazlı veri `1950_2023_tam_veri_seti.json` içinde
  `secimler["2024yerel"].ilceler` vb. altında.
- Bu yarışlarda katılım oranı/seçmen sayısı kaynakta verilmiyor, sadece aday/parti/oy/oran var.
- **Kaynaklar:** 2014/2019/2024 secim.haberturk.com'dan (il+ilçe). 1984/1989/1994/1999/2009/2004
  habertürk'te artık erişilebilir değil (sayfalar kaldırılmış); bunun yerine Türkçe Wikipedia'nın
  il-başına alt makalelerinden (örn. "Ankara'da 2009 Türkiye yerel seçimleri" — büyükşehir/il
  merkezi + tüm ilçe belediye başkanlığı sonuçlarını içeren tablolar) derlendi. Bu 6 yılın
  hepsinde **81/81 (veya o yılın gerçek il sayısı: 1984/1989'da 67, 1994'te 76, 1999'da 80) il
  başlık yarışı bulundu** — ilk denemede bazı iller (özellikle Hatay/Kocaeli/Sakarya/İçel/
  Afyonkarahisar, çünkü il merkezinin adı ilin adından farklı: Antakya/İzmit/Adapazarı/Mersin/
  Afyon) kaçırılmıştı, script'teki bu özel durum düzeltildi ve tüm iller tekrar denenerek
  kurtarıldı. İlçe geometri eşleşmesi yıla göre ~%92-99 arasındadır (1984/1989'da bugünkünden
  daha az ilçe/belde olduğu için biraz daha düşük).
- **Tarihsel doğrulama:** 1984 ANAP 55/67 il (Özal'ın ilk yerel seçim zaferi), 1989 SHP 39/67
  (büyük şehirlerde sürpriz kazanım), 1994 RP 28/76 (İstanbul/Ankara dahil çıkış), 1999 MHP
  20/80 + FP 16/80 — hepsi bilinen siyasi tarihle örtüşüyor.

## Referandumlar: 1961, 1982, 1987, 1988, 2007, 2010, 2017 (7 halk oylaması)

- **1961_2017_referandum_il_sonuclari.csv** — Tüm 7 halk oylamasının il bazında Evet/Hayır
  oy, oran, kazanan taraf ve katılım oranı, tek dosyada.
- **1950_2023_tam_veri_seti.json** (aşağıda) tamamını içeriyor (`secimler["2017referandum"]`,
  `"2010referandum"`, `"2007referandum"`, `"1988referandum"`, `"1987referandum"`,
  `"1982referandum"`, `"1961referandum"`).

**Kaynaklar:**
- 2017 ve 2010 secim.haberturk.com'dan (il+ilçe); 2010'da kaynak sadece ilçe bazında
  oran+sandık sayısı verdiği için (gerçek oy sayısı yok), ilçe/il oy sayıları sandık başına
  ~300 oy varsayımıyla **kabaca tahmin edilmiştir** — yüzdeler gerçek, mutlak oy sayıları
  yaklaşıktır. Ulusal Evet/Hayır oranı için haberturk'ün kendi gösterdiği resmi rakam
  (%57,94 Evet) kullanılmıştır.
- 2007 il bazında Türkçe Wikipedia'nın YSK kaynaklı tablosundan (ilçe verisi bu kaynakta yok).
- **1961** (9 Temmuz, 1961 Anayasası), **1982** (7 Kasım, 1982 Anayasası — Kenan Evren'in
  cumhurbaşkanlığı seçimiyle birleşik oylama), **1987** (6 Eylül, siyasi yasakların
  kaldırılması — çok yakın sonuç, %50,2 Evet) ve **1988** (25 Eylül, yerel seçimlerin bir yıl
  öne alınması — reddedildi) referandumları habertürk'te hiç yok; il bazında Türkçe
  Wikipedia'nın YSK kaynaklı tablolarından alındı. Bu 4 referandumda kaynak tabloda gerçek oy
  sayıları (sandık, seçmen, geçerli/geçersiz oy dahil) mevcuttur — **tahmin yoktur**; ulusal
  toplamlar resmi rakamlarla test edildi (1982: %91,37/%8,63 birebir örtüşüyor; diğerleri
  ±0.1 puan içinde). Bu 4 referandumda da ilçe verisi yoktur (sadece il seviyesi).

## Genel seçimler: 1950-2023 arası 20 seçim (çok yıllı dosyalar)

- **1950_2023_tam_veri_seti.json** — 1950'den 2023'e tüm 20 genel seçimin tamamı; her biri
  için (kapsam sınırlarıyla birlikte, aşağıya bakın) il/ilçe bazında oy/oran/vekil. İnteraktif
  haritanın kullandığı ham veri budur.
- **1965_2023_il_vekil_dagilimi.csv** — Parti bazında vekil verisi olan 16 seçimin (1965-2023)
  düz (flat) CSV hâli: her satır bir (seçim yılı, il, parti) kombinasyonu — oy, oran, vekil sayısı.
  **Sadece vekil çıkaran partileri içerir.**
- **1991_2023_tum_partiler_il_sonuclari.csv** — Aynı 1991-2023 aralığı ama **baraj altı kalan
  küçük partiler ve bağımsızlar dahil TÜM partiler** (oy alan her parti, vekili olsun olmasın),
  il bazında oy/oran/vekil/kazandı mı. Belirli bir ilde bir küçük partinin gerçekte kaç oy
  aldığını görmek için bu dosyayı kullanın.
- **1965_2023_meclis_dagilimi_ozet.csv** — Bu 16 seçimde hangi parti kaç milletvekili çıkardı
  (ulusal toplam), tek bakışta karşılaştırma için.
- **1950_1961_genel_secim_il_oy_sonuclari.csv** — 1950/1954/1957/1961'in il bazında oy/oran/
  kazanan verisi (bu 4 seçimde vekil sütunu ayrıca **yok** — aşağıdaki kapsam notuna bakın).

**Veri kalitesi notu (2026-09-20 güncellemesi):** 1991-2023 arası il düzeyindeki parti kırılımı
başlangıçta sadece "büyük" (genelde vekil çıkaran, ~4-7) partiyi ayrı ayrı veriyordu; geri kalan
her şey tek bir "Diğer" sayısına sıkışıyordu (bazı illerde %20-40'lara varan büyüklükte). Bu artık
ilçe düzeyindeki (mertnuhoglu / haberturk kaynaklı) çok daha zengin parti kırılımı il seviyesine
toplanarak düzeltildi — "Diğer" artık çoğu il/yılda %1'in altına düştü ve gerçek küçük parti/
bağımsız adlarıyla gösteriliyor. Tek bilinen istisna: **Siirt, 2002** — incelendi (2026-09-20):
il düzeyindeki "Diğer" oranının kendisi (%60,5 — Wikipedia'nın YSK kaynaklı tablosuyla AK Parti/
CHP/MHP/DYP rakamları birebir örtüşüyor) aslında BİR HATA DEĞİL; bu yılın il-vekil kaynağı zaten
sadece 5 "büyük" partiyi ayrı tutup gerisini (DEHAP dahil, ki 2002'de Siirt'i açık farkla
kazanan parti oydu) "Diğer"e atıyor — bu yöntem TÜM illerde aynı (örn. Diyarbakır'da da "Diğer"
%67,7). Asıl gerçek veri boşluğu **ilçe düzeyinde**: mertnuhoglu kaynağındaki Siirt ilçe-parti
kırılımı (ilce_partiler.csv) bu il için bozuk — Merkez'de "AK Parti %86,71, DEHAP 0" gibi
gerçeklikle bağdaşmayan sayılar var (Wikipedia'nın "Siirt'te 2002 Türkiye genel seçimleri"
sayfasına göre DEHAP il genelinde %32,2 ile birinci, Merkez/Baykan/Kurtalan/Pervari'yi kazanan
parti). Güvenilir bir ilçe-bazlı alternatif kaynak bulunamadığı için ilçe verisi DÜZELTİLMEDİ
(yanlış ama var olan sayıları tutmak, doğrulanamayan tahmini sayılarla değiştirmekten daha
güvenli) — bu, veri setindeki tek bilinen ilçe-düzeyi veri kalitesi sorunu olarak kalıyor.
Ayrıca birden çok kaynağın aynı partiyi farklı
kısaltmayla verdiği durumlar (örn. "Saadet Partisi"/"SP", "Millet Partisi"/"MP", "BĞMSZ"/"BĞMZ")
tek bir kanonik ada birleştirildi; bazı kısaltmaların (örn. "AP", "DTP") farklı on yıllarda farklı
partilere ait olduğu tespit edilip karışmaması için ayrı anahtarlar kullanıldı (bkz. kod
yorumları: build_multi_year_bundle.py, cleanup_final.py).

**Kaynaklar ve yöntem:**
- 2011-2023 (5 seçim): secim.haberturk.com'un il/ilçe/parti sayfalarından kazınmış; her
  seçimin toplam vekil sayısı resmi sonuçla birebir doğrulanmıştır (600/550/550/550/550).
- 1991-2007 (5 seçim): İl bazında vekil/oy verisi Türkçe Wikipedia'nın YSK kaynaklı "İllere
  göre sonuçlar" tablolarından (hepsi resmi toplamla doğrulandı: 450/550/550/550/550); ilçe
  bazında oy verisi [mertnuhoglu/secim_verileri](https://github.com/mertnuhoglu/secim_verileri)
  derlemesinden alınmıştır. Bu dönemde habertürk'ün eski (1991-2007) arşiv sayfalarında
  Türkçe karakterli il isimlerinde bir sunucu hatası bulunduğu için o kaynak kullanılamadı.
- **1965, 1969, 1973, 1977, 1983, 1987 (6 seçim, haberturk'te yok):** İl bazında Türkçe
  Wikipedia'nın YSK kaynaklı tablolarından — bu yıllarda tabloda parti başına vekil sütunu da
  bulunduğu için tam sandalye dağılımı çıkarılabildi (her yılın toplamı resmi sonuçla
  doğrulandı: 450/450/450/450/399/450). **Bu 6 yılda ilçe verisi yoktur** (mertnuhoglu deposu
  bu döneme uzanmıyor) — sadece il seviyesi.
- **1950, 1954, 1957, 1961 (4 seçim):** Aynı şekilde Wikipedia'dan il bazında oy/oran alındı,
  ancak vekil verisi güvenilir şekilde çıkarılamadı: 1950'de kaynak tabloda vekil sütunu hiç
  yok (dönemin çoğunluk/blok liste sistemi); 1954 ve 1961'de sadece ilin TOPLAM sandalye
  büyüklüğü var, parti başına dağılım yok (1961 ayrıca o yıla özgü "millî bakiye" sistemiyle
  dağıtıldığından D'Hondt ile yeniden hesaplanamaz); 1957'de parti başına bir "Mv" sütunu
  görünüyor ama örneklem denetiminde iki en büyük parti için aynı (hatalı/tutarsız) değeri
  taşıdığı ve toplamının resmi 610 sandalyeyle uyuşmadığı tespit edildi. Bu 4 yıl için güvenilir
  olmayan sayıları yayımlamak yerine **sadece il bazında kazanan parti ve oy oranı** verildi;
  ilçe verisi de yoktur.
- Not: Türkiye'nin il sayısı zamanla arttı (1950/1954'te 63, 1957/1961-1987'de 67, 1991'de 74,
  1995'te 79, 1999'da 80, 2002'den itibaren 81) — her yılın kendi dönemine ait il listesi
  kullanılmıştır. Bazı iller isim değiştirdi (Afyon→Afyonkarahisar, İçel→Mersin, Seyhan→Adana,
  Çoruh→Artvin, Urfa→Şanlıurfa, Maraş→Kahramanmaraş) ve bu haritada modern isimlerine eşlendi.

---

# 2023 Türkiye Genel Seçimi (14 Mayıs) - Veri Seti (orijinal, tek yıl)

Kaynak: secim.haberturk.com (Habertürk'ün resmi YSK sonuçlarına dayanan seçim
sonuçları sitesi). Veriler 19 Eylül 2026 tarihinde bu siteden otomatik olarak
toplanmış, ardından parti bazlı sayfalardaki tam (81 ilin tamamını kapsayan)
tablolarla çapraz kontrol edilerek doğrulanmıştır. Toplam vekil sayısı 600
olarak doğru şekilde tutmaktadır (AK Parti 268, CHP 169, Yeşil Sol 61, MHP 50,
İYİ Parti 43, Yeniden Refah 5, TİP 4).

## Dosyalar

- **il_vekil_dagilimi.csv** — Asıl/doğru veri seti. 81 ilin her biri için,
  7 milletvekili çıkaran partinin (AK Parti, CHP, Yeşil Sol, MHP, İYİ Parti,
  Yeniden Refah, TİP) o ildeki oyu, oy oranı ve kazandığı milletvekili sayısı.
  Parti sayfalarındaki tam listeden alınmıştır (il sayfasındaki özet tablo
  sadece en çok oy alan 6 partiyi gösterdiği için İstanbul/Kocaeli/Konya gibi
  büyük illerde bazı vekillikleri kaçırıyordu — bu dosya o sorunu düzeltir).

- **il_ozet.csv** — İl bazında genel durum: toplam sandık, toplam seçmen,
  kullanılan oy, geçerli oy, katılım oranı.

- **il_partiler_top6_ozet.csv** — İl sayfalarındaki "OY DAĞILIMI" tablosunun
  ham hâli (yalnızca ildeki en çok oy alan 6 parti/liste). Hızlı özet için
  kullanışlı ama eksiksiz değildir; vekil sayıları için il_vekil_dagilimi.csv
  kullanın.

- **ilce_ozet.csv** — 973 ilçenin her biri için genel durum (sandık, seçmen,
  katılım vb.)

- **ilce_partiler.csv** — 973 ilçenin her birinde ~25 partinin aldığı oy ve
  oy oranı (milletvekilleri il bazında dağıtıldığı için ilçe düzeyinde vekil
  sayısı yoktur, sadece oy verisi vardır).

- **turkiye_il_sinirlari.geojson** — Türkiye'nin 81 ilinin sınır verisi
  (properties.plaka = il plaka kodu). HDX kaynaklı açık coğrafi veriden
  (ttezer/turkiye-harita-verisi deposu) alınıp web haritasında hafif kalması
  için basitleştirilmiştir (387.000 nokta -> 15.000 nokta, şekil sapması
  ortalama %0.2'nin altında).

- **turkiye_ilce_sinirlari.geojson** — Türkiye'nin 973 ilçesinin sınır verisi
  (properties.id = "TR-D-plaka-sira", properties.plaka = il plaka kodu). Aynı
  kaynaktan, aynı yöntemle basitleştirilmiştir (663.000 -> 73.500 nokta).
  ilce_ozet.csv / ilce_partiler.csv'deki ilçe adlarıyla eşleştirmek için
  ttezer deposunun districts.csv dosyasındaki isimler kullanılmıştır; 973
  ilçeden 972'si otomatik eşleşti, yalnızca Siirt'in "Aydınlar" ilçesi için
  sınır verisi bulunamadı (haritada o bölge boş/nötr görünür, oy verisi
  ilce_partiler.csv'de yine de mevcuttur).

## Kapsam ve sınırlamalar

- **Sandık (ballot box) düzeyinde ulusal/toplu veri bu sette YOKTUR.** YSK'nın
  açık veri portalı sandık bazlı sonuçları toplu ve makine-okunur biçimde
  yayımlamıyor; yalnızca PDF raporlar var. Tek kamuya açık sandık-bazlı örnek,
  gönüllülerin (Oy ve Ötesi) sadece Adana, İstanbul, İzmir ve Antalya'da
  topladığı, resmi olmayan ve eksik bir veri seti (github.com/egeakman/2023-oveo-data).
  İstersen bunu ayrıca ekleyebilirim.
- Bu yüzden pratik ve eksiksiz kapsam için il + ilçe düzeyinde durduk; bu,
  haberturk/hürriyet/vs. sitelerinin de gösterdiği en ayrıntılı kamuya açık
  düzeydir.
- Rakamlar YSK'nın kesinleşmiş sonuçlarını yansıtır (Habertürk sitesi "tahmini
  milletvekili" başlığını kullansa da 14 Mayıs 2023 sonrası kesinleşen resmi
  sayılarla birebir örtüşmektedir).
