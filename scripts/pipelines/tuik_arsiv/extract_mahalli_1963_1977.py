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
P63 = ["AP", "CHP", "CKMP", "MP62", "TİP", "YTP61", "Bağımsız"]
P68 = ["AP", "BP69", "CHP", "CKMP", "CGP", "MP62", "TİP", "YTP61", "Bağımsız"]
ONCU68 = ["sandik", "secmen", "oyKullanan", "gecerliOy", "katilim%"]
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
    "1963yerel": {
        # il fasikulleri (A baskanlik, B belediye meclisi, C il genel meclisi, D muhtarlik); her tablo karsilikli
        # iki sayfa: sol ad, 1960 nufusu, sandik, secmen, oy kullanan; sag muteber (gecerli) oy ve partiler.
        # Yuzde ve katilim basilmamis: tek denetim parti toplami == gecerli oy. Kitap iki parca (kitap_birlestir).
        # Yanlis-Dogru Cetveli (s.5): basliklarda AP/CHP sirasi duzeltmeleri (veri sirasi AP, CHP; okuma konumla
        # oldugu icin etkisiz) ve Malatya 44/6 il genel meclisi sol sayfa (kod -> PDF sayfasi calisirken bulunur).
        "demirbas": "0015160", "tarih": "17 Kasım 1963",
        "yayin": "DİE, Mahalli Seçimler Sonuçları, 17 Kasım 1963 (yayın no. 474, 1965)",
        "duzen": "karsilikli", "partiler": P63, "genelIlce": "1965", "binlikBosluk": True,
        "sol": ["nufus", "sandik", "secmen", "oyKullanan"], "sag": ["gecerliOy"] + P63,
        "tablolar": {"il_genel_meclisi": "G", "belediye_meclisi": "M"},
        "cetvelKod": {"44/6": [{"satir": 1, "yanlis": 17475, "dogru": 174715}, {"satir": 2, "yanlis": 31487, "dogru": 61487},
                               {"satir": 3, "yanlis": 20795, "dogru": 10795}, {"satir": 8, "yanlis": 18264, "dogru": 18624}]},
    },
    "1968yerel": {
        # il fasikulleri (her ilde A il genel meclisi, B baskanlik, C belediye meclisi, D muhtarlik); tablolar tek
        # yuz (yatay sayfa). Il genel meclisinde her parti oy + %, belediye meclisinde yalniz oy. Ilce satiri
        # "NN Ad" (ilce kodu, kitap sirasi), belde satiri "B.KKK Ad" (bucak.koy kodu). Guven Partisi projede CGP.
        "demirbas": "0015244", "tarih": "2 Haziran 1968",
        "yayin": "DİE, Mahalli Seçimler Sonuçları, 2 Haziran 1968 (yayın no. 555, 1969)",
        "duzen": "fasikul", "partiler": P68, "genelIlce": "1969", "binlikBosluk": True,
        "sutunlar": {"il_genel_meclisi": ONCU68 + [x for p in P68 for x in (p, p + "%")],
                     "belediye_meclisi": ONCU68 + P68},
        "tablolar": {"il_genel_meclisi": "G", "belediye_meclisi": "M"},
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


def kelime_duzelt(w):
    """extract_mahalli.kelime_duzelt + kalin satirda her rakamin UC kez yazilmasi ('111333999' -> '139'). Binligi
    bosluklu kitapta 4+ haneli parca olamaz; 6+ karakterli tamamen uclu parca yalniz bu OCR hatasi olabilir."""
    t = w["text"]
    if E.BINLIK_BOSLUK and len(t) >= 6 and len(t) % 3 == 0 and re.fullmatch(r"[\d.,]+", t) and t[0::3] == t[1::3] == t[2::3]:
        return t[0::3]
    return E.kelime_duzelt(w)


def pdf_yolu(cfg):
    """Kitabin PDF'i (bolunmus kitap .cache'te birlestirilir: kitap_birlestir.py)."""
    from kitap_birlestir import kitap_yolu
    return pathlib.Path(kitap_yolu(cfg["demirbas"]))


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
        y = kelime_duzelt(w)
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
        L, k = die_tablo.sayfa_tablosu(page, 160, n, None, kelime_duzelt=kelime_duzelt, etiket_zorunlu=False, **ek)
        if L is None:
            return None, k
        satir = []
        i_s, i_m = cfg["sol"].index("sandik"), cfg["sol"].index("secmen")
        L = [(e, v, y, h, (v[i_s], v[i_m])) for e, v, y, h in L]
        ilk_y = min((y for e, v, y, h, (a, b) in L if isinstance(a, int) and isinstance(b, int) and b >= max(a, 50)),
                    default=None)
        for e, v, y, h, (a, b) in L:
            # veri satiri: sandik ve secmen tam sayi, secmen >= sandik (baslik/sayfa no satirlari elenir). Metin
            # katmani bozuk satir (ad okunur ya da en az 3 hucre sayi, ilk veri satirinin altinda) de alinir:
            # degerleri goruntuden ikinci okumayla bulunur, tutmazsa satir dogrulanmamis kalir.
            if isinstance(a, int) and isinstance(b, int) and b >= max(a, 50):
                satir.append({"etiket": e, "v": dict(zip(cfg["sol"], v)), "y": y, "ham": h})
            elif ilk_y is not None and y > ilk_y + 3 and b != 0 and (
                    re.search(r"[^\W\d_]{3,}", e or "") or
                    (sum(isinstance(x, int) for x in v) >= 3 and any(isinstance(x, int) and x for x in v[i_m:i_m + 2]))):
                # secmen 0: kitapta (*) dipnotlu, secim yapilmayan birim (Bozcaada, Gokceada); adsiz ve secmen /
                # oy kullanan okunmayan parca: bolunmus satirin artigi
                satir.append({"etiket": e, "v": dict(zip(cfg["sol"], v)), "y": y, "ham": h, "bozuk": True})
        return satir, k
    R, k = die_tablo.sayfa_tablosu(page, 120, n, None, etiketsiz=True, kelime_duzelt=kelime_duzelt, **ek)
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


def fasikul_sayfalari(cfg):
    """Il fasikulu kitabinda (1968) her ilin tablo sayfalari: {plaka: {"G": [...], "B": [...], "M": [...]}}.
    Sayfa turu basliktan (pdftotext; .cache/tuik/<demirbas>.txt): G il genel meclisi, B belediye baskanligi, M
    belediye meclisi, u muhtarlik. Il, fasikulun ilk (G) sayfasindaki "NN — IL" basligindan; okunmazsa sira."""
    yol = ROOT / ".cache" / "tuik" / f"{cfg['demirbas']}.txt"
    if not yol.exists():
        yol.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        subprocess.run(["pdftotext", "-layout", str(pdf_yolu(cfg)), str(yol)], check=True)
    sayfalar = yol.read_text(encoding="utf-8").split("\f")
    tr = str.maketrans("İŞÜÖÇĞ", "ISUOCG")
    turler = []
    for p in sayfalar:
        h = re.sub(r"\s+", " ", p[:1200]).upper().translate(tr)
        turler.append("G" if re.search(r"G ?E ?N ?E ?L ?M ?E ?C ?L", h) else
                      "M" if re.search(r"M ?E ?C ?L ?I ?S ?I ?U ?Y ?E ?L ?E ?R", h) else
                      "B" if re.search(r"B ?A ?S ?K ?A ?N", h) else "u" if re.search(r"M ?U ?H ?T ?A ?R", h) else ".")
    out, plaka = {}, 0
    for i, (tur, p) in enumerate(zip(turler, sayfalar), 1):
        if tur == "G" and re.search(r"(?:^|\s)(\d\s*\d)\s*[—–-]+\s*[A-ZÇĞİÖŞÜ]", p[:1500]):
            m = re.search(r"(?:^|\s)(\d\s*\d)\s*[—–-]+\s*[A-ZÇĞİÖŞÜ]", p[:1500])
            kod = int(re.sub(r"\s", "", m.group(1)))
            plaka = kod if kod == plaka + 1 else plaka + 1
            out[plaka] = {"G": [i], "B": [], "M": []}
        elif plaka and tur in ("B", "M"):
            out[plaka][tur].append(i)
    return out


KOD = re.compile(r"^\s*(\d{1,2})\s+(?=\D)|^\s*(\d)\s*[.,]\s*(\d{3})\b")


def tablo_oku_fasikul(pdf, cfg, tur):
    """Tek yuzlu fasikul tablolari: her ilin sayfalari; satir etiketi bastaki koddan ayrilir (kod: 'NN' ilce,
    'B.KKK' belde). Ilk satir il toplami. Sutun kenarlari sayfanin kendisinden; bulunamazsa ya da satirlarin
    cogu tutarsizsa en iyi sayfanin kenarlari olcek+kaydirmayla oturtulur (kenar_uydur)."""
    fas = fasikul_sayfalari(cfg)
    n = len(cfg["sol"])
    secenek = {}
    for pl, d in fas.items():
        for no in d[tur]:
            secenek[no] = yuz_secenekleri(pdf.pages[no - 1], cfg, True, None)
    en_iyi = (-1, None)
    for no, so in secenek.items():
        if so and len(so[0][0]) >= 6:
            oran = sum(1 for s in so[0][0] if E.dogrula(s["v"], cfg["partiler"])[1]["durum"] == "tutarli") / len(so[0][0])
            if oran > en_iyi[0]:
                en_iyi = (oran, so[0][1])
    sablon = en_iyi[1]
    satirlar, eslesmeyen = [], []
    for pl, d in sorted(fas.items()):
        if not d[tur]:
            eslesmeyen.append({"plaka": pl, "neden": "fasikülde bu tablonun sayfası bulunamadı"})
            continue
        ilk = True
        for no in d[tur]:
            pg = pdf.pages[no - 1]
            so = yuz_secenekleri(pg, cfg, True, sablon)
            if not so:
                eslesmeyen.append({"sayfa": no, "neden": "sütunlar bulunamadı"})
                continue
            sol, kl, _ = max(so, key=lambda x: (sum(1 for s in x[0] if E.dogrula(s["v"], cfg["partiler"])[1]["durum"] == "tutarli"), len(x[0])))
            ts = E._sayfa_tokenleri(pg, True)
            kd = E._duzeltmeler(pg)
            words = pg.extract_words()
            for sira, s in enumerate(sorted(sol, key=lambda s: s["y"]), 1):
                # satirin solundaki kod (etiketten once; sayi oldugu icin etikete girmez)
                sol_w = sorted((w for w in words if abs(w["top"] - s["y"]) < 4 and w["x1"] < 130), key=lambda w: w["x0"])
                bas = " ".join(w["text"] for w in sol_w)
                m = KOD.match(bas)
                kod = (m.group(1) if m and m.group(1) else f"{m.group(2)}.{m.group(3)}") if m else None
                etiket = re.sub(r"[.…\s]{2,}$", "", s["etiket"] or "").strip(" .")
                tip = "il" if ilk else ("ilce" if kod and "." not in kod else "belde" if kod else None)
                ilk = False
                satirlar.append({"etiket": etiket, "kod": kod, "tipOn": tip, "plaka": pl, "v": s["v"],
                                 "sagYok": False, "sayfa": [no], "sira": sira,
                                 "karakterDuzeltme": [(tt, yy) for y_, tt, yy in kd if abs(y_ - s["y"]) < 5],
                                 "tokSol": ts.get(s["y"]), "tokSag": None, "kenarSol": kl, "kenarSag": None,
                                 "ySol": s["y"], "ySag": None})
    return satirlar, eslesmeyen


def karsilikli_ciftler(cfg, tur):
    """1963: tur ('G' il genel meclisi, 'M' belediye meclisi) tablosunun sol sayfalari (basliktan) ve hemen
    ardindaki sag sayfa, PDF sirasinda. Il, satirlardaki il toplami etiketinden (tiplendir)."""
    yol = ROOT / ".cache" / "tuik" / f"{cfg['demirbas']}.txt"
    if not yol.exists():
        yol.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        subprocess.run(["pdftotext", "-layout", str(pdf_yolu(cfg)), str(yol)], check=True)
    sayfalar = yol.read_text(encoding="utf-8").split("\f")
    tr = str.maketrans("İŞÜÖÇĞÎ", "ISUOCGI")
    out = []
    for i, p in enumerate(sayfalar, 1):
        h = re.sub(r"\s+", " ", p[:900]).upper().translate(tr)
        k = ("G" if re.search(r"I ?L ?G ?E ?N ?E ?L", h) else
             "M" if re.search(r"B ?E ?L ?E ?D ?I ?Y ?E ?M ?E ?C ?L", h) else "")
        if k == tur and i > 8:
            out.append((i, i + 1))
    return out


def sayfa_kodu_bul(cfg, kod):
    """Fasikul sayfa kodunu ('44/6') tasiyan PDF sayfasi (sayfanin ust kismi)."""
    yol = ROOT / ".cache" / "tuik" / f"{cfg['demirbas']}.txt"
    il, no = kod.split("/")
    for i, p in enumerate(yol.read_text(encoding="utf-8").split("\f"), 1):
        if re.search(rf"(?<!\d){il}\s*/\s*{no}(?!\d)", p[:700]):
            return i
    return None


def tablo_oku_karsilikli(pdf, cfg, tur):
    """1963 karsilikli sayfalar: sol yuz satirlari (ad + kimlik sutunlari) ile sag yuz satirlari (sonuc) dikey
    konumla eslenir: iki yuzun baslik satiri farki kadar kaydirilmis y, en yakin satir (4 pt icinde, karsilikli
    tek). Eslesme denetimi: gecerli oy, oy kullanandan buyuk olamaz. Ad iki satira bolunmusse ('Adana Sehir,
    Bucak ve' / 'Koyleri Toplami') ust satir eklenir."""
    ciftler = karsilikli_ciftler(cfg, tur)
    satirlar, eslesmeyen = [], []
    sablon_sol = sablon_sag = None
    en_iyi = -1
    for a, b in ciftler:
        so, sa = yuz_secenekleri(pdf.pages[a - 1], cfg, True, None), yuz_secenekleri(pdf.pages[b - 1], cfg, False, None)
        if so and sa and len(sa[0][0]) >= 6:
            oran = sum(1 for r in sa[0][0] if E.dogrula(r["v"], cfg["partiler"])[1]["durum"] == "tutarli") / len(sa[0][0])
            if oran > en_iyi:
                en_iyi, sablon_sol, sablon_sag = oran, so[0][1], sa[0][1]
    for a, b in ciftler:
        L, R = pdf.pages[a - 1], pdf.pages[b - 1]
        so = yuz_secenekleri(L, cfg, True, sablon_sol)
        sa = yuz_secenekleri(R, cfg, False, sablon_sag)
        if not so or not sa:
            eslesmeyen.append({"sayfa": [a, b], "neden": "sütunlar bulunamadı"})
            continue
        dy = baslik_farki(L, R) or 0.0
        en = None
        for sol, kl, _ in so:
            for sag, kr, _ in sa:
                hiza = []
                kullanilan = set()
                for s in sorted(sol, key=lambda s: s["y"]):
                    ad = sorted((abs(r["y"] - s["y"] - dy), j) for j, r in enumerate(sag) if j not in kullanilan)
                    r = None
                    if ad and ad[0][0] < 4 and (len(ad) < 2 or ad[1][0] >= 4):
                        r = sag[ad[0][1]]
                        g, k = r["v"].get("gecerliOy"), s["v"].get("oyKullanan")
                        if isinstance(g, int) and isinstance(k, int) and g > k:
                            r = None
                        else:
                            kullanilan.add(ad[0][1])
                    hiza.append((s, r))
                puan = (sum(1 for s, r in hiza if r and E.dogrula(r["v"], cfg["partiler"])[1]["durum"] == "tutarli"),
                        sum(1 for s, r in hiza if r))
                if en is None or puan > en[0]:
                    en = (puan, hiza, kl, kr)
        _, hiza, kl, kr = en
        words = L.extract_words()
        ts, tr_ = E._sayfa_tokenleri(L, True), E._sayfa_tokenleri(R, False)
        for sira, (s, r) in enumerate(hiza, 1):
            etiket = s["etiket"] or ""
            if re.match(r"^\W*(K\s*[öo]\s*y|TOPLAM)", etiket, re.I):
                ust = sorted((w for w in words if 3 < s["y"] - w["top"] < 16 and w["x1"] < 260
                              and not re.fullmatch(r"[\d.,]+", w["text"])), key=lambda w: w["x0"])
                etiket = " ".join(w["text"] for w in ust) + " " + etiket
            satirlar.append({"etiket": etiket.strip(), "v": {**s["v"], **(r["v"] if r else {})}, "sagYok": r is None,
                             "sayfa": [a, b], "sira": sira, "karakterDuzeltme": [],
                             "tokSol": ts.get(s["y"]), "tokSag": tr_.get(r["y"]) if r else None,
                             "kenarSol": kl, "kenarSag": kr, "ySol": s["y"],
                             "ySag": r["y"] if r else s["y"] + dy})
    return satirlar, eslesmeyen


def fasikul_tiplendir(satirlar, tablo):
    """Fasikul satirlarina tip / ust ilce: il toplami, kodlu ilce satiri; belediye meclisinde kodsuz satir
    sayfadaki konumuna gore belde (kimlik sonra baskanlik kaydiyla kurulur)."""
    ust = None
    for s in satirlar:
        tip = s["tipOn"]
        if tip is None:
            tip = "ilce" if tablo == "il_genel_meclisi" else "belde"
        if tip == "il":
            ust = None
        elif tip == "ilce":
            ust = s["etiket"]
        s.update(tip=tip, ustIlce=ust if tip == "belde" else None)
    return satirlar


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
    """Okunan ad (bos/kisa: tutar sayilir) ilce adiyla ya da parantez icindeki diger adiyla ('Sinanpasa
    (Sincanli)' <- 'Sincanli') ayni ya da benzer (>= 0,75)."""
    o = E._anahtar(okunan)
    if len(o) < 3:
        return True
    adlar = [E._anahtar(ad)] + [E._anahtar(x) for x in re.findall(r"\(([^)]*)\)", ad or "")]
    return any(a and (o == a or E._benzer(o, a) >= 0.75) for a in adlar)


def _ad_ayni(okunan, ad):
    """Okunan ad (en az 3 harf) ilce adiyla ya da parantez icindeki adiyla birebir ayni (benzerlik degil)."""
    o = E._anahtar(okunan)
    return len(o) >= 3 and o in [E._anahtar(ad)] + [E._anahtar(x) for x in re.findall(r"\(([^)]*)\)", ad or "")]


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
         her satirin secmeni sirasindaki ilcenin genel secim secmeninden en fazla %20 sapiyor (adi kitapta birebir
         okunan satir bu sapmadan muaf).
      2. secmen (sira tutmazsa; buyuksehirlerde merkez ilceler basta, Canakkale'de Imroz/Bozcaada satiri yok):
         adi okunan satir once adla (birebir ad: sapmadan muaf; benzer ad: sapma <= %10), kalanlar
         genel secim secmeni en yakin ilceye; eslesme karsilikli ve tek, sapma <= %10, ikinci aday en az
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
            # kitapta adi birebir okunan satir secmen sapmasindan muaf (1973 Kozan: kitap secmeni 344 227 basmis,
            # il toplami da onunla tutuyor; 1973 Cankaya: yerel secmen genel secimden %21 az)
            if len(ref) == len(satirlar) and all(
                    _ad_ayni(r["adKaynakta"], ad) or (
                        (_ad_tutar(r["adKaynakta"], ad) or _sapma(r["secmen"], sec.get(ad)) < 0.05)
                        and _sapma(r["secmen"], sec.get(ad)) <= SIRA_SAPMA) for r, ad in zip(satirlar, ref)):
                atama, yontem = list(zip(satirlar, ref)), "sira"
            else:
                # once adi okunabilen satirlar: adi tek bir ilceyle tutan ve secmeni o ilceden <= %10 sapan satir
                # o ilceye; kalanlar kalan ilcelere secmenle
                aday, kalan = {}, dict(sec)
                for i, r in enumerate(satirlar):
                    tutan = [ad for ad in sec if len(E._anahtar(r["adKaynakta"])) >= 3 and _ad_tutar(r["adKaynakta"], ad)]
                    if len(tutan) == 1 and tutan[0] in kalan and (
                            _ad_ayni(r["adKaynakta"], tutan[0]) or _sapma(r["secmen"], sec[tutan[0]]) <= SECMEN_SAPMA):
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
        if not atama and il:
            # blok bir butun olarak adlandirilamadi (toplam tutmadi ya da bir satir baglanamadi): yalniz dogrulanmis
            # satirlar tek tek baglanir (ad-oncelikli, karsilikli tek, sapma <= %10, ikinci aday en az 3 puan uzak);
            # celisen satir adsiz
            uygun = [r for r in satirlar if r["kontrol"]["durum"] == "tutarli" and not r["kontrol"].get("katilimUyumsuz")]
            aday, kalan = {}, dict(sec)
            for r in uygun:
                tutan = [ad for ad in sec if len(E._anahtar(r["adKaynakta"])) >= 3 and _ad_tutar(r["adKaynakta"], ad)]
                if len(tutan) == 1 and tutan[0] in kalan and (
                        _ad_ayni(r["adKaynakta"], tutan[0]) or _sapma(r["secmen"], sec[tutan[0]]) <= SECMEN_SAPMA):
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
                rapor[p] = neden + [f"blok bir bütün olarak adlandırılamadı; {len(atama)}/{len(satirlar)} doğrulanmış satır "
                                    "adla ya da seçmenle tek tek bağlandı"]
                for r in satirlar:
                    r["kimlik"] = {"yontem": "cozulemedi", "neden": "; ".join(neden)}
        if cfg.get("duzen") == "fasikul":
            atama = kod_ile_tamamla(satirlar, atama or [], sec)
            if atama and yontem is None:
                yontem = "kod"
        if atama:
            for r, ad in atama:
                r["ad"] = ad
                if (r.get("kimlik") or {}).get("yontem") == "kod":
                    continue
                r["kimlik"] = {"yontem": yontem, "genelSecimSecmeni": sec.get(ad),
                               "not": "kitap sırası ve okunabilen adlar" if yontem == "sira"
                               else "genel seçim (aynı yıl) ilçe seçmeniyle karşılıklı tek eşleşme"}
        elif p not in rapor:
            rapor[p] = neden or ["adlandırılamadı"]
            for r in satirlar:
                r["kimlik"] = {"yontem": "cozulemedi", "neden": "; ".join(rapor[p])}
    return rapor


def kod_ile_tamamla(satirlar, atama, sec):
    """1968 fasikulu: ilce satiri kitapta 'NN Ad' (NN: kitap sirasi, 00 Merkez, sonra alfabe). Adi okunamayan ya da
    baglanamayan dogrulanmis satir, koduyla kitap sirasindaki ilceye baglanir; yalniz blokta adla baglanan her
    satirin kodu o sirayla tutuyorsa (liste ile kitap sirasi ayni) ve okunan ad (varsa) o ilceyle celismiyorsa."""
    ref = kitap_sirasi(list(sec))
    sira = {ad: i for i, ad in enumerate(ref)}
    adli = [(r, ad) for r, ad in atama if r.get("kodKaynakta") and "." not in r["kodKaynakta"]]
    if not adli or any(int(r["kodKaynakta"]) != sira.get(ad) for r, ad in adli):
        return atama
    alinan = {ad for _, ad in atama}
    bagli = {id(r) for r, _ in atama}
    yeni = list(atama)
    for r in satirlar:
        k = r.get("kodKaynakta")
        if id(r) in bagli or not k or "." in k or r["kontrol"]["durum"] != "tutarli" or int(k) >= len(ref):
            continue
        ad = ref[int(k)]
        if ad in alinan or not _ad_tutar(r["adKaynakta"], ad):
            continue
        r["kimlik"] = {"yontem": "kod", "not": f"kitaptaki ilçe kodu {k} = kitap sırasında {ad}"}
        yeni.append((r, ad))
        alinan.add(ad)
    return yeni


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


def cetvel_uygula(satirlar, cfg, ilk, son):
    """Kitabin Yanlis-Dogru Cetveli (DIE'nin kendi duzeltmesi) dogrulamadan ONCE uygulanir. Kayit: PDF sayfasi,
    sutun (yuzun kendi sutun sirasi, 1'den), satir. Hucre o sayfa + sutundaki degeri cetveldeki yanlis degere
    esit olan TEK satirda degistirilir (satir sayimi OCR'da kayabilir; deger eslesmesi esastir). Dondurur:
    uygulanamayan kayitlar."""
    kalan = []
    for no, kayitlar in cfg.get("cetvel", {}).items():
        if not ilk <= no <= son:
            continue
        for c in kayitlar:
            aday = []
            for s in satirlar:
                if no not in s["sayfa"]:
                    continue
                yuz = cfg["sol"] if no == s["sayfa"][0] else cfg["sag"]
                for alan in (yuz if c.get("sutun") is None else [yuz[c["sutun"] - 1]]):
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
        if c["sayfa"] not in s["sayfa"] or s.get("sira") != c["satir"] or c.get("sutun") is None:
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
    a, b = s["sayfa"][0], s["sayfa"][-1]
    if cfg["sag"] and s.get("ySag") is None:
        return None
    yuzdeli = all(p + "%" in cfg["sol"] + cfg["sag"] for p in cfg["partiler"])
    metin = {}
    for no, kenar, y, alanlar in ((a, s["kenarSol"], s["ySol"], cfg["sol"]), (b, s["kenarSag"], s["ySag"], cfg["sag"])):
        if not alanlar:
            continue
        if not kenar or not all(isinstance(x, float) for x in kenar):
            return None
        pg = pdf.pages[no - 1]
        img = G.goruntu(str(pdf_yolu(cfg)), no, str(PNG / cfg["demirbas"]))
        donusum = G.kayma(pg, img, (cfg["demirbas"], no), PNG / cfg["demirbas"] / f"{no:04d}.png")
        if donusum is None:
            return None
        metin.update(zip(alanlar, G.satir_metinleri(img, pg, kenar, y, donusum)))
    tv = s["v"]
    if not yuzdeli:
        # yuzdesiz tablo (1968 belediye meclisi): iki okumanin ortak degerleri, en fazla bir hucre toplamla
        adaylar = {x for x in G.sayi_adaylari(metin.get("gecerliOy")) + [tv.get("gecerliOy")] if isinstance(x, int) and x > 0}
        tutan = [v for v in (G.coz_yuzdesiz(metin, cfg["partiler"], tv, g) for g in sorted(adaylar)) if v
                 and E.dogrula(v, cfg["partiler"])[1]["durum"] == "tutarli"]
        if len(tutan) != 1:
            return None
        v = tutan[0]
        if "katilim%" not in cfg["sol"]:
            # 1963: katilim basilmamis, secmen / oy kullanan denetlenemez; metin katmaninin okudugu (sonra akla
            # yatkinlik: gecerli <= oy kullanan <= secmen)
            v.update({k: tv.get(k) for k in ("sandik", "secmen", "oyKullanan")})
            return v if isinstance(v.get("gecerliOy"), int) else None
        if not all(isinstance(v.get(k), int) for k in ("secmen", "oyKullanan", "gecerliOy")) or not isinstance(v.get("katilim%"), float):
            return None
        return v
    oncu_ok = not E.dogrula(tv, cfg["partiler"])[1].get("katilimUyumsuz") and all(
        isinstance(tv.get(k), int) for k in ("secmen", "oyKullanan", "gecerliOy")) and \
        isinstance(tv.get("katilim%"), float) and tv["secmen"] and abs(100 * tv["oyKullanan"] / tv["secmen"] - tv["katilim%"]) <= 0.1
    if oncu_ok:
        v = G.coz(metin, cfg["partiler"], ONCU, tv["gecerliOy"], yedek=tv)
        v.update({k: tv.get(k) for k in ONCU})
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
    pdf = die_tablo.ac(pdf_yolu(cfg))
    G.onbellek_ac(PNG.parent / f"ocr_{cfg['demirbas']}.json")
    il_ad = E.il_adlari()
    ilce_kume = E.genel_ilceler(cfg["genelIlce"])
    for tablo, aralik in cfg["tablolar"].items():
        if tablolar and tablo not in tablolar:
            continue
        fasikul = cfg.get("duzen") == "fasikul"
        karsilikli = cfg.get("duzen") == "karsilikli"
        if fasikul:
            cfg = dict(KITAPLAR[secim], sol=KITAPLAR[secim]["sutunlar"][tablo], sag=[])
            satirlar, eslesmeyen = tablo_oku_fasikul(pdf, cfg, aralik)
            ilk, son = 0, 0
        elif karsilikli:
            satirlar, eslesmeyen = tablo_oku_karsilikli(pdf, cfg, aralik)
            ilk, son = 0, len(pdf.pages)
            cfg = dict(cfg, cetvel={})
            for kod, kayitlar in KITAPLAR[secim].get("cetvelKod", {}).items():
                no = sayfa_kodu_bul(cfg, kod)
                if no and any(no == s["sayfa"][0] for s in satirlar):
                    cfg["cetvel"][no] = [dict(c, sutun=None) for c in kayitlar]
        else:
            ilk, son = aralik
            satirlar, eslesmeyen = tablo_oku(pdf, cfg, ilk, son)
        # ilk satir (adsiz) Turkiye toplami
        if satirlar and not fasikul and not karsilikli and not E._anahtar(satirlar[0]["etiket"]):
            satirlar[0]["etiket"] = "GENEL TOPLAM"
        for s in satirlar:
            # kalin harfli satirda OCR her harfi iki kez yaziyor ("TTuunncceellii" -> "Tunceli")
            s["etiket"] = " ".join(w[0::2] if len(w) >= 4 and len(w) % 2 == 0 and w[0::2] == w[1::2] else w
                                   for w in (s["etiket"] or "").split())
            # 1973: il satiri "ADANA İL TOPLAMI" (tiplendir il adini birebir arar; OCR "tL", "1L"); 1963 "ADANA ÎLÎ
            # BELEDİYELERİ TOPLAMI", "Adana Şehir, Bucak ve Köyleri Toplamı" (ilce), "Bahçe Şehir" (ilce belediyesi)
            s["etiket"] = re.sub(r"\s+[İIÎi1lt|]\s*L\s*[İIÎi1l]?\s+BELED\S*\s+TOPLAM\w*\s*$", "", s["etiket"], flags=re.I)
            s["etiket"] = re.sub(r"\s+[İIÎi1lt|]\s*L\s+TOPLAM\w*\s*$", "", s["etiket"], flags=re.I)
            if karsilikli:
                s["etiket"] = re.sub(r"\s+[ŞS]\s*e\s*h\s*i\s*r\b.*$", "", s["etiket"], flags=re.I).strip(" ,.^")
        cetvel_uygulanmayan = cetvel_uygula(satirlar, cfg, ilk, son)
        if fasikul:
            satirlar, eksik_il, ilsiz = fasikul_tiplendir(satirlar, tablo), [], []
            eksik_il = sorted(set(range(1, 68)) - {s["plaka"] for s in satirlar if s["tip"] == "il"})
        else:
            satirlar, eksik_il, ilsiz = E.tiplendir(satirlar, il_ad, ilce_kume, tablo)
            if karsilikli and tablo == "il_genel_meclisi":
                # 1963: il merkezi ilcesi sehrin adiyla ("Adana Şehir, Bucak ve Köyleri Toplamı")
                for s in satirlar:
                    if s["tip"] == "ilce" and il_ad.get(E._anahtar(s["etiket"])) == s["plaka"]:
                        s["etiket"] = "Merkez"
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
            # kodu belde gosteren satir (1968 'B.KKK') haritada yok: goruntu okumasi (yavas) yapilmaz
            belde_kodlu = "." in (s.get("kod") or "")
            if (kontrol["durum"] != "tutarli" or kontrol.get("katilimUyumsuz")) and not belde_kodlu:
                v3 = goruntu_oku(pdf, cfg, s)
                okunan_goruntu = locals().get("okunan_goruntu", 0) + 1
                if okunan_goruntu % 25 == 0:
                    G.onbellek_kaydet()  # uzun calismada kesilirse tesseract sonuclari kaybolmasin
                if v3:
                    v3 = cetvel_gec(v3, s, cetvel_uygulanmayan, cfg)
                    oy3, kontrol3, duz3 = E.dogrula(v3, cfg["partiler"])
                    if kontrol3["durum"] == "tutarli" and not kontrol3.get("katilimUyumsuz"):
                        goruntu = {"metinKatmani": {k: x for k, x in s["v"].items() if k in cfg["partiler"] or k in ONCU},
                                   "not": "metin katmanı tutarsızdı; hücreler sayfa görüntüsünden (tesseract) ayrıca okundu, "
                                          + ("her parti oyu kitabın yüzdesiyle seçildi, satır toplam ve yüzdelerle tutuyor"
                                             if all(p + "%" in cfg["sol"] + cfg["sag"] for p in cfg["partiler"]) else
                                             "her hücre iki okumanın ortak değeri (kitapta parti yüzdesi yok), en fazla bir "
                                             "hücre satır toplamıyla seçildi")}
                        s = dict(s, v=v3)
                        oy, kontrol, duz = oy3, kontrol3, duz3
            v = s["v"]
            r = {"tip": s["tip"], "plaka": s["plaka"], "adKaynakta": s["etiket"], "ustIlce": s["ustIlce"],
                 "sandik": v.get("sandik"), "secmen": v.get("secmen"), "oyKullanan": v.get("oyKullanan"),
                 "katilim": v.get("katilim%"), "gecerliOy": kontrol.pop("gecerliOy", v.get("gecerliOy")),
                 "oy": dict(sorted(oy.items(), key=lambda kv: -kv[1])),
                 "yuzde": {p: v[p + "%"] for p in cfg["partiler"] if isinstance(v.get(p + "%"), float) and v[p + "%"]},
                 "kontrol": kontrol, "sayfa": s["sayfa"]}
            if s.get("kod"):
                r["kodKaynakta"] = s["kod"]
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
            if "katilim%" not in cfg["sol"]:
                g, k, s_ = r.get("gecerliOy"), r.get("oyKullanan"), r.get("secmen")
                if not (isinstance(g, int) and isinstance(k, int) and isinstance(s_, int) and g <= k <= s_):
                    # 1963: katilim basilmamis; secmen / oy kullanan ancak gecerli <= oy kullanan <= secmen ise
                    if s_ is not None or k is not None:
                        r["secmenOkunan"] = {"secmen": s_, "oyKullanan": k}
                    r["secmen"] = r["oyKullanan"] = None
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
