"""
Taranmis DIE kitap sayfasindan tablo hucrelerini GORUNTUDEN (tesseract) okuyan ikinci okuma.

Neden: 1963-1977 kitaplarinin metin katmani (ABBYY, 2009) rakamlarin arasina bosluk koyuyor ("48 447" ->
"4 8 4 4 7"); koordinat okumasi bunlari ayri sayi sanip satiri tutarsiz birakiyor. Bu modul ayni hucreyi
sayfa goruntusunden bagimsiz olarak okur. Hucre sinirlari metin katmanindan bulunan sutun kenarlaridir;
goruntu ile metin katmani arasindaki yatay/dikey kayma sayfa basina olculur (metin katmaninin karakter
kutulari ile goruntunun murekkep izinin en cok ortustugu kaydirma).

Tahmin yok: bir oy hucresi icin birkac aday cikar (ham rakamlar; sutun cizgisinin '1' okunmasi icin bastaki /
sondaki '1' atilmis hali); yalniz kitabin ayni satirdaki yuzdesini tutan aday secilir. Satirin kabulu
cagiranin isidir (extract_mahalli.dogrula: parti toplami == gecerli oy ve her yuzde kendi oyunu tutmali).
"""
import functools
import pathlib
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

DPI = 300
IZIN = "0123456789.—-"


@functools.lru_cache(maxsize=6)
def goruntu(pdf_yolu, no, onbellek):
    """Sayfanin 300 dpi gri goruntusu (onbellekte PNG)."""
    d = pathlib.Path(onbellek)
    d.mkdir(parents=True, exist_ok=True)
    yol = d / f"{no:04d}.png"
    if not yol.exists():
        kok = d / f"_{no:04d}"
        subprocess.run(["pdftoppm", "-f", str(no), "-l", str(no), "-r", str(DPI), "-gray", "-png", "-singlefile",
                        str(pdf_yolu), str(kok)], check=True)
        pathlib.Path(str(kok) + ".png").rename(yol)
    return Image.open(yol).convert("L")


_KAYMA = {}
_ONBELLEK = {"yol": None, "hucre": {}, "kayma": {}}


def onbellek_ac(yol):
    """Tesseract sonuclari icin disk onbellegi (.cache altinda; ayni girdiye ayni cikti)."""
    import json
    _ONBELLEK["yol"] = pathlib.Path(yol)
    if _ONBELLEK["yol"].exists():
        d = json.loads(_ONBELLEK["yol"].read_text(encoding="utf-8"))
        _ONBELLEK["hucre"], _ONBELLEK["kayma"] = d.get("hucre", {}), d.get("kayma", {})


def onbellek_kaydet():
    import json
    if _ONBELLEK["yol"]:
        _ONBELLEK["yol"].parent.mkdir(parents=True, exist_ok=True)
        _ONBELLEK["yol"].write_text(json.dumps({"hucre": _ONBELLEK["hucre"], "kayma": _ONBELLEK["kayma"]}), encoding="utf-8")


def kayma(page, img, anahtar, png_yolu=None):
    """Goruntu ile metin katmani arasindaki donusum (ax, bx, ay, by): x_goruntu = ax * x + bx (pt), y ayni.
    Sayfanin tamami tesseract'la okunur; sayfada bir kez gecen (>= 3 haneli) sayilar metin katmanindaki ayni
    sayilarla eslenir, kutu merkezlerinden dogru uydurulur (3 pt'den uzak eslesmeler atilip yeniden).
    Kitaplarda kayma 20 pt'yi asabiliyor; olcek ~1."""
    if anahtar in _KAYMA:
        return _KAYMA[anahtar]
    ak = str(anahtar)
    if ak in _ONBELLEK["kayma"]:
        _KAYMA[anahtar] = tuple(_ONBELLEK["kayma"][ak]) if _ONBELLEK["kayma"][ak] else None
        return _KAYMA[anahtar]
    import collections
    import csv
    import io
    sc = img.size[0] / float(page.width)
    if png_yolu is None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name)
            png_yolu = f.name
    out = subprocess.run(["tesseract", str(png_yolu), "-", "--psm", "6", "tsv"], capture_output=True, text=True).stdout
    tw = [(re.sub(r"\D", "", r["text"]), (int(r["left"]) + int(r["width"]) / 2) / sc, (int(r["top"]) + int(r["height"]) / 2) / sc)
          for r in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE) if r.get("text")]
    pw = [(re.sub(r"\D", "", w["text"]), (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2) for w in page.extract_words()]
    tc = collections.Counter(t for t, _, _ in tw if len(t) >= 3)
    pc = collections.Counter(t for t, _, _ in pw if len(t) >= 3)
    ortak = [t for t in tc if tc[t] == 1 and pc.get(t) == 1]
    T = {t: (x, y) for t, x, y in tw}
    P = {t: (x, y) for t, x, y in pw}
    sonuc = None
    if len(ortak) >= 6:
        xs = np.array([(P[t][0], T[t][0]) for t in ortak])
        ys = np.array([(P[t][1], T[t][1]) for t in ortak])
        ax, bx = np.polyfit(xs[:, 0], xs[:, 1], 1)
        ay, by = np.polyfit(ys[:, 0], ys[:, 1], 1)
        m = (np.abs(xs[:, 1] - (ax * xs[:, 0] + bx)) < 3) & (np.abs(ys[:, 1] - (ay * ys[:, 0] + by)) < 3)
        if m.sum() >= 6:
            ax, bx = np.polyfit(xs[m, 0], xs[m, 1], 1)
            ay, by = np.polyfit(ys[m, 0], ys[m, 1], 1)
            sonuc = (float(ax), float(bx), float(ay), float(by))
    if sonuc is None:
        sonuc = _geometrik_kayma(out, sc, page)
    _KAYMA[anahtar] = sonuc
    _ONBELLEK["kayma"][ak] = list(sonuc) if sonuc else None
    return sonuc


def _geometrik_kayma(tsv, sc, page):
    """Metin katmani rakamlari okunamayacak kadar bozuksa (ortak sayi < 6): sozcuk kutularinin konumlari yine
    dogrudur (ABBYY karakteri yanlis tanimis ama yerini bulmus). Tesseract ve metin katmani kutu merkezleri
    arasinda en cok cifti 1,5 pt icinde ortusturen oteleme (olcek 1) aranir; sozcuklerin en az %30'u ortusmeli."""
    import csv
    import io
    T = np.array([((int(r["left"]) + int(r["width"]) / 2) / sc, (int(r["top"]) + int(r["height"]) / 2) / sc)
                  for r in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
                  if (r.get("text") or "").strip() and int(r.get("conf", "0").split(".")[0] or 0) >= 0])
    P = np.array([((w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2) for w in page.extract_words()])
    if len(T) < 30 or len(P) < 30:
        return None
    d = (T[:, None, :] - P[None, :, :]).reshape(-1, 2)
    d = d[(np.abs(d[:, 0]) < 40) & (np.abs(d[:, 1]) < 40)]
    if not len(d):
        return None
    h, xe, ye = np.histogram2d(d[:, 0], d[:, 1], bins=160, range=[[-40, 40], [-40, 40]])
    i, j = np.unravel_index(h.argmax(), h.shape)
    dx, dy = (xe[i] + xe[i + 1]) / 2, (ye[j] + ye[j + 1]) / 2
    for _ in range(2):
        m = (np.abs(d[:, 0] - dx) < 1.5) & (np.abs(d[:, 1] - dy) < 1.5)
        dx, dy = d[m, 0].mean(), d[m, 1].mean()
    eslesen = sum(1 for p in P if np.min(np.abs(T[:, 0] - p[0] - dx) + np.abs(T[:, 1] - p[1] - dy)) < 3)
    if eslesen < 0.3 * min(len(T), len(P)):
        return None
    return (1.0, float(dx), 1.0, float(dy))


def _tesseract(kirpinti):
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        kirpinti.save(f.name)
        return subprocess.run(["tesseract", f.name, "-", "--psm", "7", "-c", f"tessedit_char_whitelist={IZIN}"],
                              capture_output=True, text=True).stdout.strip()


def satir_metinleri(img, page, kenarlar, y, donusum, ilk_genislik=48):
    """Satirin her sutun hucresinin tesseract metni. Hucre: onceki kenar + 3 pt .. kenar + 1.5 pt (sutun
    cizgileri hucre disinda kalsin); ilk sutun kenardan ilk_genislik pt geriye. donusum: kayma()."""
    sc = img.size[0] / float(page.width)
    ax, bx, ay, by = donusum
    X = lambda x: int((ax * x + bx) * sc)  # noqa: E731
    Y = lambda v: int((ay * v + by) * sc)  # noqa: E731
    kutular = []
    for k, e in enumerate(kenarlar):
        x0 = kenarlar[k - 1] + 3 if k else e - ilk_genislik
        kutular.append((X(x0), Y(y - 3.5), X(e + 1.5), Y(y + 10)))
    anahtar = f"{img.size}:{getattr(img, 'filename', '')}:{kutular}"
    if anahtar in _ONBELLEK["hucre"]:
        return _ONBELLEK["hucre"][anahtar]
    with ThreadPoolExecutor(4) as ex:
        sonuc = list(ex.map(lambda b: _tesseract(img.crop(b)), kutular))
    _ONBELLEK["hucre"][anahtar] = sonuc
    return sonuc


def sayi_adaylari(t):
    """Hucre metninden tam sayi adaylari. '—' / '-' tek basina = 0 (kitapta sifir); bos = None."""
    if not t:
        return [None]
    r = re.sub(r"[^\d]", "", t)
    if not r:
        return [0] if re.search(r"[—-]", t) else [None]
    out = [r]
    if len(r) > 1 and r[0] == "1":
        out.append(r[1:])
    if len(r) > 1 and r[-1] == "1":
        out.append(r[:-1])
    if len(r) > 2 and r[0] == "1" and r[-1] == "1":
        out.append(r[1:-1])
    return list(dict.fromkeys(int(x) for x in out if x))


def yuzde_adaylari(t):
    if not t:
        return [None]
    out = [float(m) for m in re.findall(r"\d{1,3}\.\d", t)]
    r = re.sub(r"[^\d]", "", t)
    if not out and 2 <= len(r) <= 3:
        out.append(float(r[:-1] + "." + r[-1]))
    for m in list(out):
        s = f"{m:.1f}"
        if s.startswith("1") and len(s) > 3:
            out.append(float(s[1:]))
    if not out:
        return [0.0] if re.search(r"[—-]", t) else [None]
    return list(dict.fromkeys(x for x in out if x <= 100))


def coz(metin, partiler, oncu, gecerli=None, yedek=None):
    """metin: {alan: tesseract metni}; yedek: ayni satirin metin katmani okumasi {alan: deger}.
    - secmen / oy kullanan / katilim: iki okumanin adaylarindan katilim yuzdesini (0,1 puan) tutan tek ikili.
    - gecerli: verilmisse o; yoksa iki okumanin adaylari (dogrula parti toplamiyla karar verir: tek aday kalmali).
    - parti: iki okumanin adaylarindan kitabin yuzdesini tutan tek oy degeri. Yuzdesi okunmayan sifirdan buyuk
      oy kabul edilmez (sutun cizgisi / leke '4', '1' okunabiliyor). Hicbiri tutmazsa oy bos, okunan yuzde
      korunur (extract_mahalli.dogrula o tek hucreyi toplam + yuzdeyle bulabilir).
    Dondurur: {alan: deger}."""
    yedek = yedek or {}

    def adaylar(alan, yuzde=False):
        c = (yuzde_adaylari if yuzde else sayi_adaylari)(metin.get(alan))
        y = yedek.get(alan)
        if isinstance(y, float if yuzde else int):
            c = c + [y]
        return [x for x in dict.fromkeys(c) if x is not None]

    v = {"sandik": None, "secmen": None, "oyKullanan": None, "katilim%": None, "gecerliOy": None}
    sa = adaylar("sandik")
    v["sandik"] = sa[0] if len(set(sa)) == 1 else (yedek.get("sandik") if isinstance(yedek.get("sandik"), int) else None)
    ikili = {(s_, k, t) for s_ in adaylar("secmen") for k in adaylar("oyKullanan") for t in adaylar("katilim%", True)
             if s_ and k and k <= s_ and abs(100 * k / s_ - t) <= 0.1}
    if len({(s_, k) for s_, k, _ in ikili}) == 1:
        v["secmen"], v["oyKullanan"], v["katilim%"] = min(ikili)
    g = gecerli if isinstance(gecerli, int) else None
    if g is None:
        ga = [x for x in adaylar("gecerliOy") if not v["oyKullanan"] or x <= v["oyKullanan"]]
        g = ga[0] if len(set(ga)) == 1 else None
    v["gecerliOy"] = g
    for p in partiler:
        if p not in metin:
            continue
        oc, yc = adaylar(p), adaylar(p + "%", True)
        secilen = None
        if isinstance(g, int) and g > 0:
            uyan = {(o, y) for o in oc for y in yc if o and abs(100 * o / g - y) <= 0.1}
            if len({o for o, _ in uyan}) == 1:
                secilen = min(uyan)
        sifirdan_buyuk = [x for x in oc if x]
        yuzdeler = {y for y in yc if y > 0}
        if secilen:
            v[p], v[p + "%"] = secilen
        elif not sifirdan_buyuk and not yuzdeler:
            v[p], v[p + "%"] = (0 if 0 in oc else None), (0.0 if 0.0 in yc else None)
        else:
            v[p], v[p + "%"] = None, (yuzdeler.pop() if len(yuzdeler) == 1 else None)
    return v
