"""
Taranmis (OCR metinli) DIE secim kitaplarindaki il/ilce tablolarini, kelime
KOORDINATLARINDAN okuyan yardimci.

Neden metin degil koordinat: bu kitaplarda binlik ayiraci bosluktur ("118 408")
ve sifir degerler "—" ile gosterilir; metin cikariminda tireler bir alt satira
kayar, hangi sutunun bos oldugu kaybolur. Koordinatla:
  1. kelimeler dikey konuma gore satirlara gruplanir (tire satiri ustune katilir)
  2. araligi dar, 3 haneli devam gruplari tek sayiya birlestirilir
  3. sayilarin sag kenarlari sayfa icinde kumelenerek sutunlar bulunur

Cikti: [(etiket, [deger|None ...], y, ham_parcalar)] - None = sutunda hic deger yok, 0 = "—".
"""
import re

import pdfplumber

SAYI = re.compile(r"^\d{1,3}$")
TIRE = re.compile(r"^[—–-]+,?$")


def _satirlar(words, tol=5.5):
    words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    out, cur, top = [], [], None
    for w in words:
        if top is None or w["top"] - top <= tol:
            cur.append(w)
            top = top if top is not None else w["top"]
        else:
            out.append(cur)
            cur, top = [w], w["top"]
    if cur:
        out.append(cur)
    return out


def etiketsiz_satir_mi(s):
    return all(w["text"].strip(".,'`;:").isdigit() or TIRE.match(w["text"]) for w in s)


def _tokenler(ws, x_min):
    """Satirdaki sayi parcalari ve tireler, x sirali: [(metin, x0, x1, tur)]."""
    out = []
    for w in sorted((w for w in ws if w["x0"] >= x_min), key=lambda w: w["x0"]):
        if TIRE.match(w["text"]):
            out.append(("0", w["x0"], w["x1"], "tire"))
            continue
        t = w["text"].strip("'`;:")
        if re.fullmatch(r"\d{1,3}[.,]\d{1,2}", t):
            out.append((t.replace(",", "."), w["x0"], w["x1"], "yuzde"))
            continue
        t = t.strip(".,")
        if t.isdigit():
            out.append((t, w["x0"], w["x1"], "sayi"))
    return out


def _gruplar(tok, buyuk_bosluk):
    g = []
    for t in tok:
        if g and t[3] == "sayi" and g[-1][-1][3] == "sayi" and t[1] - g[-1][-1][2] < buyuk_bosluk:
            g[-1].append(t)
        else:
            g.append([t])
    return g


def _deger(parcalar):
    if len(parcalar) == 1 and parcalar[0][3] == "tire":
        return 0
    yz = [p for p in parcalar if p[3] == "yuzde"]
    if yz:
        return float(yz[0][0])
    s = "".join(p[0] for p in parcalar if p[3] == "sayi")
    return int(s) if s else None


def sayfa_tablosu(page, x_etiket_son, sutun_sayisi, satir_filtre=None, buyuk_bosluk=12.0, hazir_kenarlar=None,
                  etiketsiz=False, kelime_duzelt=None):
    """Sayfadaki veri satirlari: [(etiket, degerler)] ; len(degerler) == sutun_sayisi.
    Sutun sag kenarlari once 'temiz' satirlardan (buyuk bosluklarla tam
    sutun_sayisi gruba bolunenler) medyanla bulunur; sonra her parca, sag kenari
    parcanin sagindan buyuk olan ILK sutuna atanir (kalin punto satirlarinda
    sutunlar arasi bosluk daralsa da sinir asilmaz).

    kelime_duzelt(kelime) -> yeni metin | None: OCR harf/rakam karisikliklari
    icin (orn. '9*.3' -> '94.3'); degisen kelimenin eski hali w['orijinal']'de."""
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    if kelime_duzelt:
        for w in words:
            yeni = kelime_duzelt(w)
            if yeni is not None and yeni != w["text"]:
                w["orijinal"], w["text"] = w["text"], yeni
    satirlar = []
    ham = _satirlar(words)
    # etiketi olup sayisi eksik kalan satir + hemen altindaki ETIKETSIZ sayi
    # satiri = tek satir (OCR satiri ikiye bolmus; orn. 1966 Trabzon/Maçka)
    birlesik = []
    for s in ham:
        if birlesik and etiketsiz_satir_mi(s) and not etiketsiz and len(_tokenler(birlesik[-1], x_etiket_son - 30)) <= 2:
            birlesik[-1] = birlesik[-1] + s
        else:
            birlesik.append(s)
    for s in birlesik:
        # etiket: soldaki sayi OLMAYAN kelimeler; sayi bolgesi x_etiket_son'dan
        # biraz once baslayabilir (6 haneli secmen sayisinin ilk grubu)
        etk = [w for w in sorted(s, key=lambda w: w["x0"])
               if w["x1"] <= x_etiket_son + 10 and not w["text"].strip(".,'`;:").isdigit()
               and not TIRE.match(w["text"])]
        etiket = " ".join(w["text"] for w in etk).strip()
        # sayi bolgesi: etiketin (harf iceren) son kelimesinin sagi - kitaptan
        # kitaba etiket sutunu genisligi degisiyor, sabit x esigi ilk grubu kesiyordu
        harfli = [w for w in etk if re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", w["text"])]
        if etiketsiz:
            # karsi sayfa: satirlarda ad yok; harf iceren satirlar baslik
            if any(re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,}", w["text"]) for w in s):
                continue
            tok = _tokenler(s, 0)
            if len(tok) >= 2:
                satirlar.append(("", tok, s[0]["top"]))
            continue
        x_bas = (max(w["x1"] for w in harfli) + 1) if harfli else x_etiket_son - 30
        tok = _tokenler(s, x_bas)
        if etiket and tok and (satir_filtre is None or satir_filtre(etiket)):
            satirlar.append((etiket, tok, s[0]["top"]))
    # sayfa basina bosluk esigi: taranmis sayfalarin olcegi farkli; tam
    # sutun_sayisi gruba bolunen satir sayisini en cok yapan esik secilir
    en_iyi, kenar = -1, None
    for esik in [x / 2 for x in range(14, 29)]:
        k_ = [[] for _ in range(sutun_sayisi)]
        n = 0
        for _, tok, _y in satirlar:
            g = _gruplar(tok, esik)
            if len(g) == sutun_sayisi:
                n += 1
                for k, grp in enumerate(g):
                    k_[k].append(grp[-1][2])
        if n > en_iyi:
            en_iyi, kenar = n, k_
    if any(not k for k in kenar):
        if not hazir_kenarlar:
            return None, [len(k) for k in kenar]
        # ayni tablonun ayni yondeki sayfasindan; tarama kaymasi icin kenarlari
        # sayfadaki sayi-sonu x1'lerine en iyi oturan ofsetle kaydir
        x1ler = [g[-1][2] for _, tok, _y in satirlar for g in _gruplar(tok, 9.0)]
        def maliyet(d):
            return sum(min(abs(x - (e + d)) for e in hazir_kenarlar) for x in x1ler)
        d = min((x / 2 for x in range(-50, 51)), key=maliyet)
        kenarlar = [e + d for e in hazir_kenarlar]
    else:
        kenarlar = [sorted(k)[len(k) // 2] for k in kenar]
    out = []
    for etiket, tok, y in satirlar:
        parca = [[] for _ in range(sutun_sayisi)]
        for t in tok:
            i = next((k for k, e in enumerate(kenarlar) if t[2] <= e + 4), sutun_sayisi - 1)
            parca[i].append(t)
        out.append((etiket, [_deger(p) if p else None for p in parca], y, ["—" if t[3] == "tire" else t[0] for t in tok]))
    return out, kenarlar


def ac(pdf_yolu):
    return pdfplumber.open(pdf_yolu)
