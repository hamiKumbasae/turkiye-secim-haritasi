# Güncel il/ilçe geometrisi

GÜNCEL il/ilçe sınırları. Tarihsel/eski yıllara özgü sınırlar için `../historical/`'a bakın.

## İlçe ve il katmanı (2026-11-01'den beri)

`scripts/pipelines/ilce_katmani/build_ilce_katmani.py` üretir (yöntem ve sonuçlar:
`docs/rapor/ILCE_KATMANI_2026-11-01.md`). Kimlikler ve özellikler önceki dosyayla aynı (ilçe `{id, plaka}`,
il `{plaka}`, aynı sıra).

- Kaynak sınırlar:
  - **OpenStreetMap** ilçe sınırları (`admin_level=6`, `../../data/raw/osm/ilce/`, ODbL 1.0, © OpenStreetMap
    katkıcıları): TKGM birimleriyle en az HDX kadar uyumlu olan 803 ilçe (`ilce_duzeltme.json`).
  - **HDX COD-AB-TUR** (OCHA, CC BY-IGO; `ttezer/turkiye-harita-verisi` commit `83eeb7a1`,
    `dist/geojson/districts.geojson`, sha256 `16fb6b98…af067ad`, 663.098 nokta): OSM'nin TKGM ile daha kötü
    uyduğu 131 ilçe ve OSM'nin bıraktığı alanlar. Ham dosya depoda yok (bkz. `../raw/PROVENANCE.md`).
  - **İstanbul** (39 ilçe): önceki dosyadaki geometri aynen (tarihsel İstanbul katmanları ona göre kurulu).
- TKGM idari birimleri (`../../data/raw/tkgm/mahalle/`) yalnız hakem: iki kaynak aynı alanı istediğinde ya da
  alan boşta kaldığında hangi ilçeye ait olduğunu söyler; sınır çizgisi TKGM'den çizilmez.
- Topoloji: bütün aday sınırlar düğümlenip yüzlere ayrılır, her yüz tek ilçeye verilir; ortak yaylar uçları
  sabit Douglas-Peucker 0,001° (~100 m) ile sadeleştirilir, 4 ondalık. Komşu ilçeler aynı yayı paylaşır:
  dikiş boşluğu ve örtüşme yok (İstanbul'un kendi içindeki eski ince boşluklar hariç).
- `turkiye_il_sinirlari.geojson` = ilçelerin il il birleşimi (il ile ilçe sınırları birebir aynı).
- `turkiye_ilce_sinirlari.geojson`: 170.023 nokta (önce 73.826); `turkiye_il_sinirlari.geojson`: il il birleşim.
- `ilce_duzeltme.json`: hangi ilçenin OSM'den alındığı ve ölçüleri (`ilce_duzeltme_sec.py`).

## 2026-11-01 öncesi

`ttezer/turkiye-harita-verisi` (HDX COD-AB-TUR) kaynağından `mapshaper` (`-simplify visvalingam 8%
keep-shapes`) ile il ve ilçe ayrı ayrı sadeleştirilmişti (il 387k → 15k, ilçe 663k → 73,5k nokta).
Komşu ilçeler arasında 6.062 dikiş boşluğu ve 2.052 örtüşme vardı; il ile ilçeler birebir örtüşmüyordu
(`docs/rapor/GEOMETRI_DENETIMI.md` 4.5).

## Mahalle

- `mahalle_geo.json` — mahalle/muhtarlık düzeyi poligonlar (bkz. `../../data/normalized/PROVENANCE.md` —
  oy verisi ayrı, `data/normalized/mahalle/`'de); `tkgm_muhtarlik_esle.py uygula` yeniden yazar.
