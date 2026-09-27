"""
Tarihsel sinir poligonlarindaki dikis deliklerini doldurur.

Tarihsel il (era*) ve ilce (HIST-*/HISTK-*) poligonlari bugunku poligonlarin birlesimiyle
uretildi; birlesim yerlerinde kaynak verideki kucuk bosluklar delik (interior ring) olarak
kaldi ve haritada il/ilce icinde cizgi gibi gorunuyordu (ornek: 1950-1957 Zonguldak, Kutahya,
Nigde). Dolum kurali:
  - il (era*) poligonlari: butun delikler doldurulur (bugunku il sinirlarinda hic delik yok;
    hicbir delik baska bir ili icermiyor).
  - ilce birlesimleri: yalniz bileşen bugunku ilcelerin kendi deliklerine (gol vb.) denk
    gelmeyen delikler doldurulur (dikis); bileşenlerde zaten olan delik korunur.

apply_idari_merges.py HISTK poligonlarini uretirken ayni kurali uygular (doldur_dikis).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/dikis_deliklerini_doldur.py
"""
import glob
import json
import pathlib

from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def delikleri_doldur(geom, koru=None, yabanci=None):
    """koru: bileşenlerin kendi delikleri (gol); yabanci: birlesime ait olmayan diger ilceler.
    Bunlardan birine yarisindan fazlasi denk gelen delik korunur, digerleri (dikis) doldurulur."""
    polys = []
    for p in getattr(geom, "geoms", [geom]):
        if p.geom_type != "Polygon":
            continue
        kalan = []
        for r in p.interiors:
            h = Polygon(r)
            if any(k is not None and not k.is_empty and h.intersection(k).area > 0.5 * h.area for k in (koru, yabanci)):
                kalan.append(r)
        polys.append(Polygon(p.exterior, kalan))
    return polys[0] if len(polys) == 1 else MultiPolygon(polys)


def bilesen_delikleri(geoms):
    return unary_union([Polygon(r) for g in geoms for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"
                        for r in p.interiors])


def main():
    toplam = 0
    for f in sorted(glob.glob(str(ROOT / "geo/historical/turkiye_il_sinirlari_era*.geojson"))):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        for ft in d["features"]:
            g = temiz(shape(ft["geometry"]))
            once = sum(len(p.interiors) for p in getattr(g, "geoms", [g]))
            ft["geometry"] = mapping(delikleri_doldur(g))
            toplam += once
        pathlib.Path(f).write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("il (era) delikleri dolduruldu:", toplam)

    # repodaki HIST-* ilce birlesimleri (HISTK'lar apply_idari_merges.py'de ayni kuralla uretilir)
    hp = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
    sp = json.loads((ROOT / "geo/historical/district_splits.json").read_text(encoding="utf-8"))
    parca = {e["syntheticId"]: e["hideIds"] for v in sp.values() for e in v}
    mod = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in
           json.loads((ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson").read_text(encoding="utf-8"))["features"]}
    h = json.loads(hp.read_text(encoding="utf-8"))
    dolan = 0
    for ft in h["features"]:
        i = ft["properties"]["id"]
        if i.startswith("HISTK-") or i not in parca:
            continue
        g = temiz(shape(ft["geometry"]))
        once = sum(len(p.interiors) for p in getattr(g, "geoms", [g]))
        pl = ft["properties"].get("plaka")
        yab = unary_union([v for k, v in mod.items() if k not in parca[i] and k.split("-")[2] == f"{pl:02d}"]) if pl else None
        yeni = delikleri_doldur(g, bilesen_delikleri([mod[x] for x in parca[i] if x in mod]), yab)
        dolan += once - sum(len(p.interiors) for p in getattr(yeni, "geoms", [yeni]))
        ft["geometry"] = mapping(yeni)
    hp.write_text(json.dumps(h, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("HIST-* ilce birlesimlerinde doldurulan dikis deligi:", dolan)


if __name__ == "__main__":
    main()
