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
from common.election_io import load_all_elections  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "index.template.html"
STYLES = ROOT / "src" / "styles" / "main.css"
JS_DIR = ROOT / "src" / "js"
OUT = ROOT / "index.html"
DATA_NORM = ROOT / "data" / "normalized"
GEO_NORM = ROOT / "geo" / "normalized"
GEO_HIST = ROOT / "geo" / "historical"

DATA_PLACEHOLDER = '"__BUILD_WILL_INSERT_EMBEDDED_GZ_JSON__"'
CSS_PLACEHOLDER = "/*__BUILD_WILL_INSERT_CSS__*/"
JS_PLACEHOLDER = "//__BUILD_WILL_INSERT_JS__"

ERA_ADLARI = ["era1950", "era1954", "era1957_1987", "era1991", "era1995", "era1999"]

# src/js/*.js, tek bir paylasimli closure'a (async IIFE) derlenecek sekilde
# BU SIRAYLA concatenate edilir — modul degil, dogrudan metin birlestirme
# (build.py bunlari tek <script> icine "inline" eder). Sira onemli: alt
# bolumler ustteki let/const'lari referans alir (ayni async IIFE govdesinde
# calisir, fonksiyon hoisting'i sayesinde fonksiyon SIRASI onemli degil ama
# ilk calisan top-level kod olan data-loader.js'in en basta olmasi gerekir).
JS_FILES = [
    "data-loader.js", "election-config.js", "state.js", "seatbar.js",
    "summary.js", "map.js", "tooltip.js", "detail-panel.js", "search.js", "nav.js",
    "table.js", "app.js",
]


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
    secimler = load_all_elections()
    secim_tarihi_data = {"partiler": partiler, "secimler": secimler}

    mahalle_votes = {}
    for path in sorted((DATA_NORM / "mahalle").glob("*.json")):
        mahalle_votes[path.stem] = load_json(path)

    # Yil basina GERCEKTEN mahalle-duzeyi oy verisi olan ilce sayisi (mahalle_votes
    # dosyasinin ust-seviye anahtar sayisi = {geomId: {osmId:...}} seklinde) -
    # frontend'in (summary.js computeLevels()) sadece poligon (MAHALLE_GEO) degil,
    # gercek oy verisi olup olmadigini soylemesi icin kucuk, eager-yuklu bir ozet.
    mahalle_coverage = {year: len(rows) for year, rows in mahalle_votes.items()}

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
        # mahalle_geo.json TEK blok kaliyor (tum yillar arasinda paylasimli,
        # ~5MB sikistirilmis — buyumesi yeni ilce eklenince olur, yeni yil
        # eklenince degil). mahalle_votes ise YIL BASINA ayri anahtar: sayfa
        # acilisinda 15 yilin TAMAMINI (75MB acik veri) decompress etmek
        # yerine, JS sadece kullanicinin gercekten actigi yili lazy-load
        # ediyor (bkz. src/js/data-loader.js + map.js).
        "mahalle_geo.json": gzip_b64(mahalle_geo),
        "mahalle_coverage.json": gzip_b64(mahalle_coverage),
        **{f"mahalle_votes_{year}.json": gzip_b64(rows) for year, rows in mahalle_votes.items()},
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
    for placeholder in (DATA_PLACEHOLDER, CSS_PLACEHOLDER, JS_PLACEHOLDER):
        if placeholder not in template_html:
            raise SystemExit(f"Placeholder sablonda bulunamadi: {placeholder!r} ({TEMPLATE})")

    # rstrip: kaynak dosyalar standart sekilde sondaki \n ile bitiyor, ama
    # sablondaki placeholder'in KENDI satirinda zaten bir \n var — ikisini
    # birden birakmak (orijinalde olmayan) fazladan bos satir yaratir.
    css = STYLES.read_text(encoding="utf-8").rstrip("\n")
    js = "".join((JS_DIR / name).read_text(encoding="utf-8") for name in JS_FILES).rstrip("\n")
    embedded_json_str = json.dumps(embedded, ensure_ascii=False, separators=(",", ":"))

    out_html = template_html.replace(CSS_PLACEHOLDER, css, 1)
    out_html = out_html.replace(JS_PLACEHOLDER, js, 1)
    out_html = out_html.replace(DATA_PLACEHOLDER, embedded_json_str, 1)

    OUT.write_text(out_html, encoding="utf-8")
    print(f"yazildi: {OUT} ({len(out_html)} bayt)")


if __name__ == "__main__":
    main()
