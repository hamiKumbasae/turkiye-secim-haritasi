"""
OpenStreetMap'teki guncel ilce sinirlarini (boundary=administrative, admin_level=6) il il ceker.

Kaynak: Overpass API (overpass-api.de; yedek: overpass.kumi.systems). Il alani ISO3166-2 etiketiyle
bulunur (TR-46 ...). Uye yollar (out geom) shapely ile poligona cevrilir (outer - inner); fetch_osm_mahalle.py
ile ayni yontem. Lisans: ODbL 1.0, (c) OpenStreetMap katkicilari.

Amac: ilce katmani (geo/normalized/turkiye_ilce_sinirlari.geojson, HDX COD-AB kaynakli) ile TKGM'nin
uyusmadigi ilcelerde bagimsiz, guncel bir ilce siniri (scripts/geo/ilce_katmani.py). Il alanina degen
komsu ilcelerin iliskileri de doner; ayni osm_id birden cok dosyada olabilir.

Geometri: Douglas-Peucker 0.0001 derece (topoloji korunarak), 4 ondalik basamak (mahalle ile ayni).
Cikti: <cikti>/<plaka>.geojson; her ozellik {osm_id, ad, admin_level, ref, wikidata}.
Kullanim: python3 fetch_osm_ilce.py <cikti klasoru> <plaka,plaka,...>
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_osm_mahalle import al, poligon  # noqa: E402

SORGU = """[out:json][timeout:900];
area["ISO3166-2"="TR-{plaka:02d}"]["admin_level"="4"]->.il;
rel(area.il)["boundary"="administrative"]["admin_level"="6"];
out geom;"""


def main():
    cikti = pathlib.Path(sys.argv[1])
    cikti.mkdir(parents=True, exist_ok=True)
    for plaka in [int(p) for p in sys.argv[2].split(",")]:
        t0 = time.time()
        d = al(SORGU.format(plaka=plaka))
        ozellikler, bos = [], 0
        for el in sorted(d.get("elements", []), key=lambda e: e.get("id", 0)):
            if el.get("type") != "relation":
                continue
            t = el.get("tags", {})
            g = poligon(el)
            if g is None:
                bos += 1
                continue
            ozellikler.append({"type": "Feature", "geometry": g, "properties": {
                "osm_id": el["id"], "ad": t.get("name"), "admin_level": t.get("admin_level"),
                "ref": t.get("ref"), "wikidata": t.get("wikidata")}})
        (cikti / f"{plaka:02d}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": ozellikler}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        print(f"::notice title=OSM ilce {plaka:02d}::{len(ozellikler)} poligon, geometrisi kurulamayan {bos}, "
              f"{time.time() - t0:.0f} sn", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
