"""
TUIK secimdagitimapp "Secim cevresi ve ilcelere gore milletvekili genel
secimi sonuclari" raporlarinin (data/raw/tuik/secimdagitimapp-ilce-*/) TAMAMINI
kaynak katmanina cikarir:

  data/kaynaklar/tuik/genel/<secim>.json

Iki rapor bicimi var, ikisi de okunur:
  1961-1987: il satiri + ilce satirlari (+ her sayi satirinin altinda yuzde satiri)
  1991-2023: il satiri + il duzeyinde "İl/İlçe merkezi" / "Belde/Köy" kirilimi,
             sonra her ilce icin ilce satiri + "Şehir toplamı" /
             "Bucak ve köyler toplamı" alt satirlari

Hicbir sayi degistirilmez; TUIK'in sutun basliklari (`sutunlar`) ve parti
sutunlarinin eslendigi partiler.json anahtarlari (`partiEslemesi`) ayrica
saklanir. Bir il birden fazla secim cevresine bolunmusse (Ankara (1),
Ankara (2) ...) her cevre ayri kayittir.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/extract_tuik_ilce.py              # tum yillar
  python3 scripts/pipelines/tuik_arsiv/extract_tuik_ilce.py 2007 1999
"""
import collections
import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "tuik"
OUT = ROOT / "data" / "kaynaklar" / "tuik" / "genel"
KLASORLER = ["secimdagitimapp-ilce-1961-1987", "secimdagitimapp-ilce-1991-2023"]
TABLO = "Seçim çevresi ve ilçelere göre milletvekili genel seçimi sonuçları"

_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_HARF = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]")

META = {"SANDIK SAYISI": "sandik", "KAYITLI SECMEN SAYISI": "secmen",
        "OY KULLANAN SECMEN SAYISI": "oyKullanan", "GECERLI OY SAYISI": "gecerliOy"}
ALT = {"IL/ILCE MERKEZI": "sehir", "BELDE/KOY": "koy", "SEHIR TOPLAMI": "sehir",
       "BUCAK VE KOYLER TOPLAMI": "koy"}

# TUIK sutun basligi -> partiler.json anahtari (yil araligina gore)
PARTI = {
    "AP": "AP", "CHP": "CHP", "CKMP": "CKMP", "YTP": "YTP61", "MİLLET PARTİSİ": "MP62",
    "TİP": "TİP", "GP": "GP", "CGP": "CGP", "MHP": "MHP", "BİRLİK PARTİSİ": "TBP73", "TBP": "TBP73",
    "DEMOKRATİK PARTİ": "DEMP73", "MSP": "MSP", "ANAP": "ANAP", "HP": "HP", "MDP": "MDP",
    "RP": "RP", "DYP": "DYP", "DSP": "DSP", "SHP": "SHP", "IDP": "IDP", "MÇP": "MÇP",
    "BĞMZ": "Bağımsız", "BAĞIMSIZ": "Bağımsız",
    "HADEP": "HADEP", "YDH": "YDH", "YDP": "YDP", "YENİ PARTİ": "YENP95", "İP": "İP",
    "BBP": "BBP", "BP": "BP", "DBP": "DBP99", "DEPAR": "DEPAR", "DP": "DP", "DTP": "DEMTP",
    "EMEP": "EMEP", "FP": "FP", "LDP": "LDP", "SİP": "SİP", "ÖDP": "ÖDP",
    "AK PARTİ": "AK Parti", "BTP": "BTP", "DEHAP": "DEHAP", "GENÇ PARTİ": "GP",
    "SAADET PARTİSİ": "SP", "SAADET": "SP", "TKP": "TKP", "YURT-P": "YURT-P", "ATP": "ATP",
    "HYP": "HYP", "HAS PARTİ": "HAS", "HEPAR": "HEPAR", "MMP": "MMP", "DSP ": "DSP",
    "HDP": "HDP", "BDP": "BDP", "İYİ PARTİ": "İYİ Parti", "İYİ": "İYİ Parti", "HÜDA PAR": "HÜDAPAR",
    "VATAN PARTİSİ": "VATAN", "VATAN": "VATAN", "YENİDEN REFAH": "YENİDEN REFAH",
    "YEŞİL SOL PARTİ": "YEŞİL SOL", "ZAFER PARTİSİ": "ZP", "MEMLEKET": "MEMLEKET", "SOL PARTİ": "SOL PARTİ",
    "TÜRKİYE İŞÇİ PARTİSİ": "TİP", "ADALET PARTİSİ": "AP23", "ANAVATAN": "ANAP",
    "DEMOKRAT PARTİ": "DP", "BAĞIMSIZ TÜRKİYE PARTİSİ": "BTP", "HAK-PAR": "HAK-PAR",
    "DEVA": "DEVA", "GELECEK PARTİSİ": "Gelecek Partisi", "TKH": "TKH", "MİLLİ YOL": "MİLLİYOL",
    "HKP": "HKP", "EMEP ": "EMEP", "DEM PARTİ": "DEM Parti", "TKP ": "TKP", "YRP": "YENİDEN REFAH",
}
PARTI_DONEM = [  # (baslik, ilk_yil, son_yil, anahtar)
    ("SP", 1991, 1991, "SosP"), ("SP", 2002, 9999, "SP"),
    ("MİLLET PARTİSİ", 1992, 9999, "MP92"), ("YTP", 2002, 9999, "YTP02"),
    ("DTP", 2007, 2008, "DTP"), ("BP", 2018, 9999, "BP"), ("YURT-P", 2002, 2002, "YP"),
]

TUIK_IL = {"AFYON": 3, "ICEL": 33, "MERSIN": 33, "K,MARAS": 46, "KMARAS": 46, "K.MARAS": 46,
           "KAHRAMANMARAS": 46, "HAKKARI": 30, "SANLIURFA": 63, "URFA": 63}
_MODERN = {fold(v["il_ADI"]): int(k) for k, v in json.loads(
    (ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text(encoding="utf-8")).items()}


def il_plaka(ad):
    a = re.sub(r"\s*\(\d+\)\s*$", "", ad)
    f = fold(a).replace(",", "").replace(" ", "")
    return TUIK_IL.get(fold(a)) or TUIK_IL.get(f) or _MODERN.get(fold(a))


def parti_anahtari(baslik, yil):
    b = " ".join(baslik.split()).upper()
    for h, y0, y1, k in PARTI_DONEM:
        if b == h and y0 <= yil <= y1:
            return k
    return PARTI.get(b)


def _clean(s):
    return " ".join(re.sub(r"<[^>]+>", " ", html.unescape(s)).split())


def _int(v):
    v = v.replace(".", "").replace(" ", "")
    if v in ("-", ""):
        return 0 if v == "-" else None
    return int(v) if v.isdigit() else None


def parse(raw):
    t = raw.decode("cp1254", "ignore")
    grid = [[_clean(c) for c in _CELL.findall(r)] for r in _ROW.findall(t)]
    header, dipnot, rows = [], [], []
    started = False
    for cells in grid:
        ne = [c for c in cells if c != ""]
        if not ne:
            continue
        is_data = _HARF.search(ne[0]) and len(ne) > 2 and all(
            _int(x) is not None or re.fullmatch(r"\(\d+\)", x) for x in ne[1:])
        if not started:
            if is_data and header:
                started = True
            else:
                for c in ne:
                    if re.search(r"Seçim çevresi ve ilçe|aldığı oy sayısı|Sonuçları$|^\(\d+\)", c):
                        continue
                    if _HARF.search(c):
                        header.append(" ".join(c.split()))
                continue
        if not _HARF.search(ne[0]):
            continue  # yuzde satiri
        if not is_data:
            if len(ne) == 1 and len(ne[0]) > 25:
                dipnot.append(ne[0])
            continue
        vals = [x for x in ne[1:] if not re.fullmatch(r"\(\d+\)", x)]
        girinti = cells.index(ne[0])
        rows.append((ne[0], girinti, [_int(x) for x in vals]))
    # Sutun basliklari raporda birden fazla satira dagilabiliyor (1999'da
    # "Sandık sayısı" parti basliklarindan SONRAKI satirda) - veri satirlarinda
    # ise sira hep: sandik, kayitli, oy kullanan, gecerli, partiler.
    sabit = sorted((h for h in header if fold(h) in META), key=lambda h: list(META).index(fold(h)))
    header = sabit + [h for h in header if fold(h) not in META]
    return header, rows, dipnot


def _kayit(header, vals, yil):
    meta, partiler = {}, {}
    for h, v in zip(header, vals):
        f = fold(h)
        if f in META:
            meta[META[f]] = v
        else:
            partiler[h] = v
    return meta, partiler


def extract(secim_klasor, yil_etiketi):
    yil = int(yil_etiketi[:4])
    cevreler, eslenemeyen, sutun_seti = [], collections.Counter(), {}
    for f in sorted(secim_klasor.glob("*.html")):
        header, rows, dipnot = parse(f.read_bytes())
        if not rows:
            cevreler.append({"dosya": f.name, "hata": "veri satiri bulunamadi"})
            continue
        for h in header:
            if fold(h) not in META:
                k = parti_anahtari(h, yil)
                sutun_seti[h] = k
                if k is None:
                    eslenemeyen[h] += 1
        turkiye = None
        if fold(rows[0][0]) == "TURKIYE":  # 1961-1987 raporlari ulke toplamiyla baslar
            m, p = _kayit(header, rows[0][2], yil)
            turkiye = {**m, "partiler": p}
            rows = rows[1:]
        ad0, g0, v0 = rows[0]
        meta, part = _kayit(header, v0, yil)
        cevre = {"dosya": f.name, "cevre": ad0, "plaka": il_plaka(ad0), **meta, "partiler": part,
                 "ilceler": []}
        if dipnot:
            cevre["dipnotlar"] = dipnot
        if turkiye:
            cevre["turkiyeToplami"] = turkiye
        son = None
        for ad, g, v in rows[1:]:
            m, p = _kayit(header, v, yil)
            alt = ALT.get(fold(ad))
            if alt and son is None:
                cevre.setdefault("kirilim", {})[alt] = {**m, "partiler": p}
            elif alt:
                son.setdefault("kirilim", {})[alt] = {**m, "partiler": p}
            else:
                son = {"ad": ad, **m, "partiler": p}
                cevre["ilceler"].append(son)
        cevreler.append(cevre)
    return {
        "secim": secim_klasor.name, "kaynak": "tuik", "tur": "genel", "tablo": TABLO,
        "uygulama": "https://biruni.tuik.gov.tr/secimdagitimapp/secim.zul",
        "hamKlasor": str(secim_klasor.relative_to(ROOT)),
        "partiEslemesi": sutun_seti, "eslenemeyenSutunlar": dict(eslenemeyen),
        "ozet": {"cevre": len(cevreler), "ilce": sum(len(c.get("ilceler", [])) for c in cevreler),
                 "sehirKoyKirilimli": sum(1 for c in cevreler for i in c.get("ilceler", []) if "kirilim" in i)},
        "cevreler": cevreler,
    }


def main():
    secili = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    for kl in KLASORLER:
        for d in sorted((RAW / kl).iterdir()):
            if not d.is_dir() or (secili and d.name not in secili):
                continue
            o = extract(d, d.name)
            (OUT / f"{d.name}.json").write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
            print(d.name, o["ozet"], "eslenemeyen:", o["eslenemeyenSutunlar"] or "-")


if __name__ == "__main__":
    main()
