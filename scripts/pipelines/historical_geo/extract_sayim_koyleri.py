"""
DIE genel nufus sayimi 'Idari Bolunus' kitaplari (1985, 1990) -> koy/belde -> ilce/bucak dizini.

Kitaplarin 3 numarali il tablosu ("Ilce, bucak ve koy muhtarliklari itibariyle nufus sayisi")
iki sutunlu basilmis: "NN <AD> İLÇESİ" -> "N <AD> BUCAĞI" -> "NNN <KÖY> [(B)|(BM)] <nüfus>".
Sutunlar okuma sirasiyla (sol, sag, sonraki sayfa sol ...) islenir; ilce/bucak durumu sayfa
ve sutun gecislerinde tasinir. Sehir (il/ilce merkezi belediyesi) icindeki mahalleler
kitapta yoktur.

Kitaplar depoda tutulmaz (~115 MB): TUIK kutuphanesinden indirilip SHA-256 ile dogrulanir,
.cache/tuik-nufus-sayimi/ altinda (gitignore) onbelleklenir.

Cikti: data/kaynaklar/tuik/nufus_sayimi/<yil>_koyler.json
  {"kaynak": ..., "satirlar": [{plaka, il, ilce, bucak, ad, tip: koy|belde|bucak_merkezi, nufus, sayfa}]}

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_sayim_koyleri.py 1985 1990
"""
import hashlib
import json
import pathlib
import re
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from common.turkish_text import fold  # noqa: E402

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
TAM = ROOT / ".cache/tuik-nufus-sayimi"
OUT = ROOT / "data/kaynaklar/tuik/nufus_sayimi"
KITAPLAR = {
    "1960": {"no": "0015128", "sha256": "3e38c8d66e0bbfc7f07924a26c23b41b9ca1c17349428ef508ebd78c65060362",
             "baslik": "23 Ekim 1960 Genel Nüfus Sayımı — İl, İlçe, Bucak ve Köyler", "tarih": "1960-10-23",
             "bicim": "1960"},
    "1985": {"no": "0013062", "sha256": "feb485f5f062cb24636f27f1791369bbce7dc252383a3bf4d28c059e67101ca7",
             "baslik": "Genel Nüfus Sayımı İdari Bölünüş, 20.10.1985", "tarih": "1985-10-20"},
    "1990": {"no": "0013349", "sha256": "f4003db9584ddf4faa26519c8cc88139e54d4f4b9ef2c9f1eed50fcab99eab85",
             "baslik": "Genel Nüfus Sayımı İdari Bölünüş, 21.10.1990", "tarih": "1990-10-21"},
}
TABLO3 = re.compile(r"BUCAK VE K[ÖO]Y MUHTARLIK|SUB.?DISTRICT AND VI[LI]+AGES", re.I)
ILCE = re.compile(r"^(\d{2})\s+(.+?)\s+İLÇESİ$")
BUCAK = re.compile(r"^(\d)\s+(.+?)\s+BUCA\S{1,3}\s*\*?$")
# satir numarasi OCR'da ayri satira dusebiliyor ('KÜNERLİK 1197' / '013'): numara istege bagli
KOY = re.compile(r"^(\d{3})?\s*([A-ZÇĞİÖŞÜÂÎÛ][A-ZÇĞİÖŞÜÂÎÛa-zçğıöşü0-9.'’\- ]*?)\s*((?:\((?:B|BM|8|3|8M|S)[,)]?\s*\)?\s*)*)(\d{1,3}(?: ?\d{3})?|\d+)$")
YASAK = re.compile(r"^(ŞEHİR|SEHİR|ŞEHIR|TOPLAM|İLÇE|İDARİ|ADMINISTRATIVE|POPULATION|NÜFUS|PROVINCE|İLİ|GENEL)")


def kitap(yil):
    k = KITAPLAR[yil]
    p = TAM / f"{k['no']}.pdf"
    if not p.exists():
        TAM.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(f"https://kutuphane.tuik.gov.tr/pdf/{k['no']}.pdf",
                                     headers={"User-Agent": "Mozilla/5.0"})
        p.write_bytes(urllib.request.urlopen(req, timeout=600).read())
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != k["sha256"]:
        raise SystemExit(f"{p}: SHA-256 uyusmuyor ({h})")
    return p


def sutun_satirlari(pg):
    ws = pg.extract_words()
    mid = pg.width / 2
    for sol in (True, False):
        satir = {}
        for w in ws:
            if (w["x0"] < mid) == sol:
                satir.setdefault(round(w["top"] / 3), []).append(w)
        for k in sorted(satir):
            yield " ".join(x["text"] for x in sorted(satir[k], key=lambda w: w["x0"]))


IL_ADI = {f["properties"]["plaka"]: f["properties"].get("ad") or f["properties"].get("name")
          for f in json.loads((ROOT / "geo/normalized/turkiye_il_sinirlari.geojson").read_text(encoding="utf-8"))["features"]}


def il_basligi(metin):
    """sayfa basligindaki il plakasi (OCR: 'İLİ : 34 İSTANBUL', 'ALt\\n: 35', 'I 34 İSTANBUL')"""
    m = re.search(r"(?:^|\n)\s*[:;I|]?\s*[:;]?\s*(\d{2})(?:\s|$)", metin[:160])
    if m and 1 <= int(m.group(1)) <= 81:
        return int(m.group(1)), IL_ADI.get(int(m.group(1)))
    return None


def tekle(w):
    """kalin puntoda cift yazilmis sozcuk: 'MMeerrkkeezz' -> 'Merkez', 'İİLLÇÇEESSİİ' -> 'İLÇESİ'"""
    return w[0::2] if len(w) >= 4 and len(w) % 2 == 0 and fold(w[0::2]) == fold(w[1::2]) else w


ETIKET = re.compile(r"^\(?(B|BM|8|3|8M|S|SM)[,)]*$")
YASAK_BAS = {"SEHIR", "TOPLAM", "ILCE", "ILCELER", "IDARI", "ADMINISTRATIVE", "POPULATION", "NUFUS", "PROVINCE",
             "ILI", "GENEL", "BUCAK", "KOY", "SEHIRLER"}


def ilce_toplami(tok, ft):
    """'NN <AD> İLÇESİ TOPLAMI [nüfus]' -> ad (ilce bolumunun kapanisi)"""
    if "TOPLAMI" in ft or any(t.startswith("TOPLAM") for t in ft):
        i = next(k for k, t in enumerate(ft) if t.startswith("TOPLAM"))
        if i >= 2 and ft[i - 1].startswith("ILCES"):
            bas = 1 if re.fullmatch(r"\d{1,2}\.?", tok[0]) else 0
            if i - 1 > bas:
                return " ".join(tok[bas:i - 1])
    return None


def satir_coz(ln):
    """(tur, ad, etiketler) - tur: ilce | ilce_toplami | bucak | koy | None. Yapi ASCII'ye
    katlanmis sozcuklerde aranir (OCR 'ILÇESI', 'BUCAĞı' karisik), ad asil metinden alinir."""
    tok = [tekle(t) for t in ln.split()]
    ft = [fold(t).upper() for t in tok]
    if not tok:
        return None, None, None
    it = ilce_toplami(tok, ft)
    if it:
        return "ilce_toplami", it, None
    if any("TOPLAM" in t for t in ft):
        return None, None, None
    if len(tok) >= 3 and re.fullmatch(r"\d{2}", tok[0]) and re.match(r"^ILCES", ft[-1]):
        return "ilce", " ".join(tok[1:-1]), None
    if len(tok) >= 2 and ft[-1].startswith("BUCA"):
        bas = 1 if re.fullmatch(r"[0-9O]", tok[0]) else 0
        return "bucak", " ".join(tok[bas:-1]), None
    kod = bool(re.fullmatch(r"\d{3}", tok[0]))
    nuf = bool(re.fullmatch(r"\d[\d.]*", tok[-1]))
    govde = tok[int(kod):len(tok) - int(nuf)]
    etiket = [t for t in govde if ETIKET.match(t)]
    ad = [t for t in govde if not ETIKET.match(t)]
    if not (kod or nuf) or not ad or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2}", " ".join(ad)):
        return None, None, None
    if fold(ad[0]).upper() in YASAK_BAS or len(" ".join(ad)) < 3:
        return None, None, None
    tip = "bucak_merkezi" if (kod and tok[0] == "000") or any(re.search(r"M", e) for e in etiket) else \
          "belde" if etiket else "koy"
    return "koy", " ".join(ad), tip


def isle(satirlar, tampon, il, ilce, bucak, tur, ad, tip, sayfa_no):
    """ilce basligi gecici etikettir; 'X İLÇESİ TOPLAMI' satiri bolumu kapatir ve o bolumde
    okunan koyleri X'e atar (baslik OCR'da dusmus ya da bolunmus olsa bile)."""
    if tur == "ilce":
        return ad, None, tampon
    if tur == "ilce_toplami":
        for r in tampon:
            r["ilce"], r["ilceKaynagi"] = ad, "toplam"
        satirlar.extend(tampon)
        return None, None, []
    if tur == "bucak":
        return ilce, ad, tampon
    if tur == "koy" and il:
        tampon.append({"plaka": il[0], "il": il[1], "ilce": ilce, "bucak": bucak, "ad": ad, "tip": tip,
                       "sayfa": sayfa_no, "ilceKaynagi": "baslik"})
    return ilce, bucak, tampon


def ayikla(yil):
    satirlar, il, ilce, bucak, sayfa_no, tampon = [], None, None, None, 0, []
    with pdfplumber.open(kitap(yil)) as pdf:
        for sayfa_no, pg in enumerate(pdf.pages, 1):
            metin = pg.extract_text() or ""
            if not TABLO3.search(fold(metin[:700]).upper().replace("I", "I")) and not TABLO3.search(metin[:700]):
                continue
            ib = il_basligi(metin)
            if ib and (il is None or ib[0] != il[0]):
                satirlar.extend(r for r in tampon if r["ilce"])   # kapanmamis bolum: baslik etiketiyle
                il, ilce, bucak, tampon = ib, None, None, []
            for ln in sutun_satirlari(pg):
                tur, ad, tip = satir_coz(ln.strip())
                ilce, bucak, tampon = isle(satirlar, tampon, il, ilce, bucak, tur, ad, tip, sayfa_no)
    return satirlar


IL_AD_PLAKA = None


def il_ad_plaka():
    """1960 kitabinda plaka yok; il adi (harfleri aralikli basilmis) -> plaka"""
    global IL_AD_PLAKA
    if IL_AD_PLAKA is None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from common.election_io import load_election
        IL_AD_PLAKA = {fold(r["ad"]).upper().replace(" ", ""): r["plaka"] for r in load_election("2023")["iller"]}
        IL_AD_PLAKA.update({"ICEL": 33, "MARAS": 46, "URFA": 63, "ANTEP": 27, "COLEMERIK": 30})
    return IL_AD_PLAKA


def sutun_satirlari_1960(pg):
    ws = pg.extract_words()
    num = [w["x0"] for w in ws if re.fullmatch(r"\d{1,3}\.", w["text"]) and w["x0"] > pg.width * 0.35]
    sinir = min(num) - 3 if num else pg.width / 2
    for sol in (True, False):
        satir = {}
        for w in ws:
            if (w["x0"] < sinir) == sol:
                satir.setdefault(round(w["top"] / 3), []).append(w)
        for k in sorted(satir):
            yield " ".join(tekle(x["text"]) for x in sorted(satir[k], key=lambda w: w["x0"]))


def satir_coz_1960(ln):
    tok = ln.split()
    ft = [fold(t).upper() for t in tok]
    if not tok:
        return None, None, None
    it = ilce_toplami(tok, ft)
    if it:
        return "ilce_toplami", it, None
    if any("TOPLAM" in t for t in ft):
        return None, None, None
    if "ILCESI" in ft:
        i = ft.index("ILCESI")
        bas = 1 if re.fullmatch(r"\d{1,2}\.", tok[0]) else 0
        if i > bas:
            return "ilce", " ".join(tok[bas:i]), None
    if len(tok) >= 2 and ft[-1].startswith("BUCA") and not re.search(r"\d", ln):
        return "bucak", " ".join(tok[:-1]), None
    if re.fullmatch(r"\d{1,3}\.", tok[0]) and len(tok) >= 2:
        ad = []
        for t in tok[1:]:
            if re.fullmatch(r"[\d.]+|X|B\.|M\.|\(B\.\)|—|-", t):
                break
            ad.append(t)
        if not ad or not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2}", " ".join(ad)):
            return None, None, None
        tip = "bucak_merkezi" if "B. M." in ln or "B.M." in ln else "belde" if "(B.)" in ln else "koy"
        return "koy", " ".join(ad), tip
    return None, None, None


def ayikla_1960():
    satirlar, il, ilce, bucak, tampon = [], None, None, None, []
    with pdfplumber.open(kitap("1960")) as pdf:
        for sayfa_no, pg in enumerate(pdf.pages, 1):
            metin = pg.extract_text() or ""
            if "Muhtarl" not in metin[:400] or "Bucak" not in metin[:400]:
                continue
            # 'İli : 293\nİ S T A N B UL' -> il adi (harfleri birlestir)
            bas = [x for x in metin.split("\n")[:4] if re.fullmatch(r"[A-ZÇĞİÖŞÜ ]{3,}", x.strip())]
            if bas:
                pl = il_ad_plaka().get(fold(bas[0]).upper().replace(" ", ""))
                if pl and (il is None or il[0] != pl):
                    satirlar.extend(r for r in tampon if r["ilce"])
                    il, ilce, bucak, tampon = (pl, bas[0].replace(" ", "")), None, None, []
            for ln in sutun_satirlari_1960(pg):
                tur, ad, tip = satir_coz_1960(ln.strip())
                ilce, bucak, tampon = isle(satirlar, tampon, il, ilce, bucak, tur, ad, tip, sayfa_no)
    return satirlar


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for yil in sys.argv[1:] or KITAPLAR:
        k = KITAPLAR[yil]
        rows = ayikla_1960() if k.get("bicim") == "1960" else ayikla(yil)
        (OUT / f"{yil}_koyler.json").write_text(json.dumps({
            "kaynak": {"yayin": k["baslik"], "url": f"https://kutuphane.tuik.gov.tr/pdf/{k['no']}.pdf",
                       "sha256": k["sha256"], "tarih": k["tarih"],
                       "not": "OCR metin katmanından; köy adlarında OCR hataları olabilir (ör. 'Ş'→'S', 'ğ'→'5'). "
                              "Şehir içi mahalleler kitapta yok."},
            "satirlar": rows}, ensure_ascii=False, indent=0), encoding="utf-8")
        iller = sorted({r["plaka"] for r in rows})
        print(yil, len(rows), "satır,", len(iller), "il")


if __name__ == "__main__":
    main()
