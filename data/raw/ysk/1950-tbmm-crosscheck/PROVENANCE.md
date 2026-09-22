# 1950 çoklu kaynak doğrulaması — ham kanıt

`sources.yml`'deki `1950` girişinin `discrepancies` alanının dayandığı ham
belge. `1950_Secim_Sonuclari_il_bazli_ayri_sayfa.pdf` —
`https://www.ysk.gov.tr/doc/dosyalar/docs/1950MilletvekiliSecimi/
1950_Secim_Sonuclari.pdf`'den 2026-09-22'de indirildi. Bu, `../1950-1977/`
klasöründeki il-bazlı arşivden **AYRI** bir YSK sayfası — 1950'ye özel,
il bazında seçmen/oy kullanan/parti oyları tablosu. İçeriği `../1950-1977/`
ile karşılaştırıldı, il bazında BİREBİR AYNI çıktı (örn. Ankara: DP 146.876,
CHP 126.081, Millet Partisi 26.196) — yani YSK'nin bu iki farklı sayfası
kendi arasında tutarlı.

TBMM'nin `www5.tbmm.gov.tr/develop/owa/secim_sorgu.secimdeki_partiler?
p_secim_yili=1950` sayfasının rakamları için (PDF/indirilebilir dosya değil,
dinamik sorgu sonucu) `../../../scripts/genel-1950-1977-pipeline/
ysk_national_totals.json`'daki `_tbmm_1950` anahtarına bakın — orada kaynak
URL ve çekilme tarihiyle birlikte kayıtlı.

## Bütünlük

`checksums.sha256` — 2026-09-22.
