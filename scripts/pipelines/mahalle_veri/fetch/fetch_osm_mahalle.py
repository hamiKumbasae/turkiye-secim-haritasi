"""
OpenStreetMap'teki guncel mahalle/koy sinirlarini (boundary=administrative, admin_level 8-10) il il ceker.

Kaynak: Overpass API (overpass-api.de; yedek: overpass.kumi.systems). Il alani ISO3166-2 etiketiyle
bulunur (TR-46 ...). Uye yollar (out geom) shapely ile poligona cevrilir (outer - inner).
Lisans: ODbL 1.0, (c) OpenStreetMap katkicilari (sitedeki diger OSM sinirlariyla ayni).

Geometri sitedeki diger mahalle poligonlariyla ayni yogunlukta: Douglas-Peucker 0.0001 derece
(topoloji korunarak), 4 ondalik basamak. Ilce ataması (geomId) burada yapilmaz; eslestirme betigi
poligonun icindeki bir noktayi projenin ilce sinirlarinda arar.

Cikti: <cikti>/<plaka>.geojson; her ozellik {osm_id, ad, admin_level, place}.
Kullanim: python3 fetch_osm_mahalle.py <cikti klasoru> <plaka,plaka,...>
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

from shapely.geometry import LineString, MultiPolygon, Polygon, mapping
from shapely.ops import polygonize, unary_union
from shapely.validation import make_valid

SUNUCULAR = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
UA = "turkiye-secim-haritasi (github.com/hamiKumbasae/turkiye-secim-haritasi)"
TOLERANS = 0.0001

SORGU = """[out:json][timeout:900];
area["ISO3166-2"="TR-{plaka:02d}"]["admin_level"="4"]->.il;
rel(area.il)["boundary"="administrative"]["admin_level"~"^(8|9|10)$"];
out geom;"""


def al(sorgu, deneme=6):
    for i in range(deneme):
        url = SUNUCULAR[i % len(SUNUCULAR)]
        try:
            veri = urllib.parse.urlencode({"data": sorgu}).encode()
            req = urllib.request.Request(url, data=veri, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=960) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            print("  tekrar:", url, str(e)[:150], flush=True)
            if i == deneme - 1:
                raise
            time.sleep(30 * (i + 1))


def yuvarla(o):
    if isinstance(o, (list, tuple)):
        if o and isinstance(o[0], (int, float)):
            return [round(o[0], 4), round(o[1], 4)]
        return [yuvarla(x) for x in o]
    return o


def poligon(rel):
    dis, ic = [], []
    for m in rel.get("members", []):
        if m.get("type") != "way" or not m.get("geometry"):
            continue
        cizgi = LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
        (ic if m.get("role") == "inner" else dis).append(cizgi)
    if not dis:
        return None
    dp = list(polygonize(unary_union(dis)))
    if not dp:
        return None
    g = unary_union(dp)
    if ic:
        ip = list(polygonize(unary_union(ic)))
        if ip:
            g = g.difference(unary_union(ip))
    g = make_valid(g)
    if g.geom_type == "GeometryCollection":
        g = unary_union([p for p in g.geoms if isinstance(p, (Polygon, MultiPolygon))])
    g = g.simplify(TOLERANS, preserve_topology=True)
    if g.is_empty or g.geom_type not in ("Polygon", "MultiPolygon"):
        return None
    m = mapping(g)
    return {"type": m["type"], "coordinates": yuvarla(m["coordinates"])}


def main():
    cikti = pathlib.Path(sys.argv[1])
    cikti.mkdir(parents=True, exist_ok=True)
    for plaka in [int(p) for p in sys.argv[2].split(",")]:
        t0 = time.time()
        d = al(SORGU.format(plaka=plaka))
        ozellikler, bos = [], 0
        for el in d.get("elements", []):
            if el.get("type") != "relation":
                continue
            t = el.get("tags", {})
            g = poligon(el)
            if g is None:
                bos += 1
                continue
            ozellikler.append({"type": "Feature", "geometry": g, "properties": {
                "osm_id": el["id"], "ad": t.get("name"), "admin_level": t.get("admin_level"), "place": t.get("place")}})
        (cikti / f"{plaka:02d}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": ozellikler}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        seviye = {}
        for f in ozellikler:
            seviye[f["properties"]["admin_level"]] = seviye.get(f["properties"]["admin_level"], 0) + 1
        print(f"::notice title=OSM {plaka:02d}::{len(ozellikler)} poligon {seviye}, geometrisi kurulamayan {bos}, "
              f"{time.time() - t0:.0f} sn", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
