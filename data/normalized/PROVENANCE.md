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
