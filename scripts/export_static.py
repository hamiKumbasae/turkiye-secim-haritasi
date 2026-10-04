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
  data/meclis_harita/<yil>_<igm|bm>.json - yerel secim il genel meclisi / belediye meclisi
  geo/il_sinirlari.geojson
  geo/ilce_sinirlari.geojson
  geo/ilce_sinirlari_hist.geojson
  geo/mahalle/<geomId>.json          - ilce basina mahalle poligonlari (yalniz o ilceye inilince
                                       indirilir; tek dosya 17MB idi)
  geo/mahalle_coverage.json
  geo/district_splits.json
  geo/harita_notlari.json            - 'veri yok' poligon aciklamalari (tarihsel idari katman)
  geo/meclis_2024.json
  geo/eras/<era>.geojson             - 8 tarihsel il-sinirlari donemi

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

ERA_ADLARI = ["era1950", "era1954", "era1957_1965", "era1957_1987", "era1991", "era1994", "era1995", "era1999"]


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def without_provenance(obj):
    if isinstance(obj, dict):
        return {k: without_provenance(v) for k, v in obj.items() if k != "kaynak"}
    if isinstance(obj, list):
        return [without_provenance(v) for v in obj]
    return obj


def public_files(public=True) -> dict:
    """Yayin dosyalari: {goreli yol: JSON nesnesi}. Atlas bunlari ayri dosya olarak fetch eder;
    build.py ayni yollarla index.html'e gomer (tek on yuz, iki dagitim)."""
    files = {}

    def ekle(rel, obj):
        files[rel] = without_provenance(obj) if public else obj

    ekle("data/parties.json", load_json(DATA_NORM / "partiler.json"))
    for key, record in load_all_elections().items():
        ekle(f"data/elections/{key}.json", record)
    for path in sorted((DATA_NORM / "meclis_harita").glob("*.json")):
        ekle(f"data/meclis_harita/{path.name}", load_json(path))
    mahalle_coverage = {}
    for path in sorted((DATA_NORM / "mahalle").glob("*.json")):
        rows = load_json(path)
        ekle(f"data/mahalle_votes/{path.name}", rows)
        mahalle_coverage[path.stem] = len(rows)
    ekle("geo/il_sinirlari.geojson", load_json(GEO_NORM / "turkiye_il_sinirlari.geojson"))
    ekle("geo/ilce_sinirlari.geojson", load_json(GEO_NORM / "turkiye_ilce_sinirlari.geojson"))
    ekle("geo/ilce_sinirlari_hist.geojson", load_json(GEO_HIST / "turkiye_ilce_sinirlari_hist_splits.geojson"))
    for geom_id, rows in load_json(GEO_NORM / "mahalle_geo.json").items():
        ekle(f"geo/mahalle/{geom_id}.json", rows)
    ekle("geo/district_splits.json", load_json(GEO_HIST / "district_splits.json"))
    ekle("geo/harita_notlari.json", load_json(GEO_HIST / "idari" / "harita_notlari.json"))
    ekle("geo/meclis_2024.json", load_json(DATA_NORM / "meclis_2024.json"))
    ekle("geo/mahalle_coverage.json", mahalle_coverage)
    for name in ERA_ADLARI:
        ekle(f"geo/eras/{name}.geojson", load_json(GEO_HIST / f"turkiye_il_sinirlari_{name}.geojson"))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist_static", help="çıktı klasörü (varsayılan: dist_static/)")
    ap.add_argument("--public", action="store_true", help="kayıtlardaki kaynak alanlarını yayın kopyasından çıkar")
    args = ap.parse_args()
    out = ROOT / args.out
    files = public_files(args.public)
    for rel, obj in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    sayac = {}
    for rel in files:
        k = "/".join(rel.split("/")[:2]) if rel.count("/") > 1 else rel
        sayac[k] = sayac.get(k, 0) + 1
    for k, n in sorted(sayac.items()):
        print(f"yazıldı: {n:4d}  {k}")
    print(f"\nTamamlandı: {out}/ altında {len(files)} statik veri dosyası üretildi.")


if __name__ == "__main__":
    main()
