#!/usr/bin/env python3
"""data/normalized/ altindaki secim verisini iliskisel bir SQLite veritabanina yukler.

Kullanim:
    python3 scripts/veritabani/build_db.py                 # il + ilce (+ mahalle) -> build/secimler.sqlite
    python3 scripts/veritabani/build_db.py --mahalle-yok   # mahalle tablolari bos kalir (kucuk dosya)
    python3 scripts/veritabani/build_db.py -o yol.sqlite

Sema: scripts/veritabani/schema.sql, aciklama: docs/VERITABANI.md.
Kaynak dosyalar degistirilmez; veritabani her calistirmada sifirdan uretilir.
"""
import argparse
import json
import pathlib
import re
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_all_elections  # noqa: E402

DATA = ROOT / "data" / "normalized"
GEO = ROOT / "geo" / "normalized"

REFERANDUM_SECENEKLERI = {"Evet", "Hayır"}
DIGER = {"Diğer", "Bağımsız", "Bağımsızlar", "Diğerleri"}


def yil_of(secim_id: str) -> int:
    return int(re.match(r"\d{4}", secim_id).group())


def j(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True) if o else None


class Secenekler:
    """secenek tablosu: ad -> secenek_id, ilk gorulen tipiyle."""

    def __init__(self, con, partiler):
        self.con, self.partiler, self.ids = con, partiler, {}

    def tip(self, ad, tur):
        if ad in DIGER:
            return "diger"
        if tur == "referandum" and ad in REFERANDUM_SECENEKLERI:
            return "referandum"
        if tur == "cumhurbaskanligi" and ad not in self.partiler:
            return "aday"
        return "parti"

    def id(self, ad, tur):
        if ad is None:
            return None
        if ad not in self.ids:
            p = self.partiler.get(ad, {})
            cur = self.con.execute(
                "INSERT INTO secenek(ad, kisa, tip, renk_acik, renk_koyu) VALUES (?,?,?,?,?)",
                (ad, p.get("short"), self.tip(ad, tur), p.get("light"), p.get("dark")),
            )
            self.ids[ad] = cur.lastrowid
        return self.ids[ad]


def kaynak_notu(r):
    parcalar = [r.get(k) for k in ("not", "veriNotu", "etiketNotu", "ilceGeneliSonuc") if r.get(k)]
    return " | ".join(parcalar) or None


def kaynak_json(r):
    k = {key: r[key] for key in ("kaynak", "kaynak_url", "duzeltmeKaynagi", "oyKapsami",
                                 "ilceFarki", "sehirKoy") if r.get(key) is not None}
    return j(k)


def build(out: pathlib.Path, mahalle: bool):
    t0 = time.time()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    con.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    con.execute("PRAGMA foreign_keys = OFF")  # yukleme sirasinda kapali, sonda toplu kontrol

    partiler = json.loads((DATA / "partiler.json").read_text(encoding="utf-8"))
    sec = Secenekler(con, partiler)

    secimler = load_all_elections()
    sira = sorted(secimler, key=lambda k: (yil_of(k), k))
    mahalle_dosyalari = {p.stem for p in (DATA / "mahalle").glob("*.json")}

    il_ad, ilce_bilgi = {0: "Yurt Dışı"}, {}   # son gorulen ad/plaka (kronolojik)

    for sid in sira:
        d = secimler[sid]
        tur = d["tur"]
        con.execute(
            "INSERT INTO secim VALUES (?,?,?,?,?,?,?,?)",
            (sid, tur, yil_of(sid), d["ad"], d.get("contestType"), d.get("resultBasis"),
             d.get("toplamSandalye") or None, int(sid in mahalle_dosyalari)),
        )

        for r in d["iller"]:
            plaka = r["plaka"]
            il_ad[plaka] = r["ad"]
            con.execute(
                "INSERT INTO sonuc_il VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, plaka, r["ad"], r.get("secmen"), r.get("oyKullanan"), r.get("gecerliOy"),
                 r.get("gecersizOy"), r.get("sandik"), r.get("katilim"), sec.id(r.get("kazanan"), tur),
                 r.get("toplamVekil") or None, r.get("ilceSayisi"), kaynak_notu(r), kaynak_json(r)),
            )
            con.executemany(
                "INSERT INTO oy_il VALUES (?,?,?,?,?)",
                [(sid, plaka, sec.id(p, tur), v.get("oy"), v.get("oran")) for p, v in r["oy"].items()],
            )
            con.executemany(
                "INSERT INTO sandalye_il VALUES (?,?,?,?)",
                [(sid, plaka, sec.id(p, tur), n) for p, n in (r.get("vekil") or {}).items() if n],
            )

        yd = d.get("yurtdisi")
        if yd:
            oylar = yd.get("oy", {})
            kazanan = max(oylar, key=lambda p: oylar[p].get("oy") or 0) if oylar else None
            con.execute(
                "INSERT INTO sonuc_il(secim_id, plaka, ad, oy_kullanan, gecerli_oy, katilim, kazanan_id, not_metni)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (sid, 0, "Yurt Dışı", yd.get("kullanilanOy"), yd.get("gecerliOy"), yd.get("katilim"),
                 sec.id(kazanan, tur), "Yurt dışı ve gümrük oyları"),
            )
            con.executemany(
                "INSERT INTO oy_il VALUES (?,?,?,?,?)",
                [(sid, 0, sec.id(p, tur), v.get("oy"), v.get("oran")) for p, v in oylar.items()],
            )

        for r in d["ilceler"]:
            iid = r.get("geomId") or f"YOK-{r['plaka']:02d}-{r['ad']}"
            ilce_bilgi[iid] = (r["plaka"], r["ad"])
            con.execute(
                "INSERT INTO sonuc_ilce VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, iid, r["plaka"], r["ad"], r.get("secmen"), r.get("oyKullanan"), r.get("gecerliOy"),
                 r.get("gecersizOy"), r.get("sandik"), r.get("katilim"), sec.id(r.get("kazanan"), tur),
                 r.get("baskan"), int(bool(r.get("sadeceKazanan"))), int(bool(r.get("buyuksehirSonucu"))),
                 kaynak_notu(r), kaynak_json(r)),
            )
            con.executemany(
                "INSERT INTO oy_ilce VALUES (?,?,?,?,?,?,?)",
                [(sid, iid, sec.id(p, tur), v.get("oy"), v.get("oran"), v.get("aday"), v.get("sandalye"))
                 for p, v in r["oy"].items()],
            )

    con.executemany("INSERT INTO il VALUES (?,?)", sorted(il_ad.items()))

    n_mah = 0
    if mahalle:
        geo = json.loads((GEO / "mahalle_geo.json").read_text(encoding="utf-8"))
        mahalle_ad = {}
        for sid in sira:
            if sid not in mahalle_dosyalari:
                continue
            tur = secimler[sid]["tur"]
            md = json.loads((DATA / "mahalle" / f"{sid}.json").read_text(encoding="utf-8"))
            sonuc, oylar = [], []
            for iid, mahalleler in md.items():
                for mid, r in mahalleler.items():
                    mahalle_ad.setdefault((iid, mid), (geo.get(iid, {}).get(mid) or {}).get("ad"))
                    sonuc.append((sid, iid, mid, r.get("secmen"), r.get("oyKullanan"), r.get("gecerliOy"),
                                  r.get("sandik"), r.get("katilim"), sec.id(r.get("kazanan"), tur)))
                    oylar.extend((sid, iid, mid, sec.id(p, tur), v.get("oy"), v.get("oran"))
                                 for p, v in r["oy"].items())
                    if iid not in ilce_bilgi:   # yalniz mahalle verisinde gecen ilce birimi
                        ilce_bilgi[iid] = (int(iid.split("-")[2]) if iid.startswith("TR-D-") else None, iid)
            con.executemany("INSERT INTO sonuc_mahalle VALUES (?,?,?,?,?,?,?,?,?)", sonuc)
            con.executemany("INSERT INTO oy_mahalle VALUES (?,?,?,?,?,?)", oylar)
            n_mah += len(sonuc)
            print(f"  mahalle {sid}: {len(sonuc):,} satır, {len(oylar):,} oy", flush=True)
        con.executemany("INSERT INTO mahalle VALUES (?,?,?)",
                        [(mid, iid, ad) for (iid, mid), ad in mahalle_ad.items()])

    # Cumhurbaskanligi adaylari partiler.json'da renk icin yer aliyor; yalniz CB seciminde
    # gecen secenekler aday sayilir.
    con.execute("""
        UPDATE secenek SET tip = 'aday'
        WHERE tip = 'parti' AND secenek_id IN (SELECT secenek_id FROM oy_il JOIN secim USING (secim_id)
                                               WHERE tur = 'cumhurbaskanligi')
          AND secenek_id NOT IN (SELECT secenek_id FROM oy_il JOIN secim USING (secim_id)
                                 WHERE tur <> 'cumhurbaskanligi')""")

    con.executemany(
        "INSERT INTO ilce VALUES (?,?,?,?)",
        [(iid, plaka, ad, int(iid.startswith("TR-D-"))) for iid, (plaka, ad) in sorted(ilce_bilgi.items())],
    )
    con.commit()

    hatalar = con.execute("PRAGMA foreign_key_check").fetchall()
    if hatalar:
        print(f"YABANCI ANAHTAR HATASI: {len(hatalar)} satır, ilk 10: {hatalar[:10]}", file=sys.stderr)
        sys.exit(1)
    con.execute("ANALYZE")
    con.commit()
    con.close()
    con = sqlite3.connect(tmp)
    con.execute("VACUUM")
    con.close()
    tmp.replace(out)

    print(f"{out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: "
          f"{len(sira)} seçim, {n_mah:,} mahalle sonucu, "
          f"{out.stat().st_size / 1e6:.0f} MB, {time.time() - t0:.0f} sn")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=pathlib.Path, default=ROOT / "build" / "secimler.sqlite")
    ap.add_argument("--mahalle-yok", action="store_true", help="mahalle tablolarini doldurma")
    a = ap.parse_args()
    build(a.out.resolve(), mahalle=not a.mahalle_yok)


if __name__ == "__main__":
    main()
