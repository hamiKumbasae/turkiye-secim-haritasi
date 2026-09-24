"""
Wikipedia yerel secim il sayfalarindan (data/raw/wikipedia/il-sayfalari/yerel/)
TUM belediye baskanligi sonuclarini cikarir ve kaynak katmanina yazar:

  data/kaynaklar/wikipedia/yerel/<secim>.json

Birim turleri (`tur`):
  il_merkezi        il merkezi belediyesi (Buyuksehir/Anakent dahil)
  ilce              ilce belediyesi
  belde             belde belediyesi (ust = bagli oldugu ilce)
  buyuksehir_ilce   buyuksehir baskanligi oylarinin ilce kirilimi

Sonuc tipleri (`sonucTipi`):
  oy       aday/parti bazinda oy sayilari var ({{Seçim tablosu}} / belde tablosu)
  kazanan  sadece kazanan parti biliniyor (1950/1955 "İlçelere göre sonuçlar")

Hicbir sey normalize edilmez/duzeltilmez: kaynaktaki kisaltma, parti linki,
aday adi ve sayilar oldugu gibi, yaninda eslenen parti anahtari (`parti`)
ile saklanir. Birlestirme (data/normalized'a) ayri script'in isi
(merge_yerel_ilce.py).

Kullanim:
  python3 scripts/pipelines/wikipedia_arsiv/extract_yerel.py            # tum yillar
  python3 scripts/pipelines/wikipedia_arsiv/extract_yerel.py 1968yerel
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
from iller import il_adi, plaka  # noqa: E402
from partiler_wiki import parti_anahtari  # noqa: E402
from wikitext import links, parse_table, plain, sections, tables, tr_int  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "wikipedia" / "il-sayfalari" / "yerel"
OUT = ROOT / "data" / "kaynaklar" / "wikipedia" / "yerel"


def _hdr_index(grid):
    """Aday tablosunun baslik satirindan sutun indeksleri."""
    for r in grid:
        texts = [fold(c["text"]) for c in r]
        if any(t.startswith("BELDE") for t in texts):
            return None  # belde listesi, aday tablosu degil
        if any(t.startswith("OY SAYISI") or t == "OY" or t == "TOPLAM OY" for t in texts) and \
                any(t in ("PARTI", "ADAY") for t in texts):
            ix = {}
            for i, t in enumerate(texts):
                if t.startswith("KIS") and "kisaltma" not in ix:
                    ix["kisaltma"] = i + (1 if r[i].get("colspan", 1) > 1 or (i + 1 < len(r) and r[i + 1].get("span")) else 0)
                elif t == "PARTI" and "parti" not in ix:
                    ix["parti"] = i
                elif t.startswith("ADAY") and "aday" not in ix:
                    ix["aday"] = i
                elif (t.startswith("OY SAYISI") or t in ("OY", "TOPLAM OY")) and "oy" not in ix:
                    ix["oy"] = i
            return ix
    return None


_HARITARENK = re.compile(r"\{\{\s*Siyasi parti haritarenk\s*\|([^{}]*)\}\}")


def _haritarenk_satiri(m):
    """2024 sayfalari aday satirlarini sablonla yaziyor:
    {{Siyasi parti haritarenk|<parti makalesi>|<aday>|<oy>|<oran>|<kazandi 1/0>[|<gorunen ad>]}}
    -> duz tablo satiri (renk | kisaltma | parti | aday | oy | oran)."""
    a = [x.strip() for x in m.group(1).split("|")]
    parti, aday, oy, oran = (a + [""] * 4)[:4]
    ad = a[5] if len(a) > 5 and a[5] else re.sub(r"\s*\(.*?\)$", "", parti)
    return f"|-\n|\n|\n| [[{parti}|{ad}]]\n| {aday}\n| {oy}\n| {oran}"


def aday_tablosu(body, yil):
    """{{Seçim tablosu}} govdesi -> birim sozlugu (ad/tur haric)."""
    body = _HARITARENK.sub(_haritarenk_satiri, body)
    grid = parse_table(body)
    ix = _hdr_index(grid)
    out = {"sonucTipi": "oy", "secmen": None, "sandik": None, "gecerliOy": None, "gecersizOy": None,
           "adaylar": []}
    if not ix or "oy" not in ix:
        return None
    atla = set()
    for k, r in enumerate(grid):
        if k in atla:
            continue
        texts = [c["text"] for c in r]
        low = [fold(t) for t in texts]
        if any("SECMEN SAYISI" in t for t in low) and k + 1 < len(grid):
            atla.add(k + 1)
            nxt = [tr_int(c["text"]) for c in grid[k + 1] if not c.get("span")]
            nums = [n for n in nxt if n is not None]
            hdr = [t for t, c in zip(low, r) if not c.get("span")]
            for h, n in zip(hdr, nxt):
                if n is None:
                    continue
                if "SECMEN" in h:
                    out["secmen"] = n
                elif "SANDIK" in h:
                    out["sandik"] = n
            if out["secmen"] is None and nums:
                out["secmen"] = nums[0]
            continue
        first = next((t for t, c in zip(low, r) if t), "")
        if first.startswith("TOPLAM") and not first.startswith("TOPLAM SECMEN"):
            nums = [tr_int(c["text"]) for c in r if tr_int(c["text"]) is not None]
            if nums:
                out["gecerliOy"] = nums[0]
            continue
        if first.startswith("GECERSIZ"):
            nums = [tr_int(c["text"]) for c in r if tr_int(c["text"]) is not None]
            if nums:
                out["gecersizOy"] = nums[0]
            continue
        if r and all(c["header"] for c in r):
            continue
        if len(r) <= ix["oy"]:
            continue
        oy = tr_int(r[ix["oy"]]["text"])
        if oy is None:
            continue
        kis = r[ix["kisaltma"]]["text"] if "kisaltma" in ix and ix["kisaltma"] < len(r) else ""
        pcell = r[ix["parti"]] if "parti" in ix and ix["parti"] < len(r) else None
        plink = (links(pcell["raw"]) or [None])[0] if pcell else None
        pad = pcell["text"] if pcell else ""
        aday = r[ix["aday"]]["text"] if "aday" in ix and ix["aday"] < len(r) else ""
        key, how = parti_anahtari(plink, kis, yil, ad=pad)
        if key is None and fold(pad).startswith("BAGIMSIZ"):
            key, how = "Bağımsız", "parti_adi"
        out["adaylar"].append({"parti": key, "eslemeYontemi": how, "kisaltma": kis or None,
                               "partiAdi": pad or None, "partiLink": plink,
                               "aday": aday or None, "oy": oy,
                               "rowspanPaylasimli": bool(r[ix["oy"]].get("span"))})
    if not out["adaylar"]:
        return None
    return out


def kazanan_tablosu(body, yil, birim_turu, ust=None):
    """'İlçe | Parti' (1950/55) ya da 'Belde | Kazanan parti | Aday | Oy | Oran' tablolari."""
    grid = parse_table(body)
    hi = next((i for i, r in enumerate(grid[:4])
               if any(fold(c["text"]).startswith(("PARTI", "KAZANAN")) for c in r)), None)
    if hi is None:
        return []
    hdr = [fold(c["text"]) for c in grid[hi]]
    grid = grid[hi:]
    ip = next(i for i, h in enumerate(hdr) if h.startswith("PARTI") or h.startswith("KAZANAN"))
    ia = next((i for i, h in enumerate(hdr) if h.startswith("ADAY")), None)
    io = next((i for i, h in enumerate(hdr) if h.startswith("OY SAYISI") or h == "OY"), None)
    out = []
    for r in grid[1:]:
        if len(r) <= ip or r[0]["header"]:
            continue
        ad = r[0]["text"]
        if not ad:
            continue
        plink = (links(r[ip]["raw"]) or [None])[0]
        key, how = parti_anahtari(plink, None, yil, ad=r[ip]["text"])
        oy = tr_int(r[io]["text"]) if io is not None and io < len(r) else None
        b = {"tur": birim_turu, "ad": ad, "ust": ust, "sonucTipi": "kazanan",
             "kazanan": key, "kazananHam": {"partiAdi": r[ip]["text"] or None, "partiLink": plink,
                                            "eslemeYontemi": how,
                                            "aday": r[ia]["text"] if ia is not None and ia < len(r) else None,
                                            "oy": oy}}
        out.append(b)
    return out


def katilim_ve_baskan_tablolari(text, yil):
    """Parti sonucu olmayan eski (1930-1946) tablolar:
    'İlçe | Seçmen | Kullanılan oy' (1934) ve 'İlçe/Belde | Seçilen Başkan' (1946)."""
    out = []
    for _, body in tables(text):
        grid = parse_table(body)
        if not grid:
            continue
        h = [fold(c["text"]) for c in grid[0]]
        if not h or h[0] not in ("ILCE", "BELDE"):
            continue
        bt = "ilce" if h[0] == "ILCE" else "belde"
        if "SECMEN" in h and any(x.startswith("KULLANILAN") for x in h):
            i_s, i_k = h.index("SECMEN"), next(i for i, x in enumerate(h) if x.startswith("KULLANILAN"))
            for r in grid[1:]:
                if len(r) > max(i_s, i_k) and r[0]["text"] and not r[0]["header"]:
                    ad = r[0]["text"]
                    tur = "il_merkezi" if fold(ad) in ("MERKEZ", "IL MERKEZI") else bt
                    out.append({"tur": tur, "ad": ad, "ust": None, "sonucTipi": "katilim",
                                "secmen": tr_int(r[i_s]["text"]), "oyKullanan": tr_int(r[i_k]["text"])})
        elif any("BASKAN" in x for x in h):
            i_b = next(i for i, x in enumerate(h) if "BASKAN" in x)
            for r in grid[1:]:
                if len(r) > i_b and r[0]["text"] and not r[0]["header"]:
                    out.append({"tur": bt, "ad": r[0]["text"], "ust": None, "sonucTipi": "baskan",
                                "baskan": r[i_b]["text"] or None,
                                "baskanLink": (links(r[i_b]["raw"]) or [None])[0]})
    return out


_SAYI = r"(\d{1,3}(?:\.\d{3})+|\d+)"


def metin_ozeti(text, il):
    """Tablosuz sayfalarin (1930-1946) giris metninden: il geneli secmen/katilim
    (varsa erkek/kadin ayri), il merkezi belediye baskani ve metnin kendisi.
    Sadece kalibi acik cumleler okunur; yorum yapilmaz."""
    giris = re.split(r"^==", text, maxsplit=1, flags=re.M)[0]
    duz = plain(re.sub(r"\{\{Seçim bilgi kutusu.*?\n\}\}", "", giris, flags=re.S))
    kayit = {"tur": "il_ozeti", "ad": il, "ust": None, "sonucTipi": "metin", "metin": duz[:3000]}
    m = re.search(_SAYI + r" seçmen(?:in|den)\s+" + _SAYI + r"['’]", duz)
    if m:
        kayit["secmen"], kayit["oyKullanan"] = tr_int(m.group(1)), tr_int(m.group(2))
    for cins in ("erkek", "kadın"):
        m = re.search(_SAYI + rf" {cins} seçmenden(?: ise)? " + _SAYI + r"['’]", duz)
        if m:
            kayit.setdefault("cinsiyet", {})[cins] = {"secmen": tr_int(m.group(1)), "oyKullanan": tr_int(m.group(2))}
    m = re.search(r"Belediye Başkanlığına (?:yeniden |tekrar )?([A-ZÇĞİÖŞÜ][^'’,.;()]{2,60}?)['’]", duz)
    if m:
        kayit["ilMerkeziBaskani"] = m.group(1).strip()
    m = re.search(r"katılım oranı %\s*([\d,]+)", duz)
    if m:
        kayit["katilimOraniMetinde"] = float(m.group(1).replace(",", "."))
    return kayit


def kazanan_of(adaylar):
    """En cok oy alan TEK aday (bagimsizlar birlestirilmeden) - kaynak sayfalarinin kendi kurali."""
    if not adaylar:
        return None
    best = max(adaylar, key=lambda a: a["oy"])
    return best["parti"] if best["parti"] else "?"


def _bolum_turu(h2):
    f = fold(h2)
    if "BUYUKSEHIR" in f and ("ILCE" in f or "BELDE" in f):
        return "buyuksehir_ilce"
    if f.startswith("BELDELERE GORE"):
        return "belde_liste"
    if f.startswith("ILCELERE GORE") or f.startswith("ILCE VE BELDELERE"):
        return "ilce_liste"
    if "ILCE" in f:
        return "ilce"
    if f in ("KAYNAKCA", "NOTLAR", "SECIM SONRASI", "DIS BAGLANTILAR", "AYRICA BAKINIZ"):
        return None
    return "il_merkezi"


def sayfa_birimleri(text, yil, il):
    birimler = katilim_ve_baskan_tablolari(text, yil)
    if yil < 1950:
        birimler.append(metin_ozeti(text, il))
    notlar = []
    # H2 oncesi tablolar (bazi eski sayfalar) il merkezi sayilir
    first_h2 = re.search(r"^==[^=]", text, re.M)
    on = text[:first_h2.start()] if first_h2 else text
    bolumler = [("(giris)", on)] + sections(text, 2)
    for h2, govde in bolumler:
        tur = "il_merkezi" if h2 == "(giris)" else _bolum_turu(h2)
        if tur is None:
            continue
        if tur in ("ilce_liste", "belde_liste"):
            bt = "ilce" if tur == "ilce_liste" else "belde"
            for _, body in tables(govde):
                birimler += kazanan_tablosu(body, yil, bt)
            continue
        h3s = sections(govde, 3)
        if not h3s:
            h3s = [(il if tur == "il_merkezi" else h2, govde)]
        else:
            # ilk H3'ten ONCE duran tablo (orn. 2024: "== Bilecik Belediyesi ==" altinda
            # dogrudan sonuc tablosu, ardindan "=== Merkez beldeleri ===")
            m3 = re.search(r"^===[^=]", govde, re.M)
            if m3 and tables(govde[:m3.start()]):
                h3s = [(il if tur == "il_merkezi" else h2, govde[:m3.start()])] + h3s
        for h3, g3 in h3s:
            ad = plain(h3)
            if fold(ad).endswith("BELDELERI") or fold(ad) == "BELDELER":
                ust = re.sub(r"\s*beldeleri\s*$", "", ad, flags=re.I) or None
                for _, b in tables(g3):
                    birimler += kazanan_tablosu(b, yil, "belde", ust=ust)
                continue
            # ilk aday tablosu = asil sonuc; sonrakiler (ara secim vb.) sayilir ama alinmaz
            belde_govde = ""
            m4 = re.search(r"^====", g3, re.M)
            ana, belde_govde = (g3[:m4.start()], g3[m4.start():]) if m4 else (g3, "")
            tabs = [b for p, b in tables(ana)]
            sonuc, ek = None, 0
            for b in tabs:
                s = aday_tablosu(b, yil)
                if s and sonuc is None:
                    sonuc = s
                elif s:
                    ek += 1
            if sonuc:
                if tur == "il_merkezi" and any(x["tur"] == "il_merkezi" for x in birimler):
                    t = "il_merkezi_ek"  # ayni bolumde ikinci belediye (orn. Anakent + Merkez)
                else:
                    t = tur
                birimler.append(dict(tur=t, ad=ad, ust=None, kazanan=kazanan_of(sonuc["adaylar"]),
                                     ekTablo=ek, **sonuc))
            elif tur == "ilce" and tabs:
                notlar.append(f"{ad}: tablo ayristirilamadi")
            for _, b in tables(belde_govde):
                birimler += kazanan_tablosu(b, yil, "belde", ust=ad)
    return birimler, notlar


def extract(secim):
    d = RAW / secim
    idx = json.loads((d / "_index.json").read_text(encoding="utf-8"))
    yil = int(secim[:4])
    kayitlar, sayfa_notlari, istat = [], {}, collections.Counter()
    for baslik, meta in sorted(idx["sayfalar"].items()):
        il = il_adi(baslik)
        if il is None:
            continue  # ana makale / il disi sayfa
        text = (d / meta["dosya"]).read_text(encoding="utf-8")
        birimler, notlar = sayfa_birimleri(text, yil, il)
        for b in birimler:
            b.update(il=il, plaka=plaka(il), sayfa=baslik, revid=meta["revid"])
            istat[(b["tur"], b["sonucTipi"])] += 1
            kayitlar.append(b)
        if notlar:
            sayfa_notlari[baslik] = notlar
        if not birimler:
            sayfa_notlari.setdefault(baslik, []).append("hic sonuc tablosu bulunamadi")
    esle = collections.Counter(a["eslemeYontemi"] for k in kayitlar for a in k.get("adaylar", []))
    eslenemeyen = collections.Counter((a["kisaltma"], a["partiLink"]) for k in kayitlar
                                      for a in k.get("adaylar", []) if a["parti"] is None)
    out = {
        "secim": secim, "kaynak": "wikipedia", "tur": "yerel",
        "hamKlasor": str(d.relative_to(ROOT)), "kategori": idx["kategori"], "cekildi": idx["cekildi"],
        "lisans": idx["lisans"],
        "ozet": {f"{t}/{s}": n for (t, s), n in sorted(istat.items())},
        "partiEslemesi": dict(esle),
        "eslenemeyenPartiler": [{"kisaltma": k, "partiLink": l, "adet": n} for (k, l), n in eslenemeyen.most_common()],
        "sayfaNotlari": sayfa_notlari,
        "kayitlar": kayitlar,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{secim}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main():
    secimler = sys.argv[1:] or sorted(p.name for p in RAW.iterdir() if p.is_dir())
    for s in secimler:
        o = extract(s)
        print(s, o["ozet"], "eslenemeyen:", sum(x["adet"] for x in o["eslenemeyenPartiler"]),
              "sorunlu sayfa:", len(o["sayfaNotlari"]))


if __name__ == "__main__":
    main()
