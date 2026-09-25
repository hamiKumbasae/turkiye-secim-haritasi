"""
DIE Mahalli Idareler Secimi Sonuclari 25.3.1984 (0012953) -> kaynak katmani,
IKI BAGIMSIZ OCR okumasi + kitabin ic kisitlariyla:

  data/kaynaklar/tuik/yerel/1984yerel/<tablo>.json
  data/kaynaklar/tuik/yerel/1984yerel/ocr/p<sayfa>.json   (goruntu OCR okumalari, onbellek)

Neden ayri okuyucu: kitabin metin katmani harf harf ve zayif OCR ('*' = 4,
'386' -> '366', tireler kayip). extract_mahalli.py'nin 1984 okumasinda
satirlarin ~%35'i tutarsiz kaliyordu; ustelik tek bir hucre tutmayinca degeri
toplamdan GERI HESAPLIYORDU (ocrDuzeltme 'toplam + yüzde') - bu, 1994/1999
hattinin 'tahmin yok' kuraliyla celisir. Bu okuyucu:

  1. Satir/sutun iskeleti extract_mahalli.py ile ayni (metin katmani, sol/sag
     yuz hizalamasi, satir tipleri).
  2. Her sutun, sayfa goruntusunden ayri bir serit olarak macOS Vision ile
     yeniden okunur (vision_ocr.swift). Her hucre icin ADAY degerler: metin
     katmani okumasi + Vision'in (ilk 3 aday) okumalari. Hicbir deger
     hesaplanmaz; aday yalnizca sayfadan okunmus bir dizgidir.
  3. Bir satir `tutarli` ancak adaylardan TEK bir secimle su kisitlarin hepsi
     tutuyorsa: parti oylari toplami = gecerli oy; oyu olan her partinin
     kitaptaki yuzdesi = oy / gecerli; katilim % = oy kullanan / secmen;
     gecerli % = gecerli / oy kullanan. Birden cok farkli cozum varsa satir
     `belirsiz` kalir. Hucre bos (her iki okumada da) ise '-' (0) sayilir;
     toplam kisiti bunu dogrular.
  4. Sag yuzu eslesmeyen / cozulemeyen satir icin komsu sag satirlar denenir;
     esleme ancak tek bir sag satir tam cozum veriyorsa kabul edilir.

Vision okumasi yalnizca macOS'ta uretilebilir; onbellek depoda oldugundan
okuyucu baska sistemde onbellekten calisir.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/extract_mahalli_1984.py [tablo ...]
"""
import collections
import concurrent.futures
import itertools
import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import die_tablo  # noqa: E402
import extract_mahalli as em  # noqa: E402

SECIM = "1984yerel"
CFG = em.KITAPLAR[SECIM]
PDF = em.RAW / f"{CFG['demirbas']}.pdf"
OUT = em.OUT / SECIM
OCRDIR = OUT / "ocr"
VBIN = HERE / "vision_ocr"
# Vision gecisleri: (dpi, karo yuksekligi pt, dikey bindirme pt, yatay kaydirma pt).
# Farkli olcek/kesitler farkli hucreleri yakaliyor; adaylar birlestirilir.
GECISLER = [(300, 120, 24, 0), (400, 90, 30, 22)]
TESSERACT_PSM = (6, 11)   # tesseract yalnizca ilk gecisin karolarinda
AYAR = {"gecisler": [list(g) for g in GECISLER], "tesseractPsm": list(TESSERACT_PSM)}
PARTILER = CFG["partiler"]
SOL, SAG = CFG["sol"], CFG["sag"]
# Tolerans (yuzde puani): katilim ve gecerli % kitapta duzgun yuvarlanmis
# (cozulen satirlarda fark hic 0,05'i gecmiyor); parti yuzdelerinde %4'unde
# 0,06-0,08 fark var (yuzdeler 100'e tamamlanmis olabilir).
TOL = 0.1
TOL_ON = 0.051
PENCERE = 3        # sag yuz yeniden hizalamada denenen komsu satir sayisi


# --- Vision okumasi -------------------------------------------------------------
def _karolar(kenarlar, sol, y_ust, y_alt, h, bindir, kay):
    """Ust uste binen karolar (x0, y0, x1, y1), pt: 3 sutun genisliginde, h
    yuksekliginde. Uzun seritleri Vision kucultup hucrelerin cogunu
    kaciriyor; kisa karolarda okunan hucre sayisi ~4 kat."""
    xs = []
    for k in range(0, len(kenarlar), 2):
        x0 = (kenarlar[k - 1] - 6) if k else (kenarlar[0] - (50 if sol else 40))
        xs.append((x0 + kay, kenarlar[min(k + 2, len(kenarlar) - 1)] + 16 + kay))
    xs.insert(0, (xs[0][0] - kay, xs[0][1] - kay)) if kay else None
    out = []
    y = y_ust
    while y < y_alt:
        for x0, x1 in xs:
            out.append((x0, y, x1, min(y_alt, y + h)))
        y += h - bindir
    return out


def _vision_calistir(pngler):
    if not VBIN.exists():
        subprocess.run(["swiftc", "-O", str(HERE / "vision_ocr.swift"), "-o", str(VBIN)], check=True)
    parca = max(1, len(pngler) // 8 + 1)
    islem = [subprocess.Popen([str(VBIN), *pngler[i:i + parca]]) for i in range(0, len(pngler), parca)]
    for p in islem:
        if p.wait():
            raise RuntimeError("vision_ocr hata verdi")


def _tesseract(yol, psm):
    """Tesseract TSV kelimeleri: [(metin, conf 0-1, sol, ust, sag, alt) piksel]."""
    r = subprocess.run(["tesseract", yol, "-", "--psm", str(psm), "-c", "tessedit_char_whitelist=0123456789.-", "tsv"],
                       capture_output=True, text=True, check=True)
    out = []
    for satir in r.stdout.splitlines()[1:]:
        f = satir.split("\t")
        if len(f) == 12 and f[11].strip():
            x, y, w, h = map(int, f[6:10])
            out.append((f[11].strip(), round(max(0.0, float(f[10])) / 100, 2), x, y, x + w, y + h))
    return out


def goruntu_okumalari(istek):
    """istek: {sayfa_no: (kenarlar, sol)}. Sayfa goruntusu karolara bolunup
    iki OCR motoruyla okunur (onbellek: ocr/p<sayfa>.json). Dondurur
    {sayfa_no: {motor: [[metin, conf, y0, y1, x0, x1], ...]}} (pt, pdfplumber
    sayfa koordinati)."""
    OCRDIR.mkdir(parents=True, exist_ok=True)
    sonuc, eksik = {}, {}
    for no, (kenarlar, sol) in istek.items():
        f = OCRDIR / f"p{no:03d}.json"
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            if d["kenarlar"] == [round(e, 2) for e in kenarlar] and d.get("ayar") == AYAR:
                sonuc[no] = d["motorlar"]
                continue
        eksik[no] = (kenarlar, sol)
    if not eksik:
        return sonuc
    doc = die_tablo.ac(PDF)
    with tempfile.TemporaryDirectory() as tmp:
        isler = []
        for no, (kenarlar, sol) in eksik.items():
            pg = doc.pages[no - 1]
            x_min, y_min, x_max, y_max = pg.bbox
            for g, (dpi, h, bindir, kay) in enumerate(GECISLER):
                for n, (x0, y0, x1, y1) in enumerate(_karolar(kenarlar, sol, y_min + 40 + g * h / 2, y_max - 20, h, bindir, kay)):
                    klip = (max(x_min, x0), y0, min(x_max, x1), y1)
                    yol = f"{tmp}/p{no}_{g}_{n}.png"
                    pg.crop(klip).to_image(resolution=dpi).save(yol)
                    isler.append((no, klip, yol, dpi, g))
        _vision_calistir([i[2] for i in isler])
        tess_isler = [(i, psm) for i in isler if i[4] == 0 for psm in TESSERACT_PSM]
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            tess = list(ex.map(lambda ip: _tesseract(ip[0][2], ip[1]), tess_isler))
        ham = collections.defaultdict(lambda: collections.defaultdict(list))

        def ekle(no, motor, klip, dpi, metin, conf, px0, py0, px1, py1):
            x0, y0, x1, y1 = klip
            o = 72 / dpi
            bx = [x0 + px0 * o, y0 + py0 * o, x0 + px1 * o, y0 + py1 * o]
            # karo kenarina degen gozlem kesik olabilir; komsu karo onu tam gorur
            if bx[1] - y0 < 1.5 or y1 - bx[3] < 1.5 or bx[0] - x0 < 1.0 or x1 - bx[2] < 1.0:
                return
            ham[no][motor].append((metin, conf, round(bx[1], 1), round(bx[3], 1), round(bx[0], 1), round(bx[2], 1)))

        for no, klip, yol, dpi, _g in isler:
            for ob in json.loads(pathlib.Path(yol + ".json").read_text())["obs"]:
                ekle(no, "vision", klip, dpi, ob["text"], round(ob["conf"], 2), *ob["box"])
        for ((no, klip, _yol, dpi, _g), _psm), kelimeler in zip(tess_isler, tess):
            for metin, conf, *kutu in kelimeler:
                ekle(no, "tesseract", klip, dpi, metin, conf, *kutu)
    for no, (kenarlar, _sol) in eksik.items():
        motorlar = {m: sorted(set(ham[no][m]), key=lambda o: (o[2], o[5])) for m in ("vision", "tesseract")}
        (OCRDIR / f"p{no:03d}.json").write_text(json.dumps(
            {"sayfa": no, "ayar": AYAR, "kenarlar": [round(e, 2) for e in kenarlar],
             "not": "Sayfa görüntüsünün OCR okumaları. vision: macOS Vision (VNRecognizeTextRequest, accurate, dil "
                    "düzeltmesi kapalı, gözlem başına ilk 3 aday); tesseract: rakam beyaz listesi, psm " +
                    "/".join(map(str, TESSERACT_PSM)) + ". Karolar 3 sütun genişliğinde, üst üste binen; kenara değen "
                    "gözlemler atıldı. Gözlem: [metin, güven, üst y, alt y, sol x, sağ x] pt (pdfplumber sayfa koordinatı).",
             "motorlar": motorlar}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        sonuc[no] = motorlar
    return sonuc


TIRE = re.compile(r"^[\s\-–—_~=•.·']+$")


def yorumla(metin, yuzde):
    """Vision dizgisinden hucre degeri adaylari (yalniz okunanin yorumlari)."""
    t = metin.strip()
    if not t:
        return []
    if TIRE.match(t):
        return [0.0 if yuzde else 0] if "-" in t or "–" in t or "—" in t or "_" in t else []
    t = "".join(em.HARF_RAKAM.get(c, c) for c in t)
    if yuzde:
        m = re.fullmatch(r"(\d{1,3})\s*[.,\-+:·]\s*(\d)", t)
        if m:
            return [float(f"{m.group(1)}.{m.group(2)}")]
        d = re.sub(r"\s", "", t)
        if re.fullmatch(r"\d{2,4}", d) and int(d) <= 1000:
            return [float(d[:-1] + "." + d[-1])]
        return []
    # 1984 kitabinda binlik ayiraci yok: 'dd.d' bicimli dizgi yuzdedir, oy degil
    if re.search(r"\d\s*[.,\-+:·]\s*\d\s*$", t) and not re.search(r"\d{4,}", t):
        return []
    d = re.sub(r"[\s.,']", "", t)
    if re.fullmatch(r"\d{1,9}", d):
        return [int(d)]
    return []


YUZDE_BICIM = re.compile(r"^\s*\d{1,3}\s*[.,\-+:·]\s*\d\s*$")


def _sutun(ks, x1, metin, alanlar, tol):
    """Gozlemin sutunu: sag ucuna en yakin kenar; bicim sutun turuyle celisirse
    (yuzde bicimli dizgi oy sutununda ya da tersi) tolerans icindeki en yakin
    uygun turdeki sutun."""
    sira = sorted(range(min(len(ks), len(alanlar))), key=lambda k: abs(ks[k] - x1))
    yuzde_mi = bool(YUZDE_BICIM.match(metin.strip()))
    uzun_sayi = bool(re.fullmatch(r"\s*\d{4,}\s*", metin))
    for k in sira:
        if abs(ks[k] - x1) > tol:
            return None
        if yuzde_mi and not alanlar[k].endswith("%"):
            continue
        if uzun_sayi and alanlar[k].endswith("%"):
            continue
        return k
    return None


def _ofset(gozlem, page):
    """Vision kutulari ile metin katmani arasindaki (dx, dy): ayni dizgiyi
    tasiyan tek esli sayi kelimelerinin medyani (kutu kenarlari motorlar
    arasinda birkac pt farkli)."""
    ws = [w for w in page.extract_words() if re.fullmatch(r"\d{3,}", w["text"])]
    dx, dy = [], []
    for o in gozlem:
        if re.fullmatch(r"\d{3,}", o[0]):
            c = [w for w in ws if w["text"] == o[0] and abs(w["x1"] - o[5]) < 30 and abs(w["top"] - o[2]) < 30]
            if len(c) == 1:
                dx.append(o[5] - c[0]["x1"])
                dy.append(o[2] - c[0]["top"])
    if len(dx) < 3:
        return 0.0, 0.0
    dx.sort()
    dy.sort()
    return dx[len(dx) // 2], dy[len(dy) // 2]


def goruntu_hucreler(gozlem, page, kenarlar, satir_y, alanlar, motor):
    """Her Vision gozlemini sag kenarina en yakin sutuna (sayilar saga dayali)
    ve ust kenarina en yakin satira ata. Dondurur {satir_i: {alan: set}}."""
    out = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
    if not satir_y:
        return out
    dx, dy = _ofset(gozlem, page)
    for metin, _c, y0, _y1, _x0, x1 in gozlem:
        x1, y0 = x1 - dx, y0 - dy
        k = _sutun(kenarlar.at(y0), x1, metin, alanlar, 14)
        if k is None:
            continue
        i = min(range(len(satir_y)), key=lambda i: abs(satir_y[i] - y0))
        if abs(satir_y[i] - y0) <= 3.5:
            for v in yorumla(metin, alanlar[k].endswith("%")):
                out[i][alanlar[k]][v].add(motor)
    return out


def _coz4(A, b):
    """4x4 dogrusal sistem (Gauss eleme)."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-9:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


class Kenarlar:
    """Sutun sag kenarlari, sayfa carpikligina gore yerel: kenar_k(y) =
    e_k + d(e_k, y), d(x, y) = a + b*x + c*y + e*x*y (x, y normlu). Bazi sag
    yuzler egik/bukuk taranmis: sag altta kayma 14 pt'ye cikiyor (sutun
    araligi ~45 pt); sabit kenarlar degeri komsu sutuna atiyordu. Model
    sayfadaki sayi hucrelerinin sag uclarina (saga dayali) yinelemeli oturtulur."""

    def __init__(self, page, kenarlar):
        self.e = list(kenarlar)
        self.k = [0.0, 0.0, 0.0, 0.0]
        ws = [w for w in page.extract_words() if re.fullmatch(r"[\d.,*\-]+", w["text"])]
        ws.sort(key=lambda w: (round(w["top"]), w["x0"]))
        hucre = []
        for w in ws:
            if hucre and abs(hucre[-1][1] - w["top"]) < 2.5 and w["x0"] - hucre[-1][0] < 5:
                hucre[-1][0] = w["x1"]
            else:
                hucre.append([w["x1"], w["top"]])
        for tol in (14, 10, 7, 5):
            A = [[0.0] * 4 for _ in range(4)]
            b = [0.0] * 4
            n = 0
            for x1, y in hucre:
                ks = self.at(y)
                k = min(range(len(ks)), key=lambda k: abs(ks[k] - x1))
                if abs(ks[k] - x1) > tol:
                    continue
                f = self._f(self.e[k], y)
                r = x1 - self.e[k]
                for i in range(4):
                    b[i] += f[i] * r
                    for j in range(4):
                        A[i][j] += f[i] * f[j]
                n += 1
            if n < 20:
                break
            yeni = _coz4([[A[i][j] + (1e-3 if i == j else 0) for j in range(4)] for i in range(4)], b)
            if yeni:
                self.k = yeni

    @staticmethod
    def _f(x, y):
        u, v = (x - 300) / 100, (y - 450) / 100
        return [1.0, u, v, u * v]

    def at(self, y):
        return [e + sum(a * f for a, f in zip(self.k, self._f(e, y))) for e in self.e]


def metin_hucreler(page, kenarlar, satir_y, alanlar):
    """Metin katmanindan hucre dizgileri: hucre sinirlari icindeki kelime
    parcalari soldan saga birlestirilir ('5' '1' '.8' -> '51.8'). die_tablo
    izgarasinin parca gruplamasindan bagimsiz ikinci bir metin katmani
    okumasi. Dondurur {satir_i: {alan: set}}."""
    out = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
    if not satir_y:
        return out
    hucre = collections.defaultdict(list)
    for w in page.extract_words(keep_blank_chars=False, use_text_flow=False):
        if re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,}", w["text"]):
            continue
        ks = kenarlar.at(w["top"])
        k = next((k for k, e in enumerate(ks) if w["x1"] <= e + 4), None)
        if k is None or k >= len(alanlar) or (k == 0 and w["x1"] < ks[0] - 45):
            continue
        i = min(range(len(satir_y)), key=lambda i: abs(satir_y[i] - w["top"]))
        if abs(satir_y[i] - w["top"]) <= 3.5:
            hucre[(i, k)].append(w)
    for (i, k), ws in hucre.items():
        ws.sort(key=lambda w: w["x0"])
        metin = "".join(w["text"] for w in ws)
        for v in yorumla(metin, alanlar[k].endswith("%")):
            out[i][alanlar[k]][v].add("metin")
    return out


# --- satir iskeleti (extract_mahalli.tablo_oku + konumlar) -------------------------
def tablo_oku(pdf, ilk, son):
    ciftler, eslesmeyen = [], []
    no = ilk
    while no <= son:
        pg = pdf.pages[no - 1]
        if em._sol_mu(pg) and no < len(pdf.pages) and not em._sol_mu(pdf.pages[no]):
            ciftler.append((no, no + 1))
            no += 2
        else:
            eslesmeyen.append({"sayfa": no, "neden": "eşi olan sol/sağ yüz yok"})
            no += 1
    yuzler = []
    kenar_sol = kenar_sag = None
    for a, b in ciftler:
        L, kl = die_tablo.sayfa_tablosu(pdf.pages[a - 1], 160, len(SOL), None, kelime_duzelt=em.kelime_duzelt,
                                        hazir_kenarlar=kenar_sol)
        R, kr = die_tablo.sayfa_tablosu(pdf.pages[b - 1], 120, len(SAG), None, etiketsiz=True,
                                        kelime_duzelt=em.kelime_duzelt, hazir_kenarlar=kenar_sag)
        if L is None or R is None:
            eslesmeyen.append({"sayfa": [a, b], "neden": "sütunlar bulunamadı"})
            continue
        if kenar_sol is None and all(kl):
            kenar_sol = kl
        if kenar_sag is None and all(kr):
            kenar_sag = kr
        sol = [{"etiket": e, "v": em._satir_degerleri(SOL, v), "y": y}
               for e, v, y, h in L if len(re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]", e)) >= 2 and isinstance(v[1], int)
               and not re.match(r"^\W*TABL[OE]\b", e)]
        sag = [{"v": em._satir_degerleri(SAG, v), "y": y} for e, v, y, h in R]
        yuzler.append({"sayfa": [a, b], "sol": sol, "sag": sag, "kl": kl, "kr": kr})
    return yuzler, eslesmeyen


# --- kisit cozucu ------------------------------------------------------------------
def _uyar(o, y, g):
    return abs(100 * o / g - y) <= TOL


def coz(aday):
    """aday: {alan: {deger: kaynaklar}}. Tum kisitlari saglayan, okunmus
    degerlerden kurulu farkli cozumlerin listesi. Parti: oyu varsa okunmus bir
    yuzdesi oya uymali (yuzde hucresi hic okunamadiysa yuzdesiz kabul edilir,
    teyidi _zayif'a kalir); 0 ('-') ancak o hucrede sifir disi aday yoksa ya
    da tire okunduysa."""
    cozumler = {}
    for g in sorted(v for v in aday.get("gecerliOy", ()) if isinstance(v, int) and v > 0):
        # oncu alanlar
        on = []
        for s, k, kat in itertools.product(aday.get("secmen") or {None}, aday.get("oyKullanan") or {None},
                                           aday.get("katilim%") or {None}):
            if not (isinstance(s, int) and isinstance(k, int) and isinstance(kat, float) and s > 0):
                continue
            if k > s or g > k or abs(100 * k / s - kat) > TOL_ON:
                continue
            for gy in aday.get("gecerli%") or ():
                if isinstance(gy, float) and abs(100 * g / k - gy) <= TOL_ON:
                    on.append((s, k, kat, gy))
        if not on:
            continue
        # parti ciftleri
        secenek = []
        for p in PARTILER:
            oylar = {o for o in aday.get(p, ()) if isinstance(o, int)}
            yuzler = {y for y in aday.get(p + "%", ()) if isinstance(y, float)}
            cift = set()
            for o in oylar | {0}:
                if o == 0:
                    # '-' : oy yok ve yuzde yok/0
                    if not oylar - {0} and not yuzler - {0.0}:
                        cift.add((0, None))
                    elif 0 in oylar and (not yuzler or 0.0 in yuzler):
                        cift.add((0, None))
                    continue
                uyan = [y for y in yuzler if y > 0 and _uyar(o, y, g)]
                for y in uyan:
                    cift.add((o, y))
                if not uyan and not {y for y in yuzler if y > 0}:
                    # yuzde hucresi hic okunamadi: oy yalnizca toplam ve okuma
                    # sayisiyla teyit edilebilir (bkz. _zayif)
                    cift.add((o, None))
            if not cift:
                break
            secenek.append(sorted(cift))
        if len(secenek) != len(PARTILER):
            continue
        for kombi in itertools.product(*secenek):
            if sum(o for o, _ in kombi) != g:
                continue
            for s, k, kat, gy in on:
                anahtar = (s, k, g, tuple(o for o, _ in kombi))
                cozumler[anahtar] = {"secmen": s, "oyKullanan": k, "katilim%": kat, "gecerliOy": g, "gecerli%": gy,
                                     **{p: o for p, (o, _) in zip(PARTILER, kombi)},
                                     **{p + "%": y for p, (_, y) in zip(PARTILER, kombi) if y is not None}}
    return list(cozumler.values())


def adaylar(sol_v, sag_v, vis_sol, vis_sag):
    """{alan: {deger: {okuma kaynaklari}}}: 'izgara' ve 'metin' metin
    katmanindan (ayni OCR), 'vision' goruntuden (bagimsiz)."""
    a = collections.defaultdict(lambda: collections.defaultdict(set))
    for kaynak in (sol_v, sag_v or {}):
        for k, v in kaynak.items():
            if v is None:
                continue
            if k.endswith("%") and isinstance(v, int):
                # metin katmaninda ondalik noktasi dusmus yuzde: '157' = 15,7
                v = v / 10
            a[k][v].add("izgara")
    for vis in (vis_sol, vis_sag or {}):
        for k, vals in vis.items():
            for v, kay in vals.items():
                a[k][v] |= kay
    return a


def _motorlar(kay):
    """Bagimsiz okuma motorlari: metin katmani (izgara ve metin ayni OCR'dir), Vision, tesseract."""
    return {("metin" if k in ("izgara", "metin") else k) for k in kay}


def _yuzde_sabitler(o, y, taban, tol):
    """Okunan yuzde, tolerans penceresine TEK tam sayi birakiyorsa (kucuk
    birim) o oyu tek basina belirler."""
    if not isinstance(y, float) or not taban:
        return False
    lo, hi = (y - tol) * taban / 100, (y + tol) * taban / 100
    return math.floor(hi) - math.ceil(lo) + 1 <= 1 and math.ceil(lo) <= o <= math.floor(hi)


def _zayif(c, a):
    """Cozumde teyitsiz oy alanlari (gecerli + sifir olmayan partiler): ne
    iki bagimsiz motorla okunmus ne de kendi okunan yuzdesiyle tek degere
    sabitlenmis. '-' (0) sayilmaz: diger alanlar teyitliyken dolu bir hucreyi
    0 okumak toplami eksik birakir; bunu dengelemek icin tek teyitsiz alanin
    tam o kadar fazla okunup yuzdesini de tutturmasi gerekir."""
    out = []
    for k in ["gecerliOy"] + PARTILER:
        if k != "gecerliOy" and not c[k]:
            continue
        if len(_motorlar(a[k].get(c[k], set()))) >= 2:
            continue
        if k == "gecerliOy" and _yuzde_sabitler(c[k], c.get("gecerli%"), c.get("oyKullanan"), TOL_ON):
            continue
        if k != "gecerliOy" and c[k] and _yuzde_sabitler(c[k], c.get(k + "%"), c["gecerliOy"], TOL):
            continue
        out.append(k)
    # yuzdesi okunamamis parti: tek motora dayaniyorsa zaten sayildi; iki
    # motorla okunmussa teyitli (yuzde yalnizca ek bir kontrol)
    return out


def satir_coz(sol, sag, vis_sol, vis_sag):
    """Dondurur (v, durum, adaylar).

    Kisitlar tek basina yetmez: iki yanlis okuma birbirini dengeleyebilir
    (1476+135 ile 1478+133 ayni toplam, yuzdeler +-2 oyu ayirt edemez). Bu
    yuzden bir cozum ancak oy alanlarinin (gecerli + partiler) EN FAZLA BIRI
    tek motora dayaniyorsa kabul edilir: digerleri iki bagimsiz okumayla
    teyitliyse toplam kisiti sonuncuyu kesin belirler, dengeleyen hata
    olamaz. Bu kosulu saglayan en az zayif alanli cozum tek degilse satir
    `belirsiz`. Oncu alanlar (secmen, oy kullanan) cozumler arasinda
    ayrisiyorsa iki motorun birlikte verdigi TEK deger alinir; yoksa bos
    birakilip `belirsizAlan`'a yazilir."""
    a = adaylar(sol["v"], sag["v"] if sag else None, vis_sol, vis_sag)
    cz = coz(a)
    if not cz:
        return None, "tutarsiz", a
    # satir kimligi: oncu alanlardan en az biri bu satirin kendi metin katmani
    # izgarasinda okunmus olmali (goruntu OCR gozlemleri konumla atanir; komsu
    # satirin sayilari bu satira dusebilir)
    cz = [c for c in cz if any("izgara" in a[f].get(c[f], set()) for f in ("secmen", "oyKullanan", "gecerliOy"))]
    if not cz:
        return None, "tutarsiz", a
    zayif = {id(c): _zayif(c, a) for c in cz}
    uygun = [c for c in cz if len(zayif[id(c)]) <= 1]
    if not uygun:
        return None, "teyitsiz", a
    en_az = min(len(zayif[id(c)]) for c in uygun)
    uygun = [c for c in uygun if len(zayif[id(c)]) == en_az]
    oy_anahtar = {(c["gecerliOy"],) + tuple(c[p] for p in PARTILER) for c in uygun}
    if len(oy_anahtar) > 1:
        return None, "belirsiz", a
    v = dict(uygun[0])
    belirsiz = []
    for alan in ("secmen", "oyKullanan", "katilim%", "gecerli%"):
        degerler = {c[alan] for c in uygun}
        if len(degerler) == 1:
            continue
        ortak = [d for d in degerler if len(_motorlar(a[alan].get(d, set()))) >= 2]
        if len(ortak) == 1:
            v[alan] = ortak[0]
        else:
            v[alan] = None
            belirsiz.append(alan)
    v["sandik"] = sol["v"].get("sandik")
    if belirsiz:
        v["_belirsizAlan"] = belirsiz
    if zayif[id(uygun[0])]:
        v["_tekOkuma"] = zayif[id(uygun[0])]
    return v, "tutarli", a


# --- tablo isleme ------------------------------------------------------------------
def tablo_isle(pdf, ilk, son):
    yuzler, eslesmeyen = tablo_oku(pdf, ilk, son)
    vis = goruntu_okumalari({**{y["sayfa"][0]: (y["kl"], True) for y in yuzler},
                             **{y["sayfa"][1]: (y["kr"], False) for y in yuzler}})
    satirlar = []
    istat = collections.Counter()
    for yz in yuzler:
        a, b = yz["sayfa"]
        sol, sag = yz["sol"], yz["sag"]
        KL, KR = Kenarlar(pdf.pages[a - 1], yz["kl"]), Kenarlar(pdf.pages[b - 1], yz["kr"])
        ml, mr = _satir_merkezleri(pdf.pages[a - 1]), _satir_merkezleri(pdf.pages[b - 1])
        ys, yr = [ml.get(s["y"], s["y"]) for s in sol], [mr.get(r["y"], r["y"]) for r in sag]
        vs = metin_hucreler(pdf.pages[a - 1], KL, ys, SOL)
        vr = metin_hucreler(pdf.pages[b - 1], KR, yr, SAG)
        ekler = []
        for motor in ("vision", "tesseract"):
            # ofset her motor icin ayri: kutu kenarlari motordan motora farkli
            ekler += [(vs, goruntu_hucreler(vis[a][motor], pdf.pages[a - 1], KL, ys, SOL, motor)),
                      (vr, goruntu_hucreler(vis[b][motor], pdf.pages[b - 1], KR, yr, SAG, motor))]
        for hedef, ek in ekler:
            for i, d in ek.items():
                for alan, vals in d.items():
                    for v, kay in vals.items():
                        hedef[i][alan][v] |= kay
        esle = _hizala_indeks(sol, sag)
        ts, tr = em._sayfa_tokenleri(pdf.pages[a - 1], True), em._sayfa_tokenleri(pdf.pages[b - 1], False)

        def coz_ij(i, j):
            """Sol i + sag j satiri; metin katmaninin yapisal ayristirmasi
            (extract_mahalli.yapisal_oku: bolunmus parcalar '5' '1' '.8' kisitlara
            gore birlestirilir) ek 'izgara' adayi olarak eklenir."""
            ek_sol = _kopya(vs.get(i, {}))
            ek_sag = _kopya(vr.get(j, {})) if j is not None else {}
            if j is not None and ts.get(sol[i]["y"]) and tr.get(sag[j]["y"]):
                v2 = em.yapisal_oku({"tokSol": ts[sol[i]["y"]], "tokSag": tr[sag[j]["y"]],
                                     "kenarSol": yz["kl"], "kenarSag": yz["kr"]}, CFG)
                for alan, deger in (v2 or {}).items():
                    if deger is not None:
                        (ek_sol if alan in SOL else ek_sag)[alan][deger].add("izgara")
            return satir_coz(sol[i], sag[j] if j is not None else None, ek_sol, ek_sag)

        kullanilan = set()
        sonuc = {}
        for i, s in enumerate(sol):
            j = esle.get(i)
            v, durum, _ = coz_ij(i, j)
            if durum == "tutarli":
                sonuc[i] = (v, durum, j, "hizalama")
                kullanilan.add(j)
            else:
                sonuc[i] = (None, durum, j, None)
        # cozulemeyenler: komsu sag satirlari dene
        for i, s in enumerate(sol):
            if sonuc[i][1] == "tutarli":
                continue
            beklenen = _beklenen_sag(i, sonuc, len(sag))
            bulunan = []
            for j in range(max(0, beklenen - PENCERE), min(len(sag), beklenen + PENCERE + 1)):
                if j in kullanilan:
                    continue
                v, durum, _ = coz_ij(i, j)
                if durum == "tutarli":
                    bulunan.append((j, v))
            if len(bulunan) == 1:
                j, v = bulunan[0]
                sonuc[i] = (v, "tutarli", j, "yenidenHizalama")
                kullanilan.add(j)
        for i, s in enumerate(sol):
            v, durum, j, yontem = sonuc[i]
            istat[durum] += 1
            ham = {**s["v"], **(sag[j]["v"] if j is not None else {})}
            satirlar.append({"etiket": s["etiket"], "v": v if v else ham, "durum": durum, "hizalama": yontem,
                             "sagYok": j is None, "sayfa": [a, b],
                             "sol": adaylar(s["v"], None, vs.get(i, {}), None)})
    return satirlar, eslesmeyen, istat


def _satir_merkezleri(page):
    """die_tablo satir grubunun ilk kelime tepesi -> gruptaki kelimelerin
    medyan tepesi. Satir konumu ilk kelimeden alinirsa bir satirin basibos
    isareti ('-') ya da onceki satirdan kayan bir hane konumu 5 pt'ye kadar
    kaydiriyor ve OCR gozlemleri komsu satira ataniyordu (1984 Kayseri:
    Sukur'un sayilari Incesu'ya)."""
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    out = {}
    for grup in die_tablo._satirlar(words):
        tops = sorted(w["top"] for w in grup)
        out[grup[0]["top"]] = tops[len(tops) // 2]
    return out


def _kopya(hucre):
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for alan, vals in hucre.items():
        for v, kay in vals.items():
            out[alan][v] = set(kay)
    return out


def _hizala_indeks(sol, sag):
    """extract_mahalli._hizala ile ayni DP; {sol_i: sag_j}."""
    n, m = len(sol), len(sag)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    yol = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            sec = [(dp[i + 1][j], "s"), (dp[i][j + 1], "r")]
            p = em._puan(sol[i]["v"], sag[j]["v"], PARTILER)
            if p > 0:
                sec.append((dp[i + 1][j + 1] + p, "e"))
            dp[i][j], yol[i][j] = max(sec, key=lambda x: x[0])
    out, i, j = {}, 0, 0
    while i < n and j < m:
        if yol[i][j] == "e":
            out[i] = j
            i, j = i + 1, j + 1
        elif yol[i][j] == "s":
            i += 1
        else:
            j += 1
    if len(out) < 0.5 * n:
        return {}
    return out


def _beklenen_sag(i, sonuc, m):
    """i. sol satirin sag yuzdeki beklenen sirasi: en yakin cozulmus komsulardan."""
    onceki = next(((k, sonuc[k][2]) for k in range(i - 1, -1, -1) if sonuc[k][1] == "tutarli" and sonuc[k][2] is not None), None)
    sonraki = next(((k, sonuc[k][2]) for k in range(i + 1, len(sonuc)) if sonuc[k][1] == "tutarli" and sonuc[k][2] is not None), None)
    if onceki:
        return min(m - 1, onceki[1] + (i - onceki[0]))
    if sonraki:
        return max(0, sonraki[1] - (sonraki[0] - i))
    return min(m - 1, sonuc[i][2] if sonuc[i][2] is not None else i)


def sol_coz(a):
    """Sag yuz cozulemeyen satirda oncu alanlar: (secmen, oy kullanan,
    katilim %) katilim kisitini TEK sekilde saglayan okunmus degerler; sandik
    (kisiti yok) iki bagimsiz motor ayni degeri okuduysa."""
    cz = {(s_, k, kat) for s_ in a.get("secmen", {}) for k in a.get("oyKullanan", {}) for kat in a.get("katilim%", {})
          if isinstance(s_, int) and isinstance(k, int) and isinstance(kat, float) and 0 < k <= s_
          and abs(100 * k / s_ - kat) <= TOL_ON}
    if len(cz) > 1:
        cz = {c for c in cz if all(len(_motorlar(a[f].get(v, set()))) >= 2 for f, v in zip(("secmen", "oyKullanan"), c))}
    out = dict(zip(("secmen", "oyKullanan", "katilim%"), next(iter(cz)))) if len(cz) == 1 else {}
    return out


def _sandik(a):
    ortak = [v for v, kay in a.get("sandik", {}).items() if isinstance(v, int) and len(_motorlar(kay)) >= 2]
    return ortak[0] if len(ortak) == 1 else None


DURUM_ACIKLAMA = {
    "tutarli": "toplam, parti yüzdeleri, katılım ve geçerli % tutuyor; sıfır olmayan oy alanlarından en fazla biri tek okumaya dayanıyor",
    "teyitsiz": "kısıtları sağlayan çözüm var ama oy alanlarından ikisi ya da fazlası yalnızca tek bir okumaya dayanıyor (dengeleyen OCR hatası dışlanamıyor)",
    "belirsiz": "kısıtları sağlayan birden çok farklı oy çözümü var",
    "tutarsiz": "okunan adaylardan kısıtları sağlayan çözüm yok",
}


def isle(tablolar):
    pdf = die_tablo.ac(PDF)
    il_ad = em.il_adlari()
    ilce_kume = em.genel_ilceler(CFG["genelIlce"])
    ilce_sira = {}
    for tablo, (ilk, son) in CFG["tablolar"].items():
        if tablolar and tablo not in tablolar and tablo != "il_genel_meclisi":
            continue
        satirlar, eslesmeyen, istat = tablo_isle(pdf, ilk, son)
        satirlar, eksik_il, ilsiz = em.tiplendir(satirlar, il_ad, ilce_kume, tablo, ilce_sira, CFG.get("bbToplamSirasi"))
        if tablo == "il_genel_meclisi":
            for s in satirlar:
                if s["tip"] == "ilce" and s["plaka"]:
                    ilce_kume.setdefault(s["plaka"], set()).add(em._anahtar(s["etiket"]))
                    ilce_sira.setdefault(s["plaka"], []).append(em._anahtar(s["etiket"]))
            if tablolar and tablo not in tablolar:
                continue
        kayitlar = []
        for s in satirlar:
            v, durum = s["v"], s["durum"]
            okuma = {"hizalama": s["hizalama"]} if s["hizalama"] else {}
            if durum == "tutarli":
                oy = {p: v[p] for p in PARTILER if v.get(p)}
                on = {"secmen": v.get("secmen"), "oyKullanan": v.get("oyKullanan"), "katilim%": v.get("katilim%")}
                g = v["gecerliOy"]
                yuzde = {p: v[p + "%"] for p in PARTILER if v.get(p) and isinstance(v.get(p + "%"), float)}
                if v.get("_tekOkuma"):
                    okuma["tekOkuma"] = v["_tekOkuma"]
                if v.get("_belirsizAlan"):
                    okuma["belirsizAlan"] = v["_belirsizAlan"]
            else:
                oy, g, yuzde = {}, None, {}
                on = sol_coz(s["sol"])
            r = {"tip": s["tip"], "plaka": s["plaka"], "adKaynakta": s["etiket"], "ustIlce": s["ustIlce"],
                 "sandik": _sandik(s["sol"]), "secmen": on.get("secmen"), "oyKullanan": on.get("oyKullanan"),
                 "katilim": on.get("katilim%"), "gecerliOy": g,
                 "oy": dict(sorted(oy.items(), key=lambda kv: -kv[1])), "yuzde": yuzde,
                 "kontrol": {"durum": durum}, "sayfa": s["sayfa"]}
            if s["sagYok"] and durum != "tutarli":
                r["kontrol"]["sagSayfaEslesmedi"] = True
            if okuma:
                r["okuma"] = okuma
            if s.get("ilAdiOkunamadi"):
                r["ilAdiOkunamadi"] = True
            r["kazanan"] = next(iter(r["oy"]), None)
            kayitlar.append(r)
        say = lambda f: sum(1 for r in kayitlar if f(r))  # noqa: E731
        veri = {
            "secim": SECIM, "tablo": tablo, "aciklama": em.TABLO_ACIKLAMA[tablo],
            "kaynak": {"ana": "tuik", "yayin": CFG["yayin"], "demirbas": CFG["demirbas"],
                       "url": f"https://kutuphane.tuik.gov.tr/pdf/{CFG['demirbas']}.pdf",
                       "ham": f"data/raw/tuik/mahalli-kitap/{CFG['demirbas']}.pdf", "sayfalar": [ilk, son],
                       "okuyucu": "scripts/pipelines/tuik_arsiv/extract_mahalli_1984.py",
                       "ocr": f"data/kaynaklar/tuik/yerel/{SECIM}/ocr/",
                       "not": "DİE kitabındaki belediye/ilçe düzeyi değerler ilçe seçim kurullarının birleştirme tutanaklarından "
                              "(kitabın açıklaması). Üç okuma (metin katmanı, macOS Vision, tesseract) aday verir; hiçbir değer "
                              "hesaplanmaz. Durumlar: " + "; ".join(f"{k}: {v}" for k, v in DURUM_ACIKLAMA.items()) +
                              ". Tutarlı olmayan satırda oy yazılmaz; seçmen/oy kullanan/katılım yalnızca katılım kısıtıyla tek "
                              "çözümse, sandık iki motor aynı okuduysa yazılır."},
            "partiler": PARTILER,
            "ozet": {"satir": len(kayitlar), **{t: say(lambda r, t=t: r["tip"] == t) for t in ("il", "ilce", "belde")},
                     **{d: say(lambda r, d=d: r["kontrol"]["durum"] == d) for d in DURUM_ACIKLAMA},
                     "tekOkumaAlanli": say(lambda r: r.get("okuma", {}).get("tekOkuma")),
                     "eksikIl": eksik_il, "ilSatiriTaramadaYok": ilsiz, "eslesmeyenSayfa": eslesmeyen},
            "satirlar": kayitlar,
        }
        (OUT / f"{tablo}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
        print(tablo, {k: v for k, v in veri["ozet"].items() if k not in ("eslesmeyenSayfa",)})


def main():
    isle([a for a in sys.argv[1:] if a in CFG["tablolar"]] or None)


if __name__ == "__main__":
    main()
