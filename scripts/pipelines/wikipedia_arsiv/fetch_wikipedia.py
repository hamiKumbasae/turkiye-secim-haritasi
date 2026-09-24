"""
Turkce Wikipedia'nin "Illere gore <yil> Turkiye <tur> secimleri" kategorilerindeki
TUM il alt makalelerini (ve her secimin ana makalesini) ham wikitext olarak
data/raw/wikipedia/il-sayfalari/<tur>/<secim>/ altina arsivler.

Her secim klasoru:
  _index.json      baslik -> {dosya, pageid, revid, timestamp, url}
  <slug>.wiki      sayfanin o revizyondaki ham wikitext'i (degistirilmeden)
  _ana_makale.wiki secimin ulusal ana makalesi (varsa)

Wikipedia degisebilen bir kaynak oldugu icin bu klasor bir ANLIK GORUNTUDUR;
revid ile her sayfa tam olarak yeniden bulunabilir
(https://tr.wikipedia.org/w/index.php?oldid=<revid>). Mevcut klasorler
atlanir; --yenile ile yeniden cekilir.

Kullanim:
  python3 scripts/pipelines/wikipedia_arsiv/fetch_wikipedia.py            # hepsi
  python3 scripts/pipelines/wikipedia_arsiv/fetch_wikipedia.py 1968yerel  # tek secim
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from common.turkish_text import fold  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
OUT = ROOT / "data" / "raw" / "wikipedia" / "il-sayfalari"
API = "https://tr.wikipedia.org/w/api.php"
UA = "secim-haritasi-arsiv/1.0 (https://github.com; veri arsivi)"
KAT = re.compile(r"^İllere göre (?:(Haziran|Kasım) )?(\d{4}) Türkiye (genel|yerel|senato|cumhurbaşkanlığı) seçim(?:leri|i)$")
TUR = {"genel": "genel", "yerel": "yerel", "senato": "senato", "cumhurbaşkanlığı": "cumhurbaskanligi"}


def api(**p):
    p.update(format="json", formatversion=2, maxlag=5)
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(p), headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=90))
            if d.get("error", {}).get("code") == "maxlag":
                raise RuntimeError("maxlag")
            return d
        except Exception as e:  # ag hatasi / maxlag: bekle, tekrar dene
            print("  tekrar", attempt, e, flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("API cevap vermedi")


def secim_anahtari(ay, yil, tur):
    """Projenin data/normalized anahtar kaliplariyla ayni: 1968yerel, 2015Haziran, 2014cb, 1961senato."""
    if tur == "genel":
        return yil + {"Haziran": "Haziran", "Kasım": "Kasim", None: ""}[ay]
    return yil + {"yerel": "yerel", "senato": "senato", "cumhurbaskanligi": "cb"}[tur]


def kategoriler():
    out, cont = [], {}
    while True:
        d = api(action="query", list="allcategories", acprefix="İllere göre", aclimit=500, **cont)
        for c in d["query"]["allcategories"]:
            m = KAT.match(c["category"])
            if m:
                ay, yil, tur = m.groups()
                tur = TUR[tur]
                out.append((c["category"], tur, secim_anahtari(ay, yil, tur), (ay + " " if ay else "") + yil))
        if "continue" not in d:
            return out
        cont = d["continue"]


def uyeler(kategori):
    out, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle="Kategori:" + kategori,
                cmnamespace=0, cmlimit=500, **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" not in d:
            return out
        cont = d["continue"]


def icerikler(basliklar):
    """50'lik gruplar halinde son revizyonun wikitext'i (yonlendirmeler izlenir)."""
    out = {}
    for i in range(0, len(basliklar), 50):
        d = api(action="query", prop="revisions", rvprop="content|ids|timestamp", rvslots="main",
                redirects=1, titles="|".join(basliklar[i:i + 50]))
        for p in d["query"]["pages"]:
            if p.get("missing") or not p.get("revisions"):
                continue
            r = p["revisions"][0]
            out[p["title"]] = {"pageid": p["pageid"], "revid": r["revid"], "timestamp": r["timestamp"],
                               "wikitext": r["slots"]["main"]["content"]}
        time.sleep(1)
    return out


def slug(baslik):
    return re.sub(r"[^a-z0-9]+", "-", fold(baslik).lower()).strip("-")[:120]


def arsivle(kategori, tur, anahtar, etiket, yenile=False):
    hedef = OUT / tur / anahtar
    if (hedef / "_index.json").exists() and not yenile:
        print("atlandi", anahtar, flush=True)
        return
    hedef.mkdir(parents=True, exist_ok=True)
    basliklar = uyeler(kategori)
    ana = f"{etiket} Türkiye {'cumhurbaşkanlığı seçimi' if tur == 'cumhurbaskanligi' else tur + ' seçimleri'}"
    sayfalar = icerikler(basliklar + [ana])
    index = {"kategori": "Kategori:" + kategori, "cekildi": time.strftime("%Y-%m-%d"),
             "kaynak": "tr.wikipedia.org MediaWiki API (action=query&prop=revisions, ham wikitext)",
             "lisans": "CC BY-SA 4.0 (Wikipedia katkicilari)", "sayfalar": {}}
    for baslik, s in sorted(sayfalar.items()):
        dosya = "_ana_makale.wiki" if baslik == ana else slug(baslik) + ".wiki"
        (hedef / dosya).write_text(s["wikitext"], encoding="utf-8")
        index["sayfalar"][baslik] = {
            "dosya": dosya, "pageid": s["pageid"], "revid": s["revid"], "timestamp": s["timestamp"],
            "url": "https://tr.wikipedia.org/w/index.php?oldid=%d" % s["revid"]}
    (hedef / "_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(anahtar, len(basliklar), "uye,", len(sayfalar), "sayfa yazildi", flush=True)


def main():
    secili = [a for a in sys.argv[1:] if not a.startswith("--")]
    for kategori, tur, anahtar, etiket in kategoriler():
        if secili and anahtar not in secili:
            continue
        arsivle(kategori, tur, anahtar, etiket, "--yenile" in sys.argv)


if __name__ == "__main__":
    main()
