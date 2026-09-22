# Tarihsel dönüşüm katmanı — KAYNAK GEOMETRİSİ DEĞİL

Bu klasördeki dosyalar `../raw/` veya `ttezer`'den doğrudan gelmiyor —
bunlar bu projenin kendi türetilmiş dönüşümü: Türkiye'nin il/ilçe sınırları
zaman içinde değiştiği (yeni iller kurulması, büyükşehir ilçelerinin
bölünmesi) için, eski seçim yıllarının haritasını çizebilmek amacıyla
GÜNCEL sınırlardan geriye doğru sentezlenmiş.

`../normalized/`'daki dosyalarla farkı: `normalized/` "şu an" için tek bir
güncel sınır kümesi, burası ise "o yıl nasıl görünüyordu" sorusuna cevap
veren BİRDEN FAZLA zaman dilimi (era) kümesi.

Kaynak: `~/Desktop/2023_Secim_Verileri/` (bu depo dışı, önceki oturum),
2026-09-22'de olduğu gibi kopyalandı. İçerik `index.html`'e gömülü
karşılıklarıyla (JSON içerik düzeyinde, serileştirme farklı olsa da)
doğrulandı — bkz. bu klasördeki `checksums.sha256` ve `../../data/
provenance/checksums.json` (tüm snapshot klasörlerinin konsolide kaydı).

## Dosyalar

- `turkiye_il_sinirlari_era1950.geojson` — 1950 seçimi zamanındaki il
  sınırları (o dönem 63 il)
- `turkiye_il_sinirlari_era1954.geojson` — 1954 (Bilecik düzeltmesi sonrası,
  64 il)
- `turkiye_il_sinirlari_era1957_1987.geojson` — 1957-1987 arası ortak sınır
  kümesi (bu aralıkta il sayısı sabit kaldı)
- `turkiye_il_sinirlari_era1991.geojson`, `era1995.geojson`, `era1999.geojson`
  — ardından kurulan yeni illerin (Ardahan/Iğdır/Aksaray/Bayburt/Karaman/
  Kırıkkale/Batman/Şırnak vb.) sırayla eklenmesiyle değişen il sayıları
  (73→74→79→80)
- `district_splits.json` — büyükşehir "Merkez" ilçelerinin 2008-2014
  bölünmelerinin (örn. Antalya Merkez → Muratpaşa+Kepez) hangi eski seçim
  yıllarında geri alınması gerektiğinin eşleme mantığı
- `turkiye_ilce_sinirlari_hist_splits.geojson` — yukarıdaki eşlemeye karşılık
  gelen, bölünmüş ilçelerin birleştirilmiş (eski hâle döndürülmüş) poligonları

## Nasıl kullanılıyor

`index.html` içindeki `GEO_ERAS` / `eras` mantığı, seçilen seçim yılına göre
bu dosyalardan uygun olanı seçip haritayı ona göre çiziyor. Davranış bu
taşımayla DEĞİŞMEDİ — sadece dosyaların diskteki konumu.
