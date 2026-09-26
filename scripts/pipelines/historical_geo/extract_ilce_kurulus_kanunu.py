"""
Ilce kurulus kanunlarinin ek listeleri -> kaynak katmani (Faz 2: soy).

Her kanun icin iki birincil kaynak:
  - mevzuat.gov.tr metni (data/raw/mevzuat/<kanun>.pdf): Madde 1'in bentleri;
    "(N) sayili liste" -> hangi ilde hangi ilce kuruldu. Metin temiz.
  - Resmi Gazete asil sayisi (data/raw/resmi_gazete/<sayi>.pdf): ek listeler;
    her satir: birim (koy/kasaba/mahalle), eski ilcesi, eski bucagi. Taranmis,
    OCR'li (gurultulu: 'Akyurl', 'LlSTE', kalin basliklarda cift harf).

Cikti: data/kaynaklar/resmi_gazete/ilce_kurulus/<kanun>.json
  her yeni ilce: il, ad, liste no, satirlar [{birim, tur, eskiIlce, eskiBucak,
  eskiIlceGeomId}], eskiIlceler ozeti, tekKaynak (butun birimler tek ilceden mi).

Eski ilce adi OCR'dan okunur ve o ilin kanundan SONRAKI ilk genel secimindeki
ilce adlariyla (yeni kurulanlar haric) bulanik eslenir; eslenemeyen satir
`eskiIlce: null` ve `okunan` ile kalir (tahmin yok).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_ilce_kurulus_kanunu.py 3644
"""
import collections
import difflib
import json
import pathlib
import re
import sys

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402

KANUNLAR = {
    "3644": {"ad": "130 İlçe Kurulması Hakkında Kanun", "kabul": "1990-05-09",
             "resmiGazete": {"tarih": "1990-05-20", "sayi": 20523}, "rgPdf": "data/raw/resmi_gazete/20523.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3644.pdf", "sonrakiGenel": "1991", "oncekiGenel": "1987",
             "adsizIl": {"Çamoluk": [28, 29], "Doğankent": [28, 29]}},
    "3392": {"ad": "103 İlçe Kurulması Hakkında Kanun", "kabul": "1987-06-19",
             "resmiGazete": {"tarih": "1987-07-04", "sayi": 19507}, "rgPdf": "data/raw/resmi_gazete/19507.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3392.pdf", "sonrakiGenel": "1991", "oncekiGenel": "1987",
             "adsizIl": {},
             # kanundaki ad -> sonraki secimdeki ad; Icisleri 2018 listesi bu ilceleri 3392 ile
             # guncel adlariyla veriyor (DEMRE, CUMAYERİ)
             "sonrakiAd": {"Kale": "Demre", "Cumaova": "Cumayeri"}},
}
OUT = ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus"


def pdf_metin(p):
    with pdfplumber.open(ROOT / p) as pdf:
        return [pg.extract_text() or "" for pg in pdf.pages]


def tekle(s):
    """Kalin puntoda cift yazilmis kelimeler: 'ööpprrüübbaaşşıı' -> 'öprübaşı'."""
    return " ".join(w[0::2] if len(w) >= 4 and len(w) % 2 == 0 and w[0::2] == w[1::2] else w for w in s.split())


def benzer(a, b):
    return difflib.SequenceMatcher(None, fold(a).replace(" ", ""), fold(b).replace(" ", "")).ratio()


def maddeler(metin):
    """Madde 1 bentleri: {liste_no: {il, ad, madde, ekHukum}}. Bentler numaraya gore
    degil 'adıyla,' bitisine gore bolunur (3392'de 94. bent Resmi Gazete'de '4.'
    basilmis). ekHukum: bentte ilce kurmanin yaninda yapilan birim nakli (orn.
    3644/76: Belkaya Kasabasi Karapinar'dan Eregli'ye; 3644/69: Karakecili
    Kirikkale iline) - mevcut ilcelerin tarihsel sinirini da etkiler."""
    t = re.sub(r"\s+", " ", metin)
    bas = t.find("Madde 1")
    son = t.find("Madde 2", bas)
    t = t[bas:son]
    out = {}
    for govde in re.split(r"(?<=adıyla)[,.;]", t):
        # bendin kendi listesi SON referanstir (onune dipnot girebiliyor: 3392/14 oncesinde
        # "ekli (57) sayılı listede yer alan..." dipnotu)
        lms = list(re.finditer(r"[Ee]kli\s*\((\d+)\)\s*[Ss]ayılı listede", govde))
        if not lms:
            continue
        lm = lms[-1]
        on = govde[:lm.start()]
        bent_no = list(re.finditer(r"(?:^|\s)\d+\s*\.\s", on))
        govde = govde[bent_no[-1].end():].strip() if bent_no else re.sub(
            r"^\s*(?:Madde 1\s*[–-]\s*)?", "", govde).strip()
        lm = list(re.finditer(r"[Ee]kli\s*\((\d+)\)\s*[Ss]ayılı listede", govde))[-1]
        ad = re.search(r"([^\s,]+)\s+[İIi]linde\s+(.+?)\s+adıyla$", govde) or re.search(r"()(\S+)\s+adıyla$", govde)
        ilce_il = re.search(r"kurulan İlçe (\S+) İline bağlanmak", govde)
        out[int(lm.group(1))] = {"il": (ad.group(1) if ad else None) or (ilce_il.group(1) if ilce_il else None),
                                 "ad": ad.group(2) if ad else None,
                                 "madde": govde[:900], "ekHukum": govde[:lm.start()].strip(" ,") or None}
    return out


def il_ilce_adlari(secim, plakalar):
    """{plaka: {ad: geomId}} - o secimdeki ilce satirlari."""
    kayit = load_election(secim)
    out = collections.defaultdict(dict)
    for r in kayit["ilceler"]:
        if r["plaka"] in plakalar:
            out[r["plaka"]][r["ad"]] = r.get("geomId")
    return out


def ayristir(kanun):
    cfg = KANUNLAR[kanun]
    bentler = maddeler("\n".join(pdf_metin(cfg["mevzuatPdf"])))
    sayfalar = pdf_metin(cfg["rgPdf"])
    il_adlari = {fold(v["il_ADI"]).replace(" ", ""): int(k)
                 for k, v in json.loads((ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text()).items()}
    il_adlari.update({"AFYON": 3, "ICEL": 33})
    sonraki = il_ilce_adlari(cfg["sonrakiGenel"], set(range(1, 82)))
    # kanundan ONCEKI secimin adlari: kaynak ilce sonradan il olmus olabilir (3392: Bayburt,
    # Bartin); onceki adlar oncelikli
    onceki_secim = il_ilce_adlari(cfg["oncekiGenel"], set(range(1, 82)))
    # bu kanunla kurulan ilceler (il bazinda): kaynak ilce olamazlar
    yeni_adlar = {(il_adlari.get(fold(b["il"] or "").replace(" ", "")), fold(b["ad"])) for b in bentler.values()}

    listeler = collections.defaultdict(lambda: {"satirlar": [], "altBasliklar": [], "sayfalar": set()})
    liste = None
    varsayilan_ilce = None
    onceki = None
    for no, sayfa in enumerate(sayfalar, start=1):
        for satir in sayfa.split("\n"):
            s = tekle(satir.strip())
            m = re.search(r"\((\d+J?)\)?\s*SAY[IİŞ]L[IİŞ]\s*L\S{0,2}STE", s)
            if m:
                liste, varsayilan_ilce = int(m.group(1).replace("J", "3")), None
                listeler[liste]["sayfalar"].add(no)
                continue
            if liste is None:
                continue
            if liste == max(bentler) and re.search(r"YÜRÜTME|YARGI|İLANLAR|Fihrist|FİHRİST|TARİHİ .*SAYISI|DOLARI|DÖVİZ|EFEKTİF", s):
                liste = None   # ek listeler bitti
                break
            if re.search(r"Alınarak|Belediyesinden", s):
                listeler[liste]["altBasliklar"].append(s)
                m = re.search(r"(\S+)\s+İlçe(?:si)?\s+Belediyesinden", s) or re.search(r"İl[iı]\s+(.+?)\s+İlçesi", s)
                varsayilan_ilce = m.group(1) if m else None
                continue
            if re.search(r"İlçesine\s+Ba[gğ]lanan", s):
                # yeni alt blok ('B) İzmir İli Buca İlçesine Bağlanan Köyler'): ilce sutunlu
                listeler[liste]["altBasliklar"].append(s)
                varsayilan_ilce = None
                continue
            m = re.match(r'^["\'`]?([0-9IlJS|)O]{1,3})[-.,]?\s+((?!\d+\.\s)["\'`(—–-]?[0-9A-Za-zÇĞİÖŞÜçğıöşüÂâÎî].*)$', s)
            numara = None
            if m and not re.search(r"Sayfa|RESM|kurulmuştur", s):
                # sira numarasinda OCR: 'I' 'l' 'J' '|' ')' = 1, 'S' = 5, 'O' = 0 ('3)' = 31); tek
                # satirlik hatalar sonra komsu satirlardan duzeltilir
                ham_no = m.group(1).translate(str.maketrans({"I": "1", "l": "1", "J": "1", "|": "1", ")": "1", "S": "5", "O": "0"}))
                if ham_no.isdigit():
                    numara = int(ham_no)
            if numara is not None:
                govde = m.group(2)
                tire = bool(re.match(r"^[—–-]\s*", govde))
                govde = re.sub(r"^[—–-]\s*", "", govde)
                # iki sutunlu mahalle listesi: '1. Adatepe 11. Efeler'
                parca = re.split(r"\s(\d{1,3})\.\s", govde, maxsplit=1)
                satir_listesi = [(numara, parca[0], m.group(1))]
                if len(parca) == 3:
                    satir_listesi.append((int(parca[1]), parca[2], parca[1]))
                for nm, gv, hn in satir_listesi:
                    listeler[liste]["satirlar"].append({"sira": nm, "ham": gv, "hamNo": hn, "tire": tire,
                                                        "varsayilanIlce": varsayilan_ilce, "sayfa": no})
                listeler[liste]["sayfalar"].add(no)
            elif (listeler[liste]["satirlar"] and len(s.split()) <= 3 and len(listeler[liste]["satirlar"][-1]["ham"].split()) <= 2
                  and not re.search(r"Sayfa|RESM|SAYILI|Bağlanan|Birim|Sıra|No\.|Adı", s)):
                # iki satira kaymis satir: '45. Tem renli' / 'Muradiye Çaldıran'
                listeler[liste]["satirlar"][-1]["ham"] += " " + s
                listeler[liste]["satirlar"][-1]["devamSatiri"] = True
            elif listeler[liste]["satirlar"] or re.search(r"Birim Ad|A\s?d\s?ı\s+İlçesi", onceki or ""):
                # numarasi tamamen dusmus satir: sonra ilce/bucak sutunu eslenirse kabul edilir
                if len(s.split()) >= 3 and not re.search(r"Sayfa|RESM|SAYILI|Bağlanan|Birim|Sıra|No\.", s):
                    listeler[liste]["satirlar"].append({"sira": None, "ham": s, "varsayilanIlce": varsayilan_ilce,
                                                        "sayfa": no, "numarasiz": True})
            onceki = s

    sonuc = []
    for n in sorted(bentler):
        b = bentler[n]
        pl = il_adlari.get(fold(b["il"] or "").replace(" ", ""))
        plakalar = [pl] if pl else cfg["adsizIl"].get(b["ad"], [])
        adaylar = {ad: g for kaynak in (sonraki, onceki_secim) for p in plakalar for ad, g in kaynak.get(p, {}).items()
                   if (p, fold(ad)) not in yeni_adlar}
        adaylar_ek = {}
        # il disindan birim alan ilceler (3644/20 Yedisu <- Tunceli/Pulumur): diger illerin
        # adlari yalnizca daha yuksek benzerlik ve tek aday ile kabul edilir
        genel = collections.defaultdict(list)
        for p, adlar in sonraki.items():
            if p in plakalar:
                continue
            for ad, g in adlar.items():
                if fold(ad) != "MERKEZ" and (p, fold(ad)) not in yeni_adlar:
                    genel[ad].append((p, g))
        satirlar = []
        ham_satirlar = []
        for r in listeler.get(n, {}).get("satirlar", []):
            onceki_sira = ham_satirlar[-1]["sira"] if ham_satirlar else 0
            if "S" in (r.get("hamNo") or "") and r["sira"] != onceki_sira + 1:
                # 'S' 5 ya da 8 (6, 3) olabilir: siradaki numarayi veren okuma secilir
                for rakam in "5863":
                    alt = r["hamNo"].replace("S", rakam).translate(str.maketrans({"I": "1", "l": "1", "|": "1", ")": "1", "O": "0"}))
                    if alt.isdigit() and int(alt) == onceki_sira + 1:
                        r = dict(r, sira=int(alt))
                        break
            if r.get("numarasiz"):
                if satir_coz(r, adaylar)["eskiIlce"] is None:
                    continue  # liste satiri degil
                r = dict(r, sira=(ham_satirlar[-1]["sira"] + 1) if ham_satirlar else 1)
            ham_satirlar.append(r)
        # tek satirda bozuk okunan sira: komsulari n-1 ve n+1 ise n
        for i in range(1, len(ham_satirlar) - 1):
            a, b_, c_ = ham_satirlar[i - 1]["sira"], ham_satirlar[i]["sira"], ham_satirlar[i + 1]["sira"]
            if b_ != a + 1 and c_ == a + 2:
                ham_satirlar[i] = dict(ham_satirlar[i], sira=a + 1, siraDuzeltildi=True)
        tire_stili = any(r.get("tire") for r in ham_satirlar)
        for r in ham_satirlar:
            c = satir_coz(r, adaylar)
            if r.get("numarasiz"):
                c["numarasiOkunamadi"] = True
            if r.get("siraDuzeltildi"):
                c["siraDuzeltildi"] = True
            if c["eskiIlce"] is None:
                # OCR bozuk ilce adi ('Ancak' = Arıcak, 'Çat' = Çal): ayni ilde, en iyi aday
                # ikinciden acikca ayrisiyorsa daha dusuk esik
                c = satir_coz(r, adaylar, esik=0.6, fark=0.15)
                if c["eskiIlce"]:
                    c["dusukEsik"] = True
            if c["eskiIlce"] is None and tire_stili and satirlar and satirlar[-1]["eskiIlce"] and len(r["ham"].split()) <= 3:
                # '—' ile gosterilen liste: ilce/bucak sutunu bos = ust satirla ayni
                c = dict(c, birim=r["ham"], eskiIlce=satirlar[-1]["eskiIlce"], eskiBucak=satirlar[-1]["eskiBucak"],
                         ustSatirIleAyni=True)
                if satirlar[-1].get("ilDisi"):
                    c["ilDisi"] = satirlar[-1]["ilDisi"]
            if c["eskiIlce"] is None and len(r["ham"].split()) <= 3 and not r.get("varsayilanIlce") and \
                    re.search(r"Mahalle", " ".join(listeler.get(n, {}).get("altBasliklar", []))):
                # mahalle listesinde eski ilce yazilmamis (3392/49 Kucukcekmece): tahmin yok
                c = dict(c, birim=r["ham"], tur="mahalle", kaynakYazilmamis=True)
                satirlar.append(c)
                continue
            if c["eskiIlce"] is None:
                d = satir_coz(r, {a: v[0][1] for a, v in genel.items() if len(v) == 1}, esik=0.9)
                if d["eskiIlce"]:
                    d["ilDisi"] = genel[d["eskiIlce"]][0][0]
                    adaylar_ek[d["eskiIlce"]] = genel[d["eskiIlce"]][0][1]
                    c = d
            satirlar.append(c)
        say = collections.Counter(r["eskiIlce"] for r in satirlar)
        ilce_plaka = {r["eskiIlce"]: r.get("ilDisi", pl) for r in satirlar if r["eskiIlce"]}
        ilceler = [{"ad": a, "geomId": adaylar.get(a) or adaylar_ek.get(a), "birimSayisi": c,
                    **({"plaka": ilce_plaka[a]} if a else {})} for a, c in say.most_common()]
        cozulen = [i for i in ilceler if i["ad"]]
        # sira kontrolu: her alt liste 1'den baslar; iki sutunlu listelerde numaralar
        # karisik gelir (1, 15, 2, 16...), bu yuzden blok icinde kume olarak bakilir
        eksik_sira, blok = [], []
        for x in [r["sira"] for r in satirlar] + [1]:
            if x == 1 and blok:
                eksik_sira += sorted(set(range(1, max(blok) + 1)) - set(blok))
                blok = []
            blok.append(x)
        # yeni ilcenin kendisi: kanundan sonraki ilk genel secimdeki satiri (geomId); ad
        # sonradan degismis olabilir (Yenihisar -> Didim), eslesme o secimin adiyla
        hedef_ad = cfg.get("sonrakiAd", {}).get(b["ad"], b["ad"])

        def ad_benzer(ad):   # 'Didim (Yenihisar)': parantez ici/disi ayri karsilastirilir
            return max(benzer(hedef_ad, x) for x in [re.sub(r"\(.*?\)", "", ad)] + re.findall(r"\((.*?)\)", ad))
        yeni = [(ad_benzer(ad), ad, g, p) for p in plakalar for ad, g in sonraki.get(p, {}).items()]
        yeni = max(yeni, default=None)
        if not yeni or yeni[0] < 0.8:
            # kanundan hemen sonra baska ile gecen ilce (3644/106 Guclukonak: Siirt -> Sirnak)
            tum = [(ad_benzer(ad), ad, g, p) for p, adlar in sonraki.items() for ad, g in adlar.items()]
            iyi = [x for x in tum if x[0] >= 0.9]
            yeni = iyi[0] if len(iyi) == 1 else yeni
        yeni_geom = {"ad": yeni[1], "geomId": yeni[2], "plaka": yeni[3], "secim": cfg["sonrakiGenel"]} \
            if yeni and yeni[0] >= 0.8 else None
        sonuc.append({
            "listeNo": n, "il": b["il"], "plaka": pl, "ad": b["ad"], "yeniIlce": yeni_geom, "madde": b["madde"], "ekHukum": b["ekHukum"],
            "rgSayfalari": sorted(listeler.get(n, {}).get("sayfalar", [])),
            "altBasliklar": listeler.get(n, {}).get("altBasliklar", []),
            "satirSayisi": len(satirlar), "eskiIlceler": ilceler,
            "tekKaynak": len(cozulen) == 1 and not any(i["ad"] is None for i in ilceler),
            # OCR'da dusen satir varsa tek kaynak kesin degil (dusen birim baska ilceden olabilir)
            "eksikSira": eksik_sira,
            "cozulemeyenSatir": sum(1 for r in satirlar if r["eskiIlce"] is None and not r.get("kaynakYazilmamis")),
            "kaynakYazilmamisSatir": sum(1 for r in satirlar if r.get("kaynakYazilmamis")),
            "satirlar": satirlar,
        })
    return cfg, sonuc


def satir_coz(r, adaylar, esik=0.8, fark=0.0):
    """'Arpalı Sürmene Köprübaşı' -> birim, eski ilce, eski bucak. Ilce sutunu
    adaylara bulanik eslenir; en iyi eslesme >= esik ve (fark > 0 ise) ikinci en
    iyi FARKLI adaydan en az `fark` kadar yuksekse kabul."""
    tok = r["ham"].replace("’", "'").split()
    tur = "belde" if "(B)" in r["ham"] else None
    en_iyi, puanlar = None, collections.defaultdict(float)
    for k in (1, 2, 3):        # bucak kelime sayisi ('Marmara Ereğli si')
        for m in (1, 2):       # ilce kelime sayisi
            if len(tok) < k + m + 1:
                continue
            aday = " ".join(tok[-(k + m):-k])
            for ad in adaylar:
                sk = benzer(aday, ad)
                puanlar[ad] = max(puanlar[ad], sk)
                if sk >= esik and (en_iyi is None or sk > en_iyi[0] + 1e-9):
                    en_iyi = (sk, ad, " ".join(tok[:-(k + m)]), " ".join(tok[-k:]))
    if en_iyi and fark:
        ikinci = max((v for a, v in puanlar.items() if a != en_iyi[1]), default=0)
        if en_iyi[0] - ikinci < fark:
            en_iyi = None
    if en_iyi:
        _, ilce, birim, bucak = en_iyi
        return {"sira": r["sira"], "birim": birim.replace("(B)", "").strip(), "tur": tur, "eskiIlce": ilce,
                "eskiBucak": bucak, "okunan": r["ham"], "sayfa": r["sayfa"]}
    if r["varsayilanIlce"]:
        ad = max(adaylar, key=lambda a: benzer(a, r["varsayilanIlce"]), default=None)
        if ad and benzer(ad, r["varsayilanIlce"]) >= 0.8:
            return {"sira": r["sira"], "birim": r["ham"], "tur": "mahalle", "eskiIlce": ad, "eskiBucak": None,
                    "okunan": r["ham"], "altBaslik": r["varsayilanIlce"], "sayfa": r["sayfa"]}
    return {"sira": r["sira"], "birim": None, "tur": tur, "eskiIlce": None, "eskiBucak": None,
            "okunan": r["ham"], "sayfa": r["sayfa"]}


def main():
    kanun = sys.argv[1]
    cfg, sonuc = ayristir(kanun)
    OUT.mkdir(parents=True, exist_ok=True)
    veri = {
        "kanun": kanun, "ad": cfg["ad"], "kabul": cfg["kabul"], "resmiGazete": cfg["resmiGazete"],
        "kaynaklar": {"ekListeler": cfg["rgPdf"], "maddeler": cfg["mevzuatPdf"],
                      "rgUrl": f"https://www.resmigazete.gov.tr/arsiv/{cfg['resmiGazete']['sayi']}.pdf",
                      "mevzuatUrl": f"https://www.mevzuat.gov.tr/mevzuatmetin/1.5.{kanun}.pdf"},
        "guvenilirlik": "A (birincil/resmî); ek listeler taranmış OCR — eski ilçe adı o ilin sonraki genel seçimdeki "
                        "ilçe adlarıyla bulanık eşlendi, eşlenemeyen satır null bırakıldı",
        "ozet": {"ilce": len(sonuc), "tekKaynak": sum(1 for s in sonuc if s["tekKaynak"]),
                 "cokKaynak": sum(1 for s in sonuc if len([i for i in s["eskiIlceler"] if i["ad"]]) > 1),
                 "satir": sum(s["satirSayisi"] for s in sonuc),
                 "cozulemeyenSatir": sum(s["cozulemeyenSatir"] for s in sonuc),
                 "kaynakYazilmamisSatir": sum(1 for s in sonuc for r in s["satirlar"] if r.get("kaynakYazilmamis")),
                 "satirsizListe": [s["listeNo"] for s in sonuc if not s["satirSayisi"]],
                 "eksikSatirliListe": [s["listeNo"] for s in sonuc if s["eksikSira"]],
                 "geomIdsizYeniIlce": [s["ad"] for s in sonuc if not s["yeniIlce"]]},
        "ilceler": sonuc,
    }
    (OUT / f"{kanun}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(veri["ozet"], ensure_ascii=False))


if __name__ == "__main__":
    main()
