"""
src/index.template.html + veri kaynaklarindan dist/index.html uretir.

v0: sadece sablon/placeholder mekanizmasini kanitlar. Veri kaynagi olarak
henuz data/normalized/ KULLANMIYOR (o katman Milestone 6'da kurulacak) —
bunun yerine hala tek parca olan kok index.html'deki gomulu
window.__EMBEDDED_GZ__ blogunu oldugu gibi (yeniden sikistirmadan) okuyup
sablona yerlestiriyor. Bu, "ayni veriyi geri koy" round-trip kanitidir;
gercek normalized->build hattinin devreye girmesi Milestone 6-7'de.

Kullanim:
  python3 scripts/build.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEGACY_INDEX = ROOT / "index.html"
TEMPLATE = ROOT / "src" / "index.template.html"
OUT = ROOT / "dist" / "index.html"

PLACEHOLDER = '"__BUILD_WILL_INSERT_EMBEDDED_GZ_JSON__"'
START_MARKER = "window.__EMBEDDED_GZ__ = "
END_MARKER = ";\n</script>"


def extract_embedded_blob(html: str) -> str:
    start = html.find(START_MARKER)
    end = html.find(END_MARKER, start)
    if start == -1 or end == -1:
        raise SystemExit(f"window.__EMBEDDED_GZ__ blogu bulunamadi: {LEGACY_INDEX}")
    return html[start + len(START_MARKER):end]


def main():
    legacy_html = LEGACY_INDEX.read_text(encoding="utf-8")
    blob = extract_embedded_blob(legacy_html)

    template_html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template_html:
        raise SystemExit(f"Placeholder sablonda bulunamadi: {TEMPLATE}")
    dist_html = template_html.replace(PLACEHOLDER, blob, 1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dist_html, encoding="utf-8")
    print(f"yazildi: {OUT} ({len(dist_html)} bayt)")


if __name__ == "__main__":
    main()
