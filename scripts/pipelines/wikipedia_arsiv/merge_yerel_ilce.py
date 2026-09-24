"""
data/kaynaklar/wikipedia/yerel/<secim>.json'daki ILCE belediye baskanligi
sonuclarini, ilce satiri HIC OLMAYAN yerel secimlerin
data/normalized/elections/yerel/<secim>.json kaydina yazar.

Sadece bosluk doldurur: normalize kayitta zaten ilce satiri varsa (1984+)
o secime dokunulmaz. Il satirlarina (il merkezi) dokunulmaz; sadece
`ilceSayisi` guncellenir.

geomId: genel_ilce_1961_1987 pipeline'indaki ile ayni kural - ayni ilce
adinin (plaka + fold(ad)) en yakin ilce-duzeyi verideki geomId'si
(1984yerel, 1989yerel, 1991, 1994yerel, 1995) ve ayni yildaki genel secimin
(TUIK, 1961-1987) eslemesi. Proje yeni sinir karari VERMEZ.

1950/1955 (sonucTipi=kazanan): oy sayisi yok, sadece kazanan parti. Satir
`oy` = {kazanan: {oy: null, oran: null}} ve `sadeceKazanan: true` ile yazilir.

Kullanim:
  python3 scripts/pipelines/wikipedia_arsiv/merge_yerel_ilce.py           # kuru calisma
  python3 scripts/pipelines/wikipedia_arsiv/merge_yerel_ilce.py --write
"""
import argparse
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE.parent / "genel_ilce_1961_1987"))
from common.election_io import load_election, save_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402
from merge_into_normalized import ALIAS, CROSS_PLAKA, OVERRIDE  # noqa: E402

ROOT = HERE.parent.parent.parent
SRC = ROOT / "data" / "kaynaklar" / "wikipedia" / "yerel"
SECIMLER = ["1950yerel", "1955yerel", "1963yerel", "1968yerel", "1973yerel", "1977yerel"]
# ayni donemdeki genel secim (TUIK ilce eslemesi) - yerel secime en yakin olan
YAKIN_GENEL = {"1950yerel": "1961", "1955yerel": "1961", "1963yerel": "1961", "1968yerel": "1969",
               "1973yerel": "1973", "1977yerel": "1977"}
REFS = ["1984yerel", "1989yerel", "1991", "1994yerel", "1995"]

# Wikipedia yazimi -> referans verideki yazim. Anahtar: (plaka, fold(wiki_adi))
WIKI_ALIAS = {
    (3, "SINCANLI"): "Sinanpaşa",
    (4, "KARAKÖSE"): "Merkez",
    (6, "KOCHISAR"): "Şereflikoçhisar",
    (16, "KEMALPASA"): "Mustafakemalpaşa",
    (17, "IMROZ"): "Gökçeada",
    (28, "KARAHISAR"): "Şebinkarahisar",
    (44, "ARAPKIR"): "Arapgir",
    (10, "AVYALIK"): "Ayvalık",  # kaynakta yazim hatasi
    (41, "IZMIT"): "Merkez",
    (33, "MERSIN"): "Merkez",
}
# Sonradan il olan yerlerin merkez ilcesi, o donemde eski ilinin altinda:
# (plaka_o_donem, fold) -> (yeni_plaka, referans_adi)
WIKI_CROSS = {
    (43, "USAK"): (64, "Merkez"),      # Usak ili 1953
    (44, "ADIYAMAN"): (2, "Merkez"),   # Adiyaman ili 1954
    (51, "NEVSEHIR"): (50, "Merkez"),  # Nevsehir ili 1954
}


def ref_index():
    idx = collections.defaultdict(dict)
    by_name = collections.defaultdict(set)  # fold(ad) -> {plaka} (ulke geneli tekillik kontrolu)
    for ref in REFS + sorted(set(YAKIN_GENEL.values())):
        for r in load_election(ref)["ilceler"]:
            if r.get("geomId"):
                idx[(r["plaka"], fold(r["ad"]))][ref] = r["geomId"]
                if fold(r["ad"]) != "MERKEZ":
                    by_name[fold(r["ad"])].add(r["plaka"])
    return idx, by_name


def _adaylar(plaka, ad, il):
    """Denenecek yazimlar: 'Güneyce (İkizdere)' -> ['Güneyce (İkizdere)', 'Güneyce', 'İkizdere'];
    '<İl> Merkez' -> 'Merkez'."""
    out = [ad]
    m = re.fullmatch(r"(.+?)\s*\((.+)\)", ad)
    if m:
        out += [m.group(1), m.group(2)]
    if fold(ad).endswith(" MERKEZ") or (il and fold(ad) == fold(il) + " MERKEZ"):
        out.append("Merkez")
    return out


def resolve(ctx, secim, plaka, ad, il=None):
    idx, by_name = ctx
    order = [YAKIN_GENEL[secim]] + REFS
    for cand in _adaylar(plaka, ad, il):
        key = (plaka, fold(cand))
        key = (plaka, fold(WIKI_ALIAS.get(key) or ALIAS.get(key) or cand))
        if key in CROSS_PLAKA or key in WIKI_CROSS:
            rp, rad = (CROSS_PLAKA.get(key) or WIKI_CROSS[key])
            key = (rp, fold(rad))
        if key in OVERRIDE:
            return OVERRIDE[key], "override"
        hits = idx.get(key, {})
        for ref in order:
            if ref in hits:
                return hits[ref], ref
    # O donemde baska ile bagli olup referans secimlerde yeni ilinde gecen
    # ilceler (orn. 1950'de Kocaeli'ye bagli Adapazari): ad ulke genelinde
    # TEKSE o ilcenin geomId'si kullanilir.
    for cand in _adaylar(plaka, ad, il):
        f = fold(WIKI_ALIAS.get((plaka, fold(cand))) or cand)
        pl = by_name.get(f, set())
        if len(pl) == 1:
            hits = idx[(next(iter(pl)), f)]
            for ref in order:
                if ref in hits:
                    return hits[ref], "baska_il:" + ref
    return None, "eslesmedi"


def satir(b, gid):
    base = {"ad": b["ad"], "plaka": b["plaka"], "geomId": gid, "kazanan": b["kazanan"],
            "toplamVekil": 0, "vekil": {}, "katilim": None,
            "kaynak_url": "https://tr.wikipedia.org/w/index.php?oldid=%d" % b["revid"],
            "kaynak": {"ana": "wikipedia", "sayfa": b["sayfa"], "revid": b["revid"],
                       "kaynakKatmani": f"data/kaynaklar/wikipedia/yerel/{b['_secim']}.json"}}
    if b["sonucTipi"] == "kazanan":
        base.update(secmen=None, sandik=None, gecerliOy=None, sadeceKazanan=True,
                    oy={b["kazanan"]: {"oy": None, "oran": None}} if b["kazanan"] else {})
        return base
    # Bagimsizlar tek anahtarda toplanir (projenin mevcut yerel semasi);
    # kazanan ise tek tek adaylar arasindan (kaynak sayfalarin kuraliyla) belirlendi.
    oy = {}
    for a in b["adaylar"]:
        k = a["parti"] or "Diğer"
        e = oy.setdefault(k, {"aday": [], "oy": 0})
        e["oy"] += a["oy"]
        if a["aday"]:
            e["aday"].append(a["aday"])
    toplam = sum(v["oy"] for v in oy.values())
    base.update(secmen=b["secmen"], sandik=b["sandik"] or 0, gecerliOy=toplam,
                oy={k: {"aday": "; ".join(v["aday"]) or None, "oy": v["oy"],
                        "oran": round(v["oy"] * 100 / toplam, 2) if toplam else 0.0}
                    for k, v in sorted(oy.items(), key=lambda kv: -kv[1]["oy"])})
    if b["gecerliOy"] and b["gecerliOy"] != toplam:
        base["not"] = f"Kaynak sayfanın 'Toplam' satırı {b['gecerliOy']}, aday oylarının toplamı {toplam} (oranlar aday toplamından)."
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    idx = ref_index()
    eslesmeyen = collections.defaultdict(list)
    for secim in SECIMLER:
        src = json.loads((SRC / f"{secim}.json").read_text(encoding="utf-8"))
        rec = load_election(secim)
        if rec["ilceler"] and not all(r.get("kaynak", {}).get("ana") == "wikipedia" or "kaynak_url" in r
                                      for r in rec["ilceler"]):
            print(secim, "baska kaynaktan ilce verisi var, atlandi")
            continue
        il_plakalar = {r["plaka"] for r in rec["iller"]}
        rows, via = [], collections.Counter()
        for b in src["kayitlar"]:
            if b["tur"] != "ilce" or b["plaka"] is None:
                continue
            if b["plaka"] not in il_plakalar:
                eslesmeyen[(secim, b["il"], "IL YOK")].append(b["ad"])
                continue
            b["_secim"] = secim
            gid, how = resolve(idx, secim, b["plaka"], b["ad"], b["il"])
            via[how.split(":")[0]] += 1
            if gid is None:
                eslesmeyen[(secim, b["il"], b["plaka"])].append(b["ad"])
            rows.append(satir(b, gid))
        # ayni geomId'ye iki satir baglanmasin (cakisma): kaynak ayni ilceyi iki
        # ilin sayfasinda farkli sonucla veriyorsa hangisinin dogru oldugunu
        # bilmiyoruz - ikisi de tabloda kalir, haritadan cikarilir.
        by_gid = collections.defaultdict(list)
        for r in rows:
            if r["geomId"]:
                by_gid[r["geomId"]].append(r)
        for gid, rs in by_gid.items():
            if len(rs) > 1:
                eslesmeyen[(secim, "CAKISMA", gid)].append(" / ".join(f"{r['ad']} ({r['plaka']})" for r in rs))
                for r in rs:
                    r["geomId"] = None
                    r["not"] = ("Kaynak (Wikipedia) bu ilçeyi bu seçim için birden fazla ilin sayfasında "
                                "farklı sonuçlarla veriyor; hangisinin doğru olduğu doğrulanamadığı için haritada çizilmez.")
        sayac = collections.Counter(r["plaka"] for r in rows)
        for il in rec["iller"]:
            il["ilceSayisi"] = sayac.get(il["plaka"], 0)
        print(f"{secim}: {len(rows)} ilce, geomId'li {sum(1 for r in rows if r['geomId'])}, eslesme {dict(via)}")
        if args.write:
            rec["ilceler"] = rows
            save_election(secim, rec)
    print("\n-- geomId bulunamayan / cakisan:")
    for k, v in sorted(eslesmeyen.items(), key=str):
        print("  ", *k, ":", ", ".join(v))
    if not args.write:
        print("\n(kuru calisma - yazmak icin --write)")


if __name__ == "__main__":
    main()
