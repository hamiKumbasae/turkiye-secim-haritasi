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
