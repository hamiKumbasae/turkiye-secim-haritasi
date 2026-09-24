# YSK Açık Veri — il / ilçe / belde bazında toplanmış sonuçlar

**Kaynak:** `acikveri.ysk.gov.tr/api/getSecimSandikSonucList` (sandık düzeyi),
seçim listesi `getSecimDetayList`, parti sütunları `getSandikSecimSonucBaslikList`.
**Script:** `scripts/pipelines/election_import/fetch_belde_agrege.js`.
**Çekildi:** 2026-09-24.

Her dosya bir (seçim, seçim türü) çiftidir. Sandıklar (il, ilçe, belde_ID)
anahtarıyla toplanır; belde sandıkları ilçe toplamına karışmaz. Bu, projedeki
eski `fetch_and_aggregate.js`'ten farkıdır. Küçük seçimlerde (`--ham`) sıfır
olmayan alanlarıyla sandık satırları da `hamSandik` altında saklanır.

| Dosya | secimId | tür | Not |
|---|---|---|---|
| 2019istanbul_yenileme | 16643 | 6 (büyükşehir başkanlığı) | 23 Haziran 2019; 39 ilçe, 31.186 sandık (ham sandıklar dahil) |
| 2024yenileme_baskan | 20273 | 2 (belediye başkanlığı) | 2 Haziran 2024; 7 birim |
| 2024yenileme_meclis | 20273 | 3 (belediye meclisi) | 4 birim |
| 2026ara_baskan | 21272 | 2 | 7 Haziran 2026 mahalli ara seçimi; 5 birim |
| 2026ara_meclis | 21272 | 3 | 5 birim |
| <yıl>yerel_belediye_meclisi | 4290, 11979, 16400, 20260 | 3 | 2009: 2.924 birim (1.968 belde), 2014: 1.364, 2019: 1.359, 2024: 1.363 |
| <yıl>yerel_il_genel_meclisi | aynı | 4 | 2009: 81 il / 2.929 birim; 2014 sonrası 51 il (büyükşehirlerde İGM yok) |

Meclis dosyalarında ham sandık satırı saklanmadı (seçim başına yüz binlerce
satır); API parametreleri (secimId, secimTuru) ile yeniden üretilebilir.
2009'da 108 birim haritaya bağlanamadı (sonradan bölünen eski "Merkez"
ilçelerinin YSK kimlikleri; ana veride de bilinen durum).

## Bilinen sınırlar

- Sandık düzeyi toplamlar YSK'nin kesin sonuç ilanından birkaç yüz oy farklı
  olabilir (örn. 2019 İstanbul: CHP 4.742.082 / AK Parti 3.936.068; ilan edilen
  4.741.868 / 3.935.453).
- API belde adını vermiyor; beldeler yalnızca `beldeId` ile tanımlı.
- Bağımsız adayların adları API'de yok; oyları `bagimsizN` sütunlarında.
