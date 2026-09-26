"""
Tarihsel idari katmanin (geo/historical/idari/) kanun kaynakli soy bilgisini
haritaya yansitir: bir secimde henuz ayri birim olmayan ilcenin alani, o
tarihte bagli oldugu eski ilcenin satirina katilir (ornek: Koprubasi 20.05.1990'da
3644 ile Surmene'den ayrildi; 1990 oncesi secimlerde Surmene'nin oyu Surmene +
Koprubasi alanina boyanir).

Ne kullanilir:
  - district_lineage.json: lineageStatus == "kanun_tek_kaynak" (kuruluş kanununun ek
    listesine gore butun birimleri TEK eski ilceden gelen ilceler) ve eski ilcenin geomId'si.
  - Kosul (ilce C, secim E): C, E'nin ilce satirlarinda (ya da o satirlarin tarihsel
    birlesimlerinde) yok VE
      * C o tarihte kanunen kurulmamis (Icisleri kurulus > E tarihi), ya da
      * ilce duzeyli secimlerde: C kanunla kurulmus ama E'ye ayri girmemis
        (kurulduAmaSecimeAyriGirmedi). Yerel secim satirlari belediye oldugu icin
        yalniz ilk kosul kullanilir.
  - Eski ilce E'de yoksa zincirle bir ust eski ilceye cikilir.
  - Repodaki mevcut HIST-* birlesimleri (district_splits.json) korunur; C onlarin
    parcasiysa katilmaz, hedef satir HIST ise onun uzerine eklenir.

Degerler (oy/katilim) DEGISMEZ; yalniz satirin geomId'si yeni sentetik birlesime
(HISTK-*) cevrilir. Sentetikler her calistirmada sifirdan hesaplanir (idempotent):
onceki HISTK satirlari once tabanlarina geri cevrilir.

Ciktilar: geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson (HISTK
poligonlari), geo/historical/district_splits.json (hideIds), data/normalized
secim dosyalari (geomId), geo/historical/idari/merge_plan.json (plan + rapor).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/apply_idari_merges.py
"""
import collections
import hashlib
import json
import pathlib
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from build_idari_katman import secimler  # noqa: E402
from common.election_io import election_path, load_election, save_election  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = ROOT / "geo/historical/district_splits.json"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
PLAN = IDARI / "merge_plan.json"
ONEK = "HISTK-"
ILCE_DUZEYLI = {"genel", "referandum", "cumhurbaskanligi"}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def main():
    lineage = {l["geomId"]: l for l in oku(IDARI / "district_lineage.json")["districts"]}
    cocuk = {}
    for g, l in lineage.items():
        k = l.get("kanunSoyu")
        if l["lineageStatus"] == "kanun_tek_kaynak" and k and k["eskiIlceler"][0]["geomId"]:
            cocuk[g] = {"ebeveyn": k["eskiIlceler"][0]["geomId"], "kurulus": (l["kurulus"] or {}).get("tarih"),
                        "girmedi": set(l["kurulduAmaSecimeAyriGirmedi"]), "kanun": k["kanun"], "ad": l["ad"],
                        "plaka": l["plaka"]}
    splits = oku(SPLITS)
    hist = oku(HIST_GEO)
    eski_plan = oku(PLAN)["sentetikler"] if PLAN.exists() else {}

    # repodaki (HISTK disi) tarihsel birlesimler: id -> parcalar
    hist_parca = {}
    for girdiler in splits.values():
        for e in girdiler:
            if not e["syntheticId"].startswith(ONEK):
                hist_parca[e["syntheticId"]] = set(e["hideIds"])

    plan, rapor = {}, collections.defaultdict(list)
    satir_degisim = collections.Counter()
    for s in secimler():
        try:
            kayit = load_election(s["anahtar"])
        except FileNotFoundError:
            continue
        if not kayit.get("ilceler"):
            continue
        # onceki calistirmadan kalan HISTK satirlarini tabanlarina dondur (idempotent)
        for r in kayit["ilceler"]:
            if (r.get("geomId") or "").startswith(ONEK):
                r["geomId"] = eski_plan[r["geomId"]]["taban"]
        # her satirin kapsadigi modern birimler
        kapsayan = {}
        for r in kayit["ilceler"]:
            g = r.get("geomId")
            if not g:
                continue
            for parca in hist_parca.get(g, {g}) | {g}:
                kapsayan[parca] = g
        katilan = collections.defaultdict(set)
        for c, bilgi in sorted(cocuk.items()):
            if c in kapsayan:
                continue
            uygun = (bilgi["kurulus"] and bilgi["kurulus"] > s["tarih"]) or \
                    (s["tur"] in ILCE_DUZEYLI and s["anahtar"] in bilgi["girmedi"])
            if not uygun:
                continue
            # zincir: ebeveyn secimde yoksa ve kendisi de henuz ayri degilse bir ust
            hedef, zincir, e = None, [c], bilgi["ebeveyn"]
            for _ in range(6):
                if e in kapsayan:
                    hedef = kapsayan[e]
                    break
                if e in cocuk:
                    zincir.append(e)
                    e = cocuk[e]["ebeveyn"]
                    continue
                break
            if hedef is None:
                rapor["hedefBulunamadi"].append({"secim": s["anahtar"], "ilce": c, "ad": bilgi["ad"], "ebeveyn": bilgi["ebeveyn"]})
                continue
            katilan[hedef] |= set(zincir)
        for hedef, parcalar in katilan.items():
            # zincirdeki ara ebeveynler bu secimde ayri satir olabilir mi? olamaz: kapsayan'da yoklar
            parcalar = {p for p in parcalar if p not in kapsayan}
            if not parcalar:
                continue
            anahtar = hedef + "|" + ",".join(sorted(parcalar))
            sid = f"{ONEK}{hedef.replace('TR-D-', '')}-{hashlib.sha1(anahtar.encode()).hexdigest()[:6]}"
            p = plan.setdefault(sid, {"taban": hedef, "katilanlar": sorted(parcalar), "secimler": [],
                                      "plaka": int(hedef.split("-")[2]) if hedef.startswith("TR-D-") else
                                      next(f["properties"]["plaka"] for f in hist["features"] if f["properties"]["id"] == hedef),
                                      "kanunlar": sorted({cocuk[x]["kanun"] for x in parcalar}),
                                      "adlar": sorted(cocuk[x]["ad"] for x in parcalar)})
            p["secimler"].append(s["anahtar"])
            for r in kayit["ilceler"]:
                if r.get("geomId") == hedef:
                    r["geomId"] = sid
                    satir_degisim[s["anahtar"]] += 1
        eski_hali = json.loads(election_path(s["anahtar"]).read_text(encoding="utf-8"))
        if eski_hali != kayit:
            save_election(s["anahtar"], kayit)

    # geometri: taban (modern ya da repodaki HIST) + katilan modern ilceler
    modern = {f["properties"]["id"]: f for f in oku(MODERN)["features"]}
    hist_by = {f["properties"]["id"]: f for f in hist["features"] if not f["properties"]["id"].startswith(ONEK)}
    yeni = []
    for sid, p in sorted(plan.items()):
        taban = modern.get(p["taban"]) or hist_by.get(p["taban"])
        geoms = [temiz(shape(taban["geometry"]))] + [temiz(shape(modern[x]["geometry"])) for x in p["katilanlar"]]
        yeni.append({"type": "Feature", "properties": {"id": sid, "plaka": p["plaka"]},
                     "geometry": mapping(unary_union(geoms))})
    hist["features"] = sorted(list(hist_by.values()) + yeni, key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # district_splits: HISTK kayitlari yeniden yazilir
    for pl in list(splits):
        splits[pl] = [e for e in splits[pl] if not e["syntheticId"].startswith(ONEK)]
        if not splits[pl]:
            del splits[pl]
    for sid, p in sorted(plan.items()):
        gizle = sorted(hist_parca.get(p["taban"], {p["taban"]}) | {p["taban"]} if p["taban"].startswith("TR-D-")
                       else hist_parca[p["taban"]]) + p["katilanlar"]
        yil = min(int(lineage[x]["kurulus"]["tarih"][:4]) for x in p["katilanlar"] if lineage[x]["kurulus"]["tarih"])
        splits.setdefault(str(p["plaka"]), []).append({"hideIds": sorted(set(gizle)), "splitYear": yil, "syntheticId": sid})
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")

    ozet = {"sentetik": len(plan), "satirDegisimi": sum(satir_degisim.values()),
            "secimBasina": dict(sorted(satir_degisim.items())), "katilanIlce": len({x for p in plan.values() for x in p["katilanlar"]}),
            "hedefBulunamadi": len(rapor["hedefBulunamadi"])}
    PLAN.write_text(json.dumps({"not": "apply_idari_merges.py ile üretilir; elle düzenlenmez.", "ozet": ozet,
                                "sentetikler": plan, **rapor}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
