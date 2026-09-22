"""
Kok index.html'deki (henuz dokunulmamis, tek kaynak) window.__EMBEDDED_GZ__
verisini data/normalized/ ve geo/normalized/ altina TUR BAZINDA, KAYIPSIZ
olarak ayristirir. Hicbir deger degistirilmez — sadece dosya konumu/gruplama.

Kullanim:
  python3 scripts/normalize.py
"""
import json
import gzip
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEGACY_INDEX = ROOT / "index.html"
DATA_OUT = ROOT / "data" / "normalized"
GEO_OUT = ROOT / "geo" / "normalized"

START_MARKER = "window.__EMBEDDED_GZ__ = "
END_MARKER = ";\n</script>"


def decompress(b64: str):
    return json.loads(gzip.decompress(base64.b64decode(b64)))


def classify(key: str) -> str:
    if key.endswith("cb") or "cb1tur" in key or "cb2tur" in key:
        return "cumhurbaskanligi"
    if key.endswith("yerel"):
        return "yerel_secimler"
    if key.endswith("referandum"):
        return "referandumlar"
    return "genel_secimler"


def write_json(path: pathlib.Path, obj) -> int:
    # Kompakt (indent yok): bu boyuttaki dosyalar (mahalle geometrisi/oyu
    # onlarca MB) zaten satir satir elle okunmuyor — indent sadece bayt
    # sismesi yaratiyor (17MB -> 44MB gibi). Asil "normalized" faydasi tur/
    # yila gore ayri dosyalara bolunmus olmasi, girinti degil.
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    path.write_text(text, encoding="utf-8")
    return len(text)


def main():
    html = LEGACY_INDEX.read_text(encoding="utf-8")
    start = html.find(START_MARKER)
    end = html.find(END_MARKER, start)
    gz_obj = json.loads(html[start + len(START_MARKER):end])

    # 1) secim_tarihi_data.json -> partiler.json + 4 tur-bazli dosya
    std = decompress(gz_obj["secim_tarihi_data.json"])
    write_json(DATA_OUT / "partiler.json", std["partiler"])

    buckets = {"cumhurbaskanligi": {}, "genel_secimler": {}, "yerel_secimler": {}, "referandumlar": {}}
    for key, secim in std["secimler"].items():
        buckets[classify(key)][key] = secim
    for name, obj in buckets.items():
        n = write_json(DATA_OUT / f"{name}.json", obj)
        print(f"  data/normalized/{name}.json: {len(obj)} secim, {n} bayt")

    # 2) mahalle_votes.json -> data/normalized/mahalle/<yil>.json (yil basina)
    mahalle_votes = decompress(gz_obj["mahalle_votes.json"])
    for year_key, per_ilce in mahalle_votes.items():
        n = write_json(DATA_OUT / "mahalle" / f"{year_key}.json", per_ilce)
        print(f"  data/normalized/mahalle/{year_key}.json: {len(per_ilce)} ilce, {n} bayt")

    # 3) meclis_2024.json -> data/normalized/meclis_2024.json
    meclis = decompress(gz_obj["meclis_2024.json"])
    n = write_json(DATA_OUT / "meclis_2024.json", meclis)
    print(f"  data/normalized/meclis_2024.json: {n} bayt")

    # 4) mahalle_geo.json -> geo/normalized/mahalle_geo.json (geometri, oy degil)
    mahalle_geo = decompress(gz_obj["mahalle_geo.json"])
    n = write_json(GEO_OUT / "mahalle_geo.json", mahalle_geo)
    print(f"  geo/normalized/mahalle_geo.json: {len(mahalle_geo)} ilce, {n} bayt")

    # NOT: turkiye_il_sinirlari.geojson, turkiye_ilce_sinirlari.geojson,
    # district_splits.json, turkiye_ilce_sinirlari_hist_splits.geojson ve
    # eras (= 6 era*.geojson) zaten geo/normalized/ ve geo/historical/'da,
    # icerik duzeyinde dogrulanmis halde mevcut (bkz. o klasorlerin
    # PROVENANCE.md'si) — burada tekrar yazilmiyor.

    print("normalize.py tamamlandi.")


if __name__ == "__main__":
    main()
