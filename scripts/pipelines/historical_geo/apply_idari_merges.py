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
  - Kanunla kurulup sonradan bolunmus tarihsel birimler (district_lineage.json ->
    historicalUnits, tek kaynakli olanlar; ornek: Buyukcekmece 1987 <- Catalca) modern
    parcalarina (district_splits.json hideIds) acilarak ayni kuralla katilir; "ayri
    girmedi" kosulu birimin herhangi bir parcasinin ilce duzeyli secimde ilk gorundugu
    tarihten hesaplanir.
  - Cok kaynakli ilceler (mahalle_bolusumu.json, build_mahalle_bolusumu.py): alan mahalle
    duzeyinde eski ilceler arasinda paylastirilmis; her eski ilcenin parcasi (PARCA-*)
    onun satirina katilir, paylastirilamayan kisim (BELIRSIZ-*) tarali not olarak cizilir.
    Eski ilcelerden biri o secimde bulunamazsa bolusum uygulanmaz.
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
NOTLAR = IDARI / "harita_notlari.json"
BOLUSUM = IDARI / "mahalle_bolusumu.json"
BOLUSUM_GEO = IDARI / "mahalle_bolusumu.geojson"
BELIRSIZ = "BELIRSIZ-"
ONEK = "HISTK-"
ILCE_DUZEYLI = {"genel", "referandum", "cumhurbaskanligi"}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def parca_adi(parca_geo, pid, lineage):
    c = parca_geo[pid]["properties"]["ilce"]
    return f"{tr_baslik(lineage[c]['ad'])} ({parca_geo[pid]['properties']['eskiIlce']} parçası, mahalle düzeyi)"


def bolusum_kanun(parca_geo, pid, lineage):
    return lineage[parca_geo[pid]["properties"]["ilce"]]["kurulus"]["kanun"]


def tr_baslik(s):
    """'TİLLO' -> 'Tillo' (Turkce buyuk/kucuk harf)"""
    return " ".join(w[:1] + w[1:].replace("I", "ı").replace("İ", "i").lower() for w in s.split())


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

    # tek kaynakli tarihsel birimler -> modern parcalari sozde cocuk
    ilk_gorunum = {}   # modern geomId -> ilce duzeyli secimde ilk kapsandigi tarih
    for s in secimler():
        if s["tur"] not in ILCE_DUZEYLI:
            continue
        try:
            kayit = load_election(s["anahtar"])
        except FileNotFoundError:
            continue
        for r in kayit.get("ilceler") or []:
            g = r.get("geomId") or ""
            g = eski_plan[g]["taban"] if g.startswith(ONEK) else g
            for parca in hist_parca.get(g, {g}) | {g}:
                if parca not in ilk_gorunum or s["tarih"] < ilk_gorunum[parca]:
                    ilk_gorunum[parca] = s["tarih"]
    tarihsel_cocuk, rapor_on = {}, collections.defaultdict(list)
    for h in oku(IDARI / "district_lineage.json").get("historicalUnits", []):
        if not (h["tekKaynak"] and h["eskiIlceler"][0]["geomId"] and h["id"] in hist_parca):
            continue
        parcalar = hist_parca[h["id"]]
        if parcalar <= hist_parca.get(h["eskiIlceler"][0]["geomId"], set()):
            continue  # ebeveynin tarihsel poligonu birimi zaten iceriyor (Konak1991 < Konak84)
        ilk = min((ilk_gorunum[x] for x in parcalar if x in ilk_gorunum), default=None)
        for x in sorted(parcalar):
            if x in cocuk:
                rapor_on["tarihselBirimCakisma"].append({"birim": h["id"], "parca": x})
                continue
            tarihsel_cocuk[x] = h["id"]
            cocuk[x] = {"ebeveyn": h["eskiIlceler"][0]["geomId"], "kurulus": h["resmiGazete"]["tarih"],
                        "ilkGorunum": ilk, "girmedi": set(), "kanun": h["kanun"],
                        "ad": f"{h['ad']} ({h['resmiGazete']['tarih'][:4]} sınırı: {lineage[x]['ad'] if x in lineage else x})",
                        "plaka": h["eskiIlceler"][0]["plaka"], "tarihselBirim": h["id"]}

    # mahalle bolusumu: cok kaynakli cocuk -> [(eski ilce geomId, parca id)], belirsiz parca
    bolusum = {}
    if BOLUSUM.exists():
        for c, b in oku(BOLUSUM)["ilceler"].items():
            bolusum[c] = {"parcalar": [(v["eskiIlceGeomId"], v["parcaId"]) for k, v in b["parcalar"].items() if k != "_belirsiz"],
                          "belirsiz": b["parcalar"].get("_belirsiz"), "ad": b["ad"]}
    parca_geo = {f["properties"]["id"]: f for f in oku(BOLUSUM_GEO)["features"]} if BOLUSUM_GEO.exists() else {}

    plan, rapor = {}, rapor_on
    satir_degisim = collections.Counter()
    modern_plaka = {f["properties"]["id"]: f["properties"]["plaka"] for f in oku(MODERN)["features"]}
    ilk_ayri = {g: v for g, v in ilk_gorunum.items()}
    not_secim = {}
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
                    (s["tur"] in ILCE_DUZEYLI and s["anahtar"] in bilgi["girmedi"]) or \
                    (s["tur"] in ILCE_DUZEYLI and bilgi.get("tarihselBirim") and bilgi["ilkGorunum"]
                     and bilgi["kurulus"] <= s["tarih"] < bilgi["ilkGorunum"])
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
        # mahalle bolusumu: cocugun parcalari eski ilcelerinin (zincirle) satirlarina
        katilan_parca, bolunen, belirsiz_bu = collections.defaultdict(set), set(), []
        for c, b in sorted(bolusum.items()):
            l = lineage.get(c) or {}
            kur = (l.get("kurulus") or {}).get("tarih")
            if c in kapsayan or not kur:
                continue
            if not (kur > s["tarih"] or (s["tur"] in ILCE_DUZEYLI and s["anahtar"] in set(l.get("kurulduAmaSecimeAyriGirmedi", [])))):
                continue
            hedefler = []
            for eski, pid in b["parcalar"]:
                hedef, e = None, eski
                for _ in range(6):
                    if e in kapsayan:
                        hedef = kapsayan[e]
                        break
                    if e in cocuk:
                        e = cocuk[e]["ebeveyn"]
                        continue
                    break
                hedefler.append((hedef, pid))
            if any(h is None for h, _ in hedefler):
                rapor["bolusumUygulanmadi"].append({"secim": s["anahtar"], "ilce": c,
                                                    "bulunamayan": [pid for h, pid in hedefler if h is None]})
                continue
            for h, pid in hedefler:
                katilan_parca[h].add(pid)
                katilan.setdefault(h, set())
            bolunen.add(c)
            if b["belirsiz"]:
                belirsiz_bu.append(b["belirsiz"]["parcaId"])
        for hedef, parcalar in katilan.items():
            # zincirdeki ara ebeveynler bu secimde ayri satir olabilir mi? olamaz: kapsayan'da yoklar
            parcalar = {p for p in parcalar if p not in kapsayan}
            pparca = katilan_parca.get(hedef, set())
            if not parcalar and not pparca:
                continue
            anahtar = hedef + "|" + ",".join(sorted(parcalar)) + ("|" + ",".join(sorted(pparca)) if pparca else "")
            sid = f"{ONEK}{hedef.replace('TR-D-', '')}-{hashlib.sha1(anahtar.encode()).hexdigest()[:6]}"
            p = plan.setdefault(sid, {"taban": hedef, "katilanlar": sorted(parcalar), "secimler": [],
                                      "plaka": int(hedef.split("-")[2]) if hedef.startswith("TR-D-") else
                                      next(f["properties"]["plaka"] for f in hist["features"] if f["properties"]["id"] == hedef),
                                      "kanunlar": sorted({cocuk[x]["kanun"] for x in parcalar} |
                                                         {bolusum_kanun(parca_geo, x, lineage) for x in pparca}),
                                      "adlar": sorted([cocuk[x]["ad"] for x in parcalar] +
                                                      [parca_adi(parca_geo, x, lineage) for x in pparca]),
                                      **({"parcalar": sorted(pparca)} if pparca else {})})
            p["secimler"].append(s["anahtar"])
            for r in kayit["ilceler"]:
                if r.get("geomId") == hedef:
                    r["geomId"] = sid
                    satir_degisim[s["anahtar"]] += 1
        # haritada 'veri yok' kalacak modern ilceler: o tarihte henuz ayri ilce degilse notu
        kapsanan = set(kapsayan) | bolunen
        for hedef, parcalar in katilan.items():
            kapsanan |= parcalar
        satirli_il = {r["plaka"] for r in kayit["ilceler"] if r.get("geomId")}
        bos = []
        for g, pl in modern_plaka.items():
            l = lineage.get(g)
            if g in kapsanan or pl not in satirli_il or not l or not (l.get("kurulus") or {}).get("tarih"):
                continue
            kur = l["kurulus"]["tarih"]
            if kur > s["tarih"]:
                bos.append((g, 0))
            elif s["tur"] in ILCE_DUZEYLI and s["tarih"] < ilk_ayri.get(g, "9999"):
                bos.append((g, 1))   # kanunla kurulmus ama bu secime ayri girmemis
        bos += [(x, 0) for x in belirsiz_bu]
        if bos:
            not_secim[s["anahtar"]] = dict(sorted(bos))
        eski_hali = json.loads(election_path(s["anahtar"]).read_text(encoding="utf-8"))
        if eski_hali != kayit:
            save_election(s["anahtar"], kayit)

    # geometri: taban (modern ya da repodaki HIST) + katilan modern ilceler
    modern = {f["properties"]["id"]: f for f in oku(MODERN)["features"]}
    hist_by = {f["properties"]["id"]: f for f in hist["features"]
               if not f["properties"]["id"].startswith((ONEK, BELIRSIZ))}
    yeni = []
    for sid, p in sorted(plan.items()):
        taban = modern.get(p["taban"]) or hist_by.get(p["taban"])
        geoms = [temiz(shape(taban["geometry"]))] + [temiz(shape(modern[x]["geometry"])) for x in p["katilanlar"]] + \
                [temiz(shape(parca_geo[x]["geometry"])) for x in p.get("parcalar", [])]
        yeni.append({"type": "Feature", "properties": {"id": sid, "plaka": p["plaka"]},
                     "geometry": mapping(unary_union(geoms))})
    # paylastirilamayan parcalar: yalniz ilgili secimlerde tarali not olarak cizilir
    for pid in sorted({x for v in not_secim.values() for x in v if x.startswith(BELIRSIZ)}):
        f = parca_geo[pid]
        yeni.append({"type": "Feature", "properties": {"id": pid, "plaka": f["properties"]["plaka"]}, "geometry": f["geometry"]})
    hist["features"] = sorted(list(hist_by.values()) + yeni, key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # district_splits: HISTK kayitlari yeniden yazilir
    for pl in list(splits):
        splits[pl] = [e for e in splits[pl] if not e["syntheticId"].startswith(ONEK)]
        if not splits[pl]:
            del splits[pl]
    for sid, p in sorted(plan.items()):
        bolunenler = [parca_geo[x]["properties"]["ilce"] for x in p.get("parcalar", [])]
        gizle = sorted(hist_parca.get(p["taban"], {p["taban"]}) | {p["taban"]} if p["taban"].startswith("TR-D-")
                       else hist_parca[p["taban"]]) + p["katilanlar"] + bolunenler
        yil = min([int(cocuk[x]["kurulus"][:4]) for x in p["katilanlar"] if cocuk[x]["kurulus"]] +
                  [int(lineage[c]["kurulus"]["tarih"][:4]) for c in bolunenler])
        splits.setdefault(str(p["plaka"]), []).append({"hideIds": sorted(set(gizle)), "splitYear": yil, "syntheticId": sid})
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")

    # on yuz notlari: geomId -> kuruluş ve kaynak ilceler (yalniz bir secimde bos kalanlar)
    notlar = {}
    guncel_ad = {r["geomId"]: r["ad"] for r in load_election("2023")["ilceler"] if r.get("geomId")}
    for g in sorted({g for v in not_secim.values() for g in v}):
        if g.startswith(BELIRSIZ):
            c = parca_geo[g]["properties"]["ilce"]
            l, b = lineage[c], bolusum[c]["belirsiz"]
            k = l.get("kanunSoyu") or {}
            notlar[g] = {"ad": guncel_ad.get(c) or tr_baslik(l["ad"]), "tarih": l["kurulus"]["tarih"],
                         "kanun": l["kurulus"].get("kanun"), "durum": "belirsiz_parca", "alanPayi": b["alanPayi"],
                         "mahalleler": [tr_baslik(m.removesuffix(" MAH.")) for m in b["mahalleler"]],
                         "kaynaklar": [[e["ad"], e["birimSayisi"]] for e in k.get("eskiIlceler", []) if e.get("ad")]}
            continue
        l = lineage[g]
        k = l.get("kanunSoyu") or {}
        notlar[g] = {"ad": guncel_ad.get(g) or tr_baslik(l["ad"]), "tarih": l["kurulus"]["tarih"],
                     "kanun": l["kurulus"].get("kanun"), "durum": l["lineageStatus"],
                     "kaynaklar": [[e["ad"], e["birimSayisi"]] for e in k.get("eskiIlceler", []) if e.get("ad")]}
    NOTLAR.write_text(json.dumps({"not": "apply_idari_merges.py ile üretilir; ön yüzde 'veri yok' poligonların açıklaması.",
                                  "ilceler": notlar, "secimler": not_secim}, ensure_ascii=False, separators=(",", ":")),
                      encoding="utf-8")
    ozet = {"sentetik": len(plan), "satirDegisimi": sum(satir_degisim.values()),
            "secimBasina": dict(sorted(satir_degisim.items())), "katilanIlce": len({x for p in plan.values() for x in p["katilanlar"]}),
            "hedefBulunamadi": len(rapor["hedefBulunamadi"]),
            "notluBosPoligon": sum(len(v) for v in not_secim.values())}
    PLAN.write_text(json.dumps({"not": "apply_idari_merges.py ile üretilir; elle düzenlenmez.", "ozet": ozet,
                                "sentetikler": plan, **rapor}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
