"""
2009 yerel: 29 Mart'ta iptal edilip 7 Haziran 2009'da yenilenen iki ilçe belediye başkanlığı seçimi.

Ağın (Elazığ) ve Kadışehri (Yozgat) seçimleri YSK tarafından iptal edilip 7 Haziran 2009'da
yenilendi. YSK açık verisinde bu iki ilçe merkezinin 29 Mart başkanlık sonucu yok:
  - Ağın: başkanlık satırı boştu (haritada gri).
  - Kadışehri: satırda ilçe merkezi yerine Halıköy beldesinin sonucu vardı (629 geçerli oy,
    MHP 322 = belde başkanı Zeki Şimşek).
Kaynak: depodaki Vikipedi il sayfaları (data/raw/wikipedia/il-sayfalari/yerel/2009yerel/), her
iki seçimin tablosu ("29 Mart Sonuçları" / "7 Haziran Sonuçları"; sayfa kaynağı gazetevatan.com,
ntv.com.tr). Güvenilirlik D (Vikipedi), sayılar kendi içinde tutarlı (parti toplamı = toplam).

Kural (2019 İstanbul ile aynı): seçim kaydında 29 Mart sonucu (seçim günü), yenileme sonucu ayrı
dosyada (data/normalized/ek/yenileme_ara/2009yenileme_belediye_baskanligi.json). Satıra
veriNotu ile yenileme sonucu yazılır.

Kadışehri belediye meclisi: YSK açık verisinde yalnız Halıköy beldesinin meclis satırı var, ilçe
merkezininki yok; Vikipedi'de de yok. Haritada boş, notu build_meclis_harita.py düzeltmelerinde.

Idempotent. Kullanım:
  python3 scripts/pipelines/election_import/yenileme_2009.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

WIKI = ROOT / "data/raw/wikipedia/il-sayfalari/yerel/2009yerel"
OUT = ROOT / "data/normalized/ek/yenileme_ara/2009yenileme_belediye_baskanligi.json"
ILCELER = [  # (il, plaka, ilçe, geomId, wiki dosyası)
    ("Elazığ", 23, "Ağın", "TR-D-23-001", "elazigda-2009-turkiye-yerel-secimleri.wiki"),
    ("Yozgat", 66, "Kadışehri", "TR-D-66-007", "yozgatta-2009-turkiye-yerel-secimleri.wiki"),
]
KISA = {"BĞMSZ": "Bağımsız"}


def sayi(s):
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else None


def oran(s):
    m = re.search(r"%\s*([\d.,]+)", s or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def tablo(dosya, ilce):
    metin = (WIKI / dosya).read_text(encoding="utf-8")
    i = metin.index(f"==[[{ilce}]]==")
    j = metin.index("\n==", i + 5)
    blok = metin[i:j]
    hucre = lambda satir: satir.split("|")[-1].strip() if satir.startswith(("|", "!")) else None
    satirlar = blok.splitlines()
    bas = [k for k, s in enumerate(satirlar) if "Toplam seçmen sayısı" in s][0]
    # baslik satirlari ('''Toplam seçmen sayısı''', '''Toplam sandık sayısı''') ardindan iki deger satiri
    degerler = [s for s in satirlar[bas:bas + 8]
                if s.startswith('| align="center" colspan=') and "Toplam" not in s]
    secmen, sandik = sayi(hucre(degerler[0])), sayi(hucre(degerler[1]))
    adaylar = []
    for parca in blok.split('|- align="left"')[2:]:
        h = [x for x in (hucre(s) for s in parca.splitlines() if not s.startswith("|bgcolor")) if x]
        if len(h) < 6 or not re.fullmatch(r"[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü\- ]*", h[0]) or sayi(h[3]) is None:
            continue
        aday = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h[2])).strip()
        adaylar.append({"parti": KISA.get(h[0], h[0]), "aday": aday,
                        "mart": sayi(h[3]), "haziran": sayi(h[5].strip("'"))})
    toplam = [s for s in blok.split("'''Toplam'''")[1].splitlines()[1:3]]
    gecersiz = blok.split("Geçersiz ya da boş")[1].splitlines()[1:3]
    katilim = blok.split("Katılım oranı")[1].splitlines()[1:3]
    sonuc = {}
    for n, ad in enumerate(("mart", "haziran")):
        gecerli = sayi(hucre(toplam[n]))
        oy = {a["parti"]: a[ad] for a in adaylar if a[ad] is not None}
        if sum(oy.values()) != gecerli:
            raise SystemExit(f"{ilce} {ad}: aday toplamı {sum(oy.values())} != toplam {gecerli}")
        sonuc[ad] = {"gecerliOy": gecerli, "gecersizOy": sayi(hucre(gecersiz[n])),
                     "katilim": oran(hucre(katilim[n])), "oy": oy,
                     "adaylar": {a["parti"]: a["aday"] for a in adaylar}}
    return secmen, sandik, sonuc


def oy_bicimi(oy, adaylar, gecerli):
    return {p: {"oy": n, "oran": round(100 * n / gecerli, 2), "aday": adaylar.get(p)}
            for p, n in sorted(oy.items(), key=lambda x: -x[1]) if n}


def main():
    idx = json.loads((WIKI / "_index.json").read_text(encoding="utf-8"))["sayfalar"]
    url = {v["dosya"]: v["url"] for v in idx.values()}
    rec = load_election("2009yerel")
    birimler = []
    for il, plaka, ilce, geom, dosya in ILCELER:
        secmen, sandik, s = tablo(dosya, ilce)
        m, h = s["mart"], s["haziran"]
        rows = [r for r in rec["ilceler"] if r.get("geomId") == geom]
        if len(rows) != 1:
            raise SystemExit(f"{ilce}: {len(rows)} satır")
        r = rows[0]
        kazanan_h = max(h["oy"], key=h["oy"].get)
        yuzde_h = f"{100 * h['oy'][kazanan_h] / h['gecerliOy']:.2f}".replace(".", ",")
        r.update({
            "ad": ilce, "secmen": secmen, "sandik": sandik, "gecerliOy": m["gecerliOy"],
            "katilim": m["katilim"], "oy": oy_bicimi(m["oy"], m["adaylar"], m["gecerliOy"]),
            "kazanan": max(m["oy"], key=m["oy"].get),
            "kaynak": {"ana": "wikipedia", "url": url[dosya],
                       "not": "29 Mart 2009 sonucu; YSK açık verisinde yok (seçim iptal edildi). "
                              "yenileme_2009.py"},
            "veriNotu": (f"29 Mart seçimi YSK tarafından iptal edildi; 7 Haziran 2009 yenilemesinde "
                         f"{kazanan_h} %{yuzde_h} ile kazandı "
                         f"(ek/yenileme_ara/2009yenileme_belediye_baskanligi.json)."),
        })
        if m["gecersizOy"] is not None:
            r["gecersizOy"] = m["gecersizOy"]
        birimler.append({"il": il, "plaka": plaka, "ilce": ilce, "geomId": geom, "beldeId": None,
                         "belde": None, "sandik": sandik, "secmen": secmen, "gecerliOy": h["gecerliOy"],
                         "gecersizOy": h["gecersizOy"], "katilim": h["katilim"], "oy": h["oy"],
                         "adaylar": h["adaylar"], "kazanan": kazanan_h, "kaynakUrl": url[dosya]})
    save_election("2009yerel", rec)
    OUT.write_text(json.dumps({
        "secim": "2009yenileme_belediye_baskanligi", "tur": "yenileme_ara",
        "aciklama": "7 Haziran 2009 yenileme seçimi — belediye başkanlığı (29 Mart'ta iptal edilen Ağın ve Kadışehri)",
        "kaynak": {"ana": "wikipedia", "not": "Vikipedi il sayfaları (gazetevatan.com, ntv.com.tr kaynaklı); "
                   "YSK açık verisinde yok. scripts/pipelines/election_import/yenileme_2009.py"},
        "ozet": {"birim": len(birimler), "belde": 0, "il": len(birimler)},
        "birimler": birimler,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for b in birimler:
        print(b["ilce"], "29 Mart:", [r for r in rec["ilceler"] if r.get("geomId") == b["geomId"]][0]["oy"],
              "| 7 Haziran:", b["oy"], b["kazanan"])


if __name__ == "__main__":
    main()
