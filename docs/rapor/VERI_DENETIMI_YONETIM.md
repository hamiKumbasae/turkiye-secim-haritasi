# Veri Denetimi Yönetim Raporu — Türkiye Seçim Haritası

19 Ekim 2026 (son güncelleme 21 Ekim 2026)

## Özet

Sitenin ana haritasındaki il ve ilçe sonuçları büyük ölçüde temiz; sorunlar mahalle ayrıntısında ve ek tablolarda yoğunlaşıyor. Denetim 384.013 sonuç kaydını taradı ve 13.981 bulgu çıkardı. Bunların 600'ü daha önce belgelenmiş bilinen sorunlar.

İki konu öncelikli. Birincisi, 2.453 mahallede katılım %100'ü aşıyor (7.962 kayıt); kaynak YSK, ama site bunu açıklamadan gösteriyor. İkincisi, 3.591 mahalle kaydında kazanan hâlâ "Diğer"; ilçe düzeyinde düzelttiğimiz sorun mahalle düzeyinde duruyor.

Denetim veriyi değiştirmez; yalnızca bulur ve sayar.

## Bulgular

On bir bulgu türünden üçü yüksek öncelikli ve henüz açık. "Kısmen belgeli" satırlarda kayıtların bir bölümü zaten bilinen sorunlar listesinde (`tests/fixtures/known-validation-issues.json`).

| Bulgu | Önem | Kayıt | Nerede | Durum |
| --- | --- | --- | --- | --- |
| Katılım %100'ü aşıyor | Yüksek | 8.067 | mahalle 7.962, meclis birimi 72, belde 27, Senato 6 | Açık |
| Kazanan "Diğer" (ayrıştırılmamış) | Yüksek | 3.601 | mahalle 3.591, ilçe 10 (1994–1999 yerel) | Açık |
| İl toplamı ilçelerinin toplamını tutmuyor (>%1) | Yüksek | 54 | il; genel 1965–2002, referandum 1987–1988 | Açık |
| Parti oyları toplamı geçerli oyu tutmuyor | Orta | 1.203 (374 belgeli) | meclis birimi 625, ilçe 321, TÜİK 159, il 97 | Kısmen belgeli |
| Yazılı oran oy sayısından hesaplananla tutmuyor | Orta | 200 (119 belgeli) | il 184 (çoğu 1950–2007 genel), ilçe 14, mahalle 2 | Kısmen belgeli |
| Geçerli oy kayıtlı seçmenden fazla | Orta | 188 (107 belgeli) | ilçe 107, meclis birimi 56, TÜİK 25 | Kısmen belgeli |
| Oy sayısı negatif ya da kesirli | Düşük | 2 | 1979 Senato (TİP: 0,7) | Açık |
| Seçmen sayısı yok, oy var | Düşük | 247 | ilçe 190, il 47 (ör. Sakarya 1957–1977) | Bilgi amaçlı |
| Kazanan en çok oy alan parti değil | Düşük | 86 | ilçe 60, il 26 | Bilgi amaçlı |
| Katılım %20'nin altında | Düşük | 152 | mahalle 133, ilçe 12, il 5 | Bilgi amaçlı |
| Mahalle seçmeni iki seçim arasında 5 kattan fazla değişiyor | Düşük | 181 | mahalle | Bilgi amaçlı |

## Katılımı %100'ü aşan kayıtlar

2.453 farklı mahallede, en az bir seçimde oy kullanan sayısı kayıtlı seçmenden fazla (toplam 7.962 kayıt). Bu bir site hatası değil: YSK'nin kendi sandık verisinde de var. Örneğin 2019 İstanbul yenileme seçiminde 31.186 sandığın 52'sinde oy kullanan, kayıtlı seçmenden fazla.

**Neden:** YSK'nin "oy kullanan" sayısına, sandığın listesinde kayıtlı olmayıp orada oy kullananlar da giriyor. En olası açıklama sandık kurulu üyeleri; yasal dayanağı bir kaynaktan doğrulanmadı. Seçmeni az ya da katılımı zaten çok yüksek mahallelerde birkaç ek oy, oranı %100'ün üstüne taşıyor.

**Kalıcı olanlar:** 575 mahalle en az beş seçimde %100'ü aşıyor. Bunlar neredeyse kimsenin oturmadığı çarşı ve iş merkezi mahalleleri; örneğin Tahtakale (Fatih), 2023 genel seçimde 13 kayıtlı seçmen ve 17 oyla %130,77.

**Önerilen çözüm:** Oy sayılarına dokunmadan, katılım %100'ü aştığında sitede oran yerine "hesaplanamıyor" ve kısa bir açıklama göstermek. Ana haritada (il ve ilçe) bu durum hiç yok.

## Diğer bulgular

### Mahallede kazanan "Diğer"

3.591 mahalle kaydında kazanan "Diğer" görünüyor. Mahalle verisi çekilirken yalnızca büyük partiler ayrı tutulmuş, küçük partiler tek bir "Diğer" satırında toplanmış; örneğin İYİ Parti 2019'da bu satırın içinde kalıyor. İlçe düzeyinde aynı sorun Ekim 2026'da YSK verisi yeniden çekilerek çözüldü; mahalle düzeyi hâlâ eski hâliyle duruyor.

| Seçim | Kazananı "Diğer" olan mahalle kaydı |
| --- | --- |
| 2019 yerel | 1.996 |
| 2014 yerel | 952 |
| 2024 yerel | 371 |
| 2009 yerel | 138 |
| 2023 genel | 70 |
| 2015 Haziran | 52 |
| 2018, 2011, 2015 Kasım | 12 |

### İl toplamı ilçelerinin toplamını tutmuyor

54 il kaydında il sayısı, ilçelerinin toplamından %1'den fazla farklı (42'si genel seçim, 12'si referandum). En büyük farklar:

| Seçim | İl | İl kaydı | İlçeler toplamı | Fark | Olası neden |
| --- | --- | --- | --- | --- | --- |
| 1973 genel | Ankara | 786.398 seçmen | 985.132 | +%25,3 | Merkez ilçeler (Çankaya, Altındağ, Yenimahalle, Merkez) örtüşüyor olabilir |
| 1973 genel | Kastamonu | 285.894 seçmen | 222.934 | −%22,0 | Bazı ilçeler eksik olabilir |
| 2002 genel | Kocaeli | 752.556 seçmen | 852.556 | +%13,3 | Fark tam 100.000: tek basamaklık yazım hatası olabilir |
| 1973 genel | Bitlis | 60.300 seçmen | 67.415 | +%11,8 | İncelenmeli |
| 1982 referandum | Van | 132.130 seçmen | 147.453 | +%11,6 | İncelenmeli |
| 1973 genel | Gaziantep | 268.722 seçmen | 239.914 | −%10,7 | Bazı ilçeler eksik olabilir |

### Ek dosyalardaki tutarsızlıklar

Belediye meclisi, il genel meclisi, belde ve Senato dosyalarında 1.015 bulgu var (oy toplamı tutmuyor, geçerli oy seçmenden fazla, katılım %100 üstü). Bunların çoğu 1994 ve 1999 yerel seçim dosyalarında: 1999 belediye meclisi 239, 1994 belediye meclisi 199, 1999 il genel meclisi 159, 1999 beldeler 140. Bu dosyalar mevcut doğrulayıcının kapsamında değildi, ilk kez denetlendi. 1979 Senato'da iki kayıtta oy sayısı yerine kesirli bir sayı var (TİP: 0,7); muhtemelen yanlış sütuna yazılmış bir yüzde.

## Güncelleme: büyükşehir mahalle haritası (19 Ekim 2026)

30 büyükşehirde 2015 Haziran, 2015 Kasım, 2018 ve 2023 genel seçimlerinin mahalle sonuçları YSK açık veriden muhtarlık düzeyinde, bütün partilerle yeniden çekildi. Sınırı olmayan mahalle ve köyler Tapu ve Kadastro Genel Müdürlüğü (TKGM) sınırlarıyla dolduruldu. Önce mevcut OSM/ttezer sınırları kullanılıyor; TKGM sınırı yalnız boşluğu dolduruyor ve mevcut sınırlarla çakışan TKGM birimi çizilmiyor.

| Seçim | Haritaya bağlanan seçmen (önce) | Sonra |
| --- | --- | --- |
| 2015 Haziran | %83,3 | %92,8 |
| 2015 Kasım | %83,4 | %92,8 |
| 2018 | %83,4 | %92,8 |
| 2023 | %84,4 | %93,3 |

Hâlâ en zayıf iller: Kahramanmaraş (%58,5), Hatay (%73,7), Van (%81,5). Bu illerde TKGM'nin kadastro mahalleleri bugünkü idari mahallelerle örtüşmüyor; şehir merkezlerindeki birçok yeni mahallenin hiçbir açık kaynakta sınırı yok. Eşleşmeyen muhtarlıkların listesi `docs/rapor/mahalle_eslesme/*.csv` dosyalarında.

Yan etkiler: bu dört seçimde mahallede kazananı "Diğer" görünen kayıt kalmadı (kazanan artık gerçek parti). Katılımı %100'ü aşan mahalle kaydı ise arttı (2023: 868'den 1.401'e), çünkü haritada artık çok daha fazla küçük köy var. Bunlar YSK'nin kendi sayıları. TKGM sınırlarının açık veri lisansı yok; sitede kaynak olarak gösteriliyor ve sitenin CC BY-SA lisansının dışında tutuluyor.

**21 Ekim 2026 — 81 il:** Aynı yöntem kalan 51 ile ve 2023 CB 1./2. tur ile 2024 yerel seçime genişletildi. Türkiye genelinde haritaya bağlanan seçmen: 2015 Haziran %81,8 → %90,8; 2018 %82,1 → %91,0; 2023 genel %83,0 → %91,4; 2023 CB %76,0 → %91,4; 2024 yerel %79,2 → %91,6. Büyükşehir olmayan illerde oran %44–54'ten %82–85'e çıktı. Kalan yaklaşık 5 milyon seçmen çoğunlukla şehir merkezlerinde TKGM'de karşılığı olmayan idari mahallelerde.

**21 Ekim 2026 — güncel OSM sınırları:** Kahramanmaraş, Hatay ve Van belediyelerinin indirilebilir mahalle sınırı sunan bir açık veri portalı bulunamadı; yalnızca lisansı belirtilmemiş kent rehberi (KEOS) haritaları var. Bunun yerine OpenStreetMap'teki güncel mahalle sınırları 81 il için çekildi ve TKGM'den önce kullanıldı. 2023 genel seçimde haritaya bağlanan seçmen %91,4 → %93,8 (2024 yerel %91,6 → %94,1). Kahramanmaraş %56,4 → %78,8, Van %81,5 → %83,1; Hatay'da OSM'de de sınır olmadığı için değişmedi (%73,9).

**21 Ekim 2026 — kamu açık verisi:** Mahalle sınırını açık lisansla yayımlayan kamu kaynakları tarandı. Ulusal Coğrafi Bilgi Platformu (TUCBS) veriyi yalnız e-Devlet ile başvuru ve onayla veriyor. Açık lisanslı mahalle sınırı yayımlayan belediyeler: Bursa, Sakarya ve Gaziantep. Bursa ve Sakarya sınırları eklendi: Bursa %97,8 → %100, Sakarya %97,6 → %99,1. Gaziantep portalının SSL sertifikası hatalı olduğu için indirilemedi. Kahramanmaraş, Hatay ve Van için açık kamu kaynağı yok.

**26 Ekim 2026 — mahalle sınırı kaynakları yeniden tarandı:** 2023'te en çok boş seçmeni olan iller (Hatay, Manisa, Mersin, Adana, Kahramanmaraş, Diyarbakır, Van, Samsun) için belediye açık veri portalları arandı. Yalnız Manisa'nın portalı var (acikveri.manisa.bel.tr, CKAN). Orada mahalle sınırı vektör verisi yok: yalnız JPEG mahalle krokileri, nüfus/yapı tabloları ve nokta KML'leri. Diğer illerde açık veri portalı bulunamadı. Gaziantep'te boşluk 1 muhtarlığa (604 seçmen) indiği için indirilmedi. Bakanlığın "Türkiye Ulusal Coğrafi Açık Veri Portalı" adresi (tucbskontrol.csb.gov.tr) artık çözülmüyor. TKGM'nin boş döndürdüğü 2.768 birim yeniden soruldu, hiçbiri dolmadı. GitHub'daki mahalle sınırı depoları OSM/TKGM kaynaklı (yeni kaynak değil); BM COD-AB yalnız il/ilçe düzeyinde. Kalan seçenekler kullanıcıda: Kadir Has Üniversitesi ekibine yazılan istek (Marmara'daki 11 il; sınırlarının kaynağı soruldu) ve İçişleri/Bakanlığa bilgi edinme başvurusu.

**21 Ekim 2026 — eski yerel seçimler:** 2009, 2014 ve 2019 yerel seçimlerin mahalle verisi YSK'den muhtarlık düzeyinde, bütün partilerle yeniden çekildi. Kazananı "Diğer" görünen mahalle kaydı 3.089'dan 3'e indi; kalan 3 kayıt 2011 genel seçimde. Haritaya bağlanan seçmen: 2009'da %68,7 → %81,6, 2014'te %78,1 → %93,8, 2019'da %78,7 → %94,2. 2009'da 14 ilin o yılki merkez ilçesi (2,6 milyon seçmen) sonradan birkaç ilçeye bölündüğü için bugünkü ilçelere eşlenemiyor. Ayrıca sitede, bir bağlantı açılırken adres değişince yeni adresin kaybolmasına yol açan hata düzeltildi.

**21 Ekim 2026 — bütün seçimler ve eski ilçeler:** 2011 genel, 2010 ve 2017 halkoylaması, 2014 ve 2018 cumhurbaşkanlığı da YSK'den muhtarlık düzeyinde yenilendi; artık 2009–2024 arasındaki 15 seçimin hepsi aynı yöntemle. Sonradan bölünen eski ilçeler (2009 Kahramanmaraş Merkez = Dulkadiroğlu + Onikişubat gibi) genel seçimlerde kullanılan tarihsel ilçe kaydı üzerinden halef ilçelerin sınırlarıyla çiziliyor. Haritaya bağlanan seçmen: 2009 %87,3; 2010 ve 2011 %88,3; 2014–2024 %93,5–94,3. Mahallede kazananı "Diğer" görünen kayıt kalmadı (3.089 → 0).

## Eylem planı

Yedi iş var; ilk üçü yüksek öncelikli. Süreler tahmini.

| # | İş | Öncelik | Tahmini süre | Durum |
| --- | --- | --- | --- | --- |
| 1 | Katılım %100'ü aştığında sitede oran yerine "hesaplanamıyor" ve açıklama göster | Yüksek | yarım gün | Yapılacak |
| 2 | Mahalle verisini YSK'den bütün partilerle yeniden çek, "Diğer"i ayır (büyükşehirlerde 2015–2023 genel seçimleri yapıldı; yerel seçimler ve diğer iller kaldı) | Yüksek | 1–2 gün | Yapılacak |
| 3 | Kocaeli 2002 seçmen sayısını kaynakla karşılaştır, düzelt | Yüksek | birkaç saat | Yapılacak |
| 4 | 1973 Ankara, Kastamonu, Gaziantep, Bitlis ve kalan il–ilçe farklarını incele | Orta | 1 gün | Yapılacak |
| 5 | 1994–1999 meclis ve belde dosyalarını kaynak tablolarla karşılaştır | Orta | 2–3 gün | Yapılacak |
| 6 | Denetimi otomatik kontrollere ekle: yeni bulgu çıkarsa uyarsın | Orta | birkaç saat | Yapılacak |
| 7 | 1979 Senato'daki kesirli oy sayılarını düzelt | Düşük | birkaç saat | Yapılacak |

## Yöntem ve tam listeler

Denetimi [`scripts/veri_denetimi.py`](../../scripts/veri_denetimi.py) yapıyor. Betik `data/normalized` altındaki bütün sonuç kayıtlarını (il, ilçe, mahalle, meclis, belde, Senato) aynı kurallarla tarıyor, sonra düzeyleri birbiriyle karşılaştırıyor; veriyi değiştirmiyor. Daha önce belgelenmiş sorunlar "belgeli" diye ayrılıyor. Yeniden çalıştırmak için:

```
python3 scripts/veri_denetimi.py --md docs/rapor/VERI_DENETIMI.md --csv-klasor docs/rapor/veri_denetimi
```

Her bulgu türünün tam listesi ayrı bir CSV dosyasında (sütunlar: dosya, düzey, birim, ayrıntı, belgeli):

| Liste | Kayıt |
| --- | --- |
| [Katılım %100'ü aşanlar](veri_denetimi/KATILIM_100_USTU.csv) | 8.067 |
| [Kazananı "Diğer" olanlar](veri_denetimi/KAZANAN_DIGER.csv) | 3.601 |
| [Oy toplamı tutmayanlar](veri_denetimi/OY_TOPLAMI_TUTMUYOR.csv) | 1.203 |
| [Seçmen sayısı olmayanlar](veri_denetimi/SECMEN_YOK_OY_VAR.csv) | 247 |
| [Oranı tutmayanlar](veri_denetimi/ORAN_HESAPLA_TUTMUYOR.csv) | 200 |
| [Geçerli oyu seçmenden fazla olanlar](veri_denetimi/GECERLI_SECMENDEN_FAZLA.csv) | 188 |
| [Mahalle seçmeni sıçrayanlar](veri_denetimi/MAHALLE_SECMEN_SICRAMASI.csv) | 181 |
| [Katılımı %20'nin altında olanlar](veri_denetimi/KATILIM_COK_DUSUK.csv) | 152 |
| [Kazananı en çok oy alan olmayanlar](veri_denetimi/KAZANAN_EN_COK_OY_DEGIL.csv) | 86 |
| [İl–ilçe toplamı tutmayanlar](veri_denetimi/IL_ILCE_TOPLAMI.csv) | 54 |
| [Negatif ya da kesirli oy](veri_denetimi/OY_NEGATIF_YA_DA_KESIRLI.csv) | 2 |

Teknik ayrıntılı rapor: [`docs/rapor/VERI_DENETIMI.md`](VERI_DENETIMI.md).
