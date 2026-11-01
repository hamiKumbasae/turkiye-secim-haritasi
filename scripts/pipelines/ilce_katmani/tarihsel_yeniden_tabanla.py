"""
Guncel ilce katmani yeniden uretildikten sonra (build_ilce_katmani.py) tarihsel sinirlari yeni tabana tasir.

Tarihsel ilce birlesimleri (geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson: HIST-*, HISTK-*,
HISTY-*, HIST<secim>-*) bugunku ilcelerin birlesimidir; parcalari district_splits.json'daki hideIds.
  - Parcalarindan biri Istanbul'da (korunan il, bkz. build_ilce_katmani.py) olan kayit degismez: Istanbul
    ilceleri aynen korundu, Istanbul'un mahalle duzeyinde bolusulmus tarihsel ilceleri onlara gore kuruldu.
  - Oteki kayitlar, eski poligon eski parcalarinin birlesimiyle ayniysa (simetrik fark < %1), yeni
    parcalarin birlesimiyle degistirilir (yeni parcalarla zaten ayniysa da: betik yeniden calistirilabilir). Ayni degilse (mahalle duzeyinde bolusum ya da parcalardan tasma)
    degismez ve listelenir.
  Uretim betiklerinin (tarihsel_sinirlari_uret.py) kendisi yeniden calistirilmaz: secim verisine de yazan
  adimlari var ve 2026-10-31 mahalle duzeltmesinden sonra Istanbul adimi calismiyor.

Donem il sinirlari: era1950 ... era1994 build_il_sinirlari.py ile secim verisinden yeniden uretilir (bu betik
cagirir). era1995 ve era1999 (o betigin uretmedigi iki dosya): her bugunku ilce, eski donem dosyasinda alaninin
en cok dustugu ile verilir ve il il birlestirilir (ilce-il bagliligi eski dosyayla ayni kalir).

Kullanim (repo kokunden): python3 scripts/pipelines/ilce_katmani/tarihsel_yeniden_tabanla.py --eski <eski turkiye_ilce_sinirlari.geojson>
  --eski: degisiklikten onceki guncel ilce dosyasi (git show main:geo/normalized/turkiye_ilce_sinirlari.geojson).
"""
import argparse
import collections
import json
import pathlib
import subprocess
import sys

import shapely
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_ilce_katmani import KORUNAN_IL, geojson_geom, oku, poligonal  # noqa: E402

GEO = ROOT / "geo/normalized"
HIST = ROOT / "geo/historical"
HIST_GEO = HIST / "turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = HIST / "district_splits.json"
ESIK = 0.01


def yaz(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--eski", required=True)
    a = ap.parse_args()
    eski = {f["properties"]["id"]: poligonal(shape(f["geometry"])) for f in oku(a.eski)["features"]}
    yeni_f = oku(GEO / "turkiye_ilce_sinirlari.geojson")["features"]
    yeni = {f["properties"]["id"]: poligonal(shape(f["geometry"])) for f in yeni_f}
    parca = {}
    for lst in oku(SPLITS).values():
        for e in lst:
            parca[e["syntheticId"]] = e["hideIds"]
    hd = oku(HIST_GEO)
    say = collections.Counter()
    kalan = []
    for f in hd["features"]:
        gid = f["properties"]["id"]
        p = parca.get(gid)
        if not p or any(x not in yeni for x in p):
            say["parcasi bilinmiyor"] += 1
            kalan.append((gid, "parcasi bilinmiyor"))
            continue
        if any(int(x.split("-")[2]) in KORUNAN_IL for x in p):
            say["Istanbul (korunan)"] += 1
            continue
        h = poligonal(shape(f["geometry"]))
        # eski parcalarla ayni (ilk calistirma) ya da yeni parcalarla ayni (yeniden calistirma: degismez)
        fark = min(h.symmetric_difference(u).area / (u.area or 1)
                   for u in (shapely.union_all([eski[x] for x in p]), shapely.union_all([yeni[x] for x in p])))
        if fark >= ESIK:
            say["parcalarin birlesimi degil"] += 1
            kalan.append((gid, f"eski parcalarla simetrik fark %{fark * 100:.2f}"))
            continue
        f["geometry"] = geojson_geom(shapely.union_all([yeni[x] for x in p]))
        say["yeni parcalarla"] += 1
    yaz(HIST_GEO, hd)
    print("tarihsel ilce:", dict(say))
    for k, n in kalan:
        print("  degismedi:", k, n)

    r = subprocess.run([sys.executable, str(ROOT / "scripts/pipelines/historical_geo/build_il_sinirlari.py")],
                       cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "", r.stderr[-500:])
    if r.returncode:
        raise SystemExit("build_il_sinirlari.py hata")

    y_ids = sorted(yeni)
    for era in ("era1995", "era1999"):
        p = HIST / f"turkiye_il_sinirlari_{era}.geojson"
        d = oku(p)
        iller = [(ft["properties"], poligonal(shape(ft["geometry"]))) for ft in d["features"]]
        agac = STRtree([g for _, g in iller])
        grup = collections.defaultdict(list)
        for i in y_ids:
            j = agac.query(yeni[i], predicate="intersects")
            en = max(j, key=lambda x: (iller[x][1].intersection(yeni[i]).area, -x))
            grup[en].append(yeni[i])
        for k, ft in enumerate(d["features"]):
            if k not in grup:
                raise SystemExit(f"{era}: ilcesi kalmayan il {ft['properties']}")
            ft["geometry"] = geojson_geom(shapely.union_all(grup[k]))
        yaz(p, d)
        print(f"{era}: {len(d['features'])} il, bugunku ilcelerden")


if __name__ == "__main__":
    main()
