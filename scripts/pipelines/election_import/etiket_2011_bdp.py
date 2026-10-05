"""
2011 genel secim: BDP destekli bagimsizlarin ilce satirlarindaki etiketini il satiriyla esitler.

2011'de BDP adaylari "Emek, Demokrasi ve Ozgurluk Bloku" bagimsizlari olarak girdi. Diyarbakir,
Mardin, Mus, Van ve Batman'da il satiri bu oylarin tamamini "BDP" olarak tasir (il satirinda
"Bağımsız" yok); ilce satirlarinin bir kisminda ise ayni oylar "Bağımsız" diye geliyordu. Bu
illerde ilcelerin BDP + Bağımsız toplami il satirinin BDP oyuna birebir esit, diger partiler de
tutuyor. Haritada ayni bloğun oyu iki renge bolunuyordu.

Kural (idempotent): il satirinda "BDP" olup "Bağımsız" olmayan illerde, ilce satirindaki
"Bağımsız" oyu "BDP"ye eklenir; oran ve kazanan yeniden hesaplanir. Il toplami tutmazsa durur.
Diger illerdeki bagimsizlara dokunulmaz (oralarda il satiri da "Bağımsız").

Kullanim (tarihsel_sinirlari_uret.py, merkez_ilce_tamamla.py'den sonra cagirir; il toplami ancak
2011 Van Merkez satiri geri konduktan sonra tutar):
  python3 scripts/pipelines/election_import/etiket_2011_bdp.py
"""
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

SECIM = "2011"
NOT = ("BDP destekli bağımsızların oyu (Emek, Demokrasi ve Özgürlük Bloku); kaynakta bu ilçede "
       "\"Bağımsız\" etiketliydi, il satırıyla aynı biçimde BDP'ye bağlandı.")


def main():
    rec = load_election(SECIM)
    hedef = {i["plaka"]: i for i in rec["iller"] if "BDP" in i["oy"] and "Bağımsız" not in i["oy"]}
    degisen = collections.Counter()
    for r in rec["ilceler"]:
        oy = r.get("oy") or {}
        if r["plaka"] not in hedef or "Bağımsız" not in oy:
            continue
        ek = oy.pop("Bağımsız")["oy"] or 0
        bdp = (oy.get("BDP") or {}).get("oy") or 0
        g = r["gecerliOy"]
        oy["BDP"] = {"oy": bdp + ek, "oran": round(100 * (bdp + ek) / g, 2) if g else None}
        r["kazanan"] = max(oy, key=lambda p: oy[p]["oy"] or 0)
        r["etiketNotu"] = NOT
        degisen[r["plaka"]] += 1
    # dogrulama: her hedef ilde ilce BDP toplami = il BDP
    for pl, il in hedef.items():
        t = sum(((r.get("oy") or {}).get("BDP") or {}).get("oy") or 0 for r in rec["ilceler"] if r["plaka"] == pl)
        if t != il["oy"]["BDP"]["oy"]:
            raise SystemExit(f"{il['ad']}: ilçe BDP toplamı {t} != il {il['oy']['BDP']['oy']}")
    if degisen:
        save_election(SECIM, rec)
    print(SECIM, ", ".join(f"{hedef[p]['ad']} {n} ilçe" for p, n in sorted(degisen.items())) or "değişiklik yok")


if __name__ == "__main__":
    main()
