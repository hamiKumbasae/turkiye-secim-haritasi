"""
5747 sayili Kanun (22.03.2008, RG 26824 mukerrer: buyuksehirlerde 43 ilce) -> kaynak katmani.

Onceki kanunlardan farki: ek listeler birimleri eski ILCEYE gore degil, bagli olduklari
BELEDIYEYE gore gruplar ("Taşoluk İlk Kademe Belediyesine bağlı"); yalniz koy
cetvellerinde ILCESI sutunu var. Madde 1 bentleri ayrica tuzel kisiligi kaldirilip
yeni ilceye katilan ilk kademe belediyelerini sayar (Aksu, Pinarli, Yurtpinar ->
Calkaya = Aksu ilcesi).

Belediyenin ilcesi: DIE, Mahalli Idareler Secimi 28.03.2004 (0018169) Tablo 9
belediye baskanligi (data/kaynaklar/tuik/yerel/2004yerel/belediye_baskanligi.json,
`ustIlce`). Tabloda il satirinin hemen altinda, ilk ilce satirindan once gelen beldelerin
`ustIlce`'si bos: bunlar il merkez ilcesinin beldeleri ("Merkez"). 2004 ile 2008 arasinda
ilce degistiren belde varsa bu okuma onu gormez (kanunda yazmiyor; bilinen yok).

Metin: mevzuat.gov.tr (data/raw/mevzuat/5747.pdf, dogal metin; 6552 ile 2014'te
degisen satirlar dipnotlu). Resmi Gazete asil metni (data/raw/resmi_gazete/26824_1.htm)
ile her listenin kaynak basliklari ve koy ilceleri karsilastirilir (fark -> rapor).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_5747.py
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

MEVZUAT = "data/raw/mevzuat/5747.pdf"
RG = "data/raw/resmi_gazete/26824_1.htm"
DIE = "data/kaynaklar/tuik/yerel/2004yerel/belediye_baskanligi.json"
OUT = ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus/5747.json"
ONCEKI, SONRAKI = "2007", "2011"
IL_PLAKA = {"Adana": 1, "Ankara": 6, "Antalya": 7, "Diyarbakır": 21, "Erzurum": 25, "Eskişehir": 26,
            "Mersin": 33, "İstanbul": 34, "İzmir": 35, "Kocaeli": 41, "Sakarya": 54, "Samsun": 55}
# DIE 2004'te belde satiri olmayan ilk kademe belediyeleri: il merkezinin kendisi
# (Sakarya il merkezi Adapazari = Merkez ilce; 5747/1-37 "Adapazarı İlk Kademe Belediyesi")
BELEDIYE_ELLE = {(54, "Adapazarı"): ("Merkez", "Sakarya il merkezi; Merkez ilçenin belediyesi (DİE 2004'te il satırı)")}
# DIE 2004 kitabindaki okunusu kanundakinden farkli beldeler (ayni ilde tek aday)
DIE_AD = {(34, "Alemdağ"): "Alemdar", (34, "Çekmeköy"): "Çekme", (25, "Kazım Karabekir"): "Kazımkarabekir",
          (25, "Dadaşköy"): "Dadaşköy (1)"}
# Madde 1/3: Pursaklar icin ek liste yok; birimler bent metninden
PURSAKLAR = [("Pursaklar", "belediye"), ("Sarayköy", "belediye"), ("Sirkeli", "belediye"),
             ("Altınova (Yıldırım Beyazıt ve Peçenek mahalleleri)", "mahalle")]


T = "2008-03-22"
DIGER = [
    {"madde": "2/2", "eventType": "abolished", "effectiveDate": T, "unit": "Eminönü",
     "metin": "İstanbul İlinde Eminönü İlçesi kaldırılmıştır. Eminönü Belediyesinin tüzel kişiliği kaldırılarak "
              "mahalleleriyle birlikte Fatih Belediyesine katılmıştır."},
    {"madde": "2/3", "eventType": "boundary_adjustment", "effectiveDate": T, "unit": "Kadıköy/Ümraniye/Esenler/Başakşehir/Bağcılar",
     "metin": "Kadıköy'e bağlı Atatürk ve Barbaros mahallelerinin E-80 ile O4 karayolunun kuzeyinde kalan kısımları "
              "Ümraniye'ye; Esenler'e bağlı askerî alanın ... Proje Yolunun kuzeyinde kalan kısmı Başakşehir'e, güneyinde "
              "kalan kısmı Bağcılar'a katılmıştır (6552 ile 2014'te 've Barbaros Mahallesinin' eklendi)."},
    {"madde": "2/4", "eventType": "boundary_adjustment", "effectiveDate": T, "unit": "Büyükçekmece/Ümraniye/Pendik/Avcılar",
     "metin": "Gürpınar'a bağlı Pınartepe ve Kıraç'a bağlı Çakmaklı mahallesinin TEM-D100 bağlantı yolunun batısı "
              "Büyükçekmece'ye; Çekmeköy'e bağlı Mehmet Akif Ersoy mahallesinin Ümraniye-Şile yolunun güneyi Ümraniye'ye; "
              "Ömerli'ye bağlı Merkez mahallesinin yarımadadaki tepeleri Pendik'e bağlı Kurtdoğmuş köyüne; Bahçeşehir 1. "
              "Kısım mahallesinin bir kısmı Avcılar'a katılmıştır."},
    {"madde": "2/5", "eventType": "renamed", "effectiveDate": T, "unit": "Ilıca", "unitAfter": "Aziziye",
     "metin": "Erzurum İlinde Dadaşkent İlk Kademe Belediyesi Ilıca Belediyesine katılmış ve Ilıca İlçesinin adı Aziziye "
              "olarak değiştirilmiştir. Merkez İlçeye bağlı Dereboğazı ve Yukarıyenice köyleri Aziziye İlçesine bağlanmıştır."},
    {"madde": "2/6", "eventType": "boundary_adjustment", "effectiveDate": T, "unit": "Bala/Gölbaşı/Çankaya",
     "metin": "Ankara İlinde Bala İlçesine bağlı Karaali İlk Kademe Belediyesinin Merkez ve Yazlık mahalleleri Gölbaşı "
              "Belediyesine; Tohumlar, Karahasanlı, Kömürcü, Evciler, Çavuşlu, Yayla ve Akarlar mahalleleri Çankaya "
              "Belediyesine; Ahmetçayırı ve Yöreli mahalleleri Bala Belediyesine katılmıştır."},
]


def mevzuat_sayfalar():
    with pdfplumber.open(ROOT / MEVZUAT) as pdf:
        return [pg.extract_text() or "" for pg in pdf.pages]


def rg_satirlar():
    s = (ROOT / RG).read_bytes().decode("windows-1254")
    s = re.sub(r"(?is)<(style|script|xml)[^>]*>.*?</\1>", "", s)
    s = re.sub(r"(?i)<br[^>]*>|</p>|</tr>|</h\d>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    return [x for x in (re.sub(r"\s+", " ", ln).strip() for ln in s.split("\n")) if x]


def bentler(metin):
    """Madde 1 bentleri: no -> {il, ad, liste, belediyeler, metin}."""
    m1 = metin[metin.index("MADDE 1"):metin.index("adlarıyla kırküç ilçe kurulmuştur")]
    parcalar = re.split(r"\n(?=\d{1,2}\. )", m1)
    out = {}
    for p in parcalar[1:]:
        no = int(p.split(".")[0])
        duz = re.sub(r"\s+", " ", p[len(str(no)) + 1:]).strip().rstrip(",")
        il, ad = re.search(r"üzere (\S+) İlinde (.+)$", duz).groups()
        liste = re.search(r"ekli \((\d+)\) sayılı liste", duz, re.I)
        bel = []
        # 'A, B ve C ilk kademe belediyelerinin' / 'X İlk Kademe Belediyesi(ne|nin)'
        for grup in re.findall(r"((?:[A-ZÇĞİÖŞÜ][\wçğıöşü]*(?: [A-ZÇĞİÖŞÜ][\wçğıöşü]*)?, )*"
                               r"[A-ZÇĞİÖŞÜ][\wçğıöşü]*(?: [A-ZÇĞİÖŞÜ][\wçğıöşü]*)?"
                               r"(?: ve [A-ZÇĞİÖŞÜ][\wçğıöşü]*(?: [A-ZÇĞİÖŞÜ][\wçğıöşü]*)?)?) "
                               r"(?:ilk kademe belediyeleri|İlk Kademe Belediyesi)", duz):
            for x in re.split(r", | ve ", grup):
                if x not in bel:
                    bel.append(x)
        # 'Palandöken Belediyesi ve', 'Karşıyaka Belediyesi ile' (ilk kademe demeden)
        for x in re.findall(r"([A-ZÇĞİÖŞÜ][\wçğıöşü]+) Belediyesi(?: ve| ile| merkez)", duz):
            if x not in bel and x != "Kademe":
                bel.append(x)
        out[no] = {"bent": no, "il": il, "ad": ad, "liste": int(liste.group(1)) if liste else None,
                   "belediyeler": bel, "metin": duz}
    return out


DIPNOT = re.compile(r"^\d \d{1,2}/\d{1,2}/\d{4} tarihli")
GRUP = re.compile(r"^(?:(\d+) )?(.+?) (İlçe|İlk Kademe|ilk kademe) [Bb]elediyesine bağlı,?\s*(.*)$")


def listeler(sayfalar):
    """(N) sayili liste -> {no, sayfalar, altBasliklar, satirlar[{sira, birim, tur, grup, grupTuru, koyIlce, koyBucak}]}"""
    out, cur, bolum, grup = {}, None, None, None
    for sn, sayfa in enumerate(sayfalar, 1):
        for ln in sayfa.split("\n"):
            ln = ln.strip()
            if DIPNOT.match(ln):
                break  # sayfa sonu dipnotlari (6552 degisiklik kayitlari)
            m = re.match(r"^\((\d+)\) SAYILI L[İI]STE", ln)
            if m:
                n = int(m.group(1))
                cur = out.setdefault(n, {"no": n, "sayfalar": set(), "altBasliklar": [], "satirlar": []}) if n <= 41 else None
                bolum = grup = None
                continue
            if cur is None or not ln:
                continue
            cur["sayfalar"].add(sn)
            if "BAĞLANAN" in ln:
                cur["altBasliklar"].append(ln)
                bolum = "koy" if re.search(r"BAĞLANAN (BELEDİYE VE )?KÖY", ln) else "mahalle"
                grup = None
                continue
            if ln.startswith("NO BİRİMİN ADI"):
                continue
            g = GRUP.match(ln)
            if g and bolum == "mahalle":
                grup = (g.group(2).strip(), "ilce" if g.group(3) == "İlçe" else "ilk_kademe")
                if g.group(4):
                    cur["satirlar"].append({"sira": int(g.group(1)) if g.group(1) else None, "birim": g.group(4).rstrip(","),
                                            "tur": "mahalle", "grup": grup})
                continue
            r = re.match(r"^(\d+) (.+)$", ln)
            if bolum == "koy" and r:
                w = r.group(2).split()
                not_ilce = re.match(r"^\((\S+) [İi]lçesi", r.group(2))
                if not_ilce:
                    # '(Küçükçekmece İlçesi Şamlar Köyünün ... kısmı ...)': koy kismi, ilcesi notta
                    cur["satirlar"].append({"sira": int(r.group(1)), "birim": r.group(2), "tur": "koy_kismi",
                                            "koyIlce": not_ilce.group(1), "koyBucak": None, "ilceNottan": True})
                elif len(w) >= 2 and w[-2].startswith("(") and w[-2].endswith(")"):
                    # bucak sutunu bos: 'Lütfiye (Aşağıkalabak) Merkez'
                    cur["satirlar"].append({"sira": int(r.group(1)), "birim": " ".join(w[:-1]), "tur": "koy",
                                            "koyIlce": w[-1], "koyBucak": None})
                elif len(w) >= 3:
                    birim = " ".join(w[:-2])
                    tur = "belediye" if birim.endswith(" B.") else "koy"
                    cur["satirlar"].append({"sira": int(r.group(1)), "birim": birim.removesuffix(" B."), "tur": tur,
                                            "koyIlce": w[-2], "koyBucak": w[-1]})
                else:
                    cur["satirlar"].append({"sira": int(r.group(1)), "birim": r.group(2), "tur": "koy", "okunamadi": True})
            elif bolum == "mahalle" and r and grup:
                cur["satirlar"].append({"sira": int(r.group(1)), "birim": r.group(2).rstrip(","), "tur": "mahalle", "grup": grup})
            elif cur["satirlar"]:
                cur["satirlar"][-1]["birim"] += " " + ln  # sarkan satir
                if cur["satirlar"][-1].get("ilceNottan") is not None or cur["satirlar"][-1]["tur"] == "koy_kismi":
                    pass
    return out


def rg_koy_satiri_var(rg_seg, r):
    """mevzuat koy satiri RG asil metninde ayni sira/ad/ilce/bucak ile geciyor mu"""
    if r.get("ilceNottan"):
        return fold(r["koyIlce"]) in fold(rg_seg)
    duz = re.sub(r"[|\s]+", " ", rg_seg).replace("–", "-").replace("\u2011", "-")
    parca = [str(r["sira"]), r["birim"] + (" B." if r["tur"] == "belediye" else ""), r["koyIlce"]] + \
        ([r["koyBucak"]] if r["koyBucak"] else [])
    return re.search(r"(?<![\d])" + r"\s+".join(re.escape(x) for x in " ".join(parca).split()) + r"(?![\wçğıöşü])", duz) is not None


def rg_kontrol(rg, ilce_adlari):
    """RG asil metninde her listenin grup basliklari ve koy ILCESI sutunundaki ilce adlari (sayim)."""
    metin = "|".join(rg)
    out = {}
    for m in re.finditer(r"\((\d+)\) SAYILI\|L[İI]STE(.*?)(?=\(\d+\) SAYILI\|L[İI]STE|$)", metin, re.S):
        n = int(m.group(1))
        if n > 41:
            continue
        seg = m.group(2)
        gruplar = [g.strip() for g in re.findall(r"\|([^|]+?) (?:İlçe|İlk Kademe|ilk kademe) [Bb]elediyesine bağlı", seg)]
        koy = collections.Counter()
        for k in re.split(r"BAĞLANAN KÖY", seg)[1:]:
            for w in re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", k):
                if w in ilce_adlari:
                    koy[w] += 1
        out[n] = {"gruplar": gruplar, "koyIlce": koy, "seg": seg}
    return out


def main():
    sayfalar = mevzuat_sayfalar()
    metin = "\n".join(sayfalar)
    bent = bentler(metin)
    ls = listeler(sayfalar)
    die = json.loads((ROOT / DIE).read_text(encoding="utf-8"))
    belde = {}
    for r in die["satirlar"]:
        if r["tip"] == "belde":
            belde.setdefault((r["plaka"], fold(r["adKaynakta"])), []).append((r["ustIlce"] or "Merkez", r["sayfa"]))
    onceki = collections.defaultdict(dict)
    for r in load_election(ONCEKI)["ilceler"]:
        onceki[r["plaka"]][r["ad"]] = r.get("geomId")
    sonraki = collections.defaultdict(dict)
    for r in load_election(SONRAKI)["ilceler"]:
        sonraki[r["plaka"]][r["ad"]] = r.get("geomId")
    tum_adlar = {a for d in onceki.values() for a in d} | {"Merkez"}
    rg = rg_kontrol(rg_satirlar(), tum_adlar)

    def ilce_coz(pl, ad):
        """eski ilce adi (2007 satiri) -> (ad, geomId) ya da (None, None)"""
        for a, g in onceki[pl].items():
            if fold(a) == fold(ad):
                return a, g
        # dizgi hatasi ('Yüreği'): ayni ilde tek yakin aday
        yakin = [(a, g) for a, g in list(onceki[pl].items()) + [("Merkez", None)]
                 if difflib.SequenceMatcher(None, fold(a), fold(ad)).ratio() >= 0.9]
        return yakin[0] if len(yakin) == 1 else (None, None)

    def belediye_ilcesi(pl, ad):
        if (pl, ad) in BELEDIYE_ELLE:
            return BELEDIYE_ELLE[(pl, ad)][0], {"kaynak": "elle", "not": BELEDIYE_ELLE[(pl, ad)][1]}
        x = belde.get((pl, fold(DIE_AD.get((pl, ad), ad))), [])
        if len(x) == 1:
            return x[0][0], {"kaynak": "DİE 2004 Tablo 9", "sayfa": x[0][1],
                             **({"dieAdi": DIE_AD[(pl, ad)]} if (pl, ad) in DIE_AD else {})}
        return None, {"kaynak": "DİE 2004 Tablo 9", "sorun": "bulunamadı" if not x else "birden çok"}

    sonuc, rapor = [], collections.defaultdict(list)
    for no, b in bent.items():
        pl = IL_PLAKA[b["il"]]
        satirlar = []
        # bentte adi gecen (tuzel kisiligi kaldirilip katilan ya da merkez olan) belediyeler
        for ad in b["belediyeler"]:
            il_, kay = belediye_ilcesi(pl, ad)
            satirlar.append({"sira": None, "birim": ad, "tur": "belediye", "kaynakYeri": f"Madde 1/{no}",
                             "eskiBelediye": ad, "eskiIlceOkunan": il_, "belediyeIlcesiKaynagi": kay})
        if no == 3:
            for ad, tur in PURSAKLAR[3:]:
                il_, kay = belediye_ilcesi(pl, "Altınova")
                satirlar.append({"sira": None, "birim": ad, "tur": tur, "kaynakYeri": "Madde 1/3", "eskiBelediye": "Altınova",
                                 "eskiIlceOkunan": il_, "belediyeIlcesiKaynagi": kay})
        L = ls.get(b["liste"]) if b["liste"] else None
        for r in (L or {}).get("satirlar", []):
            r = dict(r, kaynakYeri=f"({b['liste']}) sayılı liste")
            if "koyIlce" in r:
                r["eskiIlceOkunan"] = r.pop("koyIlce")
                r["eskiBucak"] = r.pop("koyBucak")
            elif r.get("grup"):
                gad, gtur = r.pop("grup")
                r["eskiBelediye"] = f"{gad} {'İlçe' if gtur == 'ilce' else 'İlk Kademe'} Belediyesi"
                if gtur == "ilce":
                    r["eskiIlceOkunan"] = gad
                else:
                    r["eskiIlceOkunan"], r["belediyeIlcesiKaynagi"] = belediye_ilcesi(pl, gad)
            satirlar.append(r)
        for r in satirlar:
            a, g = ilce_coz(pl, r["eskiIlceOkunan"]) if r.get("eskiIlceOkunan") else (None, None)
            r["eskiIlce"], r["eskiIlceGeomId"] = a, g
            if a is None:
                rapor["cozulemeyen"].append({"bent": no, "ilce": b["ad"], **r})
        say = collections.Counter(r["eskiIlce"] for r in satirlar)
        geo = {r["eskiIlce"]: r["eskiIlceGeomId"] for r in satirlar}
        eski = [{"ad": a, "geomId": geo[a], "plaka": pl if a else None, "birimSayisi": c} for a, c in say.most_common()]
        # RG asil metni ile karsilastirma
        fark = None
        if L:
            m_gruplar = []
            for r in satirlar:
                if r["kaynakYeri"].startswith("(") and r.get("eskiBelediye"):
                    x = re.sub(r" (İlçe|İlk Kademe) Belediyesi$", "", r["eskiBelediye"])
                    if not m_gruplar or m_gruplar[-1] != x:
                        m_gruplar.append(x)
            rgx = rg.get(b["liste"], {"gruplar": [], "seg": ""})
            rg_yok = [f"{r['sira']} {r['birim']}" for r in L["satirlar"] if "koyIlce" in r and not rg_koy_satiri_var(rgx["seg"], r)]
            if [fold(x) for x in m_gruplar] != [fold(x) for x in rgx["gruplar"]] or rg_yok:
                fark = {"mevzuatGruplar": m_gruplar, "rgGruplar": rgx["gruplar"], "rgdeBulunmayanKoySatiri": rg_yok}
                rapor["rgFarki"].append({"liste": b["liste"], "ilce": b["ad"], **fark})
        yeni = next(((a, g) for a, g in sonraki[pl].items() if fold(a) == fold(b["ad"])), None)
        cozulen = [e for e in eski if e["ad"]]
        sonuc.append({
            "listeNo": b["liste"], "il": b["il"], "plaka": pl, "ad": b["ad"],
            "yeniIlce": {"ad": yeni[0], "geomId": yeni[1], "plaka": pl, "secim": SONRAKI} if yeni else None,
            "madde": f"5747 Madde 1/{no}: {b['metin']}", "ekHukum": None,
            "rgSayfalari": sorted(L["sayfalar"]) if L else [], "altBasliklar": L["altBasliklar"] if L else [],
            "satirSayisi": len(satirlar), "eskiIlceler": eski,
            "tekKaynak": len(cozulen) == 1 and len(eski) == 1,
            "eksikSira": [], "cozulemeyenSatir": sum(1 for r in satirlar if r["eskiIlce"] is None),
            "kaynakYazilmamisSatir": 0,
            **({"rgFarki": fark} if fark else {}),
            "satirlar": satirlar,
        })
        if not yeni:
            rapor["geomIdsizYeniIlce"].append(b["ad"])
    veri = {
        "kanun": "5747", "ad": "Büyükşehir Belediyesi Sınırları İçerisinde İlçe Kurulması ve Bazı Kanunlarda Değişiklik "
                                "Yapılması Hakkında Kanun",
        "kabul": "2008-03-06", "resmiGazete": {"tarih": "2008-03-22", "sayi": 26824, "mukerrer": 1},
        "kaynaklar": {"ekListeler": RG, "maddeler": MEVZUAT, "belediyeIlceleri": DIE,
                      "rgUrl": "https://www.resmigazete.gov.tr/eskiler/2008/03/20080322M1-1.htm",
                      "mevzuatUrl": "https://www.mevzuat.gov.tr/MevzuatMetin/1.5.5747.pdf"},
        "digerHukumler": DIGER,
        "guvenilirlik": "A (birincil/resmî, doğal metin); satırlar mevzuat metninden, her listenin belediye başlıkları ve "
                        "köy satırları Resmî Gazete aslıyla karşılaştırıldı (rgFarki). İlk kademe belediyesinin ilçesi "
                        "DİE 2004 Tablo 9'dan (kanunda yazmıyor).",
        "yontem": "Birim kaynağı: köy cetvelinde İLÇESİ sütunu; mahalle listesinde grup başlığı ('X İlçe Belediyesine "
                  "bağlı' = X ilçesi; 'X İlk Kademe Belediyesine bağlı' = X beldesinin 2004 ilçesi); Madde 1 bendinde "
                  "tüzel kişiliği kaldırılıp katılan / merkez olan belediyeler (tur=belediye, aynı yöntemle). DİE "
                  "tablosunda il satırının altında ilk ilçe satırından önce gelen beldeler il merkez ilçesinin "
                  "(Merkez) beldeleridir.",
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
        print(f"{x['plaka']:>2} {x['ad']:<12} tek={x['tekKaynak']!s:<5} " +
              ", ".join(f"{e['ad']}:{e['birimSayisi']}" for e in x["eskiIlceler"]) + ("  RG-FARK" if x.get("rgFarki") else ""))
    for k, v in rapor.items():
        print("##", k, len(v))
        for y in v[:40]:
            print("  ", {kk: vv for kk, vv in y.items() if kk not in ("belediyeIlcesiKaynagi",)})
    return sonuc, rapor


if __name__ == "__main__":
    main()
