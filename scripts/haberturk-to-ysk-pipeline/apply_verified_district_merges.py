"""
scripts/audit_district_coverage.py'nin ortaya cikardigi "eksik modern ilce"
listesinden, YUKSEK GUVENLE dogrulanmis vakalari gercek tarihsel poligon
birlesimiyle duzeltir. Iki farkli girdi turu isler:

  1. VERIFIED_MERGES (Python, bu dosyada): TEK-EBEVEYNLI, butun bir cocuk
     ilcenin TAMAMININ tek bir eski ilceden ayrildigi, birden fazla kaynakla
     dogrulanmis basit vakalar (Beylikduzu<-Buyukcekmece, Cekmekoy<-Umraniye).

  2. geo/historical/district_mahalle_merges.yaml, confidence: verified
     olan girisler: COK-EBEVEYNLI (bir yeni ilcenin mahalleleri BIRDEN FAZLA
     eski ilceden geldigi) vakalar - kanunun EKLI LISTESINDEKI (resmi, 5747
     sayili kanun) mahalle isimleri GUNCEL mahalle_geo.json ile TAM (kalintisiz)
     eslestirilebildiginde islenir (bkz. o dosyanin basindaki aciklama).
     confidence: partial/research_needed olan girisler BU SCRIPT TARAFINDAN
     ATLANIR - sadece dokumantasyon/ileride-isleme-icin kayit olarak durur.

Her iki turde de deger (oy/katilim/vs.) DEGISTIRILMEZ, sadece hangi
poligonla eslendigi (geomId alani) degisir - gercek, zaten dogrulanmis oy
sayilarinin GORSEL OLARAK dogru (tarihsel) alanda gosterilmesini saglar.

Bir eski ilce (orn. Umraniye) BIRDEN FAZLA kaynaktan parca alabilir (hem
Cekmekoy'un TAMAMINDAN hem Atasehir'in BAZI mahallelerinden) - script butun
katkilari TEK bir birlestirme islemine toplar (iki ayri/celisen sentetik
poligon URETMEZ).

Kullanim:
  python3 scripts/haberturk-to-ysk-pipeline/apply_verified_district_merges.py

Gereksinim: sadece geometri URETIMI icin shapely+pyyaml gerekir (bir kerelik,
dev-time). Sentetik id'ler/geometri bir kere URETILIP diske YAZILDIGI icin
build.py/CI hicbir zaman bu bagimliliklara ihtiyac duymaz.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

GEO_NORM = ROOT / "geo" / "normalized" / "turkiye_ilce_sinirlari.geojson"
MAHALLE_GEO = ROOT / "geo" / "normalized" / "mahalle_geo.json"
HIST_GEO = ROOT / "geo" / "historical" / "turkiye_ilce_sinirlari_hist_splits.geojson"
DISTRICT_SPLITS = ROOT / "geo" / "historical" / "district_splits.json"
MAHALLE_MERGES_YAML = ROOT / "geo" / "historical" / "district_mahalle_merges.yaml"

# ---------------- tek-ebeveynli, basit vakalar (kanun + coklu kaynak dogrulamasi) ----------------
VERIFIED_MERGES = [
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-014",  # Buyukcekmece
        "whole_child_geomids": ["TR-D-34-012"],  # Beylikduzu (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Buyukcekmece",
        "split_year": 2008,
        "affected_years": ["1994yerel", "1999yerel", "2004yerel"],
    },
    {
        "plaka": 34,
        "old_district_geomid": "TR-D-34-037",  # Umraniye
        "whole_child_geomids": ["TR-D-34-016"],  # Cekmekoy (TAMAMI)
        "synthetic_id": "HIST-Istanbul-Umraniye",
        "split_year": 2008,
        "affected_years": ["1994yerel", "1999yerel", "2004yerel"],
    },
]


def load_yaml_verified_sources():
    """district_mahalle_merges.yaml'daki confidence:verified girislerini,
    VERIFIED_MERGES ile AYNI ic-modele (old_district_geomid -> katkilar)
    donusturur. pyyaml yoksa bos liste doner (script geometri adimini
    atlar, data-patch adimi zaten calisir durumdaki HIST-* id'lere dokunmaz)."""
    try:
        import yaml
    except ImportError:
        print("UYARI: pyyaml kurulu degil - district_mahalle_merges.yaml okunamadi "
              "(mahalle-bazli birlesimler atlandi, sadece VERIFIED_MERGES islendi). "
              "`pip install pyyaml` ile kurup tekrar calistirabilirsiniz.")
        return []

    doc = yaml.safe_load(MAHALLE_MERGES_YAML.read_text(encoding="utf-8"))
    out = []
    for group_key, group in doc.items():
        split_year = group.get("split_year")
        affected_years = group.get("affected_years", [])
        for district_key, entry in group.items():
            if not isinstance(entry, dict) or entry.get("confidence") != "verified":
                continue
            new_geomid = entry["new_district_geomid"]
            for src in entry["sources"]:
                name_ascii = (src["old_district_name"]
                              .replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g")
                              .replace("Ü", "U").replace("ü", "u").replace("Ş", "S").replace("ş", "s")
                              .replace("Ö", "O").replace("ö", "o").replace("Ç", "C").replace("ç", "c"))
                out.append({
                    "old_district_geomid": src["old_district_geomid"],
                    "mahalle_source_geomid": new_geomid,  # hangi (yeni) ilcenin mahalle_geo'sundan cekilecek
                    "mahalle_names": src["mahalle_names"],
                    "fully_covered_new_geomid": new_geomid,  # bu id, TUM mahalleleri baska ebeveynlere dagitildigi icin ayrica "veri yok" gosterilmemeli
                    "synthetic_id": f"HIST-Istanbul-{name_ascii}",
                    "split_year": split_year,
                    "affected_years": affected_years,
                    "plaka": 34,
                })
    return out


def gather_contributions():
    """old_district_geomid -> {synthetic_id, split_year, affected_years, plaka,
    whole_child_geomids: set, mahalle_pieces: [(source_geomid, [names])], hide: set}"""
    by_old = {}

    def ensure(m):
        old = m["old_district_geomid"]
        if old not in by_old:
            by_old[old] = {
                "synthetic_id": m.get("synthetic_id") or f"HIST-Istanbul-{old.split('-')[-1]}",
                "split_year": m["split_year"],
                "affected_years": list(m["affected_years"]),
                "plaka": m["plaka"],
                "whole_child_geomids": set(),
                "mahalle_pieces": [],
                "hide": {old},  # ebeveynin KENDI eski modern sekli her zaman gizlenir (artik sentetige esleniyor)
            }
        return by_old[old]

    for m in VERIFIED_MERGES:
        c = ensure(m)
        c["whole_child_geomids"].update(m["whole_child_geomids"])
        c["hide"].update(m["whole_child_geomids"])

    for m in load_yaml_verified_sources():
        c = ensure(m)
        c["mahalle_pieces"].append((m["mahalle_source_geomid"], m["mahalle_names"]))
        c["hide"].add(m["fully_covered_new_geomid"])

    return by_old


def ensure_district_splits_json(contributions):
    """hideIds/splitYear/syntheticId kayitlarini gunceller - shapely GEREKTIRMEZ."""
    splits = json.loads(DISTRICT_SPLITS.read_text(encoding="utf-8"))
    changed = False
    for old_geomid, c in contributions.items():
        plaka_key = str(c["plaka"])
        splits.setdefault(plaka_key, [])
        want_hide_ids = sorted(c["hide"])
        existing_entry = next((e for e in splits[plaka_key] if e["syntheticId"] == c["synthetic_id"]), None)
        if existing_entry is None:
            splits[plaka_key].append({
                "hideIds": want_hide_ids,
                "splitYear": c["split_year"],
                "syntheticId": c["synthetic_id"],
            })
            changed = True
            print(f"eklendi (district_splits.json): {c['synthetic_id']} -> {want_hide_ids}")
        elif sorted(existing_entry["hideIds"]) != want_hide_ids:
            existing_entry["hideIds"] = want_hide_ids
            changed = True
            print(f"duzeltildi (hideIds guncellendi): {c['synthetic_id']} -> {want_hide_ids}")
    if changed:
        DISTRICT_SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
        print("yazildi:", DISTRICT_SPLITS)


def ensure_geometry(contributions):
    try:
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
    except ImportError:
        print("UYARI: shapely kurulu degil - sentetik poligon uretimi/guncellemesi "
              "atlandi (zaten uretilmisse dosya degismeden kalir). `pip install "
              "shapely` ile kurup tekrar calistirabilirsiniz.")
        return

    modern = json.loads(GEO_NORM.read_text(encoding="utf-8"))
    by_id = {f["properties"]["id"]: f for f in modern["features"]}
    mahalle_geo = json.loads(MAHALLE_GEO.read_text(encoding="utf-8"))

    hist_geo = json.loads(HIST_GEO.read_text(encoding="utf-8"))
    features_by_id = {f["properties"]["id"]: f for f in hist_geo["features"]}

    changed = False
    for old_geomid, c in contributions.items():
        geoms = [shape(by_id[old_geomid]["geometry"])]
        for child_id in sorted(c["whole_child_geomids"]):
            geoms.append(shape(by_id[child_id]["geometry"]))
        for source_geomid, mahalle_names in c["mahalle_pieces"]:
            rows = mahalle_geo.get(source_geomid, {})
            by_name = {info["ad"]: info for info in rows.values()}
            for name in mahalle_names:
                info = by_name.get(name)
                if info is None:
                    raise SystemExit(
                        f"HATA: '{name}' mahallesi {source_geomid} icinde bulunamadi "
                        f"(district_mahalle_merges.yaml'daki isim mahalle_geo.json ile "
                        f"eslesmiyor - Turkce karakter/bosluk farki olabilir)."
                    )
                geoms.append(shape(info["geometry"]))

        merged = unary_union(geoms)
        new_feature = {
            "type": "Feature",
            "properties": {"id": c["synthetic_id"], "plaka": c["plaka"]},
            "geometry": mapping(merged),
        }
        old_feature = features_by_id.get(c["synthetic_id"])
        # idempotent: ayni WKT/koordinat setiyle yeniden yazip gereksiz git-diff
        # uretmemek icin, GERCEKTEN farkliysa guncelle.
        if old_feature is None or json.dumps(old_feature["geometry"], sort_keys=True) != json.dumps(new_feature["geometry"], sort_keys=True):
            features_by_id[c["synthetic_id"]] = new_feature
            changed = True
            print(f"guncellendi/eklendi (geometri): {c['synthetic_id']} "
                  f"({len(c['whole_child_geomids'])} butun cocuk + "
                  f"{sum(len(n) for _, n in c['mahalle_pieces'])} mahalle parcasi)")

    if changed:
        hist_geo["features"] = sorted(features_by_id.values(), key=lambda f: f["properties"]["id"])
        HIST_GEO.write_text(json.dumps(hist_geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print("yazildi:", HIST_GEO)


def patch_data_rows(contributions):
    by_year = {}
    for old_geomid, c in contributions.items():
        for year in c["affected_years"]:
            by_year.setdefault(year, []).append((old_geomid, c["synthetic_id"]))

    for year, patches in by_year.items():
        secim = load_election(year)
        changed = []
        patch_map = dict(patches)
        for d in secim["ilceler"]:
            if d.get("plaka") == 34 and d.get("geomId") in patch_map:
                old = d["geomId"]
                d["geomId"] = patch_map[old]
                changed.append((d["ad"], old, d["geomId"]))
        if changed:
            save_election(year, secim)
            print(f"{year}: guncellendi -> {changed}")
        else:
            print(f"{year}: degisiklik yok (zaten uygulanmis veya eslesen satir yok)")


def main():
    contributions = gather_contributions()
    ensure_geometry(contributions)
    ensure_district_splits_json(contributions)
    patch_data_rows(contributions)


if __name__ == "__main__":
    main()
