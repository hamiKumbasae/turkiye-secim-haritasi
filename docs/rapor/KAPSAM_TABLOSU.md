# Seçim verisi kapsam tablosu

> `scripts/rapor/kapsam_tablosu.py` üretir, elle düzenlemeyin. Yalnız depodaki veriye dayanır.
> Görev tanımı: `YAPILACAKLAR.md` (2., 3., 9. ve 10. maddeler). Kaynak günlüğü:
> `data/kaynaklar/ARASTIRMA_KAYDI.md`. İl il kırılım: `kapsam_il_bazinda.csv`.

**Sayım:** *Birim* kaynaktaki ilçe/belediye satırıdır; seçimden sonra kurulan ilçelerin boş satırları
sayılmaz. *Sonuçlu* en az bir oyu olan satırdır; yalnız kazananı bilinen satır eksik sayılır.
*Dönemdeki ilçe* İçişleri kuruluş tarihlerinden; yerel seçimde birim belediye olduğu için satır
sayısı bundan farklı olabilir. Kalite: COMPLETE ≥ %99,5 · MOSTLY_COMPLETE ≥ %90 · PARTIAL ≥ %50 ·
VERY_PARTIAL > 0 · NONE araştırıldı, kaynak yok · UNKNOWN henüz araştırılmadı.
Güvenilirlik: A birincil/resmî · D zayıf/keşif (Wikipedia).

## Genel durum özeti

76 satır (46 seçim; yerel seçimlerde başkanlık, belediye meclisi ve il genel meclisi ayrı): COMPLETE 50, MOSTLY_COMPLETE 3, PARTIAL 6, VERY_PARTIAL 2, NONE 3, UNKNOWN 12.

- **Genel seçim:** 20 satırdan 17 tam; eksik olanlar: 1950 (NONE), 1954 (NONE), 1957 (NONE).
- **Referandum:** 7 satırın hepsi ilçe düzeyinde tam.
- **Yerel seçim:** 45 satırdan 22 tam; eksik olanlar: 1950 (VERY_PARTIAL), 1950 BM (UNKNOWN), 1950 İGM (UNKNOWN), 1955 (VERY_PARTIAL), 1955 BM (UNKNOWN), 1955 İGM (UNKNOWN), 1963 BM (UNKNOWN), 1963 İGM (UNKNOWN), 1968 BM (UNKNOWN), 1968 İGM (UNKNOWN), 1973 BM (UNKNOWN), 1973 İGM (UNKNOWN), 1977 BM (UNKNOWN), 1977 İGM (UNKNOWN), 1984 BM (PARTIAL), 1984 İGM (PARTIAL), 1989 BM (MOSTLY_COMPLETE), 1994 BM (PARTIAL), 1994 İGM (PARTIAL), 1999 BM (PARTIAL), 1999 İGM (PARTIAL), 2004 BM (MOSTLY_COMPLETE), 2004 İGM (MOSTLY_COMPLETE).
- **Cumhurbaşkanlığı:** 4 satırın hepsi ilçe düzeyinde tam.
- **Tam ama zayıf kaynaklı:** 1963 yerel, 1968 yerel, 1973 yerel, 1977 yerel — sayılar tam, ancak satırların bir kısmı ya da tamamı yalnız Wikipedia'dan; A kaynağıyla doğrulanmadı.

## Ana tablo

| Seçim türü | Yıl | Oylama | İl verisi | İlçe verisi | Dönemdeki ilçe | Birim | Sonuçlu | Eksik | Eksik % | Kalite | En iyi mevcut kaynak | Yeni araştırma? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Genel seçim | 1950 | - | 63/63 | Yok | 478 | – | 0 | 478 | 100,0 | NONE | YSK (A) | Hayır (kaynak araması kapandı) |
| Genel seçim | 1954 | - | 64/64 | Yok | 506 | – | 0 | 506 | 100,0 | NONE | YSK (A) | Hayır (kaynak araması kapandı) |
| Genel seçim | 1957 | - | 67/67 | Yok | 560 | – | 0 | 560 | 100,0 | NONE | YSK (A) | Hayır (kaynak araması kapandı) |
| Genel seçim | 1961 | - | 67/67 | Tam | 636 | 636 | 636 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1965 | - | 67/67 | Tam | 637 | 637 | 637 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1969 | - | 67/67 | Tam | 638 | 638 | 638 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1973 | - | 67/67 | Tam | 638 | 638 | 638 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1977 | - | 67/67 | Tam | 638 | 638 | 638 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1983 | - | 67/67 | Tam | 640 | 640 | 640 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1987 | - | 67/67 | Tam | 646 | 646 | 646 | 0 | 0,0 | COMPLETE | TÜİK (A) | Hayır |
| Genel seçim | 1991 | - | 74/74 | Tam | 895 | 894 | 894 | 0 | 0,0 | COMPLETE | mertnuhoglu tabanı, TÜİK ile karşılaştırılmış (A) | Hayır |
| Genel seçim | 1995 | - | 79/79 | Tam | 918 | 918 | 918 | 0 | 0,0 | COMPLETE | mertnuhoglu tabanı, TÜİK ile karşılaştırılmış (A) | Hayır |
| Genel seçim | 1999 | - | 80/80 | Tam | 921 | 921 | 921 | 0 | 0,0 | COMPLETE | mertnuhoglu tabanı, TÜİK ile karşılaştırılmış (A) | Hayır |
| Genel seçim | 2002 | - | 81/81 | Tam | 923 | 923 | 923 | 0 | 0,0 | COMPLETE | mertnuhoglu tabanı, TÜİK ile karşılaştırılmış (A) | Hayır |
| Genel seçim | 2007 | - | 81/81 | Tam | 923 | 923 | 923 | 0 | 0,0 | COMPLETE | mertnuhoglu tabanı, TÜİK ile karşılaştırılmış (A) | Hayır |
| Genel seçim | 2011 | - | 81/81 | Tam | 977 | 957 | 957 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Genel seçim | 2015 Haziran | - | 81/81 | Tam | 972 | 970 | 970 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Genel seçim | 2015 Kasım | - | 81/81 | Tam | 972 | 970 | 970 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Genel seçim | 2018 | - | 81/81 | Tam | 972 | 972 | 972 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Genel seçim | 2023 | - | 81/81 | Tam | 972 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Referandum | 1961 | - | 67/67 | Tam | 636 | 636 | 636 | 0 | 0,0 | COMPLETE | TÜİK/DİE (A) | Hayır |
| Referandum | 1982 | - | 67/67 | Tam | 640 | 640 | 640 | 0 | 0,0 | COMPLETE | TÜİK/DİE (A) | Hayır |
| Referandum | 1987 | - | 67/67 | Tam | 645 | 645 | 645 | 0 | 0,0 | COMPLETE | TÜİK/DİE (A) | Hayır |
| Referandum | 1988 | - | 67/67 | Tam | 674 | 674 | 674 | 0 | 0,0 | COMPLETE | TÜİK/DİE (A) | Hayır |
| Referandum | 2007 | - | 81/81 | Tam | 906 | 923 | 923 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Referandum | 2010 | - | 81/81 | Tam | 978 | 957 | 957 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Referandum | 2017 | - | 81/81 | Tam | 972 | 970 | 970 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 1950 | Belediye başkanlığı | 2/63 (+61 yalnız kazanan) | Çok kısmi | 478 | 496 | 5 | 491 | 99,0 | VERY_PARTIAL | Türkçe Wikipedia (D) | Evet |
| Yerel seçim | 1950 | Belediye meclisi | 0 | Yok | 478 | – | 0 | 478 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1950 | İl genel meclisi | 0 | Yok | 478 | – | 0 | 478 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1955 | Belediye başkanlığı | 40/64 (+24 yalnız kazanan) | Çok kısmi | 539 | 530 | 0 | 530 | 100,0 | VERY_PARTIAL | Türkçe Wikipedia (D) | Evet |
| Yerel seçim | 1955 | Belediye meclisi | 0 | Yok | 539 | – | 0 | 539 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1955 | İl genel meclisi | 0 | Yok | 539 | – | 0 | 539 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1963 | Belediye başkanlığı | 67/67 | Tam | 615 | 620 | 620 | 0 | 0,0 | COMPLETE | Türkçe Wikipedia (D) | Doğrulama (D kaynaklı satırlar A kaynağıyla) |
| Yerel seçim | 1963 | Belediye meclisi | 0 | Yok | 615 | – | 0 | 615 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1963 | İl genel meclisi | 0 | Yok | 615 | – | 0 | 615 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1968 | Belediye başkanlığı | 67/67 | Tam | 615 | 619 | 619 | 0 | 0,0 | COMPLETE | Türkçe Wikipedia (D) | Doğrulama (D kaynaklı satırlar A kaynağıyla) |
| Yerel seçim | 1968 | Belediye meclisi | 0 | Yok | 615 | – | 0 | 615 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1968 | İl genel meclisi | 0 | Yok | 615 | – | 0 | 615 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1973 | Belediye başkanlığı | 67/67 | Tam | 616 | 620 | 620 | 0 | 0,0 | COMPLETE | Türkçe Wikipedia (D) | Doğrulama (D kaynaklı satırlar A kaynağıyla) |
| Yerel seçim | 1973 | Belediye meclisi | 0 | Yok | 616 | – | 0 | 616 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1973 | İl genel meclisi | 0 | Yok | 616 | – | 0 | 616 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1977 | Belediye başkanlığı | 67/67 | Tam | 616 | 621 | 621 | 0 | 0,0 | COMPLETE | Türkçe Wikipedia (D) | Doğrulama (D kaynaklı satırlar A kaynağıyla) |
| Yerel seçim | 1977 | Belediye meclisi | 0 | Yok | 616 | – | 0 | 616 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1977 | İl genel meclisi | 0 | Yok | 616 | – | 0 | 616 | 100,0 | UNKNOWN | - | Evet (araştırılmadı) |
| Yerel seçim | 1984 | Belediye başkanlığı | 67/67 | Tam | 624 | 644 | 644 | 0 | 0,0 | COMPLETE | Wikipedia satırları, sayılar DİE kitabıyla teyitli (A) | Hayır |
| Yerel seçim | 1984 | Belediye meclisi | 26/67 | Kısmi | 624 | 644 | 335 | 309 | 48,0 | PARTIAL | TÜİK/DİE (A) | Evet |
| Yerel seçim | 1984 | İl genel meclisi | 56/67 | Kısmi | 624 | 644 | 359 | 285 | 44,3 | PARTIAL | TÜİK/DİE (A) | Evet |
| Yerel seçim | 1989 | Belediye başkanlığı | 67/67 | Tam | 665 | 752 | 752 | 0 | 0,0 | COMPLETE | Wikipedia satırları, sayılar DİE kitabıyla teyitli (A) | Hayır |
| Yerel seçim | 1989 | Belediye meclisi | 66/67 | Neredeyse tam | 665 | 752 | 742 | 10 | 1,3 | MOSTLY_COMPLETE | TÜİK/DİE (A) | Evet |
| Yerel seçim | 1989 | İl genel meclisi | 66/67 | Tam | 665 | 752 | 748 | 4 | 0,5 | COMPLETE | TÜİK/DİE (A) | Hayır |
| Yerel seçim | 1994 | Belediye başkanlığı | 76/76 | Tam | 891 | 931 | 931 | 0 | 0,0 | COMPLETE | TÜİK/DİE %46; YSK %34; Wikipedia satırları, sayılar DİE kitabıyla teyitli %20 (A) | Hayır |
| Yerel seçim | 1994 | Belediye meclisi | 73/76 | Kısmi | 891 | 931 | 653 | 278 | 29,9 | PARTIAL | TÜİK/DİE (A) | Evet |
| Yerel seçim | 1994 | İl genel meclisi | 75/76 | Kısmi | 891 | 931 | 642 | 289 | 31,0 | PARTIAL | TÜİK/DİE (A) | Evet |
| Yerel seçim | 1999 | Belediye başkanlığı | 80/80 | Tam | 904 | 943 | 943 | 0 | 0,0 | COMPLETE | TÜİK/DİE %42; YSK %34; Wikipedia satırları, sayılar DİE kitabıyla teyitli %23 (A) | Hayır |
| Yerel seçim | 1999 | Belediye meclisi | 77/80 | Kısmi | 904 | 943 | 753 | 190 | 20,1 | PARTIAL | TÜİK/DİE (A) | Evet |
| Yerel seçim | 1999 | İl genel meclisi | 79/80 | Kısmi | 904 | 943 | 830 | 113 | 12,0 | PARTIAL | TÜİK/DİE (A) | Evet |
| Yerel seçim | 2004 | Belediye başkanlığı | 81/81 | Tam | 906 | 945 | 945 | 0 | 0,0 | COMPLETE | TÜİK/DİE %50; YSK %26; Wikipedia satırları, sayılar DİE kitabıyla teyitli %25 (A) | Hayır |
| Yerel seçim | 2004 | Belediye meclisi | 79/81 | Neredeyse tam | 906 | 945 | 902 | 43 | 4,6 | MOSTLY_COMPLETE | TÜİK/DİE (A) | Evet |
| Yerel seçim | 2004 | İl genel meclisi | 81/81 | Neredeyse tam | 906 | 945 | 878 | 67 | 7,1 | MOSTLY_COMPLETE | TÜİK/DİE (A) | Evet |
| Yerel seçim | 2009 | Belediye başkanlığı | 81/81 | Tam | 950 | 957 | 956 | 1 | 0,1 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2009 | Belediye meclisi | 81/81 | Tam | 950 | 957 | 956 | 1 | 0,1 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2009 | İl genel meclisi | 81/81 | Tam | 950 | 955 | 955 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2014 | Belediye başkanlığı | 81/81 | Tam | 973 | 970 | 970 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2014 | Belediye meclisi | 81/81 | Tam | 973 | 970 | 970 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2014 | İl genel meclisi | 51/51 | Tam | – | 449 | 449 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2019 | Belediye başkanlığı | 81/81 | Tam | 973 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2019 | Belediye meclisi | 81/81 | Tam | 973 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2019 | İl genel meclisi | 51/51 | Tam | – | 452 | 452 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2024 | Belediye başkanlığı | 81/81 | Tam | 973 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2024 | Belediye meclisi | 81/81 | Tam | 973 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Yerel seçim | 2024 | İl genel meclisi | 51/51 | Tam | – | 452 | 452 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Cumhurbaşkanlığı | 2014 CB | - | 81/81 | Tam | 972 | 970 | 970 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Cumhurbaşkanlığı | 2018 CB | - | 81/81 | Tam | 972 | 972 | 972 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Cumhurbaşkanlığı | 2023 CB 1. tur | - | 81/81 | Tam | 972 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |
| Cumhurbaşkanlığı | 2023 CB 2. tur | - | 81/81 | Tam | 972 | 973 | 973 | 0 | 0,0 | COMPLETE | YSK (A) | Hayır |

**Notlar**

- Yerel seçim 1950 — Belediye başkanlığı: 491 satırda yalnız kazanan parti (oy yok); bazı satırlarda katılım yok; 61 ilde yalnız kazanan / sandalye dağılımı.
- Yerel seçim 1950 — Belediye meclisi: projede kayıt yok; 1950/1955'te başkanlık satırları zaten meclis sandalyesi.
- Yerel seçim 1950 — İl genel meclisi: projede kayıt yok; 1950/1955'te başkanlık satırları zaten meclis sandalyesi.
- Yerel seçim 1955 — Belediye başkanlığı: 530 satırda yalnız kazanan parti (oy yok); 24 ilde yalnız kazanan / sandalye dağılımı.
- Yerel seçim 1955 — Belediye meclisi: projede kayıt yok; 1950/1955'te başkanlık satırları zaten meclis sandalyesi.
- Yerel seçim 1955 — İl genel meclisi: projede kayıt yok; 1950/1955'te başkanlık satırları zaten meclis sandalyesi.
- Yerel seçim 1963 — Belediye başkanlığı: bazı satırlarda katılım yok.
- Yerel seçim 1963 — Belediye meclisi: projede kayıt yok.
- Yerel seçim 1963 — İl genel meclisi: projede kayıt yok.
- Yerel seçim 1968 — Belediye başkanlığı: bazı satırlarda katılım yok.
- Yerel seçim 1968 — Belediye meclisi: projede kayıt yok.
- Yerel seçim 1968 — İl genel meclisi: projede kayıt yok.
- Yerel seçim 1973 — Belediye başkanlığı: bazı satırlarda katılım yok.
- Yerel seçim 1973 — Belediye meclisi: projede kayıt yok.
- Yerel seçim 1973 — İl genel meclisi: projede kayıt yok.
- Yerel seçim 1977 — Belediye başkanlığı: bazı satırlarda katılım yok.
- Yerel seçim 1977 — Belediye meclisi: projede kayıt yok.
- Yerel seçim 1977 — İl genel meclisi: projede kayıt yok.
- Yerel seçim 1984 — Belediye başkanlığı: bazı satırlarda seçmen, katılım yok.
- Yerel seçim 1994 — Belediye başkanlığı: 9 satırda ilçe belediyesi yerine büyükşehir/ilçe geneli toplamı; bazı satırlarda seçmen, katılım yok.
- Yerel seçim 1994 — Belediye meclisi: bazı satırlarda katılım yok.
- Yerel seçim 1994 — İl genel meclisi: bazı satırlarda katılım yok.
- Yerel seçim 1999 — Belediye başkanlığı: 41 satırda ilçe belediyesi yerine büyükşehir/ilçe geneli toplamı.
- Yerel seçim 2004 — Belediye başkanlığı: 24 satırda ilçe belediyesi yerine büyükşehir/ilçe geneli toplamı.
- Yerel seçim 2014 — İl genel meclisi: yalnız büyükşehir olmayan 51 ilde seçilir (6360 sayılı Kanun).
- Yerel seçim 2019 — İl genel meclisi: yalnız büyükşehir olmayan 51 ilde seçilir (6360 sayılı Kanun).
- Yerel seçim 2024 — İl genel meclisi: yalnız büyükşehir olmayan 51 ilde seçilir (6360 sayılı Kanun).

## Referandumlar: alan denetimi

Ülke sonucu ayrı kayıt değildir; il toplamlarından hesaplanır. *var* = sonuçlu satırların ≥ %95'inde,
*kısmi* = bir kısmında, *yok* = hiçbirinde.

| Referandum | Düzey | İlçe durumu | EVET | HAYIR | Geçerli | Geçersiz | Katılım | Kayıtlı seçmen | Sandık |
|---|---|---|---|---|---|---|---|---|---|
| 9 Temmuz 1961 | il | – | var | var | var | var | var | var | var |
| 9 Temmuz 1961 | ilçe | Tam | var | var | var | var | var | var | var |
| 7 Kasım 1982 | il | – | var | var | var | var | var | var | var |
| 7 Kasım 1982 | ilçe | Tam | var | var | var | var | var | var | var |
| 6 Eylül 1987 | il | – | var | var | var | var | var | var | var |
| 6 Eylül 1987 | ilçe | Tam | var | var | var | var | var | var | var |
| 25 Eylül 1988 | il | – | var | var | var | var | var | var | var |
| 25 Eylül 1988 | ilçe | Tam | var | var | var | var | var | var | var |
| 21 Ekim 2007 | il | – | var | var | var | yok | var | var | var |
| 21 Ekim 2007 | ilçe | Tam | var | var | var | yok | var | var | var |
| 12 Eylül 2010 | il | – | var | var | var | yok | var | var | var |
| 12 Eylül 2010 | ilçe | Tam | var | var | var | kısmi | var | var | var |
| 16 Nisan 2017 | il | – | var | var | var | yok | var | var | var |
| 16 Nisan 2017 | ilçe | Tam | var | var | var | kısmi | var | var | var |

## Yerel seçimler: A/B/C/D sınıflaması

A tam veri (≥ %90) · B kısmi · C yalnız il/genel toplam · D sonuç veri seti yok.

| Yıl | Belediye başkanlığı | Belediye meclisi | İl genel meclisi |
|---|---|---|---|
| 1950 | B (yalnız kazanan) | D | D |
| 1955 | B (yalnız kazanan) | D | D |
| 1963 | A (%100,0) | D | D |
| 1968 | A (%100,0) | D | D |
| 1973 | A (%100,0) | D | D |
| 1977 | A (%100,0) | D | D |
| 1984 | A (%100,0) | B (%52,0) | B (%55,7) |
| 1989 | A (%100,0) | A (%98,7) | A (%99,5) |
| 1994 | A (%100,0) | B (%70,1) | B (%69,0) |
| 1999 | A (%100,0) | B (%79,9) | B (%88,0) |
| 2004 | A (%100,0) | A (%95,4) | A (%92,9) |
| 2009 | A (%99,9) | A (%99,9) | A (%100,0) |
| 2014 | A (%100,0) | A (%100,0) | A (%100,0) |
| 2019 | A (%100,0) | A (%100,0) | A (%100,0) |
| 2024 | A (%100,0) | A (%100,0) | A (%100,0) |

1984 ve 1989'u yanlışlıkla "eksik" saymayın: başkanlık satırlarının tamamı DİE kitaplarıyla
teyitli. Bu yıllardaki boşluk meclis sonuçlarında (taranmış kitabın okunamayan satırları).

## Araştırma önceliği (yalnız eksik seçimler)

Öncelik kalite/önem değil, araştırma verimliliğidir: 1 tamamlanmaya çok yakın → 4 neredeyse hiç veri yok.

| Öncelik | Seçim | Eksiklik | Mevcut veri | Araştırılması gereken kaynak türü |
|---|---|---|---|---|
| 1 — Tamamlanmaya çok yakın | Yerel seçim 1989 belediye meclisi | 10 birim (%1,3) | 742/752 birim; 10 il kısmi, 57 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 1 — Tamamlanmaya çok yakın | Yerel seçim 2004 belediye meclisi | 43 birim (%4,6) | 902/945 birim; 25 il kısmi, 56 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 1 — Tamamlanmaya çok yakın | Yerel seçim 2004 il genel meclisi | 67 birim (%7,1) | 878/945 birim; 40 il kısmi, 41 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 2 — Kısmi veri mevcut | Yerel seçim 1999 il genel meclisi | 113 birim (%12,0) | 830/943 birim; 54 il kısmi, 26 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 2 — Kısmi veri mevcut | Yerel seçim 1999 belediye meclisi | 190 birim (%20,1) | 753/943 birim; 59 il kısmi, 21 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 2 — Kısmi veri mevcut | Yerel seçim 1994 belediye meclisi | 278 birim (%29,9) | 653/931 birim; 4 il hiç yok, 56 il kısmi, 16 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 2 — Kısmi veri mevcut | Yerel seçim 1994 il genel meclisi | 289 birim (%31,0) | 642/931 birim; 9 il hiç yok, 36 il kısmi, 31 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 2 — Kısmi veri mevcut | Yerel seçim 1984 il genel meclisi | 285 birim (%44,3) | 359/644 birim; 66 il kısmi, 1 il tam | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 2 — Kısmi veri mevcut | Yerel seçim 1984 belediye meclisi | 309 birim (%48,0) | 335/644 birim; 2 il hiç yok, 65 il kısmi | Basılı DİE kitabının okunamayan sayfaları elle/yeniden OCR; YSK il kurulu tutanakları |
| 3 — Dağınık veri mevcut | Yerel seçim 1950 belediye başkanlığı | 491 birim (%99,0) | 5/496 birim; 62 il hiç yok, 1 il tam | DİE 1950/1955 mahalli seçim yayınları, il yıllıkları, dönemin gazeteleri |
| 3 — Dağınık veri mevcut | Genel seçim 1950 | 478 birim (%100,0) | il düzeyi tam (63/63) | Parçalı il çalışmaları (ACADEMIC-002), yerel gazeteler, BCA; ulusal kaynak araması kapandı |
| 3 — Dağınık veri mevcut | Genel seçim 1954 | 506 birim (%100,0) | il düzeyi tam (64/64) | Parçalı il çalışmaları (ACADEMIC-002), yerel gazeteler, BCA; ulusal kaynak araması kapandı |
| 3 — Dağınık veri mevcut | Yerel seçim 1955 belediye başkanlığı | 530 birim (%100,0) | 0/530 birim; 63 il hiç yok | DİE 1950/1955 mahalli seçim yayınları, il yıllıkları, dönemin gazeteleri |
| 3 — Dağınık veri mevcut | Genel seçim 1957 | 560 birim (%100,0) | il düzeyi tam (67/67) | Parçalı il çalışmaları (ACADEMIC-002), yerel gazeteler, BCA; ulusal kaynak araması kapandı |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1950 belediye meclisi | 478 birim (%100,0) | yok | İstatistik Umum Müdürlüğü yayınları, il yıllıkları, dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1950 il genel meclisi | 478 birim (%100,0) | yok | İstatistik Umum Müdürlüğü yayınları, il yıllıkları, dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1955 belediye meclisi | 539 birim (%100,0) | yok | İstatistik Umum Müdürlüğü yayınları, il yıllıkları, dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1955 il genel meclisi | 539 birim (%100,0) | yok | İstatistik Umum Müdürlüğü yayınları, il yıllıkları, dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1963 belediye meclisi | 615 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1963 il genel meclisi | 615 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1968 belediye meclisi | 615 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1968 il genel meclisi | 615 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1973 belediye meclisi | 616 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1973 il genel meclisi | 616 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1977 belediye meclisi | 616 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |
| 4 — Neredeyse hiç veri yok | Yerel seçim 1977 il genel meclisi | 616 birim (%100,0) | yok | DİE Mahalli İdareler Seçimi Sonuçları kitapları (TÜİK kütüphanesi katalog kontrolü), dönemin gazeteleri |

