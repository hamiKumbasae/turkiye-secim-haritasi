# Geometri ham kaynakları — pin bilgisi (dosyaların KENDİSİ değil)

Bu klasör kasıtlı olarak neredeyse boş: hem `ttezer/turkiye-harita-verisi`
(~488MB depo) hem de OpenStreetMap Türkiye `.osm.pbf` özütü (~647MB) bu
depoya sığmayacak kadar büyük. Burada sadece **hangi commit/tarihe
pinlendiği** ve **nasıl yeniden indirileceği** kayıtlı.

## ttezer/turkiye-harita-verisi

- Repo: `https://github.com/ttezer/turkiye-harita-verisi`
- **Dürüst boşluk:** Bu projede kullanılan il/ilçe/mahalle geometrisi önceki
  bir oturumda çekildi ve o an hangi commit'in kullanıldığı kayıt altına
  alınmamıştı. Aşağıdaki pin, o orijinal fetch'in DEĞİL, **2026-09-22'de
  bu belgenin yazıldığı andaki** `master` HEAD'inin kaydı:
  - commit: `83eeb7a1e0a476dde81ada1a62f803231cf16e61`
  - tarih: 2026-07-08T07:00:34Z
- Bu, geriye dönük birebir yeniden üretilebilirliği garanti etmiyor (repo bu
  tarihten sonra değişmiş olabilir). Ama **doğruluk etkilenmiyor**: asıl
  kullanılan çıktı (`geo/normalized/turkiye_il_sinirlari.geojson` ve
  `turkiye_ilce_sinirlari.geojson`) `index.html`'e gömülü olanla byte-hash
  düzeyinde karşılaştırılıp doğrulandı (2026-09-22) — pin sadece "sıfırdan
  yeniden üretmek istersen buradan başla" bilgisi, mevcut verinin kanıtı
  değil.

Yeniden indirmek için:
```bash
curl -sL https://codeload.github.com/ttezer/turkiye-harita-verisi/tar.gz/83eeb7a1e0a476dde81ada1a62f803231cf16e61 -o ttezer.tar.gz
```

- **İl/ilçe katmanının asıl kaynağı:** depodaki `source/hdx/cod-ab-tur/` (HDX COD-AB-TUR, OCHA, lisans
  CC BY-IGO; HDX meta veri tarihi 2026-04-07, indirme 2026-04-10) ve ondan üretilen
  `dist/geojson/districts.geojson`. 2026-11-01'de bu commit'ten yeniden indirildi; dosyanın sha256'sı
  `16fb6b98e6ce800b43334326a7d737d172beb1c2fecb4dca71a61c5d2af067ad` (973 ilçe, 663.098 nokta, komşu
  ilçeler birebir ortak sınırlı). `scripts/pipelines/ilce_katmani/build_ilce_katmani.py --ham <bu dosya>`
  sha256'yı sınar. Bkz. `../normalized/PROVENANCE.md`.

## OpenStreetMap Türkiye (mahalle poligonları için)

- `osadikoglu/turkey-admin-units-osm` (`https://github.com/osadikoglu/turkey-admin-units-osm`)
  — küçük, sadece admin_level=8 OSM relation ID'lerinin bir indeksi (geometri
  içermiyor), pipeline'da `scripts/pipelines/mahalle_veri/eslesme/01_osm_mahalle_poligonlari.py`
  tarafından kullanılıyor.
- Asıl geometri **Geofabrik'in Türkiye `.osm.pbf` özütünden** (`osmium
  tags-filter` + `osmium export` ile işlenerek) çıkarıldı. **Dürüst boşluk:**
  hangi tarihli özütün indirildiği kayıt altına alınmamış — Geofabrik günlük
  güncellenen bir servis olduğu için geriye dönük "o gün" dosyasını tekrar
  indirmek mümkün değil, sadece güncel özüt indirilebilir:
  `https://download.geofabrik.de/europe/turkey-latest.osm.pbf`

## Neden dosyaların kendisi burada değil

647MB (OSM) + 488MB (ttezer repo) bu deponun toplam boyutunu ~10 kat
büyütürdü — "tek dosya indir, çift tıkla çalışsın" felsefesiyle ve `.git`
şişmesini önleme hedefiyle çelişir. Onun yerine asıl KULLANILAN, çok daha
küçük türetilmiş çıktı `geo/normalized/`'da saklanıyor (bkz. o klasörün
PROVENANCE.md'si).
