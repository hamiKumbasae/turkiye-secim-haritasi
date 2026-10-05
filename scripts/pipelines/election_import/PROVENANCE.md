# Habertürk → YSK Açık Veri Portalı geçişi (2026-09-22, üçüncü oturum)

Kullanıcının isteği üzerine: "Habertürk verisini silsek o verileri YSK'de
bulamıyor muyuz?" — cevap evet, ve bu klasördeki pipeline tam olarak bunu
yapıyor: Habertürk'ün primary kaynak olduğu 15 seçimin **il VE ilçe düzeyi**
verisini, YSK'nin kendi resmi `acikveri.ysk.gov.tr` API'sinden **sandık
düzeyinde çekip agrege ederek** yeniden üretiyor — Habertürk tamamen devre
dışı kalıyor.

## Neden bu daha önce yapılmamıştı

Proje zaten `scripts/pipelines/mahalle_veri/` ile bu API'yi kullanıyordu, ama
sadece **mahalle (muhtarlık) düzeyi** için — ve mahalle özelliği, poligon
GEOMETRİSİ olan ilçelerle sınırlı (578-651 / 973 ilçe, mahalle sınırı
kaynaklarının kapsamına göre). Bu pipeline'ın kritik farkı: **il/ilçe
düzeyinde poligon kısıtı yok** — haritanın il/ilçe sınırları zaten eksiksiz
(973 ilçe, ayrı bir geometri kaynağından). Yani sadece SAYI toplamak için
mahalle özelliğinin kapsam sınırına tabi değiliz — YSK'nin `getIlceList`
uç noktasından **TÜM** ~998 ilçenin resmi ID'sini çekip her biri için ayrı
ayrı sorgulayabiliyoruz.

## Yöntem

1. **`fetch_il_ilce_list.js`** — `getIlceList?ilId=X` ile 81 il için TÜM
   ilçe ID'lerini çeker (998 ilçe, poligon kısıtı yok) →
   `data/raw/ysk/acikveri-il-ilce-listesi.json`.
2. **`match_ilce_geomid.py`** — Bu 998 ilçeyi, projenin kendi 973-ilçelik
   güncel listesiyle (genel_secimler.json "2023") isim+plaka bazında
   eşleştirir → `data/raw/ysk/acikveri-ilce-geomid-eslemesi.json`. ~974-980
   eşleşiyor; kalan ~18-24'ü ya (a) 2014-2017 büyükşehir bölünmeleri öncesi
   artık kullanılmayan eski "**<İl> MERKEZ**" ID'leri (bazıları `hist_geomid.py`
   ile `geo/historical/district_splits.json`'daki sentetik HIST-*-Merkez
   geomId'lere çözülüyor, kalanlar projenin zaten bilinen bir kapsam
   sınırı — bkz. her seçimin kendi `known_issues`'ı) ya da (b) gerçekten
   OY VERİSİ OLMAYAN boş plasman kayıtları (doğrulandı — örn. "Antalya
   Merkez" 2023 için 0 sandık döndürüyor, oylar zaten modern ilçelere
   dağılmış).
3. **`getSandikSecimSonucBaslikList`** ile her seçimin parti/aday →
   `partiN_ALDIGI_OY` sütun eşlemesi çekildi (bazıları
   `scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/`'de zaten vardı,
   bu oturumda eksik 6'sı — 2014cb/2018cb/2023cb1tur/2023cb2tur/
   2010referandum/2017referandum — eklendi).
4. **`fetch_and_aggregate.js <label> <secimId> <secimTuru> <baslikDosyasi>`**
   — 998 ilçenin HER biri için `getSecimSandikSonucList` çağrılır (sandık
   düzeyinde ham veri), dönen TÜM sandık satırları o ilçe için toplanır
   (secmen/geçerli/geçersiz/parti oyları) — bu **tahmini/örneklem DEĞİL,
   o ilçenin kayıtlı TÜM sandıklarının tam toplamı**. İlçe toplamları
   kendi ili altında tekrar toplanarak il toplamı elde edilir. Çıktı:
   `.work/<label>_agrege.json` (gitignore'da, ara dosya). Resumable —
   her 20 ilçede bir `.work/<label>_progress.json`'a checkpoint yazılır.
5. **`merge_referandum.py` / `merge_genel.py` / `merge_yerel.py` /
   `merge_cb.py`** (tür-özel) — agrege JSON'u ilgili
   `data/normalized/*.json` dosyasına işler, Habertürk kaynaklı `iller`/
   `ilceler`'in YERİNE geçer.

## Doğrulama

Her seçim için: (a) parti/aday oyları toplamının resmi geçerli oy sayısıyla
eşleşmesi, (b) en az bir tanıdık il (genelde Ankara) için mevcut/eski
veriyle çapraz karşılaştırma, (c) ulusal toplamın bilinen resmi sonuçla
uyumu. Ayrıntılar her seçimin kendi `sources.yml` girişinde.

## Yerel seçimlerde bulunan iki bug ve düzeltmeleri (2026-09-23, dördüncü oturum)

2009/2014/2019/2024 yerel seçimleri ilk geçişte yukarıdaki genel yöntemle
(adım 3-5'te `fetch_and_aggregate.js` + `merge_genel_yerel.py`) işlendi, ama
doğrulama sırasında iki ayrı ciddi sorun bulundu:

**Bug 1 — eksik önbellekli `baslik_*.json` → oy sessizce düşüyordu.**
`scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/baslik_2014yerel.json`
(daha önceki bir oturumdan kalma, farklı bir amaç için çekilmiş önbellek)
sadece 18 satır içeriyordu ve BDP'nin sütununu (`parti20`) hiç barındırmıyordu.
`fetch_and_aggregate.js`'in `relevantCols` listesi bu dosyadan türetildiği
için, BDP sütunundaki gerçek oylar YANLIŞ eşlenmiyor, tamamen TOPLANMIYORDU —
Diyarbakır 2014'te "AK Parti kazandı" (%87) gibi tarihsel gerçekle çelişen bir
sonuç üretti (oysa BDP'nin adayı Gültan Kışanak o büyükşehir seçimini gerçekte
kazanmıştı). Düzeltme: **`refresh_all_baslik.js`** yazıldı, tüm 15 seçim için
`getSandikSecimSonucBaslikList` canlı yeniden çekildi; sadece 4 yerel
seçimin baslik dosyası gerçekten eksikti (genel/CB/referandum ya zaten
tamdı ya da eksik olan sütunlar zararsız "bağımsız aday" tekrarlarıydı).

**Bug 2 — "il" kaydı yanlış modelleniyordu (ilçe yarışları büyükşehir
yarışıyla karıştırılıyordu).** Bug 1 düzeltildikten SONRA bile İstanbul
2019 hâlâ yanlıştı (AKP %45,9/CHP %40,3 — gerçekte neredeyse berabere bir
seçimdi, CHP %48,65/AKP %48,79). Kök neden: yerel seçimlerde HER idari
birimin (ilçe, ve büyükşehirse ayrıca bütün büyükşehirin) KENDİ AYRI bir
yarışı var; `fetch_and_aggregate.js`'in "ile ait tüm ilçeleri topla"
yaklaşımı bu ayrı yarışları anlamsız bir havuzda birleştiriyordu — hiçbir
gerçek seçimi yansıtmıyordu. API testiyle doğrulandı: `secimTuru=6`
(ilçeId boş) sorgusu büyükşehir statüsündeki iller için doğru
büyükşehir-geneli yarışı ilçe kırılımlı döndürüyor (İstanbul: CHP
%48,77/AKP %48,61 — gerçeğe çok yakın), büyükşehir OLMAYAN iller için
0 satır döndürüyor (güvenilir bir otomatik tespit sinyali). Düzeltme:
**`fetch_yerel_v2.js` + `merge_yerel_v2.py`** yazıldı — büyükşehir
illerde `secimTuru=6` (ilçeId boş) agregesi, diğerlerinde sadece
"`<İl> MERKEZ`" ilçesinin `secimTuru=2` sonucu "il" kaydı olarak
kullanılıyor (1950-1977/1994-2004 pipeline'larındaki "il kaydı = merkezin
kendi yarışı" kuralıyla aynı); "ilçeler" ise her zaman ilgili ilçenin
kendi ayrı `secimTuru=2` sonucu. Tüm 4 yıl yeniden çekilip birleştirildi,
bilinen sonuçlara karşı doğrulandı (İstanbul/Ankara 2024 CHP kazandı,
İstanbul 2019 başa baş, İstanbul 2014 AKP kazandı, Diyarbakır'da
BDP/DTP hâkimiyeti).

**Genel seçim vekil/sandalye alanı korunması.** `merge_genel_yerel.py`'nin
`build_record()` fonksiyonu ilk sürümde `toplamVekil`/`vekil` alanlarını
`0`/`{}` olarak sabitliyordu (sandık-düzeyi oy API'si sandalye dağılımı
içermiyor). Bu, 2011/2015Haziran/2015Kasım/2018/2023'ün önceki
(Habertürk kaynaklı, doğru) il-bazlı sandalye verisini SİLİYORDU. Düzeltme:
migrasyon öncesi (`git show HEAD:...`) kayıtlardan plaka bazında
`vekil`/`toplamVekil` geri yüklendi (oy/seçmen/sandık alanları YSK'den,
sandalye dağılımı eski doğrulanmış kaynaktan — ikisi karışık değil, ayrı
alanlar); fonksiyon artık bu alanları parametre olarak kabul edip
koruyor, gelecekte tekrar sıfırlanmaz.

## Yurtdışı seçmen paneli (2026-09-23, dördüncü oturum)

Kullanıcının "Habertürk kalıntısı istisnaları da çöz" talimatı üzerine, tek
kalan Habertürk-birincil veri (8 seçimin "yurtdışı" alt-paneli, hiçbir ile
atanmayan temsilcilik/konsolosluk sandıkları) de YSK'ye taşınmaya çalışıldı.

**Keşif:** `getSecimSandikSonucList`'i `yurtIciDisi=2` + boş `ilId` ile
sorgulamak, YSK'nin kendisinin hazırladığı 2 agrege satır döndürüyor:
"ÜLKELER SANDIKLAR TOPLAMI" (büyükelçilik/konsolosluk sandıkları — projenin
"yurtdışı" panelinin zaten temsil ettiği kategori) ve "GÜMRÜK KAPILARI
SANDIKLAR TOPLAMI" (sınır kapısı sandıkları — proje şu ana kadar hiç
kullanmadı, kullanmaya da devam etmiyor, 1988 referandumundaki aynı isimli
kategoriyle aynı "haritaya dahil etme" konvansiyonu). "ÜLKELER" satırının
`gecerli_OY_TOPLAMI`/`oy_KULLANAN_SECMEN_SAYISI`/parti sütunları 2018 için
Habertürk'ün mevcut rakamlarıyla (1.340.685 geçerli oy, 1.357.204 kullanan)
birebir eşleşti — güvenilir.

**Başarısız/atlanan 3 seçim:** 2023 genel, 2023cb1tur, 2023cb2tur için bu
agrege satır `secmen_SAYISI=0` dönüyor (boş) — birkaç `sorguTuru`/`yurtIciDisi`
varyantı denendi, hiçbiri veri vermedi; `getSecimDetayList`'te seçimin
kendisi var ama bu özel özet hesaplanmamış görünüyor. Bu 3 seçim Habertürk
kaynağında kaldı.

**"secmen"/"katilim"/"sandik" alanları neden güncellenmedi:** "ÜLKELER"
agrege satırının `secmen_SAYISI` alanı YANILTICI — gerçek kayıtlı seçmen
sayısı değil, `oy_KULLANAN_SECMEN_SAYISI` ile birebir aynı (yani bu özel
toplam satırında anlamlı doldurulmamış). Doğru kayıtlı seçmen sayısını almak
için `disTemsilcilikId` bazında gerçek (ham) sandık satırlarını tek tek
çekip toplama denendi (`fetch_yurtdisi.js`'in artık kaldırılmış sweep
fonksiyonu) — ama farklı ID'ler için TUTARSIZ ve İMKANSIZ büyüklükte sonuçlar
verdi (örn. 2015 Haziran için tek bir "Almanya" ID'sinde 26,9 milyon
"seçmen" toplamı — tüm Almanya'daki kayıtlı Türk seçmen sayısından bile kat
kat fazla). Bu, YSK'nin arka ucunda bu spesifik filtre kombinasyonu için bir
veri kalitesi sorunu (muhtemelen bir SQL JOIN'in kombinasyonel olarak
fazla-satır üretmesi) — güvenilir bir sonuç alınamadı, bu yüzden 3 alan
(secmen/katilim/sandik) TÜM 8 seçimde (5 taşınan dahil) eski Habertürk
değerinde bırakıldı. Sadece gecerliOy/kullanilanOy/oy (parti dağılımı) YSK'nin
güvenilir agrege satırından güncellendi.

**Araçlar:** `fetch_yurtdisi.js` (agrege satırı çeker) + `merge_yurtdisi.py`
(parti sütun eşlemesini `party_map_helper`/`cb_name_alias.json` ile yapıp
ilgili `data/normalized/*.json` dosyasının `[key]['yurtdisi']` alanını
günceller — genel için parti/ittifak sütunları + `major` dışı olanlar
`Diğer`'e, referandum için `bagimsiz1`/`bagimsiz2`=Evet/Hayır, CB için
`bagimsizN` sütunları aday adına).

## Aydın/Muğla/Ordu/Tekirdağ/Trabzon'un eski "Merkez" ilçesi (2026-09-23, dördüncü oturum)

Kullanıcının "görselleştirmedeki boşlukları araştır" talebi üzerine, 2011
genel seçiminin ilçe kaydı taranıp `district_splits.json`'da olmayan bu 5
ilin eski "Merkez" ilçesinin (2011/2009yerel gibi erken YSK-API'li
seçimlerde) hiç eşlenmediği, o ilin gerçek oylarının kaybolduğu bulundu —
aynı kök neden, `pipelines/yerel_1994_1999_2004/parse_ilce_belde.py`'de
bulunup düzeltilen sorunla BİREBİR aynı (bu 5 il "Merkez"i TEK bir yeni
isimle - Efeler/Menteşe/Altınordu/Süleymanpaşa/Ortahisar - değiştirdi,
çok-parçalı bölünme değil). Düzeltme bu kez PAYLAŞILAN `hist_geomid.py`
modülüne eklendi (`MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA` sözlüğü) — hem
1994-2004 pipeline'ı hem `election_import`'ın 3 merge script'i
(`merge_genel_yerel.py`, `merge_yerel_v2.py`, `merge_cb.py`) aynı fonksiyonu
çağırdığı için TEK bir yerden düzeltildi.

**Düzeltme sırasında bulunan ikinci bug (mükerrer kayıt):** İlk deneme
sonucu geomId başına İKİ kayıt oluşuyordu — biri modern ilçenin KENDİ
güncel YSK ID'sinden (o dönem henüz yokmuş gibi sandik=0/oy={} boş
geliyor, çünkü ilçe gerçekten henüz yoktu), biri de eski "Merkez" ID'sinin
tarihsel çözümlemesinden (gerçek oylarla). Üç merge script'i de bu iki
kaynağı geomId'ye göre TEK kayıtta birleştirecek (gerçek veriyi olan
kazanır) ve ismi düzgün üretecek (`ad = hist_id.replace("HIST-",...)` eski
kodu, sentetik olmayan gerçek geomId'ler için "TR D 09 005" gibi çirkin
bir isim üretiyordu — artık sadece HIST- önekliler için bu dönüşüm
uygulanıyor, gerçek geomId'ler `ILCE_ADI_BY_GEOMID`'den doğru ismi alıyor)
şekilde düzeltildi.

**Etkilenen seçimler (yeniden işlendi):** 2011 genel (10 ilçe artık HIST/
modern-tarihsel çözümlemeyle geldi, önceden sadece 5'i - Balıkesir/
Malatya/Manisa/Kahramanmaraş/Şanlıurfa - çalışıyordu), 2009yerel (11),
2014yerel/2014cb (bu ikisinde seçim tarihi 2012-2014 split'inin ÜSTÜNDE/
yakınında olduğu için düzeltme çoğunlukla no-op oldu, il zaten büyükşehir
yoluyla doğru geliyordu — ama kod yolu artık tutarlı).

## Kullanıcının "boşlukları doğrula" talebiyle devam eden araştırma (aynı gün, ikinci tur)

Yukarıdaki "hâlâ çözülemeyen" listesindeki her madde tek tek araştırıldı
(varsayımla geçilmedi, gerçek kaynak/kod incelemesiyle):

- **Mardin — ÇÖZÜLDÜ.** Web araştırması: "Mardin merkez ilçenin ismi
  Artuklu olarak değiştirilmiştir" — Hatay/Van'ın aksine basit 1:1 yeniden
  adlandırma (modern ilçe listesinde Mardin'in TEK yeni ilçesi Artuklu,
  diğer 9'u zaten vardı). `MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA`'ya eklendi,
  2011/2009yerel/2010referandum için yeniden işlendi.
- **Hatay — gerçekten çok-parçalı, DOĞRULANDI.** 6360 sayılı kanun metni
  (web araştırması): eski Antakya Belediyesi'nden Antakya VE Defne diye
  İKİ yeni ilçe kuruldu, ayrıca Arsuz (Arsuz Belediyesi'nden) ve Payas
  (Dörtyol'un bir parçasından). Basit isim eşlemesiyle çözülemez — Denizli
  ile aynı kategori, gerçek sentetik birleşim poligonu gerekir.
- **Van — gerçekten çok-parçalı, DOĞRULANDI (ve zaten kısmen çalışıyor).**
  Web araştırması: eski Merkez resmi olarak Tuşba VE İpekyolu diye ikiye
  bölündü (ikisi de 2012). Van zaten `district_splits.json`'da vardı
  (splitYear=2011) — 2010referandum gibi split-öncesi seçimlerde sentetik
  HIST-Van-Merkez ile ZATEN doğru çalışıyordu; sadece 2011 (split ile AYNI
  yıl, seçim splitten önce olmuş olabilir) sınır durumunda eşleşmiyor —
  bu ayrı, küçük bir edge-case, düzeltilmedi.
- **Tillo/Siirt — kök neden bulundu, ÇÖZÜLEMEZ (kapsam dışı kalmalı).**
  Web araştırması: Tillo 1990'da ilçe olurken resmi adı "Aydınlar"a
  çevrildi. Ama bu bir isim eşleme sorunu DEĞİL — projenin temel il/ilçe
  sınır GeoJSON'unda (ttezer/turkiye-harita-verisi kaynaklı) Siirt için
  sadece 6 ilçe var (Baykan/Eruh/Kurtalan/Merkez/Pervari/Şirvan),
  Aydınlar/Tillo hiç yok. Kaynak haritanın kendisinde eksik bir poligon —
  yeni geometri bulunup eklenmadıkça çözülemez.
- **Kahramanmaraş/Çağlayancerit + Samsun/Ondokuzmayıs (TÜM yıllarda sıfır)
  — kök neden bulundu, ÇÖZÜLDÜ.** `acikveri-il-ilce-listesi.json`
  incelendiğinde YSK'nin KENDİ ilçe listesinde bu 2 ilçe için İKİŞER farklı
  `ilce_ID` olduğu görüldü (örn. Kahramanmaraş'ta hem 1027 hem 678,
  ikisi de "ÇAĞLAYANCERİT" — YSK'nin kendi veritabanındaki bir mükerrer
  kayıt, muhtemelen eski/temizlenmemiş bir ID). Her ikisi de aynı modern
  geomId'ye eşleniyor, biri hep gerçek oy veriyor biri hep sıfır dönüyor —
  TAM OLARAK yukarıdaki "mükerrer kayıt" bug'ının aynısı, sadece henüz
  2015Haziran/2015Kasım/2018/2023 (genel), 2019yerel/2024yerel,
  2018cb/2023cb1tur/2023cb2tur, 2010referandum/2017referandum için
  yeniden işlenmemişti. Hepsi yeniden işlendi, düzeldi (tarayıcıda
  doğrulandı: Çağlayancerit 2023 → "AKP %42.52, 5.802 oy").

## Eşlenemeyen Merkez ilçeleri — çözüldü (2026-10-05)

Denizli, Hatay ve Van'ın 2012'de bölünen eski Merkez ilçesi (2009 yerel, 2010 referandumu,
2011 genel) bugünkü ilçe kimliğine eşlenemediği için aktarımda ilçe satırı olarak düşmüştü;
oyları yalnız il toplamındaydı. `merkez_ilce_tamamla.py` bu satırları geri koyar (her içe
aktarmadan sonra; `tarihsel_sinirlari_uret.py` de çağırır):

- 2010 referandumu, 2011 genel: Merkez = il satırı − ildeki diğer ilçe satırları (aynı YSK
  sandık verisinin toplamı; parti/seçenek, seçmen, sandık ve geçerli oy ayrı ayrı).
- 2009 yerel başkanlık: il merkezi belediyesinin sonucu = il satırı (o tarihte büyükşehir
  değil). Meclis sonuçları `data/raw/ysk/acikveri-belde-agrege/` içindeki "DENİZLİ MERKEZ",
  "HATAY MERKEZ" satırlarından `build_meclis_harita.py` ile bağlanır.
- Poligonlar: HIST-Denizli-Merkez (Merkezefendi + Pamukkale), HIST-Hatay-Merkez (Antakya +
  Defne), HIST-Van-Merkez (`historical_geo/birlesim_2009_sonrasi.py`).
- 2010 ve 2017 referandumunda henüz kurulmamış ilçelerin `{Evet: 0, Hayır: 0}` satırlarının oy
  alanı boşaltılır (ön yüz bunları sonuçlu sayıp boyuyordu).

## 2026-10-04 bağımsız oy onarımı

`ballot_votes.js`, belediye/genel seçimlerde bağımsız toplamını tek sentetik `bagimsiz0_ALDIGI_OY` sütununda taşır. Bu sütun mevcut merge scriptlerinin numaralı bağımsız eşlemesiyle uyumludur. Cumhurbaşkanlığı (9) ve referandum (7) aday/tercih sütunları birleştirilmez. `fetch_and_aggregate.js` ve `fetch_yerel_v2.js` repo kök yolunu doğru çözer. Aggregation version 2 olmayan progress dosyaları arşivlenip sorgu yeniden çalıştırılmalıdır. Regresyonlar: `node --test tests/ballot_votes.test.cjs`.
