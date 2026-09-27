"""
1994-2004 yerel secimlerinde ilce satirinin belediye baskanligi sonucunu ilce belediyesinin
kendi yarisina cevirir.

Sorun: bu yillarin ilce satirlari YSK il arsivinden (merge_mahalli.py resmi_karsilastir). YSK
arsivindeki ilce satiri cogu zaman tek bir yaris degil: ilce merkezi + bagli beldelerin
toplami, buyuksehir ilcelerinde buyuksehir baskanligi yarisinin o ilcedeki oylari ya da
bilesimi kayitli olmayan bir toplam (kaynak.tuik.birim / kaynak.tuikBirimFarki). Haritada bu
toplamin birincisi ilcenin rengi oluyordu; ilce belediye baskanini kazanan parti bundan farkli
olabiliyor (1994 Cal: toplamda SHP, ilce belediyesinde DYP).

Kural:
  - Bu uc turden bir satirin DIE kitabindaki ilce merkezi belediyesi satiri (belediye
    baskanligi tablosu; kaynak.tuik.sayfa + ad ile tek aday) 'tutarli' ve kimligi cozulmusse
    oy, kazanan, gecerliOy, secmen, sandik, katilim o satirdan alinir. YSK satirinin degerleri
    kaynak.yskSatiri'nda aynen saklanir; aday adlari korunur.
  - DIE satiri dogrulanamiyorsa degerlere dokunulmaz; satira 'ilceGeneliSonuc' (ne oldugu)
    yazilir, on yuz ipucunda gosterir.
  - Idempotent: kaynak.yskSatiri olan satir atlanir. geomId/ad degismez.

Zincir: merge_mahalli.py'den sonra (bu adim taban dosyadan yeniden uretilmez), sonra
meclis_harita/build_meclis_harita.py ve scripts/build.py.

Kullanim:
  .venv/bin/python scripts/pipelines/tuik_arsiv/ilce_belediyesi_sonucu.py
"""
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
from common.election_io import load_election, save_election  # noqa: E402
from extract_mahalli import _anahtar  # noqa: E402

ROOT = HERE.parent.parent.parent
SRC = ROOT / "data" / "kaynaklar" / "tuik" / "yerel"
SECIMLER = ["1994yerel", "1999yerel", "2004yerel"]
TOPLAM = "ilçe merkezi + bağlı beldeler toplamı"
BB = "büyükşehir belediye başkanlığı (ilçedeki oylar)"
ACIKLAMA = {TOPLAM: "ilçe merkezi ve bağlı beldelerin toplamı",
            BB: "büyükşehir belediye başkanlığı oylarının ilçedeki dağılımı",
            None: "YSK ilçe toplamı (hangi belediyeleri kapsadığı kayıtlı değil)"}


def dogrulanmis(d):
    return (d.get("kontrol") or {}).get("durum") == "tutarli" and (d.get("kimlik") or {}).get("yontem") != "cozulemedi"


def main():
    for secim in SECIMLER:
        rec = load_election(secim)
        katman = json.loads((SRC / secim / "belediye_baskanligi.json").read_text(encoding="utf-8"))["satirlar"]
        sayfa_idx = collections.defaultdict(list)
        for d in katman:
            if d.get("tip") == "ilce" and d.get("plaka"):
                sayfa_idx[(d["plaka"], tuple(d.get("sayfa") or []))].append(d)
        sayac = collections.Counter()
        for r in rec["ilceler"]:
            k = r.get("kaynak") or {}
            tuik = k.get("tuik") or {}
            birim = tuik.get("birim")
            if k.get("yskSatiri") or not (birim in (TOPLAM, BB) or k.get("tuikBirimFarki")):
                continue
            aday = [d for d in sayfa_idx.get((r["plaka"], tuple(tuik.get("sayfa") or [])), [])
                    if (tuik.get("adKaynakta") and d.get("adKaynakta") == tuik["adKaynakta"])
                    or _anahtar(d.get("ad") or d.get("adKaynakta") or "") == _anahtar(r["ad"])]
            d = aday[0] if len(aday) == 1 else None
            tur = birim if birim in (TOPLAM, BB) else None
            if not d or not dogrulanmis(d):
                r["ilceGeneliSonuc"] = ACIKLAMA[tur]
                sayac["dogrulanamadi" if d else "die_satiri_yok"] += 1
                continue
            eski = {"birim": ACIKLAMA[tur], "oy": {p: (v.get("oy") if isinstance(v, dict) else v) for p, v in r["oy"].items()},
                    "kazanan": r.get("kazanan")}
            for alan in ("gecerliOy", "secmen", "sandik", "katilim"):
                eski[alan] = r.get(alan)
            if k.get("tuikBirimFarki"):
                eski["tuikBirimFarki"] = k.pop("tuikBirimFarki")
            adaylar = {p: v.get("aday") for p, v in r["oy"].items() if isinstance(v, dict) and v.get("aday")}
            g = d["gecerliOy"]
            r["oy"] = {p: {"oy": o, "oran": round(100 * o / g, 2), **({"aday": adaylar[p]} if p in adaylar else {})}
                       for p, o in sorted(d["oy"].items()) if o}
            r["kazanan"] = max(r["oy"], key=lambda p: r["oy"][p]["oy"]) if r["oy"] else None
            r["gecerliOy"], r["secmen"], r["sandik"], r["katilim"] = g, d["secmen"], d["sandik"], d["katilim"]
            r.pop("ilceGeneliSonuc", None)
            k.pop("teyit", None)
            k["ana"] = "tuik"
            tuik.update({"birim": "ilçe merkezi belediyesi", "tablo": "belediye_baskanligi"})
            tuik.pop("digerDagilimi", None)
            k["tuik"] = tuik
            k["yskSatiri"] = eski
            r["kaynak"] = k
            sayac["duzeltildi"] += 1
            sayac["kazanan_degisti"] += eski["kazanan"] != r["kazanan"]
        save_election(secim, rec)
        print(secim, dict(sayac))


if __name__ == "__main__":
    main()
