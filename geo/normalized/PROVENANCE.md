# Güncel, basitleştirilmiş il/ilçe geometrisi

`../raw/`'daki `ttezer/turkiye-harita-verisi` kaynağından `mapshaper`
(`-simplify visvalingam 8% keep-shapes`) ile basitleştirilmiş, GÜNCEL
(2024 itibarıyla) il/ilçe sınırları. Tarihsel/eski yıllara özgü sınırlar
için `../historical/`'a bakın.

- `turkiye_il_sinirlari.geojson` — il: 387k → 15k nokta
- `turkiye_ilce_sinirlari.geojson` — ilçe: 663k → 73.5k nokta

- `mahalle_geo.json` — mahalle/muhtarlık düzeyi poligonlar, osm_id bazında
  tekilleştirilmiş (bkz. `../../data/normalized/PROVENANCE.md` — oy verisi
  ayrı, `data/normalized/mahalle/`'de), `scripts/normalize.py` ile üretildi

## Doğrulama

Üç dosyanın içeriği de (Python derin eşitlik ile), 2026-09-22 itibarıyla
`index.html`'e gömülü karşılıklarıyla BİREBİR AYNI doğrulandı — bunlar birer
kopya değil, şu an gerçekten kullanılan geometrinin kendisi.
