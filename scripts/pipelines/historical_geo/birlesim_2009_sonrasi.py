"""
2009 ve sonrasi secimlerde henuz kurulmamis ilcelerin alanini ana ilcelerinin poligonuna katar.

1961-2007 icin build_ilce_secim.py ve apply_idari_merges.py bu isi yapar; 2009 sonrasinda kalan
taralı ilceler kanun ek listesi repoda olmayan uc ilce ve 2012'de bolunen uc Merkez ilcesiydi:

  Kemalpasa (Artvin, KHK 694, 2017)  -> Hopa      HIST-Artvin-Hopa (repoda dogrulanmis, 2007'de de)
  Sultanhani (Aksaray, KHK 694, 2017) -> Merkez   HIST-Aksaray-Merkez  (kaba: beldesi Aksaray
                                                   ilcesinde, koyleri KHK ekinde; 2007 haritasiyla ayni)
  Derecik (Hakkari, 7148, 2018)       -> Semdinli HIST-Hakkari-Semdinli (kaba: beldesi Semdinli'de)
  Denizli Merkez (2012: Merkezefendi + Pamukkale)  HIST-Denizli-Merkez
  Hatay Merkez (2012: Antakya + Defne)             HIST-Hatay-Merkez (Defne'nin kanun ek listesindeki
                                                   birimlerinin %73'u Merkez'den; Merkez cogunlugu kurali)
  Van Merkez (2012: Ipekyolu + Tusba)              HIST-Van-Merkez (repoda dogrulanmis)

Kural (her secim, her calistirmada sifirdan, idempotent): yeni ilcenin o secimde oyu yoksa (bos
iskelet satiri) ana ilcenin satiri birlesim poligonuna baglanir; oyu varsa (YSK sonucu sonraki
ilcelere gore toplamis) satirlar kendi poligonunda kalir. Merkez satirlari
election_import/merkez_ilce_tamamla.py ile zaten birlesim kimligiyle gelir. Oy degerleri degismez.

Ciktilar: geo/historical/district_splits.json, geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson
(eksik birlesim poligonlari eklenir), data/normalized/elections/<tur>/<2009+>.json (geomId).

Kullanim (tarihsel_sinirlari_uret.py apply_idari_merges.py'den sonra cagirir):
  python3 scripts/pipelines/historical_geo/birlesim_2009_sonrasi.py
"""
import json
import pathlib
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from common.election_io import load_election, save_election  # noqa: E402
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur  # noqa: E402

SPLITS = ROOT / "geo/historical/district_splits.json"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
EL = ROOT / "data/normalized/elections"

# sentetik id -> (plaka, bilesenler, splitYear)
BIRLESIM = {
    "HIST-Artvin-Hopa": (8, ["TR-D-08-005", "TR-D-08-006"], 2017),
    "HIST-Aksaray-Merkez": (68, ["TR-D-68-002", "TR-D-68-008"], 2017),
    "HIST-Hakkari-Semdinli": (30, ["TR-D-30-003", "TR-D-30-005"], 2018),
    "HIST-Denizli-Merkez": (20, ["TR-D-20-015", "TR-D-20-016"], 2012),
    "HIST-Hatay-Merkez": (31, ["TR-D-31-002", "TR-D-31-005"], 2012),
    "HIST-Van-Merkez": (65, ["TR-D-65-009", "TR-D-65-013"], 2011),
}
# yeni ilce -> (ana ilcenin bugunku geomId'si, birlesim). build_meclis_harita.py SENTETIK_TABAN ayni eslemeyi tutar.
KATILIM = {
    "TR-D-08-006": ("TR-D-08-005", "HIST-Artvin-Hopa"),
    "TR-D-68-008": ("TR-D-68-002", "HIST-Aksaray-Merkez"),
    "TR-D-30-005": ("TR-D-30-003", "HIST-Hakkari-Semdinli"),
}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def oylu(r):
    return any(isinstance(v, dict) and (v.get("oy") or 0) > 0 for v in (r.get("oy") or {}).values())


def poligonlar():
    splits, hist = oku(SPLITS), oku(HIST_GEO)
    modern = {f["properties"]["id"]: f for f in oku(MODERN)["features"]}
    var = {f["properties"]["id"] for f in hist["features"]}
    degisti = False
    for sid, (plaka, ids, yil) in BIRLESIM.items():
        liste = splits.setdefault(str(plaka), [])
        kayit = next((e for e in liste if e["syntheticId"] == sid), None)
        if kayit is None:
            liste.append({"hideIds": sorted(ids), "splitYear": yil, "syntheticId": sid})
            degisti = True
        elif sorted(kayit["hideIds"]) != sorted(ids):
            raise SystemExit(f"{sid}: district_splits.json'daki hideIds farkli: {kayit['hideIds']}")
        if sid not in var:
            geoms = [temiz(shape(modern[g]["geometry"])) for g in ids]
            u = unary_union(geoms)
            yabanci = unary_union([temiz(shape(f["geometry"])) for g, f in modern.items()
                                   if g not in ids and shape(f["geometry"]).intersects(u.envelope)])
            u = delikleri_doldur(u, bilesen_delikleri(geoms), yabanci)
            hist["features"].append({"type": "Feature", "properties": {"id": sid, "plaka": plaka},
                                     "geometry": mapping(u)})
            degisti = True
    if degisti:
        HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")


def secimler():
    for p in sorted(EL.glob("*/*.json")):
        if p.stem[:4].isdigit() and int(p.stem[:4]) >= 2009:
            yield p.stem


def main():
    poligonlar()
    for secim in secimler():
        rec = load_election(secim)
        once = json.dumps(rec, ensure_ascii=False, sort_keys=True)
        by_geom = {}
        for r in rec["ilceler"]:
            by_geom.setdefault(r.get("geomId"), []).append(r)
        # once geri al: KATILIM birlesimlerini tabanina dondur
        for yeni, (ana, sid) in KATILIM.items():
            for r in by_geom.get(sid, []):
                r["geomId"] = ana
        by_geom = {}
        for r in rec["ilceler"]:
            by_geom.setdefault(r.get("geomId"), []).append(r)
        baglanan = []
        for yeni, (ana, sid) in KATILIM.items():
            yeni_satir = by_geom.get(yeni, [])
            ana_satir = by_geom.get(ana, [])
            if any(oylu(r) for r in yeni_satir) or len(ana_satir) != 1:
                continue
            ana_satir[0]["geomId"] = sid
            baglanan.append(f"{ana_satir[0]['ad']} ← {yeni}")
        if json.dumps(rec, ensure_ascii=False, sort_keys=True) != once:
            save_election(secim, rec)
        print(secim, "; ".join(baglanan) or "-")


if __name__ == "__main__":
    main()
