"""
1963-1977 belediye baskanligi: depodaki kayit (Vikipedi il sayfalari; o sayfalar bu kitaplari kaynak gosteriyor)
DIE kitabinin baskanlik tablosuyla (extract_mahalli_1963_1977.py -> data/kaynaklar/tuik/yerel/<secim>/
belediye_baskanligi.json) karsilastirilir; kitapta dogrulanmis satirin sayilari kayda islenir.

Isleme merge_mahalli.satiri_isle ile (1984-2004 ile ayni kural): kitap satiri ic kontrolden gectiyse (parti
toplami == gecerli oy; 1973/1977'de yuzdeler de) parti oylari ve gecerli oy kitaptan yazilir, Vikipedi'deki aday
adlari korunur; sandik / secmen / katilim yalniz kitabin katilim yuzdesi tutuyorsa. Her degisiklik
kaynak.farklar'da (eski -> yeni), degismeyen satir kaynak.teyit = ["tuik"]. Kitapta toplam tutmayan satir
(1963/1968: tutanaktaki fark) islenmez, kaynak.tuikKullanilmadi'da nedeni yazilir.

Kimlik (tahmin yok; kitap satirinda ad cogu yerde metin katmaninda yok):
  1. ayni ilde secmen (ve okunduysa sandik) birebir ayni TEK kitap satiri;
  2. kitapta okunan ad (merge_mahalli.eslestir: ad / benzerlik / kitap sirasi + sayisal destek);
  3. en az 3 partinin oyu (>= 10) birebir ayni TEK satir.
Il satiri (il merkezi belediyesi) ayni kurallarla; il merkezinin ilce satiri ("Merkez", kaynak 'il satiri') il
satirindan birebir kopyalanir.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/merge_baskanlik_1963_1977.py [secim ...] [--yaz]
"""
import argparse
import collections
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
from common.election_io import load_election, save_election  # noqa: E402
import extract_mahalli_1963_1977 as X  # noqa: E402
import merge_mahalli as M  # noqa: E402

for _s, _c in X.KITAPLAR.items():
    M.KITAPLAR.setdefault(_s, _c)

SECIMLER = ["1963yerel", "1968yerel", "1973yerel", "1977yerel"]


def _po(p):
    return {k: (v.get("oy") if isinstance(v, dict) else v) for k, v in (p.get("oy") or {}).items()}


def kimlik_bul(p, adaylar, kullanilan):
    """p (proje satiri) icin kitap satiri ve yontem; yoksa (None, None)."""
    bos = [d for d in adaylar if id(d) not in kullanilan]
    s = p.get("secmen")
    if s:
        uyan = [d for d in bos if d.get("secmen") == s and (not p.get("sandik") or not d.get("sandik")
                                                            or p["sandik"] == d["sandik"])]
        if len(uyan) == 1:
            return uyan[0], "secmen"
    po = _po(p)
    uyan = [d for d in bos if sum(1 for k, o in d["oy"].items() if o >= 10 and po.get(k) == o) >= 3]
    if len(uyan) == 1:
        return uyan[0], "oy"
    return None, None


def isle(secim, rapor):
    rec = load_election(secim)
    bel = M.kaynak_katmani(secim, "belediye_baskanligi")["satirlar"]
    sayac = collections.Counter()
    die = collections.defaultdict(list)
    for d in bel:
        # il toplami ve Turkiye toplami disindaki satirlar (ilce merkezi, il merkezi ve beldeler) aday
        if d["tip"] in ("ilce", "belde") and d["plaka"]:
            die[d["plaka"]].append(d)
    kullanilan = set()
    yontemler = collections.Counter()

    def bagla(p, d, yontem):
        kullanilan.add(id(d))
        yontemler[yontem] += 1
        M.satiri_isle(p, d, secim, "belediye_baskanligi", sayac)
        p["kaynak"]["tuik"]["kimlik"] = {"secmen": "seçmen (ve sandık) kitapla birebir",
                                         "ad": "kitapta okunan ad", "oy": "≥3 partinin oyu kitapla birebir"}[yontem]

    # 1-3: secmen ve oy esitligi (il satirlari once: il merkezi belediyesi en buyuk satir)
    il_kalan, ilce_kalan = [], []
    for r in rec["iller"]:
        d, y = kimlik_bul(r, die.get(r["plaka"], []), kullanilan)
        if d:
            bagla(r, d, y)
        else:
            il_kalan.append(r)
    ilceler = [r for r in rec["ilceler"] if (r.get("kaynak") or {}).get("ana") != "il satırı"]
    for r in ilceler:
        d, y = kimlik_bul(r, die.get(r["plaka"], []), kullanilan)
        if d:
            bagla(r, d, y)
        else:
            ilce_kalan.append(r)
    # 2: adla (yalniz adi okunan kitap satirlari; zayif eslesme sayisal destekle)
    for pl in sorted({r["plaka"] for r in ilce_kalan}):
        proje = [r for r in ilce_kalan if r["plaka"] == pl]
        adli = [d for d in die.get(pl, []) if id(d) not in kullanilan and len(M._anahtar(M.dad(d))) >= 3]
        for p, d in M.eslestir(proje, adli, sira_esik=0):
            bagla(p, d, "ad")
            ilce_kalan.remove(p)
    # il merkezinin ilce satiri: il satirindan kopya
    il = {r["plaka"]: r for r in rec["iller"]}
    for r in rec["ilceler"]:
        if (r.get("kaynak") or {}).get("ana") == "il satırı" and r["plaka"] in il and "tuik" in (il[r["plaka"]].get("kaynak") or {}):
            src = il[r["plaka"]]
            for alan in ("sandik", "secmen", "katilim", "gecerliOy", "oy", "kazanan"):
                if alan in src:
                    r[alan] = copy.deepcopy(src[alan])
            r["kaynak"] = dict(r["kaynak"], tuik=copy.deepcopy(src["kaynak"]["tuik"]))
            for k in ("teyit", "farklar", "tuikKullanilmadi"):
                if k in src["kaynak"]:
                    r["kaynak"][k] = copy.deepcopy(src["kaynak"][k])
    farkli = [r for r in rec["iller"] + ilceler if (r.get("kaynak") or {}).get("farklar")]
    kazanan_degisen = [f"{r['plaka']}:{r['ad']}" for r in farkli
                       if any(f["alan"] == "kazanan" for f in r["kaynak"]["farklar"])]
    rapor[secim] = {
        "kitapSatiri": sum(len(v) for v in die.values()),
        "baglanan": dict(yontemler),
        "teyit": sum(1 for r in rec["iller"] + ilceler if (r.get("kaynak") or {}).get("teyit")),
        "farkli": len(farkli),
        "tuikKullanilmadi": sum(1 for r in rec["iller"] + ilceler if (r.get("kaynak") or {}).get("tuikKullanilmadi")),
        "baglanamayanIl": [r["ad"] for r in il_kalan],
        "baglanamayanIlce": [f"{r['plaka']}:{r['ad']}" for r in ilce_kalan],
        "kazananDegisen": kazanan_degisen,
    }
    return rec


def kazanan_farki(eski, yeni):
    """{plaka:ad: (eski kazanan, yeni kazanan)}"""
    e = {(r["plaka"], r["ad"]): r.get("kazanan") for r in eski["iller"] + eski["ilceler"]}
    return {f"{r['plaka']}:{r['ad']}": (e.get((r["plaka"], r["ad"])), r.get("kazanan"))
            for r in yeni["iller"] + yeni["ilceler"] if e.get((r["plaka"], r["ad"])) != r.get("kazanan")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("secimler", nargs="*")
    ap.add_argument("--yaz", action="store_true")
    a = ap.parse_args()
    rapor = {}
    for secim in a.secimler or SECIMLER:
        eski = load_election(secim)
        rec = isle(secim, rapor)
        r = rapor[secim]
        r["kazananDegisen"] = kazanan_farki(eski, rec)
        print(secim, {k: (v if not isinstance(v, (list, dict)) or k == "baglanan" else len(v)) for k, v in r.items()})
        print("  kazanan değişen:", r["kazananDegisen"])
        print("  bağlanamayan ilçe:", r["baglanamayanIlce"][:30])
        if a.yaz:
            save_election(secim, rec)
            yol = M.SRC / secim / "baskanlik_birlestirme.json"
            yol.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
