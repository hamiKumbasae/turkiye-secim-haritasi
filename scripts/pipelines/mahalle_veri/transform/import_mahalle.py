"""
Bu pipeline'in ciktisini (build_mahalle_aday_bazli.py veya
build_mahalle_parti_bazli.py'nin urettigi mahalle_<yil>.json) dogru yerlere
otomatik olarak yerlestirir:
  - oy verisi -> data/normalized/mahalle/<yil_anahtari>.json
  - geometri  -> geo/normalized/mahalle_geo.json'a osm_id bazinda EKLENIR
    (var olan diger yillarin geometrisi korunur, sadece yeni/degisen osm_id'ler
    guncellenir — geometri paylasimli, yil basina degil)

Elle kopyala-yapistir yerine gecti — "yeni bir seçim eklerken data/normalized/
mahalle/... ve geo/normalized/mahalle_geo.json'a elle ekleyin" talimati
hataya acikti (bkz. scripts/pipelines/mahalle_veri/README.md eski hali).

Girdi formati (build_mahalle_*.py ciktisi):
  {geomId: [{id, ad, geometry, secmen, sandik, katilim, kazanan, oy}, ...]}

Kullanim:
  python3 import_mahalle.py --year 2028 --input mahalle_2028.json
  python3 import_mahalle.py --year 2028 --input mahalle_2028.json --build
    (son adimda scripts/build.py'yi de calistirir)
"""
import argparse
import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
DATA_NORM = REPO_ROOT / "data" / "normalized"
GEO_NORM = REPO_ROOT / "geo" / "normalized"


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", required=True, help="secim anahtari, orn. 2028cb, 2028yerel")
    ap.add_argument("--input", required=True, type=pathlib.Path, help="build_mahalle_*.py ciktisi mahalle_<yil>.json")
    ap.add_argument("--build", action="store_true", help="basariliysa scripts/build.py'yi de calistir")
    args = ap.parse_args()

    data = load_json(args.input)

    geo_path = GEO_NORM / "mahalle_geo.json"
    geo = load_json(geo_path) if geo_path.exists() else {}

    votes = {}
    new_osm_ids = 0
    for geom_id, rows in data.items():
        geo.setdefault(geom_id, {})
        vote_rows = {}
        for r in rows:
            osm_id = r["id"]
            if osm_id not in geo[geom_id]:
                geo[geom_id][osm_id] = {"ad": r["ad"], "geometry": r["geometry"]}
                new_osm_ids += 1
            vote_rows[osm_id] = {
                "secmen": r["secmen"], "sandik": r["sandik"], "katilim": r["katilim"],
                "kazanan": r["kazanan"], "oy": r["oy"],
            }
        votes[geom_id] = vote_rows

    votes_path = DATA_NORM / "mahalle" / f"{args.year}.json"
    write_json(votes_path, votes)
    write_json(geo_path, geo)

    print(f"yazildi: {votes_path} ({len(votes)} ilce)")
    print(f"guncellendi: {geo_path} (+{new_osm_ids} yeni osm_id)")

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import validate as _validate  # noqa: E402

    partiler = load_json(DATA_NORM / "partiler.json")
    secimler = {}
    for name in ["cumhurbaskanligi", "genel_secimler", "yerel_secimler", "referandumlar"]:
        secimler.update(load_json(DATA_NORM / f"{name}.json"))
    secim_tarihi = {"partiler": partiler, "secimler": secimler}
    mahalle_votes = {p.stem: load_json(p) for p in sorted((DATA_NORM / "mahalle").glob("*.json"))}
    meclis = load_json(DATA_NORM / "meclis_2024.json")

    errors = _validate.validate_structural(secim_tarihi, mahalle_votes, geo, meclis)
    if errors:
        print(f"\n{len(errors)} DOGRULAMA HATASI:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("\nDogrulama gecti.")

    if args.build:
        subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "build.py")], cwd=REPO_ROOT, check=True)


if __name__ == "__main__":
    main()
