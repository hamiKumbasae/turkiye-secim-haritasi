# YSK Açık Veri — muhtarlık düzeyi seçim sonuçları (81 il, bütün partiler/adaylar)

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimSandikSonucList` (sandık düzeyi, yurt içi; secimTuru 8 genel,
9 cumhurbaşkanlığı, 2 yerel ilçe/belediye başkanlığı), parti/aday sütunları
`scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/baslik_*.json`.
**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_muhtarlik_tum.js`.
**Çekildi:** 30 büyükşehir 2026-10-19; 81 il 2026-10-20 (2009, 2014, 2019 yerel 2026-10-21, run 39593047911; 2010 ve 2017 halkoylaması, 2011 genel, 2014 ve 2018 CB 2026-10-21, run 39604120185), GitHub Actions üzerinde (`.github/workflows/ysk-mahalle-cek.yml`,
run 39426266447). Başarısız sorgu: 0. 30 büyükşehrin 2015–2023 genel verisi iki çekimde birebir aynı.

| Dosya | secimId | secimTuru | İlçe | Muhtarlık | Seçmen |
|---|---|---|---|---|---|
| 2015Haziran.json | 13884 | 8 | 998 | 50.015 | 53.772.719 |
| 2015Kasim.json | 14868 | 8 | 998 | 50.020 | 54.084.541 |
| 2018.json | 16300 | 8 | 998 | 49.302 | 56.406.836 |
| 2023.json | 20230 | 8 | 998 | 49.931 | 60.774.566 |
| 2023cb1tur.json | 20230 | 9 | 998 | 49.931 | 60.774.566 |
| 2023cb2tur.json | 20240 | 9 | 998 | 49.931 | 60.823.248 |
| 2024yerel.json | 20260 | 2 | 998 | 32.184 | 57.801.470 |
| 2009yerel.json | 4290 | 2 | 998 | 18.589 | 39.722.118 |
| 2014yerel.json | 11979 | 2 | 998 | 31.678 | 48.906.096 |
| 2019yerel.json | 16400 | 2 | 998 | 32.008 | 53.246.898 |
| 2010referandum.json | 6522 | 7 | 998 | 52.993 | 49.495.493 |
| 2011.json | 7468 | 8 | 998 | 53.086 | 50.237.343 |
| 2014cb.json | 13340 | 9 | 998 | 49.910 | 52.920.981 |
| 2017referandum.json | 15575 | 7 | 998 | 50.217 | 55.408.773 |
| 2018cb.json | 16300 | 9 | 998 | 49.302 | 56.406.836 |

2024 yerel ilçe belediye başkanlığı oyudur: büyükşehir olmayan illerde köyler bu oylamaya katılmaz, bu yüzden
muhtarlık sayısı daha azdır. YSK listesindeki 998 ilçenin 25'i kaldırılmış eski birimler (büyükşehirlerin "X MERKEZ"i, Eminönü) ya da aynı
ilçenin ikinci kaydıdır (Çağlayancerit, 19 Mayıs/Ondokuzmayıs); site 973 bugünkü ilçeyi kullanır
(`data/raw/ysk/acikveri-ilce-geomid-eslemesi.json`).

Eski ilçeler: bir seçimin site kaydı bugünkü ilçelerin birleşimi olan tarihsel bir ilçe kullanıyorsa
(ör. 2009'da HIST-Kahramanmaraş-Merkez = Dulkadiroğlu + Onikişubat; `geo/historical/district_splits.json`),
o ilçenin muhtarlıkları halef ilçelerin sınırlarıyla eşlenir ve tarihsel ilçenin altına yazılır. Bugüne eşlenmeyen
eski "X MERKEZ" kayıtları seçmen sayısı birebir tutan seçim kaydına gider (Aydın Merkez → Efeler).
2009 yerel seçmen toplamı sitenin ilçe kayıtlarından 3.146 (%0,008) az: Elazığ Ağın ve Yozgat Kadışehri'nde
29 Mart 2009 seçimi iptal edilip yenilendi, YSK açık verisinde yok (site bu iki ilçeyi Vikipedi'den alır).

Seçmen toplamları sitenin ilçe kayıtlarıyla birebir aynı. Her ilçe için muhtarlık başına seçmen, oy kullanan,
geçerli/geçersiz oy, sandık sayısı ve BÜTÜN parti/ittifak sütunları (küçük partiler "Diğer"e toplanmaz;
bağımsızlar `bagimsiz0_ALDIGI_OY`). Muhtarlığı olmayan sandıklar (cezaevi vb.) ilçe başına `_muhtarliksiz`.

Kullanım: `scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py` bu sonuçları TKGM mahalle
sınırlarıyla eşleştirip sitenin mahalle verisine yazar.
