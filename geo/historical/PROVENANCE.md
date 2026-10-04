# Tarihsel dönüşüm katmanı — KAYNAK GEOMETRİSİ DEĞİL

Bu klasördeki dosyalar `../raw/` veya `ttezer`'den doğrudan gelmiyor —
bunlar bu projenin kendi türetilmiş dönüşümü: Türkiye'nin il/ilçe sınırları
zaman içinde değiştiği (yeni iller kurulması, büyükşehir ilçelerinin
bölünmesi) için, eski seçim yıllarının haritasını çizebilmek amacıyla
GÜNCEL sınırlardan geriye doğru sentezlenmiş.

`../normalized/`'daki dosyalarla farkı: `normalized/` "şu an" için tek bir
güncel sınır kümesi, burası ise "o yıl nasıl görünüyordu" sorusuna cevap
veren BİRDEN FAZLA zaman dilimi (era) kümesi.

Kaynak: `~/Desktop/2023_Secim_Verileri/` (bu depo dışı, önceki oturum),
2026-09-22'de olduğu gibi kopyalandı. İçerik `index.html`'e gömülü
karşılıklarıyla (JSON içerik düzeyinde, serileştirme farklı olsa da)
doğrulandı — bkz. bu klasördeki `checksums.sha256` ve `../../data/
provenance/checksums.json` (tüm snapshot klasörlerinin konsolide kaydı).

## Dosyalar

- `turkiye_il_sinirlari_era1950.geojson` — 1950 seçimi zamanındaki il
  sınırları (o dönem 63 il)
- `turkiye_il_sinirlari_era1954.geojson` — 1954 (Bilecik düzeltmesi sonrası,
  64 il)
- 2026-10-04: `era1957_1965`, `era1957_1987`, `era1991`, `era1994` artık
  `scripts/pipelines/historical_geo/build_il_sinirlari.py` ile seçim verisindeki
  ilçe-il bağlılığından üretiliyor (bkz. `idari/README.md`); aşağıdaki açıklamalar
  ilk sürüm içindir.
- `turkiye_il_sinirlari_era1957_1987.geojson` — 1957-1987 arası ortak sınır
  kümesi (bu aralıkta il sayısı sabit kaldı)
- `turkiye_il_sinirlari_era1991.geojson`, `era1995.geojson`, `era1999.geojson`
  — ardından kurulan yeni illerin (Ardahan/Iğdır/Aksaray/Bayburt/Karaman/
  Kırıkkale/Batman/Şırnak vb.) sırayla eklenmesiyle değişen il sayıları
  (73→74→79→80)
- `district_splits.json` — bölünmüş/birleştirilmiş ilçelerin hangi eski
  seçim yıllarında sentetik (HIST-*) poligonla gösterilmesi gerektiğinin
  eşleme mantığı. İKİ FARKLI kaynaktan geliyor (bkz. 2026-09-23 notu):
  - plaka 34 DIŞINDAKİ 13 il: büyükşehir "Merkez" ilçelerinin 2008-2014
    bölünmeleri (örn. Antalya Merkez → Muratpaşa+Kepez) — bu isimler YSK
    kaynağında hâlâ tek bir "<İl> MERKEZ" satırı olarak geldiği için,
    `scripts/pipelines/election_import/hist_geomid.py` bunu VERİ ÇEKME
    sırasında (pipeline ingestion) otomatik çözer.
  - plaka 34 (İstanbul), `HIST-Istanbul-Buyukcekmece`/`HIST-Istanbul-Umraniye`:
    FARKLI bir mekanizma — bu ilçeler YSK kaynağında hâlâ KENDİ (Büyükçekmece/
    Ümraniye) adlarıyla geldiği için isim-çözümlemeye hiç girmiyor, veri
    satırı zaten doğru eşleşiyor ama MODERN (2008-sonrası, küçülmüş)
    sınırıyla. `scripts/pipelines/election_import/apply_verified_district_merges.py`
    bunu veri çekildikten SONRA, tek seferlik bir düzeltme adımı olarak
    uygular (idempotent, tekrar çalıştırılabilir) — hem geometriyi üretir
    hem de 1994/1999/2004 yerel'deki ilgili satırların `geomId` alanını
    günceller. Sadece TEK-EBEVEYNLİ ve birden fazla kaynaktan TUTARLI
    doğrulanmış vakalar işlendi (Beylikdüzü←Büyükçekmece, Çekmeköy←Ümraniye) —
    çok-ebeveynli (Ataşehir, Sancaktepe, Başakşehir, Sultangazi, Arnavutköy,
    Esenyurt) veya kaynakları çelişen vakalar BİLEREK atlandı, `scripts/
    audit_district_coverage.py` ile envanteri çıkarılabilir.
  - 2026-09-29: İstanbul'un 1992–2008 dönemi (1994yerel … 2007referandum) artık
    `scripts/pipelines/historical_geo/build_istanbul_1992_2008.py` ile boşluksuz
    kuruluyor (`HIST-Istanbul-*-9208`, bkz. `idari/README.md`); yukarıdaki
    mekanizmalar İstanbul için yalnız 1991'de kullanılıyor.
  - 2026-10-04: 1961–2007 seçimleri için `HIST<seçim>-*` birleşimleri
    (`scripts/pipelines/historical_geo/build_ilce_secim.py`, tablolar
    `idari/ilce_eslesme/<seçim>.csv`; bkz. `idari/README.md`).
- `turkiye_ilce_sinirlari_hist_splits.geojson` — yukarıdaki eşlemeye karşılık
  gelen, bölünmüş ilçelerin birleştirilmiş (eski hâle döndürülmüş) poligonları

## Nasıl kullanılıyor

`index.html` içindeki `GEO_ERAS` / `eras` mantığı, seçilen seçim yılına göre
il-sınırı dosyalarından uygun olanı seçip haritayı ona göre çiziyor. Davranış
bu taşımayla DEĞİŞMEDİ — sadece dosyaların diskteki konumu.

`district_splits.json` ise (2026-09-23'ten itibaren) hem Python pipeline'da
(ingestion sırasında) HEM DE doğrudan frontend'de (`frontend/src/js/map.js`,
`DISTRICT_SPLITS` embedded değişkeni) kullanılıyor — haritada bir sentetik
HIST-* poligon o yıl gerçekten kullanılıyorsa, `hideIds` alanındaki modern
ilçe id'leri (birleşimin PARÇASI oldukları için) AYRICA "veri yok" katmanında
çizilmiyor; yoksa aynı alan iki kez (bir doğru renkli, bir de yanlışlıkla
gri) görünürdü.

## `idari/` — tarihsel idari coğrafya katmanı (2026-09-25, Faz 1)

Her seçim tarihindeki il/ilçe yapısı: İçişleri Bakanlığı kuruluş tarihleri
(resmî) + seçim verisindeki ilçe kanıtı + bu klasördeki doğrulanmış `HIST-*`
birleşimleri. Olay kaydı, ilçe soy kaydı ve seçim snapshot'ları; ayrıntı ve
kurallar `idari/README.md`'de. Henüz ön yüz tarafından kullanılmıyor.
