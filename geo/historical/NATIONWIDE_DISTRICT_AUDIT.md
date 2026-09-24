# Türkiye Geneli İlçe Sınırı Denetimi (2026-09-24)

Her seçim yılı kendi dönemin gerçek ilçe sınırlarıyla gösterilmeli — bir modern ilçe o tarihte henüz kurulmamışsa, o alanın oyu kendi dönemindeki GERÇEK (eski) ilçesinin sınırında görünmeli, "veri yok" boşluğu olarak değil. Bu dosya, bu hedefe göre **tüm 81 ilin** denetim sonucunu ve hangilerinin düzeltildiğini/düzeltilemediğini kaydeder.

## Yöntem

- Karşılaştırma: her ilin **modern** (2023 genel seçimindeki) ilçe listesi vs. her ilçe-düzeyi veri içeren seçim yılında (genel: 1991,1995,1999,2002,2007; yerel: 1984,1989,1994,1999,2004 — ilçe kırılımı olmayan 1950-1983 dönemi hariç) o ilin kaydında GERÇEKTEN bulunan geomId'ler.
- `geo/historical/district_splits.json`'da zaten aktif kullanılan bir HIST-* sentetik poligon varsa, o poligonun "hideIds" listesindeki modern ilçeler **eksik SAYILMAZ** (zaten doğru gösteriliyor).
- **Önemli düzeltme**: yerel seçimlerde (1984-2004) büyükşehir OLMAYAN illerde "il" kaydının kendisi zaten merkez ilçenin sonucu (çift saymamak için `ilceler` listesine AYRICA eklenmiyor, bkz. `scripts/pipelines/yerel_1994_1999_2004/`). Bu yüzden ismi **tam olarak** "Merkez" olan bir ilçe, yerel seçimlerde eksik sayılmaz — bu bir veri boşluğu değil, kasıtlı bir tasarım.

## Özet: 19 il tam, 62 ilde gerçek eksik var (toplam 316 ilçe-yıl kaydı)

## ✅ Tam (19 il) — düzeltme gerekmiyor

Ardahan, Ağrı, Bartın, Batman, Bayburt, Düzce, Iğdır, Karabük, Karaman, Kilis, Kırklareli, Kırıkkale, Osmaniye, Siirt, Tunceli, Uşak, Yalova, Çanakkale, Şırnak.

## 🔧 Bu oturumda düzeltildi

**İstanbul (plaka 34) — kısmi.** Ataşehir/Beylikdüzü/Çekmeköy için ÖNCEKİ bir oturumda birincil kaynakla (5747 sayılı Kanun) tam doğrulanmış geometri vardı ama sadece 1994/1999/2004 yerel seçimlerine bağlanmıştı. Bu oturumda AYNI (değişmeyen) geometri, `affected_years` listesi genişletilerek genel 1991/1995/1999/2002/2007'ye de bağlandı — yeni araştırma yok, sadece zaten doğrulanmış düzeltmenin eksik kalan yıllara uygulanması. Kaynak: `geo/historical/district_mahalle_merges.yaml` (`atasehir` girişi) ve `apply_verified_district_merges.py`'deki `VERIFIED_MERGES` (Beylikdüzü/Çekmeköy). Doğrulama: 11/11 analitik test + 67/67 Playwright testi (yeni test: `scenario_istanbulGenelGecmisi`).

İstanbul'da hâlâ 22 ilçe eksik (aşağıdaki araştırılmış-ama-bloke ve hiç-araştırılmamış bölümlere bakın).

## 📋 Araştırıldı, birincil kaynakla KISMEN/TAMAMEN BLOKE (İstanbul, önceki oturum)

`geo/historical/district_mahalle_merges.yaml` içinde 5747 sayılı Kanun'un ekli listeleri 2 bağımsız birincil kaynaktan (mevzuat.gov.tr + TBMM arşivi) satır satır okunarak doğrulandı, ama şu 5 ilçe **tahminle doldurulmadı**, `research_needed`/`partial` olarak bırakıldı:

- **Arnavutköy** — kanunun 6 "İlk Kademe Belediyesi" kaynağının kendisi hangi eski ilçeye (Çatalca mı Gaziosmanpaşa mı) bağlı olduğu sadece çelişkili blog kaynaklarında var.
- **Başakşehir** — Küçükçekmece'nin 5 tam mahallesi dışındaki katkılar (Esenler'in aynı-isimli mahallesi, Bahçeşehir'in kısmi mahalleleri, Samlar köyünün baraj-gölü-sınırlı parçası) hepsi parça/belirsiz.
- **Esenyurt** — Kıraç kaynağındaki "Merkez"/"Namık Kemal" isimleri Esenyurt'un kendi listesiyle çakışıyor; kaynak İlk Kademe Belediyelerinin eski ilçesi sadece blog kaynaklı.
- **Sancaktepe** — "Abdurrahmangazi"/"Osmangazi" mahalleleri kanunda hem Kartal hem Ümraniye kaynaklı olarak İKİ AYRI listede geçiyor, güncel veride tek mahalle var — hangi yarısının nereden geldiği bilinmiyor.
- **Sultangazi** — Esenler-kaynaklı "Habipler" parseli parsel/kadastro sınırıyla tarif ediliyor (kalıcı engel); ayrıca kanunun "İsmet Paşa" mahallesi güncel veride hiç yok.

Tam detay ve kaynak linkleri için `district_mahalle_merges.yaml`'daki ilgili girişlere bakın.

Bunlardan Sultangazi'nin bir parçası (Esenler-kaynaklı "Habipler" parseli) **kalıcı olarak** çözülemez (bu depoda parsel/kadastro verisi yok). Diğerleri, daha güçlü bir birincil/resmi kaynak (belediye resmi tarihçe sayfası + ikinci bir bağımsız doğrulama) bulunursa ileride çözülebilir.

## ⚠️ Var olan (ama bu oturumda GÜVENLE genişletilemeyen) geometri — 13 il

Bu illerin her birinde ZATEN bir `HIST-<İl>-Merkez` sentetik poligonu var (`district_splits.json`), ve genel 1991-2007'de aktif kullanılıyor. Yerel 1994-2004'e de AYNI şekilde genişletmeyi denedim, ama kontrol ederken şunu gördüm: bu illerin yerel 1994-2004 verisinde, "gizlenmesi gereken" modern ilçelerin bir kısmının ZATEN KENDİ GERÇEK, DOĞRU satırı var (İstanbul'daki gibi tek bir eski satır değil) — örneğin Antalya'da hem Muratpaşa hem Kepez'in 1994yerel'de kendi ayrı, gerçek kaydı var. Bunu körü körüne "eski Merkez"e yeniden eşlemek YANLIŞ birleştirme/veri kaybı riski taşır. **Bu yüzden dokunmadım** — her biri kendi başına, hangi modern ilçenin GERÇEKTEN o yıl ayrı veri içerdiğini satır satır kontrol eden bir inceleme gerektiriyor (İstanbul'a yapılan türden, ama 13 kat).

- **Samsun** (plaka 55): 9 eksik ilçe → Asarcık, Atakum, Ayvacık, Canik, Ondokuzmayıs, Salıpazarı, Tekkeköy, Yakakent, İlkadım
- **Eskişehir** (plaka 26): 8 eksik ilçe → Alpu, Beylikova, Günyüzü, Han, Mihalgazi, Odunpazarı, Tepebaşı, İnönü
- **Antalya** (plaka 7): 8 eksik ilçe → Aksu, Demre, Döşemealtı, Kemer, Kepez, Konyaaltı, Muratpaşa, İbradı
- **Mersin** (plaka 33): 7 eksik ilçe → Akdeniz, Aydıncık, Bozyazı, Mezitli, Toroslar, Yenişehir, Çamlıyayla
- **Erzurum** (plaka 25): 7 eksik ilçe → Aziziye, Karaçoban, Köprüköy, Palandöken, Pazaryolu, Uzundere, Yakutiye
- **Van** (plaka 65): 6 eksik ilçe → Bahçesaray, Edremit, Saray, Tuşba, Çaldıran, İpekyolu
- **Diyarbakır** (plaka 21): 6 eksik ilçe → Bağlar, Eğil, Kayapınar, Kocaköy, Sur, Yenişehir
- **Kahramanmaraş** (plaka 46): 5 eksik ilçe → Dülkadiroğlu, Ekinözü, Nurhak, Onikişubat, Çağlayancerit
- **Manisa** (plaka 45): 5 eksik ilçe → Ahmetli, Gölmarmara, Köprübaşı, Yunusemre, Şehzadeler
- **Malatya** (plaka 44): 5 eksik ilçe → Battalgazi, Doğanyol, Kale, Kuluncak, Yazıhan
- **Şanlıurfa** (plaka 63): 4 eksik ilçe → Eyyubiye, Haliliye, Harran, Karaköprü
- **Balıkesir** (plaka 10): 4 eksik ilçe → Altıeylül, Gömeç, Karesi, Marmara
- **Artvin** (plaka 8): 1 eksik ilçe → Murgul

## ❓ Hiç araştırılmadı — birincil kaynak taraması yapılmadı

Aşağıdaki iller için henüz hiçbir kanun/tarihçe araştırması yapılmadı. Sayı, ilçe adı ve (mümkünse) kanun, ileride birincil kaynakla doğrulanıp `district_mahalle_merges.yaml`'a aynı formatta eklenmeli. Büyükten küçüğe, etki sırasına göre:

| İl | Eksik ilçe sayısı | Eksik ilçeler |
|---|---|---|
| Konya | 16 | Ahırlı, Akören, Altınekin, Derbent, Derebucak, Emirgazi, Güneysınır, Halkapınar, Hüyük, Karatay, Meram, Selçuklu, Taşkent, Tuzlukçu, Yalıhüyük, Çeltik |
| Sakarya | 10 | Adapazarı, Arifiye, Erenler, Ferizli, Karapürçek, Kocaali, Pamukova, Serdivan, Söğütlü, Taraklı |
| İzmir | 10 | Balçova, Bayraklı, Beydağ, Buca, Gaziemir, Güzelbahçe, Karabağlar, Menderes, Narlıdere, Çiğli |
| Ordu | 9 | Altınordu, Gülyalı, Gürgentepe, Kabadüz, Kabataş, Çamaş, Çatalpınar, Çaybaşı, İkizce |
| Denizli | 9 | Babadağ, Baklan, Bekilli, Beyağaç, Bozkurt, Honaz, Merkezefendi, Pamukkale, Serinhisar |
| Trabzon | 8 | Beşikdüzü, Dernekpazarı, Düzköy, Hayrat, Köprübaşı, Ortahisar, Çarşıbaşı, Şalpazarı |
| Kocaeli | 8 | Başiskele, Darıca, Derince, Dilovası, Kartepe, Körfez, Çayırova, İzmit |
| Kastamonu | 7 | Ağlı, Doğanyurt, Hanönü, Pınarbaşı, Seydiler, İhsangazi, Şenpazar |
| Hatay | 7 | Antakya, Arsuz, Belen, Defne, Erzin, Kumlu, Payaş |
| Bursa | 7 | Büyükorhan, Gürsu, Harmancık, Kestel, Nilüfer, Osmangazi, Yıldırım |
| Afyonkarahisar | 7 | Bayat, Başmakçı, Evciler, Hocalar, Kızılören, Çobanlar, İscehisar |
| Kütahya | 6 | Aslanapa, Dumlupınar, Hisarcık, Pazarlar, Çavdarhisar, Şaphane |
| Kayseri | 6 | Akkışla, Hacılar, Kocasinan, Melikgazi, Talas, Özvatan |
| Giresun | 6 | Doğankent, Güce, Piraziz, Yağlıdere, Çamoluk, Çanakçı |
| Aydın | 6 | Buharkent, Didim, Efeler, Karpuzlu, Köşk, İncirliova |
| Adana | 6 | Aladağ, Sarıçam, Seyhan, Yüreğir, Çukurova, İmamoğlu |
| Yozgat | 5 | Aydıncık, Kadışehri, Saraykent, Yenifakılı, Çandır |
| Sivas | 5 | Akıncılar, Altınyayla, Doğanşar, Gölova, Ulaş |
| Çorum | 5 | Boğazkale, Dodurga, Laçin, Oğuzlar, Uğurludağ |
| Burdur | 5 | Altınyayla, Karamanlı, Kemer, Çavdır, Çeltikçi |
| Ankara | 5 | Akyurt, Etimesgut, Evren, Kahramankazan, Pursaklar |
| Zonguldak | 4 | Alaplı, Gökçebey, Kilimli, Kozlu |
| Tokat | 4 | Başçiftlik, Pazar, Sulusaray, Yeşilyurt |
| Tekirdağ | 4 | Ergene, Kapaklı, Marmaraereğlisi, Süleymanpaşa |
| Rize | 4 | Derepazarı, Güneysu, Hemşin, İyidere |
| Muğla | 4 | Kavaklıdere, Menteşe, Ortaca, Seydikemer |
| Gaziantep | 4 | Karkamış, Nurdağı, Şahinbey, Şehitkamil |
| Çankırı | 4 | Atkaracalar, Bayramören, Korgun, Kızılırmak |
| Mardin | 3 | Artüklü, Dargeçit, Yeşilli |
| Kırşehir | 3 | Akpınar, Akçakent, Boztepe |
| Isparta | 3 | Aksu, Gönen, Yenişarbademli |
| Elazığ | 3 | Alacakaya, Arıcak, Kovancılar |
| Bingöl | 3 | Adaklı, Yayladere, Yedisu |
| Sinop | 2 | Dikmen, Saraydüzü |
| Niğde | 2 | Altunhisar, Çiftlik |
| Muş | 2 | Hasköy, Korkut |
| Gümüşhane | 2 | Köse, Kürtün |
| Erzincan | 2 | Otlukbeli, Üzümlü |
| Bolu | 2 | Dörtdivan, Yeniçağa |
| Bilecik | 2 | Yenipazar, İnhisar |
| Adıyaman | 2 | Sincik, Tut |
| Aksaray | 1 | Sultanhanı |
| Nevşehir | 1 | Acıgöl |
| Kars | 1 | Akyaka |
| Hakkari | 1 | Derecik |
| Edirne | 1 | Süloğlu |
| Bitlis | 1 | Güroymak |
| Amasya | 1 | Hamamözü |

**Not:** Bu illerin çoğu iki farklı dalgadan geliyor — (a) 2008 (5747 sayılı Kanun, orijinal 16 büyükşehir: Ankara/İzmir/Adana/Bursa/Gaziantep/Kayseri/Kocaeli/Konya/Sakarya + yukarıdaki 13'ün bir kısmı), (b) 2012 (6360 sayılı Kanun, 13 yeni büyükşehir: Aydın/Balıkesir/Denizli/Hatay/Kahramanmaraş/Malatya/Manisa/Mardin/Muğla/Tekirdağ/Trabzon/Şanlıurfa/Van), (c) büyükşehir OLMAYAN illerdeki 1987-1990'lar arası dağınık "yeni ilçe kurma" kanunları (her biri kendi ayrı, küçük kanunu). (a) ve (b) tek bir kanun metninden (annex listeleriyle) verimli işlenebilir; (c) ilçe başına ayrı araştırma gerektirir.

## Altyapı (bu oturumda genelleştirildi)

`scripts/pipelines/historical_geo/apply_verified_district_merges.py` ve `district_mahalle_merges.yaml` artık İstanbul'a özel değil — `plaka` alanına göre HERHANGİ bir il için `HIST-<İlAdı>-<İsim>` sentetik id üretebiliyor (`il_adi_ascii()` fonksiyonu). Yeni bir il için yapılacaklar: YAML'a `<il>_<yıl>:` grubu eklemek (`plaka` alanı zorunlu), `confidence: verified` girişleri script tarafından otomatik işlenir.
