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
| <yıl>yerel_belediye_meclisi / _il_genel_meclisi | 4290, 11979, 16400, 20260 | 3 / 4 | 2009-2024 genel mahalli seçimler (ayrı commit) |

## Bilinen sınırlar

- Sandık düzeyi toplamlar YSK'nin kesin sonuç ilanından birkaç yüz oy farklı
  olabilir (örn. 2019 İstanbul: CHP 4.742.082 / AK Parti 3.936.068; ilan edilen
  4.741.868 / 3.935.453).
- API belde adını vermiyor; beldeler yalnızca `beldeId` ile tanımlı.
- Bağımsız adayların adları API'de yok; oyları `bagimsizN` sütunlarında.
