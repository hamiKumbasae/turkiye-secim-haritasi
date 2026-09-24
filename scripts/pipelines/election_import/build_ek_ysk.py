"""
data/raw/ysk/acikveri-belde-agrege/<label>.json (fetch_belde_agrege.js ciktisi)
dosyalarindan, projede HIC OLMAYAN YSK kayitlarini ek dosyalara yazar:

  data/normalized/ek/belediye_meclisi/<secim>.json   belediye meclisi uyeligi oylari (2009-2024)
  data/normalized/ek/il_genel_meclisi/<secim>.json   il genel meclisi uyeligi oylari (2009-2024)
  data/normalized/ek/yenileme_ara/<label>.json       2019 Istanbul BB yenilemesi, 2024 yenileme,
                                                     2026 mahalli idareler ara secimi

Her birim = (il, ilce, belde): belde sandiklari ilce toplamina karismaz.
Parti adlari party_map_helper.build_auto_map ile partiler.json anahtarina
eslenir; eslenemeyen ad `oy` icinde kaynaktaki adiyla kalir ve dosyanin
`eslenemeyenPartiler` listesinde gorunur. Bagimsiz adaylarin oylari tek
"Bağımsız" anahtarinda (API'de aday adi yok, yalnizca bagimsizN sutunlari).

Koken: her dosyada `kaynak` = {ana: "ysk", api, secimId, secimTuru, hamDosya}.
Harita (build.py) bu dosyalari okumaz.

Kullanim:
  python3 scripts/pipelines/election_import/build_ek_ysk.py
"""
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from party_map_helper import build_auto_map, proper_case_tr  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "ysk" / "acikveri-belde-agrege"
EK = ROOT / "data" / "normalized" / "ek"
GEOM = json.loads((ROOT / "data/raw/ysk/acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))

HEDEF = {  # label -> (alt klasor, dosya adi, aciklama)
    "2019istanbul_yenileme": ("yenileme_ara", "2019istanbul_bb_yenileme",
                              "23 Haziran 2019 İstanbul Büyükşehir Belediye Başkanlığı yenileme seçimi (31 Mart 2019 sonucunun YSK tarafından iptali üzerine)"),
    "2024yenileme_baskan": ("yenileme_ara", "2024yenileme_belediye_baskanligi", "2 Haziran 2024 yenileme seçimi — belediye başkanlığı"),
    "2024yenileme_meclis": ("yenileme_ara", "2024yenileme_belediye_meclisi", "2 Haziran 2024 yenileme seçimi — belediye meclisi üyeliği"),
    "2026ara_baskan": ("yenileme_ara", "2026mahalli_ara_belediye_baskanligi", "7 Haziran 2026 mahalli idareler ara seçimi — belediye başkanlığı"),
    "2026ara_meclis": ("yenileme_ara", "2026mahalli_ara_belediye_meclisi", "7 Haziran 2026 mahalli idareler ara seçimi — belediye meclisi üyeliği"),
}
for y in ("2009", "2014", "2019", "2024"):
    HEDEF[f"{y}yerel_belediye_meclisi"] = ("belediye_meclisi", f"{y}yerel", f"{y} mahalli idareler genel seçimi — belediye meclisi üyeliği (oy)")
    HEDEF[f"{y}yerel_il_genel_meclisi"] = ("il_genel_meclisi", f"{y}yerel", f"{y} mahalli idareler genel seçimi — il genel meclisi üyeliği (oy)")

PARTI_COL = re.compile(r"^(parti|ittifak)\d+_ALDIGI_OY$")
BAG_COL = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def isle(label, alt, ad, aciklama):
    d = json.loads((RAW / f"{label}.json").read_text(encoding="utf-8"))
    col_ad = {r["column_NAME"]: r["ad"] for r in d["baslik"] if PARTI_COL.match(r["column_NAME"])}
    esleme, eslenemeyen = build_auto_map(set(col_ad.values()), [])
    birimler, iller = [], collections.defaultdict(lambda: collections.Counter())
    for b in sorted(d["birimler"].values(), key=lambda x: (x["ilId"], x["ilceAdi"], x["beldeId"])):
        t = b["toplam"]
        oy = collections.Counter()
        for c, v in t.items():
            if PARTI_COL.match(c) and c in col_ad:
                oy[esleme.get(col_ad[c], col_ad[c])] += v
            elif BAG_COL.match(c):
                oy["Bağımsız"] += v
        oy = {k: v for k, v in sorted(oy.items(), key=lambda kv: -kv[1]) if v}
        secmen, kullanan = t.get("secmen_SAYISI", 0), t.get("oy_KULLANAN_SECMEN_SAYISI", 0)
        r = {"il": proper_case_tr(b["ilAdi"]), "plaka": b["ilId"], "ilce": proper_case_tr(b["ilceAdi"]),
             "yskIlceId": b["ilceId"], "geomId": GEOM.get(f"{b['ilId']}-{b['ilceId']}"),
             "beldeId": b["beldeId"] or None, "belde": proper_case_tr(b["beldeAdi"]) if b.get("beldeAdi") else None,
             "sandik": b["sandik"], "secmen": secmen, "oyKullanan": kullanan,
             "gecerliOy": t.get("gecerli_OY_TOPLAMI", 0), "gecersizOy": t.get("gecersiz_OY_TOPLAMI", 0),
             "katilim": round(kullanan * 100 / secmen, 2) if secmen else None,
             "oy": oy, "kazanan": next(iter(oy), None)}
        birimler.append(r)
        il = iller[(b["ilId"], r["il"])]
        for f in ("sandik", "secmen", "oyKullanan", "gecerliOy", "gecersizOy"):
            il[f] += r[f]
        for k, v in oy.items():
            il["oy." + k] += v
    il_list = []
    for (pl, ad_il), c in sorted(iller.items()):
        oy = {k[3:]: v for k, v in sorted(c.items(), key=lambda kv: -kv[1]) if k.startswith("oy.")}
        il_list.append({"il": ad_il, "plaka": pl, **{f: c[f] for f in ("sandik", "secmen", "oyKullanan", "gecerliOy", "gecersizOy")},
                        "oy": oy, "kazanan": next(iter(oy), None)})
    veri = {
        "secim": ad, "tur": alt, "aciklama": aciklama,
        "kaynak": {"ana": "ysk", "api": "acikveri.ysk.gov.tr/api/getSecimSandikSonucList",
                   "secimId": d["secimId"], "secimTuru": d["secimTuru"], "cekildi": d["cekildi"],
                   "hamDosya": f"data/raw/ysk/acikveri-belde-agrege/{label}.json",
                   "not": "Sandık düzeyi veriden il/ilçe/belde bazında toplandı; YSK kesin sonuç ilanından birkaç yüz oy farklı olabilir."},
        "partiEslemesi": esleme, "eslenemeyenPartiler": sorted(eslenemeyen),
        "ozet": {"birim": len(birimler), "belde": sum(1 for r in birimler if r["beldeId"]), "il": len(il_list),
                 "geomIdsiz": sum(1 for r in birimler if not r["geomId"]), "cekimHatasi": len(d["hatalar"])},
        "iller": il_list, "birimler": birimler,
    }
    (EK / alt).mkdir(parents=True, exist_ok=True)
    (EK / alt / f"{ad}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{alt}/{ad}: {veri['ozet']} eslenemeyen={veri['eslenemeyenPartiler']}")


def main():
    for label, (alt, ad, aciklama) in HEDEF.items():
        if (RAW / f"{label}.json").exists():
            isle(label, alt, ad, aciklama)
        else:
            print("yok (henuz cekilmedi):", label)


if __name__ == "__main__":
    main()
