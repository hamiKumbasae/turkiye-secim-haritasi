"""
DIE "Mahalli Idareler Secimi Sonuclari" kitaplarindaki (taranmis, OCR metinli)
ilce / belediye tablolarini kaynak katmanina cikarir:

  data/kaynaklar/tuik/yerel/<secim>/<tablo>.json

  1984yerel  kutuphane.tuik.gov.tr/pdf/0012953.pdf  (DIE yayin no 1109, 1985) - artik extract_mahalli_1984.py
  1989yerel  kutuphane.tuik.gov.tr/pdf/0013280.pdf  (DIE, 1990)

Tablolar (kitaptaki sirasiyla):
  il_genel_meclisi     ilcelere gore IGM uyeligi oylari (1989: + sehir/koy kirilimi)
  buyuksehir           buyuksehir belediye baskanligi, bagli ilce belediyelerine gore
  belediye_baskanligi  belediyelere gore (il merkezi / ilce merkezi / belde)
  belediye_meclisi     belediyelere gore belediye meclisi uyeligi oylari

Okuma: die_tablo.sayfa_tablosu. Her tablo iki yuzlu: sol sayfa (belediye adi,
sandik, secmen, oy kullanan, katilim %, gecerli oy, ilk partiler) + sag sayfa
(kalan partiler, etiketsiz). Iki yuz satir SIRASIYLA eslenir; esleme, sag
sayfadaki parti yuzdelerinin sol sayfadaki gecerli oya uymasiyla puanlanan bir
hizalamayla (DP) yapilir - bos / baslik satirlari boylece atlanir.

Dogrulama (kitabin kendi ic tutarliligi, her satir):
  - parti oylari toplami == gecerli oy
  - her parti icin oy / gecerli * 100 == kitaptaki yuzde (1 ondalik)
OCR duzeltmesi YALNIZCA iki kisit birlikte tuttugunda yapilir: tek bir hucre
yuzdesiyle uyusmuyorsa (ya da okunamadiysa) ve gecerli - digerleri o hucrenin
yuzdesini veriyorsa. Okunan ham deger `ocrDuzeltme` icinde saklanir.
Karakter duzeyi OCR karisikliklari ('9*.3', 'A296399', '56S') once kelime
bazinda cevrilir; hangi kelimelerin cevrildigi `karakterDuzeltme`'de.

Satir tipi (`tip`): turkiye | il | ilce | belde | sehir | koy. Ilce / belde
ayrimi o donemin ilce listesiyle yapilir: ayni kitabin IGM tablosu (ilcelere
gore) + TUIK genel secim ilce listesi (1984 icin 1983, 1989 icin 1987).

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/extract_mahalli.py [1989yerel 2004yerel]
  (1984yerel: extract_mahalli_1984.py)
"""
import difflib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import die_tablo  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "tuik" / "mahalli-kitap"
OUT = ROOT / "data" / "kaynaklar" / "tuik" / "yerel"

ONCU = ["sandik", "secmen", "oyKullanan", "katilim%", "gecerliOy"]
P84 = ["ANAP", "DYP", "HP", "MDP", "RP", "SODEP", "Bağımsız"]
P89 = ["ANAP", "DSP", "DYP", "IDP", "MÇP", "RP", "SHP", "Bağımsız"]

KITAPLAR = {
    "1984yerel": {
        "demirbas": "0012953", "tarih": "25 Mart 1984", "yayin": "DİE, Mahalli İdareler Seçimi Sonuçları 25.3.1984 (yayın no. 1109)",
        "partiler": P84, "genelIlce": "1983",
        # 1984 kitabinda gecerli oyun da yuzdesi var; DYP oyu solda, yuzdesi sagda
        "sol": ONCU + ["gecerli%", "ANAP", "ANAP%", "DYP"],
        "sag": ["DYP%", "HP", "HP%", "MDP", "MDP%", "RP", "RP%", "SODEP", "SODEP%", "Bağımsız", "Bağımsız%"],
        # 1984 buyuksehir tablosunda il satirlari yalnizca 'TOPLAM-TOTAL'
        # etiketli (il adi ayri satirda, sayisiz): sirasiyla Ankara, Istanbul, Izmir
        "bbToplamSirasi": [6, 34, 35],
        "tablolar": {"il_genel_meclisi": (10, 35), "buyuksehir": (38, 39),
                     "belediye_baskanligi": (42, 93), "belediye_meclisi": (96, 147)},
    },
    "1989yerel": {
        "demirbas": "0013280", "tarih": "26 Mart 1989", "yayin": "DİE, Mahalli İdareler Seçimi Sonuçları 26.3.1989",
        "partiler": P89, "genelIlce": "1987", "binlikBosluk": True,
        "sol": ONCU + ["ANAP", "ANAP%", "DSP", "DSP%"],
        "sag": ["DYP", "DYP%", "IDP", "IDP%", "MÇP", "MÇP%", "RP", "RP%", "SHP", "SHP%", "Bağımsız", "Bağımsız%"],
        # taramada Tablo 2'nin ilk iki yaprağı karışık sırada: s.20 (Türkiye,
        # Adana...) + s.17, s.18 (Tufanbeyli...) + s.21; s.19 Tablo 1'in sağ yüzü
        "ozelCiftler": {"il_genel_meclisi": [(20, 17), (18, 21)]},
        "tablolar": {"il_genel_meclisi": (22, 115), "buyuksehir": (118, 119),
                     "belediye_baskanligi": (122, 209), "belediye_meclisi": (212, 299)},
    },
}
P04_SOL = ["EMEP", "DSP", "ANAP", "BTP", "AK Parti", "BBP", "İP"]
P04_SAG = ["ÖDP", "LDP", "TKP", "DYP", "ATP", "MP92", "CHP", "GP", "YTP02", "SHP", "SP", "DP", "MHP", "Bağımsız"]
KITAPLAR["2004yerel"] = {
    "demirbas": "0018169", "tarih": "28 Mart 2004", "yayin": "DİE, Mahalli İdareler Seçimi 28.03.2004 (yayın no. 2935)",
    # dijital dizgi (OCR degil): sol sayfa ad + sandik, secmen, oy kullanan, gecerli
    # + 7 parti (uyelik sayisi alt satirda); sag sayfa 14 parti. Satir tipi
    # etiketin girintisinden: il ~87 (kalin), ilce ~95, belde ~108.
    "dijital": True, "partiler": P04_SOL + P04_SAG,
    "sol": ["sandik", "secmen", "oyKullanan", "gecerliOy"] + P04_SOL, "sag": P04_SAG,
    "tablolar": {"il_genel_meclisi": (110, 253), "buyuksehir": (255, 260),
                 "belediye_baskanligi": (262, 389), "belediye_meclisi": (391, 594)},
}
TABLO_ACIKLAMA = {
    "il_genel_meclisi": "İl genel meclisi üyeleri seçimi sonuçlarının ilçelere göre dağılımı",
    "buyuksehir": "Büyükşehir belediye başkanlığı seçimi sonuçlarının bağlı ilçe belediyelerine göre dağılımı",
    "belediye_baskanligi": "Belediye başkanlığı seçimi sonuçlarının belediyelere göre dağılımı",
    "belediye_meclisi": "Belediye meclisi üyeleri seçimi sonuçlarının belediyelere göre dağılımı",
}

# --- OCR karakter duzeltmesi -------------------------------------------------
HARF_RAKAM = {"*": "4", "«": "4", "A": "4", "S": "5", "s": "5", "$": "5", "O": "0", "o": "0", "Q": "0",
              "D": "0", "I": "1", "l": "1", "ı": "1", "i": "1", "|": "1", "!": "1", "Z": "2", "z": "2",
              "B": "8", "G": "6", "b": "6", "g": "9", "İ": "1", "Ü": "0"}


def _cift_harf(t):
    """Kalin puntoda OCR her karakteri iki kez yazmis: '776655' -> '765',
    '2222..77' -> '22.7'. Yalnizca binligi bosluklu kitapta (orada 4+ haneli
    parca olamaz) kullanilir."""
    if len(t) >= 4 and len(t) % 2 == 0 and t[0::2] == t[1::2] and re.fullmatch(r"[\d.,]+", t):
        return t[0::2]
    return None


BINLIK_BOSLUK = False


def kelime_duzelt(w):
    """Rakam agirlikli kelimelerde harf/rakam karisikligi. Adlarin rakamli OCR
    bozulmalari ('1MA.104LU') dokunulmaz: en fazla 1 harf (ya da >=3 rakamla 2)."""
    t = w["text"]
    if BINLIK_BOSLUK and _cift_harf(t):
        return _cift_harf(t)
    rakam = sum(c.isdigit() for c in t)
    if not rakam:
        return None
    harf = sum(c.isalpha() for c in t)
    if harf > 2 or (harf == 2 and rakam < 3):
        return None
    t2 = t.rstrip("-_•'`\"")
    t2 = "".join(HARF_RAKAM.get(c, c) for c in t2)
    t2 = re.sub(r"[^\d.,]", "", t2)
    return t2 or None


# --- donem il / ilce adlari ----------------------------------------------------
IL_EK = {"AKARAHISAR": 3, "AFYON": 3, "AFYONKARAHISAR": 3, "KMARAS": 46, "KAHRAMANMARAS": 46, "MARAS": 46,
         "GANTEP": 27, "GAZIANTEP": 27, "SURFA": 63, "URFA": 63, "SANLIURFA": 63, "ICEL": 33, "MERSIN": 33,
         "HAKKARI": 30}


def il_adlari():
    d = json.loads((ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text(encoding="utf-8"))
    out = {fold(v["il_ADI"]).replace(" ", ""): int(k) for k, v in d.items() if int(k) <= 67}
    out.update(IL_EK)
    return out


def genel_ilceler(yil):
    d = json.loads((ROOT / f"data/kaynaklar/tuik/genel/{yil}.json").read_text(encoding="utf-8"))
    out = {}
    for c in d["cevreler"]:
        for r in c.get("ilceler") or []:
            out.setdefault(c["plaka"], set()).add(_anahtar(r["ad"]))
    return out


OCR_HARF = str.maketrans({"0": "O", "1": "I", "5": "S", "8": "B", "9": "Ş", "6": "G", "4": "A", "!": "I",
                          "$": "S", "?": "Ş", "»": "Ş", "«": "Ş", "|": "I"})


def _anahtar(ad):
    """Ad karsilastirma anahtari: bosluksuz fold, parantez ici (eski ad) atilir.
    Adlarda rakam olmadigindan OCR'in harf yerine yazdigi rakamlar geri cevrilir
    ('NEV9EH1R' -> NEVŞEHİR); 'HERKEZ-CENTRAL' gibi merkez satirlari -> MERKEZ."""
    ad = re.sub(r"\(.*?\)?", "", ad or "").translate(OCR_HARF)
    f = fold(ad)
    if re.search(r"CENTR|ENTRAL|^\W*[MHN] ?E ?R ?K ?E ?Z\b", f):
        return "MERKEZ"
    f = re.sub(r"[-/]?\s*(CITY|VILLAGES)\b", "", f)
    return re.sub(r"[^A-Z]", "", f)


def _ilce_mi(a, kume):
    return a in kume or _ilce_adayi(a, kume) is not None


def _ilce_adayi(a, kume):
    """OCR'i bozuk ilce adi icin tek harf civari fark: uzunluk farki <= 1 ve
    benzerlik >= 0.85. Donen: eslesen referans anahtar (ya da None)."""
    if len(a) < 4:
        return None
    en_iyi = max(((_benzer(a, k), k) for k in kume if abs(len(k) - len(a)) <= 1), default=(0, None))
    return en_iyi[1] if en_iyi[0] >= 0.85 else None


# --- sayfa cifti okuma ----------------------------------------------------------
def _sol_mu(page):
    satir = (page.extract_text() or "").split("\n")
    etk = sum(1 for s in satir if re.match(r"^[A-ZÇĞİÖŞÜa-zçğıöşü][^\d]{2,}\s[\d*]", s)
              and len(re.findall(r"\d+", s)) >= 4)
    return etk >= 5


def _satir_degerleri(sutunlar, degerler):
    return {k: v for k, v in zip(sutunlar, degerler)}


def _puan(sol, sag, partiler):
    """Sol ve sag satirin ayni belediyeye ait olma puani: sag sayfadaki parti
    yuzdeleri soldaki gecerli oya uyuyor mu."""
    d = {**sol, **sag}
    g = d.get("gecerliOy")
    if not isinstance(g, int) or g <= 0:
        return -1.0
    puan, bilgi = 0.0, False
    for p in partiler:
        o, y = d.get(p), d.get(p + "%")
        if p + "%" not in sag:
            continue
        if isinstance(o, int) and isinstance(y, float):
            bilgi = True
            puan += 1.0 if abs(100 * o / g - y) <= 0.15 else -0.7
    toplam = sum(d.get(p) or 0 for p in partiler if isinstance(d.get(p), int))
    if toplam == g:
        puan += 2.0
    return puan if bilgi or toplam == g else 0.05


def _hizala(sol, sag, partiler):
    """Sirali iki listeyi, eslesen ciftlerin puani en buyuk olacak sekilde hizala."""
    n, m = len(sol), len(sag)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    yol = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            sec = [(dp[i + 1][j], "s"), (dp[i][j + 1], "r")]
            p = _puan(sol[i]["v"], sag[j]["v"], partiler)
            if p > 0:
                sec.append((dp[i + 1][j + 1] + p, "e"))
            dp[i][j], yol[i][j] = max(sec, key=lambda x: x[0])
    for i in range(n):
        yol[i][m] = "s"
    for j in range(m):
        yol[n][j] = "r"
    i = j = 0
    ciftler, solda_kalan = [], []
    while i < n or j < m:
        if i < n and j < m and yol[i][j] == "e":
            ciftler.append((sol[i], sag[j]))
            i, j = i + 1, j + 1
        elif i < n and (j >= m or yol[i][j] == "s"):
            solda_kalan.append(sol[i])
            ciftler.append((sol[i], None))
            i += 1
        else:
            j += 1
    return ciftler


def _duzeltmeler(page):
    out = []
    for w in page.extract_words(keep_blank_chars=False, use_text_flow=False):
        y = kelime_duzelt(w)
        if y is not None and y != w["text"]:
            out.append((w["top"], w["text"], y))
    return out


def _sayfa_tokenleri(page, sol):
    """{satir_top: [(metin, x0, x1, tur)]} - die_tablo ile ayni satirlama; yapisal
    okuma icin sayi parcalarinin x konumlari."""
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    for w in words:
        y = kelime_duzelt(w)
        if y is not None:
            w["text"] = y
    out = {}
    for s in die_tablo._satirlar(words):
        x_bas = 0
        if sol:
            harfli = [w for w in s if w["x1"] <= 170 and re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", w["text"])]
            x_bas = max(w["x1"] for w in harfli) + 1 if harfli else 90
        out[s[0]["top"]] = die_tablo._tokenler(s, x_bas)
    return out


def _slot_secenekleri(tok, i, tur, kenar):
    """tok[i:]'den bir hucre: [(deger, sonraki_i, x_ceza)]. tur 'n' = sayi, 'p' =
    yuzde. Binligi bosluklu kitapta (1989) devam parcalari 3 hanelidir; 1984
    kitabinda sayilar ayiracsiz ama OCR bazen boluyor ('7 78' = 778). Yuzdelerin
    ondalik noktasi sik sik dusmus ve rakamlar ayrilmis: '4 1 3' = 41,3."""
    if i >= len(tok):
        return []

    def ceza(j):
        return min(abs(tok[j][2] - kenar), 60) / 20 if kenar else 0

    def yakin(j):
        return not kenar or abs(tok[j][2] - kenar) <= 40

    t = tok[i]
    out = []
    if t[3] == "tire":
        return [(0 if tur == "n" else 0.0, i + 1, ceza(i))] if yakin(i) else []
    if tur == "p":
        if t[3] == "yuzde" and yakin(i):
            out.append((float(t[0]), i + 1, ceza(i)))
        # noktasiz / bolunmus yuzde: 1-3 kisa rakam parcasi (+ istege bagli yuzde parcasi)
        metin = ""
        for j in range(i, min(i + 3, len(tok))):
            u = tok[j]
            if j > i and u[1] - tok[j - 1][2] > 10:
                break
            if u[3] == "yuzde":
                if metin and len(metin) <= 2 and yakin(j):
                    out.append((float(metin + u[0]), j + 1, ceza(j) + 0.5))
                break
            if u[3] != "sayi" or len(u[0]) > 3:
                break
            metin += u[0]
            if 2 <= len(metin) <= 3 and yakin(j):
                out.append((float(metin[:-1] + "." + metin[-1]), j + 1, ceza(j) + 0.5))
        return out
    if t[3] != "sayi":
        return []
    metin = ""
    for j in range(i, min(i + 4, len(tok))):
        u = tok[j]
        if u[3] != "sayi":
            break
        if j > i and (u[1] - tok[j - 1][2] > 12 or (BINLIK_BOSLUK and len(u[0]) != 3)):
            break
        metin += u[0]
        if len(metin) > 9:
            break
        if yakin(j):
            out.append((int(metin), j + 1, ceza(j)))
    return out


def _cozumler(tok, sablon, kenarlar, partili, sinir=4000):
    """sablon: alan adlari; partili: atlanabilen (bos birakilabilen) alanlar.
    Tum tokenleri tuketen ayrismalar: [(degerler, x_ceza)]."""
    out = []

    def git(k, i, acc, ceza):
        if len(out) >= sinir:
            return
        if k == len(sablon):
            if i == len(tok):
                out.append((dict(acc), ceza))
            return
        ad = sablon[k]
        kenar = kenarlar[k] if kenarlar and k < len(kenarlar) else None
        for deger, j, c in _slot_secenekleri(tok, i, "p" if ad.endswith("%") else "n", kenar):
            acc[ad] = deger
            git(k + 1, j, acc, ceza + c)
            del acc[ad]
        if ad in partili:
            git(k + 1, i, acc, ceza + 0.3)

    git(0, 0, {}, 0.0)
    return out


def _puanla(v, partiler):
    g = v.get("gecerliOy")
    if not isinstance(g, int) or g <= 0:
        return -99, False
    puan, tam = 0.0, True
    s, k, kat = v.get("secmen"), v.get("oyKullanan"), v.get("katilim%")
    if isinstance(s, int) and isinstance(k, int) and isinstance(kat, float) and s:
        if abs(100 * k / s - kat) <= 0.1:
            puan += 3
        else:
            puan -= 3
            tam = False
    if isinstance(k, int) and g > k:
        puan -= 5
        tam = False
    gy = v.get("gecerli%")
    if isinstance(k, int) and k and isinstance(gy, float):
        if abs(100 * g / k - gy) <= 0.1:
            puan += 2
        else:
            puan -= 2
            tam = False
    toplam = 0
    for p in partiler:
        o, y = v.get(p) or 0, v.get(p + "%")
        toplam += o
        if isinstance(y, float):
            if abs(100 * o / g - y) <= 0.1:
                puan += 2 if o else 0.5
            else:
                puan -= 3
                tam = False
    if toplam == g:
        puan += 6
    else:
        tam = False
    return puan, tam


def yapisal_oku(satir, cfg):
    """Sutun kenarlarina bagli olmadan: sayi parcalarini sablona gore ayristir,
    katilim / yuzde / toplam kisitlarini en iyi saglayan ayrismayi sec."""
    partili = {a for a in cfg["sol"] + cfg["sag"] if a.rstrip("%") in cfg["partiler"]}
    soller = _cozumler(satir["tokSol"], cfg["sol"], satir["kenarSol"], partili)
    if not soller or satir["tokSag"] is None:
        return None
    soller = sorted(soller, key=lambda sc: -(_puanla(sc[0], [p for p in cfg["partiler"] if p + "%" in sc[0]])[0] - sc[1]))[:6]
    saglar = _cozumler(satir["tokSag"], cfg["sag"], satir["kenarSag"], partili)
    en_iyi = None
    for sv, sc in soller:
        for rv, rc in saglar:
            v = {**sv, **rv}
            puan, tam = _puanla(v, cfg["partiler"])
            puan -= sc + rc
            if en_iyi is None or puan > en_iyi[0]:
                en_iyi = (puan, tam, v)
    if en_iyi and en_iyi[1]:
        return en_iyi[2]
    return None


def tablo_oku(pdf, cfg, ilk, son, ozel=()):
    sol_s, sag_s = cfg["sol"], cfg["sag"]
    ciftler, eslesmeyen = list(ozel), []
    no = ilk
    while no <= son:
        pg = pdf.pages[no - 1]
        if _sol_mu(pg) and no + 1 <= son + 1 and no < len(pdf.pages) and not _sol_mu(pdf.pages[no]):
            ciftler.append((no, no + 1))
            no += 2
        else:
            eslesmeyen.append({"sayfa": no, "neden": "eşi olan sol/sağ yüz yok"})
            no += 1
    satirlar = []
    kenar_sol = kenar_sag = None
    for a, b in ciftler:
        L, kl = die_tablo.sayfa_tablosu(pdf.pages[a - 1], 160, len(sol_s), None, kelime_duzelt=kelime_duzelt,
                                        hazir_kenarlar=kenar_sol)
        R, kr = die_tablo.sayfa_tablosu(pdf.pages[b - 1], 120, len(sag_s), None, etiketsiz=True,
                                        kelime_duzelt=kelime_duzelt, hazir_kenarlar=kenar_sag)
        if L is None or R is None:
            eslesmeyen.append({"sayfa": [a, b], "neden": "sütunlar bulunamadı"})
            continue
        if kenar_sol is None and all(kl):
            kenar_sol = kl
        if kenar_sag is None and all(kr):
            kenar_sag = kr
        kd = _duzeltmeler(pdf.pages[a - 1]), _duzeltmeler(pdf.pages[b - 1])
        ts, tr = _sayfa_tokenleri(pdf.pages[a - 1], True), _sayfa_tokenleri(pdf.pages[b - 1], False)
        sol = [{"etiket": e, "v": _satir_degerleri(sol_s, v), "y": y, "ham": h}
               for e, v, y, h in L if len(re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]", e)) >= 2 and isinstance(v[1], int)
               and not re.match(r"^\W*TABL[OE]\b", e)]
        sag = [{"v": _satir_degerleri(sag_s, v), "y": y, "ham": h} for e, v, y, h in R]
        hiza = _hizala(sol, sag, cfg["partiler"])
        if sum(1 for _, r in hiza if r) < 0.5 * len(sol):
            # sag yuz bu sol yuzun devami degil (tarama sirasi bozuk / sayfa eksik):
            # sol yuzun satirlari sag yuz OLMADAN (kismi) alinir
            eslesmeyen.append({"sayfa": b, "neden": f"s.{a} sol yüzüyle hizalanamadı"})
            hiza = [(x, None) for x in sol]
        for s, r in hiza:
            k = [(t, y) for yy, t, y in kd[0] if abs(yy - s["y"]) < 5]
            if r:
                k += [(t, y) for yy, t, y in kd[1] if abs(yy - r["y"]) < 5]
            satirlar.append({"etiket": s["etiket"], "v": {**s["v"], **(r["v"] if r else {})},
                             "sagYok": r is None, "sayfa": [a, b], "ham": s["ham"] + (r["ham"] if r else []),
                             "karakterDuzeltme": k,
                             "tokSol": ts.get(s["y"]), "tokSag": tr.get(r["y"]) if r else None,
                             "kenarSol": kl, "kenarSag": kr})
    return satirlar, eslesmeyen


# --- dijital (dizgi) kitap: 2004 ------------------------------------------------
CID = {"(cid:247)": "ğ", "(cid:248)": "İ", "(cid:249)": "Ş", "(cid:250)": "ş", "(cid:246)": "Ğ"}
SAYI_TIRE = re.compile(r"^(\d+|-)$")


def _dijital_satirlar(page):
    """[(top, [kelime])] - kenar boslugundaki dondurulmus yazi (Futura) atilir."""
    ws = [w for w in page.extract_words(extra_attrs=["fontname", "size"]) if "Futura" not in w["fontname"]]
    satir = []
    for w in sorted(ws, key=lambda w: (w["top"], w["x0"])):
        if satir and abs(w["top"] - satir[-1][0]) <= 2.5:
            satir[-1][1].append(w)
        else:
            satir.append([w["top"], [w]])
    return [(t, sorted(k, key=lambda w: w["x0"])) for t, k in satir]


def _ayir(kelimeler, n):
    """Sondaki n sayi/tire + onceki etiket; olmazsa None."""
    metin = [w["text"] for w in kelimeler]
    if len(metin) < n or not all(SAYI_TIRE.match(t) for t in metin[-n:]):
        return None
    if len(metin) > n and SAYI_TIRE.match(metin[-n - 1]):
        return None
    etiket = " ".join(metin[:-n])
    for k, v in CID.items():
        etiket = etiket.replace(" " + k + " ", v).replace(k + " ", v).replace(" " + k, v).replace(k, v)
    deger = [0 if t == "-" else int(t) for t in metin[-n:]]
    return etiket.strip(), deger, (kelimeler[0]["x0"] if len(metin) > n else None), \
        ("Bold" in kelimeler[0]["fontname"] if len(metin) > n else False)


def dijital_tablo_oku(pdf, cfg, ilk, son):
    sol_s, sag_s = cfg["sol"], cfg["sag"]
    satirlar, eslesmeyen = [], []
    for a in range(ilk, son, 2):
        b = a + 1
        ds = _dijital_satirlar(pdf.pages[a - 1])
        # girinti referansi: sayfanin 'Belediye/Municipality' ya da 'İl ve ilçe'
        # sutun basligi (tek/cift sayfada kagit kaymasi farkli)
        ref = min((w["x0"] for _, k in ds for w in k if w["text"] in ("Municipality", "Province")), default=86.7)
        L = [(t, _ayir(k, len(sol_s))) for t, k in ds]
        L = [(t, x) for t, x in L if x and x[0]]
        R = [(t, [0 if w["text"] == "-" else int(w["text"]) for w in k]) for t, k in _dijital_satirlar(pdf.pages[b - 1])
             if len(k) == len(sag_s) and all(SAYI_TIRE.match(w["text"]) for w in k)]
        if not L:
            continue
        # iki yuzun dikey kaymasi: en cok satiri +-1.5 icinde eslestiren ofset
        # alt satirdaki uyelik sayilari da 14 sutunlu oldugundan bir satir kaymis
        # hizalama da cok satir eslestirir: parti toplami = gecerli tutan satir
        # sayisini en cok yapan ofset secilir
        def tutan(d):
            n = 0
            for t, (_, deger, _, _) in L:
                r = min(R, key=lambda u: abs(u[0] - t - d), default=None)
                if r and abs(r[0] - t - d) <= 1.5 and sum(deger[4:]) + sum(r[1]) == deger[3]:
                    n += 1
            return n
        ofset = max((tutan(d / 2), -abs(d), d / 2) for d in range(-24, 25))[2]
        for t, (etiket, deger, x0, kalin) in L:
            r = min(R, key=lambda u: abs(u[0] - t - ofset), default=None)
            sag = r[1] if r and abs(r[0] - t - ofset) <= 1.5 else None
            v = dict(zip(sol_s, deger))
            if sag:
                v.update(zip(sag_s, sag))
            satirlar.append({"etiket": etiket, "v": v, "sagYok": sag is None, "sayfa": [a, b], "x0": x0, "kalin": kalin, "ref": ref,
                             "ham": [], "karakterDuzeltme": [], "tokSol": None, "tokSag": None})
    return satirlar, eslesmeyen


def dijital_tiplendir(satirlar):
    il_ad = {fold(v["il_ADI"]).replace(" ", ""): int(k) for k, v in json.loads(
        (ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text(encoding="utf-8")).items()}
    il_ad.update({"ICEL": 33, "AFYON": 3, "SURFA": 63, "KMARAS": 46})
    plaka, ilce, gorulen = None, None, set()
    for s in satirlar:
        f = fold(s["etiket"])
        if re.search(r"TURK.?YE|TURKEY", f):
            s.update(tip="turkiye", plaka=None, ustIlce=None)
            plaka = None
        elif re.match(r"^(KENT|KIR)\b", f):
            s.update(tip="sehir" if f.startswith("KENT") else "koy", plaka=plaka, ustIlce=ilce)
        elif s["kalin"] and f.replace(" ", "") in il_ad:
            plaka = il_ad[f.replace(" ", "")]
            gorulen.add(plaka)
            ilce = None
            s.update(tip="il", plaka=plaka, ustIlce=None)
        elif s["x0"] is not None and s["x0"] - s["ref"] < 14:
            ilce = s["etiket"]
            s.update(tip="ilce", plaka=plaka, ustIlce=None)
        else:
            s.update(tip="belde", plaka=plaka, ustIlce=ilce)
    return satirlar, sorted(set(range(1, 82)) - gorulen), []


# --- satir dogrulama / duzeltme -------------------------------------------------
def _uyar(o, y, g):
    return abs(100 * o / g - y) <= 0.1 if g else True


def dogrula(v, partiler):
    """v: {alan: deger}. Dondurur: (oy, kontrol, ocrDuzeltme)."""
    g = v.get("gecerliOy")
    oy = {p: v.get(p) for p in partiler}
    duz = []
    if not isinstance(g, int) or g <= 0:
        return {p: o for p, o in oy.items() if o}, {"durum": "gecerliOyOkunamadi"}, duz

    def yuzde_uymaz(p):
        o, y = oy[p], v.get(p + "%")
        if isinstance(y, float) and y > 0 and not isinstance(o, int):
            return True
        return isinstance(o, int) and isinstance(y, float) and not _uyar(o, y, g)

    toplam = sum(o for o in oy.values() if isinstance(o, int))
    if toplam != g:
        supheli = [p for p in partiler if yuzde_uymaz(p)]
        if len(supheli) == 1:
            p = supheli[0]
            aday = g - (toplam - (oy[p] if isinstance(oy[p], int) else 0))
            y = v.get(p + "%")
            if aday >= 0 and (not isinstance(y, float) or _uyar(aday, y, g)):
                duz.append({"alan": p, "okunan": oy[p], "duzeltilen": aday, "yontem": "toplam + yüzde"})
                oy[p] = aday
        elif not supheli and toplam > 0 and sum(1 for p in partiler if isinstance(v.get(p + "%"), float) and oy[p]) >= 2:
            # parti hucreleri kendi yuzdeleriyle tutarli: yanlis okunan gecerli oy
            if all(_uyar(o, v[p + "%"], toplam) for p, o in oy.items()
                   if isinstance(o, int) and isinstance(v.get(p + "%"), float)) \
                    and (not isinstance(v.get("oyKullanan"), int) or toplam <= v["oyKullanan"]):
                duz.append({"alan": "gecerliOy", "okunan": g, "duzeltilen": toplam, "yontem": "parti toplamı + yüzdeler"})
                g = toplam
    toplam = sum(o for o in oy.values() if isinstance(o, int))
    uymaz = [p for p in partiler if yuzde_uymaz(p)]
    # toplam tutuyorsa yuzde uyumsuzlugu yuzde hucresinin OCR hatasi sayilir
    # (orn. 1989 Antalya/Kale DYP 1836 / 4248 = %43,2, kitapta '48.2' okunmus)
    kontrol = {"durum": "tutarli" if toplam == g else "tutarsiz"}
    if toplam != g:
        kontrol["partiToplami"] = toplam
    if uymaz:
        kontrol["yuzdeUyumsuz"] = uymaz
    s, k, kat = v.get("secmen"), v.get("oyKullanan"), v.get("katilim%")
    if isinstance(s, int) and isinstance(k, int) and isinstance(kat, float) and s and abs(100 * k / s - kat) > 0.15:
        kontrol["katilimUyumsuz"] = True
    return {p: o for p, o in oy.items() if isinstance(o, int) and o}, dict(kontrol, gecerliOy=g), duz


# --- satir tipleri ---------------------------------------------------------------
def _benzer(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def _sirali_hizala(ref, adlar, esik=0.55):
    """ref (ilce sirasi) ile adlar (belediye satirlari) arasinda sira koruyan,
    toplam benzerligi en buyuk esleme. Dondurur: her ad icin eslesti mi."""
    n, m = len(ref), len(adlar)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            b = 1.5 if ref[i] == adlar[j] else _benzer(ref[i], adlar[j])
            dp[i][j] = max(dp[i + 1][j], dp[i][j + 1], dp[i + 1][j + 1] + b if b >= esik else -1)
    out, i, j = [False] * m, 0, 0
    while i < n and j < m:
        b = 1.5 if ref[i] == adlar[j] else _benzer(ref[i], adlar[j])
        if b >= esik and dp[i][j] == dp[i + 1][j + 1] + b:
            out[j] = True
            i, j = i + 1, j + 1
        elif dp[i][j] == dp[i + 1][j]:
            i += 1
        else:
            j += 1
    return out


def tiplendir(satirlar, il_ad, ilce_kume, tablo, ilce_sira=None, bb_toplam=None):
    """Sirali satirlara tip / il / ust ilce ata. Kitapta iller plaka sirasinda;
    OCR'i bozuk il adi ('slPkOP', 'TEKJRDAĞ') siradaki ilin adina benzerlikle
    taninir (o ilin ilcesi olmamak kaydiyla)."""
    ad_plaka = {}
    for k, v in il_ad.items():
        ad_plaka.setdefault(v, []).append(k)
    gorulen, plaka, merkezli, ilsiz = set(), None, set(), []
    birebir_il = {}
    for j, s in enumerate(satirlar):
        a = _anahtar(s["etiket"])
        if a in il_ad:
            birebir_il.setdefault(il_ad[a], []).append(j)
    out = []
    for i, s in enumerate(satirlar):
        a = _anahtar(s["etiket"])
        sec = s["v"].get("secmen") or 0
        sonraki_sec = (satirlar[i + 1]["v"].get("secmen") or 0) if i + 1 < len(satirlar) else 0
        il_buyuklugu = sec >= 15000 and sec >= sonraki_sec
        bulanik = _siradaki_il(a, plaka, gorulen, ad_plaka, ilce_kume) if il_buyuklugu else None
        # adi birebir yazilmis il satiri ileride varsa bu satir o il degildir
        # (1989 IGM: Hatay ilcesi 'ERZİN' ~ MERSİN, İÇEL satiri ilerde)
        if bulanik and any(j > i for j in birebir_il.get(bulanik[1], [])):
            bulanik = None
        if bulanik and bulanik[0] < 0.65 and not _alt_toplam_tutar(satirlar, i):
            bulanik = None
        ham = fold(s["etiket"])
        if re.search(r"GENEL ?TOPLAM|GENERAL ?TOTAL|TURKIYE", ham):
            tip = "turkiye"
            plaka = None
        elif bb_toplam and tablo == "buyuksehir" and re.search(r"^TOPLAM", ham):
            plaka = bb_toplam[len(gorulen)]
            gorulen.add(plaka)
            tip = "il"
        elif re.search(r"^\W*SEHIR\b|\bCITY\b", ham) and tablo == "il_genel_meclisi":
            tip = "sehir"
        elif re.search(r"^\W*K ?O ?Y ?L ?E ?R\b|V ?I ?L ?L ?A ?G ?E", ham) and tablo == "il_genel_meclisi":
            tip = "koy"
        elif (a in il_ad and il_ad[a] not in gorulen) or bulanik:
            plaka = il_ad[a] if a in il_ad and il_ad[a] not in gorulen else bulanik[1]
            gorulen.add(plaka)
            tip = "il"
        elif a == "MERKEZ" and plaka in merkezli and tablo != "buyuksehir":
            # ayni ilde ikinci MERKEZ: il satiri OCR'da kacmis. Hemen onceki buyuk
            # satir il satiridir ('MU' = Muş, 'NtöDE' = Niğde); yoksa il satiri
            # taramada hic yok (1984 Urfa) - il sinirini yine de buradan baslat
            yeni = min((p for p in ad_plaka if p not in gorulen and p > (plaka or 0)), default=None)
            onceki = out[-1] if out else None
            if onceki and onceki["tip"] in ("ilce", "belde", "ilceAdayi") and (onceki["v"].get("secmen") or 0) >= max(15000, sec):
                onceki.update(tip="il", plaka=yeni, ilAdiOkunamadi=True)
            else:
                ilsiz.append(yeni)
            plaka = yeni
            gorulen.add(plaka)
            merkezli.add(plaka)
            tip = "ilce"
        elif tablo in ("il_genel_meclisi", "buyuksehir") or a == "MERKEZ" or a in ilce_kume.get(plaka, set()):
            tip = "ilce"
            if a == "MERKEZ":
                merkezli.add(plaka)
        elif _ilce_adayi(a, ilce_kume.get(plaka, set())):
            tip = "ilceAdayi"
        else:
            tip = "belde"
        out.append(dict(s, tip=tip, plaka=plaka, anahtar=a))
    # benzerlikle ilce adayi: ayni ilde o ilce adiyla BIREBIR eslesen baska satir
    # yoksa ilce (orn. 'BOĞAZLTYAN'), varsa belde (orn. Konya 'KAŞINHANI' belde,
    # 'KADINHANI' ilce satiri zaten var)
    birebir = {(r["plaka"], r["anahtar"]) for r in out if r["tip"] == "ilce"}
    for r in out:
        if r["tip"] == "ilceAdayi":
            r["tip"] = "belde" if (r["plaka"], _ilce_adayi(r["anahtar"], ilce_kume[r["plaka"]])) in birebir else "ilce"
    # ayni kitabin IGM tablosundaki ilce SIRASI varsa (alfabetik, MERKEZ basta):
    # belediye tablosunda ilce merkezleri ayni sirayla gelir, beldeler araya
    # girer. Sirali hizalama ad benzerligi dusukken bile (iki ayri OCR hatasi)
    # dogru satiri bulur.
    if ilce_sira and tablo in ("belediye_baskanligi", "belediye_meclisi"):
        for p in {r["plaka"] for r in out if r["plaka"]}:
            R = ilce_sira.get(p)
            B = [r for r in out if r["plaka"] == p and r["tip"] in ("ilce", "belde")]
            if not R or not B:
                continue
            for r, eslesti in zip(B, _sirali_hizala(R, [r["anahtar"] for r in B])):
                if eslesti:
                    r["tip"] = "ilce"
                elif r["anahtar"] != "MERKEZ" and r["anahtar"] not in ilce_kume.get(p, set()):
                    r["tip"] = "belde"
    ilce = None
    for r in out:
        if r["tip"] in ("turkiye", "il"):
            ilce = None
        elif r["tip"] == "ilce":
            ilce = "Merkez" if r["anahtar"] == "MERKEZ" else r["etiket"]
        r["ustIlce"] = ilce if r["tip"] in ("belde", "sehir", "koy") else None
        del r["anahtar"]
    return out, sorted(set(range(1, 68)) - gorulen), ilsiz


def _alt_toplam_tutar(satirlar, i):
    """Il satirinin secmeni, altindaki (sehir/koy disi) satirlarin kumulatif
    toplamina bir noktada (%0.5 icinde) esit olmali."""
    hedef, t = satirlar[i]["v"].get("secmen") or 0, 0
    for s in satirlar[i + 1:]:
        if re.search(r"SEHIR|CITY|KOYLER|VILLAGE", fold(s["etiket"])):
            continue
        t += s["v"].get("secmen") or 0
        if abs(t - hedef) <= 0.005 * hedef:
            return True
        if t > hedef * 1.005:
            return False
    return False


def _siradaki_il(a, plaka, gorulen, ad_plaka, ilce_kume):
    """Siradaki (en fazla 3) gorulmemis ilden adi en cok benzeyen; OCR bir il
    adini kacirmissa sonrakiler de kaymasin diye tek aday degil."""
    if len(a) < 3 or a == "MERKEZ" or _ilce_mi(a, ilce_kume.get(plaka, set())):
        return None
    adaylar = sorted(p for p in ad_plaka if p not in gorulen and p > (plaka or 0))[:3]
    # esitlikte kucuk plaka (kitap sirasi): 't BEL' IÇEL'e de ISTANBUL'a da 0.5
    en_iyi = max(((max(_benzer(a, n) for n in ad_plaka[p]), -p) for p in adaylar), default=(0, None))
    en_iyi = (en_iyi[0], -en_iyi[1]) if en_iyi[1] is not None else en_iyi
    return en_iyi if en_iyi[0] >= 0.5 else None


def isle(secim, tablolar=None):
    global BINLIK_BOSLUK
    cfg = KITAPLAR[secim]
    BINLIK_BOSLUK = cfg.get("binlikBosluk", False)
    pdf = die_tablo.ac(RAW / f"{cfg['demirbas']}.pdf")
    il_ad = il_adlari()
    ilce_kume = genel_ilceler(cfg["genelIlce"]) if cfg.get("genelIlce") else {}
    ilce_sira = {}
    sonuc = {}
    for tablo, (ilk, son) in cfg["tablolar"].items():
        if tablolar and tablo not in tablolar:
            continue
        if cfg.get("dijital"):
            satirlar, eslesmeyen = dijital_tablo_oku(pdf, cfg, ilk, son)
            satirlar, eksik_il, ilsiz = dijital_tiplendir(satirlar)
        else:
            satirlar, eslesmeyen = tablo_oku(pdf, cfg, ilk, son, cfg.get("ozelCiftler", {}).get(tablo, ()))
            satirlar, eksik_il, ilsiz = tiplendir(satirlar, il_ad, ilce_kume, tablo, ilce_sira, cfg.get("bbToplamSirasi"))
        if tablo == "il_genel_meclisi":
            # ayni kitabin ilce listesi (ve sirasi) sonraki tablolarda ilce/belde ayrimina eklenir
            for s in satirlar:
                if s["tip"] == "ilce" and s["plaka"]:
                    ilce_kume.setdefault(s["plaka"], set()).add(_anahtar(s["etiket"]))
                    ilce_sira.setdefault(s["plaka"], []).append(_anahtar(s["etiket"]))
        kayitlar = []
        for s in satirlar:
            oy, kontrol, duz = dogrula(s["v"], cfg["partiler"])
            yapisal = None
            if kontrol["durum"] != "tutarli" and s["tokSol"]:
                v2 = yapisal_oku(s, cfg)
                if v2:
                    oy2, kontrol2, duz2 = dogrula(v2, cfg["partiler"])
                    if kontrol2["durum"] == "tutarli":
                        yapisal = {"sutunOkumasi": {k: x for k, x in s["v"].items() if k in cfg["partiler"] or k in ONCU},
                                   "not": "sütun kenarı okuması tutarsızdı; sayı parçaları katılım/yüzde/toplam kısıtlarıyla yeniden ayrıştırıldı"}
                        s = dict(s, v=v2)
                        oy, kontrol, duz = oy2, kontrol2, duz2
            v = s["v"]
            r = {"tip": s["tip"], "plaka": s["plaka"], "adKaynakta": s["etiket"], "ustIlce": s["ustIlce"],
                 "sandik": v.get("sandik"), "secmen": v.get("secmen"), "oyKullanan": v.get("oyKullanan"),
                 "katilim": v.get("katilim%") if "katilim%" in v else (round(100 * v["oyKullanan"] / v["secmen"], 1) if v.get("secmen") else None),
                 "gecerliOy": kontrol.pop("gecerliOy", v.get("gecerliOy")),
                 "oy": dict(sorted(oy.items(), key=lambda kv: -kv[1])),
                 "yuzde": {p: v[p + "%"] for p in cfg["partiler"] if isinstance(v.get(p + "%"), float) and v[p + "%"]},
                 "kontrol": kontrol, "sayfa": s["sayfa"]}
            if "uyelik" in v:
                r["uyelik"] = v["uyelik"]
            if duz:
                r["ocrDuzeltme"] = duz
            if yapisal:
                r["yapisalOkuma"] = yapisal
            if s["karakterDuzeltme"]:
                r["karakterDuzeltme"] = [f"{a}→{b}" for a, b in s["karakterDuzeltme"]]
            if s["sagYok"]:
                r["kontrol"]["sagSayfaEslesmedi"] = True
            if s.get("ilAdiOkunamadi"):
                r["ilAdiOkunamadi"] = True
            r["kazanan"] = next(iter(r["oy"]), None)
            kayitlar.append(r)
        say = lambda f: sum(1 for r in kayitlar if f(r))  # noqa: E731
        veri = {
            "secim": secim, "tablo": tablo, "aciklama": TABLO_ACIKLAMA[tablo],
            "kaynak": {"ana": "tuik", "yayin": cfg["yayin"], "demirbas": cfg["demirbas"],
                       "url": f"https://kutuphane.tuik.gov.tr/pdf/{cfg['demirbas']}.pdf",
                       "ham": f"data/raw/tuik/mahalli-kitap/{cfg['demirbas']}.pdf",
                       "sayfalar": [ilk, son], "ozelSayfaCiftleri": cfg.get("ozelCiftler", {}).get(tablo), "not": "DİE kitabındaki belediye/ilçe düzeyi değerler ilçe seçim kurullarının birleştirme tutanaklarından (kitabın açıklaması)."},
            "partiler": cfg["partiler"],
            "ozet": {"satir": len(kayitlar), **{t: say(lambda r, t=t: r["tip"] == t) for t in ("il", "ilce", "belde", "sehir", "koy")},
                     "tutarli": say(lambda r: r["kontrol"]["durum"] == "tutarli"),
                     "tutarsiz": say(lambda r: r["kontrol"]["durum"] != "tutarli"),
                     "ocrDuzeltilen": say(lambda r: r.get("ocrDuzeltme")),
                     "yapisalOkunan": say(lambda r: r.get("yapisalOkuma")),
                     "eksikIl": eksik_il, "ilSatiriTaramadaYok": ilsiz, "eslesmeyenSayfa": eslesmeyen},
            "satirlar": kayitlar,
        }
        (OUT / secim).mkdir(parents=True, exist_ok=True)
        (OUT / secim / f"{tablo}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
        print(secim, tablo, veri["ozet"])
        sonuc[tablo] = veri
    return sonuc


# 1984 bu okuyucuyla degil extract_mahalli_1984.py ile okunur (uc OCR okumasi,
# geri hesap yok); KITAPLAR["1984yerel"] ayarlari orada kullaniliyor.
AYRI_OKUYUCU = {"1984yerel": "extract_mahalli_1984.py"}


def main():
    secimler = [a for a in sys.argv[1:] if a in KITAPLAR] or [k for k in KITAPLAR if k not in AYRI_OKUYUCU]
    for s in [s for s in secimler if s in AYRI_OKUYUCU]:
        sys.exit(f"{s}: bu okuyucu kullanılmıyor, bkz. scripts/pipelines/tuik_arsiv/{AYRI_OKUYUCU[s]}")
    tablolar = [a for a in sys.argv[1:] if a in TABLO_ACIKLAMA] or None
    for s in secimler:
        isle(s, tablolar)


if __name__ == "__main__":
    main()
