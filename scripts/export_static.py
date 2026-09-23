"""
data/normalized/ + geo/normalized/ + geo/historical/ kaynaklarindan, build.py'nin
TEK-DOSYA (index.html icine gomulu gzip) modeli YERINE GECMEDEN, AYRI/granular
statik JSON dosyalari uretir - bunlar turkiye-secim-atlasi (public frontend
reposu) icin veri kaynagi olur, frontend onlari fetch() ile okur.

build.py'deki assemble_embedded() ile AYNI kaynaklari okur, ama TEK gzip blogu
yerine her parcayi kendi dosyasina yazar (offline tek-dosya build.py hala
degismeden calisir, bu script ONA EK bir cikti yolu).

Cikti (varsayilan: dist_static/, --out ile degistirilebilir):
  data/parties.json                  - parti renk/kisa-ad tablosu (partiler.json)
  data/elections/<key>.json          - HER secim (46 dosya), normalize kaydin AYNISI
  data/mahalle_votes/<year>.json     - SADECE mahalle-duzeyi oy verisi olan yillar
  geo/il_sinirlari.geojson
  geo/ilce_sinirlari.geojson
  geo/ilce_sinirlari_hist.geojson
  geo/mahalle_geo.json
  geo/mahalle_coverage.json
  geo/district_splits.json
  geo/meclis_2024.json
  geo/eras/<era>.geojson             - 6 tarihsel il-sinirlari donemi

Bu dosyalar turkiye-secim-atlasi reposunun kendi data/+geo/ klasorlerine
KOPYALANIR (elle, bkz. proje ust-duzey plani) - bu script o kopyalama islemini
YAPMAZ, sadece kaynagi URETIR.

Kullanim:
  python3 scripts/export_static.py [--out dist_static]
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common.election_io import load_all_elections  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_NORM = ROOT / "data" / "normalized"
GEO_NORM = ROOT / "geo" / "normalized"
GEO_HIST = ROOT / "geo" / "historical"

ERA_ADLARI = ["era1950", "era1954", "era1957_1987", "era1991", "era1995", "era1999"]


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist_static", help="çıktı klasörü (varsayılan: dist_static/)")
    args = ap.parse_args()
    out = ROOT / args.out

    write_json(out / "data" / "parties.json", load_json(DATA_NORM / "partiler.json"))

    secimler = load_all_elections()
    for key, record in secimler.items():
        write_json(out / "data" / "elections" / f"{key}.json", record)
    print(f"yazıldı: {len(secimler)} seçim -> {out / 'data' / 'elections'}/")

    mahalle_coverage = {}
    n_mahalle = 0
    for path in sorted((DATA_NORM / "mahalle").glob("*.json")):
        rows = load_json(path)
        write_json(out / "data" / "mahalle_votes" / path.name, rows)
        mahalle_coverage[path.stem] = len(rows)
        n_mahalle += 1
    print(f"yazıldı: {n_mahalle} yıl mahalle oy verisi -> {out / 'data' / 'mahalle_votes'}/")

    write_json(out / "geo" / "il_sinirlari.geojson", load_json(GEO_NORM / "turkiye_il_sinirlari.geojson"))
    write_json(out / "geo" / "ilce_sinirlari.geojson", load_json(GEO_NORM / "turkiye_ilce_sinirlari.geojson"))
    write_json(out / "geo" / "ilce_sinirlari_hist.geojson", load_json(GEO_HIST / "turkiye_ilce_sinirlari_hist_splits.geojson"))
    write_json(out / "geo" / "mahalle_geo.json", load_json(GEO_NORM / "mahalle_geo.json"))
    write_json(out / "geo" / "district_splits.json", load_json(GEO_HIST / "district_splits.json"))
    write_json(out / "geo" / "meclis_2024.json", load_json(DATA_NORM / "meclis_2024.json"))
    write_json(out / "geo" / "mahalle_coverage.json", mahalle_coverage)

    for name in ERA_ADLARI:
        write_json(out / "geo" / "eras" / f"{name}.geojson", load_json(GEO_HIST / f"turkiye_il_sinirlari_{name}.geojson"))
    print(f"yazıldı: {len(ERA_ADLARI)} tarihsel il-sınırları dönemi -> {out / 'geo' / 'eras'}/")

    print(f"\nTamamlandı: {out}/ altında statik veri üretildi.")


if __name__ == "__main__":
    main()
