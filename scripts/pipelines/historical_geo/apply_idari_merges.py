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
  - Kanun listesinde kaynagi yazilmamis 1987 tarihsel birimleri: sayim_kaniti.json (elle; DIE
    1960/1985/1990 nufus sayimi koy/belde baglilgi): Kucukcekmece <- Bakirkoy, Pendik <- Kartal.
  - Merkez cogunlugu: birden cok eski ilceden kurulan (kanun_cok_kaynak) ama birimlerinin en az
    %70'i ilin Merkez ilcesinden (ya da Merkez'in adi degisen halefinden) gelen ilceler butunuyle
    Merkez'e katilir (Aksu, Konyaalti, Defne ...); kucuk diger kaynaklar notta yazilir. Mahalle
    duzeyinde paylastirma denendi ve arsivlendi (arsiv/mahalle-bolusumu/).
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
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur  # noqa: E402
from common.election_io import election_path, load_election, save_election  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = ROOT / "geo/historical/district_splits.json"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
PLAN = IDARI / "merge_plan.json"
NOTLAR = IDARI / "harita_notlari.json"
IST9208 = IDARI / "istanbul_1992_2008.json"
SAYIM = IDARI / "sayim_kaniti.json"
MERKEZ_ESIK = 0.7
ONEK = "HISTK-"
ILCE_DUZEYLI = {"genel", "referandum", "cumhurbaskanligi"}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


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
    birimler = list(oku(IDARI / "district_lineage.json").get("historicalUnits", []))
    # kanunda kaynagi yazilmamis tarihsel birimler: nufus sayimi kitaplarindan eski ilce
    for k in (oku(SAYIM)["birimler"] if SAYIM.exists() else []):
        birimler = [h for h in birimler if h["id"] != k["id"]]
        birimler.append({"id": k["id"], "ad": k["ad"], "kanun": k["kanun"], "tekKaynak": True,
                         "resmiGazete": {"tarih": k["kurulus"]}, "sayimKaniti": True,
                         "eskiIlceler": [{"ad": k["eskiIlce"], "geomId": k["eskiIlceGeomId"], "plaka": k["plaka"]}]})
    for h in birimler:
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

    # Merkez cogunlugu: ana kaynagi Merkez ilce olan cok kaynakli ilceler butunuyle Merkez'e
    cogunluk = {}
    for g, l in lineage.items():
        k = l.get("kanunSoyu") or {}
        if l["lineageStatus"] != "kanun_cok_kaynak" or g in cocuk or not k.get("eskiIlceler"):
            continue
        es = k["eskiIlceler"]
        top, toplam = es[0], sum(e["birimSayisi"] for e in es)
        merkezli = top["ad"] == "Merkez" or (lineage.get(top["geomId"] or "", {}).get("lineageStatus") == "merkez_ilce")
        if not (merkezli and top["geomId"] and toplam and top["birimSayisi"] / toplam >= MERKEZ_ESIK):
            continue
        cocuk[g] = {"ebeveyn": top["geomId"], "kurulus": (l["kurulus"] or {}).get("tarih"),
                    "girmedi": set(l["kurulduAmaSecimeAyriGirmedi"]), "kanun": k["kanun"], "ad": l["ad"],
                    "plaka": l["plaka"]}
        cogunluk[g] = {"ana": top["ad"], "pay": round(top["birimSayisi"] / toplam, 2),
                       "digerleri": [[e["ad"] or "kaynağı yazılmamış", e["birimSayisi"]] for e in es[1:]]}

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
        # haritada 'veri yok' kalacak modern ilceler: o tarihte henuz ayri ilce degilse notu
        kapsanan = set(kapsayan)
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
        if bos:
            not_secim[s["anahtar"]] = dict(sorted(bos))
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
        # birlesim yerlerindeki dikis deliklerini doldur (bileşenlerin kendi delikleri korunur)
        icerik = (hist_parca.get(p["taban"], {p["taban"]}) | set(p["katilanlar"]))
        bilesen = [temiz(shape(modern[x]["geometry"])) for x in icerik if x in modern]
        u = unary_union(geoms)
        yabanci = unary_union([temiz(shape(f["geometry"])) for k, f in modern.items()
                               if k not in icerik and shape(f["geometry"]).intersects(u.envelope)])
        yeni.append({"type": "Feature", "properties": {"id": sid, "plaka": p["plaka"]},
                     "geometry": mapping(delikleri_doldur(u, bilesen_delikleri(bilesen), yabanci))})
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
        yil = min(int(cocuk[x]["kurulus"][:4]) for x in p["katilanlar"] if cocuk[x]["kurulus"])
        splits.setdefault(str(p["plaka"]), []).append({"hideIds": sorted(set(gizle)), "splitYear": yil, "syntheticId": sid})
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")

    # on yuz notlari: geomId -> kuruluş ve kaynak ilceler (yalniz bir secimde bos kalanlar)
    notlar = {}
    guncel_ad = {r["geomId"]: r["ad"] for r in load_election("2023")["ilceler"] if r.get("geomId")}
    for g in sorted({g for v in not_secim.values() for g in v}):
        l = lineage[g]
        k = l.get("kanunSoyu") or {}
        notlar[g] = {"ad": guncel_ad.get(g) or tr_baslik(l["ad"]), "tarih": l["kurulus"]["tarih"],
                     "kanun": l["kurulus"].get("kanun"), "durum": l["lineageStatus"],
                     "kaynaklar": [[e["ad"], e["birimSayisi"]] for e in k.get("eskiIlceler", []) if e.get("ad")]}
    # birlesimler: her tarihsel poligonun bugunku sinirlarla kapsadigi ilceler (+ Merkez cogunlugu notu)
    birlesimler = {}
    # mahalle duzeyinde paylastirilan bugunku ilcelerin payi (build_istanbul_1992_2008.py)
    kismi = {}
    if IST9208.exists():
        k9208 = oku(IST9208)
        for ad, v in k9208["ilceler"].items():
            kismi[v["id"]] = {m: k9208["bugunkuIlceler"][m]["parcalar"][ad]["pay"] for m in v["bugunkuIlceler"]
                              if k9208["bugunkuIlceler"].get(m, {}).get("tur") == "mahalle"}
    for girdiler in splits.values():
        for e in girdiler:
            adlar = sorted({guncel_ad.get(x) or tr_baslik(lineage[x]["ad"]) if x in lineage else x
                            for x in e["hideIds"] if x.startswith("TR-D-")})
            if len(adlar) < 2:
                continue
            b = {"ilceler": adlar}
            if kismi.get(e["syntheticId"]):
                b["paylar"] = {guncel_ad.get(x, x): pay for x, pay in sorted(kismi[e["syntheticId"]].items())}
            cg = [dict(cogunluk[x], ad=guncel_ad.get(x) or tr_baslik(lineage[x]["ad"]))
                  for x in e["hideIds"] if x in cogunluk]
            if cg:
                b["cogunluk"] = cg
            birlesimler[e["syntheticId"]] = b
    NOTLAR.write_text(json.dumps({"not": "apply_idari_merges.py ile üretilir; ön yüzde 'veri yok' poligonların ve "
                                         "tarihsel birleşim poligonlarının açıklaması.",
                                  "ilceler": notlar, "secimler": not_secim, "birlesimler": birlesimler},
                                 ensure_ascii=False, separators=(",", ":")),
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
