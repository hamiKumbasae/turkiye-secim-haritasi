# 1961-1987 Genel Seçim İlçe Pipeline'ı (TÜİK)

1961, 1965, 1969, 1973, 1977, 1983 ve 1987 genel seçimlerine **ilçe düzeyi**
ekler. Önceden bu yıllarda sadece il düzeyi vardı ("bu dönemde ilçe kırılımı
yok" diye düşünülüyordu — yanlış: DİE sonuçları ilçe ilçe yayımlamış, TÜİK
de hâlâ sunuyor). Kaynak ve doğrulama: `data/raw/tuik/secimdagitimapp-ilce-1961-1987/PROVENANCE.md`.

## Script'ler

```
fetch_tuik_ilce.py        TÜİK secimdagitimapp'i (ZK uygulaması) tarayıcısız
                           sürüp her yıl × il raporunu data/raw/tuik/'e indirir.
tuik_report.py             Tek bir rapor HTML'ini (cp1254) il + ilçe satırlarına
                           ayrıştırır.
merge_into_normalized.py   Raporlardan ilçe satırlarını üretir ve
                           data/normalized/elections/genel/<yıl>.json'a yazar.
```

## Eşleme kuralları

- **Parti:** TÜİK sütun başlığı → `partiler.json` anahtarı (`PARTY`). Tüm
  partilerin kodu var, ilçe satırlarında "Diğer" yok. 1969 "Birlik Partisi"
  ile 1973/77 "Türkiye Birlik Partisi" aynı parti (`TBP73`).
- **geomId:** proje yeni sınır kararı VERMEZ. Aynı ilçe adının (plaka +
  `fold(ad)`) dönemin en yakın ilçe-düzeyi verisindeki (1984yerel,
  1989yerel, 1991, 1994yerel, 1995) geomId'si kullanılır; 1987 için
  1989yerel, diğerleri için 1984yerel öncelikli. Yazım farkları `ALIAS`,
  il değiştiren ilçe `CROSS_PLAKA` (Kaynarca: Kocaeli → Sakarya), özel
  durumlar `OVERRIDE`:
  - Eminönü → `HIST-Istanbul-Eminonu`, Fatih → `HIST-Istanbul-Fatih`
    (2007referandum ile aynı; Eminönü 2008'e kadar ayrı ilçe).
  - Malatya Merkez → Battalgazi (`TR-D-44-004`): mevcut `HIST-Malatya-Merkez`
    Yeşilyurt'u da içeriyor ve bu yıllarda Yeşilyurt'un kendi satırı var
    (çakışırdı).
- **Büyükşehir Merkez ilçeleri** (Adana, Bursa, Gaziantep, Kayseri, Konya):
  `geo/historical/metro_merkez_1961_1987.json` — bölünme kanununun doğrudan
  haleflerinin birleşimi (3306, 3391, 3398, 3399, 3508 sayılı kanunlar),
  poligonlar `scripts/pipelines/historical_geo/build_metro_merkez.py` ile.
- **Ankara Merkez (1961-1983) bilerek eşlenmedi:** Altındağ, Çankaya ve
  Yenimahalle bu dönemde zaten ayrı ilçelerdi; "Merkez" 31-57 bin seçmenli
  bir kalıntı ve sınırı hiçbir halef kümesiyle güvenilir biçimde
  eşleşmiyor. Satır tabloda görünür, haritada çizilmez.

## Bilinen kapsam sınırı

Satırlar modern (veya 1984-1995'teki tarihsel) poligonlara bağlandığı için,
1961-1987 arasında henüz kurulmamış ilçelerin alanı (örn. 1987-1990
dalgasında kurulan ilçeler) haritada nötr/gri kalır, oyu ise ebeveyn
ilçenin satırındadır. Bu, 1984/1989 yerel ve 1991 verisiyle aynı davranış.

## Yeniden çalıştırmak

```bash
python3 scripts/pipelines/genel_ilce_1961_1987/fetch_tuik_ilce.py 1961 1965 1969 1973 1977 1983 1987
python3 scripts/pipelines/historical_geo/build_metro_merkez.py   # shapely gerekir
python3 scripts/pipelines/genel_ilce_1961_1987/merge_into_normalized.py          # kuru çalışma
python3 scripts/pipelines/genel_ilce_1961_1987/merge_into_normalized.py --write
python3 scripts/regenerate_checksums.py data/normalized
python3 scripts/build.py
```
