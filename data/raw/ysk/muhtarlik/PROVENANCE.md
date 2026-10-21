# YSK Açık Veri — muhtarlık düzeyi seçim sonuçları (81 il, bütün partiler/adaylar)

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimSandikSonucList` (sandık düzeyi, yurt içi; secimTuru 8 genel,
9 cumhurbaşkanlığı, 2 yerel ilçe/belediye başkanlığı), parti/aday sütunları
`scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/baslik_*.json`.
**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_muhtarlik_tum.js`.
**Çekildi:** 30 büyükşehir 2026-10-19; 81 il 2026-10-20 (2009, 2014, 2019 yerel 2026-10-21, run 39593047911), GitHub Actions üzerinde (`.github/workflows/ysk-mahalle-cek.yml`,
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

2024 yerel ilçe belediye başkanlığı oyudur: büyükşehir olmayan illerde köyler bu oylamaya katılmaz, bu yüzden
muhtarlık sayısı daha azdır. YSK listesindeki 998 ilçenin 25'i kaldırılmış eski birimler (büyükşehirlerin "X MERKEZ"i, Eminönü) ya da aynı
ilçenin ikinci kaydıdır (Çağlayancerit, 19 Mayıs/Ondokuzmayıs); site 973 bugünkü ilçeyi kullanır
(`data/raw/ysk/acikveri-ilce-geomid-eslemesi.json`).

2009 yerel: 14 ilin o yılki "MERKEZ" ilçesi (Aydın, Balıkesir, Denizli, Hatay, Kahramanmaraş, Malatya, Manisa, Mardin,
Muğla, Ordu, Tekirdağ, Trabzon, Şanlıurfa, Van; 2,6 milyon seçmen) sonradan birkaç ilçeye bölündüğü için bugünkü
ilçelere eşlenmez; bu ilçelerin mahalleleri haritada yok (önceki veride de yoktu). Seçmen toplamı sitenin 2009
ilçe kayıtlarından 3.146 (%0,008) az.

Seçmen toplamları sitenin ilçe kayıtlarıyla birebir aynı. Her ilçe için muhtarlık başına seçmen, oy kullanan,
geçerli/geçersiz oy, sandık sayısı ve BÜTÜN parti/ittifak sütunları (küçük partiler "Diğer"e toplanmaz;
bağımsızlar `bagimsiz0_ALDIGI_OY`). Muhtarlığı olmayan sandıklar (cezaevi vb.) ilçe başına `_muhtarliksiz`.

Kullanım: `scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py` bu sonuçları TKGM mahalle
sınırlarıyla eşleştirip sitenin mahalle verisine yazar.
