"""
src/index.template.html + data/normalized/ + geo/normalized/ + geo/historical/
kaynaklarindan dist/index.html uretir.

v1: artik kok index.html'i OKUMUYOR — tamamen yeni raw->normalized hattindan
gercek assembly yapiyor. gzip mtime=0 ile deterministik (iki calistirma
bayt-bayt ayni cikti uretir).

Kullanim:
  python3 scripts/build.py
  python3 scripts/build.py --verify-against-legacy   # eski kok index.html ile
                                                        # JSON derin-esitlik kanit
"""
import sys
import json
import gzip
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "index.template.html"
OUT = ROOT / "dist" / "index.html"
DATA_NORM = ROOT / "data" / "normalized"
GEO_NORM = ROOT / "geo" / "normalized"
GEO_HIST = ROOT / "geo" / "historical"
LEGACY_INDEX = ROOT / "index.html"

PLACEHOLDER = '"__BUILD_WILL_INSERT_EMBEDDED_GZ_JSON__"'
START_MARKER = "window.__EMBEDDED_GZ__ = "
END_MARKER = ";\n</script>"

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

    eras = {name: load_json(GEO_HIST / f"turkiye_il_sinirlari_{name}.geojson") for name in ERA_ADLARI}

    embedded = {
        "mahalle_geo.json": gzip_b64(load_json(GEO_NORM / "mahalle_geo.json")),
        "mahalle_votes.json": gzip_b64(mahalle_votes),
        "meclis_2024.json": gzip_b64(load_json(DATA_NORM / "meclis_2024.json")),
        "secim_tarihi_data.json": gzip_b64(secim_tarihi_data),
        "turkiye_il_sinirlari.geojson": gzip_b64(load_json(GEO_NORM / "turkiye_il_sinirlari.geojson")),
        "turkiye_ilce_sinirlari.geojson": gzip_b64(load_json(GEO_NORM / "turkiye_ilce_sinirlari.geojson")),
        "district_splits.json": gzip_b64(load_json(GEO_HIST / "district_splits.json")),
        "turkiye_ilce_sinirlari_hist_splits.geojson": gzip_b64(load_json(GEO_HIST / "turkiye_ilce_sinirlari_hist_splits.geojson")),
        "eras": gzip_b64(eras),
    }
    return embedded


def extract_embedded_from_html(html: str) -> dict:
    start = html.find(START_MARKER)
    end = html.find(END_MARKER, start)
    if start == -1 or end == -1:
        raise SystemExit("window.__EMBEDDED_GZ__ blogu bulunamadi")
    return json.loads(html[start + len(START_MARKER):end])


def decompress(b64: str):
    return json.loads(gzip.decompress(base64.b64decode(b64)))


def verify_against_legacy(new_embedded: dict):
    legacy_html = LEGACY_INDEX.read_text(encoding="utf-8")
    legacy_embedded = extract_embedded_from_html(legacy_html)

    all_ok = True
    for key in legacy_embedded:
        old_val = decompress(legacy_embedded[key])
        new_val = decompress(new_embedded[key])
        ok = old_val == new_val
        all_ok &= ok
        print(f"  {'OK ' if ok else 'FARK'}  {key}")
    if not all_ok:
        raise SystemExit("KAYIPSIZLIK KANITI BASARISIZ — eski ve yeni veri arasinda fark var")
    print("KAYIPSIZLIK KANITI: TUMU GECTI (eski index.html == yeni dist/index.html, JSON derin esitlik)")


def main():
    verify = "--verify-against-legacy" in sys.argv

    embedded = assemble_embedded()

    template_html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template_html:
        raise SystemExit(f"Placeholder sablonda bulunamadi: {TEMPLATE}")
    embedded_json_str = json.dumps(embedded, ensure_ascii=False, separators=(",", ":"))
    dist_html = template_html.replace(PLACEHOLDER, embedded_json_str, 1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dist_html, encoding="utf-8")
    print(f"yazildi: {OUT} ({len(dist_html)} bayt)")

    if verify:
        verify_against_legacy(embedded)


if __name__ == "__main__":
    main()
