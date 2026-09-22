"""
Hizli, yapisal dogrulama — scripts/build.py'ye gomulu bir pre-flight gate
olarak calisir (assembly sonrasi, index.html yazilmadan once). Yavas/
analitik kontroller icin bkz. tests/validate_elections.py.

Bagimsiz calistirmak icin:
  python3 scripts/validate.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_NORM = ROOT / "data" / "normalized"
GEO_NORM = ROOT / "geo" / "normalized"
SOURCES_YML = ROOT / "sources.yml"


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sources_yml_election_keys() -> set:
    text = SOURCES_YML.read_text(encoding="utf-8")
    section = text.split("elections:", 1)[1].split("geometry:", 1)[0]
    keys = set(re.findall(r'^  "([^"]+)":', section, re.M))
    keys.discard("yurtdisi-secmen")
    return keys


def validate_structural(secim_tarihi: dict, mahalle_votes: dict, mahalle_geo: dict, meclis: dict) -> list:
    """secim_tarihi = {'partiler':..., 'secimler':...} — assemble_embedded()'in
    urettigi ic-hafiza sekliyle ayni. Hata mesajlarinin listesini dondurur
    (bos liste = sorun yok)."""
    errors = []

    # 1) sources.yml'deki her anahtar, secimler'de var mi
    expected = sources_yml_election_keys()
    actual = set(secim_tarihi["secimler"].keys())
    missing = expected - actual
    extra = actual - expected
    if missing:
        errors.append(f"sources.yml'de olup secimler'de olmayan anahtarlar: {sorted(missing)}")
    if extra:
        errors.append(f"secimler'de olup sources.yml'de olmayan anahtarlar: {sorted(extra)}")

    # 2) her secimin 'iller' alani bos olmamali
    for key, secim in secim_tarihi["secimler"].items():
        iller = secim.get("iller")
        if not iller:
            errors.append(f"{key}: 'iller' bos veya yok")

    # 3) mahalle_votes'taki her ilce (geomId), mahalle_geo'da karsiligi olmali
    #    (oy verisi olup geometrisi olmayan bir ilce, haritada cizilemez demektir)
    for year_key, per_ilce in mahalle_votes.items():
        for geom_id in per_ilce:
            if geom_id not in mahalle_geo:
                errors.append(f"mahalle_votes[{year_key}][{geom_id}]: mahalle_geo'da bu ilce yok")

    # 4) mahalle_votes'taki her osm_id, o ilcenin mahalle_geo girisinde karsiligi olmali
    for year_key, per_ilce in mahalle_votes.items():
        for geom_id, osm_rows in per_ilce.items():
            geo_ilce = mahalle_geo.get(geom_id, {})
            dangling = [osm_id for osm_id in osm_rows if osm_id not in geo_ilce]
            if dangling:
                errors.append(
                    f"mahalle_votes[{year_key}][{geom_id}]: geometrisi olmayan {len(dangling)} osm_id "
                    f"(orn: {dangling[:3]})"
                )

    # 5) meclis_2024 bos olmamali
    if not meclis:
        errors.append("meclis_2024.json bos")

    return errors


def main():
    partiler = load_json(DATA_NORM / "partiler.json")
    secimler = {}
    for name in ["cumhurbaskanligi", "genel_secimler", "yerel_secimler", "referandumlar"]:
        secimler.update(load_json(DATA_NORM / f"{name}.json"))
    secim_tarihi = {"partiler": partiler, "secimler": secimler}

    mahalle_votes = {p.stem: load_json(p) for p in sorted((DATA_NORM / "mahalle").glob("*.json"))}
    mahalle_geo = load_json(GEO_NORM / "mahalle_geo.json")
    meclis = load_json(DATA_NORM / "meclis_2024.json")

    errors = validate_structural(secim_tarihi, mahalle_votes, mahalle_geo, meclis)
    if errors:
        print(f"{len(errors)} DOGRULAMA HATASI:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Yapisal dogrulama gecti, hata yok.")


if __name__ == "__main__":
    main()
