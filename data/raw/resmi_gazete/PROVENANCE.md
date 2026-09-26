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

## 20523 (20 Mayıs 1990) — 3644 sayılı 130 İlçe Kurulması Hakkında Kanun ve ek listeleri

`20523.pdf` (96 sayfa, taranmış, OCR metinli), indirilme 2026-09-25. Kanunun ek
(1)–(130) sayılı listeleri s. 9–75: her yeni ilçeye bağlanan bucak/kasaba/köy/mahalle
ve eski ilçesi, eski bucağı. Kanun maddeleri ayrıca `data/raw/mevzuat/3644.pdf`
(mevzuat.gov.tr, temiz metin). Çıkarım:
`scripts/pipelines/historical_geo/extract_ilce_kurulus_kanunu.py 3644` →
`data/kaynaklar/resmi_gazete/ilce_kurulus/3644.json` (tarihsel idari katman, Faz 2).

OCR özellikleri: sıra numarasında 'I' / 'l' / ')' = 1, 'S' = 5 ya da 8 (bağlamdan),
kalın başlıklarda harfler çift. Eski ilçe adı, o ilin 1991 genel seçimindeki ilçe
adlarıyla bulanık eşlendi; her listede sıra numaraları 1..n kesintisiz doğrulandı
(2.056 satırın tamamı eşlendi, eksik sıra yok). 130 yeni ilçenin tamamı İçişleri
kuruluş listesinde de 3644 ile kayıtlı.

## 19507 (4 Temmuz 1987) — 3392 sayılı 103 İlçe Kurulması Hakkında Kanun ve ek listeleri

`19507.pdf` (103 sayfa, taranmış, OCR metinli), indirilme 2026-09-26. Kanun maddeleri
`data/raw/mevzuat/3392.pdf`. Çıkarım aynı betikle (`extract_ilce_kurulus_kanunu.py 3392`)
→ `data/kaynaklar/resmi_gazete/ilce_kurulus/3392.json`.

Bu sayıya özgü OCR/dizgi: 94. bent Resmî Gazete'de "4." basılmış (bentler 'adıyla'
bitişine göre bölünür); sıra numaraları "I." "J." "3," "S"; bazı listelerde satır iki
satıra kaymış; Hisarcık listesinde "—" = üst satırla aynı; mahalle listeleri iki sütunlu.
İstanbul'un 1987 ilçelerinin (Pendik, Küçükçekmece, Ümraniye, Kağıthane) mahalle
listelerinde mahallelerin eski ilçesi **yazılmamış** (54 satır, `kaynakYazilmamis`);
bu ilçeler tek kaynaklı sayılmaz. 3 satır OCR nedeniyle eşlenemedi; Demirözü, Pendik,
Ümraniye listelerinde sıra boşluğu var. 103 yeni ilçenin 98'i İçişleri listesinde 3392
ile kayıtlı; kalan 5'i (Pendik, Küçükçekmece, Büyükçekmece, Ümraniye, Konak) sonradan
bölündüğü için repodaki tarihsel poligonlarla (`HIST-*`) eşleşti.
