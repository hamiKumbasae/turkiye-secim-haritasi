"""
YSK mahalli idareler kesin sonuclari (il toplamlari) PDF'lerini okur:
  data/raw/ysk/mahalli-kesin-1984-1989/<yil>/<yil>-<Tur>-Secimleri-Sonucu.pdf
  data/raw/ysk/mahalli-kesin-1994-1999/<yil>/[<yil>-]<Tur>-Secimleri-Sonucu.pdf
Turler: il genel meclisi (igm), belediye meclisi (bm).

Okuma (metin katmani, OCR yok):
  - Sutunlar sayilarin sag kenarlarindan (sayilar saga dayali) kumelenir; ilk dort sutun
    sandik, secmen, oy kullanan, gecerli oy; kalanlar partiler.
  - Parti adi, sutunun ustundeki basliktan okunur (yatay ya da harf harf dikey yazilmis).
  - Hucre sayinin sag kenarina en yakin sutuna yazilir; bos hucre ('-' ya da yok) 0 degil,
    yok sayilir.
  - Tahmin yok: satir 'tutarli' ancak parti oylari toplami gecerli oya birebir esitse.
    Oy kullanan > secmen ise (kaynak yazim hatasi, ör. 1984 Canakkale) katilim yazilmaz.
  - Dogrulama: DIE kitabinin dogrulanmis il satirlariyla parti parti karsilastirildi (1984 igm 37,
    bm 16, 1989 igm 58, bm 62 ilde birebir; 1994'te farkli cikan 7 ilde DIE il satiri baska ile
    ait - bkz. build_meclis_harita.py).

Cikti: data/kaynaklar/ysk/mahalli-kesin/<yil>yerel_<igm|bm>.json

Kullanim:
  .venv/bin/python scripts/pipelines/ysk_kesin/parse_mahalli_kesin.py
"""
import collections
import json
import pathlib
import re
import unicodedata

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "ysk"
OUT = ROOT / "data" / "kaynaklar" / "ysk" / "mahalli-kesin"
DOSYA = {"igm": "Il-Genel-Meclisi-Uyeligi-Secimleri-Sonucu.pdf", "bm": "Belediye-Meclis-Uyeligi-Secimleri-Sonucu.pdf"}
KLASOR = {"1984": "mahalli-kesin-1984-1989", "1989": "mahalli-kesin-1984-1989",
          "1994": "mahalli-kesin-1994-1999", "1999": "mahalli-kesin-1994-1999"}
# 1999: parti basliklari harf harf dikey; otomatik okuma bazi etiketleri yer degistirdi. Sutun
# sirasi sayfa goruntusunden elle okundu (2026-09-27); yalniz sayfadaki parti sutunu sayisi bu
# listeyle birebir ayniysa kullanilir.
ELLE_SIRA = {
    ("1999", "igm"): ["ANAP", "BP", "BBP", "CHP", "DP", "DBP99", "DSP", "DEMTP", "DYP", "DEPAR", "EMEP", "FP",
                      "HADEP", "İP", "LDP", "MP92", "MHP", "ÖDP", "SİP", "YDP", "Bağımsız"],
    ("1999", "bm"): ["ANAP", "BP", "BBP", "CHP", "DP", "DBP99", "DSP", "DEMTP", "DYP", "DEHAP", "DEPAR", "EMEP",
                     "FP", "HADEP", "İP", "LDP", "MP92", "MHP", "ÖDP", "SİP", "YDP", "Bağımsız"],
}
# 1989 belediye meclisi basligi 'SODEP' yaziyor; parti 1985'ten beri SHP (DIE kitabi SHP; oylar
# 62 ilde birebir ayni) -> SHP.
ETIKET_YIL = {"1989": {"SODEP": "SHP"}}
# baslik etiketi (harf disi atilmis, buyuk harf) -> proje parti adi
PARTI = {"ANAP": "ANAP", "BBP": "BBP", "CHP": "CHP", "DP": "DP", "DSP": "DSP", "DYP": "DYP", "İP": "İP", "IP": "İP",
         "MHP": "MHP", "RP": "RP", "SBP": "SBP", "SHP": "SHP", "YDP": "YDP", "MİLLETPARTİSİ": "MP92", "MP": "MP92",
         "BAĞIMSIZLAR": "Bağımsız", "PARTİSİ": "MP92", "MİLLET": "MP92", "BAĞIMSIZ": "Bağımsız", "SDP": "SODEP", "SODEP": "SODEP", "HP": "HP", "MDP": "MDP",
         "IDP": "IDP", "İDP": "IDP", "MÇP": "MÇP", "FP": "FP", "DEPAR": "DEPAR", "HADEP": "HADEP", "LDP": "LDP",
         "DBP": "DBP99", "DTP": "DEMTP", "BP": "BP", "EMEP": "EMEP", "ÖDP": "ÖDP", "SİP": "SİP", "DEHAP": "DEHAP"}
SAYI = re.compile(r"^(\d{1,3}(\.\d{3})*|-)$")


def fold(s):
    s = unicodedata.normalize("NFC", s).replace("i", "İ").upper()
    return re.sub(r"[^A-ZÇĞİÖŞÜ]", "", s)


def parti_adi(b):
    if b in PARTI:
        return PARTI[b]
    for k in sorted(PARTI, key=len, reverse=True):
        if len(k) >= 4 and b.endswith(k):
            return PARTI[k]
    return None


def pdf_yolu(yil, tur):
    k = RAW / KLASOR[yil] / yil
    for ad in (f"{yil}-{DOSYA[tur]}", DOSYA[tur]):
        if (k / ad).exists():
            return k / ad
    return None


def sayfa_oku(pg):
    words = pg.extract_words(keep_blank_chars=False, use_text_flow=False)
    # satirlar il adina (sayilarin solundaki buyuk harfli kelime) capalanir; her sayi dikeyde en
    # yakin capaya (<= 7 pt) baglanir - ad ve hucreler ayni satirda birkac pt kayik olabiliyor
    sayilar = [w for w in words if SAYI.match(w["text"])]
    if len(sayilar) < 20:
        return [], None
    ilk_sayi_x = sorted(w["x0"] for w in sayilar)[len(sayilar) // 20]
    adlar = [w for w in words if not SAYI.match(w["text"]) and w["x1"] < ilk_sayi_x
             and re.fullmatch(r"[A-ZÇĞİÖŞÜÂ.()\-]+", w["text"]) and len(w["text"]) >= 2]
    capa = collections.defaultdict(list)
    for w in adlar:  # ayni satirdaki cok kelimeli adlar (KAHRAMAN MARAŞ) tek capa
        k = next((t for t in capa if abs(t - w["top"]) < 3), w["top"])
        capa[k].append(w)
    veri_ = collections.defaultdict(list)
    for w in sayilar:
        if not capa:
            break
        t = min(capa, key=lambda t: abs(t - w["top"]))
        if abs(t - w["top"]) <= 7:
            veri_[t].append(w)
    veri = [(" ".join(x["text"] for x in sorted(capa[t], key=lambda x: x["x0"])), sorted(veri_[t], key=lambda x: x["x0"]))
            for t in sorted(capa) if len(veri_[t]) >= 5]
    if not veri:
        return [], None
    # sutunlar: sayilarin sag kenari kumeleri (tire de sutuna yazilir)
    xs = sorted(w["x1"] for _, say in veri for w in say)
    kume = [[xs[0]]]
    for x in xs[1:]:
        (kume[-1] if x - kume[-1][-1] < 6 else kume.append([x]) or kume[-1]).append(x)
    merkez = [sum(c) / len(c) for c in kume if len(c) >= max(3, len(veri) // 4)]
    ust = min(w["top"] for _, say in veri for w in say) - 2
    sol = {i: min(w["x0"] for _, say in veri for w in say if abs(w["x1"] - m) < 6) for i, m in enumerate(merkez)}
    # baslik: sutunun komsu sutunlarina tasmayan kelimeler. Yatay etiket: sayilara en yakin bir
    # ya da iki satir; harf harf dikey yazilmis etiket: tek harfler, iki yonde denenir
    ust_kelime = [w for w in words if w["bottom"] <= ust + 2]
    baslik = []
    for i, m in enumerate(merkez):
        sinir_sol = merkez[i - 1] + 1 if i else 0
        sinir_sag = sol[i + 1] - 1 if i + 1 < len(merkez) else pg.width
        ws = [w for w in ust_kelime if w["x0"] >= sinir_sol and w["x1"] <= sinir_sag]
        aday = []
        kisa = [w for w in ws if len(w["text"]) <= 2]
        x_mod = collections.Counter(round(w["x0"]) for w in kisa).most_common(1)
        tek = [w for w in kisa if x_mod and abs(w["x0"] - x_mod[0][0]) <= 1.5]  # ayni dikey yigin
        if len(tek) >= 2:
            aday += [fold("".join(w["text"] for w in sorted(tek, key=k))) for k in (lambda w: w["top"], lambda w: -w["top"])]
        satirlar_ = sorted({round(w["bottom"]) for w in ws if len(w["text"]) > 1}, reverse=True)
        for n in (1, 2):
            sec = [w for w in ws if len(w["text"]) > 1 and round(w["bottom"]) in satirlar_[:n]]
            aday.append(fold("".join(w["text"] for w in sorted(sec, key=lambda w: (round(w["top"]), w["x0"])))))
        baslik.append(next((b for b in aday if parti_adi(b)), aday[-1] if aday else ""))
    satir = []
    for ad, say in veri:
        hucre = {}
        for w in say:
            i = min(range(len(merkez)), key=lambda j: abs(merkez[j] - w["x1"]))
            if abs(merkez[i] - w["x1"]) < 8 and i not in hucre:
                hucre[i] = None if w["text"] == "-" else int(w["text"].replace(".", ""))
        satir.append((ad, hucre))
    return satir, baslik


def izgara_oku(pg, n_parti):
    """1999: sutunlar tablo cizgilerinden (dikey kenar kumeleri). Beklenen hucre sayisi
    (il adi + 4 + partiler) tutmazsa sayfa okunmaz."""
    xs = sorted(e["x0"] for e in pg.edges if e["orientation"] == "v")
    if not xs:
        return []
    kenar = [[xs[0]]]
    for x in xs[1:]:
        (kenar[-1] if x - kenar[-1][-1] < 2 else kenar.append([x]) or kenar[-1]).append(x)
    kenar = [sum(k) / len(k) for k in kenar]
    if len(kenar) - 1 != 1 + 4 + n_parti:
        return None
    words = pg.extract_words(keep_blank_chars=False, use_text_flow=False)
    ilk = kenar[1]
    adlar = [w for w in words if w["x1"] <= ilk and not SAYI.match(w["text"])
             and re.fullmatch(r"[A-ZÇĞİÖŞÜÂ.()\-]+", w["text"]) and len(w["text"]) >= 2]
    capa = collections.defaultdict(list)
    for w in adlar:
        k = next((t for t in capa if abs(t - w["top"]) < 3), w["top"])
        capa[k].append(w)
    satir = collections.defaultdict(dict)
    for w in words:
        if not SAYI.match(w["text"]) or w["x0"] < ilk or not capa:
            continue
        t = min(capa, key=lambda t: abs(t - w["top"]))
        if abs(t - w["top"]) > 7:
            continue
        c = (w["x0"] + w["x1"]) / 2
        i = next((j for j in range(1, len(kenar) - 1) if kenar[j] <= c < kenar[j + 1]), None)
        if i is not None and (i - 1) not in satir[t]:
            satir[t][i - 1] = None if w["text"] == "-" else int(w["text"].replace(".", ""))
    return [(" ".join(x["text"] for x in sorted(capa[t], key=lambda x: x["x0"])), satir[t])
            for t in sorted(capa) if len(satir[t]) >= 5]


def oku(yil, tur):
    p = pdf_yolu(yil, tur)
    out, bilinmeyen = [], set()
    with pdfplumber.open(p) as pdf:
        for pg in pdf.pages:
            elle = ELLE_SIRA.get((yil, tur))
            if elle:
                satir = izgara_oku(pg, len(elle))
                if satir is None:
                    bilinmeyen.add("ızgara hücre sayısı tutmadı")
                    continue
                baslik = [""] * (4 + len(elle))
            else:
                satir, baslik = sayfa_oku(pg)
            if not satir:
                continue
            partiler = {}
            elle = ELLE_SIRA.get((yil, tur))
            if elle:
                if len(baslik) - 4 == len(elle):
                    partiler = {i + 4: ad for i, ad in enumerate(elle)}
                else:
                    bilinmeyen.add(f"sütun sayısı {len(baslik) - 4} != {len(elle)}")
            for i, b in enumerate([] if elle else baslik[4:], start=4):
                ad = parti_adi(b)
                ad = ETIKET_YIL.get(yil, {}).get(ad, ad)
                if ad:
                    partiler[i] = ad
                else:
                    bilinmeyen.add(b)
            for ad, h in satir:
                if any(i not in h for i in range(4)):
                    continue
                oy = {partiler[i]: v for i, v in h.items() if i in partiler and v}
                sandik, secmen, kullanan, gecerli = (h[i] for i in range(4))
                tut = gecerli is not None and len(partiler) == len(baslik) - 4 and sum(oy.values()) == gecerli
                r = {"ilKaynakta": ad, "sandik": sandik, "secmen": secmen, "oyKullanan": kullanan, "gecerliOy": gecerli,
                     "oy": oy, "kontrol": {"durum": "tutarli" if tut else "tutarsiz"}}
                if secmen and kullanan and kullanan <= secmen:
                    r["katilim"] = round(100 * kullanan / secmen, 2)
                out.append(r)
    return out, sorted(bilinmeyen), p


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for yil in KLASOR:
        for tur in DOSYA:
            satir, bilinmeyen, p = oku(yil, tur)
            kayit = {"secim": f"{yil}yerel", "tur": tur, "kaynak": {"ana": "ysk", "dosya": str(p.relative_to(ROOT)),
                     "okuma": "scripts/pipelines/ysk_kesin/parse_mahalli_kesin.py (metin katmanı; tahmin yok)"},
                     "satirlar": satir}
            (OUT / f"{yil}yerel_{tur}.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
            print(yil, tur, "satır", len(satir), "tutarlı", sum(1 for r in satir if r["kontrol"]["durum"] == "tutarli"),
                  "tanınmayan başlık", bilinmeyen)


if __name__ == "__main__":
    main()
