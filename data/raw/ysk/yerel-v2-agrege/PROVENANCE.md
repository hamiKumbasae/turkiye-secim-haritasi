# YSK Açık Veri — 2009–2024 yerel seçim il/ilçe agregeleri (bütün partiler)

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimSandikSonucList` (sandık düzeyi), parti sütunları
`scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/baslik_*.json`
(`getSandikSecimSonucBaslikList`).
**Script:** `scripts/pipelines/election_import/fetch_yerel_v2.js` (değiştirilmeden),
`scripts/pipelines/election_import/fetch_bagimsiz_aday.js` (bağımsızlar aday aday).
**Çekildi:** 2026-10-12, GitHub Actions üzerinde (`.github/workflows/ysk-yerel-cek.yml`,
`.github/workflows/ysk-bagimsiz-aday.yml`). Portal geliştirme ortamından açılmadığı için çekim
GitHub'ın sunucularında çalıştırıldı; çıktı `ysk-yerel-veri` dalına yazılıp buraya alındı.
Başarısız sorgu: 0 (dört seçimde de).

| Dosya | secimId | İçerik |
|---|---|---|
| 2009yerel.json | 4290 | 81 il, 998 ilçe sorgusu (956 dolu) |
| 2014yerel.json | 11979 | 81 il, 998 ilçe sorgusu (970 dolu) |
| 2019yerel.json | 16400 | 81 il, 998 ilçe sorgusu (973 dolu) |
| 2024yerel.json | 20260 | 81 il, 998 ilçe sorgusu (973 dolu) |
| bagimsiz-aday.json | 4290, 11979 | Bağımsızların toplamı kayıttaki kazanandan fazla görünen 13 ilçe; `bagimsizN` sütunları ayrı ayrı |

Dosya biçimi `fetch_yerel_v2.js` çıktısıdır: `iller[ilId]` (büyükşehirde secimTuru=6 toplamı,
diğerlerinde il merkezi ilçesinin secimTuru=2 sonucu), `ilceler["ilId-ilceId"]` (her ilçenin kendi
secimTuru=2 sonucu), `colToName` (YSK sütunu → parti adı). Bağımsızların toplamı `bagimsiz0_ALDIGI_OY`
sütunundadır (`ballot_votes.js`).

## Ne için kullanıldı

`merge_yerel_v2.py` büyük partiler dışındaki partileri tek bir `Diğer` satırında topluyordu.
`diger_ayristir_yerel.py` bu agregelerle `Diğer`i partilere ayırdı (kural ve sonuç sayıları
betiğin başında ve `scripts/pipelines/election_import/PROVENANCE.md` içinde).

## Bilinen sınırlar

- Bağımsız adayların adları API'de yok (ilçe başlık listesi boş döndü); adaylar yalnız oy pusulası
  sırasıyla (`bagimsiz1`, `bagimsiz2`, …) ayrılabiliyor.
- Sandık düzeyi toplamlar YSK'nin kesin sonuç ilanından birkaç oy farklı olabilir; kayıtlardaki
  `kazanan` alanı bu yüzden yalnız `Diğer` olduğu yerde değiştirildi.
