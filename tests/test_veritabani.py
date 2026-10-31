#!/usr/bin/env python3
"""build/secimler.sqlite'in kaynak JSON'larla birebir tuttugunu dogrular.

    python3 scripts/veritabani/build_db.py && python3 tests/test_veritabani.py
"""
import json
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_all_elections  # noqa: E402

DB = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build" / "secimler.sqlite"
hatalar = []


def kontrol(ad, beklenen, bulunan):
    if beklenen != bulunan:
        hatalar.append(f"{ad}: beklenen {beklenen}, bulunan {bulunan}")


def main():
    con = sqlite3.connect(DB)
    q = lambda sql, *p: con.execute(sql, p).fetchone()[0]  # noqa: E731

    kontrol("yabancı anahtar ihlali", 0, len(con.execute("PRAGMA foreign_key_check").fetchall()))
    secimler = load_all_elections()
    NORM = ROOT / "data" / "normalized"
    oku = lambda p: json.loads(p.read_text(encoding="utf-8"))  # noqa: E731
    oyv = lambda v: (v.get("oy") if isinstance(v, dict) else v) or 0  # noqa: E731
    meclis = {p.stem: oku(p) for p in sorted((NORM / "meclis_harita").glob("*.json"))}
    ek = lambda klasor: sorted((NORM / "ek" / klasor).glob("*.json"))  # noqa: E731
    kontrol("oylama sayısı", len(secimler) + len(meclis) + len(ek("senato")) + len(ek("yenileme_ara")),
            q("SELECT count(*) FROM secim"))

    # Ana secimler ve meclis haritalari ayni bicimde: il/ilce satiri, oy toplamlari
    for sid, d in [*secimler.items(), *meclis.items()]:
        kontrol(f"{sid} il satırı", len(d["iller"]), q("SELECT count(*) FROM sonuc_il WHERE secim_id=? AND plaka>0", sid))
        kontrol(f"{sid} ilçe satırı", len(d["ilceler"]), q("SELECT count(*) FROM sonuc_ilce WHERE secim_id=?", sid))
        for duzey, tablo in (("iller", "oy_il"), ("ilceler", "oy_ilce")):
            json_oy = sum(oyv(v) for r in d[duzey] for v in r["oy"].values())
            json_n = sum(len(r["oy"]) for r in d[duzey])
            filtre = " AND plaka>0" if tablo == "oy_il" else ""
            kontrol(f"{sid} {tablo} oy toplamı", json_oy,
                    q(f"SELECT coalesce(sum(oy),0) FROM {tablo} WHERE secim_id=?{filtre}", sid))
            kontrol(f"{sid} {tablo} satır", json_n, q(f"SELECT count(*) FROM {tablo} WHERE secim_id=?{filtre}", sid))
        json_secmen = sum(r.get("secmen") or 0 for r in d["iller"])
        kontrol(f"{sid} il seçmen toplamı", json_secmen,
                q("SELECT coalesce(sum(secmen),0) FROM sonuc_il WHERE secim_id=? AND plaka>0", sid))
        kontrol(f"{sid} sandalye", sum(sum((r.get("vekil") or {}).values()) for r in d["iller"]),
                q("SELECT coalesce(sum(sandalye),0) FROM sandalye_il WHERE secim_id=?", sid))

    # Ek kayitlar
    for p in ek("milletvekilleri"):
        d = oku(p)
        kontrol(f"{p.stem} milletvekili", len(d["kayitlar"]),
                q("SELECT count(*) FROM secilen WHERE secim_id=? AND gorev='milletvekili'", d["secim"]))
    for p in ek("senato"):
        d = oku(p)
        kontrol(f"{p.stem} il satırı", len(d["iller"]), q("SELECT count(*) FROM sonuc_il WHERE secim_id=?", p.stem))
        kontrol(f"{p.stem} il oy toplamı", sum(a.get("oy") or 0 for r in d["iller"] for a in r["adaylar"]),
                q("SELECT coalesce(sum(oy),0) FROM oy_il WHERE secim_id=?", p.stem))
        kontrol(f"{p.stem} senatör", len(d["secilenler"]),
                q("SELECT count(*) FROM secilen WHERE secim_id=? AND gorev='senator'", p.stem))
    for p in ek("yenileme_ara"):
        d = oku(p)
        kontrol(f"{p.stem} il satırı", len({r["plaka"] for r in d.get("iller") or []}),
                q("SELECT count(*) FROM sonuc_il WHERE secim_id=?", p.stem))
        kontrol(f"{p.stem} birim satırı", len(d.get("birimler") or []) + sum(
                    len([i for i in r.get("ilceler") or [] if i.get("geomId")]) for r in d.get("iller") or []),
                q("SELECT count(*) FROM sonuc_ilce WHERE secim_id=?", p.stem)
                + q("SELECT count(*) FROM sonuc_belde WHERE secim_id=?", p.stem))
    for p in ek("beldeler"):
        d = oku(p)
        kontrol(f"{p.stem} belde başkanlığı", len(d["kayitlar"]),
                q("SELECT count(*) FROM sonuc_belde WHERE secim_id=?", d["secim"]))
        kontrol(f"{p.stem} belde TÜİK oy toplamı",
                sum(sum(k["tuik"]["oy"].values()) for k in d["kayitlar"] if k.get("tuik")),
                q("SELECT coalesce(sum(o.oy),0) FROM oy_belde o JOIN sonuc_belde b USING(sonuc_belde_id)"
                  " WHERE b.secim_id=? AND b.kaynak='tuik'", d["secim"]))
    for p in ek("belediye_meclisi"):
        bel = [r for r in oku(p)["birimler"]
               if r.get("tip") == "belde" or r.get("beldeId") is not None or r.get("belde")]
        kontrol(f"{p.stem} meclis beldeleri", len(bel), q("SELECT count(*) FROM sonuc_belde WHERE secim_id=?", p.stem + "_bm"))
        kontrol(f"{p.stem} meclis belde oy toplamı",
                sum(v for r in bel for v in (r.get("oy") or {}).values() if v is not None and v < 10**12),
                q("SELECT coalesce(sum(o.oy),0) FROM oy_belde o JOIN sonuc_belde b USING(sonuc_belde_id)"
                  " WHERE b.secim_id=?", p.stem + "_bm"))
    m24 = oku(NORM / "meclis_2024.json")
    kontrol("2024 meclis üye toplamı", sum(sum(v["partiler"].values()) for v in m24.values()),
            q("SELECT sum(sandalye) FROM sandalye_ilce WHERE secim_id='2024yerel_bm'"))

    mahalle = sorted((ROOT / "data" / "normalized" / "mahalle").glob("*.json"))
    if not q("SELECT count(*) FROM sonuc_mahalle"):
        mahalle = []   # --mahalle-yok ile uretilmis
    else:
        for p in mahalle:
            md = json.loads(p.read_text(encoding="utf-8"))
            n = sum(len(m) for m in md.values())
            oy = sum((v.get("oy") or 0) for m in md.values() for r in m.values() for v in r["oy"].values())
            kontrol(f"{p.stem} mahalle satır", n, q("SELECT count(*) FROM sonuc_mahalle WHERE secim_id=?", p.stem))
            kontrol(f"{p.stem} mahalle oy", oy,
                    q("SELECT coalesce(sum(oy),0) FROM oy_mahalle WHERE secim_id=?", p.stem))

    # Gorunumler tablolarla ayni satir sayisini vermeli (JOIN'de satir kaybi yok)
    for gorunum, tablo in (("v_oy_il", "oy_il"), ("v_oy_ilce", "oy_ilce"), ("v_oy_mahalle", "oy_mahalle"),
                           ("v_secilen", "secilen"), ("v_oy_belde", "oy_belde")):
        kontrol(f"{gorunum} satır", q(f"SELECT count(*) FROM {tablo}"), q(f"SELECT count(*) FROM {gorunum}"))
    ist = next(r for r in secimler["2023"]["iller"] if r["plaka"] == 34)["oy"]["AK Parti"]["oran"]
    kontrol("2023 İstanbul AK Parti oranı", ist,
            q("SELECT oran FROM v_oy_il WHERE secim_id='2023' AND plaka=34 AND secenek='AK Parti'"))
    kontrol("CB adayları 'aday' tipinde", "aday",
            q("SELECT tip FROM secenek WHERE ad='Recep Tayyip Erdoğan'"))

    if hatalar:
        print(f"{len(hatalar)} hata:\n  " + "\n  ".join(hatalar[:50]))
        sys.exit(1)
    print(f"tamam: {q('SELECT count(*) FROM secim')} oylama, {len(mahalle)} mahalle dosyası, ek kayıtlar kaynakla birebir")


if __name__ == "__main__":
    main()
