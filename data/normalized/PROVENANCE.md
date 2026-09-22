# Normalize edilmiş veri

`scripts/normalize.py` ile kök `index.html`'in gömülü verisinden (henüz
dokunulmamış, tek kaynak) **tür bazında** ayrıştırılmış, kayıpsız çıktı.
Hiçbir sayı/değer değiştirilmedi — sadece dosya konumu ve gruplama.

**Doğrulama (2026-09-22):** Her dosyanın içeriği, kaynağı olan gömülü JSON'un
karşılık gelen kesimiyle Python `==` (derin eşitlik) ile tek tek karşılaştırıldı
— partiler, 4 tür dosyası, 15 mahalle yıl dosyası, meclis_2024.json: **22/22
kontrol geçti**.

**Ek (2026-09-22, aynı gün ikinci bir oturumda):** `yerel_secimler.json`'a
1950/1955/1963/1968/1973/1977 için 6 yeni anahtar eklendi (sadece il merkezi,
`ilceler` boş) — bunlar YUKARIDAKİ index.html-kaynaklı doğrulamanın DIŞINDA,
çünkü index.html'de hiç yoktu (bu oturumda ilk kez Wikipedia'nın il-bazlı alt
makalelerinden çekildi). Yöntem, çapraz kontroller ve bilinen sınırlar için
bkz. [`../../SECIM_TAKVIMI.md`](../../SECIM_TAKVIMI.md) ve `sources.yml`'deki
ilgili 6 giriş. `partiler.json`'a bu eklemeyle birlikte 4 yeni parti girdi
(TSİP, SDP, MKP, KARMA).

## Dosyalar

- `partiler.json` — tüm seçimler arası paylaşılan parti adı→renk/kısaltma
  eşlemesi (94 parti)
- `cumhurbaskanligi.json`, `genel_secimler.json`, `yerel_secimler.json`,
  `referandumlar.json` — il/ilçe düzeyi seçim sonuçları, seçim türüne göre
  ayrılmış (anahtarlar `sources.yml`'deki ile birebir aynı, örn. `"2023"`,
  `"2014yerel"`, `"2017referandum"`, `"2023cb2tur"`)
- `mahalle/<secim_anahtari>.json` — mahalle/muhtarlık düzeyi oy verisi,
  15 dosya, her biri bir seçim (bkz. `sources.yml`'deki YSK `backup` girişleri)
- `meclis_2024.json` — 2024 yerel seçiminin il meclisi üye dağılımı (ayrı,
  küçük bir veri kümesi)

**Not:** mahalle GEOMETRİSİ burada değil, `../../geo/normalized/mahalle_geo.json`'da
(oy verisinden ayrı — bir mahallenin sınırları yıldan yıla değişmiyor, tekrar
tekrar saklamaya gerek yok).

## Format

Kompakt JSON (girintisiz, `sort_keys=True`) — bu boyuttaki dosyalar (bazıları
onlarca MB) zaten satır satır elle okunmuyor; asıl "normalized" faydası
tür/yıla göre ayrı dosyalara bölünmüş olması, insan tarafından biçimli
görünmesi değil.

## Bütünlük

`checksums.sha256` — 2026-09-22 itibarıyla.
