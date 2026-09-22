"""
src/index.template.html + data/normalized/ + geo/normalized/ + geo/historical/
kaynaklarindan index.html uretir (repo kokunde — GitHub'dan indirip cift
tiklayarak acmak icin, ayrica GitHub Pages "Deploy from branch" kok dizin
modunu de destekler).

gzip mtime=0 ile deterministik: ayni veriden iki calistirma bayt-bayt ayni
cikti uretir.

Kullanim:
  python3 scripts/build.py
"""
import json
import gzip
import base64
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate as _validate  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "index.template.html"
OUT = ROOT / "index.html"
DATA_NORM = ROOT / "data" / "normalized"
GEO_NORM = ROOT / "geo" / "normalized"
GEO_HIST = ROOT / "geo" / "historical"

PLACEHOLDER = '"__BUILD_WILL_INSERT_EMBEDDED_GZ_JSON__"'

TUR_DOSYALARI = ["cumhurbaskanligi", "genel_secimler", "yerel_secimler", "referandumlar"]
ERA_ADLARI = ["era1950", "era1954", "era1957_1987", "era1991", "era1995", "era1999"]


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def gzip_b64(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # mtime=0: gzip varsayilan olarak sikistirma anini gomer, bu da ayni
    # veriden iki farkli build'de farkli bayt uretir. mtime=0 ile deterministik.
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    return base64.b64encode(compressed).decode("ascii")


def assemble_embedded() -> dict:
    partiler = load_json(DATA_NORM / "partiler.json")
    secimler = {}
    for name in TUR_DOSYALARI:
        secimler.update(load_json(DATA_NORM / f"{name}.json"))
    secim_tarihi_data = {"partiler": partiler, "secimler": secimler}

    mahalle_votes = {}
    for path in sorted((DATA_NORM / "mahalle").glob("*.json")):
        mahalle_votes[path.stem] = load_json(path)

    mahalle_geo = load_json(GEO_NORM / "mahalle_geo.json")
    meclis_2024 = load_json(DATA_NORM / "meclis_2024.json")

    # Pre-flight gate: sikistirip yazmadan once yapisal dogrulama (bkz.
    # scripts/validate.py). Hata varsa build burada durur.
    errors = _validate.validate_structural(secim_tarihi_data, mahalle_votes, mahalle_geo, meclis_2024)
    if errors:
        print(f"{len(errors)} DOGRULAMA HATASI, build durduruldu:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)

    eras = {name: load_json(GEO_HIST / f"turkiye_il_sinirlari_{name}.geojson") for name in ERA_ADLARI}

    embedded = {
        "mahalle_geo.json": gzip_b64(mahalle_geo),
        "mahalle_votes.json": gzip_b64(mahalle_votes),
        "meclis_2024.json": gzip_b64(meclis_2024),
        "secim_tarihi_data.json": gzip_b64(secim_tarihi_data),
        "turkiye_il_sinirlari.geojson": gzip_b64(load_json(GEO_NORM / "turkiye_il_sinirlari.geojson")),
        "turkiye_ilce_sinirlari.geojson": gzip_b64(load_json(GEO_NORM / "turkiye_ilce_sinirlari.geojson")),
        "district_splits.json": gzip_b64(load_json(GEO_HIST / "district_splits.json")),
        "turkiye_ilce_sinirlari_hist_splits.geojson": gzip_b64(load_json(GEO_HIST / "turkiye_ilce_sinirlari_hist_splits.geojson")),
        "eras": gzip_b64(eras),
    }
    return embedded


def main():
    embedded = assemble_embedded()

    template_html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template_html:
        raise SystemExit(f"Placeholder sablonda bulunamadi: {TEMPLATE}")
    embedded_json_str = json.dumps(embedded, ensure_ascii=False, separators=(",", ":"))
    out_html = template_html.replace(PLACEHOLDER, embedded_json_str, 1)

    OUT.write_text(out_html, encoding="utf-8")
    print(f"yazildi: {OUT} ({len(out_html)} bayt)")


if __name__ == "__main__":
    main()
