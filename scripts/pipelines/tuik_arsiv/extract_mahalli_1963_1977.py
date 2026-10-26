"""
1963-1977 DIE yerel secim kitaplarindaki il genel meclisi (IGM) ve belediye meclisi (BM) tablolarini kaynak
katmanina cikarir (extract_mahalli.py ile ayni bicim):

  data/kaynaklar/tuik/yerel/<secim>/{il_genel_meclisi,belediye_meclisi}.json

  1977yerel  kutuphane.tuik.gov.tr/pdf/0015740.pdf  DIE, Yerel Secim Sonuclari, 11 Aralik 1977 (1979)
  1973yerel  kutuphane.tuik.gov.tr/pdf/0015468.pdf  DIE, Mahalli Secimler Sonuclari, 9 Aralik 1973 (1974)

Neden ayri okuyucu: bu kitaplarin tarama metin katmaninda (ABBYY, 2009) ilce/belediye adlarinin cogu yok
(sayfada basili, OCR almamis; ornek 1977 IGM Adana'nin 14 satirindan yalniz Kadirli ve Osmaniye'nin adi
var). extract_mahalli.tablo_oku adsiz satirlari atar. Burada:

  - Sayilar extract_mahalli/die_tablo ile ayni koordinat okumasiyla okunur (sol yuz: sandik, secmen, oy
    kullanan, katilim %, gecerli oy, ilk partiler; sag yuz: kalan partiler), adsiz satirlar da alinir.
    Iki yuz sirayla, sag yuzdeki parti yuzdelerinin sol yuzdeki gecerli oya uymasiyla hizalanir.
  - Dogrulama extract_mahalli.dogrula ile ayni (parti toplami == gecerli oy; her parti yuzdesi kitaptakiyle;
    katilim). Tutarsiz satir sayi parcalarinin kisitlarla yeniden ayristirilmasiyla (yapisal_oku) denenir.
    Kitabin "Yanlis-Dogru Cetveli" (DIE'nin kendi duzeltmeleri) okumadan once uygulanir.
  - IGM ilce adi (tahmin yok): il blogundaki satir sayisi, donemin ilce listesinin (Merkez + TUIK genel secim
    ilce listesi, ayni yil) uzunluguna esitse satirlar o sirayla adlandirilir; blokta adi okunabilen her
    satir sirasindaki adla tutmali, ilce satirlarinin sandik/secmen toplami il satirina esit olmali. Biri
    tutmazsa blogun satirlari adsiz kalir (haritaya islenmez) ve nedeni yazilir.
  - BM kimligi adla degil, ayni secimin belediye baskanligi kaydiyla (sandik, secmen) birebir eslemeyle
    sonraki adimda (build_meclis_harita) kurulur; burada yalniz il bloklari ve okunabilen adlar.

Tahmin yok: okunamayan ya da dogrulanamayan hucre bos/isaretli kalir; toplamdan geri hesap yalniz
extract_mahalli.dogrula'nin kuralinda (tek hucre, kendi yuzdesiyle teyitli) yapilir ve `ocrDuzeltme`'ye yazilir.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/extract_mahalli_1963_1977.py [1977yerel] [il_genel_meclisi belediye_meclisi]
"""
import json
import re
import unicodedata
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import die_tablo  # noqa: E402
import extract_mahalli as E  # noqa: E402
import goruntu_okuma as G  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "tuik" / "mahalli-kitap"
OUT = ROOT / "data" / "kaynaklar" / "tuik" / "yerel"
PNG = ROOT / ".cache" / "tuik" / "png"

P77_SOL = ["AP", "CHP", "CGP"]
P77_SAG = ["DEMP73", "MSP", "MHP", "SDP", "TBP73", "TİP", "TSİP", "Bağımsız"]
ONCU = ["sandik", "secmen", "oyKullanan", "katilim%", "gecerliOy"]
P73_SOL = ["AP", "CHP"]
P73_SAG = ["CGP", "DEMP73", "MP62", "MHP", "MSP", "TBP73", "Bağımsız"]

KITAPLAR = {
    "1977yerel": {
        "demirbas": "0015740", "tarih": "11 Aralık 1977", "yayin": "DİE, Yerel Seçim Sonuçları, 11 Aralık 1977 (1979)",
        "partiler": P77_SOL + P77_SAG, "genelIlce": "1977", "binlikBosluk": True,
        "sol": ONCU + [x for p in P77_SOL for x in (p, p + "%")],
        "sag": [x for p in P77_SAG for x in (p, p + "%")],
        "tablolar": {"il_genel_meclisi": (8, 43), "belediye_meclisi": (128, 201)},
        # Yanlis-Dogru Cetveli (kitap s. son, PDF s.235): bu iki tablodaki tek kayit kitap s.21 (PDF 27, IGM sag
        # yuz) sutun 15 satir 1 = Kars il satiri Bagimsiz oyu. Digerleri baskanlik tablosunda (s.51-78).
        "cetvel": {27: [{"sutun": 15, "satir": 1, "yanlis": 50678, "dogru": 50679}]},
    },
    "1973yerel": {
        "demirbas": "0015468", "tarih": "9 Aralık 1973",
        "yayin": "DİE, Mahalli Seçimler Sonuçları, 9 Aralık 1973 (yayın no. 716, 1974)",
        "partiler": P73_SOL + P73_SAG, "genelIlce": "1973", "binlikBosluk": True,
        # sol yuzde gecerli oy katilimdan once
        "sol": ["sandik", "secmen", "oyKullanan", "gecerliOy", "katilim%"] + [x for p in P73_SOL for x in (p, p + "%")],
        "sag": [x for p in P73_SAG for x in (p, p + "%")],
        "tablolar": {"il_genel_meclisi": (10, 47), "belediye_meclisi": (138, 221)},
        # Yanlis-Dogru Cetveli (PDF s.223; kitap sayfasi + 6 = PDF). s.49-96 kayitlari baskanlik tablosunda.
        "cetvel": {10: [{"sutun": 5, "satir": 2, "yanlis": 63.4, "dogru": 38.8}],
                   11: [{"sutun": 2, "satir": 2, "yanlis": 7.7, "dogru": 5.9},
                        {"sutun": 4, "satir": 2, "yanlis": 14.2, "dogru": 16.0}],
                   18: [{"sutun": 5, "satir": 12, "yanlis": 36.9, "dogru": 72.2}],
                   29: [{"sutun": 1, "satir": 17, "yanlis": 345, "dogru": 945}],
                   34: [{"sutun": 6, "satir": 1, "yanlis": 87214, "dogru": 67214}],
                   38: [{"sutun": 6, "satir": 17, "yanlis": 35544, "dogru": 3544},
                        {"sutun": 7, "satir": 34, "yanlis": 32.7, "dogru": 23.7}],
                   187: [{"sutun": 1, "satir": 38, "yanlis": 89, "dogru": 29}]},
    },
}


def sag_yuz_mu(page):
    t = re.sub(r"\s", "", page.extract_text() or "")
    return "siyasipartilerin" in t or "siyasipartiler" in t


def kitap_no(page):
    """Sayfanin kitaptaki numarasi (ilk dolu satirin basindaki/sonundaki 1-3 haneli sayi) ya da None."""
    for s in (page.extract_text() or "").splitlines():
        if s.strip():
            # sol yuz "122 3. Belediye ...", sag yuz "3. Belediye ... 123" (bastaki "3." tablo numarasi)
            m = re.match(r"^\s*(\d{1,3})(?![.\d])", s) or re.search(r"\b(\d{1,3})\s*$", s)
            return int(m.group(1)) if m else None
    return None


def guvenilir_no(pdf, n):
    """Kitap numarasi yalniz bir komsu PDF sayfasinin numarasiyla ardisiksa (sayfa numarasi da OCR'la
    yanlis okunabiliyor: "5" -> "1")."""
    k = kitap_no(pdf.pages[n - 1])
    if k is None:
        return None
    onceki = kitap_no(pdf.pages[n - 2]) if n >= 2 else None
    sonraki = kitap_no(pdf.pages[n]) if n < len(pdf.pages) else None
    return k if onceki == k - 1 or sonraki == k + 1 else None


def baslik_farki(sol, sag):
    """Sag yuz basligi ile sol yuz basliginin dikey farki (pt): her yuzde en ustteki >= 4 harfli sozcuk."""
    def ust(pg):
        ys = [w["top"] for w in pg.extract_words() if re.fullmatch(r"[^\W\d_]{4,}", w["text"])]
        return min(ys) if ys else None
    a, b = ust(sol), ust(sag)
    return b - a if a is not None and b is not None else None


def kenar_uydur(page, sablon, x_min):
    """Sablon kenarlari (iyi okunmus sayfadan) bu sayfaya olcek + kaydirmayla oturtulur: sayfadaki sayi
    gruplarinin sag kenarlarina toplam uzakligi en kucuk (a, b). die_tablo yalniz kaydirma deniyor; sayfalar
    arasinda kucuk olcek farki sag sutunlari bir sutun kaydirabiliyor."""
    import numpy as np
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    for w in words:
        y = E.kelime_duzelt(w)
        if y is not None:
            w["text"] = y
    x1 = [g[-1][2] for sat in die_tablo._satirlar(words) for g in die_tablo._gruplar(die_tablo._tokenler(sat, x_min), 9.0)]
    if len(x1) < 20:
        return None
    X = np.array(x1)[:, None]
    S = np.array(sablon)[None, :]
    en_iyi = None
    for a in np.arange(0.97, 1.0301, 0.0025):
        for b in np.arange(-45, 45.01, 0.5):
            m = np.minimum(np.abs(X - (a * S + b)).min(axis=1), 8).sum()
            if en_iyi is None or m < en_iyi[0]:
                en_iyi = (m, a, b)
    _, a, b = en_iyi
    return [float(a * e + b) for e in sablon]


def _yuz(page, cfg, sol, kenar=None):
    """Bir yuzun satirlari; kenar verilirse o kenarlarla (zorla), verilmezse sayfanin kendi kenarlariyla."""
    n = len(cfg["sol"] if sol else cfg["sag"])
    ek = dict(hazir_kenarlar=kenar, kenar_zorla=True, ofset_ara=False) if kenar else {}
    if sol:
        L, k = die_tablo.sayfa_tablosu(page, 160, n, None, kelime_duzelt=E.kelime_duzelt, etiket_zorunlu=False, **ek)
        if L is None:
            return None, k
        satir = []
        ilk_y = min((y for e, v, y, h in L if isinstance(v[0], int) and isinstance(v[1], int) and v[1] >= max(v[0], 50)),
                    default=None)
        for e, v, y, h in L:
            # veri satiri: sandik ve secmen tam sayi, secmen >= sandik (baslik/sayfa no satirlari elenir). Metin
            # katmani bozuk satir (ad okunur ya da en az 3 hucre sayi, ilk veri satirinin altinda) de alinir:
            # degerleri goruntuden ikinci okumayla bulunur, tutmazsa satir dogrulanmamis kalir.
            if isinstance(v[0], int) and isinstance(v[1], int) and v[1] >= max(v[0], 50):
                satir.append({"etiket": e, "v": dict(zip(cfg["sol"], v)), "y": y, "ham": h})
            elif ilk_y is not None and y > ilk_y + 3 and v[1] != 0 and (
                    re.search(r"[^\W\d_]{3,}", e or "") or
                    (sum(isinstance(x, int) for x in v) >= 3 and any(isinstance(x, int) and x for x in v[1:3]))):
                # secmen 0: kitapta (*) dipnotlu, secim yapilmayan birim (Bozcaada, Gokceada); adsiz ve secmen /
                # oy kullanan okunmayan parca: bolunmus satirin artigi
                satir.append({"etiket": e, "v": dict(zip(cfg["sol"], v)), "y": y, "ham": h, "bozuk": True})
        return satir, k
    R, k = die_tablo.sayfa_tablosu(page, 120, n, None, etiketsiz=True, kelime_duzelt=E.kelime_duzelt, **ek)
    if R is None:
        return None, k
    return [{"v": dict(zip(cfg["sag"], v)), "y": y, "ham": h} for e, v, y, h in R], k


def yuz_secenekleri(page, cfg, sol, sablon):
    """[(satirlar, kenarlar, kaynak)]: sayfanin kendi kenarlari ve sablonun bu sayfaya oturtulmus hali."""
    out = []
    satir, k = _yuz(page, cfg, sol)
    if satir is not None:
        out.append((satir, k, "sayfa"))
    if sablon:
        uy = kenar_uydur(page, sablon, 150 if sol else 0)
        if uy:
            satir, k = _yuz(page, cfg, sol, uy)
            if satir is not None:
                out.append((satir, k, "şablon"))
    return out


def _tutarli_sayisi(hiza, partiler):
    return sum(1 for s, r in hiza if r and E.dogrula({**s["v"], **r["v"]}, partiler)[1]["durum"] == "tutarli")


def tablo_oku(pdf, cfg, ilk, son):
    sayfalar = [n for n in range(ilk, son + 1)]
    ciftler, eslesmeyen = [], []
    i = 0
    while i < len(sayfalar):
        a = sayfalar[i]
        if not sag_yuz_mu(pdf.pages[a - 1]) and i + 1 < len(sayfalar) and sag_yuz_mu(pdf.pages[sayfalar[i + 1] - 1]):
            # kitap numaralari okunuyorsa sag yuz sol yuzun hemen ardindaki kitap sayfasi olmali (taramada eksik
            # sayfa varsa ardisik PDF sayfalari ayni tablo satirlari degildir)
            na, nb = guvenilir_no(pdf, a), guvenilir_no(pdf, sayfalar[i + 1])
            if na is not None and nb is not None and nb != na + 1:
                eslesmeyen.append({"sayfa": a, "neden": f"kitap s.{na}; sağ yüzü (s.{na + 1}) taramada yok"})
                eslesmeyen.append({"sayfa": sayfalar[i + 1], "neden": f"kitap s.{nb}; sol yüzü (s.{nb - 1}) taramada yok"})
            else:
                ciftler.append((a, sayfalar[i + 1]))
            i += 2
        else:
            eslesmeyen.append({"sayfa": a, "neden": "eşi olan sol/sağ yüz yok"})
            i += 1
    satirlar = []
    # sablon: kendi kenarlariyla okununca satirlarinin en buyuk orani tutarli olan cift (en az 10 satir)
    sablon_sol = sablon_sag = None
    en_iyi_oran = -1
    for a, b in ciftler:
        so, sa = yuz_secenekleri(pdf.pages[a - 1], cfg, True, None), yuz_secenekleri(pdf.pages[b - 1], cfg, False, None)
        if not so or not sa or len(so[0][0]) < 10:
            continue
        hiza = E._hizala(so[0][0], sa[0][0], cfg["partiler"])
        oran = _tutarli_sayisi(hiza, cfg["partiler"]) / len(so[0][0])
        if oran > en_iyi_oran:
            en_iyi_oran, sablon_sol, sablon_sag = oran, so[0][1], sa[0][1]
    for a, b in ciftler:
        # her yuz icin sayfanin kendi kenarlari ve sablon denenir; ciftin en cok tutarli satir veren birlesimi
        # secilir (secim satirlarin kendi ic tutarliligina dayanir)
        so = yuz_secenekleri(pdf.pages[a - 1], cfg, True, sablon_sol)
        sa = yuz_secenekleri(pdf.pages[b - 1], cfg, False, sablon_sag)
        if not so or not sa:
            eslesmeyen.append({"sayfa": [a, b], "neden": "sütunlar bulunamadı"})
            continue
        en_iyi = None
        for sol, kl, ks in so:
            for sag, kr, kk in sa:
                hiza = E._hizala(sol, sag, cfg["partiler"])
                puan = (_tutarli_sayisi(hiza, cfg["partiler"]), sum(1 for _, r in hiza if r))
                if en_iyi is None or puan > en_iyi[0]:
                    en_iyi = (puan, sol, kl, sag, kr, hiza, ks, kk)
        (dogru, _), sol, kl, sag, kr, hiza, ks, kk = en_iyi
        ts, tr = E._sayfa_tokenleri(pdf.pages[a - 1], True), E._sayfa_tokenleri(pdf.pages[b - 1], False)
        kd = E._duzeltmeler(pdf.pages[a - 1]), E._duzeltmeler(pdf.pages[b - 1])
        if sum(1 for _, r in hiza if r) < 0.5 * len(sol):
            # yuzdelerle hizalanamadi (sag yuz metni cok bozuk): satir sayilari esitse sirayla eslenir (yanlis eslesen
            # satir toplam/yuzde kontrolunden gecemez); degilse sol yuz satirlari sag yuz olmadan alinir.
            if len(sol) == len(sag):
                hiza = list(zip(sol, sag))
                eslesmeyen.append({"sayfa": b, "neden": f"s.{a} ile yüzdelerle hizalanamadı; satır sayısı eşit, sırayla eşlendi"})
            else:
                eslesmeyen.append({"sayfa": b, "neden": f"s.{a} sol yüzüyle hizalanamadı"})
                hiza = [(x, None) for x in sol]
        # sag yuzde esi bulunamayan satirin sag yuzdeki konumu: ayni ciftte eslesen satirlarin dikey farki (medyan);
        # hic eslesen yoksa iki yuzun baslik satirlarinin dikey farki (dizgi ayni, fark tarama kaymasi; eslesen
        # ciftlerde medyan farkla 1,5 pt icinde). Yanlis satira denk gelen okuma toplam/yuzde kontrolunden gecemez.
        farklar = sorted(r["y"] - s["y"] for s, r in hiza if r)
        dy_cift = farklar[len(farklar) // 2] if farklar else baslik_farki(pdf.pages[a - 1], pdf.pages[b - 1])
        for sira, (s, r) in enumerate(sorted(hiza, key=lambda sr: sr[0]["y"]), 1):
            k = [(t, y) for yy, t, y in kd[0] if abs(yy - s["y"]) < 5]
            if r:
                k += [(t, y) for yy, t, y in kd[1] if abs(yy - r["y"]) < 5]
            satirlar.append({"etiket": s["etiket"], "v": {**s["v"], **(r["v"] if r else {})},
                             "sagYok": r is None, "sayfa": [a, b], "karakterDuzeltme": k,
                             "tokSol": ts.get(s["y"]), "tokSag": tr.get(r["y"]) if r else None,
                             "kenarSol": kl, "kenarSag": kr, "ySol": s["y"], "sira": sira,
                             "ySag": r["y"] if r else (s["y"] + dy_cift if dy_cift is not None else None)})
    return satirlar, eslesmeyen


def genel_ilce_listesi(yil):
    """{plaka: [(ilce adi, secmen)]} TUIK genel secim kaynak katmanindan (ayni yil)."""
    d = json.loads((ROOT / f"data/kaynaklar/tuik/genel/{yil}.json").read_text(encoding="utf-8"))
    out = {}
    for c in d["cevreler"]:
        for r in c.get("ilceler") or []:
            out.setdefault(c["plaka"], []).append((r["ad"], r.get("secmen")))
    return out


def kitap_sirasi(adlar):
    """DIE kitaplarinda ilceler Merkez basta (ilde Merkez ilcesi varsa; Istanbul'da yok), sonra Turk alfabesiyle."""
    abc = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"

    def anahtar(a):
        a = re.sub(r"\(.*?\)", "", a).strip().upper().replace("i", "İ")
        return [abc.index(c) if c in abc else 99 for c in a.replace("Â", "A").replace("Î", "İ").replace("Û", "U")]
    digerleri = [a for a in adlar if E._anahtar(a) != "MERKEZ"]
    return (["Merkez"] if len(digerleri) < len(adlar) else []) + sorted(digerleri, key=anahtar)


def _ad_tutar(okunan, ad):
    o, a = E._anahtar(okunan), E._anahtar(ad)
    return len(o) < 3 or o == a or E._benzer(o, a) >= 0.75


def _sapma(sec, ref):
    return abs(sec / ref - 1) if sec and ref else 9.0


SIRA_SAPMA = 0.20     # sirayla adlandirmada satir secmeni genel secim secmeninden en fazla bu kadar sapabilir
SECMEN_SAPMA = 0.10   # secmenle eslemede en fazla sapma
SECMEN_FARK = 0.03    # secmenle eslemede en iyi ile ikinci aday arasindaki en az sapma farki


def ilce_adlandir(kayitlar, cfg):
    """IGM il bloklarindaki ilce satirlarini adlandirir (tahmin yok). Her blokta ilce satirlarinin sandik ve
    secmen toplami il satirina esit olmali (blok tam okunmus). Sonra:
      1. sira: satir sayisi donemin ilce listesine esit; liste kitap sirasinda (Merkez + alfabe); okunabilen her
         ad sirasindakiyle tutuyor (ya da satirin secmeni o ilcenin genel secim secmeninden %5'ten az sapiyor);
         her satirin secmeni sirasindaki ilcenin genel secim secmeninden en fazla %20 sapiyor.
      2. secmen (sira tutmazsa; buyuksehirlerde merkez ilceler basta, Canakkale'de Imroz/Bozcaada satiri yok):
         her satir genel secim secmeni en yakin ilceye; eslesme karsilikli ve tek, sapma <= %10, ikinci aday en az
         3 puan uzak; okunabilen ad baska bir ilceyi gosteriyorsa blok adlandirilmaz.
    Adlandirilamayan blogun satirlari adsiz kalir (haritaya islenmez), nedeni `kimlik.neden`'de."""
    liste = genel_ilce_listesi(cfg["genelIlce"])
    rapor = {}
    bloklar = {}
    for r in kayitlar:
        if r["tip"] == "ilce" and r["plaka"]:
            bloklar.setdefault(r["plaka"], []).append(r)
    il_satiri = {r["plaka"]: r for r in kayitlar if r["tip"] == "il"}
    for p, satirlar in sorted(bloklar.items()):
        sec = dict(liste.get(p, []))
        neden = []
        il = il_satiri.get(p)
        if not il:
            neden.append("il satırı yok")
        else:
            for alan in ("sandik", "secmen"):
                t = sum(r.get(alan) or 0 for r in satirlar)
                if t != il.get(alan):
                    neden.append(f"ilçe {alan} toplamı {t}, il satırı {il.get(alan)}")
        atama, yontem = None, None
        if not neden:
            ref = kitap_sirasi(list(sec))
            if len(ref) == len(satirlar) and all(
                    (_ad_tutar(r["adKaynakta"], ad) or _sapma(r["secmen"], sec.get(ad)) < 0.05)
                    and _sapma(r["secmen"], sec.get(ad)) <= SIRA_SAPMA for r, ad in zip(satirlar, ref)):
                atama, yontem = list(zip(satirlar, ref)), "sira"
            else:
                # once adi okunabilen satirlar: adi tek bir ilceyle tutan ve secmeni o ilceden <= %10 sapan satir
                # o ilceye; kalanlar kalan ilcelere secmenle
                aday, kalan = {}, dict(sec)
                for i, r in enumerate(satirlar):
                    tutan = [ad for ad in sec if len(E._anahtar(r["adKaynakta"])) >= 3 and _ad_tutar(r["adKaynakta"], ad)]
                    if len(tutan) == 1 and _sapma(r["secmen"], sec[tutan[0]]) <= SECMEN_SAPMA and tutan[0] in kalan:
                        aday[i] = tutan[0]
                        del kalan[tutan[0]]
                for i, r in enumerate(satirlar):
                    if i in aday:
                        continue
                    sira = sorted((_sapma(r["secmen"], v), ad) for ad, v in kalan.items())
                    if sira and sira[0][0] <= SECMEN_SAPMA and (len(sira) < 2 or sira[1][0] - sira[0][0] >= SECMEN_FARK):
                        aday[i] = sira[0][1]
                ters = {}
                for i, ad in aday.items():
                    ters.setdefault(ad, []).append(i)
                okunan_celisir = [r["adKaynakta"] for i, r in enumerate(satirlar) if i in aday
                                  and len(E._anahtar(r["adKaynakta"])) >= 3 and not _ad_tutar(r["adKaynakta"], aday[i])
                                  and any(_ad_tutar(r["adKaynakta"], ad) for ad in sec)]
                if len(aday) == len(satirlar) and all(len(v) == 1 for v in ters.values()) and not okunan_celisir:
                    atama, yontem = [(r, aday[i]) for i, r in enumerate(satirlar)], "secmen"
                else:
                    if len(aday) < len(satirlar):
                        neden.append(f"{len(satirlar) - len(aday)} satır genel seçim seçmeniyle tek bir ilçeye bağlanamadı")
                    if any(len(v) > 1 for v in ters.values()):
                        neden.append("iki satır aynı ilçeye düştü")
                    if okunan_celisir:
                        neden.append(f"okunan ad başka ilçeyi gösteriyor: {okunan_celisir}")
        if not atama and il and any("toplamı" in n for n in neden):
            # blok tam okunamadi (bir satirin secmeni yanlis okunmus): yalniz dogrulanmis satirlar tek tek secmenle
            # baglanir (ad-oncelikli, karsilikli tek, sapma <= %10, ikinci aday en az 3 puan uzak); celisen satir adsiz
            uygun = [r for r in satirlar if r["kontrol"]["durum"] == "tutarli" and not r["kontrol"].get("katilimUyumsuz")]
            aday, kalan = {}, dict(sec)
            for r in uygun:
                tutan = [ad for ad in sec if len(E._anahtar(r["adKaynakta"])) >= 3 and _ad_tutar(r["adKaynakta"], ad)]
                if len(tutan) == 1 and _sapma(r["secmen"], sec[tutan[0]]) <= SECMEN_SAPMA and tutan[0] in kalan:
                    aday[id(r)] = (r, tutan[0])
                    del kalan[tutan[0]]
            for r in uygun:
                if id(r) in aday:
                    continue
                okunabilir = len(E._anahtar(r["adKaynakta"])) >= 3
                sira = sorted((_sapma(r["secmen"], v), ad) for ad, v in kalan.items())
                if sira and sira[0][0] <= SECMEN_SAPMA and (len(sira) < 2 or sira[1][0] - sira[0][0] >= SECMEN_FARK) \
                        and (not okunabilir or _ad_tutar(r["adKaynakta"], sira[0][1])):
                    aday[id(r)] = (r, sira[0][1])
            sayac = {}
            for r, ad in aday.values():
                sayac[ad] = sayac.get(ad, 0) + 1
            atama = [(r, ad) for r, ad in aday.values() if sayac[ad] == 1]
            yontem = "secmen (blok eksik)"
            if atama:
                rapor[p] = neden + [f"blok toplamı tutmadı; {len(atama)}/{len(satirlar)} doğrulanmış satır seçmenle tek tek bağlandı"]
                for r in satirlar:
                    r["kimlik"] = {"yontem": "cozulemedi", "neden": "; ".join(neden)}
        if atama:
            for r, ad in atama:
                r["ad"] = ad
                r["kimlik"] = {"yontem": yontem, "genelSecimSecmeni": sec.get(ad),
                               "not": "kitap sırası ve okunabilen adlar" if yontem == "sira"
                               else "genel seçim (aynı yıl) ilçe seçmeniyle karşılıklı tek eşleşme"}
        elif p not in rapor:
            rapor[p] = neden or ["adlandırılamadı"]
            for r in satirlar:
                r["kimlik"] = {"yontem": "cozulemedi", "neden": "; ".join(rapor[p])}
    return rapor


def _ad_norm(s):
    """build_meclis_harita.ad_norm ile ayni: parantez ici atilir, kucuk harf, yalniz harf."""
    if not s:
        return ""
    s = re.sub(r"\(.*?\)", "", s)
    s = unicodedata.normalize("NFC", s.replace("İ", "i").replace("I", "ı").lower())
    return re.sub(r"[^a-zçğıöşü]", "", s)


def _ad_parcalari(s):
    s = unicodedata.normalize("NFC", (s or "").replace("İ", "i").replace("I", "ı").lower())
    return frozenset(x for x in re.split(r"[^a-zçğıöşü]+", s) if x)


def yerel_adlarina_cevir(kayitlar, secim):
    """IGM satirlari genel secim (TUIK) ilce adlariyla adlandirildi; harita birimleri ayni yilin yerel secim
    kaydindaki adlarla. Yazim farki olan ad (Dogubeyazit / Dogubayazit, Bozoyuk / Bozuyuk, Sinanpasa
    (Sincanli) / Sincanli (Sinanpasa), S.Karaagac / Sarkikaraagac) ayni ildeki yerel ada cevrilir: ayni ad
    parcalari, kisaltma (bas harf + kalan) ya da benzerlik >= 0,7 ve ikinciden en az 0,1 fazla; aday tek olmali
    ve baska satirin birebir adi olmamali. Genel secim adi `adGenel`de kalir."""
    ana = json.loads((ROOT / "data/normalized/elections/yerel" / f"{secim}.json").read_text(encoding="utf-8"))
    yerel = {}
    for a in ana["ilceler"]:
        yerel.setdefault(a["plaka"], []).append(a["ad"])
    cevrilen = []
    for pl in {r["plaka"] for r in kayitlar if r.get("ad")}:
        adlar = yerel.get(pl, [])
        normlar = {_ad_norm(a): a for a in adlar}
        satirlar = [r for r in kayitlar if r["plaka"] == pl and r.get("ad") and r["tip"] == "ilce"]
        birebir = {_ad_norm(r["ad"]) for r in satirlar if _ad_norm(r["ad"]) in normlar}
        for r in satirlar:
            n = _ad_norm(r["ad"])
            if n in normlar:
                continue
            # "(il merkezi belediyesi)": buyuk kentin belediyesi, ilce degil (Ankara/Istanbul/Izmir merkez ilceleri
            # haritada tek birim; IGM ilce satirlari ona baglanmaz)
            bos = [a for a in adlar if _ad_norm(a) not in birebir and "il merkezi" not in a]
            aday = [a for a in bos if _ad_parcalari(a) == _ad_parcalari(r["ad"])]
            m = re.fullmatch(r"\s*([^\W\d_])\.\s*([^\W\d_]+)\s*", r["ad"])
            if not aday and m:
                bas, kalan = _ad_norm(m.group(1)), _ad_norm(m.group(2))
                aday = [a for a in bos if _ad_norm(a).startswith(bas) and _ad_norm(a).endswith(kalan)]
            if not aday:
                puan = sorted(((E._benzer(n, _ad_norm(a)), a) for a in bos), reverse=True)
                if puan and puan[0][0] >= 0.7 and (len(puan) == 1 or puan[0][0] - puan[1][0] >= 0.1):
                    aday = [puan[0][1]]
            if len(aday) == 1:
                cevrilen.append((pl, r["ad"], aday[0]))
                r["adGenel"], r["ad"] = r["ad"], aday[0]
                birebir.add(_ad_norm(aday[0]))
    return cevrilen


def katilim_duzelt(r):
    """Katilim yuzdesinin ondalik noktasi metin katmaninda dusmus olabilir ('495' = 49,5). Yalniz oy kullanan /
    secmen oranini (0,1 puan) tutuyorsa duzeltilir; tutmuyorsa yuzde bos birakilir (deger `katilimOkunan`'da)."""
    k, s, kat = r.get("oyKullanan"), r.get("secmen"), r.get("katilim")
    if kat is None or (isinstance(kat, float) and kat <= 100):
        return
    hesap = 100 * k / s if isinstance(k, int) and isinstance(s, int) and s else None
    aday = kat / 10
    r["katilimOkunan"] = kat
    r["katilim"] = aday if hesap is not None and abs(hesap - aday) <= 0.1 else None


def belediye_kimlik(kayitlar, secim):
    """BM: il blogundaki satirlardan (sandik, secmen) ayni secimin belediye baskanligi kaydindaki bir ilce (Merkez
    dahil) satiriyla il icinde TEK olarak birebir tutani `ilce`, digerleri `belde`. Ayni belediyenin meclis ve
    baskanlik secimi ayni secmen listesiyle yapilir. Dondurur: eslesmeyen baskanlik ilceleri {plaka: [ad]}."""
    ana = json.loads((ROOT / "data/normalized/elections/yerel" / f"{secim}.json").read_text(encoding="utf-8"))
    by = {}
    for a in ana["ilceler"]:
        if a.get("secmen"):
            by.setdefault((a["plaka"], a["secmen"]), []).append(a)
    bulunan = set()
    for r in kayitlar:
        if r["tip"] not in ("ilce", "belde") or not r["plaka"] or not r.get("secmen"):
            continue
        aday = by.get((r["plaka"], r["secmen"]), [])
        aday = [a for a in aday if not a.get("sandik") or not r.get("sandik") or a["sandik"] == r["sandik"]]
        if len(aday) == 1:
            r["tip"], r["ad"] = "ilce", aday[0]["ad"]
            r["kimlik"] = {"yontem": "baskanlikSecmeni", "not": "sandık + seçmen başkanlık kaydındaki ilçe belediyesiyle birebir"}
            bulunan.add(aday[0]["geomId"])
        else:
            r["tip"] = "belde"
            if len(aday) > 1:
                r["kimlik"] = {"yontem": "cozulemedi", "neden": "seçmen birden çok başkanlık satırıyla tutuyor"}
    # 2. asama, kalan baskanlik ilceleri: il icinde (a) kitapta okunan ad ayni (OCR'a karsi benzerlik >= 0,85) ve
    # secmen %3 icinde, ya da (b) secmen birebir ayni (>= 1000; sandik iki tablodan birinde farkli okunmus) ve iki
    # tarafta da il icinde tek. Buyuksehir satiri kitapta "<il> Belediyesi Toplami".
    def ad_anahtari(x):
        return re.sub(r"BELEDIYES[I]?TOPLAMI?$", "", E._anahtar(x))
    for a in ana["ilceler"]:
        if a["geomId"] in bulunan or not a.get("secmen"):
            continue
        havuz = [r for r in kayitlar if r["plaka"] == a["plaka"] and r["tip"] == "belde" and r.get("secmen")
                 and not r.get("kimlik")]
        aa = ad_anahtari(a["ad"])
        ada = [r for r in havuz if len(ad_anahtari(r["adKaynakta"])) >= 3
               and (ad_anahtari(r["adKaynakta"]) == aa or E._benzer(ad_anahtari(r["adKaynakta"]), aa) >= 0.85)
               and abs(r["secmen"] - a["secmen"]) <= 0.03 * a["secmen"]]
        sec = [r for r in havuz if r["secmen"] == a["secmen"]] if a["secmen"] >= 1000 and \
            len(by.get((a["plaka"], a["secmen"]), [])) == 1 and \
            sum(1 for r in kayitlar if r["plaka"] == a["plaka"] and r.get("secmen") == a["secmen"]) == 1 else []
        if len(ada) == 1:
            r, yontem, n = ada[0], "baskanlikAdi", "kitapta okunan ad başkanlık kaydındaki ilçe belediyesiyle aynı, seçmen %3 içinde"
        elif len(sec) == 1:
            r, yontem, n = sec[0], "baskanlikSecmeni", "seçmen başkanlık kaydındaki ilçe belediyesiyle birebir ve il içinde tek (sandık farklı okunmuş)"
        else:
            continue
        r["tip"], r["ad"], r["kimlik"] = "ilce", a["ad"], {"yontem": yontem, "not": n}
        bulunan.add(a["geomId"])
    eksik = {}
    for a in ana["ilceler"]:
        if a["geomId"] not in bulunan:
            eksik.setdefault(a["plaka"], []).append(a["ad"])
    return eksik


def cetvel_uygula(satirlar, cfg):
    """Kitabin Yanlis-Dogru Cetveli (DIE'nin kendi duzeltmesi) dogrulamadan ONCE uygulanir. Kayit: PDF sayfasi,
    sutun (yuzun kendi sutun sirasi, 1'den), satir. Hucre o sayfa + sutundaki degeri cetveldeki yanlis degere
    esit olan TEK satirda degistirilir (satir sayimi OCR'da kayabilir; deger eslesmesi esastir). Dondurur:
    uygulanamayan kayitlar."""
    kalan = []
    for no, kayitlar in cfg.get("cetvel", {}).items():
        for c in kayitlar:
            aday = []
            for s in satirlar:
                if no not in s["sayfa"]:
                    continue
                alan = (cfg["sol"] if no == s["sayfa"][0] else cfg["sag"])[c["sutun"] - 1]
                x = s["v"].get(alan)
                if isinstance(x, (int, float)) and abs(x - c["yanlis"]) < 0.01:
                    aday.append((s, alan))
            if len(aday) == 1:
                s, alan = aday[0]
                s["v"] = dict(s["v"], **{alan: c["dogru"]})
                s.setdefault("cetvel", []).append(dict(c, alan=alan, sayfa=no))
            else:
                kalan.append(dict(c, sayfa=no, neden=f"sayfada bu değer {len(aday)} satırda"))
    return kalan


def cetvel_gec(v, s, kalan, cfg):
    """Metin katmaninda okunamayan (cetvel_uygula'da eslesmeyen) kayit, ikinci okumanin degerine uygulanir:
    satirin sayfasi ve sayfadaki sirasi kayittakiyle ayni, hucre degeri cetveldeki yanlis deger olmali."""
    for c in list(kalan):
        if c["sayfa"] not in s["sayfa"] or s.get("sira") != c["satir"]:
            continue
        alan = (cfg["sol"] if c["sayfa"] == s["sayfa"][0] else cfg["sag"])[c["sutun"] - 1]
        x = v.get(alan)
        if isinstance(x, (int, float)) and abs(x - c["yanlis"]) < 0.01:
            v = dict(v, **{alan: c["dogru"]})
            s.setdefault("cetvel", []).append({k: c[k] for k in ("sutun", "satir", "yanlis", "dogru", "sayfa")} |
                                              {"alan": alan, "not": "ikinci okumada"})
            kalan.remove(c)
    return v


def goruntu_oku(pdf, cfg, s):
    """Tutarsiz satirin ikinci okumasi (goruntu_okuma.py). Sol yuzun oncu alanlari (sandik, secmen, oy kullanan,
    katilim, gecerli) metin katmanindan alinir, katilim kendi yuzdesini tutuyorsa; yoksa goruntuden."""
    a, b = s["sayfa"]
    if s.get("ySag") is None:
        return None
    metin = {}
    for no, kenar, y, alanlar in ((a, s["kenarSol"], s["ySol"], cfg["sol"]), (b, s["kenarSag"], s["ySag"], cfg["sag"])):
        if not kenar or not all(isinstance(x, float) for x in kenar):
            return None
        pg = pdf.pages[no - 1]
        img = G.goruntu(str(RAW / f"{cfg['demirbas']}.pdf"), no, str(PNG / cfg["demirbas"]))
        donusum = G.kayma(pg, img, (cfg["demirbas"], no), PNG / cfg["demirbas"] / f"{no:04d}.png")
        if donusum is None:
            return None
        metin.update(zip(alanlar, G.satir_metinleri(img, pg, kenar, y, donusum)))
    tv = s["v"]
    oncu_ok = not E.dogrula(tv, cfg["partiler"])[1].get("katilimUyumsuz") and all(
        isinstance(tv.get(k), int) for k in ("secmen", "oyKullanan", "gecerliOy")) and \
        isinstance(tv.get("katilim%"), float) and tv["secmen"] and abs(100 * tv["oyKullanan"] / tv["secmen"] - tv["katilim%"]) <= 0.1
    if oncu_ok:
        v = G.coz(metin, cfg["partiler"], ONCU, tv["gecerliOy"], yedek=tv)
        v.update({k: tv[k] for k in ONCU})
    else:
        # gecerli oy iki okumada farkliysa her aday denenir; satiri tutarli yapan TEK aday kabul edilir
        adaylar = {x for x in G.sayi_adaylari(metin.get("gecerliOy")) + [tv.get("gecerliOy")] if isinstance(x, int) and x > 0}
        tutan = []
        for g in sorted(adaylar):
            vg = G.coz(metin, cfg["partiler"], ONCU, g, yedek=tv)
            if E.dogrula(vg, cfg["partiler"])[1]["durum"] == "tutarli":
                tutan.append(vg)
        if len(tutan) != 1:
            return None
        v = tutan[0]
    # kabul icin oncu alanlar eksiksiz ve katilim tutarli olmali
    if not all(isinstance(v.get(k), int) for k in ("secmen", "oyKullanan", "gecerliOy")) or not isinstance(v.get("katilim%"), float):
        return None
    return v


def isle(secim, tablolar=None):
    cfg = KITAPLAR[secim]
    E.BINLIK_BOSLUK = cfg.get("binlikBosluk", False)
    pdf = die_tablo.ac(RAW / f"{cfg['demirbas']}.pdf")
    G.onbellek_ac(PNG.parent / f"ocr_{cfg['demirbas']}.json")
    il_ad = E.il_adlari()
    ilce_kume = E.genel_ilceler(cfg["genelIlce"])
    for tablo, (ilk, son) in cfg["tablolar"].items():
        if tablolar and tablo not in tablolar:
            continue
        satirlar, eslesmeyen = tablo_oku(pdf, cfg, ilk, son)
        # ilk satir (adsiz) Turkiye toplami
        if satirlar and not E._anahtar(satirlar[0]["etiket"]):
            satirlar[0]["etiket"] = "GENEL TOPLAM"
        cetvel_uygulanmayan = cetvel_uygula(satirlar, cfg)
        satirlar, eksik_il, ilsiz = E.tiplendir(satirlar, il_ad, ilce_kume, tablo)
        kayitlar = []
        for s in satirlar:
            oy, kontrol, duz = E.dogrula(s["v"], cfg["partiler"])
            yapisal = None
            if kontrol["durum"] != "tutarli" and s["tokSol"]:
                v2 = E.yapisal_oku(s, cfg)
                if v2:
                    oy2, kontrol2, duz2 = E.dogrula(v2, cfg["partiler"])
                    if kontrol2["durum"] == "tutarli":
                        yapisal = {"sutunOkumasi": {k: x for k, x in s["v"].items() if k in cfg["partiler"] or k in ONCU},
                                   "not": "sütun kenarı okuması tutarsızdı; sayı parçaları katılım/yüzde/toplam kısıtlarıyla yeniden ayrıştırıldı"}
                        s = dict(s, v=v2)
                        oy, kontrol, duz = oy2, kontrol2, duz2
            goruntu = None
            if kontrol["durum"] != "tutarli" or kontrol.get("katilimUyumsuz"):
                v3 = goruntu_oku(pdf, cfg, s)
                if v3:
                    v3 = cetvel_gec(v3, s, cetvel_uygulanmayan, cfg)
                    oy3, kontrol3, duz3 = E.dogrula(v3, cfg["partiler"])
                    if kontrol3["durum"] == "tutarli" and not kontrol3.get("katilimUyumsuz"):
                        goruntu = {"metinKatmani": {k: x for k, x in s["v"].items() if k in cfg["partiler"] or k in ONCU},
                                   "not": "metin katmanı tutarsızdı; hücreler sayfa görüntüsünden (tesseract) ayrıca okundu, "
                                          "her parti oyu kitabın yüzdesiyle seçildi, satır toplam ve yüzdelerle tutuyor"}
                        s = dict(s, v=v3)
                        oy, kontrol, duz = oy3, kontrol3, duz3
            v = s["v"]
            r = {"tip": s["tip"], "plaka": s["plaka"], "adKaynakta": s["etiket"], "ustIlce": s["ustIlce"],
                 "sandik": v.get("sandik"), "secmen": v.get("secmen"), "oyKullanan": v.get("oyKullanan"),
                 "katilim": v.get("katilim%"), "gecerliOy": kontrol.pop("gecerliOy", v.get("gecerliOy")),
                 "oy": dict(sorted(oy.items(), key=lambda kv: -kv[1])),
                 "yuzde": {p: v[p + "%"] for p in cfg["partiler"] if isinstance(v.get(p + "%"), float) and v[p + "%"]},
                 "kontrol": kontrol, "sayfa": s["sayfa"]}
            if duz:
                r["ocrDuzeltme"] = duz
            if yapisal:
                r["yapisalOkuma"] = yapisal
            if goruntu:
                r["goruntuOkuma"] = goruntu
            if s.get("cetvel"):
                r["cetvelDuzeltme"] = s["cetvel"]
            if s["karakterDuzeltme"]:
                r["karakterDuzeltme"] = [f"{a}→{b}" for a, b in s["karakterDuzeltme"]]
            if s["sagYok"]:
                r["kontrol"]["sagSayfaEslesmedi"] = True
            r["kazanan"] = next(iter(r["oy"]), None)
            kayitlar.append(r)
        for r in kayitlar:
            katilim_duzelt(r)
        if tablo == "il_genel_meclisi":
            adlandirma = ilce_adlandir(kayitlar, cfg)
            for c in yerel_adlarina_cevir(kayitlar, secim):
                print("  ad:", *c)
        else:
            adlandirma = belediye_kimlik(kayitlar, secim)
        say = lambda f: sum(1 for r in kayitlar if f(r))  # noqa: E731
        veri = {
            "secim": secim, "tablo": tablo, "aciklama": E.TABLO_ACIKLAMA[tablo],
            "kaynak": {"ana": "tuik", "yayin": cfg["yayin"], "demirbas": cfg["demirbas"],
                       "url": f"https://kutuphane.tuik.gov.tr/pdf/{cfg['demirbas']}.pdf",
                       "ham": f"data/raw/tuik/mahalli-kitap/{cfg['demirbas']}.pdf", "sayfalar": [ilk, son],
                       "okuyucu": "scripts/pipelines/tuik_arsiv/extract_mahalli_1963_1977.py",
                       "not": "DİE kitabındaki değerler ilçe seçim kurullarının birleştirme tutanaklarından (kitabın açıklaması)."},
            "partiler": cfg["partiler"],
            "ozet": {"satir": len(kayitlar), **{t: say(lambda r, t=t: r["tip"] == t) for t in ("il", "ilce", "belde")},
                     "tutarli": say(lambda r: r["kontrol"]["durum"] == "tutarli"),
                     "tutarsiz": say(lambda r: r["kontrol"]["durum"] != "tutarli"),
                     "ocrDuzeltilen": say(lambda r: r.get("ocrDuzeltme")),
                     "yapisalOkunan": say(lambda r: r.get("yapisalOkuma")),
                     "goruntudenOkunan": say(lambda r: r.get("goruntuOkuma")),
                     "adlandirilan": say(lambda r: r.get("ad")),
                     "eksikIl": eksik_il, "ilSatiriTaramadaYok": ilsiz, "eslesmeyenSayfa": eslesmeyen,
                     "cetvelUygulanamayan": cetvel_uygulanmayan,
                     ("adlandirilamayanIller" if tablo == "il_genel_meclisi" else "baskanliktaEslesmeyenIlceler"): adlandirma},
            "satirlar": kayitlar,
        }
        G.onbellek_kaydet()
        (OUT / secim).mkdir(parents=True, exist_ok=True)
        (OUT / secim / f"{tablo}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
        oz = {k: v for k, v in veri["ozet"].items() if k not in ("eslesmeyenSayfa", "adlandirilamayanIller", "baskanliktaEslesmeyenIlceler", "cetvelUygulanamayan")}
        print(secim, tablo, oz, "| adlandırılamayan il / eşleşmeyen başkanlık ilçesi:", sum(len(v) if tablo != "il_genel_meclisi" else 1 for v in (adlandirma or {}).values()),
              "| eşleşmeyen sayfa:", len(eslesmeyen))


def main():
    secimler = [a for a in sys.argv[1:] if a in KITAPLAR] or list(KITAPLAR)
    tablolar = [a for a in sys.argv[1:] if a in E.TABLO_ACIKLAMA] or None
    for s in secimler:
        isle(s, tablolar)


if __name__ == "__main__":
    main()
