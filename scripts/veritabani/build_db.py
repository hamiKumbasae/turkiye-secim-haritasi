#!/usr/bin/env python3
"""data/normalized/ altindaki secim verisini iliskisel bir SQLite veritabanina yukler.

Kullanim:
    python3 scripts/veritabani/build_db.py                 # her sey -> build/secimler.sqlite
    python3 scripts/veritabani/build_db.py --mahalle-yok   # mahalle tablolari bos kalir (kucuk dosya)
    python3 scripts/veritabani/build_db.py -o yol.sqlite

Yuklenenler: ana secimler (elections/), meclis haritalari (meclis_harita/), mahalle sonuclari,
ek kayitlar (ek/: milletvekilleri, senato, beldeler, belediye meclisi beldeleri, ara/yenileme
secimleri) ve 2024 belediye meclisi uye dagilimi (meclis_2024.json).

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
sys.path.insert(0, str(HERE))
from common.election_io import load_all_elections  # noqa: E402

DATA = ROOT / "data" / "normalized"
GEO = ROOT / "geo" / "normalized"

REFERANDUM_SECENEKLERI = {"Evet", "Hayır"}
DIGER = {"Diğer", "Bağımsız", "Bağımsızlar", "Diğerleri"}
OYLAMA_TURU = {"genel": "milletvekili", "yerel": "baskanlik", "referandum": "referandum",
               "cumhurbaskanligi": "cumhurbaskanligi"}


HESAPLA = object()   # kazanan verilmediyse oylardan en cok alan


def yil_of(secim_id: str) -> int:
    return int(re.match(r"\d{4}", secim_id).group())


def j(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True) if o else None


def fold(s: str) -> str:
    """Turkce buyuk/kucuk harf ve bosluk farkini yok sayan anahtar."""
    return re.sub(r"[\s\-.]+", "", s.replace("İ", "i").replace("I", "ı").lower())


def oylar(oy: dict):
    """Iki kaynak bicimini tek bicime cevirir: {parti: {oy, oran, ...}} ya da {parti: sayi}."""
    for ad, v in (oy or {}).items():
        yield (ad, v) if isinstance(v, dict) else (ad, {"oy": v})


class Secenekler:
    """secenek tablosu: ad -> secenek_id. Yalniz buyuk/kucuk harfi farkli adlar ('YENİDEN REFAH',
    'Yeniden Refah') tek secenektir; ilk gorulen yazim kalir."""

    def __init__(self, con, partiler):
        self.con, self.partiler, self.ids, self.katlanmis = con, partiler, {}, {}

    def tip(self, ad, tur):
        if ad in DIGER:
            return "diger"
        if tur == "referandum" and ad in REFERANDUM_SECENEKLERI:
            return "referandum"
        if tur == "cumhurbaskanligi" and ad not in self.partiler:
            return "aday"
        return "parti"

    def id(self, ad, tur=None):
        if ad is None:
            return None
        if ad not in self.ids:
            k = fold(ad)
            if k in self.katlanmis:
                self.ids[ad] = self.katlanmis[k]
            else:
                p = self.partiler.get(ad, {})
                cur = self.con.execute(
                    "INSERT INTO secenek(ad, kisa, tip, renk_acik, renk_koyu) VALUES (?,?,?,?,?)",
                    (ad, p.get("short"), self.tip(ad, tur), p.get("light"), p.get("dark")),
                )
                self.ids[ad] = self.katlanmis[k] = cur.lastrowid
        return self.ids[ad]


def kaynak_notu(r):
    parcalar = [r.get(k) for k in ("not", "veriNotu", "etiketNotu", "ilceGeneliSonuc") if r.get(k)]
    return " | ".join(parcalar) or None


def kaynak_json(r):
    k = {key: r[key] for key in ("kaynak", "kaynak_url", "duzeltmeKaynagi", "oyKapsami",
                                 "ilceFarki", "sehirKoy") if r.get(key) is not None}
    return j(k)


class Yukleyici:
    """Ortak yazma islemleri. Ana secimler ve ek kayitlar ayni sonuc/oy tablolarina bunlarla yazar."""

    def __init__(self, con, sec):
        self.con, self.sec = con, sec
        self.il_ad = {0: "Yurt Dışı"}
        self.ilce_bilgi = {}                 # ilce_id -> (plaka, ad), kronolojik son gorulen
        self.ilce_adlari = {}                # (plaka, fold(ad)) -> [(yil, ilce_id)]
        self.secimler = set()

    def secim(self, sid, tur, oylama, ad, *, ana=None, aciklama=None, yarisma=None, temel=None,
              sandalye=None, mahalle=False):
        self.con.execute(
            "INSERT INTO secim(secim_id, tur, oylama, ana_secim_id, yil, ad, aciklama, yarisma_turu,"
            " sonuc_temeli, toplam_sandalye, mahalle_verisi) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (sid, tur, oylama, ana, yil_of(sid), ad, aciklama, yarisma, temel, sandalye or None, int(mahalle)),
        )
        self.secimler.add(sid)

    def sonuc_il(self, sid, tur, plaka, ad, r, *, kazanan=HESAPLA, notu=None):
        if ad and plaka:
            self.il_ad[plaka] = ad
        oy = list(oylar(r.get("oy")))
        if kazanan is HESAPLA:
            kazanan = r.get("kazanan") or en_cok(oy)
        self.con.execute(
            "INSERT INTO sonuc_il VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, plaka, ad, r.get("secmen"), r.get("oyKullanan"), r.get("gecerliOy"),
             r.get("gecersizOy"), r.get("sandik"), r.get("katilim"), self.sec.id(kazanan, tur),
             r.get("toplamVekil") or None, r.get("ilceSayisi"), notu or kaynak_notu(r), kaynak_json(r)),
        )
        self.con.executemany(
            "INSERT INTO oy_il VALUES (?,?,?,?,?)",
            [(sid, plaka, self.sec.id(p, tur), v.get("oy"), v.get("oran")) for p, v in oy],
        )
        self.con.executemany(
            "INSERT INTO sandalye_il VALUES (?,?,?,?)",
            [(sid, plaka, self.sec.id(p, tur), n) for p, n in (r.get("vekil") or {}).items() if n],
        )

    def sonuc_ilce(self, sid, tur, iid, plaka, ad, r, *, kazanan=HESAPLA, sadece_kazanan=None, notu=None):
        self.ilce_bilgi[iid] = (plaka, ad)
        self.ilce_adlari.setdefault((plaka, fold(ad)), []).append((yil_of(sid), iid))
        oy = list(oylar(r.get("oy")))
        if kazanan is HESAPLA:
            kazanan = r.get("kazanan") or en_cok(oy)
        if sadece_kazanan is None:
            sadece_kazanan = bool(r.get("sadeceKazanan"))
        self.con.execute(
            "INSERT INTO sonuc_ilce VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, iid, plaka, ad, r.get("secmen"), r.get("oyKullanan"), r.get("gecerliOy"),
             r.get("gecersizOy"), r.get("sandik"), r.get("katilim"), self.sec.id(kazanan, tur),
             r.get("baskan"), int(sadece_kazanan), int(bool(r.get("buyuksehirSonucu"))),
             notu or kaynak_notu(r), kaynak_json(r)),
        )
        self.con.executemany(
            "INSERT INTO oy_ilce VALUES (?,?,?,?,?,?,?)",
            [(sid, iid, self.sec.id(p, tur), v.get("oy"), v.get("oran"), v.get("aday"), v.get("sandalye"))
             for p, v in oy],
        )

    def ilce_bul(self, plaka, ad, yil):
        """Il plakasi ve ilce adindan, o yila en yakin secimdeki ilce birimini bulur."""
        if not ad:
            return None
        adaylar = []
        il = self.il_ad.get(plaka, "")
        for a in (ad, re.sub(rf"^{re.escape(il)}\s+", "", ad), "Merkez" if fold(ad) in (fold(il), fold(il + " merkez")) else None):
            if a:
                adaylar += self.ilce_adlari.get((plaka, fold(a)), [])
        if not adaylar:
            return None
        return min(adaylar, key=lambda t: (abs(t[0] - yil), -t[0]))[1]


def en_cok(oy):
    sayili = [(v.get("oy") or 0, p) for p, v in oy if v.get("oy")]
    return max(sayili)[1] if sayili else None


def ana_secimler(y: Yukleyici, mahalle_dosyalari):
    secimler = load_all_elections()
    sira = sorted(secimler, key=lambda k: (yil_of(k), k))
    for sid in sira:
        d = secimler[sid]
        tur = d["tur"]
        y.secim(sid, tur, OYLAMA_TURU[tur], d["ad"], yarisma=d.get("contestType"), temel=d.get("resultBasis"),
                sandalye=d.get("toplamSandalye"), mahalle=sid in mahalle_dosyalari)
        for r in d["iller"]:
            y.sonuc_il(sid, tur, r["plaka"], r["ad"], r, kazanan=r.get("kazanan"))
        yd = d.get("yurtdisi")
        if yd:
            r = {"oyKullanan": yd.get("kullanilanOy"), "gecerliOy": yd.get("gecerliOy"),
                 "katilim": yd.get("katilim"), "oy": yd.get("oy")}
            y.sonuc_il(sid, tur, 0, "Yurt Dışı", r, notu="Yurt dışı ve gümrük oyları")
        for r in d["ilceler"]:
            iid = r.get("geomId") or f"YOK-{r['plaka']:02d}-{r['ad']}"
            y.sonuc_ilce(sid, tur, iid, r["plaka"], r["ad"], r, kazanan=r.get("kazanan"))
    return secimler, sira


def meclis_haritalari(y: Yukleyici):
    """meclis_harita/<secim>_bm|igm.json: belediye meclisi ve il genel meclisi, il ve ilce duzeyi.
    Yalniz dogrulanmis satirlar (kitapla toplami tutanlar) oy icerir; digerleri bos ve notludur."""
    n = 0
    for p in sorted((DATA / "meclis_harita").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        ana, ek = p.stem.rsplit("_", 1)
        oylama = {"bm": "belediye_meclisi", "igm": "il_genel_meclisi"}[ek]
        y.secim(p.stem, "yerel", oylama, d["ad"], ana=ana, aciklama=d.get("aciklama") or d.get("oylamaAdi"),
                yarisma=d.get("contestType"), temel=d.get("resultBasis"))
        for r in d["iller"]:
            y.sonuc_il(p.stem, "yerel", r["plaka"], r["ad"], r, kazanan=r.get("kazanan"))
        for r in d["ilceler"]:
            y.sonuc_ilce(p.stem, "yerel", r["geomId"], r["plaka"], r["ad"], r, kazanan=r.get("kazanan"))
        n += 1
    return n


def mahalleler(y: Yukleyici, sira, secimler, mahalle_dosyalari):
    con, sec = y.con, y.sec
    geo = json.loads((GEO / "mahalle_geo.json").read_text(encoding="utf-8"))
    mahalle_ad, n_mah = {}, 0
    for sid in sira:
        if sid not in mahalle_dosyalari:
            continue
        tur = secimler[sid]["tur"]
        md = json.loads((DATA / "mahalle" / f"{sid}.json").read_text(encoding="utf-8"))
        sonuc, oy = [], []
        for iid, mler in md.items():
            for mid, r in mler.items():
                mahalle_ad.setdefault((iid, mid), (geo.get(iid, {}).get(mid) or {}).get("ad"))
                sonuc.append((sid, iid, mid, r.get("secmen"), r.get("oyKullanan"), r.get("gecerliOy"),
                              r.get("sandik"), r.get("katilim"), sec.id(r.get("kazanan"), tur)))
                oy.extend((sid, iid, mid, sec.id(p, tur), v.get("oy"), v.get("oran")) for p, v in r["oy"].items())
        con.executemany("INSERT INTO sonuc_mahalle VALUES (?,?,?,?,?,?,?,?,?)", sonuc)
        con.executemany("INSERT INTO oy_mahalle VALUES (?,?,?,?,?,?)", oy)
        n_mah += len(sonuc)
        print(f"  mahalle {sid}: {len(sonuc):,} satır, {len(oy):,} oy", flush=True)
    con.executemany("INSERT INTO mahalle VALUES (?,?,?)", [(mid, iid, ad) for (iid, mid), ad in mahalle_ad.items()])
    return n_mah


def build(out: pathlib.Path, mahalle: bool):
    import ek  # scripts/veritabani/ek.py

    t0 = time.time()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    con.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    con.execute("PRAGMA foreign_keys = OFF")  # yukleme sirasinda kapali, sonda toplu kontrol

    partiler = json.loads((DATA / "partiler.json").read_text(encoding="utf-8"))
    y = Yukleyici(con, Secenekler(con, partiler))
    mahalle_dosyalari = {p.stem for p in (DATA / "mahalle").glob("*.json")}

    secimler, sira = ana_secimler(y, mahalle_dosyalari)
    n_meclis = meclis_haritalari(y)
    ozet = ek.yukle(y)
    n_mah = mahalleler(y, sira, secimler, mahalle_dosyalari) if mahalle else 0

    # Cumhurbaskanligi adaylari partiler.json'da renk icin yer aliyor; yalniz CB seciminde
    # gecen secenekler aday sayilir.
    con.execute("""
        UPDATE secenek SET tip = 'aday'
        WHERE tip = 'parti' AND secenek_id IN (SELECT secenek_id FROM oy_il JOIN secim USING (secim_id)
                                               WHERE tur = 'cumhurbaskanligi')
          AND secenek_id NOT IN (SELECT secenek_id FROM oy_il JOIN secim USING (secim_id)
                                 WHERE tur <> 'cumhurbaskanligi')""")

    # Kaynagi yalniz oy sayisi veren satirlarda (senato, ara secimler, bazi meclis kayitlari) oran
    # bostur; gecerli oydan, o da yoksa secenek oylarinin toplamindan hesaplanir (iki ondalik).
    for t, anahtar in (("oy_il", "plaka"), ("oy_ilce", "ilce_id")):
        sonuc = "sonuc_il" if t == "oy_il" else "sonuc_ilce"
        con.execute(f"""
            UPDATE {t} SET oran = round(100.0 * oy / coalesce(
                (SELECT nullif(s.gecerli_oy, 0) FROM {sonuc} s WHERE s.secim_id = {t}.secim_id AND s.{anahtar} = {t}.{anahtar}),
                (SELECT nullif(sum(o.oy), 0) FROM {t} o WHERE o.secim_id = {t}.secim_id AND o.{anahtar} = {t}.{anahtar})), 2)
            WHERE oran IS NULL AND oy IS NOT NULL""")

    con.executemany("INSERT INTO il VALUES (?,?)", sorted(y.il_ad.items()))
    con.executemany(
        "INSERT INTO ilce VALUES (?,?,?,?)",
        [(iid, plaka, ad, int(iid.startswith("TR-D-"))) for iid, (plaka, ad) in sorted(y.ilce_bilgi.items())],
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

    for satir in ozet:
        print("  " + satir)
    print(f"{out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: "
          f"{len(sira)} ana seçim, {n_meclis} meclis oylaması, {n_mah:,} mahalle sonucu, "
          f"{out.stat().st_size / 1e6:.0f} MB, {time.time() - t0:.0f} sn")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=pathlib.Path, default=ROOT / "build" / "secimler.sqlite")
    ap.add_argument("--mahalle-yok", action="store_true", help="mahalle tablolarini doldurma")
    a = ap.parse_args()
    build(a.out.resolve(), mahalle=not a.mahalle_yok)


if __name__ == "__main__":
    main()
