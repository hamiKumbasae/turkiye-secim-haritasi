"""
2009-2011 YSK aktarimlarinda dusen "Merkez" ilce satirlarini geri koyar.

YSK acik verisinde 2012'de bolunen uc ilin eski Merkez ilcesi (Denizli -> Merkezefendi +
Pamukkale, Hatay -> Antakya + Defne, Van -> Ipekyolu + Tusba) bugunku ilce kimligine
eslenemedigi icin aktarimda ilce satiri olarak dusmustu; oylari il toplaminda duruyordu
(bkz. election_import/PROVENANCE.md "Bilinen kapsam siniri"). Bu betik:

  - 2010 referandumu ve 2011 genel secim: Merkez satiri = il satiri - ildeki diger ilce
    satirlarinin toplami. Il satiri ayni YSK sandik verisinin il toplami oldugu icin fark,
    dusen Merkez sandiklarinin toplamina esittir (tahmin degil; 2015 sonrasi secimlerde il
    satiri ilce toplamina birebir esit). Parti/secenek oylari, secmen, sandik ve gecerli oy
    ayri ayri cikarilir; katilim il ve ilce katilim*secmen degerlerinden (yuvarlama payi var).
  - 2009 yerel (belediye baskanligi): Denizli ve Hatay o tarihte buyuksehir degildi; il satiri il
    merkezi belediyesinin sonucudur. Merkez satiri il satirinin birebir kopyasidir
    (ekle_il_merkezi_satirlari.py ile ayni kural, ilMerkeziBelediyesi: true). Meclis
    sonuclari ham YSK dosyasindan build_meclis_harita.py ile bu satira baglanir.
  - 2012 oncesi YSK'de ayri birim olarak gecen "Pamukkale" (Pamukkale beldesi; 2012'de ilce
    oldu) satiri oldugu gibi kalir; poligonu HIST-Denizli-Merkez tarafindan gizlenir (haritada
    Merkez'in icinde), oyu tabloda ve il toplaminda durur. Satira aciklama notu eklenir.

  - 2010 ve 2017 referandumunda henuz kurulmamis ilcelerin bos satirlari {Evet: 0, Hayir: 0} ile
    geliyordu; on yuz bunlari sonuclu sayip boyuyordu. Sandigi, secmeni ve gecerli oyu 0 olan
    satirin oy alani bosaltilir (diger secimlerdeki bos satirlarla ayni bicim).

Merkez satirlarinin poligonu: HIST-Denizli-Merkez, HIST-Hatay-Merkez, HIST-Van-Merkez
(scripts/pipelines/historical_geo/birlesim_2009_sonrasi.py uretir).

Idempotent: once eklenmis satirlari silip yeniden hesaplar.

Kullanim:
  python3 scripts/pipelines/election_import/merkez_ilce_tamamla.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

ISARET = "merkezIlceTamamlama"
FARK = {  # secim -> {plaka: geomId}
    "2010referandum": {20: "HIST-Denizli-Merkez", 31: "HIST-Hatay-Merkez"},
    "2011": {20: "HIST-Denizli-Merkez", 31: "HIST-Hatay-Merkez", 65: "HIST-Van-Merkez"},
}
# il satirinda olmayan ilce etiketi -> il satirindaki karsiligi. 2011 Van: BDP destekli bagimsizlar il
# satirinda "BDP", ilce satirlarinin bir kisminda "Bağımsız" (kaynaktaki haliyle; burada yalniz fark icin).
ESDEGER = {("2011", 65): {"Bağımsız": "BDP"}}
KOPYA = {"2009yerel": {20: "HIST-Denizli-Merkez", 31: "HIST-Hatay-Merkez"}}
PAMUKKALE_SECIMLER = ["2009yerel", "2010referandum", "2011"]
PAMUKKALE_NOT = ("2012 öncesi YSK verisinde ayrı birim olarak geçen Pamukkale beldesi (2012'de ilçe oldu); "
                 "haritada ayrı çizilmez, alanı Merkez ilçesinin poligonunda.")
ACIKLAMA_FARK = ("YSK aktarımında Merkez ilçesi bugünkü ilçelere eşlenemediği için düşmüştü; satır = il satırı − "
                 "ildeki diğer ilçe satırları (aynı YSK sandık verisi). Katılım yuvarlama payıyla.")
ACIKLAMA_KOPYA = "İl merkezi belediyesi: il satırının sonucu (o tarihte büyükşehir değil)."


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def temizle(rec):
    rec["ilceler"] = [r for r in rec["ilceler"] if not r.get(ISARET)]


def fark_satiri(rec, plaka, geom, esdeger):
    il = next(i for i in rec["iller"] if i["plaka"] == plaka)
    digerleri = [r for r in rec["ilceler"] if r["plaka"] == plaka]
    ilce_oy = {}
    for r in digerleri:
        for parti, v in (r.get("oy") or {}).items():
            k = esdeger.get(parti, parti)
            ilce_oy[k] = ilce_oy.get(k, 0) + (v.get("oy") or 0)
    if set(ilce_oy) - set(il["oy"]):
        raise SystemExit(f"{plaka}: il satirinda olmayan ilce etiketi {sorted(set(ilce_oy) - set(il['oy']))}")
    oy = {}
    for parti, v in il["oy"].items():
        kalan = (v.get("oy") or 0) - ilce_oy.get(parti, 0)
        if kalan < 0:
            raise SystemExit(f"{plaka} {parti}: negatif fark {kalan}")
        if kalan:
            oy[parti] = kalan
    gecerli = il["gecerliOy"] - sum(r.get("gecerliOy") or 0 for r in digerleri)
    if gecerli != sum(oy.values()):
        raise SystemExit(f"{plaka}: parti farki {sum(oy.values())} != gecerli farki {gecerli}")
    secmen = il["secmen"] - sum(r.get("secmen") or 0 for r in digerleri)
    sandik = il["sandik"] - sum(r.get("sandik") or 0 for r in digerleri)
    kullanan = il["katilim"] * il["secmen"] / 100 - sum((r.get("katilim") or 0) * (r.get("secmen") or 0) / 100
                                                        for r in digerleri)
    satir = {
        "ad": "Merkez", "plaka": plaka, "geomId": geom, "gecerliOy": gecerli, "secmen": secmen,
        "sandik": sandik, "katilim": round(100 * kullanan / secmen, 2),
        "oy": {p: {"oy": n, "oran": round(100 * n / gecerli, 2)} for p, n in sorted(oy.items())},
        "kazanan": max(oy, key=oy.get), "toplamVekil": 0, "vekil": {},
        "kaynak": {"ana": "ysk", "yontem": "il_eksi_ilceler", "aciklama": ACIKLAMA_FARK},
        ISARET: True,
    }
    return satir


def kopya_satiri(rec, plaka, geom):
    il = next(i for i in rec["iller"] if i["plaka"] == plaka)
    satir = {k: v for k, v in il.items() if k in ("gecerliOy", "secmen", "sandik", "katilim", "oy", "kazanan",
                                                    "toplamVekil", "vekil", "gecersizOy", "oyKullanan")}
    satir.update({"ad": "Merkez", "plaka": plaka, "geomId": geom, "ilMerkeziBelediyesi": True,
                  "kaynak": {"ana": "ysk", "yontem": "il_satiri", "aciklama": ACIKLAMA_KOPYA}, ISARET: True})
    satir.setdefault("toplamVekil", 0)
    satir.setdefault("vekil", {})
    return satir


def sifir_satirlari(rec):
    n = 0
    for r in rec["ilceler"]:
        oy = r.get("oy") or {}
        if oy and not r.get("sandik") and not r.get("secmen") and not r.get("gecerliOy") \
                and all(not (v or {}).get("oy") for v in oy.values()):
            r["oy"] = {}
            n += 1
    return n


def main():
    for p in sorted(ROOT.glob("data/normalized/elections/*/*.json")):
        if p.stem[:4].isdigit() and int(p.stem[:4]) >= 2009:
            rec = load_election(p.stem)
            n = sifir_satirlari(rec)
            if n:
                save_election(p.stem, rec)
                print(p.stem, f"{n} sıfır oylu boş satırın oy alanı boşaltıldı")
    for secim in sorted(set(FARK) | set(KOPYA) | set(PAMUKKALE_SECIMLER)):
        rec = load_election(secim)
        sifir_satirlari(rec)
        temizle(rec)
        for plaka, geom in FARK.get(secim, {}).items():
            if any(r["plaka"] == plaka and r.get("geomId") == geom for r in rec["ilceler"]):
                raise SystemExit(f"{secim} {plaka}: {geom} satiri zaten var")
            rec["ilceler"].append(fark_satiri(rec, plaka, geom, ESDEGER.get((secim, plaka), {})))
        for plaka, geom in KOPYA.get(secim, {}).items():
            rec["ilceler"].append(kopya_satiri(rec, plaka, geom))
        if secim in PAMUKKALE_SECIMLER:
            for r in rec["ilceler"]:
                if r["plaka"] == 20 and r["ad"] == "Pamukkale":
                    r["geomId"] = "TR-D-20-016"
                    r["veriNotu"] = PAMUKKALE_NOT
        save_election(secim, rec)
        eklenen = [r for r in rec["ilceler"] if r.get(ISARET)]
        print(secim, ", ".join(f"{r['plaka']} {r['ad']} ({r['gecerliOy']:,} geçerli oy)" for r in eklenen))


if __name__ == "__main__":
    main()
