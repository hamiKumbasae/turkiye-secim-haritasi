"""
Yerel secimlerin il genel meclisi (igm) ve belediye meclisi (bm) oylarini haritanin okudugu
secim kaydi bicimine (iller/ilceler satirlari, oy: {parti: {oy, oran}}) cevirir.

Kaynak: data/normalized/ek/{il_genel_meclisi,belediye_meclisi}/<yil>yerel.json (YSK acik veri,
sandik duzeyinden il/ilce/belde bazinda toplanmis). Kaynak degerleri degismez; yalniz toplanir.

Kurallar:
  - Iskelet: ayni yilin belediye baskanligi kaydinin (data/normalized/elections/yerel) ilce
    satirlari. Boylece harita cografyasi (geomId'ler) baskanlik haritasiyla ayni kalir.
  - il satiri: kaynagin il toplami. 2014'ten beri buyuksehirlerde il genel meclisi secilmez
    (6360 sayili Kanun); bu illerde igm il satiri sonucsuz ve notlu, ilce satiri yok.
  - igm ilce: ilcenin tamami = kaynakta ilce satiri + o ilcenin belde satirlari (il genel
    meclisinde secim cevresi ilcedir).
  - bm ilce: yalniz ilce belediyesi meclisi (kaynakta beldeId'siz satir); belde meclisleri
    ayri belediyedir, baskanlik haritasinda da ilce = ilce belediyesi.
  - Kaynakta geomId'si olmayan "<Il> Merkez" satirlari (2009; 2012-2013'te bolunen Merkez
    ilceler): baskanlik kaydinda o ilde meclis verisiyle eslesmeyen ve oyu olan TEK satir
    varsa ona baglanir; birden cok ya da hic yoksa baglanmaz (tahmin yok) ve raporlanir.
    Belde adlari kaynakta yok; sonradan ilce olan beldeler ayri cizilmez (igm'de ana ilceye
    dahil, bm'de gosterilmez).
  - kazanan: bm'de kaynagin kazanani; igm ilcede toplanan oylarin birincisi (esitlikte bos).
  - oran = oy / gecerliOy * 100 (2 ondalik); katilim = oyKullanan / secmen * 100.

Cikti: data/normalized/meclis_harita/<yil>yerel_<igm|bm>.json

Kullanim:
  .venv/bin/python scripts/pipelines/meclis_harita/build_meclis_harita.py
"""
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
NORM = ROOT / "data" / "normalized"
OUT = NORM / "meclis_harita"
YILLAR = ["2009yerel", "2014yerel", "2019yerel", "2024yerel"]
TURLER = {"igm": ("il_genel_meclisi", "İl Genel Meclisi"), "bm": ("belediye_meclisi", "Belediye Meclisi")}
BUYUKSEHIR_IGM_NOTU = "Bu ilde il genel meclisi seçimi yapılmadı (büyükşehir, 6360 sayılı Kanun)."


def oku(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def oy_bicimi(oy, gecerli):
    return {k: {"oy": v, "oran": round(v / gecerli * 100, 2) if gecerli else None}
            for k, v in sorted(oy.items(), key=lambda x: -x[1]) if v}


def birinci(oy):
    s = sorted(oy.items(), key=lambda x: -x[1])
    if not s or (len(s) > 1 and s[0][1] == s[1][1]):
        return None
    return s[0][0]


def katilim(r):
    return round(r["oyKullanan"] / r["secmen"] * 100, 2) if r.get("secmen") and r.get("oyKullanan") is not None else None


def topla(birimler):
    oy = collections.Counter()
    t = collections.Counter()
    for b in birimler:
        oy.update(b["oy"])
        for k in ("sandik", "secmen", "oyKullanan", "gecerliOy"):
            t[k] += b.get(k) or 0
    return oy, t


def kur(yil, kisa):
    dosya, adi = TURLER[kisa]
    ek = oku(NORM / "ek" / dosya / f"{yil}.json")
    ana = oku(NORM / "elections" / "yerel" / f"{yil}.json")
    ek_geom = {b["geomId"] for b in ek["birimler"] if b["geomId"]}

    # geomId'siz Merkez satirlari -> baskanlik kaydindaki tek aday satir
    merkez_hedef, rapor = {}, []
    for (pl, ilce) in sorted({(b["plaka"], b["ilce"]) for b in ek["birimler"] if not b["geomId"]}):
        aday = [r for r in ana["ilceler"] if r["plaka"] == pl and r["geomId"] not in ek_geom and (r.get("gecerliOy") or 0) > 0]
        if len(aday) == 1:
            merkez_hedef[(pl, ilce)] = aday[0]["geomId"]
        else:
            rapor.append((pl, ilce, [r["ad"] for r in aday]))

    geom_birim = collections.defaultdict(list)
    for b in ek["birimler"]:
        if kisa == "bm" and b.get("beldeId"):
            continue
        g = b["geomId"] or merkez_hedef.get((b["plaka"], b["ilce"]))
        if g:
            geom_birim[g].append(b)

    ek_il = {r["plaka"]: r for r in ek["iller"]}
    iller = []
    for a in ana["iller"]:
        r = ek_il.get(a["plaka"])
        if not r:
            iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": {}, "kazanan": None, "vekil": {}, "toplamVekil": 0,
                          "not": BUYUKSEHIR_IGM_NOTU if kisa == "igm" and yil != "2009yerel" else "Bu ilde kaynakta sonuç yok."})
            continue
        iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": oy_bicimi(r["oy"], r["gecerliOy"]),
                      "kazanan": r["kazanan"], "gecerliOy": r["gecerliOy"], "secmen": r["secmen"],
                      "sandik": r["sandik"], "katilim": katilim(r), "ilceSayisi": a.get("ilceSayisi"),
                      "vekil": {}, "toplamVekil": 0})
    ilceler = []
    for a in ana["ilceler"]:
        if a["plaka"] not in ek_il:
            continue
        bs = geom_birim.get(a["geomId"], [])
        if not bs:
            ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"], "oy": {}, "kazanan": None,
                            "vekil": {}, "toplamVekil": 0})
            continue
        oy, t = topla(bs)
        kaz = bs[0]["kazanan"] if kisa == "bm" and len(bs) == 1 else birinci(oy)
        ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"], "oy": oy_bicimi(oy, t["gecerliOy"]),
                        "kazanan": kaz, "gecerliOy": t["gecerliOy"], "secmen": t["secmen"], "sandik": t["sandik"],
                        "katilim": katilim(t), "vekil": {}, "toplamVekil": 0})

    ulusal = collections.Counter()
    for r in ek["iller"]:
        ulusal.update(r["oy"])
    top = sum(ulusal.values())
    kazananlar = {r["kazanan"] for r in iller if r["kazanan"]}
    major = [p for p, v in ulusal.most_common() if p in kazananlar or v / top >= 0.01]

    kayit = {"ad": ana["ad"], "tur": "yerel", "oylama": kisa, "oylamaAdi": adi, "contestType": "council_votes",
             "resultBasis": "votes", "toplamSandalye": None, "majorPartiler": major,
             "kaynak": {"dosya": f"data/normalized/ek/{dosya}/{yil}.json", **ek["kaynak"]},
             "iller": iller, "ilceler": ilceler}
    baglanmayan = sum(b["gecerliOy"] for b in ek["birimler"] if not (b["geomId"] or merkez_hedef.get((b["plaka"], b["ilce"])))
                      and not (kisa == "bm" and b.get("beldeId")))
    return kayit, rapor, merkez_hedef, baglanmayan


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for yil in YILLAR:
        for kisa in TURLER:
            kayit, rapor, hedef, bag = kur(yil, kisa)
            (OUT / f"{yil}_{kisa}.json").write_text(json.dumps(kayit, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                                                  encoding="utf-8")
            veri = sum(1 for r in kayit["ilceler"] if r["oy"])
            print(f"{yil}_{kisa}: il {sum(1 for r in kayit['iller'] if r['oy'])}/{len(kayit['iller'])}, "
                  f"ilçe {veri}/{len(kayit['ilceler'])}, Merkez bağlanan {len(hedef)}, bağlanmayan oy {bag}")
            for r in rapor:
                print("   bağlanmadı:", r)


if __name__ == "__main__":
    main()
