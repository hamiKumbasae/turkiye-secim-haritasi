"""
Projede (data/normalized/elections) HIC OLMAYAN, 1950 ve sonrasina ait kayit
turlerini kaynak katmanindan (data/kaynaklar/wikipedia/) derleyip ayri
dosyalara yazar:

  data/normalized/ek/senato/<secim>.json          Cumhuriyet Senatosu 1961-1979
                                                  (il sonucu, ilce birincisi, secilen senatorler)
  data/normalized/ek/milletvekilleri/<secim>.json secilen milletvekilleri (1950-2023)
  data/normalized/ek/beldeler/<secim>.json        belde belediye baskanligi (yerel 1950-2024)

Bu dosyalar haritaya (build.py) BAGLI DEGIL - ayri, sorgulanabilir kayitlar.
Her kaydin `kaynak` alani: {"ana": "wikipedia", "sayfa", "revid"} (revid ile
sayfanin o anki hali: https://tr.wikipedia.org/w/index.php?oldid=<revid>).
Her dosyanin `kapsam` alani kaynagin ne kadar eksiksiz oldugunu (bulunan /
beklenen) acikca yazar; eksik ya da fazla olan secim "tam" diye sunulmaz.

Kullanim:
  python3 scripts/pipelines/wikipedia_arsiv/build_ek_kayitlar.py
"""
import collections
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
SRC = ROOT / "data" / "kaynaklar" / "wikipedia"
OUT = ROOT / "data" / "normalized" / "ek"

# Beklenen sandalye sayilari (TBMM / Cumhuriyet Senatosu secimle yenilenen uye)
MECLIS = {"1950": 487, "1954": 541, "1957": 610, "1961": 450, "1965": 450, "1969": 450, "1973": 450,
          "1977": 450, "1983": 400, "1987": 450, "1991": 450, "1995": 550, "1999": 550, "2002": 550,
          "2007": 550, "2011": 550, "2015Haziran": 550, "2015Kasim": 550, "2018": 600, "2023": 600}
SENATO = {"1961senato": 150, "1964senato": 51, "1966senato": 50, "1968senato": 53, "1973senato": 52,
          "1975senato": 54, "1977senato": 50, "1979senato": 50}


def kaynak(k, secim, tur):
    return {"ana": "wikipedia", "sayfa": k["sayfa"], "revid": k["revid"],
            "kaynakKatmani": f"data/kaynaklar/wikipedia/{tur}/{secim}.json"}


def secilenler(kayitlar, secim, tur):
    out, gorulen, tekrar = [], set(), 0
    for k in kayitlar:
        if k["tur"] != "secilen":
            continue
        anahtar = (k["plaka"], k["il"], k["ad"])
        if anahtar in gorulen:
            tekrar += 1
            continue
        gorulen.add(anahtar)
        out.append({"ad": k["ad"], "il": k["il"], "plaka": k["plaka"], "parti": k["parti"],
                    "partiAdiKaynakta": k["partiAdi"], "bolge": k.get("bolge"),
                    "kisiLink": k.get("kisiLink"), "kaynak": kaynak(k, secim, tur)})
    return out, tekrar


def kapsam(bulunan, beklenen):
    durum = "tam" if bulunan == beklenen else ("eksik" if bulunan < beklenen else "fazla")
    return {"bulunan": bulunan, "beklenen": beklenen, "durum": durum,
            "not": None if durum == "tam" else
            ("Kaynak sayfalarda bazi secilenler tablo disinda (duz liste) ya da hic yok." if durum == "eksik"
             else "Bazi il sayfalarinin 'Seçilenler' bolumu aday listelerini de iceriyor; fazla kayitlar ayiklanmadi.")}


def yaz(alt, secim, veri):
    (OUT / alt).mkdir(parents=True, exist_ok=True)
    (OUT / alt / f"{secim}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ozet = collections.defaultdict(dict)
    for secim, beklenen in MECLIS.items():
        d = json.loads((SRC / "genel" / f"{secim}.json").read_text(encoding="utf-8"))
        s, tekrar = secilenler(d["kayitlar"], secim, "genel")
        yaz("milletvekilleri", secim, {"secim": secim, "tur": "milletvekilleri", "kaynak": "wikipedia",
                                       "kapsam": dict(kapsam(len(s), beklenen), ayiklananTekrar=tekrar),
                                       "kayitlar": s})
        ozet["milletvekilleri"][secim] = f"{len(s)}/{beklenen}"
    for secim, beklenen in SENATO.items():
        d = json.loads((SRC / "senato" / f"{secim}.json").read_text(encoding="utf-8"))
        s, tekrar = secilenler(d["kayitlar"], secim, "senato")
        iller = [{"il": k["il"], "plaka": k["plaka"], "secmen": k.get("secmen"), "sandik": k.get("sandik"),
                  "gecerliOy": k.get("gecerliOy"), "gecersizOy": k.get("gecersizOy"),
                  "adaylar": k.get("adaylar") or k.get("partiler"), "kaynak": kaynak(k, secim, "senato")}
                 for k in d["kayitlar"] if k["tur"] == "il_sonuc"]
        ilce = [{"il": k["il"], "plaka": k["plaka"], "ilce": k["ad"], "birinciParti": k["parti"],
                 "partiAdiKaynakta": k["partiAdi"], "kaynak": kaynak(k, secim, "senato")}
                for k in d["kayitlar"] if k["tur"] == "ilce_birinci"]
        yaz("senato", secim, {"secim": secim, "tur": "senato", "kaynak": "wikipedia",
                              "aciklama": "Cumhuriyet Senatosu uye secimi (1961 Anayasasi; uyelerin ucte biri 2 yilda bir yenilenirdi, 1980'de kaldirildi).",
                              "kapsam": {"senator": dict(kapsam(len(s), beklenen), ayiklananTekrar=tekrar),
                                         "ilSayisi": len(iller), "ilceBirincisi": len(ilce)},
                              "iller": iller, "ilceBirincileri": ilce, "secilenler": s})
        ozet["senato"][secim] = f"{len(iller)} il, {len(ilce)} ilce, {len(s)}/{beklenen} senator"
    for f in sorted((SRC / "yerel").glob("*.json")):
        secim = f.stem
        if int(secim[:4]) < 1950:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        b = [{"belde": k["ad"], "ilce": k.get("ust"), "il": k["il"], "plaka": k["plaka"],
              "kazanan": k["kazanan"], "aday": k["kazananHam"]["aday"], "oy": k["kazananHam"]["oy"],
              "partiAdiKaynakta": k["kazananHam"]["partiAdi"], "kaynak": kaynak(k, secim, "yerel")}
             for k in d["kayitlar"] if k["tur"] == "belde"]
        if not b:
            continue
        yaz("beldeler", secim, {"secim": secim, "tur": "belde_belediye_baskanligi", "kaynak": "wikipedia",
                                "kapsam": {"bulunan": len(b), "not": "Sadece kazanan (aday/oy varsa); belde sayisi resmi listeyle karsilastirilmadi."},
                                "kayitlar": b})
        ozet["beldeler"][secim] = len(b)
    for k, v in ozet.items():
        print(k, v)


if __name__ == "__main__":
    main()
