"""
Veri kokeni sorgusu: bir secimin (ve istenirse bir ilin / ilcenin) verisinin
HANGI KAYNAKTAN geldigini, hangi degerlerin baska bir kaynakla teyit edildigini
ya da farkli oldugunu ve ham dosyanin nerede durdugunu yazar.

Bilgiyi uc yerden birlestirir:
  1. sources.yml                     secim duzeyinde il/ilce kaynaklari
  2. data/normalized/.../<secim>.json satir duzeyinde `kaynak` alani (varsa)
  3. data/kaynaklar/<kaynak>/...      o secim icin her kaynagin ayri katmani

Kullanim:
  python3 scripts/kaynak.py 1995                 # secim ozeti
  python3 scripts/kaynak.py 1995 İstanbul        # il satiri + ilce kokenleri ozeti
  python3 scripts/kaynak.py 1995 İstanbul Fatih  # tek ilce, alan alan
  python3 scripts/kaynak.py 1968yerel 1 Ceyhan   # il plaka ile de verilebilir
  python3 scripts/kaynak.py 1961senato           # ek kayitlar (senato/milletvekilleri/beldeler)
  python3 scripts/kaynak.py --liste              # tum secimler, duzey bazinda kaynak tablosu
"""
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common.election_io import election_path  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
KAYNAKLAR = ROOT / "data" / "kaynaklar"
EK = ROOT / "data" / "normalized" / "ek"

try:
    import yaml
except ImportError:  # .venv/bin/python ile calistirin (pyyaml)
    yaml = None


def sources_yml():
    if yaml is None:
        sys.exit("pyyaml gerekli: .venv/bin/python scripts/kaynak.py ...")
    return yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))


def _kaynak_str(k):
    if not k:
        return "-"
    ad = k.get("authority") or k.get("source")
    ek = [x for x in (k.get("status"), k.get("url") or k.get("raw") or k.get("frozen")) if x]
    return f"{ad} ({'; '.join(ek)})" if ek else str(ad)


def secim_kaynaklari(key, doc):
    e = doc.get("elections", {}).get(key)
    if not e:
        return None
    out = {"il": e.get("primary")}
    if e.get("ilce_base"):
        out["ilce"] = e["ilce_base"]
        out["ilce_tamamlayan"] = e.get("ilce_source")
    elif e.get("ilce_source"):
        out["ilce"] = e["ilce_source"]
    elif "ilce" in (e.get("primary") or {}).get("level", []):
        out["ilce"] = e["primary"]
    else:
        for b in e.get("backup") or []:
            if "ilce" in b.get("level", []):
                out["ilce"] = b
    out["eski_kaynak"] = e.get("legacy_source")
    out["kapsam"] = e.get("coverage") or []
    out["known_issues"] = e.get("known_issues") or []
    return out


def katmanlar(key):
    return sorted(str(p.relative_to(ROOT)) for p in KAYNAKLAR.glob(f"*/*/{key}.json"))


def il_bul(rec, il):
    if il.isdigit():
        return [r for r in rec["iller"] if r["plaka"] == int(il)]
    return [r for r in rec["iller"] if fold(r["ad"]) == fold(il)]


def satir_koken(r):
    k = r.get("kaynak")
    if not k:
        return None
    s = f"ana kaynak: {k.get('ana')}"
    if k.get("teyit"):
        s += f" | teyit: {', '.join(k['teyit'])} (tum degerler birebir ayni)"
    if k.get("farklar"):
        s += f" | {len(k['farklar'])} alan {k['farklar'][0]['kaynak']}'ten farkli/eksikti"
    return s


def goster_secim(key, il=None, ilce=None):
    doc = sources_yml()
    p = election_path(key)
    if not p.exists():
        ek = list(EK.glob(f"*/{key}.json"))
        if not ek:
            sys.exit(f"{key}: ne normalized'da ne ek kayitlarda var")
        for f in ek:
            d = json.loads(f.read_text(encoding="utf-8"))
            print(f"{key} — EK KAYIT ({f.parent.name}), haritaya bagli degil")
            print(f"  dosya: {f.relative_to(ROOT)}")
            print(f"  kaynak: {d['kaynak']} — {doc.get('ek_kayitlar', {}).get(f.parent.name, {}).get('source')}")
            print(f"  kapsam: {json.dumps(d.get('kapsam'), ensure_ascii=False)}")
        for k in katmanlar(key):
            print(f"  kaynak katmani: {k}")
        return
    rec = json.loads(p.read_text(encoding="utf-8"))
    sk = secim_kaynaklari(key, doc) or {}
    print(f"{key} — {rec.get('ad')} ({rec.get('tur')})  [{p.relative_to(ROOT)}]")
    print(f"  il duzeyi   : {_kaynak_str(sk.get('il'))}")
    print(f"  ilce duzeyi : {_kaynak_str(sk.get('ilce')) if rec['ilceler'] else 'ilce verisi yok'}")
    if sk.get("ilce_tamamlayan"):
        print(f"  ilce fark/teyit: {_kaynak_str(sk['ilce_tamamlayan'])}")
    if sk.get("eski_kaynak"):
        print(f"  onceki kaynak (artik kullanilmiyor): {_kaynak_str(sk['eski_kaynak'])}")
    ana = collections.Counter((r.get("kaynak") or {}).get("ana", "-") for r in rec["ilceler"])
    tey = sum(1 for r in rec["ilceler"] if (r.get("kaynak") or {}).get("teyit"))
    fark = sum(1 for r in rec["ilceler"] if (r.get("kaynak") or {}).get("farklar"))
    if rec["ilceler"] and set(ana) != {"-"}:
        print(f"  ilce satir kokenleri: {dict(ana)}; teyitli {tey}, farkli {fark}")
    for c in sk.get("kapsam", []):
        print(f"  kapsam notu : {c}")
    for ki in sk.get("known_issues", []):
        print(f"  bilinen durum [{ki.get('status')}] {ki.get('scope')}: {' '.join(str(ki.get('description', '')).split())[:220]}")
    for k in katmanlar(key):
        print(f"  kaynak katmani: {k}")
    if not il:
        return
    iller = il_bul(rec, il)
    if not iller:
        sys.exit(f"  il bulunamadi: {il}")
    ir = iller[0]
    print(f"\n  IL {ir['ad']} (plaka {ir['plaka']}): kazanan {ir.get('kazanan')}, gecerli {ir.get('gecerliOy')}"
          f" — kaynak: {ir.get('kaynak_url') or _kaynak_str(sk.get('il'))}")
    if ir.get("sehirKoy"):
        print(f"  IL sehir/koy kirilimi: kaynak {ir['sehirKoy']['kaynak']['ana']} ({len(ir['sehirKoy']['kaynak']['tuikHam'])} secim cevresi)")
    ilceler = [r for r in rec["ilceler"] if r["plaka"] == ir["plaka"]]
    if ilce:
        ilceler = [r for r in ilceler if fold(r["ad"]) == fold(ilce)]
        if not ilceler:
            sys.exit(f"  ilce bulunamadi: {ilce}")
    for r in ilceler:
        k = r.get("kaynak")
        print(f"  - {r['ad']} ({r.get('geomId')}): kazanan {r.get('kazanan')}, gecerli {r.get('gecerliOy')}"
              f" — {satir_koken(r) or r.get('kaynak_url') or _kaynak_str(sk.get('ilce'))}")
        if ilce and k:
            for f in k.get("farklar", []):
                print(f"      {f['alan']}: {f['eski']} -> {f['yeni']}  (kaynak: {f['kaynak']})")
            for a in ("tuikHam", "sayfa", "revid", "kaynakKatmani", "not"):
                if k.get(a):
                    print(f"      {a}: {k[a]}")
            if k.get("revid"):
                print(f"      wikipedia: https://tr.wikipedia.org/w/index.php?oldid={k['revid']}")
        if ilce and r.get("baskan"):
            print(f"      baskan: {r['baskan']} (ayni kaynak)")
        if ilce and r.get("sehirKoy"):
            sk = r["sehirKoy"]
            print(f"      sehir/koy kirilimi: kaynak {sk['kaynak']['ana']} ({sk['kaynak'].get('tuikHam')})"
                  f"; sehir secmen {sk.get('sehir', {}).get('secmen')}, koy secmen {sk.get('koy', {}).get('secmen')}"
                  + (f"; ilce toplamindan fark {sk['kaynak']['ilceToplamindanFark']}" if sk['kaynak'].get('ilceToplamindanFark') else ""))


def liste():
    doc = sources_yml()
    for key, e in doc.get("elections", {}).items():
        sk = secim_kaynaklari(key, doc)
        p = election_path(key)
        ilce = json.loads(p.read_text(encoding="utf-8"))["ilceler"] if p.exists() else []
        il_k = (sk["il"] or {}).get("authority") or (sk["il"] or {}).get("source")
        ilce_k = ((sk.get("ilce") or {}).get("authority") or (sk.get("ilce") or {}).get("source")) if ilce else "-"
        tam = sk.get("ilce_tamamlayan")
        print(f"{key:16} il: {str(il_k)[:38]:38} ilce: {str(ilce_k)[:40]}{' + ' + tam['authority'] + ' (fark/teyit)' if tam else ''}")
    for alt, v in (doc.get("ek_kayitlar") or {}).items():
        print(f"{'ek/' + alt:16} {v['source']['authority']}  ->  {v['files']}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "--liste":
        liste()
    else:
        goster_secim(a[0], *(a[1:3]))


if __name__ == "__main__":
    main()
