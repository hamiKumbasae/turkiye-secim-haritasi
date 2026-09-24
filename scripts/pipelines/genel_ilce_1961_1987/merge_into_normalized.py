"""
data/raw/tuik/secimdagitimapp-ilce-1961-1987/ altindaki TUIK raporlarindan
1961, 1965, 1969, 1973, 1977, 1983, 1987 genel secimlerinin ILCE satirlarini
uretip data/normalized/elections/genel/<yil>.json'a yazar.

Il satirlarinin oy/secmen/vekil degerlerine DOKUNULMAZ (onlar YSK/TUIK il
arsivinden, zaten resmi toplamlarla dogrulanmis) - sadece `ilceSayisi`
guncellenir. Bilinen istisna: Sakarya (asagiya bakin).

geomId secimi: ayni ilce adinin (plaka + fold(ad)) donemin en yakin
ilce-duzeyi verisi olan secimlerinde (1984yerel/1989yerel/1991/1994yerel/1995)
hangi geomId'ye (modern TR-D-* veya tarihsel HIST-*) baglandigina bakilir -
yani bu script YENI bir sinir karari vermez, projenin mevcut (dogrulanmis)
tarihsel eslemesini yeniden kullanir. 1987 icin 1989yerel, digerleri icin
1984yerel onceliklidir. Karsiligi olmayan buyuksehir "Merkez" ilceleri
METRO_MERKEZ'de (bkz. geo/historical/metro_merkez_1961_1987.yaml).

Ilce toplamlari il toplamiyla birebir tutmayabilir - bu bir hata degil,
kaynagin kendi yapisi: DIE'nin 1965 yayininin (Yayin No. 513) aciklamasina
gore il toplamlari YSK'nin Resmi Gazete'de ilan ettigi rakamlar, ilce
rakamlari ise ilce secim kurullarinin birlestirme tutanaklari; 1987'de il
toplamina gumruk kapisi oylari da dahil. Farklar raporlanir, duzeltilmez.

Kullanim:
  python3 scripts/pipelines/genel_ilce_1961_1987/merge_into_normalized.py          # kuru calisma (rapor)
  python3 scripts/pipelines/genel_ilce_1961_1987/merge_into_normalized.py --write  # yaz
"""
import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE))
from common.election_io import load_election, save_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402
from tuik_report import column, parse_report, party_columns  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "tuik" / "secimdagitimapp-ilce-1961-1987"
YEARS = ["1961", "1965", "1969", "1973", "1977", "1983", "1987"]

# TUIK sutun basligi (bosluk-normalize) -> partiler.json anahtari
PARTY = {
    "AP": "AP", "CHP": "CHP", "CKMP": "CKMP", "YTP": "YTP61", "MİLLET PARTİSİ": "MP62",
    "TİP": "TİP", "GP": "GP", "CGP": "CGP", "MHP": "MHP",
    "BİRLİK PARTİSİ": "TBP73", "TBP": "TBP73",  # 1969'da "Birlik Partisi", 1971'den itibaren ayni parti "Türkiye Birlik Partisi"
    "DEMOKRATİK PARTİ": "DEMP73", "MSP": "MSP",
    "ANAP": "ANAP", "HP": "HP", "MDP": "MDP",
    "RP": "RP", "DYP": "DYP", "DSP": "DSP", "SHP": "SHP", "IDP": "IDP", "MÇP": "MÇP",
    "BĞMZ": "Bağımsız",
}

# TUIK ilce yazimi -> projenin (1984-1995 verisindeki) yazimi. Anahtar: (plaka, fold(tuik_adi))
ALIAS = {
    (1, "TUFANBEYLI (MAGARA)"): "Tufanbeyli",
    (3, "SINANPASA (SINCANLI)"): "Sinanpaşa",
    (3, "SINCANLI"): "Sinanpaşa",
    (4, "DOGUBEYAZIT"): "Doğubayazıt",
    (6, "ELMADAGI"): "Elmadağ",
    (6, "S,KOCHISAR"): "Şereflikoçhisar",
    (11, "BOZOYUK"): "Bozüyük",
    (16, "M,KEMALPASA"): "Mustafakemalpaşa",
    (16, "MKEMALPASA"): "Mustafakemalpaşa",
    (17, "IMROZ"): "Gökçeada",  # 1970'e kadar resmi adi Imroz
    (28, "S,KARAHISAR"): "Şebinkarahisar",
    (28, "SKARAHISAR"): "Şebinkarahisar",
    (30, "BEYTUSSEBAB"): "Beytüşşebap",
    (32, "EGRIDIR"): "Eğirdir",
    (32, "SKARAAGAC"): "Şarkikaraağaç",
    (44, "ARAPKIR"): "Arapgir",
    (44, "POTURGE"): "Pütürge",
    (62, "CEMISKEZEK"): "Çemişgezek",
}

# Referans secimlerden BAGIMSIZ, dogrudan verilen geomId'ler. Eminonu 1928-2008
# arasi ayri ilceydi (5747 sayili Kanun ile Fatih'e katildi); 1984-2004 verisinde
# ayri satiri yok, ama 2007referandum'da oldugu gibi Eminonu'nun kendi satiri
# varken Fatih de Eminonu'suz tarihsel poligonuna baglanmali (yoksa cakisir).
OVERRIDE = {
    (34, "EMINONU"): "HIST-Istanbul-Eminonu",
    (34, "FATIH"): "HIST-Istanbul-Fatih",
    # Malatya: 1991-2011 verisinde Merkez HIST-Malatya-Merkez'e (Battalgazi+
    # Yesilyurt birlesimi) bagli ve AYNI yil Yesilyurt'un kendi satiri da var -
    # bu iki poligon cakisiyor (onceden var olan sorun). 1961-1987'de de
    # Yesilyurt ayri ilce, bu yuzden cakismayi tekrarlamamak icin Merkez modern
    # Battalgazi'ye baglanir (6360 ile 2012'de eski Merkez'in dogusu
    # Battalgazi'ye, batisi Yesilyurt'a gecti - bati kismi eksik kapsanir).
    (44, "MERKEZ"): "TR-D-44-004",
}

# Ilcenin kendisi o donemde BASKA bir ile bagliyken, projenin referans
# secimlerinde yalnizca modern ilinin altinda gecenler: (plaka_o_donem, fold) -> (ref_plaka, ref_adi)
CROSS_PLAKA = {
    (41, "KAYNARCA"): (54, "Kaynarca"),  # 1961/1965'te Kocaeli'ye bagli, sonra Sakarya
}

# Buyuksehir merkez ilceleri: referans secimlerde (1984-1995) cogunlukla
# coktan bolunmus oldugu icin karsiligi yok. Deger: sentetik HIST- id'si
# (geo/historical/metro_merkez_1961_1987.yaml'dan uretilen) ya da None
# (henuz dogrulanmis poligon yok -> satir tabloda gorunur, haritada cizilmez).
METRO_MERKEZ = {}
_mm = ROOT / "geo" / "historical" / "metro_merkez_1961_1987.json"
if _mm.exists():
    for e in json.loads(_mm.read_text(encoding="utf-8")):
        for y in e["years"]:
            METRO_MERKEZ[(e["plaka"], y)] = e["syntheticId"]

REF_ORDER = {
    "default": ["1984yerel", "1989yerel", "1991", "1994yerel", "1995"],
    "1987": ["1989yerel", "1984yerel", "1991", "1994yerel", "1995"],
}


def build_ref_index():
    idx = {}
    for ref in set(REF_ORDER["default"]):
        for r in load_election(ref)["ilceler"]:
            idx.setdefault((r["plaka"], fold(r["ad"])), {})[ref] = r["geomId"]
    return idx


def resolve_geomid(ref_idx, year, plaka, ad):
    key = (plaka, fold(ad))
    if key in ALIAS:
        key = (plaka, fold(ALIAS[key]))
    if key in CROSS_PLAKA:
        rp, rad = CROSS_PLAKA[key]
        key = (rp, fold(rad))
    if key in OVERRIDE:
        return OVERRIDE[key], "override"
    if key[1] == "MERKEZ" and (plaka, year) in METRO_MERKEZ:
        return METRO_MERKEZ[(plaka, year)], "metro_merkez"
    hits = ref_idx.get(key)
    if not hits:
        return None, "eslesmedi"
    for ref in REF_ORDER.get(year, REF_ORDER["default"]):
        if ref in hits:
            return hits[ref], ref
    return None, "eslesmedi"


def display_name(plaka, ad):
    return ALIAS.get((plaka, fold(ad)), ad)


def build_row(year, plaka, ad, rec, geom_id):
    secmen = column(rec, "Kayıtlı")
    kullanan = column(rec, "Oy kullanan")
    gecerli = column(rec, "Geçerli")
    oy = {}
    for h, v in party_columns(rec).items():
        code = PARTY[" ".join(h.split())]
        if v:
            oy[code] = oy.get(code, 0) + v
    toplam = sum(oy.values())
    kazanan = max(oy, key=oy.get) if oy else None
    return {
        "ad": display_name(plaka, ad),
        "plaka": plaka,
        "geomId": geom_id,
        "secmen": secmen,
        "gecerliOy": gecerli,
        "katilim": round(kullanan * 100 / secmen, 2) if secmen and kullanan is not None else None,
        "sandik": column(rec, "Sandık"),
        "kazanan": kazanan,
        "oy": {k: {"oy": v, "oran": round(v * 100 / toplam, 2) if toplam else 0.0}
               for k, v in sorted(oy.items(), key=lambda kv: -kv[1])},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    ref_idx = build_ref_index()
    unresolved = collections.defaultdict(list)
    sum_report = []
    for year in YEARS:
        rec = load_election(year)
        il_by_plaka = {r["plaka"]: r for r in rec["iller"]}
        rows = []
        for f in sorted((RAW / year).glob("*.html")):
            plaka = int(f.name[:2])
            parsed = parse_report(f.read_bytes())
            il_ad, il_rec = parsed["il"]
            if plaka not in il_by_plaka:
                raise SystemExit(f"{year}: {plaka} ({il_ad}) normalize kayitta yok")
            for ad, r in parsed["ilceler"]:
                gid, via = resolve_geomid(ref_idx, year, plaka, ad)
                if gid is None:
                    unresolved[(plaka, il_ad, ad)].append(year)
                rows.append(build_row(year, plaka, ad, r, gid))
            # ilce toplami vs il toplami (TUIK'in kendi il satiri)
            for label, pref in [("secmen", "Kayıtlı"), ("gecerli", "Geçerli")]:
                s = sum(column(r, pref) or 0 for _, r in parsed["ilceler"])
                t = column(il_rec, pref) or 0
                if s != t:
                    sum_report.append((year, il_ad, label, t, s, round((s - t) * 100 / t, 2) if t else None))
            il_by_plaka[plaka]["ilceSayisi"] = len(parsed["ilceler"])
        mapped = sum(1 for r in rows if r["geomId"])
        print(f"{year}: {len(rows)} ilce, geomId'li {mapped}, geomId'siz {len(rows) - mapped}")
        if args.write:
            rec["ilceler"] = rows
            save_election(year, rec)

    print("\n-- geomId bulunamayan ilceler (haritada cizilmez, tabloda gorunur):")
    for (plaka, il, ad), ys in sorted(unresolved.items()):
        print(f"  {plaka:2d} {il} / {ad}: {', '.join(ys)}")
    big = [r for r in sum_report if r[5] is None or abs(r[5]) >= 1]
    print(f"\n-- ilce toplami != il toplami: {len(sum_report)} kayit (>= %1: {len(big)})")
    for r in big:
        print("  ", *r)
    if not args.write:
        print("\n(kuru calisma - yazmak icin --write)")


if __name__ == "__main__":
    main()
