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
- Öncelik (1961 sonrası seçimleri etkileyen, çözülmemiş): 309 (1963: Gaziosmanpaşa),
  6447 (2013: Altınordu), 7148 (2018: Derecik), KHK 694 (2017: Sultanhanı, Kemalpaşa);
  ardından 5747 (2008) ve 6360 (2012) büyükşehir bölünmeleri (mahalle düzeyi).

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
