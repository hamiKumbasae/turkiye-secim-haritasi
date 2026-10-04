"""
Tek dosyalik index.html uretir: site/ on yuzu + gomulu yayin verisi (cift tiklayinca file:// ile acilir).

Sitenin tek on yuzu site/src/ altindadir; GitHub Pages surumu (site/build.py -> site/dist/) veriyi
data/, geo/ dosyalarindan fetch() ile okur. Bu betik ayni yayin dosyalarini (export_static.py:
public_files) ayni yollarla gzip+base64 olarak window.__EMBEDDED_GZ__ icine gomer; data-loader.js
gomulu veri varsa fetch yerine onu okur. Yani iki dagitim tek kod.

gzip mtime=0 ve tarih yerine icerik ozeti: ayni veriden iki calistirma bayt-bayt ayni cikti uretir
(CI 'git diff --exit-code index.html yontem.html' ile kontrol eder).

Kullanim:
  python3 scripts/build.py
"""
import base64
import gzip
import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate as _validate  # noqa: E402
from common.election_io import load_all_elections  # noqa: E402
from export_static import public_files  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "index.html"
DATA_NORM = ROOT / "data" / "normalized"
GEO_NORM = ROOT / "geo" / "normalized"
GOMULU_YER = "<!--__GOMULU_VERI__-->"
# atlas sitesinde "Son güncelleme: <bugün>"; tek dosyada tarih yerine yalniz veri surumu (deterministik)
YAYIN_TARIHI_IFADESI = "Son güncelleme: __YAYIN_TARIHI__ · "


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def gzip_b64(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # mtime=0: gzip varsayilan olarak sikistirma anini gomer; ayni veriden ayni bayt
    return base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")


def atlas_build():
    """site/build.py: sablon, CSS, JS yollari ve JS birlestirme sirasi (Pages surumuyle ayni)."""
    spec = importlib.util.spec_from_file_location("site_build", SITE / "build.py")
    mod = importlib.util.module_from_spec(spec)
    eski, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # site/ altina __pycache__ yazma
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = eski
    return mod


def on_kontrol():
    """Yapisal dogrulama (scripts/validate.py); hata varsa build durur."""
    partiler = load_json(DATA_NORM / "partiler.json")
    mahalle_votes = {p.stem: load_json(p) for p in sorted((DATA_NORM / "mahalle").glob("*.json"))}
    errors = _validate.validate_structural(
        {"partiler": partiler, "secimler": load_all_elections()}, mahalle_votes,
        load_json(GEO_NORM / "mahalle_geo.json"), load_json(DATA_NORM / "meclis_2024.json"))
    if errors:
        print(f"{len(errors)} DOGRULAMA HATASI, build durduruldu:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)


def main():
    on_kontrol()
    ab = atlas_build()
    html = ab.TEMPLATE.read_text(encoding="utf-8")
    for yer in (ab.CSS_PLACEHOLDER, ab.JS_PLACEHOLDER, GOMULU_YER, YAYIN_TARIHI_IFADESI):
        if yer not in html:
            raise SystemExit(f"Yer tutucu şablonda yok: {yer!r} ({ab.TEMPLATE})")
    css = ab.STYLES.read_text(encoding="utf-8")
    js = "\n".join((ab.JS_DIR / name).read_text(encoding="utf-8") for name in ab.JS_FILES)

    gomulu = {rel: gzip_b64(obj) for rel, obj in public_files(public=True).items()}
    veri = json.dumps(gomulu, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    surum = hashlib.sha256((veri + js + css).encode("utf-8")).hexdigest()[:10]

    html = html.replace(ab.CSS_PLACEHOLDER, css, 1).replace(ab.JS_PLACEHOLDER, js, 1)
    html = html.replace(YAYIN_TARIHI_IFADESI, "Tek dosya sürümü · ", 1).replace("__VERI_SURUMU__", surum)
    # str.replace yerine bolme: gomulu veri icinde yer tutucu gecse bile tek yere yazilir
    once, sonra = html.split(GOMULU_YER, 1)
    html = once + '<script id="embedded-data">\nwindow.__EMBEDDED_GZ__ = ' + veri + ";\n</script>" + sonra
    OUT.write_text(html, encoding="utf-8")
    # yontem.html index.html'in yaninda olmali (baglantilar goreli)
    shutil.copyfile(SITE / "yontem.html", ROOT / "yontem.html")
    print(f"yazildi: {OUT} ({len(html)} bayt, {len(gomulu)} gömülü dosya, veri sürümü {surum})")


if __name__ == "__main__":
    main()
