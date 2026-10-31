# Geometri denetimi — il, ilçe ve mahalle sınırları

Bu rapor `scripts/rapor/geometri_denetimi.py` ile üretildi; aynı veriyle her çalıştırmada aynı sonucu verir. Hiçbir geometri ya da veri dosyası değiştirilmedi. Bütün satırlar `docs/rapor/geometri_denetimi/` altındaki CSV'lerdedir.

Yeniden üretmek için (shapely ve pyproj gerekir, ~5 dakika):

```bash
python3 scripts/rapor/geometri_denetimi.py
```

## 1. Kısa özet

Haritada 973 bugünkü ilçe, 81 il, 919 tarihsel ilçe ve 990 ilçe kimliğine bağlı 51.301 mahalle poligonu var. Sonuç:

**Gerçek sorunlar (düzeltilmesi gerekenler)**

1. **Yanlış yere çizilen mahalleler.** 86 mahalle poligonu kendi ilçesinin 2 km'den daha dışında duruyor; 84'i en az bir seçimde çiziliyor. Örnekler: Tunceli Mazgirt'in Ayvatlı köyü Kayseri Pınarbaşı'nda, Balıkesir Bigadiç'in Camii mahallesi Eskişehir Çifteler'de, Çorum Sungurlu'nun Ekmekçi köyü Ankara Nallıhan'da çiziliyor. Bu mahallelerin oyu yanlış yerde boyanıyor ve ilçe haritası gereksiz yere uzaklaşıyor (bölüm 4.2).
2. **Üst üste çizilen TKGM birimleri.** Aynı seçimde birlikte çizilen ve anlamlı ölçüde (≥ 1 ha ve küçüğün ≥ %1'i) örtüşen 4.390 mahalle çifti var (3.484 km²). Bunların 2.653'i (2.740 km²) TKGM × TKGM. TKGM ham verisi kendi içinde örtüşüyor (21.366 çift, 52.638 km²) ve eşleştirme betiğinin %25 kuralı yalnız TKGM ile TKGM dışı sınırlar arasında uygulanıyor. Örtüşen iki poligondan biri ötekini örtüyor; alttaki mahallenin rengi görünmüyor, tıklanamıyor. 14 çiftte iki muhtarlık neredeyse aynı poligona düşmüş (bölüm 4.3).
3. **Haritaya bağlanmayan seçmen.** 2023 genel seçimde mahalle sonuçlarındaki seçmenin %94,61'i bir poligona bağlı; eksik kalan seçmen birkaç ilde toplanıyor (Hatay, Kahramanmaraş, Elazığ, Aksaray). Rakamlar belgelerdekinden biraz yüksek: sonraki eşleştirme düzeltmeleri kapsamı artırmış (bölüm 4.6).

**Küçük, görünümü az etkileyen sorunlar**

4. 1.002 mahalle, 24 ilçe, 8 il ve 8 tarihsel ilçe poligonu geometrik olarak geçersiz (çoğu kendi kendini kesen halka). Tarayıcı bunları çiziyor; alan ve kesişim hesaplarını bozuyor.
5. 42 mahalle poligonunda delik, dış halkayla aynı yönde yazılmış. Site SVG'yi varsayılan `nonzero` kuralıyla dolduruyor; bu deliklerin içi dolu çiziliyor. 1 kayıt poligon değil, çizgi (LineString); 2 kaydın alanı sıfır.
6. İlçe katmanı kaba sadeleştirilmiş (ilçe başına ortalama ~75 nokta). Komşu ilçeler arasında 6.062 dikiş boşluğu (367 km²) ve 2.052 örtüşme (399 km²) var. Toplam alanın %0,05'i; haritada kıl inceliğinde çizgiler olarak görünür.
7. 1.971 mahalle poligonu hiçbir seçimde çizilmiyor (1,9 MB ham GeoJSON).

**Sorun olmayanlar**

- Mahalle poligonlarının ilçe sınırından taşan alanı 55.651 km² (%7,2). Bunun çoğu ilçe katmanının kaba sadeleştirilmesinden geliyor: ilçe sınırına 2 km'lik pay verilince taşma 11.637 km²'ye (%1,5) iniyor.
- Eşleştirme betiğinin "mevcut poligonlarla %25'ten fazla örtüşen TKGM birimi çizilmez" kuralı tutuyor: 0 ihlal.
- Belediye × ttezer, Belediye × OSM gibi büyük örtüşmeler aynı seçimde birlikte çizilmiyor (eski kaynak başka seçimde kullanılıyor); haritada görünmüyor.
- Tarihsel ilçelerin 854'ü bugünkü parçalarının birleşimiyle birebir aynı. Depodaki iki geometri testi (`tests/validate_elections.py`: tarihsel ilçe örtüşme/delik ve seçim ilçe eşleme tabloları) shapely kurulunca çalıştı ve geçti.
- Dönem il sınırları (era*) geçerli; toplam alanları bugünkü ülkeyle %0,02 içinde aynı (iller arası küçük kenar örtüşmeleri var, bkz. 4.5).
- Verisi olup poligonu olmayan mahalle kaydı yok (site, sonucu olan her kaydın poligonunu buluyor).

## 2. Ne kontrol edildi, nasıl

Alanlar eşit alanlı Albers izdüşümünde (standart paraleller 37° ve 41° K, merkez 39° K / 35° D) hesaplandı. Geçersiz poligonlar hesap için `make_valid` ile onarıldı; dosyalar değişmedi.

Mahalle anahtarının ilk harfi kaynağı gösterir (`scripts/pipelines/mahalle_veri`):

| Önek | Kaynak | Poligon |
|---|---|---|
| `t…` | ttezer/turkiye-harita-verisi (25 ilde belediye/MAKS) | 16.808 |
| `r…` | OpenStreetMap | 5.897 |
| `b…` | Belediye açık verisi (Bursa, Sakarya) | 1.659 |
| `k…`, `kb…` | TKGM kadastro mahallesi (`kb`: bölümlü birimlerin birleşimi, 95) | 26.937 |

**Sadeleştirme bandı.** İlçe katmanı ham veriden %8 noktayla sadeleştirildi (`geo/normalized/PROVENANCE.md`); sınırı gerçek sınırdan 1–2 km sapabiliyor. Ayrıntılı mahalle poligonları bu yüzden kenarda ilçe dışına taşıyor. Gerçek hatayı gürültüden ayırmak için ilçe sınırına 2 km pay verilmiş hâli de ölçüldü ("2 km bandı dışında").

**Birlikte çizilme.** Site bir seçimde yalnız o seçimin verisi olan mahalle poligonlarını çizer. İki poligon hiçbir seçimde birlikte çizilmiyorsa örtüşmeleri haritada görünmez; bu yüzden her örtüşme için ortak seçim sayısı hesaplandı.

| # | Kontrol | CSV |
|---|---|---|
| 1 | Geçersiz, boş, kıymık, kırıntı parça, birebir aynı geometri, halka yönü | `gecersiz_geometri.csv`, `kiymik_kucuk.csv`, `yinelenen_geometri.csv` |
| 2 | Mahallenin ilçe dışında kalan payı (> %5 ve > 1 km²), yanlış ilçe (temsil noktası) | `mahalle_ilce_disi.csv`, `mahalle_yanlis_ilce.csv` |
| 3 | Aynı ilçede mahalle–mahalle örtüşmesi, kaynak çifti, birlikte çizilme; TKGM %25 kuralı | `mahalle_ortusme.csv`, `tkgm_yuzde25_kurali.csv` |
| 4 | İlçe alanının mahallelerce kaplanmayan payı; TKGM birimi olan/olmayan boşluk; poligonsuz seçmen | `ilce_bosluk.csv` |
| 5 | İlçe örtüşmesi ve dikiş boşlukları, il ↔ ilçeler, dönem il sınırları, tarihsel ilçeler | `ilce_ortusme.csv`, `ilce_katmani_delikler.csv`, `il_ilce_tutarlilik.csv`, `donem_il_sinirlari.csv`, `tarihsel_ilce_birlesim.csv` |
| 6 | Seçim başına poligonu olan seçmen (ülke, il) | `kapsam_secmen_ozet.csv`, `kapsam_secmen_il.csv` |
| 7 | İlçe sınırı ↔ TKGM ham birimlerinin ilçe birleşimi (bağımsız kaynak) | `tkgm_ilce_karsilastirma.csv` |

## 3. Envanter

| Katman | Kayıt | Geçersiz | Diğer bulgular |
|---|---|---|---|
| il | 81 | 8 | kırıntı parçalı: 4 |
| ilçe | 973 | 24 | kırıntı parçalı: 12 |
| tarihsel ilçe | 919 | 8 | kırıntı parçalı: 8 |
| mahalle | 51.301 | 1.002 | boş ya da dejenere (alan < 1 m²): 2; delik dış halkayla aynı yönde (SVG'de dolu çizilir): 42; kırıntı parçalı: 368; poligon değil (LineString): 1; çok küçük (< 500 m²): 6 |
| il era1950 | 63 | 0 | kırıntı parçalı: 3 |
| il era1954 | 64 | 0 | kırıntı parçalı: 3 |
| il era1955 | 66 | 0 | kırıntı parçalı: 3 |
| il era1957_1965 | 67 | 0 | kırıntı parçalı: 3 |
| il era1957_1987 | 67 | 0 | kırıntı parçalı: 3 |
| il era1991 | 74 | 0 | kırıntı parçalı: 3 |
| il era1994 | 76 | 0 | kırıntı parçalı: 3 |
| il era1995 | 79 | 0 | kırıntı parçalı: 3 |
| il era1999 | 80 | 0 | kırıntı parçalı: 3 |

Hiçbir seçimde çizilmeyen mahalle poligonu: 1.971 (OSM 23, TKGM 354, ttezer 1.594).

## 4. Bulgular

### 4.1 Geçerlilik

| Mahalle poligonunda sorun | Sayı |
|---|---|
| geçersiz: Self-intersection | 605 |
| geçersiz: Ring Self-intersection | 289 |
| geçersiz: Too few points in geometry component | 108 |
| delik dış halkayla aynı yönde (SVG'de dolu çizilir) | 42 |
| boş ya da dejenere (alan < 1 m²) | 2 |
| poligon değil (LineString) | 1 |

Kendi kendini kesen halkalar büyük olasılıkla kaynakların sadeleştirilmesinden ve 4 ondalığa yuvarlanmasından (TKGM: 10 m Douglas-Peucker) çıkan küçük düğümlerdir; tarayıcı bunları çizer. "Too few points" bir parçanın 4'ten az noktaya düşmesidir; o parça çizilmez.

**Deliği dolu çizilen poligonlar** (42; ilk 20, alana göre). Site `fill-rule` belirtmiyor (SVG varsayılanı `nonzero`); delik dış halkayla aynı yönde yazılınca içi mahallenin rengiyle boyanır. Delikteki komşu mahalle sonra çizilirse görünür, önce çizilirse altta kalır.

| İlçe | Anahtar | Mahalle | Alan km² |
|---|---|---|---|
| TR-D-58-002 | `kb11674-158846-157472-11241-12098-156885` | DELİİLYAS-MERKEZ MAH. | 189,6 |
| TR-D-03-017 | `kb146812-145033-147013` | ÜÇKUYU KÖYÜ | 150,5 |
| TR-D-12-006 | `kb204337-204336-204335` | ARAKONAK-MERKEZ MAH. | 71,3 |
| TR-D-58-013 | `k204960` | ÇATALOLUK KÖYÜ | 66,9 |
| TR-D-60-005 | `kb156242-158958-159085-158767` | ÖZALAN KÖYÜ | 66,7 |
| HIST-Kahramanmaraş-Merkez | `k131904` | BUDAKLI KÖYÜ | 43,1 |
| TR-D-46-004 | `k131904` | BUDAKLI MAH. | 43,1 |
| TR-D-19-004 | `k124261` | BÜĞET KÖYÜ | 37,7 |
| TR-D-51-005 | `k127493` | HİMMETLİ KÖYÜ | 37,3 |
| TR-D-09-008 | `k204553` | ATAEYMİR-CUMHURİYET MAH. | 36,3 |
| TR-D-21-001 | `k125661` | KOLLUDERE MAH. | 35,0 |
| TR-D-01-008 | `k45428` | AYDIN MAH. | 33,6 |
| TR-D-21-010 | `k34626` | İNCEKAVAK MAH. | 31,4 |
| TR-D-42-005 | `k180642` | HUĞLU-CUMHURİYET MAH. | 31,0 |
| TR-D-21-003 | `k35537` | GÜRÜZ MAH. | 30,0 |
| TR-D-45-012 | `k154187` | HATIPLAR MAH. | 29,6 |
| TR-D-45-004 | `kb151313-149118` | DURHASAN MAH. | 27,4 |
| TR-D-57-006 | `k157312` | YENİKENT KÖYÜ | 26,4 |
| TR-D-42-005 | `k180641` | HUĞLU-İSTİKLAL MAH. | 26,3 |
| TR-D-21-016 | `k125608` | YİĞİTÇAVUŞ  MAH. | 24,3 |

**Boş ya da poligon olmayan kayıtlar:**

| İlçe | Anahtar | Mahalle | Sorun |
|---|---|---|---|
| TR-D-05-001 | `k126999` | AYDINLIK KÖYÜ | poligon değil (LineString) |
| TR-D-46-007 | `k168529` | ALIÇLIBUCAK MAH. | boş ya da dejenere (alan < 1 m²) |
| TR-D-68-001 | `k53033` | ÇATALÇEŞME KÖYÜ | boş ya da dejenere (alan < 1 m²) |

**Birebir aynı geometri.** Mahallede 1652 grup tarihsel ilçeye (HIST-) kopyalanmış halef poligonu; beklenen. Kalan gruplarda iki ayrı muhtarlık aynı poligonu paylaşıyor (TKGM'de aynı sınırla iki birim):

| İlçe | Poligonlar | Tür |
|---|---|---|
| TR-D-13-006 | AÇIKALAN KÖYÜ (`k158327`) = AYDEMİR KÖYÜ (`k158599`) | aynı ilçe içinde |
| TR-D-36-003 | YAYLACIK KÖYÜ (`k26175`) = YAĞLICA KÖYÜ (`k26982`) | aynı ilçe içinde |
| TR-D-37-014 | İBRAHİMLİ KÖYÜ (`k130437`) = HÜSEYİNLİ KÖYÜ (`k130475`) | aynı ilçe içinde |
| TR-D-39-005 | AHMETBEY-KARŞIYAKA MAH. (`k207594`) = AHMETBEY-GÜNDOĞU MAH. (`k207596`) | aynı ilçe içinde |
| TR-D-46-002 | BULGURKAYA MAH. (`k168403`) = GÖKGEDİK MAH. (`k19337`) | aynı ilçe içinde |
| TR-D-46-002 | OSMANCIK MAH. (`k180864`) = HACIVELİUŞAĞI MAH. (`k180868`) | aynı ilçe içinde |
| TR-D-50-004 / TR-D-50-007 | CUMHURİYET MAH. (`k139181`) = CUMHURİYET MAH. (`k127778`) | farklı ilçelerde |
| TR-D-56-005 | SAĞIRSU KÖYÜ (`k126481`) = ÇAĞBAŞI KÖYÜ (`k205942`) | aynı ilçe içinde |
| TR-D-58-008 | KABALI KÖYÜ (`k12244`) = KARLI KÖYÜ (`k12380`) | aynı ilçe içinde |
| TR-D-65-007 | ORTA MAH. (`k160747`) = KAZANÇ MAH. (`k54619`) | aynı ilçe içinde |
| TR-D-66-006 | YUNUS EMRE MAH. (`k204445`) = SEYİT AHMET MAH. (`k204447`) | aynı ilçe içinde |
| TR-D-80-005 | RAHİME HATUN MAH. (`k207090`) = KAZIM KARABEKİR MAH. (`k207093`) | aynı ilçe içinde |

Kıymık ve çok küçük poligonlar önemsiz: 0 kıymık, 6 çok küçük, 368 poligonda 1.000 m²'den küçük kırıntı parça (`kiymik_kucuk.csv`).

Dış halka yönü kaynaktan kaynağa değişiyor (mahallede saat yönü: 20.154, saat yönü tersi: 31.836). Site kendi düzlem izdüşümünü kullandığı için dış halka yönü sorun değil; yalnız delik yönü önemli.

### 4.2 Mahalle ile ilçesi

| Ölçü | Değer |
|---|---|
| İlçe dışına taşan toplam mahalle alanı | 55.651 km² (%7,23) |
| … 2 km sadeleştirme bandı dışında kalan | 11.637 km² (%1,51) |
| > %5 ve > 1 km² taşan mahalle | 7.498 (çizilen 7.267); Belediye 197, OSM 557, TKGM 4.462, ttezer 2.282 |
| … 2 km bandı dışında da > %5 ve > 1 km² | 1.148 (çizilen 1.127); Belediye 15, OSM 76, TKGM 716, ttezer 341 |
| Temsil noktası kendi ilçesinde olmayan | 770 (çizilen 751; denizde 13) |
| … kendi ilçesinden 2 km'den uzak | 86 (çizilen 84); Belediye 3, OSM 8, TKGM 54, ttezer 21 |

Taşmaların çoğu sınır gürültüsü. Kalan büyük taşmalarda mahalle poligonu ile TKGM çoğu kez aynı yerde, sitenin ilçe sınırı farklı (Kadınhanı'nda ttezer "Başkuyu" ile TKGM "Başkuyu-Fatih" aynı 406 km²'yi kaplıyor ve ikisi de ilçe sınırının %47 dışında). Bu durumlarda hatalı olan büyük olasılıkla ilçe katmanıdır (bkz. 4.7).

**Kendi ilçesinden 2 km'den uzakta duran mahalleler** (ilk 20, uzaklığa göre; tamamı `mahalle_yanlis_ilce.csv`):

| İlçe (geomId) | Anahtar | Mahalle | Kaynak | Bulunduğu ilçe | Uzaklık km | Alan km² | Çizildiği seçim |
|---|---|---|---|---|---|---|---|
| Merkez (TR-D-79-002) | `k132270` | YENİ MAH. | TKGM | Bozüyük (TR-D-11-002) | 676,7 | 7,15 | 0 |
| Mazgirt (TR-D-62-003) | `k207830` | AYVATLI KÖYÜ | TKGM | Pınarbaşı (TR-D-38-010) | 236,1 | 4,80 | 8 |
| Bigadiç (TR-D-10-005) | `k167080` | CAMİİ MAH. | TKGM | Çifteler (TR-D-26-003) | 200,7 | 0,04 | 15 |
| Sungurlu (TR-D-19-013) | `k159825` | EKMEKÇİ KÖYÜ | TKGM | Nallıhan (TR-D-06-020) | 197,4 | 23,33 | 11 |
| Gülağaç (TR-D-68-004) | `k53241` | SOFULAR KÖYÜ | TKGM | Ağaçören (TR-D-68-001) | 47,3 | 11,69 | 9 |
| Zara (TR-D-58-017) | `k154382` | YEŞİLDERE KÖYÜ | TKGM | İliç (TR-D-24-003) | 28,5 | 0,04 | 11 |
| Keles (TR-D-16-008) | `b16-183657` | AKÇAPINAR MAH. | Belediye | Harmancık (TR-D-16-004) | 16,4 | 8,08 | 14 |
| Şahinbey (TR-D-27-007) | `tTR-Y-27-007-M-0082` | KALE MAH. | ttezer | İslahiye (TR-D-27-002) | 15,8 | 18,09 | 15 |
| Odunpazarı (TR-D-26-010) | `k205815` | 71 EVLER MAH. | TKGM | Tepebaşı (TR-D-26-014) | 12,9 | 0,09 | 15 |
| Eruh (TR-D-56-002) | `k168204` | OKÇULAR KÖYÜ | TKGM | Pervari (TR-D-56-004) | 8,8 | 95,35 | 8 |
| Harmancık (TR-D-16-004) | `b16-184097` | AKPINAR MAH. | Belediye | Keles (TR-D-16-008) | 7,7 | 7,79 | 14 |
| Merkez (TR-D-50-007) | `k127778` | CUMHURİYET MAH. | TKGM | Gülşehir (TR-D-50-004) | 7,6 | 4,96 | 3 |
| Oğuzeli (TR-D-27-006) | `k207194` | MİMAR SİNAN MAH. | TKGM | Şahinbey (TR-D-27-007) | 7,3 | 6,38 | 15 |
| Hasankeyf (TR-D-72-004) | `k126466` | KAYIKLI KÖYÜ | TKGM | Merkez (TR-D-56-005) | 6,5 | 10,28 | 5 |
| Bozyazı (TR-D-33-004) | `k27833` | ARDIÇLITAŞ MAH. | TKGM | Anamur (TR-D-33-002) | 6,3 | 69,54 | 14 |
| Seben (TR-D-14-008) | `tTR-Y-14-008-K-0012` | HACCAĞIZ KÖYÜ | ttezer | Kıbrıscık (TR-D-14-005) | 6,0 | 35,93 | 11 |
| Alanya (TR-D-07-003) | `tTR-Y-07-003-M-0099` | YAYLALI MAH. | ttezer | Sarıveliler (TR-D-70-006) | 5,9 | 37,29 | 14 |
| Alanya (TR-D-07-003) | `tTR-Y-07-003-M-0047` | İMAMLI MAH. | ttezer | Sarıveliler (TR-D-70-006) | 5,6 | 26,34 | 14 |
| Alanya (TR-D-07-003) | `tTR-Y-07-003-M-0009` | BASIRLI MAH. | ttezer | Gündoğmuş (TR-D-07-009) | 5,6 | 13,71 | 14 |
| Espiye (TR-D-28-007) | `k163606` | ERİCEK KÖYÜ | TKGM | Güce (TR-D-28-011) | 5,2 | 128,37 | 11 |

**İlçesinin 2 km bandı dışına en çok taşan çizilen mahalleler** (ilk 20; tamamı `mahalle_ilce_disi.csv`):

| İlçe (geomId) | Anahtar | Mahalle | Kaynak | Alan km² | İlçe dışı km² (%) | 2 km bandı dışı km² (%) | Seçim |
|---|---|---|---|---|---|---|---|
| Kadınhanı (TR-D-42-020) | `tTR-Y-42-020-M-0005` | BAŞKUYU MAH. | ttezer | 406,7 | 190,9 (%46,9) | 158,8 (%39,1) | 12 |
| Kadınhanı (TR-D-42-020) | `k146997` | BAŞKUYU-FATİH MAH. | TKGM | 406,3 | 190,7 (%46,9) | 158,7 (%39,0) | 3 |
| Toroslar (TR-D-33-012) | `k127415` | ARSLANKÖY MAH. | TKGM | 415,9 | 172,3 (%41,4) | 110,7 (%26,6) | 15 |
| Kulp (TR-D-21-013) | `k35350` | ALACA MAH. | TKGM | 198,8 | 147,7 (%74,3) | 105,3 (%53,0) | 14 |
| Eruh (TR-D-56-002) | `k168204` | OKÇULAR KÖYÜ | TKGM | 95,3 | 95,3 (%100,0) | 95,3 (%100,0) | 8 |
| Beypazarı (TR-D-06-005) | `tTR-Y-06-005-M-0040` | KARAŞAR MAH. | ttezer | 176,8 | 111,5 (%63,1) | 85,3 (%48,2) | 12 |
| Espiye (TR-D-28-007) | `k163606` | ERİCEK KÖYÜ | TKGM | 128,4 | 99,1 (%77,2) | 81,9 (%63,8) | 11 |
| Akseki (TR-D-07-001) | `tTR-Y-07-001-M-0028` | GÜMÜŞDAMLA MAH. | ttezer | 109,8 | 100,4 (%91,5) | 80,5 (%73,3) | 14 |
| Yahyalı (TR-D-38-015) | `tTR-Y-38-015-M-0039` | YENİCE MAH. | ttezer | 282,4 | 105,4 (%37,3) | 80,1 (%28,4) | 15 |
| Çağlayancerit (TR-D-46-003) | `k168437` | ENGİZEK MAH. | TKGM | 131,9 | 88,5 (%67,1) | 72,0 (%54,6) | 15 |
| Espiye (TR-D-28-007) | `k161987` | SEYDİKÖY | TKGM | 75,1 | 71,2 (%94,9) | 65,0 (%86,5) | 11 |
| Çukurca (TR-D-30-001) | `k29588` | CEVİZLİ KÖYÜ | TKGM | 122,2 | 72,3 (%59,1) | 64,5 (%52,8) | 7 |
| Elmalı (TR-D-07-006) | `tTR-Y-07-006-M-0059` | YUVA MAH. | ttezer | 111,9 | 88,7 (%79,2) | 64,4 (%57,5) | 12 |
| Gemerek (TR-D-58-005) | `k158997` | ÇATKÖY | TKGM | 121,2 | 88,0 (%72,7) | 62,6 (%51,7) | 11 |
| Ardeşen (TR-D-53-001) | `r17217784` | KAÇKAR KÖYÜ | OSM | 123,6 | 97,3 (%78,8) | 57,0 (%46,1) | 9 |
| Beyşehir (TR-D-42-005) | `tTR-Y-42-005-M-0036` | GÖLYAKA MAH. | ttezer | 175,1 | 81,6 (%46,6) | 56,9 (%32,5) | 12 |
| Derebucak (TR-D-42-011) | `kb147036-146020` | PINARBAŞI-MERKEZ MAH. | TKGM | 132,2 | 72,3 (%54,7) | 56,8 (%42,9) | 3 |
| Derebucak (TR-D-42-011) | `tTR-Y-42-011-M-0007` | PINARBAŞI MAH. | ttezer | 131,6 | 72,2 (%54,9) | 56,7 (%43,1) | 12 |
| Doğanşar (TR-D-58-004) | `k12540` | ÇATPINAR KÖYÜ | TKGM | 114,9 | 79,8 (%69,4) | 56,6 (%49,3) | 11 |
| Silifke (TR-D-33-010) | `r19990190` | SARIAYDIN MAH. | OSM | 160,7 | 101,4 (%63,1) | 54,3 (%33,8) | 14 |

### 4.3 Mahalle–mahalle örtüşmesi

Aynı ilçe içinde 1.000 m²'den büyük 44.829 örtüşen çift var. "Anlamlı": ≥ 1 ha ve küçük poligonun ≥ %1'i. "Birlikte çizilen": iki poligon en az bir seçimde aynı haritada.

| Kaynak çifti | Çift | Alan km² | Anlamlı | Anlamlı km² | Birlikte çizilen | Birlikte km² |
|---|---|---|---|---|---|---|
| TKGM × TKGM | 26.843 | 6.086,2 | 2.846 | 5.720,2 | 2.653 | 2.739,5 |
| OSM × TKGM | 3.327 | 4.852,7 | 1.602 | 4.796,4 | 974 | 467,8 |
| TKGM × ttezer | 3.553 | 11.038,9 | 1.184 | 10.967,4 | 411 | 229,2 |
| OSM × ttezer | 1.582 | 2.443,1 | 328 | 2.413,9 | 196 | 31,9 |
| OSM × OSM | 384 | 11,9 | 104 | 7,1 | 104 | 7,1 |
| Belediye × TKGM | 180 | 413,5 | 90 | 412,1 | 10 | 5,3 |
| ttezer × ttezer | 805 | 17,7 | 40 | 2,7 | 40 | 2,7 |
| Belediye × ttezer | 7.439 | 13.614,0 | 4.074 | 13.542,1 | 2 | 0,6 |
| Belediye × Belediye | 628 | 1,4 | 0 | 0,0 | 0 | 0,0 |
| Belediye × OSM | 88 | 72,6 | 26 | 72,2 | 0 | 0,0 |

- **TKGM %25 kuralı tutuyor:** her seçimde, çizilen her TKGM birimi için o seçimde çizilen TKGM dışı poligonlarla örtüşme hesaplandı; %25'i aşan 0 kayıt var (`tkgm_yuzde25_kurali.csv`). OSM × TKGM ve TKGM × ttezer birlikte çizilen örtüşmeleri bu yüzden %25'in altında kalan kenar örtüşmeleridir.
- **TKGM × TKGM için kural yok.** TKGM'nin kendi birimleri iç içe ya da üst üste olabiliyor (ham veride aynı ilçe içinde 21.366 anlamlı çift, 52.638 km²): belde mahallesi ile onu içeren köy birimi, aynı sınırla iki ayrı köy gibi. Eşleştirme iki muhtarlığı bu iki birime ayrı ayrı bağlayınca ikisi de çiziliyor.
- Neredeyse aynı (IoU ≥ 0,95) 911 çift var; 14'ü birlikte çiziliyor.

**Birlikte çizilen en büyük örtüşmeler** (ilk 20; tamamı `mahalle_ortusme.csv`):

| İlçe (geomId) | Mahalle 1 | Mahalle 2 | Kaynak | Örtüşme km² | Küçüğün % | Ortak seçim |
|---|---|---|---|---|---|---|
| Palu (TR-D-23-010) | KIRKBULAK KÖYÜ (`k156110`) | KÖKLÜCE KÖYÜ (`k160272`) | TKGM × TKGM | 70,16 | 100,0 | 11 |
| Şarkikaraağaç (TR-D-32-010) | ÇARIKSARAYLAR-ULU MAH. (`k140112`) | ÇARIKSARAYLAR-CUMHURİYET MAH. (`k206735`) | TKGM × TKGM | 57,55 | 98,9 | 15 |
| Hafik (TR-D-58-008) | KABALI KÖYÜ (`k12244`) | KARLI KÖYÜ (`k12380`) | TKGM × TKGM | 52,64 | 100,0 | 11 |
| Yakutiye (TR-D-25-020) | AKDAĞ MAH. (`k124826`) | UMUDUM MAH. (`k124866`) | TKGM × TKGM | 44,65 | 73,9 | 14 |
| Andırın (TR-D-46-002) | BULGURKAYA MAH. (`k168403`) | GÖKGEDİK MAH. (`k19337`) | TKGM × TKGM | 43,79 | 100,0 | 14 |
| Emirdağ (TR-D-03-009) | AŞAĞIPİRİBEYLİ-KARŞIYAKA MAH. (`k143018`) | AŞAĞIPİRİBEYLİ-YENİ MAH. (`k148449`) | TKGM × TKGM | 39,15 | 98,4 | 3 |
| Karakoyunlu (TR-D-76-003) | KERİMBEYLİ KÖYÜ (`k142646`) | CENNETABAT KÖYÜ (`k50695`) | TKGM × TKGM | 30,29 | 100,0 | 9 |
| Yakutiye (TR-D-25-020) | ARIBAHÇE MAH. (`k124828`) | UMUDUM MAH. (`k124866`) | TKGM × TKGM | 29,01 | 49,8 | 15 |
| Yakutiye (TR-D-25-020) | AKTOPRAK MAH. (`k124827`) | UMUDUM MAH. (`k124866`) | TKGM × TKGM | 27,93 | 98,2 | 15 |
| Altınyayla (TR-D-58-002) | DELİİLYAS-MERKEZ MAH. (`kb11674-158846-157472-11241-12098-156885`) | SERİNYAYLA KÖYÜ (`r19571736`) | OSM × TKGM | 27,39 | 99,5 | 8 |
| Niksar (TR-D-60-005) | ÖZVEREN KÖYÜ (`k158767`) | ÖZALAN KÖYÜ (`kb156242-158958-159085-158767`) | TKGM × TKGM | 26,11 | 99,9 | 9 |
| Toroslar (TR-D-33-012) | TIRTAR MAH. (`k127095`) | ARSLANKÖY MAH. (`k127415`) | TKGM × TKGM | 25,94 | 33,9 | 14 |
| İhsaniye (TR-D-03-012) | FATİH MAH. (`k143301`) | AYAZİNİ KÖYÜ (`kb148304-143301`) | TKGM × TKGM | 25,54 | 100,0 | 3 |
| Merkez (TR-D-56-005) | SAĞIRSU KÖYÜ (`k126481`) | ÇAĞBAŞI KÖYÜ (`k205942`) | TKGM × TKGM | 25,16 | 100,0 | 6 |
| Çay (TR-D-03-005) | AKTAŞ MAH. (`k143714`) | ALİ KALELİ MAH. (`k206755`) | TKGM × TKGM | 25,08 | 100,0 | 15 |
| Savur (TR-D-47-009) | YEŞİLALAN-ŞAFAK MAH. (`k203644`) | YEŞİLALAN-YENİ MAH. (`k203646`) | TKGM × TKGM | 24,90 | 100,0 | 3 |
| Bayat (TR-D-19-002) | YONCALI KÖYÜ (`k159414`) | LAPA KÖYÜ (`k207824`) | TKGM × TKGM | 24,67 | 100,0 | 3 |
| Emirdağ (TR-D-03-009) | DAVULGA-DOMURLU MAH. (`k144834`) | DAVULGA-SOFULU MAH. (`k147174`) | TKGM × TKGM | 23,73 | 100,0 | 15 |
| Merkez (TR-D-24-002) | DEREYURT MAH. (`k204985`) | YALNIZBAĞ MAH. (`kb204985-204986-204987-204988`) | TKGM × TKGM | 23,71 | 100,0 | 5 |
| Beyşehir (TR-D-42-005) | HUĞLU-İSTİKLAL MAH. (`k180641`) | HUĞLU-CUMHURİYET MAH. (`k180642`) | TKGM × TKGM | 23,44 | 89,3 | 3 |

### 4.4 Boşluklar: ilçenin mahallelerce kaplanmayan alanı

"TKGM birimli boşluk": boş kalan alanda TKGM ham verisinde bir birim var (eşleşmeyen ya da çakışma yüzünden çizilmeyen muhtarlık, ya da muhtarlığı olmayan birim). "Birimsiz boşluk": TKGM'de de birim yok (orman, göl, hazine/askerî alan ya da TKGM'nin sınırını vermediği 2.768 birim). Boşluk seçmen kaybı demek değildir; kayıp "poligonsuz seçmen" sütunundadır.

| Seçim | İlçe | Kaplı alan | Boşluk km² | TKGM birimli km² | Hiç poligonu olmayan ilçe | Dağılım (ilçe sayısı) |
|---|---|---|---|---|---|---|
| bütün poligonlar | 990 | %83,8 | 131.681 | 30.382 | 0 | <%25: 5, %25–50: 22, %50–75: 148, %75–90: 414, %90–99: 398, ≥%99: 3 |
| 2023 | 973 | %83,1 | 131.875 | 35.094 | 0 | <%25: 7, %25–50: 25, %50–75: 155, %75–90: 413, %90–99: 370, ≥%99: 3 |
| 2024yerel | 973 | %48,2 | 404.532 | 304.358 | 20 | %0: 21, <%25: 391, %25–50: 46, %50–75: 54, %75–90: 204, %90–99: 254, ≥%99: 3 |

Yerel seçimlerde kaplı alan düşük: büyükşehir olmayan illerde köyler belediye başkanlığı seçimine katılmadığı için o seçimin mahalle verisinde köy yok. Bu beklenen bir boşluk.

**2023: en çok poligonsuz seçmeni olan ilçeler** (ilk 20). Bunlar gerçek kayıp: muhtarlık sonucu var, sınırı yok.

| İlçe (geomId) | İl | Kaplı | Boşluk km² | TKGM birimli km² | İlçe seçmeni | Poligonsuz seçmen |
|---|---|---|---|---|---|---|
| İskenderun (TR-D-31-009) | Hatay | %72,4 | 70,9 | 8,4 | 164.655 | 84.473 (%51,3) |
| Merkez (TR-D-23-005) | Elazığ | %75,1 | 557,9 | 355,2 | 324.783 | 76.560 (%23,6) |
| Karatay (TR-D-42-022) | Konya | %92,6 | 209,5 | 24,4 | 249.629 | 67.582 (%27,1) |
| Dülkadiroğlu (TR-D-46-004) | Kahramanmaraş | %66,3 | 396,6 | 130,0 | 142.663 | 62.946 (%44,1) |
| Merkez (TR-D-43-009) | Kütahya | %92,0 | 197,7 | 53,9 | 193.025 | 59.059 (%30,6) |
| Kırıkhan (TR-D-31-010) | Hatay | %69,1 | 220,8 | 70,2 | 72.698 | 55.219 (%76,0) |
| Merkez (TR-D-68-002) | Aksaray | %62,5 | 1.326,9 | 415,6 | 214.944 | 53.878 (%25,1) |
| Reyhanlı (TR-D-31-013) | Hatay | %33,6 | 242,5 | 225,1 | 64.674 | 48.312 (%74,7) |
| Merkez (TR-D-60-009) | Tokat | %84,6 | 308,6 | 174,1 | 146.087 | 45.859 (%31,4) |
| Kozan (TR-D-01-008) | Adana | %85,6 | 274,4 | 33,3 | 97.522 | 45.813 (%47,0) |
| Doğubayazıt (TR-D-04-003) | Ağrı | %75,5 | 551,3 | 0,0 | 70.487 | 44.675 (%63,4) |
| Canik (TR-D-55-007) | Samsun | %93,7 | 16,9 | 0,7 | 73.136 | 41.618 (%56,9) |
| Merkez (TR-D-51-005) | Niğde | %55,1 | 998,7 | 830,5 | 161.579 | 40.677 (%25,2) |
| Turgutlu (TR-D-45-016) | Manisa | %65,0 | 192,2 | 109,3 | 129.403 | 40.415 (%31,2) |
| Erciş (TR-D-65-006) | Van | %52,0 | 1.024,3 | 25,5 | 104.103 | 39.772 (%38,2) |
| Soma (TR-D-45-014) | Manisa | %77,0 | 188,8 | 3,3 | 83.443 | 38.153 (%45,7) |
| Merkez (TR-D-76-002) | Iğdır | %40,7 | 754,6 | 96,5 | 95.186 | 37.099 (%39,0) |
| Merkez (TR-D-66-014) | Yozgat | %90,9 | 184,4 | 71,4 | 72.596 | 35.416 (%48,8) |
| Akdeniz (TR-D-33-001) | Mersin | %80,5 | 52,0 | 26,3 | 176.855 | 33.533 (%19,0) |
| Mezitli (TR-D-33-008) | Mersin | %89,6 | 38,7 | 11,8 | 157.884 | 32.682 (%20,7) |

**2023: en düşük kaplı ilçeler** (ilk 20). Seçmen kaybı küçükse boşluk görünüşle ilgilidir (Ceylanpınar'daki TİGEM arazisi, Tunceli'de muhtarlığı olmayan birimler gibi).

| İlçe (geomId) | İl | Kaplı | Boşluk km² | TKGM birimli km² | Birimsiz km² | Poligonsuz seçmen |
|---|---|---|---|---|---|---|
| Yenişarbademli (TR-D-32-013) | Isparta | %0,9 | 235,3 | 0,0 | 235,3 | 1.689 (%86,7) |
| Sultanhanı (TR-D-68-008) | Aksaray | %3,1 | 448,9 | 363,3 | 85,7 | 7.586 (%93,8) |
| Gölmarmara (TR-D-45-005) | Manisa | %14,1 | 266,7 | 0,0 | 266,7 | 10.410 (%89,1) |
| Ceylanpınar (TR-D-63-004) | Şanlıurfa | %16,3 | 1.329,9 | 1.324,8 | 5,1 | 5.832 (%11,3) |
| Pülümür (TR-D-62-007) | Tunceli | %17,1 | 1.191,5 | 972,8 | 218,7 | 1.159 (%37,6) |
| Yalıhüyük (TR-D-42-030) | Konya | %20,2 | 74,8 | 29,7 | 45,1 | 740 (%49,1) |
| Nurhak (TR-D-46-008) | Kahramanmaraş | %22,1 | 800,1 | 239,3 | 560,8 | 4.683 (%54,6) |
| Eskil (TR-D-68-003) | Aksaray | %27,0 | 1.242,8 | 144,3 | 1.098,5 | 11.259 (%59,1) |
| Hozat (TR-D-62-002) | Tunceli | %27,9 | 478,6 | 442,7 | 35,9 | 0 (%0,0) |
| Merkez (TR-D-73-006) | Şırnak | %30,1 | 1.189,7 | 206,7 | 983,0 | 14.636 (%24,1) |
| Gevaş (TR-D-65-007) | Van | %30,3 | 1.130,5 | 0,6 | 1.129,9 | 4.852 (%26,7) |
| Kiğı (TR-D-12-005) | Bingöl | %33,4 | 313,7 | 280,5 | 33,2 | 0 (%0,0) |
| Reyhanlı (TR-D-31-013) | Hatay | %33,6 | 242,5 | 225,1 | 17,4 | 48.312 (%74,7) |
| Çukurca (TR-D-30-001) | Hakkari | %37,8 | 453,8 | 218,5 | 235,3 | 0 (%0,0) |
| Kızılören (TR-D-03-014) | Afyonkarahisar | %38,6 | 68,3 | 0,0 | 68,3 | 1.194 (%64,6) |
| Tatvan (TR-D-13-007) | Bitlis | %40,2 | 1.127,2 | 141,2 | 986,0 | 1.214 (%1,9) |
| Adilcevaz (TR-D-13-001) | Bitlis | %40,4 | 945,5 | 93,9 | 851,6 | 1.910 (%10,4) |
| Mazgirt (TR-D-62-003) | Tunceli | %40,5 | 418,3 | 345,6 | 72,8 | 1.825 (%28,7) |
| Merkez (TR-D-76-002) | Iğdır | %40,7 | 754,6 | 96,5 | 658,1 | 37.099 (%39,0) |
| Beytüşşebap (TR-D-73-001) | Şırnak | %41,6 | 961,4 | 0,0 | 961,4 | 1.674 (%14,8) |

### 4.5 İlçe, il ve tarihsel katmanlar

| Ölçü | Değer |
|---|---|
| İlçe–ilçe örtüşmesi (≥ 1.000 m²) | 2.052 çift, 398,6 km² (1.255 il içi; ≥ 0,1 km²: 1.288) |
| İlçe birleşimindeki delikler | 6.284 (381,6 km²); il katmanı dolu olan dikiş boşluğu 6.062 (367,4 km²) |
| Ülke: il birleşimi / ilçe birleşimi | 779.989 / 779.885 km²; simetrik fark 1.542 km² |
| İl ↔ ilçelerinin birleşimi, simetrik fark | medyan %0,59, en çok %2,03; %2'yi aşan il 1 |
| Tarihsel ilçeler | parçaların bir bölümü (mahalle düzeyinde bölüşüm): 61, parçaların birleşiminden taşıyor: 4, parçaların birleşimiyle aynı: 854 |

İl ve ilçe katmanları ayrı ayrı sadeleştirildiği için sınırları birebir üst üste binmiyor (kıyıda ve il sınırında ~1 km'ye kadar sapma); ilçe katmanının kendi içinde de komşu sınırlar ayrı sadeleştirilmiş. Görünüm etkisi kıl inceliğinde beyaz/çift çizgiler.

**İl ile ilçelerinin birleşimi en farklı 10 il:**

| İl | İl km² | İlçeler km² | İlde var, ilçede yok km² | İlçede var, ilde yok km² | Simetrik fark |
|---|---|---|---|---|---|
| Yalova (77) | 820 | 817 | 9,4 | 7,2 | %2,03 |
| Kilis (79) | 1.408 | 1.410 | 9,4 | 10,9 | %1,44 |
| Kocaeli (41) | 3.406 | 3.400 | 23,1 | 17,6 | %1,19 |
| Muğla (48) | 12.675 | 12.670 | 68,7 | 63,9 | %1,05 |
| İstanbul (34) | 5.472 | 5.468 | 30,3 | 26,6 | %1,04 |
| Iğdır (76) | 3.667 | 3.662 | 20,9 | 16,6 | %1,02 |
| İzmir (35) | 11.883 | 11.884 | 58,9 | 59,8 | %1,00 |
| Bartın (74) | 2.327 | 2.329 | 10,1 | 12,3 | %0,96 |
| Düzce (81) | 2.503 | 2.503 | 11,9 | 11,7 | %0,94 |
| Hatay (31) | 5.512 | 5.510 | 24,6 | 22,4 | %0,85 |

**Dönem il sınırları:**

| Dönem | İl | Geçersiz | İller arası örtüşme km² | Toplam km² | Bugünkü ülkeyle simetrik fark km² |
|---|---|---|---|---|---|
| era1950 | 63 | 0 | 140,2 | 780.136 | 1.295,1 |
| era1954 | 64 | 0 | 140,2 | 780.135 | 1.295,5 |
| era1955 | 66 | 0 | 142,5 | 780.133 | 1.297,0 |
| era1957_1965 | 67 | 0 | 143,8 | 780.132 | 1.297,8 |
| era1957_1987 | 67 | 0 | 143,5 | 780.132 | 1.297,4 |
| era1991 | 74 | 0 | 153,6 | 780.126 | 1.302,6 |
| era1994 | 76 | 0 | 155,4 | 780.125 | 1.303,6 |
| era1995 | 79 | 0 | 355,5 | 779.995 | 5,9 |
| era1999 | 80 | 0 | 357,8 | 779.993 | 3,4 |

1950–1994 dönem dosyaları ile 1995/1999 dosyaları farklı bir taban geometriden üretilmiş görünüyor (bugünkü ülkeyle fark ~1.300 km²'ye karşı 3–6 km²); ikisi de kendi içinde tutarlı.

**Tarihsel ilçeler.** 61 tarihsel ilçe bugünkü ilçelerin yalnız bir bölümünü kapsıyor (İstanbul'da mahalle düzeyinde bölüşüm; beklenen). Bugünkü parçalarının dışına %0,5'ten fazla taşan 4 kayıt:

| geomId | Bugünkü parçalar | Alan km² | Parçaların dışına taşan km² (%) |
|---|---|---|---|
| HIST-Istanbul-Kartal1991 | TR-D-34-025;TR-D-34-027;TR-D-34-032 | 146,7 | 26,6 (%18,16) |
| HIST-Istanbul-Sisli-d44c9c | TR-D-34-024;TR-D-34-035 | 25,6 | 0,3 (%1,26) |
| HIST-Istanbul-Esenler-9208 | TR-D-34-008;TR-D-34-017 | 45,6 | 0,4 (%0,89) |
| HIST-Istanbul-Bakirkoy-733c6e | TR-D-34-005;TR-D-34-006;TR-D-34-007;TR-D-34-008;TR-D-34-017;TR-D-34-022 | 121,4 | 0,7 (%0,56) |

### 4.6 Kapsam: poligonu olan seçmen

Pay: mahalle sonuçlarında bir poligona bağlı muhtarlıkların seçmeni ÷ seçim kaydındaki ilçe seçmeni (yurt içi). 2023'te payda YSK muhtarlık verisinin toplamıyla birebir aynı (60.774.566).

| Seçim | İlçe seçmeni | Poligonu olan seçmen | Pay | Belgede |
|---|---|---|---|---|
| 2009yerel | 39.725.264 | 34.738.126 | %87,45 | %87,3 |
| 2010referandum | 49.495.493 | 44.016.252 | %88,93 | %88,3 |
| 2011 | 50.237.343 | 44.698.148 | %88,97 | %88,3 |
| 2014cb | 52.920.981 | 49.884.312 | %94,26 |  |
| 2014yerel | 48.906.096 | 46.066.274 | %94,19 |  |
| 2015Haziran | 53.772.719 | 50.692.368 | %94,27 |  |
| 2015Kasim | 54.084.541 | 51.001.566 | %94,30 |  |
| 2017referandum | 55.408.773 | 52.228.512 | %94,26 |  |
| 2018 | 56.406.836 | 53.164.391 | %94,25 |  |
| 2018cb | 56.406.836 | 53.164.391 | %94,25 |  |
| 2019yerel | 53.246.898 | 50.358.314 | %94,58 |  |
| 2023 | 60.774.566 | 57.498.090 | %94,61 | %93,8 |
| 2023cb1tur | 60.774.566 | 57.498.090 | %94,61 |  |
| 2023cb2tur | 60.823.248 | 57.543.684 | %94,61 |  |
| 2024yerel | 57.801.470 | 54.693.461 | %94,62 | %94,1 |

"Belgede" sütunu `VERI_DENETIMI_YONETIM.md`'deki 21 Ekim 2026 notlarıdır; sonraki eşleştirme düzeltmeleri (OSM konumu, bütün seçimlerin yeniden işlenmesi) kapsamı 0,5–1 puan artırmış.

**2023 genel: en düşük 10 il**

| İl | Pay | Belgede |
|---|---|---|
| Aksaray | %67,5 |  |
| Iğdır | %68,6 |  |
| Yozgat | %71,0 |  |
| Ağrı | %72,2 |  |
| Niğde | %73,4 |  |
| Siirt | %73,6 |  |
| Hatay | %76,5 | %73,9 |
| Tokat | %76,7 |  |
| Elazığ | %77,0 |  |
| Kütahya | %77,3 |  |

### 4.7 Bağımsız kaynakla konum: ilçe sınırı ↔ TKGM

Depoda ilçe sınırı için ikinci bir sınır seti yok; en yakın bağımsız kaynak TKGM ham birimleri (`data/raw/tkgm/mahalle`, 47.001 birim, her biri TKGM'nin kendi ilçe adıyla). Her ilçede birimlerin birleşimi sitenin ilçe poligonuyla karşılaştırıldı. TKGM'de sınırı gelmeyen birimler olduğu için alan oranı tek başına hata göstermez; asıl ölçü TKGM alanının ilçe sınırının 2 km dışında kalan kısmıdır.

| Ölçü | Değer |
|---|---|
| Karşılaştırılan ilçe | 971 (TKGM birimi olmayan 2) |
| Alan oranı (TKGM / ilçe), medyan | %95,2 |
| IoU, medyan | 0,81 |
| TKGM alanının ilçe dışında kalan payı, medyan | %6,8 |
| Hausdorff uzaklığı, medyan / %95 | 5,3 / 14,6 km |
| 2 km bandı dışında > 10 km² TKGM alanı olan ilçe | 270 |
| 2 km bandı dışında > 1 km² ve > %5 | 68 |

Medyan ilçede iki sınır 1–2 km içinde aynı; fark sitenin ilçe katmanının kaba sadeleştirilmesinden geliyor. Sistematik öteleme yok: TKGM'si eksiksiz (371 ilçe, alan oranı %95–105) ilçelerde ağırlık merkezleri arasındaki uzaklığın medyanı 572 m, ortak yön (doğu -8 m, kuzey -30 m) ihmal edilebilir. Aşağıdaki ilçelerde ise TKGM birimleri ilçe sınırının belirgin biçimde dışına çıkıyor; ya ilçe katmanı o bölgede eski/yanlış ya da TKGM birimi başka ilçeye kayıtlı.

| İlçe (geomId) | İlçe km² | TKGM km² | IoU | 2 km bandı dışı km² (%) | Hausdorff km |
|---|---|---|---|---|---|
| Ceylanpınar (TR-D-63-004) | 1.589 | 2.024 | 0,78 | 285,5 (%14,1) | 14,6 |
| Kadınhanı (TR-D-42-020) | 1.567 | 1.627 | 0,72 | 176,0 (%10,8) | 12,9 |
| Çağlayancerit (TR-D-46-003) | 470 | 678 | 0,59 | 167,5 (%24,7) | 10,5 |
| Espiye (TR-D-28-007) | 252 | 425 | 0,51 | 149,2 (%35,1) | 16,4 |
| Merkez (TR-D-14-001) | 1.616 | 1.198 | 0,52 | 138,5 (%11,6) | 14,1 |
| Karapınar (TR-D-42-021) | 2.626 | 2.660 | 0,82 | 135,3 (%5,1) | 8,6 |
| Kulp (TR-D-21-013) | 1.413 | 1.517 | 0,81 | 130,2 (%8,6) | 9,8 |
| Eruh (TR-D-56-002) | 1.028 | 948 | 0,65 | 124,9 (%13,2) | 16,0 |
| Beyşehir (TR-D-42-005) | 2.056 | 1.807 | 0,68 | 124,1 (%6,9) | 16,4 |
| Yahyalı (TR-D-38-015) | 1.587 | 1.791 | 0,81 | 121,6 (%6,8) | 10,1 |
| Alanya (TR-D-07-003) | 1.577 | 1.659 | 0,79 | 119,5 (%7,2) | 9,0 |
| Toroslar (TR-D-33-012) | 1.073 | 1.058 | 0,67 | 115,4 (%10,9) | 11,1 |
| Akseki (TR-D-07-001) | 1.545 | 1.545 | 0,73 | 115,3 (%7,5) | 10,7 |
| Meram (TR-D-42-024) | 1.788 | 1.897 | 0,82 | 112,5 (%5,9) | 9,3 |
| Gemerek (TR-D-58-005) | 1.130 | 1.318 | 0,79 | 103,5 (%7,8) | 7,7 |
| Merkez (TR-D-70-004) | 4.037 | 4.224 | 0,89 | 94,4 (%2,2) | 6,2 |
| Elmalı (TR-D-07-006) | 1.434 | 1.138 | 0,56 | 89,3 (%7,8) | 14,5 |
| Çukurca (TR-D-30-001) | 730 | 642 | 0,56 | 88,3 (%13,8) | 15,1 |
| Ayrancı (TR-D-70-001) | 2.245 | 2.187 | 0,78 | 87,5 (%4,0) | 9,6 |
| Merkez (TR-D-58-012) | 3.487 | 3.502 | 0,86 | 86,0 (%2,5) | 30,4 |

## 5. Görseller

**İlçesinin 2 km bandı dışına en çok taşan çizilen mahalle**

![01_ilce_disina_tasan_mahalle.png](img/geometri/01_ilce_disina_tasan_mahalle.png)

**Birlikte çizilen en büyük mahalle örtüşmesi**

![02_birlikte_cizilen_ortusme.png](img/geometri/02_birlikte_cizilen_ortusme.png)

**2023: en çok poligonsuz seçmeni olan ilçe**

![03_en_cok_poligonsuz_secmen.png](img/geometri/03_en_cok_poligonsuz_secmen.png)

**TKGM birimleriyle en uyumsuz ilçe sınırı**

![04_tkgm_ilce_uyumsuzlugu.png](img/geometri/04_tkgm_ilce_uyumsuzlugu.png)

## 6. Öneriler (etki / iş sırasıyla)

| # | Öneri | Etki | İş |
|---|---|---|---|
| 1 | Eşleştirmede (`tkgm_muhtarlik_esle.py`) aday sınırı ilçe poligonuyla sına: alanının çoğu ilçenin 2 km bandı dışında kalan TKGM/OSM/belediye birimi alınmasın. Önce `mahalle_yanlis_ilce.csv`'deki uzak 84 çizilen kayda tek tek bak (Ayvatlı, Camii, Ekmekçi, Okçular ...). | Yüksek: yanlış yerde boyanan mahalleler | Az |
| 2 | TKGM × TKGM örtüşmesine kural ekle: aynı seçimde çizilecek iki TKGM biriminden biri ötekinin alanının %25'inden fazlasını kaplıyorsa küçük birim büyükten çıkarılsın ya da iki muhtarlık tek kayıtta toplansın ("birden çok muhtarlık tek sınıra düştü" kuralı gibi). Birebir aynı poligonu paylaşan muhtarlıklar da toplanmalı. | Yüksek: 2.653 üst üste çift | Orta |
| 3 | Mahalle SVG yollarına `fill-rule: evenodd` ver (CSS'te tek satır) ya da kompakt üretimde delik yönünü düzelt. | Orta: 42 poligonda dolu delik | Çok az |
| 4 | `mahalle_geo.json` yazılırken geçersiz poligonları `make_valid` ile onar; LineString ve alanı sıfır kayıtları at. | Düşük–orta: 1.002 geçersiz poligon, hesap güvenilirliği | Az |
| 5 | İlçe katmanını ham kaynaktan topolojiyi koruyarak (mapshaper, ortak arklarla) ve daha az sadeleştirerek yeniden üret; il katmanını ilçelerin birleşiminden türet. | Orta: dikiş boşlukları, kenar taşmaları, il/ilçe uyumsuzluğu | Orta (dosya boyutu artar) |
| 6 | TKGM ile çok farklı çıkan ilçeleri (Ceylanpınar, Kadınhanı, Çağlayancerit, Espiye, Bolu Merkez ...) güncel idari sınırla karşılaştır. | Orta: ilçe sınırının kendisi yanlış olabilir | Orta |
| 7 | Hiçbir seçimde çizilmeyen 1.971 mahalle poligonunu `mahalle_geo.json`'dan çıkar. | Düşük: 1,9 MB | Az |
| 8 | `HIST-Istanbul-Kartal1991`'in bugünkü parçalarının dışına taşan alanını incele. | Düşük | Az |
| 9 | Belgelerdeki kapsam rakamlarını bu rapordakilerle güncelle (2023 genel %93,8 → %94,6). | Düşük | Çok az |
