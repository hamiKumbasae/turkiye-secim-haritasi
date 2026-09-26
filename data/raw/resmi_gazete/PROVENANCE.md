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

## 9644 (27 Haziran 1957) — 7033 sayılı Kanun (78 kaza) ve ek cetvelleri

`9644.pdf` (75 sayfa = 25 sayfalık gazetenin üç kopyası; ilk kopya okunur), indirilme
2026-09-26. Kanun maddeleri ve cetveller aynı sayıda (mevzuat.gov.tr'de PDF metni
yok). Taranmış, iki sütunlu, zayıf OCR; dönem dili (Vilâyet/Kaza/Nahiye), tekrarlar
"»". Çıkarım: `scripts/pipelines/historical_geo/extract_kaza_kurulus_1957.py` →
`data/kaynaklar/resmi_gazete/ilce_kurulus/7033.json`.

Sonuç **orta güven**: 77 kazanın 50'sinin bloğu okunabildi (başlığı İçişleri 7033
listesiyle eşleşen); soy blok düzeyinde (blokta anılan tüm "X Vilâyeti Y Kazasının"
kaynakları), satır denetimi yok; 11 blokta başka ilden kaynak anılıyor (sütun/başlık
kayması olabilir). Bu yüzden geometri kuralına çevrilmedi (`lineageStatus:
kanun_dogrulanmadi`). Etki sınırlı: bu kazaların tamamı 1960'a kadar yürürlüğe girdi,
1961 ve sonrası seçimlerde ayrı birim. Madde 2: Kuşadası 01.09.1957'de İzmir'den
Aydın'a bağlandı.

## 18237_2 (30 Kasım 1983, 2. mükerrer) — 2963 sayılı Kanun (6 ilçe, Ankara Merkez İlçesinin kaldırılması)

`18237_2.pdf` (27 sayfa = 9 sayfalık ekin üç kopyası; ilk kopya okunur), indirilme
2026-09-26. Kanun asıl 18237 sayısında değil 2. mükerrer sayıda
(`https://www.resmigazete.gov.tr/arsiv/18237_2.pdf`); mevzuat.gov.tr'de PDF metni yok,
Madde 1 (a)–(f) bentleri okuyucu yapılandırmasına aynen aktarıldı. Ek (1)–(6) sayılı
listeler: 104 satır, eksik sıra yok, altı ilçenin altısı tek kaynaklı (Mamak ← Çankaya,
Gölbaşı ← Çankaya, Keçiören ← Altındağ, Sincan ← Yenimahalle, Düziçi ← Bahçe,
Dalaman ← Köyceğiz). **Madde 2:** Ankara İli Merkez İlçesi kaldırılmış, alanı Altındağ'a
bağlanmıştır — 1961–1983 seçim verisindeki geomId'siz Ankara "Merkez" satırı bu ilçedir.

## 22305 (6 Haziran 1995) — KHK 550: sekiz ilçe ve üç il (Karabük, Kilis, Yalova)

`22305.pdf` (96 sayfa), indirilme 2026-09-26. Madde 1 bentleri 'adıyla' ile bitmediği
için okuyucu yapılandırmasına aynen aktarıldı. Ek (1)–(8) sayılı listeler: 130 satır,
eksik sıra yok; sekiz ilçenin sekizi tek kaynaklı (Musabeyli, Polateli ← Kilis;
Elbeyli ← Oğuzeli; Çınarcık, Çiftlikköy, Termal ← Yalova; Altınova ← Karamürsel;
Armutlu ← Gemlik). (9)–(11) sayılı listeler yeni illerin dökümü (okunmadı; il
değişiklikleri seçim verisinden tarihleriyle çıkıyor). Başlıklar çift harfli basılmış
(bir yerde farklı aksanla: 'LLÎİSSTTEE').

## 20202 (21 Haziran 1989) — 3578 sayılı 4 İl ve 5 İlçe Kurulması Hakkında Kanun

`20202.pdf` (96 sayfa), indirilme 2026-09-26; maddeler `data/raw/mevzuat/3578.pdf`.
Ek (1)–(5) sayılı listeler: 99 satır, eksik sıra yok; beş ilçenin beşi tek kaynaklı
(Ağaçören, Sarıyahşi ← Şereflikoçhisar; Pazaryolu ← İspir; Kâzımkarabekir ← Karaman;
Güzelyurt ← Aksaray). Madde 2: Kırıkkale, Aksaray, Bayburt, Karaman illeri; (6)–(9)
sayılı listeler (yeni illerin dökümü) okunmadı.

## 20522_1 (18 Mayıs 1990, mükerrer) — 3647 sayılı Kanun (2 il, 5 ilçe)

`20522_1.pdf` (33 sayfa), indirilme 2026-09-26; maddeler `data/raw/mevzuat/3647.pdf`.
Ek (1)–(5) sayılı listeler: 72 satır, eksik sıra yok; beş ilçenin beşi tek kaynaklı
(Köprüköy ← Pasinler; Hacılar ← Melikgazi; Hasankeyf ← Gercüş; Karapürçek ← Akyazı;
Aydınlar/Tillo ← Siirt Merkez). Madde 2: Batman ve Şırnak illeri; Şırnak bendinde
Andaç ve Ortaköy köyleri Çukurca'dan Uludere'ye bağlandı.

## 22801 (28 Ekim 1996) — 4200 sayılı Kanun (3 ilçe, Osmaniye ili)

`22801.pdf` (96 sayfa), indirilme 2026-09-26; maddeler `data/raw/mevzuat/4200.pdf`.
Ek (1)–(3) sayılı listeler: 35 satır, eksik sıra yok. Toprakkale ← Osmaniye, Sumbas ←
Kadirli (tek kaynaklı); Hasanbeyli ← Osmaniye (5) + Bahçe (2) (çok kaynaklı). Madde 2:
Osmaniye ili; (4) sayılı liste (ilin dökümü) okunmadı.

## 17581 (21 Ocak 1982) — 2585 sayılı Kanun (Ceylanpınar, Aliağa)

`17581.pdf` (64 sayfa), indirilme 2026-09-26; kanun ve cetveller s. 4 (mevzuat.gov.tr'de
PDF metni yok, Madde 1 okuyucuya aynen aktarıldı). "CETVEL No." biçimi: köy + "X İli Y
İlçesi Z Bucağından", tekrarlar "»" (okuyucuda `bicim: cetvel`). Ceylanpınar ←
Viranşehir (tek kaynak, 1 köy + bucak merkezi); Aliağa ← Menemen (12), Bergama (6),
Foça (2) — çok kaynaklı. 21 satır, eksik sıra yok.

## 21803 (29 Aralık 1993) — 3949 sayılı 3 İlçe Kurulması Hakkında Kanun

`21803.pdf` (96 sayfa), indirilme 2026-09-26; maddeler `data/raw/mevzuat/3949.pdf`.
Listeler ilçe başına değil tür başına (Güzelbahçe: (1) mahalle + (2) köy; Esenler (3)
mahalle; Gümüşova (4) köy); aynı ilçenin listeleri birleştirildi. Mahalle listelerinde
eski ilçe **yazılmamış** (Güzelbahçe ve Esenler tek kaynaklı sayılmaz; Esenler'in
kaynağı repodaki denetimde de bulunamamıştı). Gümüşova ← Cumaova (tek kaynak).
Tekrar işareti '"'. Madde 2: Narlıbahçe → Narlıdere, Cumaova → Cumayeri (ad değişikliği;
listelerde kaynak ilçe kanun anındaki adla yazılı).

## 12952 (17 Temmuz 1968) — 1055 sayılı Kanun (Abana, Bozkurt)

`12952.pdf` (33 sayfa), indirilme 2026-09-26; kanun s. 5 (çok sütunlu, kadro cetvelleriyle
iç içe). Madde 1: Kastamonu'nun Abana ve Pazaryeri kasabaları merkez olmak üzere Abana ve
Bozkurt ilçeleri. Cetvel (1) yalnız köy adlarını veriyor, **köylerin eski ilçesi
yazılmamış** → soy bu kaynaktan çıkmaz (`kanun_kaynak_yazilmamis`). Bozkurt 1968'de
kurulduğu için 1961/1965 seçim verisindeki Kastamonu "Bozkurt" satırları bu ilçe olamaz
(veri çelişkisi notu).

## 23901 (9 Aralık 1999) — KHK 584: Düzce ili, Kaynaşlı ve Derince ilçeleri

`23901.pdf` (98 sayfa), indirilme 2026-09-26. KHK'nin ilk sayfası (maddeler) bu PDF'te
yok; bentler ek listelerin başlıklarından ve İçişleri kaydından. Ek (1)–(2) sayılı listeler:
25 satır, eksik sıra yok; Kaynaşlı ← Düzce (19 köy), Derince ← Kocaeli Merkez (6 köy);
ikisi de tek kaynaklı. (3) sayılı liste (Düzce ilinin dökümü) okunmadı.

## 21247_1 (3 Haziran 1992, mükerrer) — 3806 sayılı Kanun (13 ilçe, Ardahan ve Iğdır)

`21247_1.pdf` (33 sayfa), indirilme 2026-09-26; maddeler `data/raw/mevzuat/3806.pdf`.
Bent numarası liste numarasına eşit değil (6. bent Sultanbeyli'nin ek listesi yok); liste
→ ilçe eşlemesi mevzuat metninden. Damal ← Hanak (15), Karakoyunlu ← Iğdır (12): tek
kaynaklı. İstanbul (Avcılar, Bağcılar, Güngören, Bahçelievler, Maltepe, Tuzla) ve İzmir
(Çiğli, Gaziemir, Balçova, Narlıbahçe) mahalle listelerinde eski ilçe yazılmamış; bu
ilçeler repoda kaymakamlık kaynaklarıyla zaten doğrulanmış (`repo_dogrulanmis`).
(13)–(14) sayılı listeler (yeni illerin dökümü) okunmadı.

## 11496 (4 Eylül 1963) — 309 sayılı Kanun (Gaziosmanpaşa)

`11496.pdf` (9 sayfa), indirilme 2026-09-26; kanun s. 1. Cetvel kadro tablosuyla iç içe iki
sütunlu basıldığından (1) sayılı cetvelin 10 satırı okuyucu yapılandırmasına aynen
aktarıldı (`satirlarElle`): ilk satır "İstanbul İli Eyüp İlçesi Rami Bucağından", diğerleri
boş (= aynı). Gaziosmanpaşa ← Eyüp (tek kaynak; Madde 1: "Eyüp İlçesinin Göktepe Bucağında").
