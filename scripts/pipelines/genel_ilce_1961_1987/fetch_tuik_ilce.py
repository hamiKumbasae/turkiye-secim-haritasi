"""
TUIK secimdagitimapp'ten (https://biruni.tuik.gov.tr/secimdagitimapp/secim.zul)
"Secim cevresi ve ilcelere gore milletvekili genel secimi sonuclari" tablosunu,
verilen her yil icin tum illerin (secim cevrelerinin) tamami icin indirir ve
data/raw/tuik/secimdagitimapp-ilce-1961-1987/<yil>/<NN>-<il>.html (1961-1987)
ya da data/raw/tuik/secimdagitimapp-ilce-1991-2023/<secim>/<NN>-<il>.html
(1991-2023; <secim> projenin anahtari: 2015Haziran, 2015Kasim, ...) olarak yazar.

Uygulama bir ZK 2.3 sayfasi: tarayici olmadan, ZK'nin AU protokolune (POST
/secimdagitimapp/zkau) dogrudan onSelect/onClick komutlari gonderilerek
suruluyor: tablo -> yil -> il secilir, "Raporu Olustur" tiklanir, cevaptaki
redirect (rapory.tuik.gov.tr/<zaman-damgasi>.html) indirilir. Mevcut dosyalar
atlanir (kaldigi yerden devam eder). Sunucuyu yormamak icin istekler sirali
ve beklemeli.

Kullanim:
  python3 scripts/pipelines/genel_ilce_1961_1987/fetch_tuik_ilce.py 1961 1965 ...
  python3 scripts/pipelines/genel_ilce_1961_1987/fetch_tuik_ilce.py 1991 "2015 (7 Haziran)" ...
"""
import html
import http.cookiejar
import pathlib
import re
import socket
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from common.turkish_text import fold  # noqa: E402

socket.setdefaulttimeout(60)
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
RAW = ROOT / "data" / "raw" / "tuik"
BASE = "https://biruni.tuik.gov.tr"
APP = BASE + "/secimdagitimapp/secim.zul"
TABLO = "ilçelere göre"


def _items(x):
    return [(i, re.sub(r"<[^>]+>|\s+", " ", html.unescape(b)).strip())
            for i, b in re.findall(r'<tr id="(z_[^"]+)"[^>]*z.type="Lit"[^>]*>(.*?)</tr>', x, re.S)]


def _new_listbox(r):
    return re.search(r'<d>(z_[^<]+)</d>\s*<d><!\[CDATA\[\s*<div id="\1" z.type="zul.sel.Libox"', r).group(1)


def hedef_klasor(year: str) -> pathlib.Path:
    """TUIK yil etiketi ('2015 (7 Haziran)') -> arsiv klasoru."""
    if int(year[:4]) <= 1987:
        return RAW / "secimdagitimapp-ilce-1961-1987" / year
    ay = {"7 Haziran": "Haziran", "1 Kasım": "Kasim"}
    m = re.fullmatch(r"(\d{4}) \((.+)\)", year)
    return RAW / "secimdagitimapp-ilce-1991-2023" / (m.group(1) + ay[m.group(2)] if m else year)


def fetch_year(year: str):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0 (secim-haritasi veri arsivi)")]
    page = op.open(APP).read().decode("utf-8", "ignore")
    dtid = re.search(r'z.dtid="([^"]+)"', page).group(1)
    action = re.search(r'zk_action="([^"]+)"', page).group(1)

    def au(cmd, uuid, data):
        p = {"dtid": dtid, "cmd.0": cmd, "uuid.0": uuid}
        for i, d in enumerate(data):
            p[f"data.{i}"] = d
        req = urllib.request.Request(BASE + action, data=urllib.parse.urlencode(p).encode())
        return op.open(req).read().decode("utf-8", "ignore")

    tablo_lb = re.search(r'<div id="(z_[^"]+)" z.type="zul.sel.Libox"[^>]*style="width:550px', page).group(1)
    tablo = [i for i, l in _items(page) if TABLO in l][0]
    r = au("onSelect", tablo_lb, [tablo, tablo])
    yil_lb = _new_listbox(r)
    yil = [i for i, l in _items(r) if l == year][0]
    r = au("onSelect", yil_lb, [yil, yil])
    iller, il_lb = _items(r), _new_listbox(r)
    rapor_btn = re.findall(r'id="(z_[^"!]+)"[^>]*z.type="zul.widget.Button"', page)[-1]  # "Raporu Oluştur"
    # 1991+ yillarda "Mutlak/Oransal sonuc" secimi zorunlu (secilmezse rapor yerine hata penceresi)
    mutlak = re.search(r'id="(z_[^"!]+)" z.type="zul.widget.Radio"[^>]*>(?:(?!</span>).)*?Mutlak sonuç', page, re.S)
    au("onCheck", mutlak.group(1), ["true"])

    out = hedef_klasor(year)
    out.mkdir(parents=True, exist_ok=True)
    for n, (iid, ad) in enumerate(iller, start=1):
        dosya = re.sub(r"[(),]", "", fold(ad).lower().replace(" ", "-"))  # "Ankara (1)" -> ankara-1
        dest = out / f"{n:02d}-{dosya}.html"
        if dest.exists():
            continue
        au("onSelect", il_lb, [iid, iid])
        r = au("onClick", rapor_btn, [])
        url = re.search(r"<d>(http[^<]+)</d>", r).group(1)
        dest.write_bytes(op.open(url).read())
        print(year, n, ad, flush=True)
        time.sleep(1)


def main():
    for year in sys.argv[1:]:
        for attempt in range(5):
            try:
                fetch_year(year)
                break
            except Exception as e:  # ag hatasi: yeni oturumla devam
                print("hata", year, e, flush=True)
                time.sleep(15 * (attempt + 1))


if __name__ == "__main__":
    main()
