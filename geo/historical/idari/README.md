# Tarihsel idari coğrafya katmanı

Amaç: her seçim tarihinde hangi il ve ilçelerin var olduğunu, ilçelerin o tarihte
hangi ile bağlı olduğunu ve bugünkü ilçe geometrilerinin geçmişte hangi eski
ilçelere ait olduğunu bilmek. Böylece eski seçimler bugünkü sınırlarla değil,
kendi dönemlerinin idari yapısıyla çizilebilir.

Örnek: Köprübaşı (Trabzon) 20.05.1990'da 3644 sayılı Kanunla kuruldu. 1990 öncesi
seçimlerde onun alanının oyu o dönem bağlı olduğu ilçenin (büyük olasılıkla
Sürmene) sonucunda. Bu durumda doğru harita, Sürmene'nin oyunu Sürmene + Köprübaşı
alanına boyamaktır. Bu katman, bunun için gereken kaydı tutar.

## Dosyalar

| Dosya | Nasıl oluşur | İçerik |
|---|---|---|
| `administrative_events.json` | Üretilir (`build_idari_katman.py`) + `elle_olaylar.json` | Her idari olay bir kayıt: kuruluş, merkez ilçe dönüşümü, ad değişikliği, il değişikliği, kaldırılma, yeniden kuruluş |
| `district_lineage.json` | Üretilir | Her güncel ilçe (`geomId`) için kuruluş, ilk seçim, adlar, il geçmişi, önceki birimler, soy durumu |
| `election_admin_snapshots.json` | Üretilir, **elle düzenlenmez** | Her seçim tarihinde iller, il sınır dosyası, ilçeler, henüz ayrı olmayan ilçeler ve geometri kuralları |
| `elle_olaylar.json` | Elle, kaynaklı | Kuruluş listesinde olmayan olaylar (şimdilik Kırşehir 1954–1957) |
| `faz1_rapor.json` | Üretilir | Tutarlılık denetimi |
| `ilce_eslesme/<seçim>.csv` | Üretilir (`build_ilce_secim.py <seçim> tablo`) | Bugünkü ilçe → o seçimdeki ilçe eşleme tablosu |
| `ilce_eslesme/<seçim>.json` | Üretilir (`build_ilce_secim.py <seçim> uygula`) | Birleşim poligonları, belirsizler, geometrisiz satırlar |

Üretim:

```bash
.venv/bin/python scripts/pipelines/historical_geo/extract_icisleri_kurulus.py   # PDF -> kaynak katmanı
python3 scripts/pipelines/historical_geo/build_idari_katman.py                  # bu klasör
```

## Kurallar

- **Tahmin yok.** Bir ilçenin hangi eski ilçe/bucak/köylerden ayrıldığı kaynakta
  yoksa `lineageStatus: "unresolved"`; modern sınır geçmişe taşınmaz,
  snapshot'ta `geometryRule: "unresolved"`.
- **Kanun tarihi seçim etkisi değildir.** 3392 sayılı Kanunla 04.07.1987'de kurulan
  97 ilçe (ve 3391/3398/3399 ile Bursa, Konya, Gaziantep'in yeni merkez ilçeleri)
  29.11.1987 genel seçimine ayrı girmedi. Bu yüzden her ilçede hem kuruluş
  (`kurulus`) hem ilçe düzeyli seçimde ayrı olarak ilk görüldüğü seçim
  (`ilkSecim`) tutulur; aradaki seçimler `kurulduAmaSecimeAyriGirmedi`'de.
- **Yerel seçim satırları ilçe değil belediyedir.** Büyükşehir alt kademe
  belediyeleri (ör. 1994'te Kepez, Konyaaltı) ilçe olmadan önce de satır olarak
  var. İlçe varlığına kanıt yalnızca genel seçim, referandum ve cumhurbaşkanlığı
  seçimlerinden alınır.
- **Eşleşme `geomId` ile.** Ad değişikliği ayrı olaydır; yazım farkları
  (`Samandağ`/`Samandağı`, `Merkez`/`Aydın merkez`, `Sincanlı (Sinanpaşa)`) ad
  değişikliği sayılmaz.

## Kimlikler

- Güncel ilçe: `TR-D-PP-NNN` (`geo/normalized/turkiye_ilce_sinirlari.geojson`).
- Tarihsel birleşim: `HIST-İl-İlçe[dönem]` (`../turkiye_ilce_sinirlari_hist_splits.geojson`,
  `../district_splits.json`).
- İl: plaka (o tarihteki).

## `lineageStatus`

| Değer | Anlamı |
|---|---|
| `1950_oncesi_mevcut` | İlçe 14.05.1950'den önce kurulmuş. Sınırı sonradan ayrılan ilçelerle küçülmüş olabilir; bu, ayrılan ilçelerin soy kaydıyla çözülür (Faz 2). |
| `repo_dogrulanmis` | Repoda kaynakla doğrulanmış bir `HIST-*` birleşiminin parçası (`district_splits.json`). |
| `merkez_ilce` | Sonradan il olan bir yerin merkez ilçesi; ilçe olarak kuruluş tarihi kaynakta yok (il olmadan önce başka ile bağlı ilçeydi). |
| `kanun_tek_kaynak` | Kuruluş kanununun ek listesine göre bütün birimleri (köy/bucak/mahalle) tek bir eski ilçeden geldi. Kuruluş öncesi seçimlerde alanı o ilçeye katılır (`geometryRule: merge_into:<geomId>`). |
| `kanun_cok_kaynak` | Ek listeye göre birden çok eski ilçeden birim aldı. Eski ilçeler ve birim sayıları kayıtlı; köy düzeyinde sınır çözülmediği için `geometryRule: unresolved_multi_parent`. |
| `kanun_dogrulanmadi` | Kanun listesi okundu ama güven orta (7033: zayıf tarama, blok düzeyi); soy kayıtlı, geometri kuralı `unresolved`. |
| `kanun_kaynak_yazilmamis` | Kanun okundu ama ek listede birimlerin eski ilçesi yazılmamış (1055 Abana/Bozkurt, 3949 Esenler); geometri `unresolved`. |
| `unresolved` | 1950 sonrası kurulmuş, soy bilgisi henüz kaynaklanmadı. |

## Durum (Faz 1, 2026-09-25)

- 81 il ve 973 güncel ilçenin tamamı İçişleri Bakanlığı listesine bağlandı (resmî,
  `data/raw/icisleri/il-ilce-kurulus-2018/`).
- Soy (Faz 1 sonunda): 436 ilçe 1950 öncesi, 78 ilçe repoda doğrulanmış birleşim,
  24 merkez ilçe, 435 ilçe `unresolved` (Faz 2 ilerlemesi aşağıda).
- 108 ilçe kanunla kurulduktan sonra en az bir seçime ayrı girmedi.
- 11 merkez ilçe dönüşümü (2008/2012 büyükşehir: Aydın Merkez → Efeler vb.).
- 15 ad değişikliği, 51 il değişikliği seçim verisinden (tarih aralığıyla);
  il değişikliklerinin çoğunun tarihi yeni ilin kuruluşundan kesin.
- Kırşehir: 1923 öncesi il, 30.06.1954'te kaldırıldı (6429), 12.06.1957'de
  yeniden il (7001). Bu yüzden 1955 yerel seçim tarihinde 66 il var; veride 64.

## Durum (Faz 2 — kanun ek listeleri)

| Kanun | Tarih | İlçe | Tek kaynak | Çok kaynak | Kaynak |
|---|---|---|---|---|---|
| 3644 | 20.05.1990 | 130 | 107 | 23 | RG 20523 ek (1)–(130) sayılı listeler, 2.056 satır |
| 3392 | 04.07.1987 | 103 | 84 | 15 (+4 kaynağı yazılmamış) | RG 19507 ek (1)–(103) sayılı listeler, 2.141 satır |
| 2963 | 30.11.1983 | 6 | 6 | 0 | RG 18237 (2. mükerrer) ek (1)–(6) sayılı listeler, 104 satır; Madde 2: Ankara Merkez İlçesi kaldırıldı → Altındağ |
| KHK 550 | 06.06.1995 | 8 | 8 | 0 | RG 22305 ek (1)–(8) sayılı listeler, 130 satır; Karabük, Kilis, Yalova illeri kuruldu |
| 3578 | 21.06.1989 | 5 | 5 | 0 | RG 20202 ek (1)–(5) sayılı listeler, 99 satır; Kırıkkale, Aksaray, Bayburt, Karaman illeri kuruldu |
| 3647 | 18.05.1990 | 5 | 5 | 0 | RG 20522 (mükerrer) ek (1)–(5) sayılı listeler, 72 satır; Batman ve Şırnak illeri kuruldu |
| 4200 | 28.10.1996 | 3 | 2 | 1 | RG 22801 ek (1)–(3) sayılı listeler, 35 satır; Osmaniye ili kuruldu |
| 2585 | 21.01.1982 | 2 | 1 | 1 | RG 17581 s. 4 cetvelleri, 21 satır (Ceylanpınar ← Viranşehir; Aliağa ← Menemen, Bergama, Foça) |
| 3949 | 29.12.1993 | 3 | 1 | — (2 kaynağı yazılmamış) | RG 21803 ek (1)–(4) listeler; Gümüşova ← Cumaova; Güzelbahçe ve Esenler mahalle kaynağı yazılmamış; Narlıbahçe → Narlıdere, Cumaova → Cumayeri |
| 1055 | 17.07.1968 | 2 | — | — (kaynak sütunu yok) | RG 12952 s. 5; Abana ve Bozkurt (merkez Pazaryeri); köylerin eski ilçesi yazılmamış |
| KHK 584 | 09.12.1999 | 2 | 2 | 0 | RG 23901 ek (1)–(2) listeler, 25 satır; Kaynaşlı ← Düzce, Derince ← Kocaeli Merkez; Düzce ili |
| 3806 | 03.06.1992 | 12 (+Sultanbeyli listesiz) | 2 | — | RG 21247 (mükerrer); Damal ← Hanak, Karakoyunlu ← Iğdır; İstanbul/İzmir mahalle listelerinde eski ilçe yazılmamış (repoda doğrulanmış); Ardahan ve Iğdır illeri |
| 309 | 04.09.1963 | 1 | 1 | 0 | RG 11496 (1) sayılı cetvel, 10 satır elle aktarıldı; Gaziosmanpaşa ← Eyüp |
| 5747 | 22.03.2008 | 43 | 29 (10'u yeni; 19'u repoda doğrulanmış ya da merkez) | 13 | RG 26824 (mükerrer) asıl metni + mevzuat metni, (1)–(41) sayılı listeler ve Madde 1 bentleri, 936 satır; belde → ilçe DİE 2004 |
| 6360 | 06.12.2012 | 26 (+Altınordu 6447 ile) | 25 (7'si yeni ve haritaya yansıdı; 7'si Merkez halefi, 11'i repoda doğrulanmış) | 1 | RG 28489 asıl metni + mevzuat metni, Madde 2 fıkraları ve (1)–(21) listeler, 1.109 satır; 720 köy/belediye satırı RG aslında birebir bulundu |
| 7033 | 01.09.1957–01.04.1960 | 78 | — (orta güven, geometriye çevrilmedi) | — | RG 9644 cetvelleri; 50/77 blok okunabildi |

- 3644'ün 130 ilçesinin tamamı İçişleri listesinde de 3644 ile kayıtlı; ek listelerde
  sıra numaraları kesintisiz (düşen satır yok).
- Örnek: Köprübaşı (Trabzon) — (120) sayılı listenin 11 köyünün 11'i Sürmene'nin
  Köprübaşı bucağından → 1990 öncesi seçimlerde `merge_into:TR-D-61-014` (Sürmene).
- İl dışından birim alanlar: Yedisu (Bingöl) ← Pülümür (Tunceli), İkizce (Ordu) ←
  Terme (Samsun), Kürtün (Gümüşhane) ← Tirebolu (Giresun), Yenihisar/Didim (Aydın) ←
  Milas (Muğla), Karakeçili (Kırıkkale) ← Bala (Ankara).
- Kanun bentlerindeki 14 ek hüküm (mevcut ilçeler arası köy/belde nakli, il
  değişikliği) `boundary_adjustment` olayı olarak kayıtlı; köy düzeyinde geometrisi
  çözülmedi.
- 3392: 1987 genel seçiminde ayrı birim olmayan ilçelerin çoğu bu kanunla kuruldu
  (ör. Aladağ ← Karaisalı, Kahramankazan ← Yenimahalle, Demre ← Kaş). İstanbul'un
  1987 ilçelerinin mahalle listelerinde eski ilçe yazılmamış; tahmin edilmedi.
  Pendik, Küçükçekmece, Büyükçekmece, Ümraniye ve Konak'ın kuruluş kaydı
  `district_lineage.json` → `historicalUnits` altında (sonradan bölündükleri için
  kuruluş sınırları repodaki `HIST-*` poligonlarında).
- Eksik satırlı (OCR) listeler tek kaynaklı sayılmaz (`eksikSira`).
- 7033 (1957): etkisi yalnız 1950–1957 seçimleri (ilçe verisi yok ya da yalnız yerel
  kazanan); orta güvenle kayıtlı, geometriye çevrilmedi. Aynı durum 6068/6324/6325
  (1953–1954) için de geçerli; bunlar sona bırakıldı.
- 2963 (1983): Ankara'nın 1961–1983 "Merkez" satırı, 30.11.1983'te kaldırılıp alanı
  Altındağ'a katılan ayrı bir ilçedir (madde 2); sınırı kaynakta yok, haritada hâlâ
  çizilemez ama kaydı artık kaynaklı. Keçiören ← Altındağ, Mamak ve Gölbaşı ← Çankaya,
  Sincan ← Yenimahalle.
- 5747 (2008): ek listeler birimleri eski ilçeye değil bağlı oldukları belediyeye göre
  gruplar ("Taşoluk İlk Kademe Belediyesine bağlı"); yalnız köy cetvellerinde İLÇESİ
  sütunu var. İlk kademe belediyesinin ilçesi DİE 2004 Tablo 9'dan (`extract_5747.py`;
  il satırının altında ilk ilçeden önce gelen beldeler = Merkez ilçe). Yeni tek kaynaklı
  (haritaya yansıyan): Sarıçam ← Yüreğir; Döşemealtı ← Antalya Merkez; Başiskele, Kartepe
  ← Kocaeli Merkez; Çayırova, Darıca, Dilovası ← Gebze; Arifiye, Erenler, Serdivan ←
  Sakarya Merkez. Çok kaynaklı (çizilmez): Çukurova (Seyhan, Karaisalı), Pursaklar
  (Keçiören, Altındağ, Çubuk; listesiz, bent metninden), Aksu (Merkez, Serik), Konyaaltı
  (Merkez, Kemer: Beldibi), Arnavutköy (Gaziosmanpaşa, Çatalca, Küçükçekmece), Başakşehir,
  Esenyurt (Büyükçekmece, Avcılar), Sultangazi (Gaziosmanpaşa, Eyüp, Esenler). Madde 2
  (Eminönü → Fatih, Ilıca → Aziziye, mahalle kısmı nakilleri) `digerHukumler`'de.
  Mevzuat metni 6552 (2014) değişikliklerini içerir; RG aslıyla fark `rgFarki`
  (yalnız dizgi: "Yüreği" = RG'de Yüreğir, boş bucak hücresi).
- 6360 (2012): cetvellerde köy ve belediyelerin ilçesi yazılı; mahalle grubu "X
  Belediyesine bağlı" (X il merkezi belediyesi = Merkez ilçe, ilçe belediyesi = o ilçe);
  merkez olan belde belediyesinin ilçesi DİE 2004 (`extract_6360.py`). Yeni tek kaynaklı:
  Arsuz ← İskenderun, Payas ← Dörtyol, Seydikemer ← Fethiye, Kapaklı ← Çerkezköy,
  Ergene ← Çorlu, Kilimli ve Kozlu ← Zonguldak Merkez. Çok kaynaklı: Defne (Merkez,
  Samandağ). Efeler, Menteşe, Artuklu, Süleymanpaşa, Ortahisar, Antakya, Merkezefendi: eski Merkez ilçenin
  halefi, önceki seçimlerde aynı geomId → `merkez_ilce` (5747'de İzmit, Adapazarı da).
  2011 genel seçim verisi 2012 sonrası ilçelere göre toplanmış; eski ilçe adları 2007
  satırlarıyla eşlendi. Madde 2'nin nakil/ad değişikliği fıkraları `digerHukumler`'de.
- Öncelik (1961 sonrası seçimleri etkileyen, çözülmemiş): 6447 (2013: Altınordu),
  7148 (2018: Derecik), KHK 694 (2017: Sultanhanı, Kemalpaşa).

## Haritaya yansıtma (Faz 4a — `apply_idari_merges.py`, 2026-09-26)

`lineageStatus == kanun_tek_kaynak` olan 218 ilçe, kurulmadan önceki (ya da kurulup
seçime henüz ayrı girmediği) seçimlerde eski ilçesinin satırına katılır: satırın
`geomId`'si `HISTK-<taban>-<sha6>` sentetiğine çevrilir (taban modern ya da repodaki
`HIST-*` poligonu + katılan modern ilçeler). Oy/katılım değerleri değişmez. Örnek:
Köprübaşı (3644, 20.05.1990) 1950yerel–1989yerel arası Sürmene satırında
(`HISTK-61-014-*`). Başka bir güncel ile geçmiş ilçeler de katılır (Elbeyli→Oğuzeli,
Armutlu→Gemlik, Ağaçören/Sarıyahşi→Şereflikoçhisar vb.); ön yüz poligonu geomId'den
çizdiği için doğru ilde görünür.

- Sonuç: 185 sentetik, 2911 satır, 23 seçim (`merge_plan.json` → `ozet`).
- Katılmayanlar: `kanun_cok_kaynak`, `kanun_dogrulanmadi` (7033), `unresolved`.
- `hedefBulunamadi` (294): hepsi yerel seçimler; eski ilçe o seçimde ayrı belediye
  satırı değil (çoğu il merkezi, il satırında). Açık karar.
- Kanunla kurulup sonradan bölünmüş tek kaynaklı tarihsel birimler (`historicalUnits`)
  modern parçalarına açılarak aynı kuralla katılır: Büyükçekmece (3392, 1987; 14 köyün
  14'ü Çatalca'dan) → 1961–1987 Çatalca = Çatalca + Büyükçekmece + Beylikdüzü. Ebeveyninin
  tarihsel poligonu içinde kalan birim (İzmir Konak1991 ⊂ Konak84) atlanır.
- `harita_notlari.json`: her seçimde "veri yok" kalan ve o tarihte henüz ayrı ilçe
  olmayan modern poligonlar (seçim → geomId → 0 = kurulmamış, 1 = kurulmuş ama seçime ayrı
  girmemiş) ve nedenleri (kanun, tarih, kaynak ilçeler). Ön yüz bunları taralı çizer ve
  ipucunda nedenini yazar (ör. 1995 Arnavutköy: Gaziosmanpaşa, Çatalca ve Küçükçekmece
  arasında bölünmüş). Renk vermez; tahmin yapılmaz.
- Betik idempotent: önceki `HISTK-*` satırları önce tabanına döndürülür.
  `build_idari_katman.py` HISTK satırlarını tabanıyla okur ve `district_splits.json`'daki
  HISTK kayıtlarını yok sayar (bu katmandan üretildikleri için geri beslenmez).
  Yeni kanun eklendikten sonra `build_idari_katman.py` → `apply_idari_merges.py` →
  `scripts/build.py` → checksum yenile.

## Çok kaynaklı ilçeler: Merkez çoğunluğu (2026-09-27)

Birden çok eski ilçeden kurulan ilçelerde (`kanun_cok_kaynak`):

- Birimlerinin en az %70'i ilin Merkez ilçesinden (ya da adı değişen halefinden) geliyorsa,
  kurulmadan önceki seçimlerde bütünüyle Merkez'e katılır: Aksu, Konyaaltı (Antalya), Defne
  (Hatay), Eğil, Kocaköy (Diyarbakır), Çeltikçi, Gönen (Isparta, Burdur), İhsangazi, Yeşilli,
  Edremit (Van), Gülağaç, Demirözü, Hasanbeyli. Küçük diğer kaynaklar ipucunda yazılır.
- Diğerleri (ör. Arnavutköy, Esenyurt, Kovancılar) bütün poligon hâlinde taralı çizilir;
  ipucu kanunu, tarihi ve kaynak ilçeleri yazar.
- `harita_notlari.json` → `birlesimler`: her tarihsel poligonun bugünkü sınırlarla
  kapsadığı ilçeler; ön yüz bunu ipucunda gösterir ("Bugünkü sınırlarla: ...").

Mahalle düzeyinde paylaştırma denendi ve arşivlendi: `arsiv/mahalle-bolusumu/README.md`
(kaynaklar, mantık, sonuçlar; git etiketi `arsiv/mahalle-bolusumu`).

Kaynağı yazılmamış 1987 birimleri için `sayim_kaniti.json` (elle, DİE 1960/1985/1990 sayım
kitaplarındaki köy/belde bağlılığı): Küçükçekmece ← Bakırköy, Pendik ← Kartal.

## Yerel seçimlerde il merkezi (2026-09-27, `ekle_il_merkezi_satirlari.py`)

Yerel seçim satırları belediyedir; 1963–1989'da il merkezi belediyesinin sonucu il satırında
durur ve Merkez ilçenin ayrı satırı yoktu (haritada merkez ilçe boş kalıyordu). Betik her
yerel seçimi aynı döneme en yakın genel seçimle eşleştirir (1963↔1961, 1968↔1969, 1973↔1973,
1977↔1977, 1984↔1983, 1989↔1987) ve il satırının sonucunu birebir kopyalayan bir Merkez satırı
ekler (`ilMerkeziBelediyesi: true`); geometrisi genel seçimdeki Merkez poligonudur, Merkez'den
sonradan ayrılan ilçeler soy kuralıyla katılır.

- İl merkezi belediyesinin birden çok ilçeyi kapsadığı 1963–1977 İstanbul (14 merkez ilçe),
  Ankara (Merkez, Altındağ, Çankaya, Yenimahalle) ve İzmir (Merkez, Karşıyaka): tek birleşik
  şehir poligonu (`HISTY-*`). Kendi satırı olmayan ve dört yanı şehirle çevrili ilçe şehre
  katılır (1963–1977 Kağıthane).
- Büyükşehir yıllarında il satırı büyükşehir başkanının sonucudur; Merkez satırı üretilmez
  (1984: İstanbul, Ankara, İzmir; 1989: + Adana, Bursa, Gaziantep, Konya, Kayseri).
- Merkez içindeki belde kendi satırıyla varsa Merkez onu dışarıda bırakır (1989 Samsun
  Tekkeköy). Merkez'in bütün alanı başka satıra bağlıysa eklenmez (1989 Malatya: Battalgazi
  beldesi satırı bugünkü Battalgazi ilçesine bağlı).
- Sonuç: 390 satır (1963–1977 her yıl 67, 1984 64, 1989 58).

## İstanbul 1992–2008 ilçe sınırları (2026-09-29, `build_istanbul_1992_2008.py`)

3806 (1992) ile 5747 (2008) arasında İstanbul'un 32 ilçesi vardı; bu sınırlar 1994/1999/2004
yerel, 1995/1999/2002/2007 genel seçimleri ve 2007 referandumunda geçerli. Önceki durumda
2008'de birden çok eski ilçeden kurulan dört ilçe (Arnavutköy, Başakşehir, Esenyurt,
Sultangazi) bu seçimlerde taranıyordu; mahalle düzeyinde bölüşüm denemesi de
(`arsiv/mahalle-bolusumu/`) ilçelerin içinde taralı parçalar bıraktığı için kaldırılmıştı.

Şimdi bütün il boşluksuz kuruluyor:

- 2008 ilçelerinin her bugünkü mahallesi, 5747'nin ek listesine göre (belde ilçesi DİE 2004
  Tablo 9) 1992–2008 ilçesine atanır. Listede adı olmayan birkaç mahallenin dayanağı
  (çevrelenmiş, belde merkezi, komşuluk) `istanbul_1992_2008.json`'da satır satır yazılı.
- Mahalle poligonları (OSM) ilçe poligonunu tam kaplamadığı için kalan alan en yakın
  mahallenin ilçesine verilir (Voronoi). Parçaların birleşimi bugünkü ilçe poligonuna eşit
  olduğundan delik ve çift çizim yok; `tests/validate_elections.py` bunu denetler.
- Sonuç 10 yeni poligon (`HIST-Istanbul-<Ad>-9208`: Büyükçekmece, Çatalca, Esenler, Eyüp,
  Gaziosmanpaşa, Kadıköy, Kartal, Küçükçekmece, Ümraniye, Üsküdar) ve yeniden kurulan
  `HIST-Istanbul-Eminonu`/`-Fatih`. Diğer 20 ilçe bugünkü poligonuyla aynı.
- İpucu, bugünkü ilçelerden alınan payı yazar (ör. "Arnavutköy (%50)").
- Mahalle altı kanun parçaları (yol/parsel sınırlı, 6 madde) bugünkü mahalle poligonlarıyla
  ayrılamıyor; hangileri olduğu `istanbul_1992_2008.json` → `kismiNotlar`'da.
- 1994–2004 yerel kayıtlarında Eminönü belediye satırı yok (DİE kitabında var); bu yüzden
  yerel seçimlerde Fatih bugünkü poligonunda (Eminönü dahil) kalıyor.
- 1991 ve öncesi: aşağıdaki "İstanbul 1961–1992" bölümü.

## İstanbul 1961–1992 ilçe sınırları (2026-09-29, `build_istanbul_1961_1992.py`)

`build_istanbul_1992_2008.py`'nin geriye doğru devamı. İstanbul'da ilçe kuran kanunlar
309 (1963, Gaziosmanpaşa), 3392 (1987, Büyükçekmece, Küçükçekmece, Pendik, Ümraniye,
Kağıthane), 3644 (1990, Bayrampaşa), 3806 (1992), 3949 (1993, Esenler) ve 5747 (2008).
Her seçim tarihinde:

- Bugünkü ilçe ya bütünüyle tek bir eski ilçeye aittir (kanun ek listesi ya da sayım
  zinciri; dayanağı betikteki `ZINCIR`'da), ya da mahalle mahalle atanır
  (`istanbul_1961_1992_mahalle.json`: 2008 ilçeleri 1961–1992, Kağıthane ve Ümraniye
  1961–1987; her mahallenin dönem dönem ilçesi ve dayanağı). 1992–2008 arası atamalar
  `istanbul_1992_2008.json`'dan gelir.
- Seçimde ayrı satırı olmayan yeni ilçe (1987 genel ve referandumunda 3392 ilçeleri, 1988
  referandumunda Küçükçekmece ve Pendik, 1989 yerelde Bayrampaşa'yı içeren Eyüp) kuruluşundan
  bir gün önceki ilçesinin satırına katılır.
- Tek bir mahallesinin bile o tarihteki ilçesi kaynakla bulunamayan bugünkü ilçe o seçimde
  bütün hâlinde taralı kalır (yarım taralı parça çizilmez).
- Parçalar `paylastir` ile üretilir (mahalle poligonları + Voronoi); birleşimleri bugünkü ilçe
  poligonuna eşittir. Her satırın poligonu kimliği `HIST-Istanbul-<Ad>-<bileşim özeti>`; aynı
  bileşim her seçimde aynı kimliği alır. Tek bir bugünkü ilçeye eşit satır bugünkü kimliğini
  korur.
- Seçimler `ilce_bolusumu.json` → `uygulananSecimler` ile tek tek açılır; kayıt
  `istanbul_1961_1992.json` (seçim seçim satır bileşimleri, taralı ilçeler ve belirsiz
  mahalleler).
- 2026-10-04: 1961–1991 genel seçimleri, referandumları ve 1984 yerel de açıldı (bkz. "Seçim seçim ilçe sınırları").
- Kapsam dışı: 1963–1977 yerel seçimleri (il merkezi belediyesi satırı `HISTY-*`, köyler
  belediye seçimine girmez) ve Yalova (1995'e kadar İstanbul'un ilçesi; il katmanında).

## Çok kaynaklı ilçelerde mahalle bölüşümü (2026-09-29, `build_ilce_bolusumu.py`)

"Merkez çoğunluğu" kuralının yerine geçmez; yalnız bir dönemde **bütün** mahallelerin ilçesi
kaynakla bulunduysa o dönemde bugünkü ilçe eski ilçelere bölünür (`ilce_bolusumu.json`:
mahalle, dönem, ilçe, dayanak). Tek bir mahalle belirsizse dönem eskisi gibi kalır: ya Merkez'e
bütünüyle katılır ya da bütün hâlinde taranır. Mahalle poligonu kaynağı `mahalle_geo.json`
(`mg:`) ya da ttezer/turkiye-harita-verisi 83eeb7a (`tt:`, kullanılanlar
`ilce_bolusumu_mahalleler.json`'da). Parçalar `ilce_bolusumu_parcalar.geojson`'da;
`apply_idari_merges.py` her parçayı o seçimdeki eski ilçenin satırına katar ve ipucu payı yazar.

## Seçim seçim ilçe sınırları, 1961–2007 (2026-10-04, `build_ilce_secim.py`)

Amaç: 1961–2007 arası her ilçe düzeyli seçimin haritasında hiçbir bugünkü ilçe sonuçsuz (taralı)
kalmasın; harita genel olarak doğru görünsün. Her seçim için:

- `ilce_eslesme/<seçim>.csv`: her bugünkü ilçenin o seçimdeki satırı, kuruluş tarihi/kanunu, yöntem,
  güven (`kesin`, `yaklasik`, `kaba`), kaynak ve not. O tarihte var olan ilçeler seçim sonucunun
  satırlarıdır (esas kaynak). Kayıt ve birleşimler: `ilce_eslesme/<seçim>.json`.
- Yöntemler: `kendi_satiri`, `tarihsel_birlesim` (mevcut kaynaklı HISTK/HIST), `istanbul_mahalle` ve
  `bolunmus_poligon` (İstanbul mahalle tablosu; Eminönü/Fatih), `istanbul_zinciri`, `ayni_eski_ilce`
  (bütün eski ilçeleri o tarihte aynı ilçede), `cogunluk` (ek liste birimlerinin ≥%70'i aynı ilçeden;
  yaklaşık), `en_buyuk_pay` (%70'e ulaşan yok; kaba), `komsuluk` (soy bilgisi yok ya da eski ilçeleri
  o tarihte belirsiz: en uzun sınır komşusu satır, aynı ilde; il o seçimde yoksa komşu ilde; kaba).
- Pay hesabı: ek listedeki her eski ilçe o seçimdeki karşılığına çevrilir (zincirle); kaynağı
  yazılmamış birim "bilinmiyor" sayılır ve paydaya girer.
- `uygula`: bir satırın bugünkü ilçeleri mevcut poligonundan fazlaysa `HIST<seçim>-<plaka>-<Ad>`
  poligonu üretilir (mevcut poligon + katılan bugünkü ilçeler, dikiş delikleri doldurulur); yalnız o
  seçimin satırlarının `geomId`'si değişir, oy değişmez. `harita_notlari.json`'da tarama ve ipucu
  ("Bugünkü sınırlarla", mahalle ve çoğunluk payları) güncellenir. Yerel seçimlerde ardından
  `build_meclis_harita.py` (meclis haritaları başkanlık satırlarının poligonlarını kullanır).
- `kontrol` (ayrıca `tests/validate_elections.py`, bütün `ilce_eslesme/*.csv` için): her satır tek
  poligona, her bugünkü ilçe en fazla bir satıra bağlı (bölünmüş poligonlar ve aynı ad/poligonlu çift
  satır hariç); tablo ile harita tutarlı; birleşimler il dışına taşmıyor.
- İstanbul: `build_istanbul_1961_1992.py` 1961–1991 genel seçimleri, referandumları ve 1984/1989
  yerel için çalışır (`ilce_bolusumu.json` → `uygulananSecimler`). 1987 öncesi Ümraniye mahalleleri
  (bugünkü Ataşehir, Çekmeköy, Sancaktepe parçaları) `prepare_istanbul_historical_assignments.py`
  içinde 1960 sayımının köy listesiyle, adı sayımda olmayanlar komşu sınır çoğunluğuyla (yaklaşık);
  Kağıthane → Şişli, Ümraniye → Üsküdar `ZINCIR`'da (1960 sayımı, yaklaşık). 1963–1977 yerelde
  sonradan kurulan İstanbul ilçeleri, o tarihteki ilçelerini kapsayan satıra (il merkezi belediyesi
  poligonu, Çatalca, Kartal) bağlanır. Sonuç 1940/1963 İstanbul ilçe haritalarıyla görsel olarak
  karşılaştırıldı.
- İşlenen seçimler: 1961–2007 genel seçimleri, 1961/1982/1987/1988/2007 referandumları, 1963–1989
  yerel seçimleri. 1994, 1999 ve 2004 yerel bekliyor (aşağıda).
- Geometrisiz satır: Ankara Merkez (1961–1983 ayrı ilçe, sınırı kaynakta yok; 2963 madde 2).
- Şüpheli: Kastamonu "Bozkurt" satırı 1961/1965'te bugünkü Bozkurt'a (1055, 1968) bağlı; korunuyor.
- Veri sorunları (değiştirilmedi): 1991'de İstanbul'da iki "Bakırköy" satırı (seçim çevresi
  bölünmesi; aynı poligon). 1994 yerel Kaynaşlı belde satırının plakası 81 (o tarihte Bolu). 1994,
  1999, 2004 yerel kayıtlarında Artvin Hopa iki kez (aynı oy; biri Hopa + Kemalpaşa, öteki yalnız
  Hopa poligonuyla) ve Kemalpaşa'nın ayrı belde satırı var: Kemalpaşa iki kez çiziliyor; bu üç seçim
  karar bekliyor.
- Sıra: [`prepare_istanbul_historical_assignments.py` → `build_istanbul_1961_1992.py`] →
  `build_ilce_secim.py <seçim>` → [yerel: `build_meclis_harita.py`] → checksum yenile →
  `scripts/build.py`.
- Bilinen tutarsızlık: `apply_idari_merges.py` yeniden çalıştırılırsa bu katmanın üzerine yazabilir
  (ör. 1987/1988 İstanbul HISTK birleşimleri); bu çalışmada o betik çalıştırılmadı.

## Bilinen boşluklar (`faz1_rapor.json`)

- **1955 yerel ve 1994 yerel için il sınır dosyası yok** (66 ve 76 il). Snapshot'ta
  `provinceGeometryStatus: "missing_snapshot_do_not_guess"`.
- **1955 yerel verisi 64 il**: Adıyaman, Nevşehir, Sakarya yok, Kırşehir il olarak var.
- **Bozkurt (Kastamonu)**: 1055 sayılı Kanunla 17.07.1968'de (merkezi Pazaryeri)
  kuruldu; 1961 ve 1965 seçim verisindeki "Bozkurt" satırları bu ilçe olamaz — seçim
  verisinin adı ya da eşlemesi doğrulanmalı.
- **2010 referandumu ve 2011 genel seçimi**: kaynak, sonuçları 2012 ve sonrasında
  kurulan 22 ilçeye göre yeniden toplamış (`kaynakSonrakiIlcelereGoreToplamis`);
  idari çelişki değil.
- **Tillo (Siirt)**: 2007'den sonraki 12 seçimde satırı yok (veri boşluğu).
- İçişleri listesi yalnızca 2018'de var olan birimleri içerir; kaldırılmış
  ilçeler (ör. Eminönü) ve kaldırılmış adlar bu kaynakta yok.

## Sonraki fazlar

1. **Faz 2 — soy, kanun kanun.** 3644 (1990, 130 ilçe), 3392 (1987, 103),
   7033 (1957, 77), 5747 (2008, 43), 6360 (2012, 26), 6324/6325 (1954, 31),
   6068 (1953, 21), 3806 (1992, 13) sayılı kanunların ekleri: hangi bucak/köy hangi
   ilçeden. Tek ebeveynli ayrılmalar `merge_into`, çok ebeveynliler köy/mahalle
   düzeyinde doğrulanamazsa `unresolved`.
2. **Faz 3 — il değişiklikleri.** 1953–1999 arasında kurulan illerin ilçelerinin
   önceki illeri (kısmen seçim verisinden zaten var), Kırşehir 1954–1957 ilçe
   bağlılıkları.
3. **Faz 4 — geometri ve ön yüz.** Birleşim poligonları, `era1955` ve `era1994`
   il sınırları; haritada il sınır dosyasının seçim kimliğine göre snapshot'tan
   seçilmesi (özel harita ve atlas).

## 04.10.2026 durum güncellemesi

- 2007 referandumu: mevcut resmî PDF'lerden eksik 17 ilçe eklendi; 923 ilçe kaydı var.
- İstanbul 1989 yerel ve 1991 genel sınırları, depodaki mahalle atamaları ve
  idari kuruluş zincirleriyle üretildi. Bu geometriler tarihî sınırların
  belgelenmiş yeniden kurulumudur; güncel mahalle geometrisi ve boşluk
  tamamlama yöntemi nedeniyle kadastro kesinliği iddiası taşımaz.
- Oy içermeyen modern ilçe iskeletleri, 2009/2011 tarihî ana ilçe birleşimini
  artık engellemiyor. Meclis görünümü de aynı tarihî geometriye bağlanıyor.
- Tillo'nun mevcut YSK meclis kayıtları eşleştirildi. Başkanlık/genel seçim
  hattındaki eksik Tillo oyları için başka seçimden oy aktarılmadı.
- 1961–1987 İstanbul mahalle bölüşümleri ve genel çok kaynaklı ilçe bölüşümleri
  hâlâ ek kaynak/doğrulama bekliyor; yalnız 1989 ve 1991 yeni katmanı etkin.
- 1950/1954/1957 genel seçimlerde ülke çapında ilçe kaynak araması önceki
  çalışma kararına göre kapalıdır; bu seçimler il düzeyinde kalır.
- Güncel sayılar `docs/rapor/ozet.json` ve yanındaki CSV'lerden okunmalıdır.

Tekrar üretim sırası: `prepare_istanbul_historical_assignments.py`,
`build_istanbul_1961_1992.py`, `apply_idari_merges.py`,
`build_meclis_harita.py`, `harita_durum_raporu.py`, checksum güncellemesi,
`build.py`. Genel amaçlı `ilce_bolusumu.json` boş bırakılmıştır; bilinmeyen
çok kaynaklı bölüşümler bu dosyada varsayımla doldurulmaz.

1961–2007 seçim seçim ilçe sınırları için bkz. "Seçim seçim ilçe sınırları, 1961–2007"
(`build_ilce_secim.py <seçim>`); İstanbul adımlarından sonra, meclis/rapor/checksum/build
adımlarından önce çalıştırılır.
