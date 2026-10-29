# İlişkisel veritabanı (SQLite)

`data/normalized/` altındaki bütün seçim verisi tek bir SQLite dosyasına, birincil ve yabancı anahtarlarla yüklenir.
Kaynak JSON'lar değişmez; veritabanı onlardan türetilir ve depoda tutulmaz (`build/` git dışı).

```bash
python3 scripts/veritabani/build_db.py                 # build/secimler.sqlite  (~250 MB, mahalle dahil, ~25 sn)
python3 scripts/veritabani/build_db.py --mahalle-yok   # yalnız il + ilçe        (~56 MB)
python3 tests/test_veritabani.py                       # kaynakla birebir mi?
```

Test her seçim için il/ilçe/mahalle satır sayılarını, oy ve seçmen toplamlarını, sandalye toplamını kaynak
JSON ile karşılaştırır ve `PRAGMA foreign_key_check` ile anahtar bütünlüğünü doğrular.

## Şema

```
secim ─┬─< sonuc_il ──────< oy_il >──────┐
       │      │  └────────< sandalye_il >┤
       │      il (plaka)                 │
       ├─< sonuc_ilce ────< oy_ilce >────┼── secenek (parti / aday / referandum / diğer)
       │      ilce (ilce_id = geomId)    │
       └─< sonuc_mahalle ─< oy_mahalle >─┘
              mahalle (ilce_id, mahalle_id)
```

| Tablo | Birincil anahtar | Satır |
|---|---|---|
| `secim` | `secim_id` (`'2023'`, `'2024yerel'`, `'2017referandum'`, `'2023cb2tur'`) | 46 |
| `il` | `plaka` (0 = yurt dışı) | 82 |
| `ilce` | `ilce_id` (güncel `TR-D-..`, tarihsel `HIST..`) | 1.866 |
| `mahalle` | `(ilce_id, mahalle_id)` | 49.330 |
| `secenek` | `secenek_id`, `ad` benzersiz | 110 |
| `sonuc_il` / `oy_il` / `sandalye_il` | `(secim_id, plaka[, secenek_id])` | 3.398 / 24.001 / 3.439 |
| `sonuc_ilce` / `oy_ilce` | `(secim_id, ilce_id[, secenek_id])` | 34.927 / 373.547 |
| `sonuc_mahalle` / `oy_mahalle` | `(secim_id, ilce_id, mahalle_id[, secenek_id])` | 602.285 / 2.423.173 |

Kolay sorgu için hazır görünümler: `v_oy_il`, `v_oy_ilce`, `v_oy_mahalle` (seçim, il/ilçe/mahalle adı,
seçenek adı, oy, oran ve `kazandi` sütunu birleşik gelir).

## Bilinmesi gerekenler

- **İlçe kimliği zamana bağlı.** Bir ilçe birimi farklı seçimlerde farklı adla ya da farklı ilde görünebilir
  (il bölünmeleri, ilçe kurulmaları). O seçimdeki ad ve il `sonuc_ilce.ad` / `sonuc_ilce.plaka`'dadır;
  `ilce` tablosundaki ad ve plaka son görülen değerdir. Ad ile ararken `sonuc_ilce.ad` kullanın.
- **Parti sürekliliği modellenmez.** Her parti adı ayrı bir `secenek`tir; partiler arası devamlılık
  (kapatılan/yeniden kurulan partiler) yorum gerektirdiği için bilerek tabloya konmadı.
- **Yalnız kazananı bilinen kayıtlar** (1950–1955 yerel gibi): `sonuc_ilce.sadece_kazanan = 1`, oylar NULL.
- **Notlar ve kaynaklar** kaybolmaz: `not_metni` ve `kaynak_json` sütunlarında kaynak kayıttaki gibi durur.
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

-- 2019 → 2024 yerel seçimde kazananı değişen iller
SELECT a.ad AS il, k1.ad AS kazanan_2019, k2.ad AS kazanan_2024
FROM sonuc_il a
JOIN sonuc_il b  ON b.plaka = a.plaka AND b.secim_id = '2024yerel'
JOIN secenek k1 ON k1.secenek_id = a.kazanan_id
JOIN secenek k2 ON k2.secenek_id = b.kazanan_id
WHERE a.secim_id = '2019yerel' AND a.kazanan_id <> b.kazanan_id;
```

## Başka veritabanına taşıma

Şema standart SQL'e yakındır. MySQL/PostgreSQL/Oracle'a taşımak için `schema.sql`'deki `TEXT` sütunları
`VARCHAR`'a, `WITHOUT ROWID` ifadesini kaldırarak çevirip veriyi CSV olarak aktarmak yeterlidir.
