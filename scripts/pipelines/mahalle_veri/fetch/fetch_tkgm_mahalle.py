"""
TKGM (Tapu ve Kadastro Genel Mudurlugu) idari yapi servisinden mahalle/koy sinirlarini ceker.

Kaynak: https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/idariYapi (Parsel Sorgu uygulamasinin kullandigi
herkese acik servis): ilListe -> ilceListe/<il id> -> mahalleListe/<ilce id>, her biri GeoJSON
FeatureCollection. Servisin yayimlanmis bir acik veri lisansi yok; veri sitede kaynak gosterilerek
kullanilir ve sitenin acik veri lisansinin disinda tutulur (bkz. data/raw/tkgm/PROVENANCE.md).

Geometri sitedeki mevcut mahalle poligonlariyla ayni yogunluga indirilir: Douglas-Peucker
(tolerans 0.0001 derece, ~10 m, topoloji korunarak) ve 4 ondalik basamak.

Cikti: <cikti>/<plaka>.geojson; her ozellik {tkgm_id, ad, ilce, ilce_tkgm_id, geomId}. geomId,
projenin ilce kimligidir (data/normalized/elections/genel/2023.json ilce adlariyla eslestirilir;
eslesmeyen ilce raporlanir, geomId bos kalir).

Kullanim: python3 fetch_tkgm_mahalle.py <cikti klasoru> <plaka,plaka,...>
"""
import json
import pathlib
import sys
import time
import urllib.request

from shapely.geometry import mapping, shape
from shapely.validation import make_valid

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from common.turkish_text import fold  # noqa: E402

BASE = "https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/idariYapi"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (turkiye-secim-haritasi; github.com/hamiKumbasae)"
TOLERANS = 0.0001


def al(url, deneme=4):
    for i in range(deneme):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            if i == deneme - 1:
                raise
            print("  tekrar:", url, str(e)[:120])
            time.sleep(2 * (i + 1))


def yuvarla(o):
    if isinstance(o, (list, tuple)):
        if o and isinstance(o[0], (int, float)):
            return [round(o[0], 4), round(o[1], 4)]
        return [yuvarla(x) for x in o]
    return o


def sadelestir(geom):
    if not geom or not geom.get("coordinates"):
        return None
    g = make_valid(shape(geom))
    if g.geom_type == "GeometryCollection":
        parcalar = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        if not parcalar:
            return None
        from shapely.ops import unary_union
        g = unary_union(parcalar)
    g = g.simplify(TOLERANS, preserve_topology=True)
    if g.is_empty:
        return None
    m = mapping(g)
    return {"type": m["type"], "coordinates": yuvarla(m["coordinates"])}


def main():
    cikti = pathlib.Path(sys.argv[1])
    plakalar = [int(p) for p in sys.argv[2].split(",")]
    cikti.mkdir(parents=True, exist_ok=True)
    sec = json.loads((ROOT / "data/normalized/elections/genel/2023.json").read_text(encoding="utf-8"))
    il_ad = {r["plaka"]: r["ad"] for r in sec["iller"]}
    ilceler = {}
    for r in sec["ilceler"]:
        if r.get("geomId", "").startswith("TR-D-"):
            ilceler.setdefault(r["plaka"], {})[fold(r["ad"])] = r["geomId"]

    tkgm_iller = {fold(f["properties"]["text"]): f["properties"]["id"] for f in al(f"{BASE}/ilListe")["features"]}
    ozet = {}
    for plaka in plakalar:
        il_id = tkgm_iller.get(fold(il_ad[plaka]))
        if il_id is None:
            print("IL ESLESMEDI", plaka, il_ad[plaka])
            ozet[plaka] = {"hata": "il eslesmedi"}
            continue
        ozellikler, eslesmeyen_ilce, geometrisiz = [], [], []
        t0 = time.time()
        for fi in al(f"{BASE}/ilceListe/{il_id}")["features"]:
            ilce_ad, ilce_id = fi["properties"]["text"], fi["properties"]["id"]
            geom_id = ilceler.get(plaka, {}).get(fold(ilce_ad))
            if not geom_id:
                eslesmeyen_ilce.append(ilce_ad)
            time.sleep(0.3)
            for fm in al(f"{BASE}/mahalleListe/{ilce_id}")["features"]:
                p = fm.get("properties") or {}
                g = sadelestir(fm.get("geometry"))
                if g is None:
                    geometrisiz.append(f"{ilce_ad}/{p.get('text')}")
                ozellikler.append({"type": "Feature", "geometry": g, "properties": {
                    "tkgm_id": p.get("id"), "ad": p.get("text"), "ilce": ilce_ad,
                    "ilce_tkgm_id": ilce_id, "geomId": geom_id}})
        (cikti / f"{plaka:02d}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": ozellikler}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        sure = time.time() - t0
        ozet[plaka] = {"il": il_ad[plaka], "birim": len(ozellikler), "geometrisiz": len(geometrisiz),
                       "eslesmeyen_ilce": eslesmeyen_ilce, "sure_sn": round(sure)}
        print(f"::notice title=TKGM {plaka:02d} {il_ad[plaka]}::{len(ozellikler)} birim, geometrisiz {len(geometrisiz)}, "
              f"eslesmeyen ilce {eslesmeyen_ilce}, {sure:.0f} sn", flush=True)
        (cikti / f"ozet_{plaka:02d}.json").write_text(json.dumps({plaka: ozet[plaka]}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
