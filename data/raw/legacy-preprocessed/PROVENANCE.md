# Kaynak

Bu klasördeki dosyalar, `~/Desktop/2023_Secim_Verileri/` (bu depo DIŞINDA,
önceki bir oturumda çalışılan bir dış üretim klasörü) içinden 2026-09-22'de
olduğu gibi kopyalandı.

**Bunlar "ham" veri değil, önceden işlenmiş (preprocessed) bir ara ürün.**
`OKUBENI.md`'nin kendi belirttiği gibi, bu dosyalar Habertürk (2011+),
Türkçe Wikipedia (1950-2009 arası boşluklar) ve `mertnuhoglu/secim_verileri`
(1991-2007 ilçe düzeyi, bkz. `../third-party/mertnuhoglu/`) kaynaklarının
BİRLEŞTİRİLMİŞ hâlidir — hangi satırın hangi kaynaktan geldiği artık dosya
düzeyinde ayrılmış değil, sadece `OKUBENI.md`'nin anlatığı sınırlar (yıl
aralıkları) üzerinden biliniyor.

**Kaynak-ayrımlı gerçek ham dosyalar** (Habertürk'ün kendi sayfa çıktısı,
Wikipedia'nın kendi tablo HTML'i) bu depoda YOK — dış üretim script'inin
orijinal kazıma çıktısı hiç saklanmamış. Bu dürüstçe bir boşluk, bkz.
`../../NOTICE.md`.

## Dosyalar

- `OKUBENI.md` — kaynakların ayrıntılı anlatımı (bkz. `../../../SOURCES.md`
  ve `../../../sources.yml`, bu belgenin yapılandırılmış transkripsiyonu)
- `1950_2023_tam_veri_seti.json` — tüm 43 seçimin birleştirilmiş ana veri
  kümesi; `index.html`'e gömülü `secim_tarihi_data.json`'un kaynağı
- `district_splits.json`'a benzer geometri dosyaları **burada değil**,
  `../../../geo/historical/`'da (oy verisi değil, sınır verisi oldukları için)
- Geri kalan `*.csv` dosyaları — ana JSON'un çeşitli kesitleri/özetleri,
  yine dış üretim script'inin ara çıktıları

## Bütünlük

`checksums.sha256` — bu klasördeki (kendisi ve PROVENANCE.md hariç) her
dosyanın SHA-256 özeti, 2026-09-22'de üretildi.
