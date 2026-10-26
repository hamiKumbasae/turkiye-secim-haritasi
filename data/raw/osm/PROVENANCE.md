# OpenStreetMap — güncel mahalle/köy sınırları (81 il)

**Kaynak:** OpenStreetMap, Overpass API (`overpass-api.de`, yedek `overpass.kumi.systems`):
her il alanında (`ISO3166-2=TR-<plaka>`) `boundary=administrative`, `admin_level` 8–10 ilişkileri, `out geom`.
**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_osm_mahalle.py`.
**Çekildi:** 2026-10-21, GitHub Actions üzerinde (`.github/workflows/osm-mahalle-cek.yml`).

**Lisans:** [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) — © OpenStreetMap katkıcıları
(sitedeki diğer OSM kaynaklı mahalle sınırlarıyla aynı; bkz. `LICENSE-DATA.md`).

## İçerik

- `<plaka>.geojson`: her poligon için `{osm_id, ad, admin_level, place}`. Üye yollardan poligon
  kuruldu (dış halkalar − iç halkalar), Douglas-Peucker 0.0001° (~10 m, topoloji korunarak), 4 ondalık.
- İlçe ataması burada yok; eşleştirme betiği (`transform/tkgm_muhtarlik_esle.py`) poligonun içindeki bir
  noktayı `geo/normalized/turkiye_ilce_sinirlari.geojson` ilçelerinde arar.

## Kullanım

Sitede sınırı olmayan muhtarlıklar için TKGM'den önce denenir (OSM sınırları güncel idari mahalle,
TKGM kadastro mahallesidir). Sitedeki mevcut poligonlarla alanının %25'inden fazlası örtüşen OSM
poligonu kullanılmaz. Haritadaki anahtarı `r<osm_id>`.

# OpenStreetMap — köy/mahalle yer noktaları (`yer/`, 81 il)

**Kaynak:** OpenStreetMap, Overpass API (`overpass-api.de`, yedek `overpass.kumi.systems`): her il alanında
(`ISO3166-2=TR-<plaka>`) `place` etiketi village/hamlet/neighbourhood/quarter/suburb/town/city/
isolated_dwelling/locality/farm olan düğümler, alanlar için merkez noktası (`out center tags`).
**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_osm_yer.py`.
**Çekildi:** 2026-10-26, GitHub Actions üzerinde (`.github/workflows/osm-yer-cek.yml`, elle çalıştırılır;
runs 40239681465, 40247051287, 40251260460). Ham veri ayrıca `osm-yer-veri` dalında.

**Lisans:** [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) — © OpenStreetMap katkıcıları.

## İçerik

- `<plaka>.json`: `[{osm, tur (n/w/r), lon, lat, place, ad, adlar}]`; `adlar` bütün ad etiketleri
  (name, name:tr, old_name, alt_name, official_name, loc_name, name:ku, name:diq, name:hy ...).
  Koordinat 5 ondalık. Toplam 84.473 nokta.

## Kullanım

Yalnız eşleştirmede kullanılır, haritaya çizilmez (`transform/tkgm_muhtarlik_esle.py`, adım 4b): TKGM
birçok köyü eski adıyla tutuyor (Bismil "Akbaş" ~ TKGM "Alibociyan"). Adla eşleşmeyen muhtarlığın güncel
adlı OSM noktası boşta duran tek bir TKGM biriminin içine düşüyor ve noktanın eski/güncel adlarından biri
birimin adını tutuyorsa (ad desteği) o birim kullanılır. Bire bir değilse ya da ad desteği yoksa muhtarlık
haritada boş kalır. Sınır çizilmez; çizilen poligon TKGM'nin kendi birimidir.
