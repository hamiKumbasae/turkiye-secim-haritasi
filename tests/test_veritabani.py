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
    kontrol("seçim sayısı", len(secimler), q("SELECT count(*) FROM secim"))

    for sid, d in secimler.items():
        kontrol(f"{sid} il satırı", len(d["iller"]), q("SELECT count(*) FROM sonuc_il WHERE secim_id=? AND plaka>0", sid))
        kontrol(f"{sid} ilçe satırı", len(d["ilceler"]), q("SELECT count(*) FROM sonuc_ilce WHERE secim_id=?", sid))
        for duzey, tablo in (("iller", "oy_il"), ("ilceler", "oy_ilce")):
            json_oy = sum((v.get("oy") or 0) for r in d[duzey] for v in r["oy"].values())
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
    for gorunum, tablo in (("v_oy_il", "oy_il"), ("v_oy_ilce", "oy_ilce"), ("v_oy_mahalle", "oy_mahalle")):
        kontrol(f"{gorunum} satır", q(f"SELECT count(*) FROM {tablo}"), q(f"SELECT count(*) FROM {gorunum}"))
    ist = next(r for r in secimler["2023"]["iller"] if r["plaka"] == 34)["oy"]["AK Parti"]["oran"]
    kontrol("2023 İstanbul AK Parti oranı", ist,
            q("SELECT oran FROM v_oy_il WHERE secim_id='2023' AND plaka=34 AND secenek='AK Parti'"))
    kontrol("CB adayları 'aday' tipinde", "aday",
            q("SELECT tip FROM secenek WHERE ad='Recep Tayyip Erdoğan'"))

    if hatalar:
        print(f"{len(hatalar)} hata:\n  " + "\n  ".join(hatalar[:50]))
        sys.exit(1)
    print(f"tamam: {len(secimler)} seçim, {len(mahalle)} mahalle dosyası kaynakla birebir")


if __name__ == "__main__":
    main()
