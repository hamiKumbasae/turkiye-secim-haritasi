"""
Birden cok eski ilceden kurulan ilcelerin (kanun_cok_kaynak) alanini, kurulmadan onceki
secimler icin bugunku mahalle poligonlariyla o donemdeki ilcelerine paylastirir.

Ornek: Pursaklar (5747, 2008) 2002'de Kecioren, Altindag ve Cubuk'a bolunmustu. Her bugunku
mahallenin donem donem hangi ilcede oldugu (dayanagiyla) geo/historical/idari/ilce_bolusumu.json
icinde yazili; bu betik her donem icin ilce poligonunu eski ilcelere boler. apply_idari_merges.py
her parcayi o secimdeki eski ilcenin satirina katar (satirin HISTK-* poligonu).

Kurallar:
  - Bir donemde tek bir mahallenin ilcesi bile belirsizse (kaynak yok) o donemde bolusum
    yapilmaz; ilce eskisi gibi tarali kalir (tahmin yok).
  - Mahalle poligonlarinin kaplamadigi alan (orman, gol, yol) en yakin mahallenin ilcesine
    verilir (mahalle sinirlarindan orneklenen noktalarla Voronoi). Parcalarin birlesimi bugunku
    ilce poligonuna esittir: delik ve cift cizim yok.
  - Mahalle poligonu kaynagi: geo/normalized/mahalle_geo.json ('mg:' kimlikleri) ya da
    ttezer/turkiye-harita-verisi (83eeb7a) mahalle geometrileri ('tt:' kimlikleri). ttezer
    poligonlarinin kullanilanlari geo/historical/idari/ilce_bolusumu_mahalleler.json'da saklanir;
    --ttezer <dizin> verilirse oradan yenilenir.

Cikti: geo/historical/idari/ilce_bolusumu_parcalar.geojson (her ozellik bir parca: ilce, donem,
eski ilce, pay) ve ozet.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_ilce_bolusumu.py [--ttezer <dizin>]
"""
import argparse
import json
import pathlib
import sys

import shapely
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from build_istanbul_1992_2008 import paylastir, temiz  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
TABLO = IDARI / "ilce_bolusumu.json"
MAHALLELER = IDARI / "ilce_bolusumu_mahalleler.json"
CIKTI = IDARI / "ilce_bolusumu_parcalar.geojson"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
MAHALLE_GEO = ROOT / "geo/normalized/mahalle_geo.json"
BASLANGIC = "1961-01-01"


def oku(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def donemler(kayit):
    """[(baslangic, bitis, {mahalle id: ilceGeomId|None})]; bir aralikta belirsiz olan mahalle None."""
    kesit = {BASLANGIC, kayit["bitis"]}
    for m in kayit["mahalleler"]:
        for d in m["donemler"]:
            kesit |= {d["baslangic"], d["bitis"]}
    for b in kayit.get("belirsiz", []):
        kesit |= {b["baslangic"], b["bitis"]}
    kesit = sorted(k for k in kesit if BASLANGIC <= k <= kayit["bitis"])
    sonuc = []
    for a, b in zip(kesit, kesit[1:]):
        atama = {}
        for m in kayit["mahalleler"]:
            d = [x for x in m["donemler"] if x["baslangic"] <= a < x["bitis"]]
            atama[m["id"]] = d[0]["ilceGeomId"] if d else None
        sonuc.append((a, b, atama))
    # esit ardisik donemleri birlestir
    birlesik = []
    for a, b, at in sonuc:
        if birlesik and birlesik[-1][2] == at:
            birlesik[-1] = (birlesik[-1][0], b, at)
        else:
            birlesik.append((a, b, at))
    return birlesik


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttezer", help="ttezer/turkiye-harita-verisi dist/geojson/mahalle-geometrileri-by-district dizini")
    args = ap.parse_args()

    tablo = oku(TABLO)["ilceler"]
    modern = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in oku(MODERN)["features"]}
    mg = oku(MAHALLE_GEO)
    saklanan = oku(MAHALLELER)["ilceler"] if MAHALLELER.exists() else {}
    if args.ttezer:
        saklanan = {}
        for g, k in sorted(tablo.items()):
            if k["geometriKaynagi"] != "ttezer":
                continue
            fs = oku(pathlib.Path(args.ttezer) / f"{g}.geojson")["features"]
            saklanan[g] = {f"tt:{f['properties']['id']}": {"ad": f["properties"].get("name"), "geometry": f["geometry"]}
                           for f in fs}
        MAHALLELER.write_text(json.dumps({
            "not": "build_ilce_bolusumu.py ile ttezer/turkiye-harita-verisi (commit 83eeb7a, dist/geojson/"
                   "mahalle-geometrileri-by-district) dosyalarindan kopyalanir; yalniz bolusumde kullanilan ilceler.",
            "ilceler": saklanan}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    ozellikler, ozet = [], {}
    for g, k in sorted(tablo.items()):
        D = modern[g]
        if k["geometriKaynagi"] == "ttezer":
            poligon = {i: v for i, v in saklanan[g].items()}
        else:
            poligon = {f"mg:{i}": v for i, v in mg[g].items()}
        ids = [m["id"] for m in k["mahalleler"]]
        eksik = set(poligon) - set(ids)
        fazla = set(ids) - set(poligon)
        if eksik or fazla:
            raise SystemExit(f"HATA {g}: tabloda olmayan mahalle {sorted(eksik)}, poligonu olmayan {sorted(fazla)}")
        geom = {i: temiz(shape(poligon[i]["geometry"])) for i in sorted(ids)}
        ozet[g] = []
        for a, b, atama in donemler(k):
            if any(v is None for v in atama.values()):
                ozet[g].append({"baslangic": a, "bitis": b, "durum": "belirsiz",
                                "mahalle": sorted(poligon[i]["ad"] for i, v in atama.items() if v is None)})
                continue
            bol = paylastir(D, {i: (atama[i], geom[i]) for i in sorted(ids)})
            fark = unary_union(list(bol.values())).symmetric_difference(D).area / D.area
            assert fark < 1e-6, (g, a, fark)
            paylar = {}
            for e, p in sorted(bol.items()):
                p = temiz(shapely.set_precision(p, 1e-5))
                pay = round(p.area / D.area, 4)
                paylar[e] = pay
                ozellikler.append({"type": "Feature", "properties": {
                    "id": f"BOL-{g[5:]}-{a[:4]}-{e.replace('TR-D-', '')}", "ilce": g, "baslangic": a, "bitis": b,
                    "ebeveyn": e, "pay": pay}, "geometry": mapping(p)})
            ozet[g].append({"baslangic": a, "bitis": b, "durum": "bolundu", "paylar": paylar})

    CIKTI.write_text(json.dumps({"type": "FeatureCollection", "features": ozellikler},
                                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
