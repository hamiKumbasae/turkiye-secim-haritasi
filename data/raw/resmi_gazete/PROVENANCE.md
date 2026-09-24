# Resmî Gazete — Yüksek Seçim Kurulu ara seçim bildirileri

**Kaynak:** `https://www.resmigazete.gov.tr/arsiv/<sayı>.pdf` (taranmış, OCR metinli).
**İndirilme:** 2026-09-24.

| Sayı | Tarih | İçerik | Kullanılan sayfalar |
|---|---|---|---|
| 12922 | 12 Haziran 1968 | 2 Haziran 1968 Senato kısmi ve milletvekili ara seçimi kesin sonuçları | 13-17 |
| 15394 | 25 Ekim 1975 | 12 Ekim 1975 Senato ve milletvekili ara seçimi sonuçları (YSK kararı 473) | 11-17 |
| 19247 | 10 Ekim 1986 | 28 Eylül 1986 milletvekili ara seçimi (YSK duyuru 1986/15) | 19-25 |

Bildiriler il (1986: seçim çevresi) düzeyinde; ilçe kırılımı yok. İki sütunlu
sayfalar sol/sağ yarı olarak ayrı okundu. Çıkarım:
`scripts/pipelines/resmi_gazete/extract_ara_secim.py` → `data/kaynaklar/resmi_gazete/genel/`
ve `data/normalized/ek/yenileme_ara/<yıl>mv_ara.json`.

## Doğrulama

Her il/çevre için partiler + bağımsız = geçerli oy; ulusal toplam TESAV
"Milletvekili Ara Seçim Sonuçları" (DİE kaynaklı) ile karşılaştırıldı:

| Seçim | İl/çevre | TESAV ile |
|---|---|---|
| 1968 | 5 | TİP'te 1 oy fark (İstanbul/Urfa satırlarında kaynağın kendi 1 oyluk tutarsızlığı) |
| 1975 | 6 | DP'de 1 oy fark (Urfa, OCR "4.44S") |
| 1986 | 11 | birebir |

OCR'ın rakam yerine harf okuduğu değerlerde ("3S210") yalnızca basılı rakamlara
uyan adaylar denendi (S→3/5/8, O→0), toplam kısıtına en yakını alındı; satırın
`ocrDuzeltme` alanında okunan/düzeltilen değer ve gerekçe yazılı.

1951 ara seçimi ve 2003 Siirt yenilemesinin Resmî Gazete sayıları bu oturumda
bulunamadı (2003: 25045 mükerrer sayısının arşiv adresi açılmadı). 1966 ve 1979
ara seçimleri ilçe düzeyinde DİE Senato kitaplarından (`data/raw/tuik/senato-metin/`).
