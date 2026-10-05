"""
YSK 1994 / 1999 / 2004 mahalli idareler "Tumu" PDF'lerini (belediye meclisi ve il genel meclisi,
il -> ilce -> belediye/sehir/koy kirilimi) okur.

Kaynak: data/raw/ysk/mahalli-meclis-1994-2004/<yil>Mahalli-<BelediyeMeclis|ilGenel>-Tumu.pdf
(ysk.gov.tr/doc/dosyalar/docs/Mahalli/<yil>/<tur>/Pdf/). Dijital metin; OCR yok.

Okuma (tahmin yok):
  - Sayfanin sutun basliklari (Sandik, Kayitli secmen, Oy kullanan secmen, Gecerli oy, [Uyelik
    sayisi], partiler) kelime koordinatlarindan okunur; bitisik kelimeler tek etiket ("MILLET
    PARTISI"). Sayilar saga dayali: bir sayi, sag kenarinin solunda kalan en yakin etiketin
    sutunudur (etiket sag kenari - 4 <= sayi sag kenari <= etiket sag kenari + 25).
  - Satir = ayni yukseklikteki kelimeler (6 pt). Bir kayit uc satirdir: oylar (ad + sandik ...),
    yuzdeler (katilim + parti yuzdeleri), 2004'te uyelik sayilari. Sayfa sonunda bolunen kayit
    sonraki sayfada devam eder.
  - Ad sutunu duzeyi verir: sol kenar = Turkiye/il, "Ilce" basligi hizasi = ilce, daha saga
    = belediye (bm: belde; igm: Sehir/Koy).
  - Kontrol: parti oylari toplami = gecerli oy; her partinin yazili yuzdesi oy/gecerli ile
    tutuyor (+-0,06, tamsayi yazilmissa +-0,51); katilim = oy kullanan / secmen. Hepsi tutarsa
    'tutarli'. Ayrica il = ilce (+ belde) toplami ve Turkiye = iller toplami raporlanir.

Cikti: data/kaynaklar/ysk/mahalli-meclis/<yil>yerel_<bm|igm>.json

Kullanim:
  python3 scripts/pipelines/ysk_kesin/parse_mahalli_meclis_tumu.py
"""
import collections
import json
import pathlib
import re
import unicodedata

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "ysk" / "mahalli-meclis-1994-2004"
OUT = ROOT / "data" / "kaynaklar" / "ysk" / "mahalli-meclis"
DOSYA = {"bm": "BelediyeMeclis", "igm": "ilGenel"}
YILLAR = ["1994", "1999", "2004"]
# baslik etiketi (harf disi atilmis, buyuk harf) -> proje parti adi
PARTI = {"ANAP": "ANAP", "BBP": "BBP", "CHP": "CHP", "DP": "DP", "DSP": "DSP", "DYP": "DYP", "İP": "İP",
         "MHP": "MHP", "RP": "RP", "SBP": "SBP", "SHP": "SHP", "YDP": "YDP", "MİLLETPARTİSİ": "MP92",
         "BAĞIMSIZLAR": "Bağımsız", "BP": "BP", "DBP": "DBP99", "DTP": "DEMTP", "DEHAP": "DEHAP",
         "DEPAR": "DEPAR", "EMEP": "EMEP", "FP": "FP", "HADEP": "HADEP", "LDP": "LDP", "ÖDP": "ÖDP",
         "SİP": "SİP", "BTP": "BTP", "AKPARTİ": "AK Parti", "TKP": "TKP", "ATP": "ATP", "GENÇPARTİ": "GP",
         "YTP": "YTP02", "SAADETPARTİSİ": "SP",
         # bazi sayfalarda iki kelimelik basliklar alt alta yazilmis: ilk kelime sutunu verir
         "MİLLET": "MP92", "SAADET": "SP", "GENÇ": "GP", "AK": "AK Parti"}
SABIT = {"SANDIK": "sandik", "KAYITLISEÇMEN": "secmen", "OYKULLANANSEÇMEN": "oyKullanan",
         "GEÇERLİOY": "gecerliOy", "GECERLİOY": "gecerliOy", "ÜYELİK": "uyelik"}
SAYI = re.compile(r"^\d{1,3}(\.\d{3})*$")
YUZDE = re.compile(r"^\d{1,3}(,\d)?$")


def fold(s):
    s = unicodedata.normalize("NFC", s).replace("i", "İ").upper()
    return re.sub(r"[^A-ZÇĞİÖŞÜ]", "", s)


def etiket(metin):
    f = fold(metin)
    if f.startswith("BAĞIMSI"):
        return "Bağımsız"
    if "İLLET" in f:  # 1999 il genel meclisi s.3: baslik "İLLET PARTİ" diye kesik
        return "MP92"
    if f in SABIT:
        return SABIT[f]
    return PARTI.get(f)


def gruplar(kelimeler, bosluk=4):
    """ayni satirdaki bitisik kelimeleri tek etikete birlestirir"""
    out = []
    for w in sorted(kelimeler, key=lambda w: w["x0"]):
        if out and w["x0"] - out[-1]["x1"] < bosluk:
            out[-1] = {"text": out[-1]["text"] + " " + w["text"], "x0": out[-1]["x0"], "x1": w["x1"],
                       "top": out[-1]["top"]}
        else:
            out.append(dict(w))
    return out


def satirlar(kelimeler, tol=6):
    out = []
    for w in sorted(kelimeler, key=lambda w: (w["top"], w["x0"])):
        if out and w["top"] - out[-1][0] <= tol:
            out[-1][1].append(w)
        else:
            out.append([w["top"], [w]])
    return [sorted(ws, key=lambda w: w["x0"]) for _, ws in out]


def sayfa_basligi(ws):
    """sutun etiketleri [(ad, sag_kenar)], ilce basligi x0, veri baslangic y, secim cevresi"""
    cevre = None
    m = [w for w in ws if w["text"].startswith("Çevresi")]
    if m:
        y = m[0]["top"]
        cevre = " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"])
                         if abs(w["top"] - y) < 3 and w["x0"] > m[0]["x1"])
    sandik = [w for w in ws if w["text"] == "Sandık"]
    if not sandik:
        return None
    y0 = sandik[0]["top"]
    bas = [w for w in ws if y0 - 2 <= w["top"] <= y0 + 14]
    ilce = next(w for w in bas if w["text"] == "İlçe")
    sutun = []
    for satir in satirlar(bas, tol=2):
        for g in gruplar(satir):
            e = etiket(g["text"])
            if e:
                sutun.append((e, g["x1"]))
    alt = [w for w in ws if w["text"] == "sayısı" and w["top"] > y0]
    veri_y = max(w["top"] for w in alt) + 4 if alt else y0 + 20
    ad_siniri = sandik[0]["x0"] - 5  # bunun solundaki her sey ad ("19 Mayıs" gibi rakamli adlar dahil)
    return {"sutun": sorted(sutun, key=lambda s: s[1]), "ilce_x0": ilce["x0"], "veri_y": veri_y, "cevre": cevre,
            "ad_siniri": ad_siniri}


def sutuna(x1, sutun):
    """saga dayali sayinin sutunu: sag kenari sag kenarina en yakin etiket (en fazla 22 pt)"""
    aday = sorted((abs(x1 - sx), ad) for ad, sx in sutun)
    return aday[0][1] if aday and aday[0][0] <= 22 else None


def sayi(t):
    """'1.234' ya da (bazi illerin sayfalarinda) '1234,0' -> 1234"""
    t = t.replace(".", "")
    if "," in t:
        tam, kesir = t.split(",")
        if kesir != "0":
            raise ValueError(t)
        t = tam
    return int(t)


def yuzde(t):
    return float(t.replace(",", "."))


def hucrele(satir, b):
    ad = [w for w in satir if w["x1"] < b["ad_siniri"] or not re.match(r"^[\d.,]+$", w["text"])]
    say = [w for w in satir if w["x1"] >= b["ad_siniri"] and re.match(r"^[\d.,]+$", w["text"])]
    hucre, kayip = collections.defaultdict(list), []
    for w in say:
        s = sutuna(w["x1"], b["sutun"])
        (hucre[s].append(w["text"]) if s else kayip.append((w["text"], round(w["x1"]))))
    return ad, say, hucre, kayip


def oku(pdf_yolu):
    kayitlar, son, hatalar = [], None, []
    cevre, bekleyen = None, []
    with pdfplumber.open(pdf_yolu) as pdf:
        for sn, p in enumerate(pdf.pages, 1):
            ws = p.extract_words(x_tolerance=1.5)
            b = sayfa_basligi(ws)
            if not b:
                continue
            cevre = b["cevre"] or cevre
            kuyruk = satirlar([w for w in ws if w["top"] > b["veri_y"]])
            while kuyruk:
                satir = kuyruk.pop(0)
                if any(w["text"] == "/" for w in satir):
                    continue  # sayfa altligi "1 / 3"
                ad, say, hucre, kayip = hucrele(satir, b)
                if any(len(v) > 1 for v in hucre.values()):
                    # oy satiri ile yuzde satiri cok yakin (ornek 2004 igm Bingol): yukseklige gore ikiye bolunur
                    ust = min(w["top"] for w in say)
                    bir = [w for w in satir if w["top"] - ust < 3]
                    iki = [w for w in satir if w["top"] - ust >= 3]
                    if bir and iki:
                        kuyruk.insert(0, iki)
                        ad, say, hucre, kayip = hucrele(bir, b)
                    if any(len(v) > 1 for v in hucre.values()):
                        hatalar.append((sn, "çift hücre", dict(hucre)))
                hatalar += [(sn, t, x) for t, x in kayip]
                h = {k: v[0] for k, v in hucre.items()}
                if ad and not say:
                    # ad satiri sayilardan bir kac pt yukarida kalmis (il satiri): sonraki satira aktarilir
                    bekleyen = ad
                    continue
                if "sandik" in h or "secmen" in h:
                    adlar, bekleyen = ad or bekleyen, []
                    x0 = adlar[0]["x0"] if adlar else None
                    duzey = ("ust" if x0 is not None and x0 < b["ilce_x0"] - 10 else
                             "ilce" if x0 is not None and abs(x0 - b["ilce_x0"]) <= 12 else "alt")
                    son = {"sayfa": sn, "cevre": cevre, "ad": " ".join(w["text"] for w in adlar).strip(),
                           "duzey": duzey, "x0": round(x0) if x0 is not None else None, "deger": h, "yuzde": None,
                           "uyelik": None}
                    kayitlar.append(son)
                elif son is not None and son["yuzde"] is None and son["uyelik"] is None and "oyKullanan" in h:
                    son["yuzde"] = h
                elif son is not None and son["uyelik"] is None and "uyelik" in h:
                    son["uyelik"] = h  # 2004: uyelik (sandalye) satiri; ilce/belde satirlarinda yuzde satiri yok
                elif h:
                    hatalar.append((sn, "sahipsiz satır", h))
    return kayitlar, hatalar


def kontrol(k):
    d, y = k["deger"], k["yuzde"] or {}
    try:
        secmen, oyk, gecerli = sayi(d["secmen"]), sayi(d["oyKullanan"]), sayi(d["gecerliOy"])
    except (KeyError, ValueError) as e:
        return None, f"eksik/okunamayan alan {e}"
    try:
        oy = {p: sayi(v) for p, v in d.items() if p not in SABIT.values() and v != "0"}
    except ValueError as e:
        return None, f"okunamayan oy {e}"
    sorun, yuzde_farki = [], []
    if sum(oy.values()) != gecerli:
        sorun.append(f"toplam {sum(oy.values())} != geçerli {gecerli}")
    notlar = []
    if oyk > secmen:
        notlar.append("oy kullanan > kayıtlı seçmen (kaynakta)")
    if gecerli > oyk:
        notlar.append("geçerli oy > oy kullanan (kaynakta)")
    # yazili yuzdeler kaynakta yer yer yuvarlama disi farkli (ornek 1994 Adana SBP 1.082/663.336 = %0,16,
    # yazili %0,1); yalniz bilgi olarak kaydedilir, tutarlilik parti toplamina ve il toplamina dayanir
    for p, v in oy.items():
        if p in y and gecerli and abs(100 * v / gecerli - yuzde(y[p])) > (0.06 if "," in y[p] else 0.51):
            yuzde_farki.append(f"{p} %{y[p]}")
    if set(y) - {"oyKullanan"} - set(oy):
        sorun.append(f"yüzdesi olup oyu olmayan sütun {sorted(set(y) - {'oyKullanan'} - set(oy))}")
    satir = {"sandik": sayi(d["sandik"]) if "sandik" in d else None, "secmen": secmen, "oyKullanan": oyk,
             "gecerliOy": gecerli, "katilim": round(100 * oyk / secmen, 2) if secmen else None, "oy": oy}
    if k.get("uyelik"):
        satir["uyelik"] = {p: sayi(v) for p, v in k["uyelik"].items()}
    if yuzde_farki:
        satir["yuzdeFarki"] = yuzde_farki
    if notlar:
        satir["kaynakNotu"] = notlar
    return satir, sorun


def yapilandir(kayitlar, kisa):
    out, il, ilce = [], None, None
    gorulen, atla = set(), False
    for k in kayitlar:
        if k["duzey"] == "ust":
            # Turkiye (ve il) satiri sonraki sayfalarin basinda tekrar ediyor: ilki tutulur, tekrarin
            # altindaki Sehir/Koy satirlari da atlanir
            atla = k["ad"] in gorulen
            gorulen.add(k["ad"])
            if atla:
                continue
        elif k["duzey"] == "ilce":
            atla = False
        elif atla:
            continue
        satir, sorun = kontrol(k)
        if satir is None:
            out.append({"ad": k["ad"], "sayfa": k["sayfa"], "kontrol": {"durum": "okunamadi", "sorun": [sorun]}})
            continue
        if k["duzey"] == "ust":
            tip = "turkiye" if k["ad"] == "Türkiye" else "il"
            # il adi sayfa basligindaki "Secim Cevresi"nden (satirdaki ad yer yer kesik: "Kastamon", "Afyon Toplam")
            il = (k["cevre"] or k["ad"]) if tip == "il" else None
            ilce = None
        elif k["duzey"] == "ilce":
            tip, ilce = "ilce", k["ad"]
        else:
            tip = {"Şehir": "sehir", "Köy": "koy"}.get(k["ad"], "belde" if kisa == "bm" else "?")
        out.append({"tip": tip, "il": il if tip != "turkiye" else None, "ilce": ilce if tip in ("ilce", "belde", "sehir", "koy") else None,
                    "ad": k["ad"], "cevre": k["cevre"], "sayfa": k["sayfa"], **satir,
                    "kontrol": {"durum": "tutarli" if not sorun else "tutarsiz", **({"sorun": sorun} if sorun else {})}})
    return out


def hiyerarsi(rows, kisa):
    """il = ilce(+belde) toplami, Turkiye = iller toplami; parti parti"""
    fark = []
    def topla(rs):
        t = collections.Counter()
        for r in rs:
            t.update(r["oy"])
            t["_gecerli"] += r["gecerliOy"]
        return t
    iller = [r for r in rows if r.get("tip") == "il"]
    for il in iller:
        alt = [r for r in rows if r.get("tip") in (("ilce", "belde") if kisa == "bm" else ("ilce",)) and r.get("il") == il["il"]]
        t = topla(alt)
        beklenen = collections.Counter(il["oy"]); beklenen["_gecerli"] = il["gecerliOy"]
        if t != beklenen:
            fark.append({"il": il["il"], "farkli": {k: [beklenen.get(k, 0), t.get(k, 0)] for k in set(t) | set(beklenen) if t.get(k, 0) != beklenen.get(k, 0)}})
    if kisa == "igm":
        for i, r in enumerate(rows):
            if r.get("tip") in ("ilce", "il", "turkiye"):
                s = [x for x in rows[i + 1:i + 3] if x.get("tip") in ("sehir", "koy")]
                if len(s) == 2:
                    t = topla(s); b = collections.Counter(r["oy"]); b["_gecerli"] = r["gecerliOy"]
                    if t != b:
                        fark.append({"satir": r["ad"], "il": r.get("il"), "sehir+koy farkli": True})
    tr = next((r for r in rows if r.get("tip") == "turkiye"), None)
    if tr:
        t = topla(iller); b = collections.Counter(tr["oy"]); b["_gecerli"] = tr["gecerliOy"]
        if t != b:
            fark.append({"turkiye": {k: [b.get(k, 0), t.get(k, 0)] for k in set(t) | set(b) if t.get(k, 0) != b.get(k, 0)}})
    return fark


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for yil in YILLAR:
        for kisa, ad in DOSYA.items():
            pdf = RAW / f"{yil}Mahalli-{ad}-Tumu.pdf"
            kayitlar, hatalar = oku(pdf)
            rows = yapilandir(kayitlar, kisa)
            fark = hiyerarsi([r for r in rows if r.get("tip")], kisa)
            say = collections.Counter((r.get("tip"), r["kontrol"]["durum"]) for r in rows)
            (OUT / f"{yil}yerel_{kisa}.json").write_text(json.dumps({
                "kaynak": {"ana": "ysk", "dosya": str(pdf.relative_to(ROOT)),
                           "url": f"https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/{yil}/{ad}/Pdf/{pdf.name}",
                           "betik": "scripts/pipelines/ysk_kesin/parse_mahalli_meclis_tumu.py"},
                "ozet": {f"{a}:{b}": n for (a, b), n in sorted(say.items(), key=str)},
                "okumaHatalari": [list(map(str, h)) for h in hatalar][:200],
                "hiyerarsiFarklari": fark,
                "satirlar": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(yil, kisa, dict(say), "okuma hatası", len(hatalar), "hiyerarşi farkı", len(fark))


if __name__ == "__main__":
    main()
