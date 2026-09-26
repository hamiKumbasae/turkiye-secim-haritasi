"""
6360 sayili Kanun (06.12.2012, RG 28489: on dort ilde buyuksehir, 26 ilce) -> kaynak katmani.

Madde 2 fikralari ilce kurar ya da birim nakleder. Kaynak birimler:
  - ek liste koy/belediye cetvelleri: ILCESI sutunu ("Karaağaç Belediyesi İskenderun Merkez");
  - ek liste mahalle gruplari: "X Belediyesine bağlı;" - X il merkezi belediyesi (Antakya,
    Balıkesir...) ise Merkez ilce, ilce belediyesi ise (Çorlu) o ilce;
  - fikra metni: merkez olan belde belediyesi ("Arsuz Belediyesi merkez olmak üzere"),
    metinde sayilan koyler ("Dörtyol ilçesi Yakacık Bucağına bağlı ... köylerinden") ve
    "Merkez ilçe sınırları içerisindeki köyler ile belediyeler" (butun Merkez ilce).
Belde belediyesinin ilcesi: DIE 2004 Tablo 9 (extract_5747.py ile ayni okuma).

Metin mevzuat.gov.tr (data/raw/mevzuat/6360.pdf; 6447 ile 2013'te Altinordu fikrasi eklendi,
sonraki fikralar teselsul ettirildi - fikra numaralari mevzuat metnine gore). Koy satirlari
Resmi Gazete asil metninde (data/raw/resmi_gazete/28489.htm) sira/ad/ilce/bucak dizisiyle
aranir; bulunmayan satir rgFarki'na yazilir.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_6360.py
"""
import collections
import difflib
import html
import json
import pathlib
import re
import sys

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402

MEVZUAT = "data/raw/mevzuat/6360.pdf"
RG = "data/raw/resmi_gazete/28489.htm"
DIE = "data/kaynaklar/tuik/yerel/2004yerel/belediye_baskanligi.json"
OUT = ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus/6360.json"
# 2011 genel secim verisi kaynakta 2012 sonrasi ilcelere gore yeniden toplanmis;
# kanundan onceki idari birimler icin 2007 genel secim satirlari kullanilir
ONCEKI, SONRAKI = "2007", "2015Haziran"
T = "2012-12-06"
IL_PLAKA = {"Aydın": 9, "Balıkesir": 10, "Denizli": 20, "Hatay": 31, "Malatya": 44, "Manisa": 45,
            "Kahramanmaraş": 46, "Mardin": 47, "Muğla": 48, "Ordu": 52, "Tekirdağ": 59, "Trabzon": 61,
            "Şanlıurfa": 63, "Van": 65, "İstanbul": 34, "Zonguldak": 67, "Ankara": 6}
# il merkezi belediyesi (mahalle gruplari "X Belediyesine bağlı;") -> Merkez ilce
IL_MERKEZI = {9: "Aydın", 10: "Balıkesir", 20: "Denizli", 31: "Antakya", 44: "Malatya", 45: "Manisa",
              46: "Kahramanmaraş", 47: "Mardin", 48: "Muğla", 59: "Tekirdağ", 61: "Trabzon",
              63: "Şanlıurfa", 65: "Van"}


def mevzuat_metni():
    with pdfplumber.open(ROOT / MEVZUAT) as pdf:
        return [pg.extract_text() or "" for pg in pdf.pages]


def rg_duz():
    s = (ROOT / RG).read_bytes().decode("windows-1254")
    s = re.sub(r"(?is)<(style|script|xml)[^>]*>.*?</\1>", "", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s).replace("\xa0", " ")).replace("–", "-")


def fikralar(metin):
    m2 = metin[metin.index("MADDE 2 –"):metin.index("MADDE 3 –")]
    m2 = re.sub(r"\n\d \d{1,2}/\d{1,2}/\d{4} tarihli.*?(?=\n\(\d+\) |\Z)", "", m2, flags=re.S)  # dipnotlar
    m2 = m2.replace("=====PAGE", "")
    out = {}
    for no, govde in re.findall(r"\((\d+)\) (.*?)(?=\n\(\d+\) |\Z)", m2, re.S):
        duz = re.sub(r"\s+", " ", govde).strip()
        duz = re.sub(r"kurulmuştur\.\d$", "kurulmuştur.", duz)
        out[int(no)] = duz
    return out


def ayristir_fikra(no, duz):
    m = re.match(r"(?:\(Ek: [^)]*\) )?(\S+) ilinde", duz)
    il = m.group(1) if m else None
    kur = re.search(r"oluşan (\S+) (?:adıyla ilçe|ilçesi) ve aynı adla belediye kurulmuştur", duz)
    liste = re.search(r"ekli \((\d+)\) sayılı liste", duz)
    merkez_bel = re.search(r"(\S+)(?: Belde)? Belediyesi merkez olmak", duz)
    return {"fikra": no, "il": il, "ad": kur.group(1) if kur else None,
            "liste": int(liste.group(1)) if liste else None,
            "merkezBelediye": merkez_bel.group(1) if merkez_bel else None, "metin": duz,
            "tumMerkez": bool(re.search(r"Merkez ilçe sınırları içerisindeki köyler ile belediyeler", duz)),
            "ek6447": "6447" in duz}


def listeler(sayfalar):
    out, cur, bolum, grup = {}, None, None, None
    for sn, sayfa in enumerate(sayfalar, 1):
        for ln in sayfa.split("\n"):
            ln = ln.strip()
            if re.match(r"^\d \d{1,2}/\d{1,2}/\d{4} tarihli", ln):
                break
            m = re.match(r"^\((\d+)\) SAYILI L[İI]STE", ln)
            if m:
                n = int(m.group(1))
                cur = out.setdefault(n, {"no": n, "sayfalar": set(), "altBasliklar": [], "satirlar": []})
                bolum = grup = None
                continue
            if cur is None or not ln:
                continue
            cur["sayfalar"].add(sn)
            if "BAĞLANAN" in ln:
                cur["altBasliklar"].append(ln)
                bolum = "koy" if re.search(r"BAĞLANAN (BELEDİYE(LER)? VE )?KÖY", ln) else "mahalle"
                grup = None
                continue
            if ln.startswith("S.NO."):
                continue
            g = re.match(r"^(.+?) Belediyesine bağlı;?$", ln)
            if g and bolum == "mahalle":
                grup = g.group(1)
                continue
            r = re.match(r"^(\d+) (.+)$", ln)
            if bolum == "koy" and r:
                cur["satirlar"].append({"sira": int(r.group(1)), "ham": r.group(2), "tur": "koy"})
            elif bolum == "mahalle" and r and grup:
                cur["satirlar"].append({"sira": int(r.group(1)), "birim": r.group(2), "tur": "mahalle", "grup": grup})
            elif cur["satirlar"]:
                k = "ham" if "ham" in cur["satirlar"][-1] else "birim"
                cur["satirlar"][-1][k] += " " + ln
    return out


def main():
    sayfalar = mevzuat_metni()
    metin = "\n".join(sayfalar)
    fk = {n: ayristir_fikra(n, d) for n, d in fikralar(metin).items()}
    ls = listeler(sayfalar)
    rg = rg_duz()
    die = json.loads((ROOT / DIE).read_text(encoding="utf-8"))
    belde = collections.defaultdict(list)
    for r in die["satirlar"]:
        if r["tip"] == "belde":
            belde[(r["plaka"], fold(r["adKaynakta"]))].append((r["ustIlce"] or "Merkez", r["sayfa"]))
    onceki = collections.defaultdict(dict)
    for r in load_election(ONCEKI)["ilceler"]:
        onceki[r["plaka"]][r["ad"]] = r.get("geomId")
    sonraki = collections.defaultdict(dict)
    for r in load_election(SONRAKI)["ilceler"]:
        sonraki[r["plaka"]][r["ad"]] = r.get("geomId")

    def ilce_coz(pl, ad):
        if not ad:
            return None, None
        for a, g in onceki[pl].items():
            if fold(a) == fold(ad):
                return a, g
        yakin = [(a, g) for a, g in onceki[pl].items() if difflib.SequenceMatcher(None, fold(a), fold(ad)).ratio() >= 0.9]
        return yakin[0] if len(yakin) == 1 else (None, None)

    def belde_ilcesi(pl, ad):
        x = belde.get((pl, fold(ad)), [])
        if len(x) == 1:
            return x[0][0], {"kaynak": "DİE 2004 Tablo 9", "sayfa": x[0][1]}
        return None, {"kaynak": "DİE 2004 Tablo 9", "sorun": "bulunamadı" if not x else "birden çok"}

    def koy_satiri(pl, r):
        w = r["ham"].split()
        bel = "Belediyesi" in w
        for k in (2, 3):  # bucak bir ya da iki kelime
            if len(w) > k and ilce_coz(pl, w[-k])[0] or (len(w) > k and w[-k] == "Merkez"):
                birim = " ".join(x for x in w[:-k] if x != "Belediyesi")
                return {"sira": r["sira"], "birim": birim, "tur": "belediye" if bel else "koy",
                        "eskiIlceOkunan": w[-k], "eskiBucak": " ".join(w[-k + 1:])}
        return {"sira": r["sira"], "birim": r["ham"], "tur": "koy", "eskiIlceOkunan": None, "okunamadi": True}

    def rgde_var(r):
        parca = [str(r["sira"]), r["birim"]] + (["Belediyesi"] if r["tur"] == "belediye" else []) + \
            [r["eskiIlceOkunan"], r["eskiBucak"]]
        return re.search(r"(?<!\d)" + r"\s+".join(re.escape(x) for x in " ".join(parca).split()) + r"(?![\wçğıöşü])", rg) is not None

    sonuc, diger, rapor = [], [], collections.defaultdict(list)
    for no, f in sorted(fk.items()):
        pl = IL_PLAKA.get(f["il"])
        if not f["ad"]:
            diger.append({"madde": f"2/{no}", "eventType": "renamed" if "ismi ise" in f["metin"] else "boundary_adjustment",
                          "effectiveDate": T, "unit": f["il"], "metin": f["metin"],
                          **({"liste": f["liste"]} if f["liste"] else {})})
            continue
        if f["ek6447"]:
            rapor["atlanan"].append({"fikra": no, "ad": f["ad"], "neden": "6447 (2013) ile eklendi; o kanunla işlenir"})
            continue
        satirlar = []
        if f["merkezBelediye"]:
            il_, kay = belde_ilcesi(pl, f["merkezBelediye"])
            satirlar.append({"sira": None, "birim": f["merkezBelediye"], "tur": "belediye", "kaynakYeri": f"Madde 2/{no}",
                             "eskiIlceOkunan": il_, "belediyeIlcesiKaynagi": kay})
        if f["tumMerkez"]:
            satirlar.append({"sira": None, "birim": "Merkez ilçe sınırları içerisindeki köyler ile belediyeler",
                             "tur": "ilce_butunu", "kaynakYeri": f"Madde 2/{no}", "eskiIlceOkunan": "Merkez"})
        for ilce, bucak, koyler in re.findall(r"(\S+) ilçesi (\S+) Bucağına bağlı (.+?) köylerinden", f["metin"]):
            for k in re.split(r", | ve ", koyler):
                satirlar.append({"sira": None, "birim": k, "tur": "koy", "kaynakYeri": f"Madde 2/{no}",
                                 "eskiIlceOkunan": ilce, "eskiBucak": bucak})
        for ilce, bucak in re.findall(r"(Merkez) ilçe (\S+) bucağına bağlı belediye", f["metin"]):
            satirlar.append({"sira": None, "birim": f"{bucak} bucağına bağlı belediye(ler) ve köyler", "tur": "bucak_butunu",
                             "kaynakYeri": f"Madde 2/{no}", "eskiIlceOkunan": ilce, "eskiBucak": bucak})
        L = ls.get(f["liste"]) if f["liste"] else None
        rg_yok = []
        for r in (L or {}).get("satirlar", []):
            if r["tur"] == "koy":
                r = koy_satiri(pl, r)
                if not r.get("okunamadi") and not rgde_var(r):
                    rg_yok.append(f"{r['sira']} {r['birim']}")
            else:
                g = r.pop("grup")
                r["eskiBelediye"] = f"{g} Belediyesi"
                if ilce_coz(pl, g)[0]:
                    r["eskiIlceOkunan"] = g
                elif fold(g) == fold(IL_MERKEZI.get(pl, "")):
                    r["eskiIlceOkunan"], r["belediyeIlcesiKaynagi"] = "Merkez", {"kaynak": "il merkezi belediyesi"}
                else:
                    r["eskiIlceOkunan"] = None
            r["kaynakYeri"] = f"({f['liste']}) sayılı liste"
            satirlar.append(r)
        for r in satirlar:
            r["eskiIlce"], r["eskiIlceGeomId"] = ilce_coz(pl, r.get("eskiIlceOkunan"))
            if r["eskiIlce"] is None:
                rapor["cozulemeyen"].append({"fikra": no, "ilce": f["ad"], **r})
        say = collections.Counter(r["eskiIlce"] for r in satirlar)
        geo = {r["eskiIlce"]: r["eskiIlceGeomId"] for r in satirlar}
        eski = [{"ad": a, "geomId": geo[a], "plaka": pl if a else None, "birimSayisi": c} for a, c in say.most_common()]
        yeni = next(((a, g) for a, g in sonraki[pl].items() if fold(a) == fold(f["ad"])), None)
        fark = {"rgdeBulunmayanKoySatiri": rg_yok} if rg_yok else None
        if fark:
            rapor["rgFarki"].append({"liste": f["liste"], "ilce": f["ad"], **fark})
        sonuc.append({
            "listeNo": f["liste"], "il": f["il"], "plaka": pl, "ad": f["ad"],
            "yeniIlce": {"ad": yeni[0], "geomId": yeni[1], "plaka": pl, "secim": SONRAKI} if yeni else None,
            "madde": f"6360 Madde 2/{no}: {f['metin']}", "ekHukum": None,
            "rgSayfalari": sorted(L["sayfalar"]) if L else [], "altBasliklar": L["altBasliklar"] if L else [],
            "satirSayisi": len(satirlar), "eskiIlceler": eski,
            "tekKaynak": len(eski) == 1 and eski[0]["ad"] is not None,
            "eksikSira": [], "cozulemeyenSatir": sum(1 for r in satirlar if r["eskiIlce"] is None),
            "kaynakYazilmamisSatir": 0, **({"rgFarki": fark} if fark else {}), "satirlar": satirlar,
        })
        if not yeni:
            rapor["geomIdsizYeniIlce"].append(f["ad"])
    veri = {
        "kanun": "6360", "ad": "On Dört İlde Büyükşehir Belediyesi ve Yirmi Yedi İlçe Kurulması ile Bazı Kanun ve Kanun "
                                "Hükmünde Kararnamelerde Değişiklik Yapılmasına Dair Kanun",
        "kabul": "2012-11-12", "resmiGazete": {"tarih": T, "sayi": 28489},
        "kaynaklar": {"ekListeler": RG, "maddeler": MEVZUAT, "belediyeIlceleri": DIE,
                      "rgUrl": "https://www.resmigazete.gov.tr/eskiler/2012/12/20121206-1.htm",
                      "mevzuatUrl": "https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6360.pdf"},
        "digerHukumler": diger,
        "guvenilirlik": "A (birincil/resmî, doğal metin); köy/belediye satırlarının ilçesi cetvelde yazılı ve Resmî "
                        "Gazete aslında aranarak doğrulandı (rgFarki). Merkez olan belde belediyesinin ilçesi DİE 2004 "
                        "Tablo 9'dan (kanunda yazmıyor).",
        "yontem": "Kaynak ilçe: cetvelde İLÇESİ sütunu; 'X Belediyesine bağlı' mahalle grubunda X il merkezi belediyesiyse "
                  "Merkez, ilçe belediyesiyse o ilçe; fıkra metninde merkez olan belde (DİE 2004), sayılan köyler ve "
                  "'Merkez ilçe sınırları içerisindeki köyler ile belediyeler'. Eski ilçe adları 2007 genel seçim "
                  "satırlarıyla eşlenir (2011 verisi 2012 sonrası ilçelere göre toplanmış).",
        "ozet": {"ilce": len(sonuc), "tekKaynak": sum(1 for x in sonuc if x["tekKaynak"]),
                 "cokKaynak": sum(1 for x in sonuc if len([i for i in x["eskiIlceler"] if i["ad"]]) > 1),
                 "satir": sum(x["satirSayisi"] for x in sonuc),
                 "cozulemeyenSatir": sum(x["cozulemeyenSatir"] for x in sonuc),
                 "kaynakYazilmamisSatir": 0, "satirsizListe": [], "eksikSatirliListe": [],
                 "rgFarkliListe": [x["listeNo"] for x in sonuc if x.get("rgFarki")],
                 "geomIdsizYeniIlce": rapor.get("geomIdsizYeniIlce", [])},
        "ilceler": sonuc,
    }
    OUT.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(veri["ozet"], ensure_ascii=False))
    for x in sonuc:
        print(f"{x['plaka']:>2} {x['ad']:<14} tek={x['tekKaynak']!s:<5} " +
              ", ".join(f"{e['ad']}:{e['birimSayisi']}" for e in x["eskiIlceler"]) + ("  RG-FARK" if x.get("rgFarki") else ""))
    print("digerHukumler:", [(d["madde"], d["eventType"]) for d in diger])
    for k, v in rapor.items():
        print("##", k, len(v))
        for y in v[:25]:
            print("  ", {kk: vv for kk, vv in y.items() if kk != "belediyeIlcesiKaynagi"})


if __name__ == "__main__":
    main()
