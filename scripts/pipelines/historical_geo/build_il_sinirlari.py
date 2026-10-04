"""
Donem il sinirlarini (geo/historical/turkiye_il_sinirlari_<era>.geojson) secim verisindeki ilce-il
bagliligindan uretir: her ilin poligonu, o secimde o ilin satirlarina bagli bugunku ilcelerin
birlesimidir (ilce satirlarinin poligonlari ve tarihsel birlesimleri; build_ilce_secim.py sonrasi
her bugunku ilce bir satira bagli). Boylece il haritasi ilce haritasiyla birebir ortusur.

Onceki elle uretilmis donem dosyalarinda bazi ilceler yanlis ildeydi (ornek 1957-1987: Cizre, Idil,
Silopi, Gercus, Hasankeyf Siirt'te; 1990'a kadar Mardin'e bagliydilar. Beytussebap ve Uludere Siirt'te;
Hakkari'ye bagliydilar. Agacoren ve Saryahsi Nigde'de; Ankara/Serefikochisar'a bagliydilar) ve 1994
yerel icin dosya yoktu (Ardahan ve Igdir Kars icinde).

Donemler (src/js/map.js -> GEO_ERAS ile ayni):
  era1957_1965  <- 1961        1958-1965 (Kaynarca Kocaeli'de; 1969'dan Sakarya)
  era1957_1987  <- 1987        1957 ve 1966-1990
  era1991       <- 1991        1991-1993
  era1994       <- 1994yerel   1994 (Bartin, Ardahan, Igdir il)
era1950, era1954 (ilce verisi yok), era1995, era1999 (zaten ilce verisiyle ortusuyor) degismez.

Bugunku ilce secimde hicbir satira bagli degilse onceki donem dosyasindaki ili kullanilir.
Delikler (dikis) doldurulur; bugunku il sinirlarinda delik yok.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_il_sinirlari.py
"""
import collections
import json
import pathlib
import sys

import shapely
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from common.election_io import load_election  # noqa: E402
from dikis_deliklerini_doldur import delikleri_doldur  # noqa: E402

GEO_HIST = ROOT / "geo/historical"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
SPLITS = GEO_HIST / "district_splits.json"
DONEMLER = {"era1957_1965": "1961", "era1957_1987": "1987", "era1991": "1991", "era1994": "1994yerel"}
# ilce satiri olmayan bugunku ilce icin yedek donem dosyasi
YEDEK = {"era1957_1965": "era1957_1987", "era1957_1987": "era1957_1987", "era1991": "era1991",
         "era1994": "era1995"}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def main():
    modern = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in oku(MODERN)["features"]}
    hide = {e["syntheticId"]: set(e["hideIds"]) for v in oku(SPLITS).values() for e in v}
    yedek_bellek = {}
    for era, secim in DONEMLER.items():
        rec = load_election(secim)
        iller = {i["plaka"] for i in rec["iller"]}
        il_of = {}
        for r in rec["ilceler"]:
            g = r.get("geomId")
            if not g or r["plaka"] not in iller:
                continue
            for x in hide.get(g, {g}):
                if x in modern:
                    il_of.setdefault(x, r["plaka"])
        eksik = [g for g in modern if g not in il_of]
        if eksik:
            yp = GEO_HIST / f"turkiye_il_sinirlari_{YEDEK[era]}.geojson"
            if yp not in yedek_bellek:
                yedek_bellek[yp] = [(f["properties"]["plaka"], temiz(shape(f["geometry"]))) for f in oku(yp)["features"]]
            for g in eksik:
                il_of[g] = max(yedek_bellek[yp], key=lambda pg: pg[1].intersection(modern[g]).area)[0]
        parcalar = collections.defaultdict(list)
        for g, p in il_of.items():
            parcalar[p].append(modern[g])
        feats = []
        for p in sorted(parcalar):
            u = delikleri_doldur(unary_union(parcalar[p]))
            u = shapely.set_precision(u, 1e-5)
            feats.append({"type": "Feature", "properties": {"plaka": p}, "geometry": mapping(u)})
        out = GEO_HIST / f"turkiye_il_sinirlari_{era}.geojson"
        out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False,
                                  separators=(",", ":")), encoding="utf-8")
        print(f"{era} <- {secim}: {len(feats)} il (seçimde {len(iller)}), yedekten {len(eksik)} ilçe")


if __name__ == "__main__":
    main()
