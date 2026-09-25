"""
Taranmis (OCR metinli) DIE secim tablolari icin yeniden kullanilabilir,
DOGRULAMALI okuma katmani. Kitaba ozel olan tek sey yapilandirma (sutunlar,
partiler, sayfa araliklari); okuma, esleme ve dogrulama burada.

Ilkeler (kullanici karari, 2026-09-25):
  - Veri TAHMIN EDILMEZ. Bir hucre okunamiyorsa ya da kisitlarla dogrulanamiyorsa
    deger oldugu gibi (ya da bos) birakilir ve isaretlenir; toplamdan/yuzdeden
    geri hesaplanan deger YAZILMAZ.
  - Her alanin nasil dogrulandigi alan bazinda kaydedilir (`dogrulama`), OCR'in
    karakter duzeyindeki her donusumu kaydedilir (`karakter`).
  - Satir durumu:
      tutarli             parti oylari toplami = gecerli oy VE kitaptaki her
                          yuzde ile uyumlu VE katilim uyumlu
      toplamTutarli       toplam tutuyor ama en az bir yuzde/katilim uyumsuz
                          (yuzde hucresinin kendi OCR hatasi olabilir)
      yuzdelerTutarli     her dolu parti hucresi yuzdesiyle uyumlu ama toplam
                          tutmuyor (kaynagin kendi tutarsizligi ya da bos okunan hucre)
      tutarsiz            digerleri

Tablo bicimi (1989-1999 DIE mahalli kitaplari): her kayit iki satir - sayi
satiri (sandik, secmen, oy kullanan, gecerli, parti oylari) ve altinda yuzde
satiri (katilim, parti yuzdeleri; yuzdeler ayni sutunun altinda). Tablo iki
yuzlu: sol sayfa ad + ilk partiler, sag sayfa kalan partiler (etiketsiz).
"""
import collections
import re

import die_tablo

TIRE_BENZERI = {"•", "·", "_", "—", "–", "-", ".", "..", "...", "*", "'", "‘", "’", "~", "―"}
HARF_RAKAM = {"*": "4", "«": "4", "A": "4", "S": "5", "s": "5", "$": "5", "O": "0", "o": "0", "Q": "0",
              "D": "0", "I": "1", "l": "1", "ı": "1", "i": "1", "|": "1", "!": "1", "Z": "2", "z": "2",
              "B": "8", "G": "6", "b": "6", "g": "9", "İ": "1"}


def _cift(t):
    """Kalin puntoda her karakter iki kez: 'KKüüççüükk' -> 'Küçük', '776655' -> '765'."""
    if len(t) >= 4 and len(t) % 2 == 0 and t[0::2] == t[1::2]:
        return t[0::2]
    return None


def kelime_normal(w):
    """OCR kelimesi -> normal metin (None: degisiklik yok). Yalniz kesin
    donusumler: tire benzerleri, cift yazilmis karakterler, rakam agirlikli
    kelimelerde harf/rakam karisikligi (en fazla 1 harf)."""
    t = w["text"]
    if t in TIRE_BENZERI or re.fullmatch(r"[._•·]{1,4}", t):
        return "-"
    c = _cift(t)
    if c:
        t = c
    rakam = sum(ch.isdigit() for ch in t)
    if rakam and re.fullmatch(r"[\d.,]*[^\d.,\s]?[\d.,]*", t) and sum(ch.isalpha() for ch in t) <= 1:
        t2 = "".join(HARF_RAKAM.get(ch, ch) for ch in t)
        t2 = re.sub(r"[^\d.,]", "", t2)
        if t2 and t2 != w["text"]:
            return t2
    return t if t != w["text"] else None


def sayfa(page, sutunlar, sol, kenar=None, zorla=False):
    """Sayfanin satirlari: [{etiket, v{sutun: deger}, y, ham, karakter[]}], kenarlar."""
    words_cache = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    degisen = [(w["top"], w["text"], kelime_normal(w)) for w in words_cache]
    degisen = [(y, a, b) for y, a, b in degisen if b is not None and b != a]
    rows, kenarlar = die_tablo.sayfa_tablosu(page, 160, len(sutunlar), None, etiketsiz=not sol,
                                             kelime_duzelt=kelime_normal, hazir_kenarlar=kenar,
                                             etiket_zorunlu=False, kenar_zorla=zorla)
    if rows is None:
        return None, kenarlar
    out = []
    for e, vals, y, ham in rows:
        etiket = " ".join(_cift(p) or p for p in e.split()).strip(" .'`•*")
        if re.match(r"^\W*(TABL[OE]|\d+\.\s*(Belediyelere|Results|İl ve|Büyükşehir))", etiket):
            continue
        out.append({"etiket": etiket, "v": dict(zip(sutunlar, vals)), "y": y, "ham": ham,
                    "karakter": [f"{a}→{b}" for yy, a, b in degisen if abs(yy - y) < 5 and a not in TIRE_BENZERI]})
    return out, kenarlar


def _yuzde_satiri_mi(r):
    dolu = [x for x in r["v"].values() if x is not None]
    return bool(dolu) and any(isinstance(x, float) for x in dolu) and all(
        (isinstance(x, float) and x <= 100) or x == 0 for x in dolu)


def kayitlar(satirlar, yuzdeli):
    """Sayi satiri + hemen altindaki yuzde satiri = kayit. yuzdeli: yuzdesi
    olan sutunlar (orn. oyKullanan -> katilim, partiler)."""
    out, i = [], 0
    while i < len(satirlar):
        r = satirlar[i]
        if _yuzde_satiri_mi(r):
            i += 1  # basi kopuk yuzde satiri (onceki sayfadan) - atla
            continue
        k = {"etiket": r["etiket"], "v": {s: x for s, x in r["v"].items() if not isinstance(x, float)},
             "y": r["y"], "ham": r["ham"], "karakter": list(r["karakter"]), "yuzde": {}}
        if i + 1 < len(satirlar) and _yuzde_satiri_mi(satirlar[i + 1]) and satirlar[i + 1]["y"] - r["y"] < 16:
            y = satirlar[i + 1]
            k["yuzde"] = {s: x for s, x in y["v"].items() if s in yuzdeli and x is not None}
            k["karakter"] += y["karakter"]
            k["yuzdeHam"] = y["ham"]
            i += 2
        else:
            i += 1
        out.append(k)
    return out


def _uyar(o, y, g, tol=0.1):
    return g and abs(100 * o / g - y) <= tol


def puan(sol, sag, partiler):
    """Sol ve sag kaydin ayni birime ait olma puani (sag yuzdeler soldaki gecerli oya uyuyor mu)."""
    g = sol["v"].get("gecerliOy")
    if not isinstance(g, int) or g <= 0:
        return -1.0
    p, bilgi = 0.0, False
    for parti in partiler:
        o, y = sag["v"].get(parti), sag["yuzde"].get(parti)
        if isinstance(o, int) and isinstance(y, float) and o > 0:
            bilgi = True
            p += 1.0 if _uyar(o, y, g, 0.15) else -0.7
    t = sum(x for x in list(sol["v"].values())[4:] + list(sag["v"].values()) if isinstance(x, int))
    if t == g:
        p += 2.0
    return p if bilgi or t == g else 0.05


def hizala(sol, sag, partiler):
    """Sira koruyan en iyi esleme (DP)."""
    n, m = len(sol), len(sag)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            s = puan(sol[i], sag[j], partiler)
            dp[i][j] = max(dp[i + 1][j], dp[i][j + 1], dp[i + 1][j + 1] + s if s > 0 else -1e9)
    i = j = 0
    out = []
    while i < n:
        s = puan(sol[i], sag[j], partiler) if j < m else -1
        if j < m and s > 0 and dp[i][j] == dp[i + 1][j + 1] + s:
            out.append((sol[i], sag[j]))
            i, j = i + 1, j + 1
        elif j < m and dp[i][j] == dp[i][j + 1]:
            j += 1
        else:
            out.append((sol[i], None))
            i += 1
    return out


def dogrula(v, yuzde, partiler):
    """Deger DEGISTIRMEZ. Dondurur: (durum, alan_dogrulama{alan: [kanit...]}, ayrinti)."""
    dog = {}
    ayr = {}
    g = v.get("gecerliOy")
    s, k = v.get("secmen"), v.get("oyKullanan")
    kat = yuzde.get("oyKullanan")
    katilim_ok = None
    if isinstance(s, int) and isinstance(k, int) and isinstance(kat, float) and s:
        katilim_ok = _uyar(k, kat, s)
        if katilim_ok:
            dog["secmen"] = ["katilim"]
            dog["oyKullanan"] = ["katilim"]
        else:
            ayr["katilimUyumsuz"] = {"okunan": kat, "hesap": round(100 * k / s, 2)}
    if not isinstance(g, int) or g <= 0:
        return "gecerliOyOkunamadi", dog, ayr
    toplam, uymaz = 0, []
    for p in partiler:
        o, y = v.get(p), yuzde.get(p)
        if isinstance(o, int):
            toplam += o
        if isinstance(o, int) and o > 0 and isinstance(y, float):
            if _uyar(o, y, g):
                dog["oy." + p] = ["yuzde"]
            else:
                uymaz.append(p)
        elif (o in (0, None)) and isinstance(y, float) and y >= 0.1:
            uymaz.append(p)  # yuzde var ama oy bos/tire okunmus
    if toplam == g:
        dog.setdefault("gecerliOy", []).append("toplam")
        for p in partiler:
            if isinstance(v.get(p), int) and v[p] > 0:
                dog.setdefault("oy." + p, []).append("toplam")
    if sum(1 for p in partiler if "yuzde" in dog.get("oy." + p, [])) >= 2:
        dog.setdefault("gecerliOy", []).append("yuzde")
    if uymaz:
        ayr["yuzdeUyumsuz"] = uymaz
    if toplam != g:
        ayr["partiToplami"] = toplam
    if toplam == g and not uymaz and katilim_ok is not False:
        durum = "tutarli"
    elif toplam == g:
        durum = "toplamTutarli"
    elif not uymaz:
        durum = "yuzdelerTutarli"
    else:
        durum = "tutarsiz"
    return durum, dog, ayr


def _duzenli(k, tol=0.25):
    """Kenar araliklari tutarli mi (parti sutunlari esit genislikte dizili)."""
    if not k or not all(k):
        return False
    d = [b - a for a, b in zip(k, k[1:])]
    return all(x > 15 for x in d) and max(d) < 3.5 * min(d)


def sutun_sablonu(pdf, ciftler, sol_s, sag_s, ornek=40):
    """Kitap sablonu: (sol?, sayfa paritesi) -> kenarlar. Kenarlari DUZENLI
    cikan sayfalarin sutun bazinda medyani. Tek sayfanin 'temiz satir'
    medyani az satirli sayfada kayabiliyor (1994 s.309, s.415: iki sutun
    ust uste); sablon + ofset bunu onler."""
    toplu = collections.defaultdict(list)
    adim = max(1, len(ciftler) // ornek)
    for a, b in ciftler[::adim]:
        for no, sut, sol in ((a, sol_s, True), (b, sag_s, False)):
            _, k = sayfa(pdf.pages[no - 1], sut, sol)
            if _duzenli(k):
                toplu[(sol, no % 2)].append(k)
    return {key: [sorted(x[i] for x in ks)[len(ks) // 2] for i in range(len(ks[0]))] for key, ks in toplu.items() if ks}


def tablo(pdf, cfg, ilk, son, ozel_ciftler=()):
    """Sayfa ciftlerini oku, kayitlara bol, iki yuzu hizala. Dondurur:
    [{etiket, v, yuzde, sayfa, karakter, sagYok}], eslesmeyen sayfalar."""
    sol_s, sag_s = cfg["sol"], cfg["sag"]
    partiler = cfg["partiler"]
    yuzdeli = {"oyKullanan"} | set(partiler)
    ciftler = list(ozel_ciftler) or [(a, a + 1) for a in range(ilk, son, 2)]
    out, eslesmeyen = [], []
    sablon = sutun_sablonu(pdf, ciftler, sol_s, sag_s)
    for a, b in ciftler:
        L, kl = sayfa(pdf.pages[a - 1], sol_s, True, sablon.get((True, a % 2)), zorla=True)
        R, kr = sayfa(pdf.pages[b - 1], sag_s, False, sablon.get((False, b % 2)), zorla=True)
        if L is None or R is None:
            eslesmeyen.append({"sayfa": [a, b], "neden": "sütun kenarları bulunamadı"})
            continue
        KL, KR = kayitlar(L, yuzdeli), kayitlar(R, yuzdeli)
        KL = [k for k in KL if isinstance(k["v"].get("secmen"), int)]
        esl = hizala(KL, KR, partiler)
        if KL and sum(1 for _, r in esl if r) < 0.5 * len(KL):
            eslesmeyen.append({"sayfa": [a, b], "neden": "iki yüz hizalanamadı; sol yüz sağ yüzsüz alındı"})
            esl = [(x, None) for x in KL]
        for l, r in esl:
            out.append({"etiket": l["etiket"], "v": {**l["v"], **(r["v"] if r else {})},
                        "yuzde": {**l["yuzde"], **(r["yuzde"] if r else {})},
                        "karakter": l["karakter"] + (r["karakter"] if r else []),
                        "sayfa": [a, b], "sagYok": r is None})
    return out, eslesmeyen
