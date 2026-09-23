# Ham veri boşlukları — dürüst envanter

Bu belge, "her dış veri kaynağını bir kez `data/raw/`'a checksum'lı snapshot
olarak sakla, canlı bağımlılığı kaldır" hedefinin **şu an tam olarak
karşılanamadığı** yerleri saklamadan listeler.

## `data/raw/ysk/1950-1977/` — DOLU (2026-09-22'de eklendi)

YSK'nin 1950-1977 genel seçimleri için resmi, TÜİK kaynaklı il-bazlı
arşivi (66 il PDF'i + ulusal özet) burada, pinlenmiş/checksum'lı bir
snapshot olarak duruyor. Ayrıntı: `data/raw/ysk/1950-1977/PROVENANCE.md`
ve `scripts/pipelines/genel_1950_1977/`. Bu, aşağıdaki paragraftaki genel
"mahalle düzeyi YSK verisi" boşluğundan AYRI ve TAMAMLANMIŞ bir kaynak.

## `data/raw/ysk/` (mahalle düzeyi kısmı) — BOŞ

YSK Açık Veri Portalı'ndan (`acikveri.ysk.gov.tr`) bu depoya gömülü tüm
mahalle/muhtarlık düzeyi veri (15 seçim, `scripts/pipelines/mahalle_veri/`
ile üretildi) ve 2014 Cumhurbaşkanlığı seçiminin il/ilçe düzeyi veri, önceki
bir oturumda çekildi. O oturumun **ara ham JSON çıktıları** (her `fetch_*.js`
çalıştırmasının `<outFile>` argümanına yazdığı dosyalar) session-özel bir
scratchpad klasöründe tutulmuştu ve o oturum bitince silindi — sadece **işlenmiş
son hâli** (`index.html`'e gömülü `mahalle_geo.json`/`mahalle_votes.json`) hayatta
kaldı, ham API yanıtları değil.

**Bu kalıcı bir kayıp değil, yeniden üretilebilir:** YSK'nin API'si hâlâ canlı
ve `scripts/pipelines/mahalle_veri/fetch/fetch_muhtarlik_votes.js` /
`fetch_muhtarlik_parti.js` script'leri her `secimId` için aynı veriyi tekrar
çekebilir (bkz. `sources.yml`'deki her CB/genel/yerel/referandum girişinin
`backup[].url` alanındaki `secim_ID` değerleri). Tahmini süre: seçim başına
~650 istek × ~150ms gecikme ≈ 3-4 dakika, 15 seçim için toplam ~50-60 dakika.
Bilerek bu oturumda yapılmadı — kullanıcı isterse ayrı bir adım olarak
tetiklenebilir.

## `data/raw/haberturk/` — BOŞ

2011 sonrası genel/yerel/CB seçimleri ile 2010/2017 referandumlarının il/ilçe
düzeyi verisinin birincil kaynağı `secim.haberturk.com`. Bu sitenin kendi ham
sayfa çıktısı (HTML/JSON, hangi biçimde kazınmışsa) **hiçbir zaman bu depoda
veya `~/Desktop/2023_Secim_Verileri/`'de ayrı dosyalar olarak saklanmamış** —
dış üretim script'i muhtemelen sayfaları anlık işleyip doğrudan
`data/raw/legacy-preprocessed/`'deki toparlanmış CSV'lere yazmış, ara ham
çıktıyı tutmamış.

**Bu, yeniden üretilebilir değil** (script'in kendisi de elde yok) — sadece
işlenmiş, kaynak-karışık `legacy-preprocessed/` verisi var. Habertürk'ün
sitesi hâlâ açık olduğu için gerekirse manuel/yeni bir kazıma ile yeniden
üretilebilir ama bu depoda hazır bir script yok.

## `data/raw/wikipedia/` — BOŞ

1950-2009 arası boşlukları dolduran Türkçe Wikipedia tablolarının ham HTML'i
de aynı şekilde saklanmamış. Aynı durum: `legacy-preprocessed/`'deki
toparlanmış veri var, kaynak sayfaların kendisi yok.

## Neden bu şekilde bırakıldı

Kullanıcının önceliği "önce altyapıyı kur, mevcut veriyi bozmadan taşı" idi —
geriye dönük olarak kaybolmuş ham dosyaları yeniden kazımak (özellikle
Habertürk/Wikipedia için, script bile mevcut değil) ayrı ve önemli bir iş.
Bunu gizlemek yerine burada açıkça işaretlemek, "kaynak her zaman dürüstçe
açıklanır" ilkesiyle tutarlı. `data/raw/ysk/` için durum daha iyi: kaynak hâlâ
canlı ve script hazır, sadece bu oturumda çalıştırılmadı.

## Etkilenmeyen kısım

`data/raw/third-party/mertnuhoglu/`, `data/raw/legacy-preprocessed/` ve
`data/raw/ysk/1950-1977/` GERÇEK snapshot'lar — pinlenmiş/checksum'lı, canlı
bağımlılık yok. Bu belgedeki boşluklar sadece haberturk/wikipedia
klasörlerini ve mahalle-düzeyi ysk verisini kapsıyor.
