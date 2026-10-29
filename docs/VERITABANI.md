# İlişkisel veritabanı (SQLite)

`data/normalized/` altındaki bütün seçim verisi tek bir SQLite dosyasına, birincil ve yabancı anahtarlarla yüklenir.
Kaynak JSON'lar değişmez; veritabanı onlardan türetilir ve depoda tutulmaz (`build/` git dışı).

```bash
python3 scripts/veritabani/build_db.py                 # build/secimler.sqlite  (~280 MB, mahalle dahil, ~30 sn)
python3 scripts/veritabani/build_db.py --mahalle-yok   # mahalle hariç          (~90 MB)
python3 tests/test_veritabani.py                       # kaynakla birebir mi?
```

Test; her oylama için il/ilçe/mahalle/belde satır sayılarını, oy, seçmen ve sandalye toplamlarını,
milletvekili ve senatör sayılarını kaynak JSON ile karşılaştırır ve `PRAGMA foreign_key_check` ile anahtar
bütünlüğünü doğrular.

## Ne yükleniyor

| Kaynak | Nereye |
|---|---|
| `elections/<tür>/*.json` (46 seçim) | `secim`, `sonuc_il`/`oy_il`/`sandalye_il`, `sonuc_ilce`/`oy_ilce` |
| `mahalle/*.json` (2009–2024) | `mahalle`, `sonuc_mahalle`/`oy_mahalle` |
| `meclis_harita/*_bm.json`, `*_igm.json` | belediye meclisi ve il genel meclisi; ayrı `secim` satırı (`'1994yerel_bm'`), il ve ilçe sonuçları |
| `ek/senato/*.json` | `secim` (`tur='senato'`), il oyları, ilçe oyları (TÜİK) ya da yalnız ilçe birincisi, senatörler |
| `ek/yenileme_ara/*.json` | `secim` (`tur='ara'`): milletvekili ara seçimleri, belediye yenileme ve ara seçimleri |
| `ek/milletvekilleri/*.json` | `secilen` (`gorev='milletvekili'`) |
| `ek/beldeler/*.json` | `sonuc_belde`/`oy_belde`: belde belediye başkanlığı |
| `ek/belediye_meclisi/*.json` | yalnız belde satırları `sonuc_belde`'ye (il/ilçe düzeyi `meclis_harita`'dan) |
| `ek/il_genel_meclisi/*.json` | yalnız kapsam özeti (il/ilçe düzeyi `meclis_harita`'dan; şehir/köy alt kırılımı yüklenmez) |
| `meclis_2024.json` | `sandalye_ilce`: 2024 belediye meclisi üye dağılımı |
| her ek dosyanın `kapsam`/`ozet` alanı | `kaynak_kapsami`: kaynakta kaç kayıt bulundu, kaç beklendi |

## Şema

```
                ┌─< sonuc_il ─────< oy_il ──────────┐
                │      │  └───────< sandalye_il ────┤
                │      il (plaka)                   │
secim ──────────┼─< sonuc_ilce ───< oy_ilce ────────┤
 (ana_secim_id) │      ilce (ilce_id = geomId)      ├── secenek (parti / aday / referandum / diğer)
                │      └──────────< sandalye_ilce ──┤
                ├─< sonuc_mahalle < oy_mahalle ─────┤
                │      mahalle (ilce_id, mahalle_id)│
                ├─< sonuc_belde ──< oy_belde ───────┤
                ├─< secilen ────────────────────────┘
                └─< kaynak_kapsami
```

| Tablo | Birincil anahtar | Satır |
|---|---|---|
| `secim` | `secim_id` | 91 oylama |
| `il` | `plaka` (0 = yurt dışı) | 82 |
| `ilce` | `ilce_id` (güncel `TR-D-..`, tarihsel `HIST..`) | ~1.900 |
| `mahalle` | `(ilce_id, mahalle_id)` | 49.330 |
| `secenek` | `secenek_id`, `ad` benzersiz | 118 |
| `sonuc_il` / `oy_il` / `sandalye_il` | `(secim_id, plaka[, secenek_id])` | |
| `sonuc_ilce` / `oy_ilce` / `sandalye_ilce` | `(secim_id, ilce_id[, secenek_id])` | |
| `sonuc_mahalle` / `oy_mahalle` | `(secim_id, ilce_id, mahalle_id[, secenek_id])` | 602.285 / 2.423.173 |
| `sonuc_belde` / `oy_belde` | `sonuc_belde_id` / `(sonuc_belde_id, secenek_id)` | 30.019 / 93.470 |
| `secilen` | `secilen_id` | 9.789 (9.279 milletvekili, 510 senatör) |
| `kaynak_kapsami` | `(secim_id, veri)` | 80 |

**`secim` satırları:** `tur` seçimin türü (`genel`, `yerel`, `referandum`, `cumhurbaskanligi`, `senato`, `ara`),
`oylama` o sandıkta neyin oylandığı (`milletvekili`, `baskanlik`, `belediye_meclisi`, `il_genel_meclisi`,
`referandum`, `cumhurbaskanligi`, `senato`). Aynı günün ikincil oylamaları ana seçime `ana_secim_id` ile bağlanır:
`'2024yerel_bm'` ve `'2024yerel_igm'` → `'2024yerel'`; `'2019istanbul_bb_yenileme'` → `'2019yerel'`.

Hazır görünümler: `v_oy_il`, `v_oy_ilce`, `v_oy_mahalle`, `v_oy_belde`, `v_secilen` (seçim, yer ve seçenek
adları birleşik gelir).

## Bilinmesi gerekenler

- **İlçe kimliği zamana bağlı.** O seçimdeki ilçe adı ve ili `sonuc_ilce.ad` / `sonuc_ilce.plaka`'dadır;
  `ilce` tablosundaki ad ve plaka son görülen değerdir. Ad ile ararken `sonuc_ilce.ad` kullanın.
- **Parti sürekliliği modellenmez.** Her parti adı ayrı bir `secenek`tir. Yalnız büyük/küçük harf farkı olan
  yazımlar ('YENİDEN REFAH' / 'Yeniden Refah') tek seçenektir.
- **Belde kimliği yoktur.** Kaynaklar arasında ortak bir belde anahtarı bulunmadığı için (eski yıllar taranmış
  kitaptan okunan adlar, 2009 sonrası meclis kayıtlarında yalnız YSK belde kodu) belde sözlüğü kurulmadı; her
  `sonuc_belde` satırı bir seçimdeki bir beldedir. İlçeye adından bağlanabilenlerde `ilce_id` doludur
  (başkanlık %97, meclis %92).
- **Taranmış kitaptan okunan satırlar** (1963–2004 meclis beldeleri) `sonuc_belde.kontrol` sütununda doğrulama
  sonucunu taşır: `tutarli` dışındakiler (`tutarsiz`, `toplamTutmuyor`, `konumSupheli` ...) dikkatle kullanılmalı.
  Okunamayan değerler (ör. 10¹² üstü sayılar) boş bırakılır ve `not_metni`'nde yazar.
- **Kaynakta doğrulanamayan alanlar** (senato ve ara seçim TÜİK satırlarında `dogrulanamayanAlanlar`) boş
  bırakılır, not düşülür.
- **Oran** ana seçimlerde kaynaktaki değerdir; kaynağı yalnız oy sayısı veren satırlarda (senato, ara seçimler)
  geçerli oydan hesaplanır.
- **Yalnız kazananı bilinen kayıtlar**: `sadece_kazanan = 1` (1950–1955 yerel ilçeleri, senatoda TÜİK kitabı
  olmayan ilçeler, Vikipedi'den gelen belde başkanları — bunlarda yalnız kazananın oyu vardır).
- **1986 milletvekili ara seçimi**: Manisa'nın iki seçim çevresi il satırında toplanır; çevre ayrıntısı
  `kaynak_json`'dadır.
- **Kapsam**: `secilen` tam değildir (örneğin 2023'te 600 milletvekilinin 405'i). Eksiklik `kaynak_kapsami`'nda:
  `SELECT * FROM kaynak_kapsami WHERE durum <> 'tam'`.
- Yurt dışı oyları `plaka = 0` satırlarındadır; il toplamlarında `WHERE plaka > 0` kullanın.

## Örnek sorgular

```sql
-- 1977 genel seçimde İstanbul'da CHP'nin en güçlü 3 ilçesi
SELECT ilce, oran FROM v_oy_ilce
WHERE secim_id = '1977' AND plaka = 34 AND secenek = 'CHP'
ORDER BY oran DESC LIMIT 3;

-- Bir ilçenin bütün genel seçimlerdeki kazananı ve katılımı
SELECT s.secim_id, se.ad AS kazanan, sc.katilim
FROM sonuc_ilce sc
JOIN secim s USING (secim_id)
LEFT JOIN secenek se ON se.secenek_id = sc.kazanan_id
WHERE sc.plaka = 34 AND sc.ad = 'Ümraniye' AND s.tur = 'genel'
ORDER BY s.yil;

-- 2024 yerel: aynı ilçede başkanlık ve belediye meclisi kazananı farklı olanlar
SELECT b.plaka, b.ad, kb.ad AS baskanlik, km.ad AS meclis
FROM sonuc_ilce b
JOIN sonuc_ilce m ON m.ilce_id = b.ilce_id AND m.secim_id = '2024yerel_bm'
JOIN secenek kb ON kb.secenek_id = b.kazanan_id
JOIN secenek km ON km.secenek_id = m.kazanan_id
WHERE b.secim_id = '2024yerel' AND b.kazanan_id <> m.kazanan_id;

-- Bir ilin bütün dönemlerdeki milletvekilleri
SELECT secim_id, ad, parti FROM v_secilen
WHERE gorev = 'milletvekili' AND il = 'Trabzon' ORDER BY yil, ad;

-- Bir oylamanın ara/yenileme seçimleri
SELECT secim_id, ad, aciklama FROM secim WHERE ana_secim_id = '2024yerel' OR tur = 'ara';
```

## Başka veritabanına taşıma

Şema standart SQL'e yakındır. MySQL/PostgreSQL/Oracle'a taşımak için `schema.sql`'deki `TEXT` sütunları
`VARCHAR`'a çevirip `WITHOUT ROWID` ifadesini kaldırmak ve veriyi CSV olarak aktarmak yeterlidir.
