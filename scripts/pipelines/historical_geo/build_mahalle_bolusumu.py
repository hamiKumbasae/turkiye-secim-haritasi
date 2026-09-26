"""
Birden cok eski ilceden kurulan ilcelerin (lineageStatus kanun_cok_kaynak) alanini
mahalle poligonlariyla eski ilceler arasinda bolustürür (Faz 4b, pilot: İstanbul).

Ornek: Arnavutköy (5747, 2008) = Gaziosmanpaşa'nın 26 + Çatalca'nın 18 + Küçükçekmece'nin
1 birimi. 2008 oncesi secimlerde Gaziosmanpaşa satiri Arnavutköy'ün dogusunu, Çatalca
satiri batisini kapsamali.

Yontem (tahmin yok; cikarim ayrica isaretli):
  1. Kanun ek listesindeki her birimin eski ilcesi (data/kaynaklar/resmi_gazete/ilce_kurulus/
     <kanun>.json; ilk kademe belediyesinin ilcesi DIE 2004).
  2. Guncel mahalle poligonu (geo/normalized/mahalle_geo.json) adiyla bir birime eslesir:
     ayni ad; belde "Merkez" mahallesi = belde adi; belde adini tasiyan guncel mahalle
     (Hadımköy, Durusu) = o beldenin (tek) ilcesi; ELLE_AD'daki yazim esleri.
  3. Adi eslesmeyen guncel mahalle ya da mahalle poligonlarinin kaplamadigi alan (gol,
     orman) parcasi: butun siniri TEK bir eski ilcenin mahalleleriyle cevriliyse ve ilcenin
     dis sinirina degmiyorsa o ilceye verilir (`cikarim: cevrelenmis`). Kanunda iki ilce
     arasinda paylasildigi yazan birimler (BELIRSIZ_BIRIM) cikarimla atanmaz.
  4. Kalan alan 'belirsiz' parcadir; haritada tarali, adaylariyla.
Parcalar ayriktir ve guncel ilce poligonunu tam boler (kirpma + sirali fark).

Cikti: geo/historical/idari/mahalle_bolusumu.json (atama raporu),
       geo/historical/idari/mahalle_bolusumu.geojson (PARCA-*/BELIRSIZ-* poligonlari).
apply_idari_merges.py bu parcalari eski ilcelerin sentetik birlesimlerine katar.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_mahalle_bolusumu.py
"""
import collections
import json
import pathlib
import re
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.turkish_text import fold  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
OUT_JSON = IDARI / "mahalle_bolusumu.json"
OUT_GEO = IDARI / "mahalle_bolusumu.geojson"
EPS = 2e-4   # derece (~20 m): komsuluk/degme toleransi
MIN_ALAN = 1e-7  # bundan kucuk kirpma kirintilari atilir

# pilot: yeni ilce geomId -> kanun kaynak dosyasi ve ilce adi
ILCELER = {
    "TR-D-34-002": {"kanun": "5747", "ad": "Arnavutköy"},
    "TR-D-34-033": {"kanun": "5747", "ad": "Sultangazi"},
}
# kanundaki ad -> guncel mahalle adi (ayni birim, farkli yazim)
ELLE_AD = {"M. Fevzi Çakmak": "Mareşal Fevzi Çakmak"}
# kanunda iki eski ilce arasinda paylasildigi yazan birimler: guncel mahalle -> adaylar
BELIRSIZ_BIRIM = {
    # 5747 (22): Gaziosmanpaşa'nın Habipler mahallesi + Esenler'in 'Habipler' parsel parcasi;
    # guncel veride iki mahalle (ESKİ HABİPLER, HABİBLER) - hangisinin hangisi oldugu yazmiyor
    ("TR-D-34-033", "ESKİ HABİPLER MAH."): ["Gaziosmanpaşa", "Esenler"],
    ("TR-D-34-033", "HABİBLER MAH."): ["Gaziosmanpaşa", "Esenler"],
}


def norm(s):
    return fold(re.sub(r"\s*MAH\.?$", "", s.strip())).replace(".", "").replace(" ", "")


def belediye_adi(r):
    b = r.get("eskiBelediye") or ""
    return re.sub(r" (İlk Kademe|İlçe) Belediyesi$", "", b)


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def bolustur(geom_id, cfg, mahalle_geo, ilce_poly, komsular):
    kanun = json.loads((ROOT / f"data/kaynaklar/resmi_gazete/ilce_kurulus/{cfg['kanun']}.json").read_text(encoding="utf-8"))
    kayit = next(i for i in kanun["ilceler"] if (i["yeniIlce"] or {}).get("geomId") == geom_id)
    birim, belde, ilce_geom = collections.defaultdict(set), collections.defaultdict(set), {}
    for r in kayit["satirlar"]:
        if not r["eskiIlce"]:
            continue
        ilce_geom[r["eskiIlce"]] = r["eskiIlceGeomId"]
        if r["tur"] in ("mahalle", "koy"):
            ad = belediye_adi(r) if r["birim"] == "Merkez" and r.get("eskiBelediye") else r["birim"]
            birim[norm(ELLE_AD.get(ad, ad))].add(r["eskiIlce"])
        if r["tur"] != "koy_kismi" and belediye_adi(r):
            belde[norm(belediye_adi(r))].add(r["eskiIlce"])
    # komsu guncel ilcelerle kaynaktaki ince ortusmeler (sliver) cikarilir: parcalar
    # eski ilcenin birlesimine katildiginda komsuyla ust uste binmesin
    C = temiz(ilce_poly)
    C = C.difference(unary_union([temiz(k) for k in komsular if k.intersects(C)]))
    atama, parca_geom = [], []
    for mid, m in sorted(mahalle_geo.get(geom_id, {}).items()):
        g = temiz(shape(m["geometry"])).intersection(C)
        if g.area < MIN_ALAN:
            continue
        n = norm(m["ad"])
        adaylar = BELIRSIZ_BIRIM.get((geom_id, m["ad"]))
        if adaylar:
            atama.append({"mahalle": m["ad"], "id": mid, "ilce": None, "adaylar": adaylar, "neden": "kanunda paylaşılmış birim"})
        elif len(birim.get(n, ())) == 1:
            atama.append({"mahalle": m["ad"], "id": mid, "ilce": next(iter(birim[n])), "neden": "ad"})
        else:
            hit = [b for b in belde if n.startswith(b) and len(belde[b]) == 1]
            if hit:
                atama.append({"mahalle": m["ad"], "id": mid, "ilce": next(iter(belde[hit[0]])), "neden": f"belde adı ({hit[0]})"})
            else:
                atama.append({"mahalle": m["ad"], "id": mid, "ilce": None, "neden": "eşleşmedi"})
        parca_geom.append(g)
    # ayrik parcalar: sirayla fark
    dolu = None
    for a, g in zip(atama, parca_geom):
        if dolu is not None:
            g = g.difference(dolu)
        dolu = g if dolu is None else dolu.union(g)
        a["_geom"] = g
    bosluk = C.difference(dolu) if dolu is not None else C
    for i, p in enumerate(getattr(bosluk, "geoms", [bosluk])):
        if p.area >= MIN_ALAN:
            atama.append({"mahalle": None, "id": f"bosluk-{i}", "ilce": None, "neden": "mahalle poligonu yok", "_geom": p})
    # cevrelenmis cikarimi: atanmamis alanin (eslesmeyen mahalle + mahalle disi) bagli
    # bilesenleri; dis sinira degmeyen ve yalniz TEK eski ilcenin parcalarina degen bilesen
    dis = C.exterior if C.geom_type == "Polygon" else unary_union([p.exterior for p in C.geoms])
    atanmamis = [a for a in atama if not a["ilce"] and not a.get("adaylar")]
    kilitli = unary_union([a["_geom"] for a in atama if a.get("adaylar")]) if any(a.get("adaylar") for a in atama) else None
    if atanmamis:
        U = unary_union([a["_geom"] for a in atanmamis]).buffer(EPS / 4).buffer(-EPS / 4)
        for comp in getattr(U, "geoms", [U]):
            if comp.distance(dis) < EPS or (kilitli is not None and comp.distance(kilitli) < EPS):
                continue
            komsu = {b["ilce"] for b in atama if b["ilce"] and b["_geom"].distance(comp) < EPS}
            if len(komsu) != 1:
                continue
            for a in atanmamis:
                if a["_geom"].intersection(comp).area > 0.5 * a["_geom"].area:
                    a["ilce"], a["cikarim"] = next(iter(komsu)), "cevrelenmis"
    toplam = C.area
    gruplar = collections.defaultdict(list)
    for a in atama:
        gruplar[a["ilce"]].append(a)
    features, ozet = [], {}
    kod = geom_id.replace("TR-D-", "")
    for ilce, xs in gruplar.items():
        geom = unary_union([x["_geom"] for x in xs])
        if ilce:
            pid = f"PARCA-{kod}-{fold(ilce).replace(' ', '')}"
            ozet[ilce] = {"parcaId": pid, "eskiIlceGeomId": ilce_geom[ilce], "alanPayi": round(geom.area / toplam, 4),
                          "mahalleler": sorted(x["mahalle"] for x in xs if x["mahalle"] and not x.get("cikarim")),
                          "cikarimla": sorted((x["mahalle"] or "mahalle dışı alan") for x in xs if x.get("cikarim"))}
        else:
            pid = f"BELIRSIZ-{kod}"
            ozet["_belirsiz"] = {"parcaId": pid, "alanPayi": round(geom.area / toplam, 4),
                                 "adaylar": sorted({e["ad"] for e in kayit["eskiIlceler"] if e["ad"]}),
                                 "mahalleler": sorted(x["mahalle"] for x in xs if x["mahalle"]),
                                 "mahalleDisiAlan": sum(1 for x in xs if not x["mahalle"])}
        features.append({"type": "Feature", "properties": {"id": pid, "plaka": int(kod.split("-")[0]), "ilce": geom_id,
                                                          "eskiIlce": ilce}, "geometry": mapping(geom)})
    for a in atama:
        a.pop("_geom")
    return {"ad": cfg["ad"], "kanun": cfg["kanun"], "listeNo": kayit["listeNo"], "parcalar": ozet, "atama": atama}, features


def main():
    mahalle_geo = json.loads((ROOT / "geo/normalized/mahalle_geo.json").read_text(encoding="utf-8"))
    modern = {f["properties"]["id"]: shape(f["geometry"])
              for f in json.loads((ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson").read_text(encoding="utf-8"))["features"]}
    rapor, features = {}, []
    for g, cfg in ILCELER.items():
        pl = g.split("-")[2]
        komsu = [v for k, v in modern.items() if k != g and k.split("-")[2] == pl]
        r, f = bolustur(g, cfg, mahalle_geo, modern[g], komsu)
        rapor[g], features = r, features + f
    OUT_JSON.write_text(json.dumps({"not": "build_mahalle_bolusumu.py ile üretilir; elle düzenlenmez.",
                                    "yontem": __doc__.split("Yontem")[1].split("Cikti:")[0].strip(),
                                    "ilceler": rapor}, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_GEO.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False,
                                  separators=(",", ":")), encoding="utf-8")
    for g, r in rapor.items():
        print(r["ad"], {k: (v["alanPayi"], len(v["mahalleler"]), v.get("cikarimla") or v.get("adaylar")) for k, v in r["parcalar"].items()})


if __name__ == "__main__":
    main()
