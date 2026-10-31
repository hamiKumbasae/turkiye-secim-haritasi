# Harita geometri düzeltmesi — 31 Ekim 2026

Bu çalışma `docs/rapor/GEOMETRI_DENETIMI.md` (PR #19) denetiminin bulduğu mahalle geometri sorunlarını ve
Tillo/Aydınlar sorusunu ele alır. Önce/sonra sayıları aynı denetim betiğiyle (`scripts/rapor/geometri_denetimi.py`,
PR #19) `main` (1fdd3cb) ve bu dal üzerinde ölçüldü.

## 1. Kısa özet

| Ölçü | Önce | Sonra |
|---|---|---|
| Kendi ilçesinden 2 km'den uzak duran mahalle poligonu (çizilen) | 86 (84) | 58 (58) |
| Birlikte çizilen anlamlı TKGM × TKGM örtüşmesi | 2.653 çift, 2.739,5 km² | 10 çift, 41,1 km² |
| Birlikte çizilen anlamlı örtüşme, bütün kaynaklar | 4.390 çift, 3.484 km² | 1.739 çift, 779,8 km² |
| Birlikte çizilen, neredeyse aynı (IoU ≥ 0,95) çift | 14 | 1 |
| Aynı ilçede birebir aynı geometrili iki muhtarlık | 11 grup (+1 farklı ilçede) | 0 |
| Geçersiz mahalle poligonu | 1.002 | 0 (WGS84'te); denetimin eşit alanlı izdüşümünde 31 |
| Deliği dış halkayla aynı yönde yazılmış | 42 | 1 (sitede `evenodd` ile etkisiz) |
| Poligon olmayan (LineString) / alanı sıfır | 1 / 2 | 0 / 0 |
| Hiçbir seçimde çizilmeyen poligon | 1.971 | 15 (İstanbul, bilerek korunuyor) |
| Mahalle poligonu | 51.301 | 49.310 |
| `geo/normalized/mahalle_geo.json` | 90.372.502 bayt | 88.536.624 bayt |
| Yayındaki `geo/mahalle/` (TopoJSON) | 42.092.840 bayt | 40.781.521 bayt |
| Tek dosyalık `index.html` | 41.265.057 bayt | 40.750.245 bayt |
| 2023 genel: poligonu olan seçmen | 57.498.090 (%94,61) | 57.470.331 (%94,56) |

Tillo: bağlantı zaten doğru (bölüm 2). Kapsamdaki küçük düşüş, yanlış yerdeki sınırların kaldırılmasından
gelir: o muhtarlıklar artık boş kalıyor (kullanıcı kuralı: eşleşmeyen boş kalır, tahmin yok).

## 2. Tillo = Aydınlar (Siirt)

- **Kuruluş:** 3647 sayılı Kanun, RG 18.05.1990, sayı 20522 (`data/kaynaklar/resmi_gazete/ilce_kurulus/3647.json`).
  Merkez ilçenin Aydınlar bucağından, "Aydınlar" adıyla kuruldu; 5 birimin hepsi Merkez'den.
- **Ad değişikliği:** Eski adı Tillo, TBMM'nin 30.10.2013'te kabul ettiği kanunla geri verildi. Kaynaklar:
  [Hürriyet Daily News, 31.10.2013](https://www.hurriyetdailynews.com/amp/names-of-university-district-changed-as-promised-by-turkish-government-57135),
  [haberler.com, 30.10.2013](https://www.haberler.com/isim-degisiklikleri-meclis-ten-gecti-5239674-haberi/)
  (teklifin gerekçesi: 1990'da 3647 ile "Aydınlar" yapıldı, yerelde hiç benimsenmedi). Kanun numarası ve
  RG tarihi bu kaynaklarda yok; doğrulanamadı.
- **Kayıtlarda:** Tillo poligonu `TR-D-56-007`. 1991'den bu yana 25 seçim kaydının hepsinde kendi satırı var
  ve bu kimliğe bağlı: 1991–2007 genel ve 2007 referandumunda "Aydınlar", 1994–2004 yerelde
  "Aydınlar (Tillo)", 2009'dan sonra YSK adıyla "Tillo" (YSK kayıtları `duzeltmeKaynagi` ile sandık
  toplamından eklenmiş; `tests/data-integrity.test.cjs`). 1990 öncesi seçimlerde (1961–1989) alan Merkez ile
  birleşim poligonunda (`HISTK-56-005-5bd2a1`, `geo/historical/idari/ilce_eslesme/*.csv`: "Kuruluşta bütün
  birimleri Merkez ilçesinden").
- **Haritada:** 2023 genel seçimde Siirt il haritasında Tillo kendi sonucuyla boyanıyor (AK Parti, seçmen 2.692).
  `docs/rapor/poligon_durumu.csv`'de Tillo yalnız 1963 il genel meclisi, 1968 belediye ve il genel meclisi ile
  1977 il genel meclisi haritalarında gri; o haritalarda Merkez'in kendisi de verisiz.
- "Tillo'nun satırı yok" diyen eski notlar güncellendi: `HARITA_VE_EKSIK_VERI_RAPORU.md` (arşiv),
  `scripts/pipelines/election_import/PROVENANCE.md`, `geo/historical/idari/README.md`, `sources.yml`.
  `harita_durum_raporu.py` yeniden çalıştırıldı (çıktıdaki eklemeler 1963–1977 meclis seçimleri; daha önce
  yenilenmemişti).

Eşleştirme mekanizmasında değişiklik gerekmedi.

## 3. Yanlış yere çizilen mahalleler

**Kök neden.** TKGM ham verisinde bazı birimler başka bir yerin sınırını taşıyor (Mazgirt "Ayvatlı" Kayseri
Pınarbaşı'nda, Bigadiç "Camii" Eskişehir Çifteler'de, Odunpazarı "71 Evler" Tepebaşı'nda). Bursa belediye
dosyasında Harmancık ile Keles'in `ilce_adi` alanı yer değiştirmiş (Harmancık etiketli 42 sınırın 42'si adıyla
Keles muhtarlığı ve Keles'te; tersi 31/31). Eşleştirme adayın konumunu hiç sınamıyordu.

**Kural (eşleştirmede, `Konum`).** Alanının yarısından çoğu ilçe kapsamının dışında kalan aday alınmaz.
İlçe kapsamı: ilçe poligonu ve o ilçenin, kendisi ilçe bandında duran TKGM birimlerinin birleşimi, 2 km
tamponla. İlçe katmanı kaba sadeleştirildiği ve bazı yerlerde yanlış olduğu için (denetim 4.7) TKGM ikinci
bağımsız sınır olarak kullanılır. Başka bir ham kaynak (TKGM birimi, belediye sınırı) aynı adlı aynı şekli
(IoU ≥ 0,5) aynı ilçeye veriyorsa aday kapsam dışında olsa da alınır. Poligon olmayan ya da alanı sıfır aday
da alınmaz. Kural TKGM, OSM, belediye ve mevcut (ttezer/eski OSM) poligonlara uygulanır. Muhtarlık sıradaki
adaya geçer, yoksa boş kalır. Bursa takası `BELEDIYE_ILCE_DUZELT` ile düzeltildi.

**Sonuç.** Kural 61 adayı reddetti (58 TKGM ham birimi, 2 OSM, 1 belediye); 5 mevcut poligon kapsam dışında
olduğu hâlde doğrulandı (liste: `docs/rapor/mahalle_eslesme/konum_kurali.csv`). Denetimin 2 km listesindeki
çizilen kayıtlardan 27'si listeden çıktı:

- **Doğru ilçedeki poligonla değişti (7):** Keles Akçapınar ve Harmancık Akpınar (Bursa takası), Şahinbey
  Kale (OSM), Seben Haccağız (OSM), Alanya Basırlı (OSM), Alanya Hacımehmetli (TKGM), Mustafakemalpaşa
  Bostandere (aynı şekilli ttezer poligonu; belediye ile doğrulandı).
- **Boş kaldı (20):** Ayvatlı, Camii, Ekmekçi, Sofular, Yeşildere, 71 Evler, Okçular, Nevşehir Merkez Cumhuriyet,
  Oğuzeli Mimar Sinan, Kayıklı, Ardıçlıtaş, Ericek, Seydiköy, Kelekçi, Kasnakçımermer, İncehıdır, Yanıkses,
  Karlıca, Kocalar, Arabuk. Ayrıca poligon olmayan 3 kayıt (Aydınlık LineString, Alıçlıbucak ve Çatalçeşme
  alanı sıfır) boş kaldı.

**Kalan 58 kayıt** kurala uyuyor: TKGM'nin kendi birimleri o ilçenin alanını orada gösteriyor, yani hatalı olan
büyük olasılıkla ilçe katmanı (Alanya, Akseki, Eruh, Espiye, Kadınhanı ...). Bunlar denetimin 5. ve 6.
önerisiyle (ilçe katmanını yeniden üretmek) çözülür.

**Seçmen etkisi.** Boş kalan muhtarlıkların seçmeni (birleşen kayıtların seçmeni korunur):

| Seçim | Poligonu olan seçmen önce | Sonra | Fark |
|---|---|---|---|
| 2009 yerel | 34.738.126 (%87,45) | 34.726.879 (%87,42) | −11.247 |
| 2010 referandum | 44.016.252 (%88,93) | 44.001.778 (%88,90) | −14.474 |
| 2011 | 44.698.148 (%88,97) | 44.683.280 (%88,94) | −14.868 |
| 2014 CB | 49.884.312 (%94,26) | 49.866.521 (%94,23) | −17.791 |
| 2014 yerel | 46.066.274 (%94,19) | 46.051.843 (%94,16) | −14.431 |
| 2015 Haziran | 50.692.368 (%94,27) | 50.673.588 (%94,24) | −18.780 |
| 2015 Kasım | 51.001.566 (%94,30) | 50.982.386 (%94,26) | −19.180 |
| 2017 referandum | 52.228.512 (%94,26) | 52.207.717 (%94,22) | −20.795 |
| 2018 | 53.164.391 (%94,25) | 53.142.433 (%94,21) | −21.958 |
| 2018 CB | 53.164.391 (%94,25) | 53.142.433 (%94,21) | −21.958 |
| 2019 yerel | 50.358.314 (%94,58) | 50.339.553 (%94,54) | −18.761 |
| 2023 | 57.498.090 (%94,61) | 57.470.331 (%94,56) | −27.759 |
| 2023 CB 1. tur | 57.498.090 (%94,61) | 57.470.331 (%94,56) | −27.759 |
| 2023 CB 2. tur | 57.543.684 (%94,61) | 57.515.900 (%94,56) | −27.784 |
| 2024 yerel | 54.693.461 (%94,62) | 54.668.847 (%94,58) | −24.614 |

2023'teki 27.759 seçmenin 21.093'ü Odunpazarı "71 Evler"in seçmeni: TKGM birimi 0,09 km² ve 13 km ötede,
Tepebaşı'nda duruyordu.

## 4. TKGM × TKGM örtüşmesi

**Kural (son işlem, `tkgm_ortusmelerini_coz`).** Aynı ilçede en az bir seçimde birlikte çizilen ve anlamlı
örtüşen (≥ 1 ha ve küçüğün ≥ %1'i) iki TKGM biriminde örtüşen alan küçük birime kalır, büyükten çıkarılır.
İç içe birimde içteki (belde mahallesi, kadastro bölümü) korunur, kısmi örtüşmede küçük olan alır; eşit
alanda kimliği küçük olan. Her `uygula` çalışmasında ham TKGM sınırından yeniden hesaplanır. Bu yüzden betik
kaç kez çalıştırılırsa çalıştırılsın sonuç aynıdır (iki seçimle yeniden çalıştırıldı, dosyalar bayt bayt aynı).
Birlikte çizilmeyen birim kırpılmaz. Kırpılan birim tek başına çizildiği seçimde de kırpılmış görünür.
Örtüşen alan zaten öteki birimindir.

**Aynı sınır (5c).** Aynı seçimde aynı sınıra (IoU ≥ %95) düşen TKGM birimleri tek kayıtta toplanır; ad
"A + B" olur, oylar toplanır (seçmen kaybı yok). 2023'te 13 grup: Palu Kırkbulak + Köklüce, Hafik Kabalı +
Karlı, Osmaniye Rahime Hatun + Kazım Karabekir, Lüleburgaz Ahmetbey-Karşıyaka + Ahmetbey-Gündoğu ...
(`docs/rapor/mahalle_eslesme/<seçim>.csv`, durum "aynı sınırlı TKGM birimleri tek kayıtta toplandı").

**Sonuç.** 1.985 birim kırpıldı (2.637 çift); 37'sinin alanı yarının altına, 3'ünün %10'un altına indi (Emirdağ
Yeni Kacerli, Şuhut Hisar, Zara Şerefiye: birimin neredeyse tamamı küçük birimlerle kaplı). Kalan 10 çiftin
40,6 km²'si tek bir durum: Muş Merkez `kb206354-206355-206356` (KARAAĞAÇ KÖYÜ),
kendi üç bölümünün (Karaağaçlı-Bağlar/Kültür/Çubuklu) birleşimi ve üçüyle 3 seçimde birlikte çiziliyor. Kırpınca
hiçbir şey kalmayacağı için ham bırakıldı. Öteki 9 çift 0,01–0,24 km²'lik kenar artıkları: ham sınırda eşiğin
altındaydılar, komşu kırpılınca küçük birimin %1'ini geçtiler.

## 5. Geçersiz, boş, kullanılmayan poligonlar ve delikler

- `mahalle_geo.json` yazılırken (son işlem) geçersiz, poligon olmayan ya da deliği dış halkayla aynı yönde
  yazılmış geometri `make_valid` + 1e-4 ızgara (`shapely.set_precision`, 4 ondalık, geçerli çıktı) +
  `orient_polygons` (dış halka saat yönü tersi, delik saat yönü) ile onarılır; geçerli poligonlara dokunulmaz.
  Sadeleştirme ayarları değişmedi.
- Poligon olmayan ya da alanı sıfır aday eşleştirmede alınmaz (konum kuralı); 3 kayıt boş kaldı.
- Hiçbir seçimde kullanılmayan poligon silinir. 1.971 → 15. Kalan 15 İstanbul ttezer poligonu
  (`TR-D-34-*`) bilerek korundu: tarihsel İstanbul betikleri (`build_istanbul_*`, `build_ilce_bolusumu.py`
  `mg:` kimlikleri) bütün İstanbul mahalle poligonlarını okuyor. Silinenlerin hiçbiri mahalle/ek dosyalarında
  ya da sitede kullanılmıyordu (ek kayıtları ilçe düzeyinde).
- Site: `.geo-path { fill-rule: evenodd }` (il, ilçe, mahalle ve karşılaştırma haritası yolları). İlçe ve il
  katmanlarında üst üste binen çok parçalı poligon yok denecek kadar az (9 kayıtta < 0,02 km²); evenodd orada
  görünür bir delik açmıyor. Denetimdeki kalan 1 "aynı yönlü delik" (Demirci Durhasan) shapely'ye göre doğru
  yönde; denetimin neden farklı saydığı ayrıca incelenmedi. Evenodd ile fark etmez.
- Denetimin kalan 31 "geçersiz" mahallesi WGS84'te geçerli (`tests/validate_elections.py` denetliyor). Eşit
  alanlı izdüşüme çevrilince 4 ondalıklı köşeler arasında kendini kesme oluşuyor; site WGS84 koordinatı çiziyor.

## 6. Doğrulama

| Kontrol | Sonuç |
|---|---|
| `scripts/validate.py` | geçti |
| `scripts/validate_public_data.py` | geçti |
| `tests/validate_elections.py` | 21/21 (yeni: eşleştirme geometri kuralları yapay poligonlarla; `mahalle_geo.json` geçerlilik/delik/kullanılmayan) |
| `node --test tests/*.test.cjs` (`site/build.py` sonrası) | 14/14 |
| `cd site && node tests/loading.test.cjs` | 30/30 |
| `veri_denetimi.py --kontrol` | yeni bulgu yok (liste yenilendi: kayıt anahtarı/adı değişen Alanya Basırlı, birleşen Palu ve Derik kayıtlarındaki YSK kaynaklı katılım/geçerli oy bulguları yeni kimlikle) |
| Tekrarlanabilirlik | `tkgm_muhtarlik_esle.py uygula 2023 2024yerel` ikinci kez: bütün dosyalar aynı |

Ekran görüntüleri (Playwright, önce/sonra; bu dalda değil, oturum çalışma klasöründe): Tillo 2023 (Siirt),
Bigadiç 2023 (Camii'nin Eskişehir'e uzanan sınırı kalkınca ilçe haritası ilçeye yakınlaşıyor), Yakutiye 2023
(Umudum'un örttüğü mahalleler görünür oldu), Mahmudiye (Eskişehir) Güllüce deliği (dolgu oranı 0,478 → 0,441; delik boş).

`requirements.txt`: `shapely>=2.1` (`orient_polygons`), `pyproj>=3.6` (yeni test ve eşleştirme betiği CI'da
çalışsın diye).

## 7. Açık işler

- Kalan 58 uzak kayıt ve ilçe sınırının 2 km dışına taşan alan (10.929 km²): ilçe katmanını ham kaynaktan,
  topolojiyi koruyarak yeniden üretmek (denetim önerisi 5–6).
- Kaynakların çeliştiği yerler: Düzköy "Yerlice" (TKGM) Maçka'daki ttezer "Yerlice" ile aynı şekil; Oğuzeli
  "Şahinbey" (TKGM) Şahinbey ilçesindeki "Şahinbey" ile %71 örtüşüyor. Kural ikisini de tutuyor (TKGM'nin ilçe
  kapsamında); yerinde doğrulanmadı.
- Muş Merkez Karaağaç köyü ile bölümleri (bölüm 4).
- Boş kalan 20 muhtarlık için doğru ilçede sınır bulunamadı; yeni bir kaynak (TKGM güncellemesi, belediye
  verisi) gelirse eşleştirme yeniden çalıştırılınca kendiliğinden alınır.
