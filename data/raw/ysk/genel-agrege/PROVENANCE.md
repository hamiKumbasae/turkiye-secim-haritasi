# YSK Açık Veri — 2011–2023 genel seçim il/ilçe agregeleri (bütün partiler)

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimSandikSonucList` (sandık düzeyi, secimTuru=8, yurt içi),
parti sütunları `scripts/pipelines/mahalle_veri/parti-sutun-eslemeleri/baslik_*.json`.
**Script:** `scripts/pipelines/election_import/fetch_and_aggregate.js` (değiştirilmeden).
**Çekildi:** 2026-10-14, GitHub Actions üzerinde (`.github/workflows/ysk-genel-cek.yml`); portal
geliştirme ortamından açılmıyor. Başarısız sorgu: 0 (beş seçimde de).

| Dosya | secimId | Dolu ilçe |
|---|---|---|
| 2011.json | 7468 | 957 |
| 2015Haziran.json | 13884 | 970 |
| 2015Kasim.json | 14868 | 970 |
| 2018.json | 16300 | 972 |
| 2023.json | 20230 | 973 |

Dosya biçimi `fetch_and_aggregate.js` çıktısıdır: `iller[ilId]` (ilçelerin toplamı),
`ilceler["ilId-ilceId"]`, `colToName` (YSK sütunu → parti/ittifak adı), `errors`. Bağımsızların
toplamı `bagimsiz0_ALDIGI_OY` sütunundadır (`ballot_votes.js`).

## Ne için kullanıldı

`merge_genel_yerel.py` büyük partiler dışındaki partileri tek bir `Diğer` satırında topluyordu.
`scripts/pipelines/election_import/diger_ayristir_ysk.py` bu agregelerle `Diğer`i, eski toplamla
birebir tutan satırlarda partilere ayırdı (5.127 kayıt). Genel seçimlerde `Diğer` hiçbir yerde
kazanan değildi; kazanan değişmedi.

## Ayrılmayan satırlar

- 2011, 67 satır: BDP destekli bağımsızlar projede "BDP" olarak etiketli (`etiket_2011_bdp.py`),
  YSK'de bağımsız; adlandırılmış parti tutmadığı için dokunulmadı.
- 2011 (4) ve 2015 Haziran (27) satır: eski `Diğer + Bağımsız` toplamı YSK'nin bugünkü verisinden
  1–4 oy farklı.
- Eşleşen YSK satırı olmayan 17 satır (tarihsel ilçeler).
