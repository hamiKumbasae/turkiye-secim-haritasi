"""
TUIK, "Halk Oylaması Sonuçları 2007, 1988, 1987, 1982, 1961" (2008;
kutuphane.tuik.gov.tr/pdf/0018260.pdf) yayininin "İl ve ilçelere göre halk
oylaması sonucu" tablolarini (Tablo 2-6) kaynak katmanina cikarir:

  data/kaynaklar/tuik/referandum/<secim>.json   (1961/1982/1987/1988/2007referandum)

PDF'in metin katmaninda iki kusur var, ikisi de burada telafi edilir:
  - Turkce harfler glif koduyla: (cid:248)=İ, (cid:249)=Ş, (cid:250)=ş, (cid:247)=ğ
  - "ı" harfi TAMAMEN dusmus ("Fındıklı" -> "Fndkl"); ad duzeltmesi
    birlestirme adiminda referans ilce adlariyla yapilir (burada kaynak yazimi
    `adKaynakta` olarak saklanir).
  - Binlik ayiraci bosluk: "1 196 275 469 255 594" gibi bitisik token'lar.
    Yuzde (ondalikli) degerler capa alinir; sandik/kayitli/kullanan ucluSu,
    yayinin kendi katilim oranina (1 ondalik) uyan TEK bolunmeyle secilir.
    Uyan bolunme tek degilse ya da hic yoksa satir `hata` ile isaretlenir.

Her sayi satiri icin tutarlilik: gecersiz + gecerli = kullanan, evet + hayir =
gecerli. Tutmayan satirlar `kontrol` alaninda raporlanir (duzeltilmez).

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/extract_halkoylamasi.py
"""
import collections
import itertools
import json
import pathlib
import re
import sys

import pdfplumber

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
PDF = ROOT / "data" / "raw" / "tuik" / "halkoylamasi-0018260" / "0018260.pdf"
OUT = ROOT / "data" / "kaynaklar" / "tuik" / "referandum"
CID = {"(cid:248)": "İ", "(cid:249)": "Ş", "(cid:250)": "ş", "(cid:247)": "ğ"}
ALT = {"SEHIR TOPLAM": "sehir", "SEHIR TOPLAMI": "sehir", "BUCAK VE KOYLER TOPLAM": "koy",
       "BUCAK VE KOYLER TOPLAMI": "koy"}
DEC = re.compile(r"^\d+\.\d$")
TARIHSEL_IL = {"İçel": 33, "Afyon": 3, "K.Maraş": 46, "Maraş": 46, "Urfa": 63, "Afyonkarahisar": 3,
               "Kahramanmaraş": 46, "Şanlıurfa": 63, "Mersin": 33}


def temizle(t):
    for k, v in CID.items():
        t = t.replace(k, v)
    t = re.sub(r"\(cid:\d+\)", "", t)
    return re.sub(r"[\ue000-\uf8ff]", "", t)  # ozel kullanim alani glifleri (dipnot isaretleri)


def _bolunmeler(tokens, n):
    """Token listesini n sayiya bol: her sayi = 1-3 haneli bas + 0..k adet 3 haneli grup."""
    if n == 0:
        if not tokens:
            yield []
        return
    for i in range(1, len(tokens) + 1):
        bas, kalan = tokens[:i], tokens[i:]
        if not (1 <= len(bas[0]) <= 3) or any(len(x) != 3 for x in bas[1:]):
            continue
        if len(bas[0]) > 1 and bas[0].startswith("0"):
            continue
        for rest in _bolunmeler(kalan, n - 1):
            yield [int("".join(bas))] + rest


def _tek(tokens):
    b = list(_bolunmeler(tokens, 1))
    return b[0][0] if len(b) == 1 else None


def satir_sayilari(tokens):
    """[sandik kayitli kullanan] katilim% gecersiz % gecerli % evet % hayir %"""
    idx = [i for i, t in enumerate(tokens) if DEC.match(t)]
    if len(idx) != 5:
        return None, f"{len(idx)} ondalik deger (5 bekleniyor)"
    seg = [tokens[:idx[0]]] + [tokens[idx[k] + 1:idx[k + 1]] for k in range(4)]
    kat = float(tokens[idx[0]])
    gecersiz, gecerli, evet, hayir = (_tek(s) for s in seg[1:])
    if None in (gecersiz, gecerli, evet, hayir):
        return None, "tek sayilik segment bolunemedi"
    adaylar = []
    for sandik, kayitli, kullanan in _bolunmeler(seg[0], 3):
        if kayitli and round(kullanan * 100 / kayitli, 1) == kat and sandik < kayitli:
            adaylar.append((sandik, kayitli, kullanan))
    # katilim tutmazsa (yayindaki yuvarlama) kullanan = gecersiz + gecerli ile dene
    if not adaylar:
        adaylar = [b for b in _bolunmeler(seg[0], 3) if b[2] == gecersiz + gecerli and b[0] < b[1]]
    if len(adaylar) != 1:
        return None, f"sandik/kayitli/kullanan icin {len(adaylar)} olasi bolunme"
    sandik, kayitli, kullanan = adaylar[0]
    rec = {"sandik": sandik, "secmen": kayitli, "oyKullanan": kullanan, "katilimYayinda": kat,
           "gecersizOy": gecersiz, "gecerliOy": gecerli, "evet": evet, "hayir": hayir}
    kontrol = []
    if gecersiz + gecerli != kullanan:
        kontrol.append(f"gecersiz+gecerli={gecersiz + gecerli} != kullanan={kullanan}")
    if evet + hayir != gecerli:
        kontrol.append(f"evet+hayir={evet + hayir} != gecerli={gecerli}")
    if kontrol:
        rec["kontrol"] = kontrol
    return rec, None


def sayfalar():
    """(yil, [satir metinleri]) - yalnizca 'İl ve ilçelere göre' tablolari."""
    with pdfplumber.open(PDF) as p:
        for no, pg in enumerate(p.pages, start=1):
            t = temizle(pg.extract_text() or "")
            m = re.search(r"Halk oylaması, (\d{4})", t)
            if not m or not re.search(r"İl ve ilçeler\s*e\s*göre", t):
                continue
            yield int(m.group(1)), no, t.split("\n")


def extract():
    iller_by_yil = {}
    for y in (1961, 1982, 1987, 1988, 2007):
        d = json.loads((ROOT / f"data/normalized/elections/referandum/{y}referandum.json").read_text(encoding="utf-8"))
        # "ı" dusmus yazimla da taninsin
        iller_by_yil[y] = {fold(r["ad"]).replace("I", ""): r["plaka"] for r in d["iller"]}
        for eski, pl in TARIHSEL_IL.items():  # yayin donemin il adlarini kullaniyor
            iller_by_yil[y].setdefault(fold(eski).replace("I", ""), pl)
    out = collections.defaultdict(lambda: {"iller": [], "hatalar": []})
    for yil, sayfa, satirlar in sayfalar():
        o = out[yil]
        for ln in satirlar:
            m = re.match(r"^(\D+?)\s+([\d .]+)$", ln.strip())
            if not m:
                continue
            ad, tokens = m.group(1).strip(), m.group(2).split()
            if fold(ad) in ("TURKIYE",) or fold(ad).startswith("HALK OYLAMASI"):
                continue
            rec, hata = satir_sayilari(tokens)
            if hata:
                o["hatalar"].append({"sayfa": sayfa, "satir": ln.strip(), "hata": hata})
                continue
            alt = ALT.get(fold(ad))
            if alt:
                hedef = o["iller"][-1]["ilceler"][-1] if o["iller"] and o["iller"][-1]["ilceler"] else (o["iller"][-1] if o["iller"] else None)
                if hedef is not None:
                    hedef.setdefault("sehirKoy", {})[alt] = rec
                continue
            f = fold(ad).replace("I", "")
            if f in iller_by_yil[yil] and (not o["iller"] or o["iller"][-1]["ilceler"] or fold(ad) != "MERKEZ"):
                # il satiri: yilin il listesinde olan ad (ilceler "Merkez" ile baslar)
                if not o["iller"] or o["iller"][-1]["ilceler"] or f != fold(o["iller"][-1]["adKaynakta"]).replace("I", ""):
                    o["iller"].append({"adKaynakta": ad, "plaka": iller_by_yil[yil][f], "sayfa": sayfa, **rec, "ilceler": []})
                    continue
            if not o["iller"]:
                o["hatalar"].append({"sayfa": sayfa, "satir": ln.strip(), "hata": "ilden once ilce"})
                continue
            o["iller"][-1]["ilceler"].append({"adKaynakta": ad, "sayfa": sayfa, **rec})
    OUT.mkdir(parents=True, exist_ok=True)
    for yil, o in sorted(out.items()):
        # ilce toplami == il toplami kontrolu
        tutmayan = []
        for il in o["iller"]:
            for f in ("secmen", "gecerliOy", "evet", "hayir"):
                s = sum(i[f] for i in il["ilceler"])
                if s != il[f]:
                    tutmayan.append({"il": il["adKaynakta"], "alan": f, "il": il[f], "ilceToplami": s})
        veri = {
            "secim": f"{yil}referandum", "kaynak": "tuik", "tur": "referandum",
            "yayin": "TÜİK, Halk Oylaması Sonuçları 2007, 1988, 1987, 1982, 1961 (Ankara, 2008)",
            "yayinUrl": "https://kutuphane.tuik.gov.tr/pdf/0018260.pdf",
            "hamDosya": str(PDF.relative_to(ROOT)),
            "not": "Ad yazımları PDF metin katmanındaki hâliyle (adKaynakta); 'ı' harfi kaynakta düşmüş.",
            "ozet": {"il": len(o["iller"]), "ilce": sum(len(i["ilceler"]) for i in o["iller"]),
                     "ayristirilamayanSatir": len(o["hatalar"]), "ilceToplamiIlToplamiTutmayan": len(tutmayan)},
            "ilceToplamiTutmayan": tutmayan, "hatalar": o["hatalar"], "iller": o["iller"],
        }
        (OUT / f"{yil}referandum.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
        print(yil, veri["ozet"])


if __name__ == "__main__":
    extract()
