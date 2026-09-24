"""
data/kaynaklar/tuik/referandum/<secim>.json'daki ILCE sonuclarini, ilce
satiri HIC OLMAYAN 1961/1982/1987/1988 referandumlarinin normalize kaydina
yazar. 2007referandum'a dokunulmaz (ilce duzeyi zaten YSK'den var).

Il satirlarinin degerlerine dokunulmaz (YSK resmi il arsivi; TUIK il
toplamlari bunlarla 4 yilda da birebir ayni - extract adiminda kontrol
edildi). Il satirina yalnizca `ilceSayisi` ve `sehirKoy` eklenir.

Ad: kaynak PDF'te "ı" harfi dusmus ("Fndkl"). Dogru yazim, ayni plakadaki
ilcelerin donemin en yakin TUIK genel secim satirlarindaki (1961/1983/1987)
yazimindan alinir ("ı" yok sayilarak eslenir). geomId: merge_yerel_ilce.py
ile ayni kural (en yakin genel secimin geomId'si; proje yeni sinir karari
vermez).

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/merge_halkoylamasi_ilce.py           # kuru calisma
  python3 scripts/pipelines/tuik_arsiv/merge_halkoylamasi_ilce.py --write
"""
import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE.parent / "wikipedia_arsiv"))
import merge_yerel_ilce as my  # noqa: E402
from merge_into_normalized import METRO_MERKEZ  # noqa: E402  (genel_ilce_1961_1987)
from common.election_io import load_election, save_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
SRC = ROOT / "data" / "kaynaklar" / "tuik" / "referandum"
YAKIN = {"1961referandum": "1961", "1982referandum": "1983", "1987referandum": "1987", "1988referandum": "1987"}
AD_REF = {"1961referandum": ["1961", "1965"], "1982referandum": ["1983", "1977"],
          "1987referandum": ["1987", "1983"], "1988referandum": ["1987", "1989yerel", "1991"]}


# Kaynaktaki kisaltma / donem adlari -> referans (projede kullanilan) ad
AD_ALIAS = {"YMAHALLE": "Yenimahalle", "MKEMALPASA": "Mustafakemalpaşa", "IMROZ": "Gökçeada",
            "POTURGE": "Pütürge", "SINCANL": "Sinanpaşa", "MAGARA": "Tufanbeyli", "DEVREKANI": "Devrakani"}
# Eylul 1987 referandumunda Adana Merkez henuz tek satir (Seyhan/Yuregir ayrimi
# 1988'de goruluyor) -> bolunmenin halefleri birlesimi olan ayni tarihsel poligon
METRO_EK = {(1, "1987referandum"): "HIST-Adana-Merkez"}
ILCE_DEGIL = {"GUMRUK KAPLAR", "GUMRUK KAPILARI"}  # gumruk kapisi oylari: ilce degil


def _ı_siz(s):
    return fold(s).replace("I", "")


def ad_indeksi(secim):
    idx = {}
    for ref in AD_REF[secim]:
        for r in load_election(ref)["ilceler"]:
            idx.setdefault((r["plaka"], _ı_siz(r["ad"])), r["ad"])
    return idx


def _sk(sk, kaynak):
    if not sk:
        return None
    out = {}
    for tip, v in sk.items():
        out[tip] = {"sandik": v["sandik"], "secmen": v["secmen"], "oyKullanan": v["oyKullanan"],
                    "gecersizOy": v["gecersizOy"], "gecerliOy": v["gecerliOy"],
                    "oy": {"Evet": v["evet"], "Hayır": v["hayir"]}}
    out["kaynak"] = kaynak
    return out


def satir(i, plaka, ad, gid, kaynak):
    g = i["gecerliOy"]
    oy = {"Evet": i["evet"], "Hayır": i["hayir"]}
    r = {"ad": ad, "plaka": plaka, "geomId": gid, "secmen": i["secmen"], "sandik": i["sandik"],
         "gecerliOy": g, "gecersizOy": i["gecersizOy"],
         "katilim": round(i["oyKullanan"] * 100 / i["secmen"], 2) if i["secmen"] else None,
         "kazanan": "Evet" if i["evet"] >= i["hayir"] else "Hayır",
         "oy": {k: {"oran": round(v * 100 / g, 2) if g else 0.0, "oy": v} for k, v in oy.items()},
         "toplamVekil": 0, "vekil": {}}
    k = dict(kaynak, sayfa=i["sayfa"], adKaynakta=i["adKaynakta"])
    if i.get("kontrol"):
        k["kaynakIciTutarsizlik"] = i["kontrol"]
    r["kaynak"] = k
    s = _sk(i.get("sehirKoy"), {"ana": "tuik", "not": "Şehir = il/ilçe merkezi; köy = bucak ve köyler."})
    if s:
        r["sehirKoy"] = s
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    ctx = my.ref_index()
    for secim, yakin in YAKIN.items():
        my.YAKIN_GENEL[secim] = yakin
        src = json.loads((SRC / f"{secim}.json").read_text(encoding="utf-8"))
        rec = load_election(secim)
        if rec["ilceler"]:
            print(secim, "zaten ilce verisi var, atlandi")
            continue
        adlar = ad_indeksi(secim)
        kaynak = {"ana": "tuik", "yayin": src["yayin"], "hamDosya": src["hamDosya"],
                  "kaynakKatmani": f"data/kaynaklar/tuik/referandum/{secim}.json"}
        rows, via, adsiz = [], collections.Counter(), []
        il_by = {r["plaka"]: r for r in rec["iller"]}
        for il in src["iller"]:
            pl = il["plaka"]
            for i in il["ilceler"]:
                if fold(i["adKaynakta"]) in ILCE_DEGIL:
                    continue
                ad = adlar.get((pl, _ı_siz(i["adKaynakta"]))) or AD_ALIAS.get(fold(i["adKaynakta"]).replace(" ", ""))
                if ad is None:
                    ad = AD_ALIAS.get(fold(i["adKaynakta"]))
                if ad is None:
                    adsiz.append(f"{il['adKaynakta']}/{i['adKaynakta']}")
                    ad = i["adKaynakta"]
                if fold(ad) == "MERKEZ" and (pl, secim) in METRO_EK:
                    gid, how = METRO_EK[(pl, secim)], "metro_merkez"
                elif fold(ad) == "MERKEZ" and (pl, yakin) in METRO_MERKEZ:
                    gid, how = METRO_MERKEZ[(pl, yakin)], "metro_merkez"
                else:
                    gid, how = my.resolve(ctx, secim, pl, ad, il["adKaynakta"])
                via[how.split(":")[0]] += 1
                rows.append(satir(i, pl, ad, gid, kaynak))
            s = _sk(il.get("sehirKoy"), {"ana": "tuik", "yayin": src["yayin"], "sayfa": il["sayfa"]})
            if s:
                il_by[pl]["sehirKoy"] = s
        # ayni geomId'ye iki satir (cakisma) -> ikisi de haritadan cikar
        by = collections.defaultdict(list)
        for r in rows:
            if r["geomId"]:
                by[r["geomId"]].append(r)
        cakisan = []
        for gid, rs in by.items():
            if len(rs) > 1:
                cakisan.append(f"{gid}: " + " / ".join(r["ad"] for r in rs))
                for r in rs:
                    r["geomId"] = None
        sayac = collections.Counter(r["plaka"] for r in rows)
        for il in rec["iller"]:
            il["ilceSayisi"] = sayac.get(il["plaka"], 0)
        print(f"{secim}: {len(rows)} ilce, geomId'li {sum(1 for r in rows if r['geomId'])}, eslesme {dict(via)}")
        print(f"   adi referansta bulunamayan: {adsiz}")
        print(f"   geomId bulunamayan: {[r['ad'] + '(' + str(r['plaka']) + ')' for r in rows if not r['geomId']]}")
        if cakisan:
            print(f"   cakisan: {cakisan}")
        if args.write:
            rec["ilceler"] = rows
            save_election(secim, rec)
    if not args.write:
        print("\n(kuru calisma - yazmak icin --write)")


if __name__ == "__main__":
    main()
