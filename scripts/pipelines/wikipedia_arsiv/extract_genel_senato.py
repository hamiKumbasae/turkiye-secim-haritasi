"""
Wikipedia genel secim (1923-2023), Cumhuriyet Senatosu (1961-1979) ve
cumhurbaskanligi il sayfalarindan (data/raw/wikipedia/il-sayfalari/<tur>/)
uc tur kaydi cikarip kaynak katmanina yazar:

  data/kaynaklar/wikipedia/<tur>/<secim>.json

Kayit turleri (`tur`):
  il_sonuc      ilin parti (ya da aday) bazinda sonucu: oy + varsa milletvekili/
                senator sayisi, secmen/sandik/gecerli/gecersiz
  secilen       secilen milletvekili / senator: ad + parti (+ varsa bolge)
  ilce_birinci  "İlçelerde en yüksek oyu alanlar": ilce -> birinci parti

Yorum/duzeltme yapilmaz; ham kisaltma, parti adi/linki saklanir, yaninda
eslenen parti anahtari (`parti`).

Kullanim:
  python3 scripts/pipelines/wikipedia_arsiv/extract_genel_senato.py           # hepsi
  python3 scripts/pipelines/wikipedia_arsiv/extract_genel_senato.py 1969 1961senato
"""
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE))
from common.turkish_text import fold  # noqa: E402
from extract_yerel import aday_tablosu  # noqa: E402
from iller import il_adi, plaka  # noqa: E402
from partiler_wiki import parti_anahtari  # noqa: E402
from wikitext import links, parse_table, sections, tables, tr_int  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "wikipedia" / "il-sayfalari"
OUT = ROOT / "data" / "kaynaklar" / "wikipedia"
TURLER = ["genel", "senato", "cumhurbaskanligi"]

OY_BASLIK = ("OY SAYISI", "TOPLAM", "OY", "TOPLAM OY", "ALDIGI OY", "GECERLI OY")
MV_BASLIK = ("MV", "MILLETVEKILI", "SENATOR SAYISI", "KAZANILAN", "SANDALYE")


def _bolum_haritasi(text):
    """Metin konumu -> (icinde bulundugu H2, en yakin herhangi seviyedeki baslik)."""
    heads = [(m.start(), len(m.group(1)), m.group(2).strip())
             for m in re.finditer(r"^(={2,6})\s*(.*?)\s*\1\s*$", text, re.M)]

    def h2_at(pos):
        h2, near = "(giris)", "(giris)"
        for p, lv, h in heads:
            if p <= pos:
                near = h
                if lv == 2:
                    h2 = h
        return h2, near
    return h2_at


def parti_tablosu(grid, yil):
    """'Parti | (Çevre oyu | Gümrük oyu |) Toplam | Oy oranı | MV sayısı' tablolari."""
    hi = None
    for i, r in enumerate(grid[:4]):
        h = [fold(c["text"]) for c in r]
        if any(x == "PARTI" or x.startswith("PARTI") for x in h) and any(
                x.startswith(OY_BASLIK) for x in h):
            hi = i
            break
    if hi is None:
        return None
    h = [fold(c["text"]) for c in grid[hi]]
    ip = next(i for i, x in enumerate(h) if x.startswith("PARTI"))
    # tercih: "Toplam" (gumruk dahil) > "Oy sayısı" > "Oy"
    io = next((i for i, x in enumerate(h) if x == "TOPLAM"), None)
    if io is None:
        io = next((i for i, x in enumerate(h) if x.startswith(OY_BASLIK) and "ORAN" not in x), None)
    imv = next((i for i, x in enumerate(h) if x.startswith(MV_BASLIK)), None)
    ik = ip - 1 if ip > 0 and h[ip - 1].startswith("KIS") else None
    satirlar, toplam = [], None
    for r in grid[hi + 1:]:
        if len(r) <= max(ip, io or 0):
            continue
        ad = r[ip]["text"]
        if fold(ad).startswith("TOPLAM") or fold(r[0]["text"]).startswith("TOPLAM"):
            nums = [tr_int(c["text"]) for c in r if tr_int(c["text"]) is not None]
            toplam = nums[0] if nums else None
            continue
        if fold(ad).startswith("GECERSIZ") or fold(r[0]["text"]).startswith("GECERSIZ"):
            continue
        oy = tr_int(r[io]["text"]) if io is not None else None
        if oy is None:
            continue
        plink = (links(r[ip]["raw"]) or [None])[0]
        kis = r[ik]["text"] if ik is not None else None
        key, how = parti_anahtari(plink, kis, yil, ad=ad)
        mv = tr_int(r[imv]["text"]) if imv is not None and imv < len(r) else None
        satirlar.append({"parti": key, "eslemeYontemi": how, "kisaltma": kis, "partiAdi": ad or None,
                         "partiLink": plink, "oy": oy, "sandalye": mv})
    if not satirlar:
        return None
    return {"sonucTipi": "parti", "gecerliOy": toplam, "partiler": satirlar}


def secilen_tablosu(grid, yil, bolge):
    hi = None
    for i, r in enumerate(grid[:3]):
        h = [fold(c["text"]) for c in r]
        if any(x in ("ISIM", "AD", "ADI SOYADI", "AD SOYAD", "MILLETVEKILI", "SENATOR", "SECILEN", "VEKIL")
               or x.startswith(("ISIM", "SENATOR", "MILLETVEKILI")) for x in h):
            hi = i
            break
    if hi is None:
        return []
    h = [fold(c["text"]) for c in grid[hi]]
    iad = next(i for i, x in enumerate(h) if x in ("ISIM", "AD", "ADI SOYADI", "AD SOYAD", "MILLETVEKILI", "SENATOR", "SECILEN", "VEKIL")
               or x.startswith(("ISIM", "SENATOR", "MILLETVEKILI")))
    ipar = next((i for i, x in enumerate(h) if "PARTI" in x), None)
    out = []
    for r in grid[hi + 1:]:
        if len(r) <= iad or r[iad]["header"]:
            continue
        ad = r[iad]["text"]
        if not ad or tr_int(ad) is not None:
            continue
        plink = (links(r[ipar]["raw"]) or [None])[0] if ipar is not None and ipar < len(r) else None
        pad = r[ipar]["text"] if ipar is not None and ipar < len(r) else None
        key, how = parti_anahtari(plink, None, yil, ad=pad) if (plink or pad) else (None, None)
        out.append({"tur": "secilen", "ad": ad, "parti": key, "eslemeYontemi": how,
                    "partiAdi": pad or None, "partiLink": plink,
                    "kisiLink": (links(r[iad]["raw"]) or [None])[0], "bolge": bolge})
    return out


def ilce_birinci_tablosu(grid, yil):
    if not grid:
        return []
    h = [fold(c["text"]) for c in grid[0]]
    if not (h and h[0].startswith("ILCE") and any("PARTI" in x or "KAZANAN" in x for x in h)):
        return []
    ip = next(i for i, x in enumerate(h) if "PARTI" in x or "KAZANAN" in x)
    out = []
    for r in grid[1:]:
        if len(r) <= ip or r[0]["header"] or not r[0]["text"]:
            continue
        plink = (links(r[ip]["raw"]) or [None])[0]
        key, how = parti_anahtari(plink, None, yil, ad=r[ip]["text"])
        out.append({"tur": "ilce_birinci", "ad": r[0]["text"], "parti": key, "eslemeYontemi": how,
                    "partiAdi": r[ip]["text"] or None, "partiLink": plink})
    return out


def sayfa_kayitlari(text, yil):
    h2_at = _bolum_haritasi(text)
    kayitlar, il_sonuc_var = [], False
    for pos, body in tables(text):
        h2, yakin = h2_at(pos)
        fh = fold(h2)
        fy = fold(yakin)
        secilen_bolumu = any("SECIL" in x or x.startswith(("MILLETVEKILLERI", "SENATOR", "VEKIL"))
                             for x in (fh, fy))
        grid = parse_table(body)
        if not grid:
            continue
        birinci = ilce_birinci_tablosu(grid, yil)
        if birinci:
            kayitlar += birinci
            continue
        if secilen_bolumu or ("BOLGE" in fy and "SECIL" in fh):
            s = secilen_tablosu(grid, yil, yakin if "BOLGE" in fold(yakin) else None)
            if s:
                kayitlar += s
                continue
        p = parti_tablosu(grid, yil)
        if p:
            kayitlar.append(dict(tur="il_sonuc", bolum=yakin, **p))
            il_sonuc_var = True
            continue
        a = aday_tablosu(body, yil)
        if a:
            kayitlar.append(dict(tur="il_sonuc", bolum=yakin, **a))
            il_sonuc_var = True
            continue
        # 1923-1946 sayfalarinda "Seçilenler" disinda tablo yok; baslikli bolum
        # disindaki isim tablolari (aday listeleri vb.) secilen SAYILMAZ.
    return kayitlar, il_sonuc_var


def extract(tur, secim):
    d = RAW / tur / secim
    idx = json.loads((d / "_index.json").read_text(encoding="utf-8"))
    yil = int(secim[:4])
    kayitlar, notlar, istat = [], {}, collections.Counter()
    for baslik, meta in sorted(idx["sayfalar"].items()):
        il = il_adi(baslik)
        if il is None:
            continue
        text = (d / meta["dosya"]).read_text(encoding="utf-8")
        ks, var = sayfa_kayitlari(text, yil)
        for k in ks:
            k.update(il=il, plaka=plaka(il), sayfa=baslik, revid=meta["revid"])
            istat[k["tur"]] += 1
        kayitlar += ks
        if not ks:
            notlar[baslik] = ["hic tablo ayristirilamadi"]
        elif not var:
            notlar[baslik] = ["il sonucu tablosu yok/ayristirilamadi"]
    eslenemeyen = collections.Counter()
    for k in kayitlar:
        for p in k.get("partiler", []) + k.get("adaylar", []) + ([k] if k["tur"] != "il_sonuc" else []):
            if p.get("parti") is None and (p.get("partiAdi") or p.get("kisaltma")):
                eslenemeyen[(p.get("kisaltma"), p.get("partiAdi"), p.get("partiLink"))] += 1
    out = {
        "secim": secim, "kaynak": "wikipedia", "tur": tur, "hamKlasor": str(d.relative_to(ROOT)),
        "kategori": idx["kategori"], "cekildi": idx["cekildi"], "lisans": idx["lisans"],
        "ozet": dict(istat),
        "eslenemeyenPartiler": [{"kisaltma": a, "partiAdi": b, "partiLink": c, "adet": n}
                                for (a, b, c), n in eslenemeyen.most_common()],
        "sayfaNotlari": notlar, "kayitlar": kayitlar,
    }
    (OUT / tur).mkdir(parents=True, exist_ok=True)
    (OUT / tur / f"{secim}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main():
    secili = set(sys.argv[1:])
    for tur in TURLER:
        for d in sorted((RAW / tur).iterdir()):
            if d.is_dir() and (not secili or d.name in secili):
                o = extract(tur, d.name)
                print(f"{tur}/{d.name}", o["ozet"], "eslenemeyen:", sum(x["adet"] for x in o["eslenemeyenPartiler"]),
                      "notlu sayfa:", len(o["sayfaNotlari"]))


if __name__ == "__main__":
    main()
