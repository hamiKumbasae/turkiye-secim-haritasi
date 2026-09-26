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

## Mahalle düzeyinde paylaştırma (Faz 4b — `build_mahalle_bolusumu.py`, pilot İstanbul)

Birden çok eski ilçeden kurulan ilçenin alanı, güncel mahalle poligonlarıyla
(`geo/normalized/mahalle_geo.json`) eski ilçeleri arasında paylaştırılır; her eski
ilçenin parçası (`PARCA-*`) onun sentetik birleşimine katılır, paylaştırılamayan kısım
(`BELIRSIZ-*`) haritada taralı ve açıklamalı çizilir (`harita_notlari.json`).

- Birimin eski ilçesi: kanun ek listesi; ilk kademe belediyesinin ilçesi DİE 2004 Tablo 9
  (`district_mahalle_merges.yaml`'daki "belde ilçeleri yalnız blog kaynaklı" engeli bununla
  kalktı: Arnavutköy, Boğazköy, Bolluca, Haraççı, Taşoluk → Gaziosmanpaşa; Hadımköy,
  Durusu → Çatalca).
- Eşleşme: aynı ad; belde "Merkez"i = belde adı; belde adını taşıyan güncel mahalle.
- Çıkarım (işaretli, `cikarim: cevrelenmis`): adı eşleşmeyen mahalle ya da mahalle dışı
  alan, dış sınıra değmeyen ve yalnız tek eski ilçenin parçalarına değen bağlı bileşense o
  ilçeye verilir (Arnavutköy: Anadolu, Mustafa Kemal Paşa, Yunus Emre → Gaziosmanpaşa).
- Kanunda iki ilçe arasında paylaşıldığı yazan birim çıkarımla atanmaz (Sultangazi'nin iki
  Habipler mahallesi: Gaziosmanpaşa ya da Esenler parseli).
- Parçalar ayrıktır, ilçeyi tam böler; komşu güncel ilçelerle kaynaktaki ince örtüşmeler
  önce çıkarılır.

| İlçe | Eski ilçe payları | Paylaştırılamayan |
|---|---|---|
| Arnavutköy (5747) | Gaziosmanpaşa %48.8, Çatalca %40.3 | %10.9 (Terkos; Sazlıdere Baraj Gölü — Küçükçekmece'nin Şamlar parçası dahil; kıyı ormanı) |
| Sultangazi (5747) | Gaziosmanpaşa %62.8, Eyüp %12.4 (Yayla) | %24.8 (iki Habipler mahallesi ve çevresi) |

Sayım dönemleri (Arnavutköy): birimlerin ilçesi DİE 1960, 1985, 1990 nüfus sayımı idari
bölünüş kitaplarından (`data/raw/tuik/nufus-sayimi-idari-bolunus/`). İki sayım arasındaki
seçimlerde birim yalnız iki sayımda da aynı ilçedeyse atanır:

| Dönem | Seçimler | Gaziosmanpaşa | Çatalca | Paylaştırılamayan |
|---|---|---|---|---|
| 1960–1985 | 1961–1984 | %34.1 (1963 öncesi Eyüp) | %47.3 (Yeniköy dahil) | %18.7 (Tayakadın: 1960 Çatalca → 1985 Gaziosmanpaşa) |
| 1985–1990 | 1987–1989 | %41.9 | %40.3 | %17.8 (Yeniköy: 1985 Çatalca → 1990 Gaziosmanpaşa) |
| 1990–2008 | 1991–2007 | %48.8 | %40.3 | %10.9 |

1960 sayımından önceki seçimlerde (1950/1955 yerel) Arnavutköy bölüştürülmez.

İstanbul (2026-09-27) — bölüştürülen ilçeler ve eski ilçe payları (1990–2008 / 1960–1985):

| İlçe | 1991–2007 | 1961–1984 | Paylaştırılamayan başlıca kısım |
|---|---|---|---|
| Arnavutköy | Gaziosmanpaşa %49, Çatalca %40 | Gaziosmanpaşa (Eyüp) %34, Çatalca %47 | Terkos, Sazlıdere Gölü; 1961–84 Tayakadın |
| Sultangazi | Gaziosmanpaşa %63, Eyüp %12 | aynı | iki Habipler mahallesi |
| Esenyurt | Büyükçekmece %90 | Çatalca (Büyükçekmece üzerinden) %90 | Yeşilkent (Avcılar parçası) |
| Başakşehir | Küçükçekmece %33, Büyükçekmece %16 | Bakırköy %33, Çatalca %16 | Başakşehir ve Başak mahalleleri (Esenler parçası) |
| Çekmeköy | — (1987–2008 Ümraniye'de) | Beykoz %52, Üsküdar %30 | Taşdelen (sayımda yok) |
| Sancaktepe | — | 1985–87: Üsküdar %31 | Samandıra'nın 2008 sonrası adları; 1961–84 Sarıgazi (Kartal → Üsküdar) |
| Ataşehir | — | Kadıköy %59, Kartal %14, Üsküdar %9 | 2008'de Ümraniye'ye bağlı mahalleler |

Ek kurallar: `liste-tümleyeni` (kanun listesinin, kanunda paylaşılmış birim dışındaki bütün
birimleri o dönemde tek ilçedense geri kalan alan o ilçeye; paylaşılmış birime değen alan
hariç) ve "Mahallesinin ... kısmı" satırlarından mahalle adı. Bahçeşehir beldesi sayımlarda
yok; 1999 ve 2004 DİE yerel kitaplarında Büyükçekmece'de (işaretli çıkarım). Eski ilçesi o
seçimde satır olmayan parça (ör. 1991'de Esenler) `PARCA-*` olarak taralı çizilir.

Kaynağı yazılmamış 1987 birimleri için `sayim_kaniti.json` (elle, köy/belde düzeyi kanıt):
Küçükçekmece ← Bakırköy, Pendik ← Kartal.

İstanbul'da ilçe verisi olan genel seçimlerde boş kalan alan (ilin %'si): 1961–1983 %6.0,
1987 %5.5, 1991 %2.5, 1995–2007 %2.1 (başta 1961–1987 %25, 1995 %11.7). Kalanlar: bölüştürülen
ilçelerin paylaştırılamayan kısımları; 1987 öncesi Kağıthane, Esenler, Ümraniye (şehir içi
mahalleler — sayım kitaplarında listelenmiyor, 1987/1993 kanunlarında kaynak yazılmamış) ve
1961–84 Sancaktepe.
Uygulandığı seçimler: eski ilçelerin tümü o seçimde satır olarak bulunuyorsa (zincirle:
1963 öncesi Gaziosmanpaşa → Eyüp). 1963–1977 yerel verisinde Gaziosmanpaşa/Eyüp belediye
satırı olmadığından uygulanmaz (`merge_plan.json` → `bolusumUygulanmadi`).
Sınırlar: sayım kitabı olmayan ilçelerde (Sultangazi) belde/mahalle bağlılığı kanun tarihindeki durumdur;
2008 sonrası mahalle ad/sınır değişiklikleri adı eşleşen mahallelerde fark edilmez.
Sıradaki adaylar: Başakşehir, Esenyurt, Esenler (İstanbul), sonra diğer illerin çok
kaynaklı ilçeleri.

## Sayım dizini ile otomatik dönemsel bağlılık (Faz 4c)

`scripts/pipelines/historical_geo/extract_sayim_koyleri.py`: DİE 1960, 1985, 1990 sayım
kitaplarından köy/belde → ilçe dizini (`data/kaynaklar/tuik/nufus_sayimi/<yıl>_koyler.json`;
1960: 33.967, 1985: 33.830, 1990: 33.232 satır). Köy satırları ilçe bölümünü kapatan
"X İLÇESİ TOPLAMI" satırıyla geriye dönük atanır (başlık OCR'da düşse bile); kitabın kendi
köy sayılarına göre kapsama ~%90. Kitaplar depoda değil: betik TÜİK kütüphanesinden indirip
SHA-256 ile doğrular (`.cache/`).

`build_mahalle_bolusumu.py` elle `DONEMSEL` tablosu olmayan bütün çok kaynaklı ilçelere
(mahalle poligonu olanlar) bunu uygular: birim sayımda kanundaki eski ilçesinde (ya da onun
kanunla ayrıldığı ata ilçede) bulunursa o dönemde aynı sayılır; bulunamaz ya da farklı çıkarsa
o dönem paylaştırılamayan kısma gider. OCR hataları yalnız taralı alanı büyütür.

Kanundan hemen önceki dönemde eski ilçelere dağıtılan pay (İstanbul dışı): Çukurova (5747) %5, Akyurt (3644) %34, Pursaklar (5747) %3, Aksu (5747) %40, İbradı (3644) %8, Konyaaltı (5747) %26, Didim (3644) %14, Defne (6360) %21, Aliağa (2585) %30, Özvatan (3644) %7, Körfez (3392) %46, Derbent (3644) %0, Dargeçit (3392) %62, Gürgentepe (3392) %15, İkizce (3644) %29, Ondokuzmayıs (3392) %9, Salıpazarı (3392) %1, Altınyayla (3644) %0, Edremit (3644) %1, Gülağaç (3644) %0, Demirözü (3392) %0.
Kalan kısım çoğunlukla ilçe merkezinin kendi (kanun listesinde olmayan) mahalleleri ve sayımda
bulunamayan köy adlarıdır. Mahalle/köy poligonu olmayan ilçelerde (büyükşehir dışı ~26 ilçe)
bölüştürme yapılamaz.

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
