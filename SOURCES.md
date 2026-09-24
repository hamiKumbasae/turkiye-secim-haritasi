# Veri Kaynakları

Bu belge, `index.html`'e gömülü 46 seçimin her birinin verisinin **nereden**
geldiğinin okunabilir özetidir. Makine-okunur, tam ayrıntılı hâli
[`sources.yml`](sources.yml)'dedir — her iki dosya da aynı 46 anahtarı kapsar
(anahtarlar `index.html` içindeki `secim_tarihi_data.json`'daki seçim
anahtarlarıyla birebir aynıdır, örn. `2023`, `2014yerel`, `2017referandum`,
`2023cb2tur`).

## Kaynak hiyerarşisi (öncelik sırası)

1. **YSK Açık Veri Portalı** (`acikveri.ysk.gov.tr`) — resmi, 2009 ve sonrası
   seçimleri kapsar. Bu depoda **mahalle/muhtarlık düzeyi** verinin tamamı ve
   **2014 Cumhurbaşkanlığı seçiminin il/ilçe düzeyi** doğrudan buradan.
1b. **YSK'nin 1950-1977 arşivi** (`ysk.gov.tr`, ayrı bir sayfa, açık API değil
   — indirilebilir PDF) — **TÜİK verisine dayanan resmi il-bazlı arşiv**,
   1950/1954/1957/1961/1965/1969/1973/1977 genel seçimlerinin il düzeyi
   verisinin kaynağı (bkz. aşağı).
2. **Habertürk** (`secim.haberturk.com`) — 2011 sonrası genel/yerel/CB
   seçimleri ile 2010/2017 referandumlarının il/ilçe düzeyi verisinin
   kaynağı. Resmi değil ama YSK'nin açıkladığı sonuçları raporluyor.
3. **Türkçe Wikipedia** (YSK kaynaklı tablolar) — 1950-2009 arası, YSK'nin
   1950-1977 arşivinin ve Habertürk'ün kapsamadığı yıllar için il düzeyi veri.
4. **mertnuhoglu/secim_verileri** (GitHub, memurlar.net kaynaklı) — 1991-2007
   genel seçimlerinin ilçe düzeyi kırılımı (Wikipedia sadece il düzeyi veriyor).

> **Not:** `~/Desktop/2023_Secim_Verileri/OKUBENI.md` (bu projenin dışında,
> önceki bir oturumun ürettiği dış üretim script'inin notu) 2026-09-19'da
> "YSK'nin açık veri portalı sandık bazlı sonuçları toplu biçimde
> yayımlamıyor" diyordu. Bu **yanlıştı** — YSK'nin `getSecimSandikSonucList`
> uç noktası tam olarak bunu yapıyor ve genel kullanıma açık. Bu depoya
> 2026-09-21/22'de eklenen tüm mahalle-düzeyi veri ve 2014cb'nin ilçe düzeyi
> bu keşfin sonucu.

## Cumhurbaşkanlığı (4 seçim)

| Yıl | İl/İlçe kaynağı | Mahalle kaynağı |
|---|---|---|
| **2014cb, 2018cb, 2023cb1tur, 2023cb2tur** | **YSK (acikveri API, sandık-düzeyi agrege)** | YSK, 641/973 ilçe |

**2026-09-22 (üçüncü oturum):** Habertürk tamamen kaldırıldı — 4 seçimin de
il/ilçe düzeyi artık `getSecimSandikSonucList` ile 998 ilçenin tamamından
agrege ediliyor. Ulusal sonuçlar bilinen resmi rakamlarla (Erdoğan/İhsanoğlu/
Demirtaş 2014, Erdoğan/İnce/Demirtaş/Akşener 2018, Erdoğan/Kılıçdaroğlu/Oğan
2023) tutarlı — ayrıntı `sources.yml`.

## Genel Seçim / Milletvekili (20 seçim)

| Dönem | İl kaynağı | İlçe kaynağı | Bilinen sorun / kapsam sınırı |
|---|---|---|---|
| **2011, 2015 Haziran, 2015 Kasım, 2018, 2023** | **YSK (acikveri API, sandık-düzeyi agrege)** | **YSK (aynı)** | Habertürk tamamen kaldırıldı (2026-09-22, üçüncü oturum) — bkz. aşağı |
| **1983, 1987, 1991, 1995, 1999, 2002, 2007** | **YSK (il-bazlı resmi arşiv)** | TÜİK (1983/1987 ilçe); 1991-2007 ilçe: mertnuhoglu tabanı + TÜİK (fark/eksik ve teyit) | 1991-2007: taban değerler mertnuhoglu'dan korundu, TÜİK ile birebir aynı olanlar `kaynak.teyit`, farklı/eksik olanlar (1995 Yeni Parti oyları, Fatih/Eminönü ayrımı) TÜİK'ten, satırın `kaynak.farklar` alanında eski/yeni değerleriyle (2026-09-24). **2002 Siirt**: hata değil, 9 Mart 2003 yenileme seçiminin resmî sonucu (bkz. aşağı) |
| **1950, 1954, 1957, 1961, 1965, 1969, 1973, 1977** | **YSK (TÜİK kaynaklı)** | TÜİK (1961-1977 ilçe) | 1961-1977 ilçe düzeyi TÜİK'in "Seçim çevresi ve ilçelere göre" tablosundan (2026-09-24, bkz. `data/raw/tuik/secimdagitimapp-ilce-1961-1987/PROVENANCE.md`). 1950/1954/1957 için resmî ilçe kaynağı bulunamadı. (Önceki "seçim çevresi il olduğu için ilçe düzeyi hiç var olmadı" notu yanlıştı.) |

**Habertürk → YSK geçişi (2026-09-22, üçüncü oturum):** Kullanıcının "Habertürk
verisini silsek o verileri YSK'de bulamıyor muyuz?" sorusu üzerine —
`scripts/pipelines/election_import/` ile YSK'nin resmi `acikveri.ysk.gov.tr`
API'sinden (`getSecimSandikSonucList`) **Türkiye'deki tüm ~998 ilçenin**
sandık-düzeyi ham verisi çekilip il/ilçe toplamlarına agrege edildi —
mahalle özelliğindeki poligon-geometri kısıtı burada yok (sadece sayı
toplanıyor), bu yüzden 2009 sonrası **her** seçim için eksiksiz kapsanabiliyor.
Habertürk primary olduğu 15 seçimin hepsi bu şekilde yükseltiliyor (genel
2011-2023, yerel 2009-2024, CB 2014-2023, referandum 2010/2017) — devam eden
bir işlem, tamamlanan seçimler yukarıdaki tabloda işaretli. Ayrıntı:
`scripts/pipelines/election_import/PROVENANCE.md`.

**1983-2007 YSK güncellemesi (2026-09-22, ikinci oturum):** Bu 7 seçimin il
düzeyi verisi de (1950-1977 ile AYNI arşiv ailesinden,
`ysk.gov.tr/doc/dosyalar/docs/Milletvekili/1983-2007/<İl>.pdf`, 81/81 il)
Wikipedia'dan YSK'nin resmi arşivine yükseltildi. 529 il×yıl kaydının
528'inde parti-vekil toplamı YSK'nin özet rakamıyla birebir eşleşti (tek
istisna: Bingöl 1983, YSK'nin kendi belgesi içi tutarsız — bkz.
`sources.yml`). 7 yılın hepsinde il toplamları bilinen resmi ulusal
sandalye sayılarıyla (399/450/450/550/550/550/550) birebir örtüştü. 2 parti
(MÇP, YENP95) ilk kez ayrı izlendi, önceden "Diğer"e karışıyordu. Ayrıntı:
`data/raw/ysk/1983-2007/PROVENANCE.md`.

**Çoklu kaynak doğrulaması (2026-09-22, sadece 1950 için, kanıt amaçlı):**
YSK'nin kendi il-bazlı PDF'lerinden topladığımız ulusal toplam, YSK'nin AYRI
bir "ulusal özet" sayfasından ve TBMM'nin kendi seçim veritabanından farklı
çıkıyor — üçü de birbirinden az çok sapıyor. İlginç olan: bizim il-bazlı
toplamımız, YSK'nin KENDİ ulusal özetinden çok TBMM'ye yakın (DP/CHP/Millet
Partisi için %0,01-0,27 fark) — yani YSK'nin kendi sitesi bile kendi
içinde tam tutarlı değil. Bu, `sources.yml`'de `1950` altında
`discrepancies` olarak (çözülmeden, sadece kaydedilerek) belgelendi. Aynı
derinlikte doğrulama diğer 19 genel seçim yılı için henüz yapılmadı — bu,
onaylanmış bir sonraki adım (bkz. `scripts/pipelines/genel_1950_1977/
verify_national_totals.py`).

**1950-1977 YSK/TÜİK güncellemesi (2026-09-22):** Bu 8 seçimin il düzeyi
verisi, YSK'nin `ysk.gov.tr`'de yayımladığı ve kendi notuna göre "Türkiye
İstatistik Kurumu verileri esas alınarak hazırlanmış" resmi bir arşivden
güncellendi. En büyük kazanım: **1950/1954/1957/1961'de önceden hiç
olmayan il bazında milletvekili (sandalye) dağılımı artık var** — 66 il ×
8 yıl için, YSK'nin kendi belirttiği toplam milletvekili sayısıyla
bire bir eşleştiği doğrulanarak. Tek istisna: **Sakarya, YSK'nin bu
arşivinde hiç yok** (67 değil 66 il listeleniyor) — Sakarya'nın verisi
eski Wikipedia kaynağıyla kaldı, bu yüzden 1957/1961'in il-toplamı resmi
ulusal rakamdan Sakarya'nın sandalyesi kadar düşük çıkar (ulusal toplam
alanı yine de doğru). Ayrıntı: `data/raw/ysk/1950-1977/PROVENANCE.md` ve
`scripts/pipelines/genel_1950_1977/`.

**2002 Siirt (açıklandı, 2026-09-24):** Önceki not, mertnuhoglu'nun Siirt ilçe
kırılımını "bozuk" sayıyordu (Merkez'de AK Parti %86,71, DEHAP birinci değil).
Hata değil: 3 Kasım 2002 Siirt seçim çevresi sonucu YSK tarafından iptal edildi
ve seçim 9 Mart 2003'te yenilendi. YSK'nin il PDF'i ve TÜİK'in resmî ilçe tablosu
yenileme seçiminin sonucunu veriyor; mertnuhoglu değerleri TÜİK ile 7/7 ilçede
birebir aynı.

## Yerel Seçim / Belediye Başkanlığı (15 seçim)

| Yıl | Kaynak | Not |
|---|---|---|
| **2024, 2019, 2014, 2009** | **YSK (acikveri API, sandık-düzeyi agrege — il+ilçe)** | Habertürk tamamen kaldırıldı (2026-09-23, dördüncü oturum) — bkz. aşağı |
| **2004, 1999, 1994** | **YSK resmi arşiv (il + ilçe/belde, ~%75-76)** | 2026-09-22'de il düzeyi, 2026-09-23'te ilçe/belde düzeyi yükseltildi (bkz. aşağı); kalan ~%24-25 (sadece Denizli'nin merkez ilçesi + Gümüşhane 1994 istisnası) eski Wikipedia kaynağında kaldı |
| 1989, 1984 | Wikipedia (il başına alt makaleler) | Katılım/seçmen verisi kaynakta yok — il VE ilçe düzeyi var; YSK'de sadece ulusal toplam PDF'i var, il-bazlı yok |
| 1977, 1973, 1968, 1963, 1955, 1950 | Wikipedia (il başına alt makaleler) | il merkezi 2026-09-22'de (bkz. [`SECIM_TAKVIMI.md`](SECIM_TAKVIMI.md)), **ilçe belediye başkanlıkları 2026-09-24'te** aynı sayfaların İlçeler bölümünden eklendi (1950/1955: yalnızca kazanan parti; satır kökeni: `kaynak.revid`); 1950/1955'te dolaylı seçim sistemi (kazanan = meclisi/başkanlığı sağlayan parti); ayrıntı için `sources.yml`'deki ilgili girişlere bakın |

**Habertürk → YSK geçişi, yerel seçimler (2026-09-23, dördüncü oturum):**
Genel/CB/referandum ile aynı `getSecimSandikSonucList` API'si kullanıldı, ama
yerel seçimlerde her ilçe (ve büyükşehirlerde ayrıca bütün büyükşehir) AYRI
bir yarış olduğu için genel seçimdeki gibi "ile ait tüm ilçeleri topla"
yöntemi YANLIŞ sonuç verir (örn. İstanbul 2019'da tüm ilçeleri toplamak
AKP %45,9/CHP %40,3 gibi hatalı bir fark üretiyordu — gerçekte neredeyse
berabere bir seçimdi). Bunun yerine: **büyükşehir statüsündeki iller için
`secimTuru=6` (Büyükşehir Belediye Başkanlığı, ilçeId=boş) agregesi**,
**diğer iller için sadece "`<İl> MERKEZ`" ilçesinin kendi `secimTuru=2`
sonucu** "il" kaydı olarak kullanıldı (2009/2014'te 16→30 büyükşehir,
Kanun 6360 ile). "ilçeler" her zaman ilgili ilçenin kendi ayrı
`secimTuru=2` sonucu. Bu düzeltme sırasında ayrıca **2014'ün BDP oy
sorunu da tamamen çözüldü**: parti-sütun eşlemesi için kullanılan
önbellekli `baslik_2014yerel.json` dosyasında BDP sütunu hiç yoktu (oylar
sessizce toplanmıyordu) — canlı yeniden çekilip düzeltildi, BDP artık
Diyarbakır'ı (ve il/ilçe toplamlarını) doğru yansıtıyor. Ayrıntı:
`scripts/pipelines/election_import/PROVENANCE.md`.

## Referandum (7 halk oylaması)

| Yıl | Kaynak | Not |
|---|---|---|
| **2017, 2010** | **YSK (acikveri API, sandık-düzeyi agrege — il+ilçe)** | Habertürk kaldırıldı (2026-09-22) — 2010'un eski "sandık×300 tahmini" sorunu da çözüldü, artık gerçek sayılar |
| 2007, 1988, 1987, 1982, 1961 | Wikipedia | İlçe verisi yok, gerçek oy sayıları (tahmin değil) |

**2010 referandum — eski tahmin sorunu ÇÖZÜLDÜ (2026-09-22):** Önceden
Habertürk kaynağı sadece oran + sandık sayısı veriyordu, ilçe/il oy sayıları
sandık başına ~300 oy varsayımıyla tahmin ediliyordu. Artık YSK'nin
`getSecimSandikSonucList` API'sinden 998 ilçenin TAMAMI sandık-düzeyinde
çekilip toplandı — gerçek seçmen/geçerli/geçersiz/Evet/Hayır sayıları.
Ulusal sonuç (%57,86 Evet) bilinen resmi rakamla tutarlı.

## Yurtdışı seçmen verisi

2015 Haziran/Kasım, 2018, 2023 genel; 2017 referandumu; 2018, 2023 (1./2.
tur) CB seçimlerinde yurtdışı sandıklarının oyu ayrı bir panelde tutuluyor,
hiçbir ile atanmıyor (haritaya dahil değil). Tahmin yok, gerçek rakamlar.

**2026-09-23 güncellemesi:** 8 seçimin 5'i (2015 Haziran/Kasım, 2018 genel;
2017 referandumu; 2018cb) Habertürk'ten YSK'nin `acikveri.ysk.gov.tr`
API'sine taşındı ("ÜLKELER SANDIKLAR TOPLAMI" hazır-agrege satırı — geçerli
oy/kullanılan oy/parti dağılımı; 2018 için Habertürk'ün rakamlarıyla birebir
eşleşti). Kalan 3'ü (2023 genel, 2023cb1tur, 2023cb2tur) YSK'de bu agrege
sıfır döndüğü için Habertürk'te kaldı. Taşınan 5 seçimde bile "seçmen/katılım/
sandık" alanları eski kaynakta bırakıldı — YSK'nin bu üç alan için verdiği
sayılar güvenilmez çıktı (ayrıntı `sources.yml`'deki known_issue).

## Harita geometrisi

- **İl/ilçe sınırları:** `ttezer/turkiye-harita-verisi` (HDX kaynaklı),
  basitleştirilmiş.
- **Mahalle sınırları:** `ttezer/turkiye-harita-verisi` (25 il, belediye açık
  verisi/MAKS kaynaklı) + `osadikoglu/turkey-admin-units-osm` üzerinden
  OpenStreetMap (kalan 56 il).
- **Tarihsel dönüşümler** (Ardahan/Iğdır→Kars gibi sonradan-il-olan ilçelerin
  eski yıllarda ana ile birleştirilmesi, büyükşehir "Merkez" ilçe
  bölünmelerinin geri alınması): bunlar kaynak geometrisi değil, bu projenin
  kendi türetilmiş dönüşüm katmanı (`geo/historical/`).

## Kapsam dışı / henüz yapılmadı

- **GENEL seçimlerin il/ilçe düzeyi artık tamamlandı:** 1950-2023 arası tüm
  20 genel seçim ya YSK'nin resmi il-bazlı arşivinden (1950-2007) ya da
  `acikveri.ysk.gov.tr` sandık-düzeyi agregesinden (2011+, bkz. yukarı).
  Sadece 1991-2007'nin İLÇE düzeyi hâlâ GitHub/mertnuhoglu kaynaklı (YSK'nin
  bu dönem için resmi ilçe-bazlı arşivi yok) — bkz. altındaki madde.
- **Yerel 1994/1999/2004 il düzeyi (2026-09-22) ve ilçe/belde düzeyi
  (2026-09-23) YSK'ye yükseltildi** (bkz. yukarıdaki tablo) — aynı PDF'lerin
  ilçe/belde kırılımı bu oturumda da çıkarıldı (~%75-76 kapsama, 100'e
  yakın ilçe kaydı önceden Wikipedia'da da hiç yoktu, tamamen yeni eklendi). 2012 Büyükşehir
  Kanunu'yla "Merkez" ilçesini TEK bir yeni isimle değiştiren 5 il (Aydın→
  Efeler, Muğla→Menteşe, Ordu→Altınordu, Tekirdağ→Süleymanpaşa, Trabzon→
  Ortahisar) basit isim eşlemesiyle çözüldü (poligon gerekmedi, doğrulanmış
  1:1 yeniden adlandırma). Kalan ~%24-25 sadece Denizli'nin merkez ilçesi —
  bu il "Merkez"i Pamukkale VE Merkezefendi diye İKİ ayrı ilçeye böldü,
  `geo/historical/district_splits.json` tarzı gerçek bir sentetik birleşim
  poligonu gerektiriyor (ayrı bir GIS işi, henüz yapılmadı) — eski
  Wikipedia kaynağında kaldı. Ayrıntı: `scripts/pipelines/yerel_1994_1999_2004/
  PROVENANCE.md`.
- Yerel 1984/1989'da sadece ULUSAL toplam PDF'i var (il bazlı yok, 1963-1977
  gibi) — bu ikisi Wikipedia'da kalacak.
- Referandum 2010/2017 için YSK'nin `halkoylamasi-arsivi/2648` sayfasındaki
  ayrı yıl sayfaları (`16-nisan-2017-.../5002`, `12-eylul-2010-.../5003`)
  henüz taranmadı — il-bazlı resmi PDF olup olmadığı bilinmiyor (not:
  sandık-düzeyi `getSecimSandikSonucList` verisi zaten primary kaynak,
  bu madde sadece ek bir PDF-arşiv çapraz kontrolü için).
- 1991-2007 genel seçimlerin İLÇE düzeyi hâlâ GitHub (mertnuhoglu) kaynaklı
  — YSK'nin bu dönem için resmi bir ilçe-bazlı arşivi bulunamadı ("seçim
  çevresi" zaten il'in kendisiydi, ayrı bir ilçe sayımı hiç yapılmamış
  olabilir).
- Wikipedia/Habertürk kaynaklı kalan verilerin tek tek YSK/TÜİK ile çapraz
  doğrulanıp gerekirse değiştirilmesi.
- 2019 İstanbul BB Yenileme, 2024 Yenileme Seçimi, 2026 Ara Seçimi (tekil/özel
  seçimler) — henüz eklenmedi.
- **1984 öncesi 6 yerel seçimin (1950-1977) ilçe düzeyi verisi** — 2026-09-22'de
  bu 6 yılın İL MERKEZİ düzeyi eklendi (bkz. yukarıdaki tablo ve
  [`SECIM_TAKVIMI.md`](SECIM_TAKVIMI.md)), ama ilçeler (Adıyaman'ın Besni'si
  gibi, 1984+ verisinde olduğu gibi) hâlâ yok — `ilceler` bu 6 yıl için boş.
  Ara seçim ve Cumhuriyet Senatosu seçimleri gibi kapsam-dışı kategoriler için
  bkz. [`data/secim_takvimi.json`](data/secim_takvimi.json).


## Ek kayıtlar (haritaya bağlı değil, 2026-09-24)

Projede başka karşılığı olmayan, 1950 sonrası kayıtlar; tek kaynak Türkçe Wikipedia
il alt makaleleri, her kayıtta sayfa + revid, her dosyada `kapsam` (bulunan/beklenen):

| Dosyalar | İçerik |
|---|---|
| `data/normalized/ek/senato/` | Cumhuriyet Senatosu 1961-1979 (8 seçim): il sonuçları, ilçe birincileri, seçilen senatörler |
| `data/normalized/ek/milletvekilleri/` | Seçilen milletvekilleri 1950-2023 — yalnızca 1969/1995/2002 tam, diğerlerinde kapsam.durum eksik/fazla |
| `data/normalized/ek/beldeler/` | Belde belediye başkanlıkları, yerel 1950-2024 |

## Referandum ilçe düzeyi (2026-09-24)

1961, 1982, 1987 ve 1988 halkoylamalarının ilçe sonuçları TÜİK'in *Halk Oylaması
Sonuçları 2007, 1988, 1987, 1982, 1961* (2008) yayınından eklendi (il ve ilçe,
şehir/köy kırılımıyla). İl düzeyi YSK'de kaldı; TÜİK il toplamları YSK ile birebir
aynı. Ayrıntı: `data/raw/tuik/halkoylamasi-0018260/PROVENANCE.md`.

## Yenileme ve ara seçimler (2026-09-24)

YSK açık veri API'sinden, il/ilçe/belde bazında: 23 Haziran 2019 İstanbul BB
yenilemesi, 2 Haziran 2024 yenileme seçimi, 7 Haziran 2026 mahalli idareler ara
seçimi → `data/normalized/ek/yenileme_ara/`. Haritaya bağlı değil. Ayrıntı:
`data/raw/ysk/acikveri-belde-agrege/PROVENANCE.md`.

## Senato ilçe oyları (2026-09-24)

1964, 1966, 1968, 1973, 1975, 1977 ve 1979 Cumhuriyet Senatosu seçimlerinin ilçe bazında parti oyları, DİE'nin
taranmış kitaplarından (TÜİK kütüphanesi) → `data/normalized/ek/senato/<seçim>.json`
içinde `ilceOylariTuik`. İl sonuçları Wikipedia ile karşılaştırıldı (1968: 24/24
birebir). Aynı 1966 kitabındaki Hatay milletvekili ara seçiminin ilçe sonuçları
`ek/yenileme_ara/1966mv_ara_hatay.json`. Ayrıntı: `data/raw/tuik/senato-metin/PROVENANCE.md`.
