"""
Yayinlanan siteyi (GitHub Pages) site/dist/ altina uretir:
  - data/, geo/  : yayin verisi (scripts/export_static.py: public_files; 'kaynak' alanlari cikarilmis)
  - index.html   : src/index.template.html + src/styles/main.css + src/js/*.js (veri gomulmez,
                   tarayici data/ ve geo/ dosyalarini fetch() ile okur; sayfa ~birkac yuz KB)
  - yontem.html, .nojekyll

Ayni on yuz (bu klasordeki src/) repo kokundeki tek dosyalik index.html'de de kullanilir:
scripts/build.py ayni yayin dosyalarini ayni yollarla sayfaya gomer, data-loader.js gomulu veri
varsa onu okur. Sabitler (TEMPLATE, JS_FILES, yer tutucular) oradan da kullanilir.

Kullanim (repo kokunden):
  python3 site/build.py            # site/dist/
  python3 site/build.py --out DIR
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
TEMPLATE = ROOT / "src" / "index.template.html"
STYLES = ROOT / "src" / "styles" / "main.css"
JS_DIR = ROOT / "src" / "js"
DIST = ROOT / "dist"

CSS_PLACEHOLDER = "/*__BUILD_WILL_INSERT_CSS__*/"
JS_PLACEHOLDER = "//__BUILD_WILL_INSERT_JS__"
GOMULU_YER = "<!--__GOMULU_VERI__-->"

# Sira onemli: alt bolumler ustteki let/const'lari referans alir (ayni async IIFE govdesinde
# calisir; ilk calisan top-level kod olan data-loader.js en basta olmali).
JS_FILES = [
    "data-loader.js", "election-config.js", "state.js", "result-utils.js", "seatbar.js",
    "summary.js", "map.js", "tooltip.js", "detail-panel.js", "search.js", "nav.js",
    "table.js", "link.js", "erisim.js", "app.js",
]


def js_metni():
    return "\n".join((JS_DIR / name).read_text(encoding="utf-8") for name in JS_FILES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DIST), help="çıktı klasörü (varsayılan: site/dist/)")
    out = pathlib.Path(ap.parse_args().out).resolve()

    sys.path.insert(0, str(REPO / "scripts"))
    from export_static import public_files  # noqa: E402

    if out.exists():
        shutil.rmtree(out)
    files = public_files(public=True)
    h = hashlib.sha256()
    for rel in sorted(files):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(files[rel], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        path.write_bytes(raw)
        h.update(rel.encode())
        h.update(hashlib.sha256(raw).digest())

    css = STYLES.read_text(encoding="utf-8")
    js = js_metni()
    h.update(js.encode())
    h.update(css.encode())
    # veri surumu: icerik ozeti, her yayinda degisir -> tarayici onbellegi (?v=) atlanir
    surum = h.hexdigest()[:10]
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace(GOMULU_YER + "\n", "")  # yalniz tek dosya surumu veri gomer
    html = html.replace(CSS_PLACEHOLDER, css, 1).replace(JS_PLACEHOLDER, js, 1)
    html = html.replace("__VERI_SURUMU__", surum).replace(
        "__YAYIN_TARIHI__", datetime.date.today().strftime("%d.%m.%Y"))
    (out / "index.html").write_text(html, encoding="utf-8")
    shutil.copyfile(ROOT / "yontem.html", out / "yontem.html")
    (out / ".nojekyll").write_text("")
    print(f"yazıldı: {out} ({len(files)} veri dosyası, index.html {len(html) / 1024:.1f} KB, veri sürümü {surum})")


if __name__ == "__main__":
    main()
