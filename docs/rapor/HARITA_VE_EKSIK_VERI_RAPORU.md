# Türkiye Seçim Haritası — İlçe Poligonu Sorunları ve Eksik Veri Raporu

> **Arşiv raporu:** Aşağıdaki sayılar 27.09.2026 durumuna aittir. 04.10.2026
> düzeltmelerinden sonra güncel durum `ozet.json`, `poligon_durumu.csv` ve
> `eksik_secim_verisi.csv` dosyalarındadır. 2007 referandumu 923 ilçeye
> tamamlandı; İstanbul 1989/1991 ve Tillo meclis eşleşmeleri düzeltildi.

Tarih: 27.09.2026 · Depo durumu: `801483a` sonrası · Kapsam: 46 seçim (genel, yerel başkanlık,
referandum, cumhurbaşkanlığı) + 18 yerel meclis kaydı (il genel meclisi, belediye meclisi)

Bu rapor, haritada ilçeleri doğru alana oturtma sorununu ve hiçbir kaynaktan alınamayan seçim
verilerini tek yerde toplar. Başka bir araca/modele verilip çözüm önerisi alınması için yazıldı:
her bölüm kendi başına okunabilir, sayılar bu depodaki dosyalardan üretilmiştir.

**Bu klasördeki dosyalar**

| Dosya | İçerik |
|---|---|
| `HARITA_VE_EKSIK_VERI_RAPORU.md` | Bu rapor |
| `poligon_durumu.csv` | Her seçim × il × bugünkü ilçe poligonu için, veri gösterilemeyen her durumun satırı (3.143 satır) |
| `eksik_secim_verisi.csv` | Sonucu olmayan her il/ilçe satırı ve nedeni (1.960 satır) |
| `ozet.json` | Seçim başına sayılar ve alan payları (aşağıdaki tablonun kaynağı) |
| `../../scripts/rapor/harita_durum_raporu.py` | Bu dosyaları yeniden üreten betik |

Yeniden üretmek için: `.venv/bin/python scripts/rapor/harita_durum_raporu.py`

---

## 1. Kısa özet

- **2010 ve sonrası neredeyse tam.** 2010 referandumundan 2024 yerel seçimine kadar her seçimde
  972 bugünkü ilçe poligonunun 969–972'si kendi sonucuyla boyanıyor. Kalan tek sorun Tillo
  (Siirt): hiçbir seçim kaydında satırı yok.
- **Asıl sorun 1961–2007 arası.** Bu dönemde bugünkü ilçelerin bir kısmı henüz kurulmamıştı.
  Onların alanı o dönemde başka bir ilçeye aitti ve o ilçenin sonucuyla boyanmalıydı. Bunu
  yapabilmek için "bugünkü X ilçesinin alanı o gün hangi ilçedeydi" bilgisi gerekiyor. Bu bilgi
  tam olmadığında poligon **taranmış (çizgili)** kalıyor: "bu seçimde henüz yoktu".
  - 1961–1988: seçim başına 41–45 ilçe taranmış, **ilin alanının ~%2'si**.
  - 1989–2007: seçim başına 8–31 ilçe, alanın ~%0,3–1,3'ü.
  - 1950 ve 1955 yerel: 150–181 ilçe, alanın %11–14'ü (bu iki yılın ilçe verisi de zayıf).
- Toplam **234 farklı bugünkü ilçe** en az bir seçimde taranmış görünüyor. Bunların hangi eski
  ilçeden ayrıldığı:
  - 77'sinde hiç bilinmiyor;
  - 40'ında birden çok eski ilçeden parça alınmış, bölüşümü bilinmiyor;
  - 39'unda kaynak (1957 kanun cetveli) zayıf okunuyor;
  - 4'ünde kanunda yazılmamış;
  - 74'ünün soyu biliniyor ama bazı seçimlerde gösterilemiyor. Bunların bir kısmı hemen
    düzeltilebilir: 2007 referandumu ve 2009/2011 (§5.1). Diğerlerinde ebeveyn ilçenin kendisi
    de o tarihte henüz yoktu (1950/1955 yerel, İstanbul 1987 öncesi), bu yüzden onlar da yeni
    kaynak gerektiriyor.
- **Eksik veri:**
  - 1950, 1954 ve 1957 genel seçimlerinin ilçe sonuçları hiçbir kaynakta yok.
  - 1950/1955 yerel seçimlerinde ilçelerin yalnız kazanan partisi biliniyor.
  - 1984–2004 yerel meclis sonuçlarının ilçe kırılımı yalnız taranmış DİE kitaplarında var ve
    bir kısmı okunamıyor. 1984'te ilçelerin yarıdan fazlası boş.
  - Mahalle düzeyi sonuçlar yalnız 2009 ve sonrası için var.

---

## 2. Harita nasıl çiziliyor (teknik mantık)

### 2.1 Veri modeli

Her seçim bir JSON kaydı (`data/normalized/elections/<tür>/<anahtar>.json`):

```
{ ad, tur, contestType, resultBasis, majorPartiler,
  iller:   [ {ad, plaka, oy:{parti:{oy,oran}}, kazanan, secmen, gecerliOy, katilim, ...} ],
  ilceler: [ {ad, plaka, geomId, oy:{...}, kazanan, ...} ] }
```

- `plaka`, **o seçim tarihindeki** il bağlılığıdır. Örneğin 1987'de Kırıkkale'nin ilçeleri
  plaka 6 (Ankara) altındadır.
- `geomId`, satırın çizileceği poligonun kimliğidir:
  - `TR-D-PP-NNN`: bugünkü ilçe;
  - `HIST-*`, `HISTK-*`, `HISTY-*`: tarihsel birleşim poligonu (§2.3).
- Yerel meclis kayıtları (`data/normalized/meclis_harita/<yıl>yerel_<igm|bm>.json`) aynı
  biçimdedir. İskelet olarak aynı yılın başkanlık kaydının ilçe satırlarını kullanırlar.
- **Coğrafi kodlama (geocoding) yok.** Satır poligona adla değil, veri hazırlanırken atanan
  `geomId` ile bağlanır. Adla eşleme yalnız veri hattında yapılır; ön yüz yalnız `geomId`'ye
  bakar.

### 2.2 Geometri kaynakları

| Dosya | Kaynak | Ne var |
|---|---|---|
| `geo/normalized/turkiye_ilce_sinirlari.geojson` | ttezer/turkiye-harita-verisi (HDX kökenli), mapshaper Visvalingam %8 ile sadeleştirilmiş | **Yalnız bugünkü** 973 ilçe (2024 sınırları) |
| `geo/normalized/turkiye_il_sinirlari.geojson` | aynı | Bugünkü 81 il |
| `geo/historical/turkiye_il_sinirlari_era*.geojson` | Bu projede bugünkü ilçelerin birleştirilmesiyle üretildi | 6 dönem için il sınırları (1950: 63 il … 1999: 80 il) |
| `geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson` | Bu projede üretildi | 283 tarihsel birleşim poligonu (HIST 36, HISTK 222, HISTY 25) |
| `geo/historical/district_splits.json` | Bu projede üretildi | Her birleşim poligonunun hangi bugünkü ilçeleri kapladığı (`hideIds`) |
| `geo/historical/idari/harita_notlari.json` | `apply_idari_merges.py` üretir | Taranmış ilçelerin kuruluş kanunu ve kaynak ilçeleri; birleşimlerin içeriği |
| `geo/normalized/mahalle_geo.json` | OSM (muhtarlık) | Mahalle poligonları (yalnız 2009+ mahalle sonuçları için) |

**Önemli:** Elde hiçbir tarihsel **ilçe** sınırı verisi yok. Geçmişin bütün ilçe sınırları,
bugünkü ilçe poligonlarının birleşimi olarak kuruluyor.

### 2.3 Tarihsel birleşim poligonları nasıl üretiliyor

Bugünkü bir ilçe geçmişte başka bir ilçenin parçasıysa, o seçim için eski ilçe şöyle kurulur:
eski ilçe = eski ilçenin bugünkü devamı + ondan ayrılan bugünkü ilçelerin birleşimi.
(`shapely.unary_union`, dikiş delikleri doldurulur.)

Hangi ilçenin nereden ayrıldığı şu kaynaklardan gelir:

1. **Kuruluş kanunlarının ek listeleri (Resmî Gazete).** Her yeni ilçeye bağlanan köy, bucak
   ve mahallenin eski ilçesi yazıyor. İşlenen kanunlar: 3644, 3392, 2963, KHK 550, 3578, 3647,
   4200, 2585, 3949, 1055, KHK 584, 3806, 309, 5747, 6360 ve 7033 (orta güven).
   Ayrıntı: `geo/historical/idari/README.md`.
   - **Tek kaynak** (bütün birimler tek eski ilçeden): ilçe o eski ilçeye katılır, kesin.
   - **Çok kaynak:** birimlerin en az %70'i ilin Merkez ilçesinden geliyorsa bütünüyle Merkez'e
     katılır ("Merkez çoğunluğu" kuralı, 14 birleşim). Küçük kaynak ipucunda yazılır: örneğin
     "Konyaaltı: %92 Merkez, Kemer 1 birim". Diğerleri çözülmez ve taranır.
2. **Repoda elle doğrulanmış birleşimler** (`HIST-*`, özellikle İstanbul ve İzmir): kaymakamlık
   tarihçe sayfaları ve kanun metniyle.
3. **Nüfus sayımı kitapları** (DİE 1960/1985/1990 idari bölünüş): köy bağlılığından eski ilçe
   (`sayim_kaniti.json`, İstanbul).
4. **İl merkezi birleşimleri** (`HISTY-*`, yerel 1963–2004): o dönemde il merkezi belediyesi
   birden çok bugünkü ilçeyi kaplıyordu (Ankara 1977: Altındağ + Çankaya + Yenimahalle).

Üretim zinciri:

```
extract_icisleri_kurulus.py → build_idari_katman.py (soy kaydı)
ekle_il_merkezi_satirlari.py → build_idari_katman.py → apply_idari_merges.py (HISTK + harita_notlari)
→ scripts/build.py (tek dosya index.html) / scripts/export_static.py (atlas)
```

### 2.4 Ön yüzde çizim algoritması (`src/js/map.js`)

Projeksiyon: eşdikdörtgen (equirectangular), boylam enlemin kosinüsüyle ölçeklenir.
Görünüme sığdırılır ve SVG `path` üretilir. Harita karosu ve kütüphane yok.

Ülke görünümü:
1. Seçim yılına göre il sınırı dönemi seçilir (`GEO_ERAS`: 1950, 1954, 1957–1987, 1991, 1995,
   1999, 2002+ bugünkü).
2. Her il, `iller` satırındaki kazananın rengiyle boyanır.

İl görünümü (`renderProvinceMap(plaka)`):
1. `veriPoligonları`: bu ilin (o tarihteki `plaka`) sonucu olan satırlarının `geomId`
   poligonları. Bunlar bugünkü ya da tarihsel poligon olabilir.
2. Bu listede hiç poligon yoksa il tek parça çizilir ve ilin rengiyle boyanır (1950–1957 genel).
3. `gizli`: veriPoligonları içindeki tarihsel birleşimlerin kapladığı bugünkü ilçeler. Bunlar
   ayrıca çizilmez.
4. `veriYok`: ilin bugünkü ilçeleri − veriPoligonları − gizli. Bunlar alt katmanda çizilir:
   - `harita_notlari.secimler[yıl]` içinde kaydı varsa **taranmış**. İpucu: kuruluş yılı,
     kanun, ayrıldığı ilçeler.
   - kaydı yoksa **gri**. İpucu: satırın `not`'u ya da "Bu dönem için veri yok".
5. Veri poligonları kazanana göre, "Katılım" ve "Parti" modlarında renk skalasıyla boyanır.

Bu yüzden haritada **üst üste binme yok**. Bu, `tests/validate_elections.py` ile 1.342 seçim×il
senaryosunda denetleniyor. Buna karşılık, bir alan hiçbir veri poligonuna girmiyorsa boş
(taranmış ya da gri) kalıyor.

---

## 3. Neden doğru ve eksiksiz çıkarılamıyor

1. **Tarihsel ilçe sınırı verisi yok.** Açık GIS kaynaklarının (HDX/OCHA, GADM, OSM) hepsi
   bugünkü sınırları veriyor. 1950–2012 arası hiçbir ilçe sınırı için sayısal bir kaynak
   bulunamadı.
2. **Yeni ilçeler çoğu zaman birden çok eski ilçeden parça aldı.** Bir köy Terme'den, iki köy
   Ünye'den… Bu köylerin bugünkü konumu ve sınırı elimizde yok. Bu yüzden eski ilçenin sınırı
   bugünkü poligonları birleştirerek kurulamıyor, köy düzeyinde bölmek gerekiyor.
   - Bugünkü köy/mahalle poligonları (OSM muhtarlık) yalnız kısmen var.
   - Mahalle düzeyinde bölüşüm denendi (Arnavutköy, Sultangazi, Esenyurt, Başakşehir) ama
     arşivlendi: `arsiv/mahalle-bolusumu/`, git etiketi `arsiv/mahalle-bolusumu`. Nedeni:
     şehir içi mahallelerin 1987 öncesi bağlılığı hiçbir kaynakta yok.
3. **Kaynak listeleri eksik ya da okunamıyor.**
   - 1953–1960 kanunları (6068, 6191, 6321, 6324, 6325, 7033) ya bulunamadı ya da taranmış
     cetvelleri zayıf (7033: 77 bloğun 50'si okunabildi).
   - Bazı listelerde eski ilçe hiç yazılmamış: 3392'de İstanbul, 3949'da Esenler, 1055'te
     Abana/Bozkurt.
4. **Kuruluş ile ilk seçim aynı değil.** 3392 ile 04.07.1987'de kurulan 97 ilçe 29.11.1987
   genel seçimine ayrı girmedi. Haritada bunlar "bu seçime ayrı girmedi" diye taranıyor (13
   poligon), ama oylarının hangi eski ilçe satırında sayıldığı kaynakta yok.
5. **Yerel seçim satırı ilçe değil belediyedir.** İl merkezi belediyesi, büyükşehir alt
   kademesi ve belde birden çok ilçe alanına yayılabiliyor. Belde adı kaynakta olmadığında
   (YSK 2009) belde bir bugünkü ilçeye bağlanamıyor.
6. **Sadeleştirme ve dikiş delikleri.** Sadeleştirilmiş bugünkü poligonlar birleştirilince
   aralarında ince boşluklar kalıyordu. `dikis_deliklerini_doldur.py` ile dolduruldu; gerçek
   delikler (göl, başka ilçe) korunuyor.

---

## 4. Poligon sorunlarının türleri ve kapsamı

### 4.1 Durum sınıfları

`poligon_durumu.csv` → `durum` sütunu:

| Durum | Haritada | Anlamı |
|---|---|---|
| `veri` | Kendi rengi | Poligonun kendi satırı ve sonucu var |
| `birlesimde` | Birleşimin rengi | Tarihsel birleşim poligonunun parçası (doğru gösterim) |
| `tarali_henuz_yok` | Taranmış | İlçe henüz kurulmamış; alanının hangi eski ilçeye ait olduğu çözülmemiş |
| `tarali_ayri_girmedi` | Taranmış | Kurulmuş ama seçime ayrı girmemiş (1987 genel, 1987/1988 referandum) |
| `gri_satir_bos` | Gri | Satır var, sonuç yok: kaynak okunamadı, eşleşmedi ya da yer tutucu |
| `gri_satir_yok` | Gri | Bu poligon için hiç satır yok ve açıklama yok |
| `poligonsuz_veri` | Çizilmez | Sonuç var ama çizilecek poligon yok |

Alan payları, o seçimde ilçe verisi olan illerin bugünkü ilçe poligonlarının toplam alanına
oranla hesaplanır (derece², karşılaştırma içindir).

### 4.2 Seçim bazında tablo

"İl tek parça": o seçimde ilçe verisi hiç olmayan ve tek parça çizilen il sayısı. Meclis
kayıtlarında gri alanın büyük kısmı veri eksikliğinden gelir (§6), poligondan değil.

| Seçim | Tür | İl | İl tek parça | İlçe satırı (sonuçlu) | Veri | Birleşimde | Taralı (henüz yok / ayrı girmedi) | Gri (satır boş / satır yok) | Poligonsuz sonuç | Taralı alan % | Gri alan % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1950 | genel | 63 | 63 | 0 (0) | 0 | 0 | 0 / 0 | 0 / 0 | 0 | 0 | 0 |
| 1954 | genel | 64 | 64 | 0 (0) | 0 | 0 | 0 / 0 | 0 / 0 | 0 | 0 | 0 |
| 1957 | genel | 67 | 67 | 0 (0) | 0 | 0 | 0 / 0 | 0 / 0 | 0 | 0 | 0 |
| 1961 | genel | 67 | 0 | 636 (636) | 411 | 434 | 43 / 0 | 0 / 1 | 1 | 2.02 | 0.05 |
| 1965 | genel | 67 | 0 | 637 (637) | 412 | 433 | 43 / 0 | 0 / 1 | 1 | 2.02 | 0.05 |
| 1969 | genel | 67 | 0 | 638 (638) | 414 | 433 | 42 / 0 | 0 / 0 | 1 | 2.02 | 0 |
| 1973 | genel | 67 | 0 | 638 (638) | 414 | 433 | 42 / 0 | 0 / 0 | 1 | 2.02 | 0 |
| 1977 | genel | 67 | 0 | 638 (638) | 414 | 433 | 42 / 0 | 0 / 0 | 1 | 2.02 | 0 |
| 1983 | genel | 67 | 0 | 640 (640) | 417 | 431 | 41 / 0 | 0 / 0 | 1 | 1.97 | 0 |
| 1987 | genel | 67 | 0 | 646 (646) | 426 | 421 | 28 / 13 | 0 / 1 | 0 | 1.97 | 0.02 |
| 1991 | genel | 74 | 0 | 895 (895) | 829 | 94 | 9 / 0 | 0 / 0 | 0 | 0.27 | 0 |
| 1995 | genel | 79 | 0 | 918 (918) | 874 | 76 | 8 / 0 | 0 / 0 | 0 | 0.26 | 0 |
| 1999 | genel | 80 | 0 | 921 (921) | 881 | 76 | 8 / 0 | 0 / 0 | 0 | 0.26 | 0 |
| 2002 | genel | 81 | 0 | 923 (923) | 890 | 75 | 8 / 0 | 0 / 0 | 0 | 0.26 | 0 |
| 2007 | genel | 81 | 0 | 923 (923) | 890 | 75 | 8 / 0 | 0 / 0 | 0 | 0.26 | 0 |
| 2011 | genel | 81 | 0 | 977 (953) | 948 | 9 | 0 / 0 | 15 / 1 | 0 | 0 | 1.13 |
| 2015Haziran | genel | 81 | 0 | 972 (969) | 969 | 0 | 0 / 0 | 3 / 1 | 0 | 0 | 0.15 |
| 2015Kasim | genel | 81 | 0 | 972 (969) | 969 | 0 | 0 / 0 | 3 / 1 | 0 | 0 | 0.15 |
| 2018 | genel | 81 | 0 | 972 (971) | 971 | 0 | 0 / 0 | 1 / 1 | 0 | 0 | 0.08 |
| 2023 | genel | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 1950yerel | yerel · başkanlık | 63 | 0 | 496 (495) | 288 | 374 | 181 / 0 | 0 / 7 | 3 | 14.02 | 1.0 |
| 1955yerel | yerel · başkanlık | 64 | 1 | 530 (528) | 338 | 348 | 150 / 0 | 1 / 12 | 3 | 11.41 | 2.17 |
| 1963yerel | yerel · başkanlık | 67 | 0 | 620 (620) | 402 | 441 | 44 / 0 | 0 / 2 | 0 | 2.03 | 0.05 |
| 1968yerel | yerel · başkanlık | 67 | 0 | 619 (619) | 402 | 442 | 45 / 0 | 0 / 0 | 0 | 2.08 | 0 |
| 1973yerel | yerel · başkanlık | 67 | 0 | 620 (620) | 404 | 440 | 44 / 0 | 0 / 1 | 0 | 2.08 | 0.19 |
| 1977yerel | yerel · başkanlık | 67 | 0 | 621 (621) | 404 | 442 | 43 / 0 | 0 / 0 | 0 | 2.03 | 0 |
| 1984yerel | yerel · başkanlık | 67 | 0 | 644 (644) | 425 | 423 | 41 / 0 | 0 / 0 | 0 | 1.97 | 0 |
| 1989yerel | yerel · başkanlık | 67 | 0 | 752 (752) | 578 | 282 | 29 / 0 | 0 / 0 | 0 | 1.23 | 0 |
| 1994yerel | yerel · başkanlık | 76 | 0 | 932 (932) | 886 | 49 | 8 / 0 | 0 / 7 | 0 | 0.32 | 0.3 |
| 1999yerel | yerel · başkanlık | 80 | 0 | 944 (944) | 914 | 44 | 8 / 0 | 0 / 7 | 0 | 0.27 | 0.3 |
| 2004yerel | yerel · başkanlık | 81 | 0 | 947 (947) | 924 | 41 | 8 / 0 | 0 / 0 | 1 | 0.27 | 0 |
| 2009yerel | yerel · başkanlık | 81 | 0 | 978 (953) | 947 | 11 | 0 / 0 | 14 / 1 | 0 | 0 | 0.79 |
| 2014yerel | yerel · başkanlık | 81 | 0 | 972 (969) | 969 | 0 | 0 / 0 | 3 / 1 | 0 | 0 | 0.15 |
| 2019yerel | yerel · başkanlık | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 2024yerel | yerel · başkanlık | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 1984yerel_bm | yerel · belediye meclisi | 67 | 2 | 644 (335) | 218 | 212 | 41 / 0 | 199 / 202 | 0 | 2.03 | 45.83 |
| 1984yerel_igm | yerel · il genel meclisi | 67 | 0 | 644 (359) | 231 | 247 | 41 / 0 | 194 / 176 | 0 | 1.97 | 41.08 |
| 1989yerel_bm | yerel · belediye meclisi | 67 | 0 | 752 (742) | 570 | 280 | 29 / 0 | 8 / 2 | 0 | 1.23 | 1.49 |
| 1989yerel_igm | yerel · il genel meclisi | 67 | 0 | 752 (748) | 575 | 280 | 29 / 0 | 3 / 2 | 0 | 1.23 | 0.35 |
| 1994yerel_bm | yerel · belediye meclisi | 76 | 4 | 932 (653) | 623 | 33 | 7 / 0 | 236 / 16 | 0 | 0.27 | 30.96 |
| 1994yerel_igm | yerel · il genel meclisi | 76 | 9 | 932 (641) | 611 | 30 | 8 / 0 | 186 / 16 | 0 | 0.36 | 25.2 |
| 1999yerel_bm | yerel · belediye meclisi | 80 | 0 | 944 (752) | 731 | 29 | 8 / 0 | 182 / 15 | 0 | 0.28 | 19.77 |
| 1999yerel_igm | yerel · il genel meclisi | 80 | 0 | 944 (830) | 808 | 33 | 8 / 0 | 105 / 11 | 0 | 0.28 | 9.87 |
| 2004yerel_bm | yerel · belediye meclisi | 81 | 0 | 947 (900) | 884 | 33 | 8 / 0 | 40 / 8 | 0 | 0.27 | 3.44 |
| 2004yerel_igm | yerel · il genel meclisi | 81 | 0 | 947 (877) | 857 | 39 | 8 / 0 | 67 / 2 | 0 | 0.27 | 5.7 |
| 2009yerel_bm | yerel · belediye meclisi | 81 | 0 | 978 (953) | 947 | 11 | 0 / 0 | 14 / 1 | 0 | 0 | 0.82 |
| 2009yerel_igm | yerel · il genel meclisi | 81 | 0 | 978 (952) | 946 | 11 | 0 / 0 | 15 / 1 | 0 | 0 | 0.81 |
| 2014yerel_bm | yerel · belediye meclisi | 81 | 0 | 972 (969) | 969 | 0 | 0 / 0 | 3 / 1 | 0 | 0 | 0.15 |
| 2014yerel_igm | yerel · il genel meclisi | 81 | 30 | 453 (448) | 448 | 0 | 0 / 0 | 5 / 1 | 0 | 0 | 0.38 |
| 2019yerel_bm | yerel · belediye meclisi | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 2019yerel_igm | yerel · il genel meclisi | 81 | 30 | 453 (451) | 451 | 0 | 0 / 0 | 2 / 1 | 0 | 0 | 0.13 |
| 2024yerel_bm | yerel · belediye meclisi | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 2024yerel_igm | yerel · il genel meclisi | 81 | 30 | 453 (451) | 451 | 0 | 0 / 0 | 2 / 1 | 0 | 0 | 0.13 |
| 1961referandum | referandum | 67 | 0 | 636 (636) | 411 | 434 | 43 / 0 | 0 / 1 | 1 | 2.02 | 0.05 |
| 1982referandum | referandum | 67 | 0 | 640 (640) | 417 | 431 | 41 / 0 | 0 / 0 | 1 | 1.97 | 0 |
| 1987referandum | referandum | 67 | 0 | 645 (645) | 424 | 424 | 28 / 13 | 0 / 0 | 0 | 1.97 | 0 |
| 1988referandum | referandum | 67 | 0 | 674 (674) | 469 | 381 | 29 / 10 | 0 / 0 | 0 | 1.92 | 0 |
| 2007referandum | referandum | 81 | 0 | 906 (906) | 884 | 51 | 31 / 0 | 0 / 7 | 0 | 1.31 | 0.6 |
| 2010referandum | referandum | 81 | 0 | 978 (978) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 2017referandum | referandum | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 2014cb | cumhurbaskanligi | 81 | 0 | 972 (969) | 969 | 0 | 0 / 0 | 3 / 1 | 0 | 0 | 0.15 |
| 2018cb | cumhurbaskanligi | 81 | 0 | 972 (971) | 971 | 0 | 0 / 0 | 1 / 1 | 0 | 0 | 0.08 |
| 2023cb1tur | cumhurbaskanligi | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |
| 2023cb2tur | cumhurbaskanligi | 81 | 0 | 972 (972) | 972 | 0 | 0 / 0 | 0 / 1 | 0 | 0 | 0.02 |

### 4.3 Taranmış 234 ilçenin kök nedenleri

Bir ilçe hangi seçimde taranırsa taransın, soy kaydındaki durumuna göre
(`poligon_durumu.csv` → `soy`, `kaynak_ilceler`):

| Soy durumu | İlçe | Ne eksik | Örnekler |
|---|---|---|---|
| `unresolved` | 77 | Hangi eski ilçeden ayrıldığı hiç kaynaklanmadı. Çoğu 1952–1960 kanunları (6068, 6191, 6321, 6324, 6325, 7033); ayrıca 6447 (2013), 7148 (2018), KHK 694 (2017) | Altındağ, Şişli, Erdemli, Keles, Derecik, Sultanhanı, Altınordu |
| `kanun_cok_kaynak` | 40 | Kanun listesinde birden çok eski ilçe var; köy düzeyi bölüşüm gerekli | Çukurova, Pursaklar, Arnavutköy, Başakşehir, Esenyurt, Sultangazi, Didim, Akyurt, Körfez, İkizce, Aliağa, Defne |
| `kanun_dogrulanmadi` | 39 | 7033 (1957–1960) cetveli okundu ama güven orta; geometriye çevrilmedi | Yenimahalle, Bornova, Zeytinburnu, Suluova, Çerkezköy, Yomra |
| `kanun_kaynak_yazilmamis` | 4 | Kanun listesinde eski ilçe sütunu yok | Esenler, Kağıthane, Abana, Bozkurt |
| `kanun_tek_kaynak` | 32 | Tek ebeveyn biliniyor. 2007 referandumunda Merkez satırı olmadığı için uygulanamıyor (§5.1). 1950/1955 yerel seçimlerinde ise ebeveynin kendisi henüz kurulmamıştı; örneğin Etimesgut ve Sincan'ın ebeveyni Yenimahalle 1957'de kuruldu | Başiskele, Kartepe, Arifiye, Serdivan (2007 ref.); Etimesgut, Sincan, Sarıçam, Başmakçı (1950/1955 yerel) |
| `repo_dogrulanmis` | 33 | Birleşim var ama bazı yıllarda devreye girmiyor. İstanbul: Ümraniye 1987'de kuruldu; ondan önce Ümraniye, Ataşehir, Çekmeköy ve Sancaktepe alanının hangi eski ilçelere düştüğü çok kaynaklı ve bölüşüm gerekiyor | Ümraniye, Ataşehir, Çekmeköy, Sancaktepe (1961–1989); Bayraklı, Karabağlar (2007 ref.) |
| `merkez_ilce` | 9 | Eski Merkez ilçenin devamı; yalnız 2007 referandumunda Merkez satırı yok | Efeler, Antakya, İzmit, Adapazarı, Menteşe, Ortahisar |

En çok taranmış il (seçim × ilçe sayısı): İstanbul 236, Ankara 61, Ordu 52, Kastamonu 47,
Adana 41, Samsun 39, Elazığ 38, Tokat 38, Konya 29, Antalya 27, Hakkari 27.

### 4.4 Gri alanlar (sonuç yok)

- **Tillo (Siirt, TR-D-56-007):** Başkanlık, genel, referandum ve CB kayıtlarında hiç satırı
  yok. YSK meclis verisinde (2009–2024) "Tillo" satırı var ama `geomId`'siz geliyor, yani
  ilçe–poligon eşleme tablosunda eksik. Başkanlık verisinin çekildiği hatta da aynı eksik
  olabilir. Kolayca düzeltilebilir.
- **2009 yerel ve 2011 genel, 2012 (6360) bölünmesi:** Yeni ilçelerin satırı var ama boş (seçim
  başına 14–15 poligon): Antakya, Arsuz, Defne, Payas, Merkezefendi, Seydikemer, Ergene,
  Kapaklı, Kilimli, Kozlu, İpekyolu, Tuşba. Bu seçimlerde oylar eski "Merkez" ya da ana ilçe
  satırında sayılıyor. Doğru çözüm, o yıllar için eski Merkez'in birleşim poligonunu devreye
  sokmak. 2009 Denizli ve Hatay Merkez'in başkanlık sonucu da haritada yok.
- **2014–2018:** Kemalpaşa (KHK 694, 2017), Derecik (7148, 2018) ve Sultanhanı (KHK 694,
  2017) kurulmadan önceki seçimlerde satırı boş.
- **1994/1999 yerel, Düzce (7 poligon):** Kaynaşlı satırı plaka 81 ile kayıtlı. O dönemde
  Kaynaşlı Bolu'nun Düzce ilçesine bağlı bir belde, Düzce ili ise 1999 sonunda kuruldu. İl
  haritasında plaka 81 olmadığı için bu satır görünmüyor. Analizde 7 Düzce poligonu gri
  sayılıyor, ama kullanıcı onları Bolu'nun ilçeleri olarak görüyor.

### 4.5 Yaklaşık gösterimler

Bunlar yanlış değil ama kaba:

- **Merkez çoğunluğu kuralı (14 birleşim):** Aksu, Konyaaltı, Eğil, Kocaköy, Edremit (Van),
  Çeltikçi, Defne, Gönen, İhsangazi, Yeşilli, Gülağaç, Demirözü, Hasanbeyli. Birimlerin %70
  veya fazlası Merkez'den geldiği için bütünüyle Merkez'e katıldı. Diğer kaynağın birkaç köyü
  yanlış ilçede görünüyor; ipucunda yazıyor.
- **İl merkezi birleşimleri (`HISTY-*`, yerel 1963–2004):** İl merkezi belediyesinin sonucu,
  şehrin kapladığı bugünkü ilçelerin hepsine boyanıyor. Belediye sınırı ilçe sınırıyla aynı
  değil.
- **Ankara Merkez (1961–1983):** 30.11.1983'te kaldırılıp Altındağ'a katılan ayrı bir ilçe;
  sınırı hiçbir kaynakta yok. Sonucu var ama çizilemiyor (`poligonsuz_veri`, 1961–1983 genel
  ve referandumlar, 1950/1955 yerel).

### 4.6 İl düzeyi

1950, 1954 ve 1957 genel seçimlerinde ilçe verisi yok; iller tek parça boyanıyor. Tarihsel
il sınırları (6 dönem) bugünkü ilçelerden kuruldu ve il düzeyinde tam.

---

## 5. Çözüm için ne gerekir

### 5.1 Eldeki bilgiyle hemen yapılabilecekler

| İş | Etki |
|---|---|
| 2007 referandumu: Merkez satırlarının eksikliği ve 2008 (5747) birleşimleri. Merkez halefleri ve Kocaeli/Sakarya'nın tek kaynaklı ilçeleri | 38 taranmış/gri poligonun büyük kısmı |
| 2009 yerel ve 2011 genel için 2012 öncesi Merkez birleşimleri (Hatay, Van, Tekirdağ, Zonguldak, Muğla, Denizli) | Seçim başına 14–15 gri poligon |
| Tillo'yu ilçe–poligon eşleme tablosuna eklemek | Bütün yıllarda 1 poligon |
| Kemalpaşa, Derecik, Sultanhanı ve Altınordu kanunlarını (KHK 694, 7148, 6447) işlemek | 2009–2018 arası birkaç poligon |
| 1994/1999 yerel Kaynaşlı satırını o dönemin iline (Bolu) almak | 1 satır |

Karar gerektirenler (tahmin sınırında):
- **Merkez olmayan ebeveynler için çoğunluk kuralı.** Örneğin Çekmeköy'ün birimlerinin %96'sı
  Ümraniye'den geliyor. Şu anki kural yalnız Merkez ebeveynler için. Genişletilirse birkaç
  düzine taranmış poligon kapanır, ama küçük parçalar yanlış ilçede görünür.

### 5.2 Yeni kaynak gerektirenler

1. **Tarihsel köy → ilçe bağlılığı.** DİE/TÜİK genel nüfus sayımı "İdari Bölünüş" kitapları:
   1960 (0015128), 1965 (0015227), 1985 (0013062), 1990 (0013349) bulundu; 1970, 1975 ve 1980
   aranmadı. Kütüphane: `kutuphane.tuik.gov.tr/pdf/<no>.pdf`. Her sayımda her köyün hangi
   ilçeye bağlı olduğu yazıyor.
2. **Köy ve mahalle konumları.** Olası kaynaklar: OSM `place=village` noktaları ve muhtarlık
   sınırları (admin_level 8/10), GeoNames, HGM yer adları, TÜİK ADNKS köy/mahalle listesi
   (konumsuz).
3. **Yöntem önerisi.** Bir seçim tarihi için:
   - her bugünkü köyü, o tarihe en yakın sayımdaki ilçesine bağla;
   - köy poligonu yoksa köy noktalarından bugünkü ilçe sınırı içinde kırpılmış Voronoi
     hücreleri üret;
   - hücreleri eski ilçeye göre birleştir.

   Bu, `kanun_cok_kaynak` (40) ve `unresolved` (77) ilçelerin çoğunu çözer. Kentsel mahalleler
   için 1987 öncesi bağlılık kaynağı hâlâ yok.
4. **1953–1960 kanunlarının (6068, 6191, 6321, 6324, 6325) cetvelleri:** Resmî Gazete arşivi.
   7033 cetveli daha iyi bir taramadan okunabilirse 39 ilçe çözülür.

### 5.3 Kısıtlar (bu projenin kuralları)

- Tahmin yok. Kaynağı olmayan bir sınır ya da değer çizilmez, açıklamalı boş kalır.
- Kaynak değerleri değiştirilmez. Düzeltmeler ayrı adım olarak yapılır ve önceki değer
  saklanır.
- Ham DİE/TÜİK PDF'leri public depoya konmaz ("izinsiz çoğaltılamaz"). Public atlas
  (`turkiye-secim-atlasi`) yalnız türetilmiş JSON içerir.

---

## 6. Ek — Eksik seçim verileri

Tam liste: `eksik_secim_verisi.csv`. Sütunlar: seçim, tür, oylama, düzey (il/ilçe), plaka, il,
ad, geomId, neden. Aşağıda, bu listeyi dolduracak bir kaynak arayan kişi için gruplanmış hali
var.

### 6.1 Hiçbir kaynakta bulunamayanlar

| Seçim | Eksik | Aranan kaynaklar |
|---|---|---|
| 1950, 1954, 1957 genel | Bütün ilçe sonuçları (63/64/67 il yalnız il düzeyinde) | YSK il arşivi (yalnız il); TÜİK seçim dağıtım uygulaması 1961'den başlıyor |
| 1950, 1955 yerel | İlçe oy sayıları; yalnız kazanan parti biliniyor. Belediye başkanı meclisçe seçiliyordu | Türkçe Wikipedia il sayfaları; YSK'de yalnız ulusal toplam |
| 1963–1977 yerel | İl genel meclisi ve belediye meclisi (her düzeyde); başkanlık il merkezi + ilçe var | YSK'de yalnız ulusal toplam PDF |
| 1955 yerel | Kırşehir (il 1954–1957 arası kaldırılmıştı), 1 il tek parça; Bingöl Solhan satırı boş | — |
| Mahalle düzeyi | 2009 öncesinin tamamı; 2009+ 15 seçimde var | YSK açık veri sandık düzeyi 2009'dan başlıyor |
| Senato, ara ve yenileme seçimleri | Haritada gösterilmiyor (`data/normalized/ek/senato`, `ek/yenileme_ara` var) | — |

### 6.2 Kaynak var ama okunamayan ya da doğrulanamayan satırlar (yerel meclis 1984–2004)

Tek ilçe kaynağı DİE "Mahalli İdareler Seçimi Sonuçları" kitapları (taranmış). Yalnız
toplamları ve yüzdeleri tutan satırlar kullanılıyor. İl toplamları 1984, 1989, 1994 ve 1999'da
YSK kesin sonuçlarından tamamlandı.

| Kayıt | İl sonucu yok | İlçe satırı doğrulanamadı | İlçe satırı eşleşmedi |
|---|---|---|---|
| 1984 il genel meclisi | 11 | 83 | 202 |
| 1984 belediye meclisi | 41 | 245 | 64 |
| 1989 il genel meclisi | 1 | 1 | 3 |
| 1989 belediye meclisi | 1 | 6 | 4 |
| 1994 il genel meclisi | 1 | 17 | 274 |
| 1994 belediye meclisi | 3 | 95 | 184 |
| 1999 il genel meclisi | 1 | 58 | 56 |
| 1999 belediye meclisi | 3 | 152 | 40 |
| 2004 il genel meclisi | 0 | 17 | 53 |
| 2004 belediye meclisi | 2 | 2 | 45 |

- "Eşleşmedi": kitaptaki satırın hangi ilçe olduğu okunamadı ya da adı ve seçmen sayısı
  haritadaki ilçeyle birebir tutmadı. 1994 il genel meclisi tablosunun 2.989 satırından
  (il, ilçe, şehir ve köy satırları) yalnız 1.329'unun hangi birime ait olduğu çözülebildi.
- Çözüm yolu: sayfaların daha iyi taranmış bir kopyası, ya da ilçe seçim kurulu tutanakları
  (il seçim kurulları, yerel gazete arşivleri).
- YSK'de bu yıllar için ilçe düzeyinde meclis dosyası yok (denendi: `Mahalli/<yıl>/...`).
- 2014 ve sonrasında 30 büyükşehirde il genel meclisi yok. Bu bir eksik değil; 6360 sayılı
  Kanun gereği.

### 6.3 Başkanlık haritasında kaynağı sorunlu satırlar

- **1994–2004 yerel, 61 ilçe:** Gösterilen sonuç ilçe belediye başkanlığı değil, YSK'nin ilçe
  toplamı (merkez + beldeler ya da büyükşehir oyu). DİE kitabındaki ilçe belediyesi satırı
  doğrulanamadı. Satırda `ilceGeneliSonuc` var, ipucunda yazıyor. (1994: 5, 1999: 37, 2004: 19.)
- **2009 yerel:** Denizli ve Hatay Merkez belediye başkanlığı satırı boş.
- **Mükerrer ya da poligonsuz:** 1950 yerel'de Taşova hem Amasya hem Tokat altında; 1955 yerel'de
  Çatalağzı ve Filyos (Zonguldak); 2004 yerel'de Karadeniz Ereğli. Bunların poligonu yok.
- **1994/1999 yerel, Kaynaşlı:** Satır o dönemde var olmayan il 81 (Düzce) altında olduğu
  için haritada görünmüyor (§4.4).

### 6.4 Seçim başına eksik satır sayısı

`eksik_secim_verisi.csv`'den, neden grubuna göre:

| Seçim | Eksik |
|---|---|
| 1950 yerel | 1 ilçe sonuçsuz, 3 poligonsuz |
| 1955 yerel | 2 ilçe sonuçsuz, 3 poligonsuz |
| 1961–1983 genel, 1961/1982 referandum | Her birinde 1 poligonsuz (Ankara Merkez) |
| 1994 / 1999 / 2004 yerel başkanlık | 5 / 37 / 19 ilçe toplamı (ilçe belediyesi değil); 2004'te 1 poligonsuz |
| 2009 yerel (başkanlık / BM / İGM) | 25 / 25 / 26 ilçe satırı boş (2012 öncesi yer tutucular) |
| 2011 genel | 24 ilçe satırı boş (aynı neden) |
| 2014 CB, 2014 yerel, 2015 H/K | 3'er satır boş (Kemalpaşa, Derecik, Sultanhanı) |
| 2018 genel, 2018 CB | 1 satır boş (Derecik) |
| 2014/2019/2024 İGM | 30 il (büyükşehir, İGM yok) + 2–5 ilçe |

---

## 7. Sonraki adım için özet

- **Hemen yapılabilir (§5.1):** 2007 referandumu, 2009 yerel ve 2011 genel, Tillo,
  2013–2018 kanunları ve Kaynaşlı. Bunlar yalnız eldeki bilgiyle kapanır.
- **Kalan taranmış alanlar:** 1961–1988'de alanın ~%2'si. Tarihsel köy bağlılığı (sayım
  kitapları) ve köy konumlarıyla, köy düzeyi yeniden inşa (§5.2) gerektiriyor.
- **Eksik seçim verisi:** Çoğu kaynak yokluğundan (1950–1957 ilçe, 1963–1977 meclis) ya da
  tarama kalitesinden (1984/1994 meclis ilçe) geliyor.
