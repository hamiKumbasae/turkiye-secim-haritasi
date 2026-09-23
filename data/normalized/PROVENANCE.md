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
- `cumhurbaskanligi.json`, `genel_secimler.json`, `yerel_secimler.json`,
  `referandumlar.json` — il/ilçe düzeyi seçim sonuçları, seçim türüne göre
  ayrılmış (anahtarlar `sources.yml`'deki ile birebir aynı, örn. `"2023"`,
  `"2014yerel"`, `"2017referandum"`, `"2023cb2tur"`)
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
