# Güncel, basitleştirilmiş il/ilçe geometrisi

`../raw/`'daki `ttezer/turkiye-harita-verisi` kaynağından `mapshaper`
(`-simplify visvalingam 8% keep-shapes`) ile basitleştirilmiş, GÜNCEL
(2024 itibarıyla) il/ilçe sınırları. Tarihsel/eski yıllara özgü sınırlar
için `../historical/`'a bakın.

- `turkiye_il_sinirlari.geojson` — il: 387k → 15k nokta
- `turkiye_ilce_sinirlari.geojson` — ilçe: 663k → 73.5k nokta

Mahalle düzeyi geometri (`mahalle_geo.json`, çok daha büyük) henüz burada
değil — `index.html`'in gömülü verisinde kalmaya devam ediyor, `data/
normalized/` + `scripts/build.py` v1 ile birlikte (bkz. proje planı,
Milestone 6-7) buraya taşınacak.

## Doğrulama

Bu iki dosyanın içeriği (JSON düzeyinde, sıralı anahtar/girinti ile
karşılaştırıldığında), 2026-09-22 itibarıyla `index.html`'e gömülü
`turkiye_il_sinirlari.geojson` / `turkiye_ilce_sinirlari.geojson`
anahtarlarıyla BİREBİR AYNI — bu bir kopya değil, şu an gerçekten
kullanılan geometrinin kendisi.
