# Normalize edilmiş veri

Bu klasördeki dosyalar, projenin **ortak veri modeli**ni oluşturur —
`scripts/build.py`'nin doğrudan okuyup `index.html`'e gömdüğü tek kaynak
bunlardır. Kendileri de bir kaynak değil, `data/raw/`'daki ham
kaynaklardan (YSK PDF/API, TÜİK, ikincil kaynaklar) seçim türü/pipeline'a
özel `scripts/<pipeline-adı>/parse_*.py` + `merge_*.py` script'leriyle
üretilmiş **türetilmiş** çıktıdır:

```
data/raw/<kaynak>/  →  scripts/<pipeline>/parse+merge  →  data/normalized/*.json  →  scripts/build.py  →  index.html
```

**Tarihsel not:** Bu klasör ilk oluşturulduğunda (2026-09-22, ilk oturum)
gerçekten tersti — o zamanki tek veri kaynağı zaten var olan bir
`index.html`'in gömülü JSON'uydu, `scripts/legacy/normalize_from_old_index.py`
onu tür bazında ayrıştırıyordu. Proje o günden bu yana raw→pipeline→normalized
mimarisine geçti; o script artık **legacy** ve kullanılmıyor (`scripts/legacy/`
altında, sadece tarihsel referans için duruyor). Her yeni seçim/kaynak
yükseltmesi artık doğrudan bu klasördeki dosyaları elle/pipeline'la
günceller, `index.html`'den asla geri okumaz.

Hangi seçimin hangi ham kaynaktan/pipeline'dan geldiği için tek referans
[`../../sources.yml`](../../sources.yml) (makine-okunur) ve
[`../../SOURCES.md`](../../SOURCES.md) (insan-okunur) — burada tekrar
edilmiyor, çünkü tam da bu tür tekrarlar zamanla birbirinden kopuyor.

## Dosyalar

- `partiler.json` — tüm seçimler arası paylaşılan parti adı→renk/kısaltma
  eşlemesi
- `elections/<tur>/<anahtar>.json` — il/ilçe düzeyi seçim sonuçları, HER
  SEÇİM AYRI BİR DOSYA (2026-09-23'te 4 büyük birleşik dosyadan — eski
  `genel_secimler.json`/`yerel_secimler.json`/`referandumlar.json`/
  `cumhurbaskanligi.json` — bu yapıya bölündü; `tur` klasörü `genel`,
  `yerel`, `referandum`, `cumhurbaskanligi`'den biri, `anahtar` dosya adı
  `sources.yml`'deki ile birebir aynı, örn. `elections/genel/2023.json`,
  `elections/yerel/2014yerel.json`, `elections/referandum/2017referandum.json`,
  `elections/cumhurbaskanligi/2023cb2tur.json`). Amaç: her seçimin
  değişikliği kendi dosyasında görünsün (git diff/checksum izolasyonu) —
  önceki tek-dosya-per-tür yapısında 20 yıllık genel seçim verisi tek bir
  ~MB'lık JSON'da birlikte tutuluyor, herhangi bir yıla dokunmak tüm
  dosyanın checksum'ını/diff'ini değiştiriyordu. Okuma/yazma HER ZAMAN
  `scripts/common/election_io.py`'deki `load_election`/`save_election`/
  `load_all_elections`/`load_elections_by_tur` yardımcılarıyla yapılır —
  hangi seçimin hangi `tur` klasörüne gideceği anahtarın kendi sonekinden
  (`tur_of()`) otomatik çıkarılır, hiçbir script artık bu dosya yollarını
  elle bilmek zorunda değil. `scripts/build.py` bu 46+ dosyayı okuyup TEK
  bir `secimler` sözlüğünde birleştirerek `index.html`'e gömer (frontend
  hâlâ tek bir bütünleşik JSON görür, bölünme sadece disk/git düzeyinde).
- `mahalle/<secim_anahtari>.json` — mahalle/muhtarlık düzeyi oy verisi,
  her biri bir seçim (bkz. `sources.yml`'deki YSK ilgili girişleri)
- `meclis_2024.json` — 2024 yerel seçiminin il meclisi üye dağılımı (ayrı,
  küçük bir veri kümesi)

**Not:** mahalle GEOMETRİSİ burada değil, `../../geo/normalized/mahalle_geo.json`'da
(oy verisinden ayrı — bir mahallenin sınırları yıldan yıla değişmiyor, tekrar
tekrar saklamaya gerek yok).

## Format

Kompakt JSON (girintisiz, `sort_keys=True`) — bu boyuttaki dosyalar (bazıları
onlarca MB) zaten satır satır elle okunmuyor; asıl "normalized" faydası
tür/yıla göre ayrı dosyalara bölünmüş olması, insan tarafından biçimli
görünmesi değil.

## Bütünlük

`checksums.sha256` (bu klasör) + merkezi manifest
[`../provenance/checksums.json`](../provenance/checksums.json) —
`tests/validate_elections.py` her ikisini de diskteki dosyalarla
karşılaştırır.

## 2026-10-04 — Atlas ile eşlenen kaynak onarımları

Atlas düzeltmesi: https://github.com/hamiKumbasae/turkiye-secim-atlasi/pull/9

- 2004 başkanlık kayıtlarında 81 il ve 910 ilçe DİE yayın no.2935'in temiz tablo arşivinden onarıldı. İl merkezi, büyükşehir ve ilçe belediyesi kapsamı `oyKapsami` ile belirtilir; kullanılan PDF sayfaları `duzeltmeKaynagi` alanındadır.
- Sakarya 1957 (DP8) ve 1961 (AP3, CHP2, YTP61:1) sandalyeleri ikincil arşivle tamamlandı. İl toplamlarını eksik kabul eden test istisnası kaldırıldı; 610 ve 450 toplamları artık gerçekten doğrulanır.
- Batman 1982 seçmen toplamı şehir/köy kırılımından 31.121 olarak onarıldı. Doğrulanamayan dört katılım `kaynakKatilim` alanında tutulur, gösterim değeri null'dır.
- Tillo'nun 15 seçim ve sekiz meclis pusulası YSK sandık sorgularından tamamlandı. Önceki Tillo eşleme eksikliği notları bu kayıtlar için geçerli değildir. Karaisalı 2024'ün 3.963 bağımsız oyu ayrıca tamamlandı.
- Özgün `kaynak` alanları korunur; kaynakla yapılan onarım bu alana `duzeltme` olarak eklenir. `export_static.py --public` çıktısı atlas düzeltmeleriyle eşleşir.
- Bağımsız oy aktarımı, `bagimsiz_TOPLAM_OY` ile numaralı aday oylarını çift saymaz. Cumhurbaşkanlığı ve referandum seçenekleri ayrı kalır. Eski progress dosyaları yeni hesapla karıştırılmamak için yeniden kullanılmaz.
- `scripts/validate_public_data.py` yeni/değişmiş veri sorunlarını reddeder. Mevcut 3.554 bulgu `tests/fixtures/known-validation-issues.json` içinde kaynak doğrulaması bekler; bu liste otomatik yenilenmemelidir. Ön yüz doğrulanmamış yüzdeleri göstermez.

## Oy toplamı tamamlamaları (2026-10-04)

- **2024 yerel, bağımsız adaylar:** eski YSK aktarımı (`fetch_yerel_v2.js`, sonradan `ballot_votes.js`
  ile düzeltildi ama veri yeniden çekilmedi) bağımsız aday oylarını almıyordu: 489 kayıtta parti
  toplamı geçerli oydan azdı, oranlar eksik toplama göre hesaplanmıştı. Eksikler depodaki Vikipedi il
  sayfalarından (`data/raw/wikipedia/il-sayfalari/yerel/2024yerel/`, YSK sonuçları) tamamlandı:
  `scripts/pipelines/election_import/wiki_bagimsiz.py`. Parti oyları (YSK, ilçe toplamı = ilçe
  belediyesi + beldeler) korundu; `Bağımsız` eklendi, kalan fark `Diğer`; oranlar geçerli oya göre;
  kazanan Vikipedi'nin "seçildi" işaretinden (26 kayıtta değişti, ör. Vakfıkebir bağımsız, Kırklareli
  merkez MHP, Kütahya merkez CHP). Kayıtlarda `kaynak.bagimsizTamamlama`, kullanıcıya `veriNotu`.
- **Küçük farklar:** parti toplamı geçerli oydan en çok %5 az olan 2.143 kayıtta (22 seçim; halk
  oylamaları ve cumhurbaşkanlığı hariç) fark `Diğer`e eklendi, oranlar geçerli oya göre yeniden
  hesaplandı, kazanan değişmedi: `diger_tamamla.py`, kayıtta `kaynak.digerTamamlama`.
- **1961, kaynak içi tutarsızlık:** Feke, Ağlasun, Yeşilova, Susuz — TÜİK tablosunun kendisinde parti
  toplamı geçerli oyla tutmuyor (yüzdeler %86–113). Kaynaktaki haliyle bırakıldı; `veriNotu` ile
  belirtildi. Basılı DİE yayınıyla (0014128) doğrulanmalı.
- Kalan 923 bulgu (`tests/fixtures/known-validation-issues.json`) kaynakla incelenmeli; 2009–2019
  yerel seçimlerdeki büyük farklar bunların çoğu (Vikipedi sayfa biçimi farklı, ayrıca ele alınmalı).

## Kayıt temizliği (2026-10-05)

- **2004 yerel, "Karadeniz Ereğli":** Zonguldak Ereğli satırının (TR-D-67-004) poligonsuz kopyasıydı
  (aynı DİE sayfası 378–379, aynı seçmen ve oylar). Kopyadaki aday adları asıl satıra taşındı, kopya
  silindi.
- **1991 genel, Bakırköy:** TÜİK ilçe tablosunda iki seçim çevresi parçası olarak iki satırdı; ikisi aynı
  poligona bağlı olduğu için haritada yalnız biri görünüyordu. Tek satırda toplandı (geçerli oy 510.106 =
  mertnuhoglu tabanındaki tek satır); iki parçanın kaynak kaydı `kaynak.parcalar` alanında.
- **2009, 2014, 2019 yerel, bağımsız adaylar:** 2024'teki aynı aktarım hatası (YSK agregesinde bağımsız
  aday oyları yok) bu üç seçimde de vardı; örneğin 2014 Mardin büyükşehirde kazanan bağımsız Ahmet Türk
  (%52,1) hiç görünmüyor, AK Parti %78 görünüyordu. `wiki_bagimsiz.py`, ham Vikipedi sayfası
  ayrıştırılamadığında aynı sayfaların ayrıştırılmış katmanını (`data/kaynaklar/wikipedia/yerel/`)
  kullanacak şekilde genişletildi ve üç seçime uygulandı (2009: 91, 2014: 44, 2019: 73 kayıt; 106 kayıtta
  bağımsız eklendi). Doğrulanmamış bulgular 924 → 731.
- **1955 yerel, il listesi:** kayıt 1954 öncesi il listesiyle kurulmuştu (64 il). 13 Kasım 1955'te var olan
  Nevşehir, Adıyaman ve Sakarya eklendi, "Kırşehir" il satırı (aslında Nevşehir'in Kırşehir ilçesi)
  ilçe satırına çevrildi; 17 ilçe satırı (yalnız kazanan) depodaki ayrıştırılmış Vikipedi katmanından
  (`election_import/yerel_1955_iller.py`). 66 il.
- **2009 yerel, Ağın ve Kadışehri:** 29 Mart başkanlık seçimi iptal edilip 7 Haziran 2009'da yenilendi;
  YSK açık verisinde ilçe merkezi yoktu (Ağın boş; Kadışehri satırında Halıköy beldesinin sonucu vardı).
  29 Mart sonucu seçim kaydına, 7 Haziran sonucu `ek/yenileme_ara/2009yenileme_belediye_baskanligi.json`'a
  (Vikipedi il sayfaları, `election_import/yenileme_2009.py`).

