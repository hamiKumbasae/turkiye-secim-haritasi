"""
1991-2007 genel secimlerinin ILCE satirlarini iki kaynak katmanindan kurar ve
her satira KOKEN (`kaynak`) yazar:

  taban    data/kaynaklar/mertnuhoglu/genel/<yil>.json  (onceki ilce verisi,
           GitHub mertnuhoglu/secim_verileri, memurlar.net kaynakli; git f4fab3a)
  resmi    data/kaynaklar/tuik/genel/<yil>.json          (TUIK secimdagitimapp)

Kural: TABAN DEGER KORUNUR; sadece TUIK'in farkli oldugu ya da tabanda HIC
OLMAYAN alanlar TUIK'ten alinir ve her biri eski/yeni degeriyle satirin
`kaynak.farklar` listesine yazilir. Degeri TUIK ile birebir ayni olan satir
`kaynak.teyit = ["tuik"]` alir. Yalnizca TUIK'te olan satir (Eminonu)
`kaynak.ana = "tuik"`.

Satir koken semasi:
  "kaynak": {"ana": "mertnuhoglu" | "tuik",
             "teyit": ["tuik"],                              # tum alanlar ayniysa
             "farklar": [{"alan": "oy.YENP95", "kaynak": "tuik",
                          "eski": null, "yeni": 487}, ...],
             "tuikHam": "data/raw/tuik/.../<yil>/<dosya>.html"}

Bilinen farklar (2026-09-24):
  - 1995: tabanda Yeni Parti (YENP95) oylari 899 ilcede yoktu
  - Fatih: tabanda Fatih+Eminonu TEK satir; TUIK Eminonu'yu ayri veriyor ->
    Eminonu kendi satiri (HIST-Istanbul-Eminonu), Fatih HIST-Istanbul-Fatih
  - 2007: proje DTP destekli bagimsizlari (kazandiklari ilcelerde) "DTP"
    etiketliyor - TUIK'te "BĞMZ". Bu bir etiket farki, deger farki sayilmaz.

Il satirlarinin degerlerine dokunulmaz (YSK resmi il arsivi), sadece
`ilceSayisi` guncellenir ve `sehirKoy` eklenir.

Sehir/koy kirilimi (`sehirKoy`): TUIK'in her ilce icin verdigi "Şehir toplamı"
ve "Bucak ve köyler toplamı"; il satirinda secim cevrelerinin toplami. Projede
baska hicbir kaynakta yok; `sehirKoy.kaynak.ana = "tuik"`.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/merge_tuik_ilce_1991_2007.py           # kuru calisma
  python3 scripts/pipelines/tuik_arsiv/merge_tuik_ilce_1991_2007.py --write
"""
import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from common.election_io import load_election, save_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
SRC = ROOT / "data" / "kaynaklar" / "tuik" / "genel"
TABAN = ROOT / "data" / "kaynaklar" / "mertnuhoglu" / "genel"
YILLAR = ["1991", "1995", "1999", "2002", "2007"]

# TUIK yazimi -> mevcut satirin yazimi. Anahtar: (plaka, fold(tuik_adi))
ALIAS = {
    (3, "SINCANLI"): "Sinanpaşa", (4, "DOGUBEYAZIT"): "Doğubayazıt",
    (6, "SKOCHISAR"): "Şereflikoçhisar", (7, "KALE"): "Demre",
    (9, "YENIHISAR"): "Didim (Yenihisar)", (9, "DIDIM"): "Didim (Yenihisar)",
    (16, "MKEMALPASA"): "Mustafakemalpaşa", (22, "SULEOGLU"): "Süloğlu",
    (27, "KARGAMIS"): "Karkamış", (28, "SKARAHISAR"): "Şebinkarahisar",
    (31, "SAMANDAG"): "Samandağı", (37, "DEVREKANI"): "Devrakani",
    (44, "ARAPKIR"): "Arapgir", (44, "POTURGE"): "Pütürge",
    (46, "CAGLIYANCERIT"): "Çağlayancerit",
    (59, "MEREGLI"): "Marmaraereğlisi", (59, "MEREGLISI"): "Marmaraereğlisi",
    (14, "CUMAOVA"): "Cumayeri", (34, "GOSMANPASA"): "Gaziosmanpaşa",
    (34, "KCEKMECE"): "Küçükçekmece", (34, "BCEKMECE"): "Büyükçekmece",
}
EMINONU = "HIST-Istanbul-Eminonu"
FATIH = "HIST-Istanbul-Fatih"


def tuik_oy(ilce, esleme):
    oy = collections.Counter()
    for h, v in ilce["partiler"].items():
        oy[esleme[h]] += v or 0
    return oy


def _katilim(secmen, kullanan):
    return round(kullanan * 100 / secmen, 2) if secmen and kullanan is not None else None


def birlestir(eski, ilce, esleme, ham, plaka, ad, geom_id):
    """eski (taban) satir + TUIK ilcesi -> kokenli satir."""
    t_oy = tuik_oy(ilce, esleme)
    if eski is None:
        gecerli = ilce["gecerliOy"]
        satir = {"ad": ad, "plaka": plaka, "geomId": geom_id, "secmen": ilce.get("secmen"),
                 "sandik": ilce.get("sandik"), "gecerliOy": gecerli,
                 "katilim": _katilim(ilce.get("secmen"), ilce.get("oyKullanan")),
                 "oy": {k: {"oran": round(v * 100 / gecerli, 2) if gecerli else 0.0, "oy": v}
                        for k, v in sorted(t_oy.items(), key=lambda kv: -kv[1])},
                 "kaynak": {"ana": "tuik", "tuikHam": ham}}
        satir["kazanan"] = max(t_oy, key=t_oy.get) if any(t_oy.values()) else None
        return satir
    # proje etiketi: DTP destekli bagimsizlar (TUIK'te BĞMZ icinde)
    dtp = eski["oy"].get("DTP", {}).get("oy") or 0
    if dtp:
        t_oy["Bağımsız"] -= min(dtp, t_oy["Bağımsız"])
        t_oy["DTP"] += dtp
    satir = json.loads(json.dumps(eski))
    satir["geomId"] = geom_id
    farklar = []
    t_meta = {"secmen": ilce.get("secmen"), "sandik": ilce.get("sandik"), "gecerliOy": ilce.get("gecerliOy")}
    for alan, yeni in t_meta.items():
        if yeni is not None and eski.get(alan) != yeni:
            farklar.append({"alan": alan, "kaynak": "tuik", "eski": eski.get(alan), "yeni": yeni})
            satir[alan] = yeni
    for parti in sorted(set(t_oy) | set(eski["oy"])):
        e = eski["oy"].get(parti, {}).get("oy") or 0
        y = t_oy.get(parti, 0)
        if e != y:
            farklar.append({"alan": "oy." + parti, "kaynak": "tuik", "eski": eski["oy"].get(parti, {}).get("oy"), "yeni": y})
            satir["oy"].setdefault(parti, {})["oy"] = y
    if farklar:
        g = satir["gecerliOy"]
        for v in satir["oy"].values():
            v["oran"] = round(v["oy"] * 100 / g, 2) if g else 0.0
        satir["oy"] = dict(sorted(satir["oy"].items(), key=lambda kv: (-kv[1]["oy"], kv[0])))
        if any(f["alan"] in ("secmen",) for f in farklar):
            satir["katilim"] = _katilim(satir["secmen"], ilce.get("oyKullanan"))
        oys = {k: v["oy"] for k, v in satir["oy"].items()}
        satir["kazanan"] = max(oys, key=oys.get) if any(oys.values()) else None
        if satir["kazanan"] != eski.get("kazanan"):
            farklar.append({"alan": "kazanan", "kaynak": "tuik", "eski": eski.get("kazanan"), "yeni": satir["kazanan"]})
        satir["kaynak"] = {"ana": "mertnuhoglu", "farklar": farklar, "tuikHam": ham}
    else:
        satir["kaynak"] = {"ana": "mertnuhoglu", "teyit": ["tuik"], "tuikHam": ham}
    return satir


def sehir_koy(kirilim, esleme, ham):
    """TUIK'in 'Şehir toplamı' / 'Bucak ve köyler toplamı' kirilimi -> satir alani.
    Degerler TUIK'ten oldugu gibi; parti anahtarlari eslenmis. 2007'deki proje
    etiketi (DTP) burada UYGULANMAZ - TUIK'in kendi 'Bağımsız'i korunur."""
    if not kirilim:
        return None
    out = {}
    for tip in ("sehir", "koy"):
        k = kirilim.get(tip)
        if not k:
            continue
        oy = collections.Counter()
        for h, v in k["partiler"].items():
            oy[esleme[h]] += v or 0
        out[tip] = {"sandik": k.get("sandik"), "secmen": k.get("secmen"), "oyKullanan": k.get("oyKullanan"),
                    "gecerliOy": k.get("gecerliOy"),
                    "oy": {p: v for p, v in sorted(oy.items(), key=lambda kv: -kv[1]) if v}}
    out["kaynak"] = {"ana": "tuik", "tuikHam": ham,
                     "not": "Şehir = il/ilçe merkezi belediye sınırı; köy = bucak ve köyler (TÜİK tanımı)."}
    return out


def _topla(a, b):
    if a is None:
        return json.loads(json.dumps(b))
    for tip in ("sehir", "koy"):
        if tip not in b:
            continue
        x, y = a.setdefault(tip, {"oy": {}}), b[tip]
        for f in ("sandik", "secmen", "oyKullanan", "gecerliOy"):
            x[f] = (x.get(f) or 0) + (y.get(f) or 0)
        for p, v in y["oy"].items():
            x["oy"][p] = x["oy"].get(p, 0) + v
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    for yil in YILLAR:
        src = json.loads((SRC / f"{yil}.json").read_text(encoding="utf-8"))
        taban = json.loads((TABAN / f"{yil}.json").read_text(encoding="utf-8"))["ilceler"]
        esleme = src["partiEslemesi"]
        rec = load_election(yil)
        eski_idx = {(r["plaka"], fold(r["ad"])): r for r in taban}
        kullanilan, rows, rapor, alanlar = set(), [], collections.Counter(), collections.Counter()
        il_kirilim, il_ham = {}, collections.defaultdict(list)
        for c in src["cevreler"]:
            plaka = c["plaka"]
            ham = f"{src['hamKlasor']}/{c['dosya']}"
            sk = sehir_koy(c.get("kirilim"), esleme, ham)
            if sk:
                il_kirilim[plaka] = _topla(il_kirilim.get(plaka), sk)
                il_ham[plaka].append(ham)
            for ilce in c["ilceler"]:
                key = (plaka, fold(ALIAS.get((plaka, fold(ilce["ad"])), ilce["ad"])))
                skr = sehir_koy(ilce.get("kirilim"), esleme, ham)
                if skr:
                    # TUIK dipnotu: ilce toplami ve sehir/koy toplamlari ayri tutanaklardan;
                    # farklar duzeltilmez, kaydedilir
                    fark = {f: (skr.get("sehir", {}).get(f) or 0) + (skr.get("koy", {}).get(f) or 0) - (ilce.get(f) or 0)
                            for f in ("secmen", "gecerliOy")}
                    if any(fark.values()):
                        skr["kaynak"]["ilceToplamindanFark"] = fark
                if plaka == 34 and key[1] == "EMINONU":
                    rows.append(birlestir(None, ilce, esleme, ham, plaka, "Eminönü", EMINONU))
                    if skr:
                        rows[-1]["sehirKoy"] = skr
                    rapor["sadece_tuik"] += 1
                    continue
                eski = eski_idx.get(key)
                if eski is None:
                    rows.append(birlestir(None, ilce, esleme, ham, plaka, ilce["ad"], None))
                    if skr:
                        rows[-1]["sehirKoy"] = skr
                    rapor["sadece_tuik_geomIdsiz"] += 1
                    continue
                kullanilan.add(key)
                gid = FATIH if (plaka == 34 and key[1] == "FATIH") else eski["geomId"]
                r = birlestir(eski, ilce, esleme, ham, plaka, eski["ad"], gid)
                if plaka == 34 and key[1] == "FATIH":
                    r["kaynak"]["not"] = "Tabanda Fatih+Eminönü tek satırdı; TÜİK Eminönü'yü ayrı veriyor (ayrı satır)."
                rapor["teyitli" if "teyit" in r["kaynak"] else "farkli"] += 1
                for f in r["kaynak"].get("farklar", []):
                    alanlar[f["alan"]] += 1
                if skr:
                    r["sehirKoy"] = skr
                    rapor["sehirKoy"] += 1
                rows.append(r)
        kalan = [dict(r, kaynak={"ana": "mertnuhoglu", "not": "TÜİK'te karşılığı yok"})
                 for k, r in eski_idx.items() if k not in kullanilan]
        rows += kalan
        sayac = collections.Counter(r["plaka"] for r in rows)
        for il in rec["iller"]:
            il["ilceSayisi"] = sayac.get(il["plaka"], 0)
            if il["plaka"] in il_kirilim:
                k = il_kirilim[il["plaka"]]
                k["kaynak"] = {"ana": "tuik", "tuikHam": il_ham[il["plaka"]],
                               "not": "Seçim çevrelerinin şehir/köy kırılımlarının toplamı. İl satırının "
                                      "kendi değerleri YSK'dendir; TÜİK il toplamı YSK ile birebir tutmayabilir."}
                il["sehirKoy"] = k
        print(f"{yil}: {dict(rapor)}, TUIK'te karsiligi yok: {len(kalan)}; farkli alanlar: {dict(alanlar.most_common(5))}")
        if args.write:
            rec["ilceler"] = rows
            save_election(yil, rec)
    if not args.write:
        print("\n(kuru calisma - yazmak icin --write)")


if __name__ == "__main__":
    main()
