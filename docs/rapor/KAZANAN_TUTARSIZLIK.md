# Kazanan ile en çok oy tutarsızlığı (il/ilçe)

31 Ekim 2026. Kapsam: `data/normalized/elections/*/*.json` içindeki bütün il ve ilçe kayıtlarında `kazanan` alanı, `oy` alanında en çok oyu alan parti ya da aday değilse. Oyu boş olan ve `sadeceKazanan` kayıtlar dışarıda. Eşitlik ayrı sayıldı. `Diğer` ve `Bağımsız` toplam satırları ayrı işaretlendi.

## Özet

İlk taramada **99 kayıt** çıktı. 27'sinde en çok oyu tek bir parti almış, 72'sinde en büyük satır bir toplam (`Bağımsız` 57, `Diğer` 15). Bu sayı `docs/rapor/veri_denetimi/KAZANAN_EN_COK_OY_DEGIL.csv` dosyasının il ve ilçe satırlarıyla aynı (98 satır ve eşitlik olan 1977 Türkeli). Önceki "86" sayısı başka bir eşikten gelmiş olmalı.

| Sınıf | Kayıt | Anlamı | Eylem |
|---|---|---|---|
| (a) Açıklanabilir | 78 | Toplam satırı (birden çok bağımsız aday ya da birden çok parti), mazbata iptali, 1950'de vekil sayısına göre kazanan, kurayla çözülen eşitlik, 1955'te meclisin seçtiği başkan | Veri aynı kaldı. Notu olmayan 47 kayda `not` eklendi (il merkezi kopyalarına il satırının notu yazıldı) |
| (b) Kazanan yanlış | 0 (+14 gizli) | Taranan 99 kaydın hiçbirinde kazanan yanlış değil. Aynı kök nedeni ararken 2024'te kazananın yanlış olduğu, ama oyların da aynı yanlışı taşıdığı için tutarsız görünmeyen 14 ilçe bulundu (aşağıda) | 14 ilçenin kazananı ve oyları düzeltildi |
| (c) Oylar yanlış | 19 | 2009–2024 yerel: oylar ilçe belediyesinin değil, ilçe merkezi ile bağlı belde belediyelerinin başkanlık oylarının toplamı | 19 kaydın oyu, geçerli oyu, seçmeni, sandığı ve katılımı ilçe belediyesinin kendi sonucuyla değiştirildi |
| (d) Belirlenemedi | 2 | 1963 Tortum, 1977 Haymana: Vikipedi ile DİE kitabında iki oy yer değiştirmiş | Not belirsizliği yazacak şekilde düzeltildi, kazanan aynı |

Sonuç: düzeltmeden sonra kazanan ile en çok oy arasında **80 kayıtta** fark kalıyor. Hepsi (a) ya da (d) ve her birinin notu var. Haritada **14 ilçenin rengi değişti** (2024). 19 düzeltilen kaydın (c) rengi aynı, çünkü kazanan zaten doğruydu. Değişen ipucu ve detay paneli: oylar, yüzdeler ve katılım.

**Güncelleme (1 Kasım 2026):** Kök neden kalıcı olarak düzeltildi. YSK'nin belde ayrımlı başkanlık verisiyle 1.095 ilçe ve 164 il satırı ilçe belediyesinin kendi sonucuna çevrildi; 188 ilçede (2009: 131, 2014: 28, 2019: 26, 2024: 3) ve 7 il satırında kazanan da değişti. PR #18'in 33 kaydı YSK ile birebir tuttu. Ayrıntı: "Kalıcı düzeltme" bölümü.

## Kök neden: belde oyları ilçe toplamına karışmış (2009–2024 yerel)

`data/raw/ysk/yerel-v2-agrege/` (`fetch_yerel_v2.js`) ilçe toplamını, belde sandıkları da dahil olmak üzere ilçedeki bütün belediye başkanlığı sandıklarından topluyor. Bir belde belediyesi kendi başkanını ayrı bir yarışta seçer; bu sandıklardaki oylar başka adaylara verilmiştir. Belde ayrımlı YSK meclis verisiyle (`data/raw/ysk/acikveri-belde-agrege/<yıl>yerel_belediye_meclisi.json`) karşılaştırıldığında, beldesi olan her ilçede v2 toplamının sandık sayısı "ilçe merkezi + beldeler" ile birebir aynı çıkıyor: 2009'da 560 ilçe, 2014–2024'te her yıl 184 ilçe. Beldesiz ilçelerde (2024'te 789) sandık sayısı birebir tutuyor, yani sorun yok.

Kanıt (2024 Kırklareli Merkez): v2 225 sandık = merkez 200 + üç belde 25. Vikipedi'deki ilçe belediyesi sonucunun oy kullananı (51.021 geçerli + 1.924 geçersiz = 52.945) YSK'nin belde hariç merkez sandıklarındaki oy kullananla (52.934) tutuyor. v2 ile Vikipedi arasındaki geçerli oy farkı (5.525) beldelerin geçerli oyuna (meclis, 5.484) eşit. CHP'nin "önde" görünmesi beldelerdeki CHP adaylarının oyundan geliyordu (v2 CHP 23.719, ilçe belediyesinde 20.770).

Belde oyları kazananı çoğu yerde değiştirmiyor. Değiştirdiği yerde iki durum çıkıyor:
- **Görünür (c):** Kayıttaki kazanan aday bazlı doğru kaynaktan gelmiş, oylar karışık toplam. Tutarsızlık bu yüzden görünüyordu (Kırklareli, Kütahya, Hakkari...).
- **Gizli (b):** Kazanan da karışık toplamdan seçilmiş. Kayıt kendi içinde tutarlı, ama kazanan yanlış. Bu ilçeler denetimde görünmüyordu. 2024'te 14 tane bulundu ve düzeltildi.

Aynı nedenle beldesi olan öteki ilçelerin oy ve oranları da şişkindi. 1 Kasım 2026'da bunların hepsi YSK'nin belde ayrımlı başkanlık verisiyle düzeltildi (aşağıda "Kalıcı düzeltme"); bu sırada 2009–2019'da 185 gizli kazanan hatası daha bulundu.

### Düzeltme yöntemi ve doğrulama
- **Yeni değerler:** Vikipedi il sayfasındaki ilçe belediyesi tablosu (sayfalar YSK sonuçlarını kaynak gösteriyor; arşivdeki revizyon `data/raw/wikipedia/il-sayfalari/yerel/<yıl>/`). Mevcut ayrıştırıcı (`data/kaynaklar/wikipedia`) içinde `<ref>` olan satırları atlıyordu, bu yüzden tablo yeniden okundu.
- **Birinci kontrol, YSK'nin kendi verisi:** Seçmen ve sandık, YSK belde ayrımlı verisindeki ilçe merkezi sandıklarından alındı. Kabul için iki şart arandı: Vikipedi'nin oy kullananı (geçerli + geçersiz) YSK'nin aynı sandıklardaki oy kullananıyla %0,5 içinde tutmalı (30 kaydın çoğunda fark 0–20 oy). Her parti oyu da v2'deki ilçe + belde toplamını aşmamalı.
- **İkinci kaynak:** Anadolu Ajansı verisi (Mynet, Daily Sabah). 2024'teki 13 görünür kayıttan 10'u (Hakkari, Gölbaşı, Çay, Bulancak, Ardeşen, Reşadiye, Banaz, Aydıncık, Kilimli, Çınarcık) ve 2019 Baykan ile Sarıveliler birebir tuttu. Kütahya'da Türkiye gazetesi yeniden sayım sonrası rakamları verdi (CHP 40.739, MHP 40.168, fark 571), bunlar da birebir aynı. Ürgüp'te AA itiraz öncesi rakamları biraz farklı (CHP 5.170, MHP 5.134). Vikipedi itiraz sonrası değerleri veriyor; oy kullanan iki kaynakta da 15.060. Çınarcık'ta Vikipedi tablosunda eksik olan HÜDA PAR 17 oy AA'dan eklendi.
- **Kırklareli:** AA ve haberler MHP 21.173, Millet 237, fark 403 yazıyor. Vikipedi'de MHP 21.287, MP92 123. İki parti toplamı iki kaynakta da aynı (21.410). YSK sandık verisinde Millet (MP92) beldeler dahil yalnız 123 oy almış, yani 237 olamaz. Bu yüzden Vikipedi esas alındı. Kazanan iki kaynakta da MHP.
- **2009 Sarayönü:** İkinci bir web kaynağı bulunamadı. Yalnız YSK tutarlılığına dayanıyor (oy kullanan 5.779, YSK'de 5.767).
- **Kayıt biçimi:** Eski YSK toplamı `kaynak.yskSatiri` altında duruyor (`birim: "ilçe merkezi ve bağlı beldelerin toplamı"`, eski oy, kazanan, seçmen, sandık, katılım, önceki `kaynak` ve `veriNotu`). Yeni değerlerin kaynağı `kaynak.ilceBelediyesi` altında (aday listesi, Vikipedi revizyonu, ikinci kaynak, YSK kontrol sayıları). Bu, 1994–2004 için kullanılan `ilce_belediyesi_sonucu.py` düzeniyle aynı. İl merkezi olan illerde (Hakkari, Kırklareli, Kütahya) il satırı ilçe satırıyla aynı değeri aldı.
- **Denetim betiği:** `veri_denetimi.py`'deki `MAHALLE_ILCEDEN_BUYUK` kontrolü, kayıtta `kaynak.yskSatiri` varsa mahalle seçmen toplamını oradaki ilçe toplamıyla karşılaştırıyor. Mahalle dosyası beldeler dahil ilçenin bütün sandıklarını kapsıyor.

### Örnek kayıtlar
- **Kırklareli 2024 (il ve Merkez):** Kazanan **MHP doğru**. Görevdeki CHP'li başkan Mehmet Siyam Kesimoğlu'nu MHP'li **Derya Bulut** yendi ve mazbatasını aldı (haberler.com, NTV, Cumhuriyet). "CHP'li Derya Bulut kazandı" bilgisi yanlıştı. Hatalı olan oylardı. Yeni değerler: MHP 21.287, CHP 20.770, Bağımsız (beş aday) 3.427.
- **Kütahya 2024:** Kazanan **CHP (Eyüp Kahveci) doğru**. MHP'nin 27 oy önde görünmesi tek bir beldenin (5 sandık) başkanlık oylarından geliyordu. Geçersiz oylar yeniden sayıldı, sonuç değişmedi: CHP 40.739, MHP 40.168 (Türkiye gazetesi, Medyascope).
- **Hakkari 2024:** Kazanan **DEM Parti (Mehmet Sıddık Akış) doğru**. AK Parti'nin önde görünmesi bir beldenin 10 sandığından geliyordu. Yeni değerler: DEM 14.528, AK Parti 13.833 (Mynet/AA ile birebir). Akış Haziran 2024'te görevden alındı ve yerine kayyum atandı; harita seçim sonucunu gösterir.
- **Ürgüp 2024:** İl seçim kurulu seçimin yenilenmesine karar vermişti; YSK bu kararı kaldırdı (NTV, 7 Nisan 2024). Kazanan CHP doğru.

### Gizli kazanan hataları (2024, düzeltildi)

| geomId | İl / İlçe | Eski kazanan | Doğru kazanan (Vikipedi, YSK tutarlı) | Ek kaynak |
|---|---|---|---|---|
| TR-D-03-008 | Afyonkarahisar / Dinar | AK Parti | CHP (CHP 7.727 – AK Parti 6.278) | — |
| TR-D-03-016 | Afyonkarahisar / Sinanpaşa | AK Parti | MHP (MHP 1.203 – AK Parti 1.037) | — |
| TR-D-15-007 | Burdur / Gölhisar | MHP | AK Parti (AK Parti 4.287 – MHP 3.946) | — |
| TR-D-15-005 | Burdur / Çavdır | MHP | CHP (CHP 1.894 – MHP 1.506) | — |
| TR-D-18-010 | Çankırı / Orta | AK Parti | MHP (MHP 1.048 – AK Parti 863) | — |
| TR-D-22-009 | Edirne / Uzunköprü | CHP | İYİ Parti (İYİ Parti 8.029 – CHP 7.944) | [AA/Mynet](https://finans.mynet.com/yerel-secim-2024/edirne-uzunkopru-belediyesi-secim-sonuclari): AA geçici sonucu İYİ 8.026 / CHP 7.941 (kazanan aynı); DHA: "İYİ Parti'den istifa eden Uzunköprü Belediye Başkanı Martin CHP'ye katıldı" |
| TR-D-22-004 | Edirne / İpsala | CHP | AK Parti (AK Parti 1.645 – CHP 1.533) | — |
| TR-D-32-005 | Isparta / Gönen | AK Parti | CHP (CHP 1.073 – AK Parti 792) | — |
| TR-D-40-004 | Kırşehir / Çiçekdağı | MHP | AK Parti (AK Parti 2.248 – MHP 1.962) | — |
| TR-D-58-002 | Sivas / Altınyayla | AK Parti | MHP (MHP 1.362 – AK Parti 1.239) | — |
| TR-D-60-001 | Tokat / Almus | CHP | MHP (MHP 1.543 – AK Parti 1.523) | [AA/Mynet](https://finans.mynet.com/yerel-secim-2024/tokat-almus-belediyesi-secim-sonuclari): AA geçici sonucu MHP 1.540 / AK Parti 1.518 (kazanan aynı) |
| TR-D-66-007 | Yozgat / Kadışehri | AK Parti | YENİDEN REFAH (YENİDEN REFAH 1.330 – AK Parti 1.319) | [AA/Mynet](https://finans.mynet.com/yerel-secim-2024/yozgat-kadisehri-belediyesi-secim-sonuclari): AA geçici sonucu YENİDEN REFAH 1.333 / AK Parti 1.326 (kazanan aynı) |
| TR-D-66-008 | Yozgat / Saraykent | AK Parti | MHP (MHP 1.721 – AK Parti 1.435) | — |
| TR-D-77-001 | Yalova / Altınova | AK Parti | CHP (CHP 2.714 – AK Parti 2.332) | — |

AA'yla kontrol edilen üç örnekte (Uzunköprü, Almus, Kadışehri) kazanan doğrulandı. Uzunköprü'de DHA haberi de var: İYİ Parti'den seçilen başkan Ediz Martin sonradan CHP'ye geçti. Öteki 11 ilçe yalnız Vikipedi ve YSK tutarlılığına dayanıyor. Vikipedi tablosunda kazanan işaretli ve oy kullanan YSK ile birebir tutuyor.

Taramada kontrolden geçmeyen üç gizli aday (Muş Hasköy, Şırnak Güçlükonak, Aksaray Güzelyurt) 1 Kasım 2026'da YSK'nin ilçe merkezi başkanlık sandıklarıyla çözüldü (aşağıda).

## Kalıcı düzeltme: belde ayrımlı YSK başkanlık verisi (1 Kasım 2026)

**Veri:** `.github/workflows/ysk-belde-baskan-cek.yml` (`fetch_belde_agrege.js`, `secimTuru=2`) dört seçimin belediye başkanlığı sandıklarını (il, ilçe, belde) birimlerinde topladı: `data/raw/ysk/acikveri-belde-agrege/<yıl>yerel_belediye_baskanligi.json` (run 41255410827, başarısız sorgu 0). Her ilçede ilçe merkezi + belde birimlerinin toplamı eski `yerel-v2-agrege` ilçe toplamıyla (sandık, geçerli oy, seçmen) birebir aynı; yani yeni veri eskisini yalnız böldü.

**Uygulama:** `scripts/pipelines/election_import/belde_ayir_baskan.py uygula`. Beldesi olan ilçede kayıt eski v2 toplamıysa (sandık ve geçerli oy aynı) oy, oran, geçerli oy, seçmen, sandık, katılım ve kazanan ilçe merkezi biriminden alındı. Kazanan aday düzeyinde (her bağımsız aday ayrı). Eski değerler `kaynak.yskSatiri`, yeni değerlerin kaynağı `kaynak.ilceBelediyesi` altında (PR #18 düzeni; oy kullanan, geçersiz, belde sayısı ve belde sandığı da orada). Büyükşehir olmayan illerde il satırı il merkezi ilçesinin satırını aldı; büyükşehir il satırları (ayrı yarış) değişmedi. Her kaydın durumu: `docs/rapor/belde_ayrimi_baskanlik.csv`.

| Seçim | Beldeli ilçe | İlçe düzeltildi | Kazananı değişen ilçe | İl satırı | Önceden düzeltilmiş (PR #18) | Düzeltilemeyen |
|---|---|---|---|---|---|---|
| 2009 | 580 | 572 | 131 | 55 | 1 | 6 (+ Kadışehri, Vikipedi kaydı) |
| 2014 | 184 | 184 | 28 | 38 | 0 | 0 |
| 2019 | 184 | 182 | 26 | 37 | 2 | 0 |
| 2024 | 184 | 157 | 3 | 34 | 27 ilçe + 3 il | 0 |

Toplam 1.095 ilçe ve 164 il satırı; 188 ilçede ve 7 il satırında (2009 Aydın, Gümüşhane, Hatay, Zonguldak; 2014 Zonguldak, Yalova; 2019 Karaman) kazanan değişti. Kazanan yalnız eski kazanan karışık toplamın birincisiyse değiştirildi (ya da 2009 Yazıhan'da olduğu gibi bağımsız kazanan karışık toplamdan seçilmişse); bunun dışında kalan kayıt çıkmadı. Bilinen sonuçlarla örnek kontrol: 2009 Alanya ANAP, Bodrum DP, Aydın CHP, Antakya (Hatay merkez) AK Parti; 2014 Yalova CHP; 2019 Karaman MHP. e-sehir.com'daki 2014 Hopa (AK Parti 4.546, CHP 4.523), 2009 Zonguldak merkez (CHP 27.319, AK Parti 20.916) ve 2009 Gümüşhane merkez (MHP 5.803, AK Parti 5.768) oyları yeni değerlerle birebir aynı.

Fark 10 oy ya da daha az olan kazanan değişiklikleri (sandık toplamı, itiraz sonrası kesin sonuçtan farklı olabilir): 2009 Göynücek (DP, 2), Akseki (CHP, 4), Gemerek (AK Parti, 4), Ulaş (MHP, 3); 2014 Avanos (CHP, 7), Yalova merkez (CHP, 6); 2024 Güzelyurt 31 Mart (İYİ Parti, 1; seçim iptal edildi).

**PR #18'in 33 kaydıyla karşılaştırma:** 30 ilçe ve 3 il satırının hepsinde YSK ilçe merkezi verisi Vikipedi'den alınan değerlerle birebir aynı (her parti oyu, geçerli oy, seçmen, sandık, oy kullanan, kazanan). Kırklareli'de YSK de MHP 21.287 / MP92 123 veriyor. Bu kayıtlar değiştirilmedi.

**Açık kalan üç 2024 kaydı:**
- **Muş Hasköy:** MHP 2.827, AK Parti 2.666 (29 sandık, belde hariç). Eski kayıtta AK Parti (bir beldenin oyları dahil). Vikipedi tablosu da MHP 2.827, geçerli oy 6.591. Kazanan MHP.
- **Şırnak Güçlükonak:** BBP 825, AK Parti 750, CHP 619 (10 sandık). Eski kayıtta AK Parti. Vikipedi de aynı. Kazanan BBP.
- **Aksaray Güzelyurt:** 31 Mart'ta ilçe belediyesinde İYİ Parti 549, AK Parti 548, MHP 537; seçim iptal edildi. Kayıt artık 2 Haziran 2024 yenilemesini gösteriyor: AK Parti 874 (Ünal Demircioğlu), İYİ Parti 580, MHP 287 (`2024yenileme_baskan.json`, birim 68-754-0; NTV). 31 Mart değerleri `kaynak.yenileme.ilkSecim`, belde dahil eski toplam `kaynak.yskSatiri` altında; `not` ipucunda görünüyor. (2024'te yenilenen Pınarbaşı ve Hilvan'da kazanan aynı kaldığı için kayıtlar 31 Mart sonucunu göstermeye devam ediyor.)

**Düzeltilemeyen 2009 kayıtları** (`ilceGeneliSonuc` alanı ipucunda gösterilir, değerlere dokunulmadı):
- Akyazı, Koçarlı, Mecitözü, Şarkikaraağaç: 29 Mart'ta ilçe belediyesi seçimi iptal edildi ve 7 Haziran 2009'da yenilendi (bianet, "Local elections repeated in 30 places"). Açık veride ilçe merkezinin başkanlık sandıkları yok, kayıt yalnız beldelerin toplamı. Yenileme sonuçları depoda yok (`ek/yenileme_ara/2009yenileme_belediye_baskanligi.json` yalnız Ağın ve Kadışehri).
- Buldan, Malatya Merkez: ilçe merkezi biriminde başlık listesinde adı olmayan `parti21`–`parti26` sütunları 222 oy taşıyor ve parti + bağımsız toplamı geçerli oyu tutmuyor. Kayıt ilçe + belde toplamı olarak kaldı.

**Regresyon kontrolü:** `tests/validate_elections.py` "beldeli ilçede başkanlık sandığı = ilçe merkezi sandığı" (1.125 ilçe; eski veride 1.085 kayıt bu kontrolden kalıyordu). Belde başkanlık sonuçları ham dosyada var ama API belde adını vermediği için `ek/beldeler` dosyalarına eklenmedi.

## Tam liste (ilk tarama, 99 kayıt)

Oy ve fark ilk taramadaki (düzeltme öncesi) değerlerdir. Sınıf: a açıklanabilir, c oylar yanlış (düzeltildi), d belirlenemedi.

| Seçim | Düzey | Birim (plaka) | Kayıttaki kazanan | Oy | En çok oy | Oy | Fark | Sınıf | Karar | Eylem | Kaynak |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1950 | il | Mardin (47) | CHP | 44.882 | Bağımsız | 47.771 | 2.889 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1950 | il | Ordu (52) | CHP | 61.111 | DP | 61.184 | 73 | a | Kazanan en çok milletvekili çıkaran parti (aday bazlı seçim) | Not eklendi | YSK 1950–1977 il PDF (Ordu.pdf) |
| 1965 | il | Muş (49) | Bağımsız | 10.701 | Diğer | 12.027 | 1.326 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1969 | il | Siirt (56) | AP | 19.225 | Diğer | 19.274 | 49 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1969 | il | Tunceli (62) | AP | 9.972 | Diğer | 16.541 | 6.569 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1987 | il | Diyarbakır (21) | SHP | 76.074 | Diğer | 86.094 | 10.020 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1987 | il | Van (65) | ANAP | 43.927 | Diğer | 63.680 | 19.753 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1995 | il | Kırşehir (40) | ANAP | 24.351 | Diğer | 25.522 | 1.171 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1995 | il | Tunceli (62) | CHP | 8.434 | Diğer | 9.857 | 1.423 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1995 | il | Iğdır (76) | HADEP | 10.863 | Diğer | 11.286 | 423 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1999 | il | Erzincan (24) | MHP | 27.745 | Diğer | 28.575 | 830 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1999 | il | Hatay (31) | MHP | 128.387 | Diğer | 145.779 | 17.392 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1999 | il | Sivas (58) | FP | 88.827 | Diğer | 99.246 | 10.419 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1999 | il | Tunceli (62) | Bağımsız | 8.052 | Diğer | 9.466 | 1.414 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | YSK il sonuçları PDF (data/raw/ysk/1950-1977, 1983-2007); 1995/1999 için data/raw/legacy-preprocessed/1991_2023_tum_partiler_il_sonuclari.csv |
| 1955yerel | il | Bilecik (11) | DP | 7 | Bağımsız | 11 | 4 | a | Oylar meclis sandalyesi; başkanı meclis seçti (DP) | Mevcut not yeterli | Vikipedi il sayfası (kayıttaki not) |
| 1963yerel | il | İstanbul (34) | CHP | 112.686 | AP | 128.828 | 16.142 | a | Mazbata iptali; ikinci aday başkan | Mevcut not (il kopyasına da yazıldı) | Vikipedi il sayfası (kayıttaki not) |
| 1963yerel | ilçe | Bolvadin (3) | AP | 1.227 | Bağımsız | 1.900 | 673 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1963yerel | ilçe | Yusufeli (8) | AP | 187 | Bağımsız | 238 | 51 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1963yerel | ilçe | Tortum (25) | AP | 366 | Bağımsız | 371 | 5 | d | Vikipedi ile DİE kitabında AP ve bağımsız oyları yer değiştirmiş; tek bağımsız varsa kazanan bağımsız | Not belirsizliği yazacak şekilde düzeltildi; kazanan değiştirilmedi | Vikipedi il sayfası; DİE kitabı |
| 1963yerel | ilçe | Dörtyol (31) | AP | 1.000 | Bağımsız | 1.242 | 242 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1963yerel | ilçe | Devrek (67) | CHP | 887 | Bağımsız | 1.110 | 223 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1963yerel | ilçe | Bayramiç (17) | CHP | 467 | Bağımsız | 850 | 383 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1963yerel | ilçe | İstanbul (il merkezi belediyesi) (34) | CHP | 112.686 | AP | 128.828 | 16.142 | a | Mazbata iptali; ikinci aday başkan | Mevcut not (il kopyasına da yazıldı) | Vikipedi il sayfası (kayıttaki not) |
| 1968yerel | il | Afyonkarahisar (3) | AP | 2.765 | Bağımsız | 3.040 | 275 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | il | Bitlis (13) | AP | 2.210 | Bağımsız | 2.326 | 116 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | il | Çanakkale (17) | CHP | 1.863 | Bağımsız | 2.386 | 523 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | il | Giresun (28) | AP | 2.011 | CHP | 3.145 | 1.134 | a | Mazbata iptali; ikinci aday başkan | Mevcut not (il kopyasına da yazıldı) | Vikipedi il sayfası (kayıttaki not) |
| 1968yerel | il | Sinop (57) | CHP | 1.114 | Bağımsız | 1.138 | 24 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | il | Tokat (60) | CHP | 3.948 | AP | 7.011 | 3.063 | a | Mazbata iptali; ikinci aday başkan | Mevcut not (il kopyasına da yazıldı) | Vikipedi il sayfası (kayıttaki not) |
| 1968yerel | ilçe | Bahçe (1) | AP | 365 | Bağımsız | 380 | 15 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Yığılca (14) | CHP | 220 | Bağımsız | 255 | 35 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Senirkent (32) | AP | 1.686 | Bağımsız | 1.798 | 112 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Tosya (37) | AP | 1.747 | Bağımsız | 1.822 | 75 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Beyşehir (42) | AP | 729 | Bağımsız | 837 | 108 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Gölköy (52) | CHP | 517 | Bağımsız | 782 | 265 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Sapanca (54) | AP | 753 | Bağımsız | 1.195 | 442 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Merkez (3) | AP | 2.765 | Bağımsız | 3.040 | 275 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Merkez (13) | AP | 2.210 | Bağımsız | 2.326 | 116 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Merkez (17) | CHP | 1.863 | Bağımsız | 2.386 | 523 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Merkez (28) | AP | 2.011 | CHP | 3.145 | 1.134 | a | Mazbata iptali; ikinci aday başkan | Mevcut not (il kopyasına da yazıldı) | Vikipedi il sayfası (kayıttaki not) |
| 1968yerel | ilçe | Merkez (57) | CHP | 1.114 | Bağımsız | 1.138 | 24 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1968yerel | ilçe | Merkez (60) | CHP | 3.948 | AP | 7.011 | 3.063 | a | Mazbata iptali; ikinci aday başkan | Mevcut not (il kopyasına da yazıldı) | Vikipedi il sayfası (kayıttaki not) |
| 1973yerel | il | Bingöl (12) | CHP | 1.017 | Bağımsız | 2.078 | 1.061 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | il | Elazığ (23) | AP | 5.506 | Bağımsız | 11.556 | 6.050 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | il | Giresun (28) | CHP | 3.194 | Bağımsız | 3.399 | 205 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Çine (9) | AP | 1.409 | Bağımsız | 1.982 | 573 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Doğubayazıt (4) | CGP | 580 | Bağımsız | 1.122 | 542 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Tutak (4) | CGP | 277 | Bağımsız | 414 | 137 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | Mengen (14) | CHP | 199 | Bağımsız | 316 | 117 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | Karakoçan (23) | AP | 510 | Bağımsız | 628 | 118 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | İspir (25) | CHP | 314 | Bağımsız | 344 | 30 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | Pasinler (25) | AP | 827 | Bağımsız | 911 | 84 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Tekman (25) | CHP | 199 | Bağımsız | 211 | 12 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | Tortum (25) | AP | 456 | Bağımsız | 567 | 111 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Afşin (46) | AP | 961 | Bağımsız | 1.025 | 64 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Mesudiye (52) | CHP | 418 | Bağımsız | 509 | 91 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Kurtalan (56) | CGP | 480 | Bağımsız | 626 | 146 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Almus (60) | AP | 276 | Bağımsız | 360 | 84 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Nazımiye (62) | CHP | 172 | Bağımsız | 217 | 45 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Bozcaada (17) | AP | 273 | Bağımsız | 471 | 198 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | Eceabat (17) | CHP | 545 | Bağımsız | 1.077 | 532 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Ovacık (18) | AP | 128 | Bağımsız | 130 | 2 | a | 'Bağımsızlar' tüm bağımsızların toplamı; kazanan DİE kitabının kendi 'kazanan' sütunundan | Mevcut not yeterli | DİE 0015468 (baskanlik_birlestirme.json) |
| 1973yerel | ilçe | Bergama (35) | AP | 2.726 | Bağımsız | 2.829 | 103 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Merkez (12) | CHP | 1.017 | Bağımsız | 2.078 | 1.061 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Merkez (23) | AP | 5.506 | Bağımsız | 11.556 | 6.050 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1973yerel | ilçe | Merkez (28) | CHP | 3.194 | Bağımsız | 3.399 | 205 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1977yerel | ilçe | Haymana (6) | AP | 671 | Bağımsız | 802 | 131 | d | Vikipedi ile DİE kitabında AP ve bağımsız oyları yer değiştirmiş; tek bağımsız varsa kazanan bağımsız | Not belirsizliği yazacak şekilde düzeltildi; kazanan değiştirilmedi | Vikipedi il sayfası; DİE kitabı |
| 1977yerel | ilçe | Orhangazi (16) | AP | 1.474 | Bağımsız | 1.899 | 425 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1977yerel | ilçe | Bulanık (49) | CHP | 642 | Bağımsız | 975 | 333 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1977yerel | ilçe | Türkeli (57) | CHP | 290 | AP | 290 | 0 | a | Eşit oy; kura ile CHP | Not eklendi | Vikipedi il sayfası (Milliyet 13.12.1977 s.6) |
| 1977yerel | ilçe | Ovacık (62) | CHP | 238 | Bağımsız | 253 | 15 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1977yerel | ilçe | Bozova (63) | AP | 524 | Bağımsız | 587 | 63 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1977yerel | ilçe | İskilip (19) | AP | 1.537 | Bağımsız | 1.739 | 202 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 1994yerel | ilçe | Merkez (64) | DYP | 12.248 | Diğer | 12.654 | 406 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | DİE kitap katmanı (data/kaynaklar/tuik/yerel) |
| 1999yerel | il | Tunceli (62) | CHP | 2.513 | Diğer | 2.766 | 253 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | DİE kitap katmanı (data/kaynaklar/tuik/yerel) |
| 1999yerel | ilçe | Merkez (62) | CHP | 2.513 | Diğer | 2.766 | 253 | a | 'Diğer' birden çok partinin toplamı; tek başına en büyüğü kazanandan az | Not eklendi | DİE kitap katmanı (data/kaynaklar/tuik/yerel) |
| 2009yerel | ilçe | Sarayönü (42) | Bağımsız | 2.437 | AK Parti | 6.807 | 4.370 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık) |
| 2009yerel | ilçe | Derepazarı (53) | AK Parti | 1.119 | Bağımsız | 1.690 | 571 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları; YSK bağımsız aday sütunları (bagimsiz-aday.json) |
| 2009yerel | ilçe | Kaynaşlı (81) | AK Parti | 2.023 | Bağımsız | 2.078 | 55 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları; YSK bağımsız aday sütunları (bagimsiz-aday.json) |
| 2014yerel | ilçe | Hacıbektaş (50) | CHP | 945 | Bağımsız | 1.917 | 972 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları; YSK bağımsız aday sütunları (bagimsiz-aday.json) |
| 2019yerel | ilçe | Baykan (56) | HDP | 1.676 | AK Parti | 2.985 | 1.309 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://www.dailysabah.com/elections/march-31-2019-turkish-local-elections-results/siirt/baykan/district-local-election-results |
| 2019yerel | ilçe | Sarıveliler (70) | Bağımsız | 1.596 | AK Parti | 2.380 | 784 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://www.dailysabah.com/elections/march-31-2019-turkish-local-elections-results/karaman/sariveliler/district-local-election-results |
| 2024yerel | il | Hakkari (30) | DEM Parti | 14.708 | AK Parti | 15.087 | 379 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/hakkari-merkez-belediyesi-secim-sonuclari |
| 2024yerel | il | Kırklareli (39) | MHP | 21.348 | CHP | 23.719 | 2.371 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/kirklareli-merkez-belediyesi-secim-sonuclari |
| 2024yerel | il | Kütahya (43) | CHP | 40.763 | MHP | 40.790 | 27 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://www.turkiyegazetesi.com.tr/gundem/kutahyada-oylar-yeniden-sayildi-iste-sonuclar-1033080 |
| 2024yerel | ilçe | Gölbaşı (2) | CHP | 7.223 | AK Parti | 7.942 | 719 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/adiyaman-golbasi-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Çay (3) | İYİ Parti | 2.925 | AK Parti | 3.669 | 744 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/afyonkarahisar-cay-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Bulancak (28) | CHP | 13.238 | AK Parti | 14.196 | 958 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/giresun-bulancak-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Merkez (30) | DEM Parti | 14.708 | AK Parti | 15.087 | 379 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/hakkari-merkez-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Selçuk (35) | CHP | 8.427 | Bağımsız | 8.784 | 357 | a | 'Bağımsız' birden çok adayın toplamı; en çok oy alan tek bağımsız kazanandan az | Not eklendi ya da mevcut | Vikipedi il sayfası aday satırları |
| 2024yerel | ilçe | Merkez (39) | MHP | 21.348 | CHP | 23.719 | 2.371 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/kirklareli-merkez-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Merkez (43) | CHP | 40.763 | MHP | 40.790 | 27 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://www.turkiyegazetesi.com.tr/gundem/kutahyada-oylar-yeniden-sayildi-iste-sonuclar-1033080 |
| 2024yerel | ilçe | Ürgüp (50) | CHP | 5.345 | MHP | 6.077 | 732 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/nevsehir-urgup-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Ardeşen (53) | CHP | 5.505 | AK Parti | 5.884 | 379 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/rize-ardesen-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Reşadiye (60) | MHP | 5.795 | AK Parti | 7.290 | 1.495 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/tokat-resadiye-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Banaz (64) | Bağımsız | 3.355 | CHP | 3.521 | 166 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/usak-banaz-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Aydıncık (66) | AK Parti | 1.847 | MHP | 1.999 | 152 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/yozgat-aydincik-belediyesi-secim-sonuclari |
| 2024yerel | ilçe | Kilimli (67) | AK Parti | 6.341 | CHP | 6.437 | 96 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://www.dailysabah.com/elections/march-31-2024-turkish-local-elections-results/zonguldak/kilimli/district-local-election-results |
| 2024yerel | ilçe | Çınarcık (77) | CHP | 8.563 | AK Parti | 8.973 | 410 | c | Oylar ilçe merkezi + bağlı belde başkanlık yarışlarının toplamıydı; kazanan doğru | Oylar ilçe belediyesinin kendi sonucuyla değiştirildi (eski değer `kaynak.yskSatiri`) | Vikipedi il sayfası (YSK) + YSK belde ayrımlı meclis verisi (oy kullanan, seçmen, sandık); https://finans.mynet.com/yerel-secim-2024/yalova-cinarcik-belediyesi-secim-sonuclari |

## Açık işler (kullanıcı)

1. ~~**Beldesi olan öteki ilçeler (2009–2024)**~~ **Yapıldı (1 Kasım 2026):** "Kalıcı düzeltme" bölümü. Kalan: 2009 Akyazı, Koçarlı, Mecitözü, Şarkikaraağaç (7 Haziran 2009 yenileme sonuçları bir kaynaktan eklenebilir, `yenileme_2009.py` düzeni) ve Buldan, Malatya Merkez (YSK sütunları tutarsız; DİE/TÜİK 2009 kitabıyla çözülebilir).
2. ~~**Gizli kazanan hataları, 2009/2014/2019**~~ **Yapıldı:** YSK ilçe merkezi verisiyle 2009'da 131, 2014'te 28, 2019'da 26 ilçenin kazananı düzeltildi. Fark 10 oy ya da daha az olan altı kayıt itiraz sonrası kesin sonuçla karşılaştırılmadı.
3. ~~**2024 Hasköy, Güçlükonak, Güzelyurt**~~ **Yapıldı:** Hasköy MHP, Güçlükonak BBP; Güzelyurt 2 Haziran 2024 yenilemesini (AK Parti) gösteriyor.
4. **1963 Tortum, 1977 Haymana:** Kazananı belirlemek için ilçe seçim kurulu tutanağı ya da dönemin gazetesi gerekiyor.
5. **Kırklareli MP92 / MHP ayrımı:** YSK kesin sonuç ilanı GitHub Actions üzerinden (`sonuc.ysk.gov.tr` ya da açık veri kesin sonuç) teyit edilebilir.
6. **1994 Uşak Merkez:** `Diğer` DİE satırındaki partilere ayrılabilir (kitap satırı tutarlı). Bu iş kapsamında yapılmadı.

## Kontroller

1 Kasım 2026 (kalıcı düzeltme): `validate_public_data.py` (1.126 belgeli bulgu), `scripts/validate.py`, `tests/validate_elections.py` 22/22 (yeni belde sandığı kontrolüyle), `node --test tests/*.test.cjs` 14/14, `site/tests/loading.test.cjs` 30/30, `veri_denetimi.py --kontrol` geçti; denetim listesi yenilendi (değişiklik yok). `data/normalized` ve `data/raw/ysk/acikveri-belde-agrege` checksum'ları yenilendi.

Önceki iş (31 Ekim 2026):

`scripts/validate_public_data.py` (1.126 belgeli bulgu; 1999 Sivas parmak izi not eklendiği için yenilendi), `scripts/validate.py`, `tests/validate_elections.py` 19/19, `node --test tests/*.test.cjs` 14/14, `site/tests/loading.test.cjs` 30/30 ve `veri_denetimi.py --kontrol` geçti. Denetim listesi belgelenen komutla yenilendi: `KAZANAN_EN_COK_OY_DEGIL`'den 19 satır çıktı, yeni bulgu yok. `data/normalized` checksum'ları yenilendi.

## Web kaynakları

- Kırklareli: https://www.haberler.com/kirklareli-de-mhp-li-derya-bulut-belediye-baskani-17001956-haberi/ · https://www.ntv.com.tr/turkiye/kirklareli-belediye-baskani-derya-bulut-mazbatasini-aldi,KIaU0dgRCUe97yK-xTrbyA · https://www.cumhuriyet.com.tr/siyaset/kirklarelinde-chpnin-itirazini-iyi-parti-reddetti-mehmet-siyam-2193268 · https://finans.mynet.com/yerel-secim-2024/kirklareli-merkez-belediyesi-secim-sonuclari
- Kütahya: https://www.turkiyegazetesi.com.tr/gundem/kutahyada-oylar-yeniden-sayildi-iste-sonuclar-1033080 · https://medyascope.tv/2024/04/08/mhpnin-itiraziyla-gecersiz-oylarin-yeniden-sayildigi-kutahyada-chpli-baskan-mazbatasini-aldi/
- Hakkari: https://finans.mynet.com/yerel-secim-2024/hakkari-merkez-belediyesi-secim-sonuclari
- Ürgüp: https://www.ntv.com.tr/turkiye/ysk-siverek-halfeti-ve-urgupte-secim-yenilenmeyecek,tXG4C6T5m0W3gzxCWb-mjQ
- Uzunköprü: https://www.dha.com.tr/politika/iyi-partiden-istifa-eden-uzunkopru-belediye-baskani-martin-chpye-katildi-2507840
- Kayıt başına öteki AA bağlantıları ilgili kaydın `kaynak.ilceBelediyesi.ikinciKaynak` alanında.
- Güzelyurt yenilemesi: https://www.ntv.com.tr/turkiye/yenilenen-secimlerin-kesin-sonuclari-aciklandiak-parti-3-dem-parti-1-chp-2-mhp-1-belediye-kazandi,Jb0Dhi40fUm575vHcN9rhw
- 2009 yenilenen seçimler: https://bianet.org/haber/local-elections-repeated-in-30-places-115070
- Örnek karşılaştırma: https://www.e-sehir.com/secim/artvin-hopa-2014-belediye-secim-sonuclari.html · https://www.e-sehir.com/secim/zonguldak-zonguldak-merkez-2009-belediye-secim-sonuclari.html · https://www.e-sehir.com/secim/gumushane-gumushane-merkez-2009-belediye-secim-sonuclari.html
