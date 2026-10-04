"""
Harita durum raporu: her secim x il x guncel ilce poligonu icin ön yüzün (src/js/map.js
renderProvinceMap) nasil cizdigini Python'da aynen yeniden kurar ve siniflandirir; eksik
secim verilerini listeler. docs/rapor/ altina CSV + ozet JSON yazar.

Poligon durumlari (bir guncel ilce poligonu, bir secimde, bir ilin haritasinda):
  veri               poligonun kendi satiri var ve sonucu var
  birlesimde         tarihsel birlesim poligonunun (HIST/HISTK/HISTY) parcasi, birlesimin sonucu var
  tarali_henuz_yok   sonuc yok; ilce o secimde henuz kurulmamisti (harita_notlari) -> taranmis
  tarali_ayri_girmedi sonuc yok; kurulmustu ama secime ayri girmedi -> taranmis
  gri_satir_bos      satiri var ama sonucu yok (kaynak okunamadi/eslesmedi)
  gri_satir_yok      satiri da yok, notu da yok -> gri "veri yok"
  il_tek_parca       bu secimde ilin hic ilce verisi yok; il tek parca ciziliyor (sayilmaz)

Kullanim:
  .venv/bin/python scripts/rapor/harita_durum_raporu.py
"""
import collections
import csv
import json
import pathlib

from shapely.geometry import shape

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "rapor"
EL = ROOT / "data" / "normalized" / "elections"
MECLIS = ROOT / "data" / "normalized" / "meclis_harita"


def oku(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def gercek(r):
    return bool(r.get("oy"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    modern = oku(ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson")["features"]
    hist = oku(ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson")["features"]
    geo_id = {f["properties"]["id"] for f in modern + hist}
    alan = {}
    for f in modern:
        g = shape(f["geometry"])
        alan[f["properties"]["id"]] = g.area if g.is_valid else g.buffer(0).area
    ad_modern = {}
    lineage = oku(ROOT / "geo/historical/idari/district_lineage.json")
    for l in (lineage.get("districts") or lineage.get("ilceler") or []):
        if isinstance(l, dict) and l.get("geomId"):
            ad_modern[l["geomId"]] = l.get("ad")
    splits = oku(ROOT / "geo/historical/district_splits.json")
    notlar = oku(ROOT / "geo/historical/idari/harita_notlari.json")
    modern_by_pl = collections.defaultdict(list)
    for f in modern:
        modern_by_pl[f["properties"]["plaka"]].append(f["properties"]["id"])

    kayitlar = {}
    for tur_dir in sorted(EL.iterdir()):
        for f in sorted(tur_dir.glob("*.json")):
            kayitlar[f.stem] = (tur_dir.name, "baskanlik" if tur_dir.name == "yerel" else "-", oku(f))
    for f in sorted(MECLIS.glob("*.json")):
        yil, kisa = f.stem.split("_")
        kayitlar[f.stem] = ("yerel", kisa, oku(f))

    poligon_rows, eksik_rows, ozet = [], [], {}
    for key, (tur, oylama, d) in kayitlar.items():
        secim = key.split("_")[0]
        not_secim = notlar["secimler"].get(secim, {})
        il_ad = {r["plaka"]: r["ad"] for r in d["iller"]}
        by_pl = collections.defaultdict(list)
        for r in d["ilceler"]:
            by_pl[r["plaka"]].append(r)
        say = collections.Counter()
        alan_say = collections.Counter()
        il_tek = 0
        # eksik: il satiri sonucsuz
        for r in d["iller"]:
            if not gercek(r):
                eksik_rows.append({"secim": key, "tur": tur, "oylama": oylama, "duzey": "il", "plaka": r["plaka"],
                                   "il": r["ad"], "ad": r["ad"], "geomId": "", "neden": r.get("not") or "il satırında sonuç yok"})
        for pl in sorted(set(il_ad) | set(by_pl)):
            rows = by_pl.get(pl, [])
            data = {r["geomId"] for r in rows if gercek(r) and r.get("geomId") in geo_id}
            for r in rows:
                if gercek(r) and r.get("geomId") not in geo_id:
                    say["poligonsuz_veri"] += 1
                    eksik_rows.append({"secim": key, "tur": tur, "oylama": oylama, "duzey": "ilce", "plaka": pl,
                                       "il": il_ad.get(pl, ""), "ad": r["ad"], "geomId": r.get("geomId") or "",
                                       "neden": "sonuç var ama çizilecek poligon yok"})
                if not gercek(r):
                    eksik_rows.append({"secim": key, "tur": tur, "oylama": oylama, "duzey": "ilce", "plaka": pl,
                                       "il": il_ad.get(pl, ""), "ad": r["ad"], "geomId": r.get("geomId") or "",
                                       "neden": r.get("not") or "ilçe satırında sonuç yok"})
                if r.get("ilceGeneliSonuc"):
                    eksik_rows.append({"secim": key, "tur": tur, "oylama": oylama, "duzey": "ilce", "plaka": pl,
                                       "il": il_ad.get(pl, ""), "ad": r["ad"], "geomId": r.get("geomId") or "",
                                       "neden": "gösterilen sonuç ilçe belediyesinin değil: " + r["ilceGeneliSonuc"]})
            if not data:
                if pl in il_ad:
                    il_tek += 1
                continue
            gizli = set()
            for e in splits.get(str(pl), []):
                if e["syntheticId"] in data:
                    gizli.update(e["hideIds"])
            satir_geom = {r.get("geomId"): r for r in rows}
            for gid in modern_by_pl.get(pl, []):
                if gid in data:
                    durum = "veri"
                elif gid in gizli:
                    durum = "birlesimde"
                elif gid in not_secim:
                    durum = "tarali_ayri_girmedi" if not_secim[gid] == 1 else "tarali_henuz_yok"
                elif gid in satir_geom:
                    durum = "gri_satir_bos"
                else:
                    durum = "gri_satir_yok"
                say[durum] += 1
                alan_say[durum] += alan[gid]
                if durum not in ("veri", "birlesimde"):
                    n = notlar["ilceler"].get(gid, {})
                    poligon_rows.append({"secim": key, "tur": tur, "oylama": oylama, "plaka": pl, "il": il_ad.get(pl, ""),
                                         "geomId": gid, "ilce_bugun": n.get("ad") or ad_modern.get(gid) or "",
                                         "durum": durum, "kurulus": n.get("tarih", ""), "kanun": n.get("kanun", ""),
                                         "soy": n.get("durum", ""),
                                         "kaynak_ilceler": "; ".join(f"{a} ({b})" for a, b in n.get("kaynaklar", [])),
                                         "satir_notu": (satir_geom.get(gid) or {}).get("not", "")})
        top = sum(alan_say.values()) or 1
        ozet[key] = {"tur": tur, "oylama": oylama, "il": len(il_ad), "ilSonucsuz": sum(1 for r in d["iller"] if not gercek(r)),
                     "ilTekParca": il_tek, "ilceSatir": len(d["ilceler"]),
                     "ilceSonuclu": sum(1 for r in d["ilceler"] if gercek(r)),
                     "poligon": dict(say), "alanPayi": {k: round(100 * v / top, 2) for k, v in alan_say.items()}}

    alanlar = ["secim", "tur", "oylama", "plaka", "il", "geomId", "ilce_bugun", "durum", "kurulus", "kanun", "soy",
               "kaynak_ilceler", "satir_notu"]
    with open(OUT / "poligon_durumu.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, alanlar, lineterminator="\n")
        w.writeheader()
        w.writerows(poligon_rows)
    with open(OUT / "eksik_secim_verisi.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["secim", "tur", "oylama", "duzey", "plaka", "il", "ad", "geomId", "neden"], lineterminator="\n")
        w.writeheader()
        w.writerows(eksik_rows)
    (OUT / "ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print("poligon satırı", len(poligon_rows), "eksik veri satırı", len(eksik_rows))
    for k, v in ozet.items():
        print(k, v["il"], v["ilTekParca"], v["poligon"], v["alanPayi"].get("tarali_henuz_yok"), v["alanPayi"].get("gri_satir_yok"))


if __name__ == "__main__":
    main()
