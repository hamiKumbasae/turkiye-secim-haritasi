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
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE))
SRC = ROOT / "data" / "kaynaklar" / "wikipedia"
OUT = ROOT / "data" / "normalized" / "ek"

# Beklenen sandalye sayilari (TBMM / Cumhuriyet Senatosu secimle yenilenen uye)
MECLIS = {"1950": 487, "1954": 541, "1957": 610, "1961": 450, "1965": 450, "1969": 450, "1973": 450,
          "1977": 450, "1983": 400, "1987": 450, "1991": 450, "1995": 550, "1999": 550, "2002": 550,
          "2007": 550, "2011": 550, "2015Haziran": 550, "2015Kasim": 550, "2018": 600, "2023": 600}
SENATO = {"1961senato": 150, "1964senato": 51, "1966senato": 50, "1968senato": 53, "1973senato": 52,
          "1975senato": 54, "1977senato": 50, "1979senato": 50}


TUIK_SENATO = ROOT / "data" / "kaynaklar" / "tuik" / "senato"
TUIK_GENEL = ROOT / "data" / "kaynaklar" / "tuik" / "genel"
# senato/ara secim -> ilce geomId icin en yakin genel secim (merge_yerel_ilce kurali)
YAKIN = {"1961senato": "1961", "1964senato": "1965", "1966senato": "1965", "1968senato": "1969",
         "1973senato": "1973", "1975senato": "1973", "1977senato": "1977", "1979senato": "1977",
         "1966ara": "1965"}


DOGRU_AD = {}  # (plaka, fold(ad)) -> projedeki yazim
# OCR bozulmasi ya da donem adi -> referans ilce adi (yalnizca emin olunanlar)
OCR_ALIAS = {"MAGARA": "Tufanbeyli", "S KOCHISAR": "Şereflikoçhisar", "CINI": "Çine", "ENES": "Enez"}


def _plaka(ad):
    import difflib
    sys.path.insert(0, str(HERE))
    from iller import plaka, _MODERN, _TARIHSEL_F  # noqa: E402
    from common.turkish_text import fold
    p = plaka(ad) or {"A KARAHISAR": 3, "AKARAHISAR": 3, "K MARAS": 46}.get(fold(ad))
    if p:
        return p, None
    adaylar = list(_MODERN) + list(_TARIHSEL_F)
    m = difflib.get_close_matches(fold(ad), adaylar, n=1, cutoff=0.75)
    if m:
        return (_MODERN.get(m[0]) or _TARIHSEL_F[m[0]]), f"OCR adı '{ad}' → en yakın il adı"
    return None, None


def tuik_ilce_oylari(secim, dosya):
    """data/kaynaklar/tuik/.../<secim>.json -> il ve ilce oy kayitlari (kaynak = tuik)."""
    if not dosya.exists():
        return None
    import merge_yerel_ilce as my
    from common.election_io import load_election
    from common.turkish_text import fold as _f
    my.YAKIN_GENEL[secim] = YAKIN[secim]
    ctx = my.ref_index()
    if not DOGRU_AD:
        for ref in my.REFS + sorted(set(YAKIN.values())):
            for r in load_election(ref)["ilceler"]:
                DOGRU_AD.setdefault((r["plaka"], _f(r["ad"])), r["ad"])
    d = json.loads(dosya.read_text(encoding="utf-8"))
    iller = []
    for il in d["iller"]:
        pl, not_ = _plaka(il["ad"])
        ilceler = []
        # ayni plakadaki bilinen ilce adlari (referans secimlerden) - OCR yazim hatalari icin
        from common.turkish_text import fold
        bilinen = {f: ad for (p_, f), ad in DOGRU_AD.items() if p_ == pl}
        for i in il["ilceler"]:
            ad, ad_not = i["ad"], None
            if fold(ad) in OCR_ALIAS:
                ad_not = f"OCR/dönem adı '{ad}' → '{OCR_ALIAS[fold(ad)]}'"
                ad = OCR_ALIAS[fold(ad)]
            gid = my.resolve(ctx, secim, pl, ad, il["ad"])[0] if pl else None
            if pl and gid is None:
                import difflib
                f = fold(ad).replace(" ", "")
                m = difflib.get_close_matches(f, [b.replace(" ", "") for b in bilinen], n=1, cutoff=0.8)
                if m:
                    ref = bilinen[next(b for b in bilinen if b.replace(" ", "") == m[0])]
                    gid2 = my.resolve(ctx, secim, pl, ref, il["ad"])[0]
                    if gid2:
                        gid, ad_not = gid2, f"OCR adı '{ad}' → '{ref}' (en yakın ilçe adı)"
            ilceler.append({"ilce": i["ad"], "geomId": gid, **{k: i.get(k) for k in ("sandik", "secmen", "oyKullanan", "muteber")},
                            "oy": i["oy"], "Bağımsız": i["Bağımsız"],
                            "kaynak": {"ana": "tuik", "sayfa": i["sayfa"], "adKaynakta": i["adKaynakta"],
                                       **({"kaynakIciTutarsizlik": i["tutarsiz"]} if i.get("tutarsiz") else {}),
                                       **({"adDuzeltme": ad_not} if ad_not else {}),
                                       **({"kisitlaCozuldu": True} if i.get("kisitlaCozuldu") else {})}})
        iller.append({"il": il["ad"], "plaka": pl, **{k: il.get(k) for k in ("sandik", "secmen", "oyKullanan", "muteber")},
                      "oy": il["oy"], "Bağımsız": il["Bağımsız"],
                      "dogrulanamayanAlanlar": sorted(set(il.get("dogrulanamayanAlanlar", []))),
                      "kaynak": {"ana": "tuik", "sayfa": il["sayfa"], "adKaynakta": il["adKaynakta"],
                                 **({"plakaNotu": not_} if not_ else {}),
                                 **({"kaynakIciTutarsizlik": il["tutarsiz"]} if il.get("tutarsiz") else {})},
                      "ilceler": ilceler})
    return {"kaynak": {"ana": "tuik", "yayin": d["yayin"], "yayinUrl": d["yayinUrl"], "pdfSha256": d["pdfSha256"],
                       "sayfalar": d["sayfalar"], "metinKlasoru": d["metinKlasoru"],
                       "kaynakKatmani": str(dosya.relative_to(ROOT))},
            "dogrulama": {"wikipediaIlSonuclariyla": d.get("wikipediaIlKarsilastirmasi"),
                          "ilceToplamiIlToplamiTutmayan": d["ilceToplamiTutmayan"], "ozet": d["ozet"],
                          "not": "dogrulanamayanAlanlar: ilçe toplamı il toplamını tutmayan alanlar (OCR ya da kaynak hatası)."},
            "iller": iller}


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
        tuik = tuik_ilce_oylari(secim, TUIK_SENATO / f"{secim}.json")
        yaz("senato", secim, {"secim": secim, "tur": "senato", "kaynak": "wikipedia" + (" + tuik (ilçe oyları)" if tuik else ""),
                              **({"ilceOylariTuik": tuik} if tuik else {}),
                              "aciklama": "Cumhuriyet Senatosu uye secimi (1961 Anayasasi; uyelerin ucte biri 2 yilda bir yenilenirdi, 1980'de kaldirildi).",
                              "kapsam": {"senator": dict(kapsam(len(s), beklenen), ayiklananTekrar=tekrar),
                                         "ilSayisi": len(iller), "ilceBirincisi": len(ilce)},
                              "iller": iller, "ilceBirincileri": ilce, "secilenler": s})
        ozet["senato"][secim] = f"{len(iller)} il, {len(ilce)} ilce, {len(s)}/{beklenen} senator" + (
            f", TUIK ilce oyu {sum(len(i['ilceler']) for i in tuik['iller'])}" if tuik else "")
    ara = tuik_ilce_oylari("1966ara", TUIK_GENEL / "1966ara.json")
    if ara:
        yaz("yenileme_ara", "1966mv_ara_hatay", {"secim": "1966mv_ara_hatay", "tur": "yenileme_ara",
            "aciklama": "5 Haziran 1966 milletvekili ara seçimi (Hatay), senato seçimiyle aynı gün",
            **ara})
        ozet["yenileme_ara"]["1966mv_ara_hatay"] = f"{sum(len(i['ilceler']) for i in ara['iller'])} ilce"
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
