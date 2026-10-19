# YSK Açık Veri — muhtarlık düzeyi genel seçim sonuçları (30 büyükşehir, bütün partiler)

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimSandikSonucList` (sandık düzeyi, secimTuru=8, yurt içi),
parti sütunları `scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/baslik_*.json`.
**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_muhtarlik_tum.js`.
**Çekildi:** 2026-10-19, GitHub Actions üzerinde (`.github/workflows/ysk-mahalle-cek.yml`). Başarısız sorgu: 0.

| Dosya | secimId | İlçe | Muhtarlık | Seçmen |
|---|---|---|---|---|
| 2015Haziran.json | 13884 | 544 | 25.699 | 41.683.822 |
| 2015Kasim.json | 14868 | 544 | 25.701 | 41.999.670 |
| 2018.json | 16300 | 544 | 25.621 | 43.869.807 |
| 2023.json | 20230 | 544 | 25.829 | 47.518.673 |

Seçmen toplamları sitenin ilçe kayıtlarıyla birebir aynı. Her ilçe için muhtarlık başına seçmen, oy kullanan,
geçerli/geçersiz oy, sandık sayısı ve BÜTÜN parti/ittifak sütunları (küçük partiler "Diğer"e toplanmaz;
bağımsızlar `bagimsiz0_ALDIGI_OY`). Muhtarlığı olmayan sandıklar (cezaevi vb.) ilçe başına `_muhtarliksiz`.

Kullanım: `scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py` bu sonuçları TKGM mahalle
sınırlarıyla eşleştirip sitenin mahalle verisine yazar.
