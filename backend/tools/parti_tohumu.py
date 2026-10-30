#!/usr/bin/env python3
"""Parti tohumunu (sabit parti_id) üretir ya da yeni seçenek adları için ek migration önerir.

parti_id'ler bir kez verilir ve DEĞİŞMEZ: V2__partiler.sql bir kez üretildi ve commit'lendi.
Veriye yeni bir parti/aday adı eklenirse (ör. 2028 seçimi) bu betik yalnız eksik adları,
mevcut en büyük kimlikten devam eden numaralarla yeni bir migration olarak yazar:

    python3 backend/tools/parti_tohumu.py --eksikler > backend/data-loader/src/main/resources/db/migration/V4__yeni_partiler.sql

data-loader, tohumda olmayan bir adla karşılaşırsa yüklemeyi durdurur ve bu komutu önerir.
"""
import argparse
import glob
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
NORM = ROOT / "data" / "normalized"
MIG = ROOT / "backend" / "data-loader" / "src" / "main" / "resources" / "db" / "migration"
DIGER = {"Diğer", "Bağımsız", "Bağımsızlar", "Diğerleri"}


def yil(k):
    return int(re.match(r"\d{4}", k).group())


def adlar():
    """ad -> (ilk görüldüğü yıl, görüldüğü seçim türleri)"""
    sonuc = {}
    for f in glob.glob(str(NORM / "elections" / "*" / "*.json")):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        k, tur = pathlib.Path(f).stem, d["tur"]
        gorulen = set()
        for duzey in ("iller", "ilceler"):
            for r in d[duzey]:
                gorulen.update(r["oy"])
                gorulen.update(r.get("vekil") or {})
                if r.get("kazanan"):
                    gorulen.add(r["kazanan"])
        gorulen.update((d.get("yurtdisi") or {}).get("oy") or {})
        for ad in gorulen:
            ilk, turler = sonuc.get(ad, (9999, set()))
            sonuc[ad] = (min(ilk, yil(k)), turler | {tur})
    return sonuc


def tip(ad, turler):
    if ad in DIGER:
        return "diger"
    if ad in ("Evet", "Hayır") and turler == {"referandum"}:
        return "referandum"
    if turler == {"cumhurbaskanligi"}:
        return "aday"
    return "parti"


def q(s):
    return "NULL" if s is None else "'" + s.replace("'", "''") + "'"


def satir(pid, ad, turler, partiler):
    p = partiler.get(ad, {})
    return f"({pid}, {q(ad)}, {q(p.get('short'))}, {q(tip(ad, turler))}, {q(p.get('light'))})"


def mevcut_tohum():
    ids = {}
    for f in sorted(MIG.glob("V*.sql")):
        for m in re.finditer(r"^\((\d+), '((?:[^']|'')*)'", f.read_text(encoding="utf-8"), re.M):
            ids[m.group(2).replace("''", "'")] = int(m.group(1))
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eksikler", action="store_true", help="yalnız tohumda olmayan adlar için migration yaz")
    a = ap.parse_args()
    partiler = json.loads((NORM / "partiler.json").read_text(encoding="utf-8"))
    hepsi = adlar()
    sira = sorted(hepsi, key=lambda ad: (hepsi[ad][0], ad))

    if a.eksikler:
        var = mevcut_tohum()
        eksik = [ad for ad in sira if ad not in var]
        if not eksik:
            print("-- tohumda eksik ad yok", file=sys.stderr)
            return
        bas = max(var.values()) + 1
        print("-- Yeni seçenek adları (backend/tools/parti_tohumu.py --eksikler)")
        print("INSERT INTO parti (parti_id, ad, kisa, tip, renk) VALUES")
        print(",\n".join(satir(bas + i, ad, hepsi[ad][1], partiler) for i, ad in enumerate(eksik)) + ";")
        return

    print("-- Parti ve öteki oy seçenekleri; SABİT kimlikler (Flyway V2).")
    print("-- Üretim: backend/tools/parti_tohumu.py (ilk görüldüğü yıl, sonra ad sırasıyla). Bu dosya bir kez")
    print("-- üretildi; yeni adlar için --eksikler ile YENİ bir migration yazılır, bu dosya değiştirilmez.")
    print("-- tip: parti | aday (yalnız cumhurbaşkanlığında) | referandum (Evet/Hayır) | diger (Diğer/Bağımsız)")
    print("-- kisa ve renk data/normalized/partiler.json'dan (açık tema rengi).")
    print("INSERT INTO parti (parti_id, ad, kisa, tip, renk) VALUES")
    print(",\n".join(satir(i + 1, ad, hepsi[ad][1], partiler) for i, ad in enumerate(sira)) + ";")


if __name__ == "__main__":
    main()
