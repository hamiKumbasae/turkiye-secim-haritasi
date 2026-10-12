"""
2009, 2014, 2019 ve 2024 yerel secimlerinde 'Diğer' toplamini YSK'nin kendi parti sutunlarina ayirir.

merge_yerel_v2.py buyuk partiler disindaki butun partileri tek bir 'Diğer' satirinda topluyordu; bu
yuzden 'Diğer' bazi ilcelerde kazanan gorunuyordu (ornek 2019: İYİ Parti'nin kazandigi ilceler).
YSK agregeleri butun parti sutunlariyla yeniden cekildi (.github/workflows/ysk-yerel-cek.yml ->
data/raw/ysk/yerel-v2-agrege/<secim>.json, fetch_yerel_v2.js ciktisi).

Kural (tahmin yok, satir ancak yeni cekilen veri eskisiyle birebir tutarsa ayrilir):
  - kayit ile taze agrege ayni il/ilce olmali (eslesme merge_yerel_v2.py ile ayni: plaka;
    acikveri-ilce-geomid-eslemesi.json, yoksa tarihsel merkez geomId'si),
  - gecerli oy birebir ayni olmali ve taze agregede parti + bagimsiz oylarinin toplami gecerli oya
    esit olmali (kaynak eksiksiz),
  - kayittaki her adlandirilmis parti (Diğer ve Bağımsız disi) taze agregedeki oyuna birebir esit olmali,
  - kayittaki 'Diğer' + 'Bağımsız' = tazede kayitta olmayan partiler + taze bagimsiz oyu (birebir).
    Eski cekimde bagimsiz toplami yoktu: ya diger_tamamla.py aradaki farki 'Diğer'e eklemisti
    (digerTamamlama) ya da wiki_bagimsiz.py Vikipedi'den eklemisti (bagimsizTamamlama). Yeni
    agregede YSK'nin kendi bagimsiz toplami var; bu iki tamamlama onunla birebir aciklaniyor.
  Uyarsa 'Diğer' o partilere ayrilir, Bağımsız YSK'nin oyu olur (oran, kaydin mevcut oranlariyla ayni
  tabana gore); kaynak.digerAyristirma'ya yazilir (bagimsiz oyu degistiyse onceki/ysk). Uymayan
  satira dokunulmaz ve nedeni raporlanir.

Kazanan: kayitlardaki kazanan alani yer yer sandik toplamindan farkli resmi sonucu tasir (itiraz/
yeniden sayim, Vikipedi'den aday duzeyinde belirlenmis kazanan; ornek 2024 Kütahya, Kilimli). Bu
yuzden yalniz kazanan 'Diğer' ise yeniden hesaplanir. Baska bir kazanan, yalniz su durumda
'Bağımsız' olur: kayitta aday duzeyinde bilgi yok (bagimsizTamamlama yok) ve TEK bir bagimsiz adayin
YSK oyu kayittaki kazanandan fazla (data/raw/ysk/yerel-v2-agrege/bagimsiz-aday.json,
fetch_bagimsiz_aday.js). Bagimsizlarin toplami onde ama tek aday degilse kazanan degismez.
Idempotent: ayrilmis satirda 'Diğer' kalmadigi icin ikinci calistirma bir sey degistirmez.
merge_yerel_v2.py yeniden calistirilirsa bu betik de ardindan calistirilmalidir.

Kullanim (repo kokunden):
  python3 scripts/pipelines/election_import/diger_ayristir_yerel.py [kontrol|uygula]
"""
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common.election_io import load_election, save_election  # noqa: E402
from common.hist_geomid import resolve_historical_merkez  # noqa: E402
from party_map_helper import PARTILER, build_party_mapping  # noqa: E402

AGREGE_DIR = ROOT / "data" / "raw" / "ysk" / "yerel-v2-agrege"
GEOMID_MAP = json.loads((ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))
SECIMLER = ["2009yerel", "2014yerel", "2019yerel", "2024yerel"]
ADAY_DOSYASI = AGREGE_DIR / "bagimsiz-aday.json"
# partiler.json'da olmayan, ayni partinin ikinci adi (2024 Karaisalı'da tek kayit)
ANAHTAR_DUZELTME = {"DEVA PARTİSİ": "DEVA"}
BAGIMSIZ_COL_RE = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")
DIGER = "Diğer"


def taze_oylar(agg, col_to_key):
    oy = collections.Counter()
    for col, v in (agg.get("oy") or {}).items():
        if not v:
            continue
        if BAGIMSIZ_COL_RE.match(col):
            oy["Bağımsız"] += v
        elif col in col_to_key:
            oy[col_to_key[col]] += v
        else:
            raise SystemExit(f"eslenmemis sutun: {col}")
    return oy


def ilce_agregeleri(agrege, yil):
    """merge_yerel_v2.py'deki ilce -> geomId eslemesinin aynisi."""
    out = {}
    for key, agg in agrege["ilceler"].items():
        geom = GEOMID_MAP.get(key)
        if not geom:
            hist = resolve_historical_merkez(agg["ilId"], agg["ilceAdi"], yil)
            if hist and agg.get("sandikSayisi", 0) > 0:
                geom = hist
        if not geom:
            continue
        onceki = out.get(geom)
        if onceki is not None and onceki.get("sandikSayisi", 0) > 0 and agg.get("sandikSayisi", 0) == 0:
            continue
        out[geom] = agg
    return out


def ayristir_satir(r, agg, col_to_key, dosya, tek_bagimsiz=None):
    oy = r.get("oy") or {}
    dig = oy.get(DIGER)
    if not dig:
        return None
    if agg is None:
        return "eşleşen YSK satırı yok"
    if agg.get("gecerli") != r.get("gecerliOy"):
        return "geçerli oy farklı"
    kaynak = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
    taze = taze_oylar(agg, col_to_key)
    if sum(taze.values()) != agg.get("gecerli"):
        return "YSK parti toplamı geçerli oya eşit değil"
    # Bagimsizlar ve 'Diğer' disindaki her parti birebir tutmali
    adli = [p for p in oy if p not in (DIGER, "Bağımsız")]
    for p in adli:
        if oy[p].get("oy") != taze.get(p, 0):
            return "adlandırılmış parti oyu farklı"
    # Eski kayitta bagimsizlar ya hic yoktu (aradaki fark digerTamamlama ile 'Diğer'e eklenmisti) ya da
    # Vikipedi'den eklenmisti (bagimsizTamamlama); ikisi birlikte YSK'nin bagimsiz + kucuk parti
    # toplamina birebir esit olmali.
    eski_bag = (oy.get("Bağımsız") or {}).get("oy", 0)
    kalan = {p: v for p, v in taze.items() if p not in adli and v}
    if eski_bag + dig.get("oy") != sum(kalan.values()):
        return "Diğer + Bağımsız toplamı tutmuyor"
    if set(kalan) <= {"Bağımsız"} and kalan.get("Bağımsız", 0) == eski_bag:
        return "ayrılacak parti yok"

    taban = sum(x["oy"] for x in oy.values())
    del oy[DIGER]
    oy.pop("Bağımsız", None)
    for p, v in kalan.items():
        oy[p] = {"oran": round(v / taban * 100, 2), "oy": v}
    eski = r.get("kazanan")
    if eski == DIGER or eski not in oy:
        r["kazanan"] = max(oy, key=lambda p: oy[p]["oy"])
    elif (oy.get("Bağımsız", {}).get("oy", 0) > oy[eski]["oy"] and "bagimsizTamamlama" not in kaynak
            and tek_bagimsiz is not None and tek_bagimsiz > oy[eski]["oy"]):
        r["kazanan"] = "Bağımsız"
    r["oy"] = dict(sorted(oy.items()))
    kaynak["digerAyristirma"] = {
        "yontem": "YSK açık veri agregesindeki parti sütunlarına ayrıldı ('Diğer' + bağımsız toplamı birebir tuttu)",
        "kaynak": dosya, "digerOy": dig.get("oy"),
        "dagilim": dict(sorted((p, v) for p, v in kalan.items() if p != "Bağımsız"))}
    if kalan.get("Bağımsız", 0) != eski_bag:
        kaynak["digerAyristirma"]["bagimsiz"] = {"onceki": eski_bag, "ysk": kalan.get("Bağımsız", 0)}
    if eski != r["kazanan"]:
        kaynak["digerAyristirma"]["oncekiKazanan"] = eski
    if tek_bagimsiz is not None:
        kaynak["digerAyristirma"]["enCokOyAlanBagimsizAday"] = tek_bagimsiz
    r["kaynak"] = kaynak
    return "ayrıldı"


def ayristir(anahtar, rec):
    dosya = AGREGE_DIR / f"{anahtar}.json"
    agrege = json.loads(dosya.read_text(encoding="utf-8"))
    mevcut = set()
    for lv in ("iller", "ilceler"):
        for r in rec[lv]:
            for eski_ad, yeni_ad in ANAHTAR_DUZELTME.items():
                if eski_ad in r["oy"]:
                    r["oy"][yeni_ad] = r["oy"].pop(eski_ad)
                    r["oy"] = dict(sorted(r["oy"].items()))
                if r.get("kazanan") == eski_ad:
                    r["kazanan"] = yeni_ad
            mevcut.update(r["oy"])
    col_to_key = build_party_mapping(agrege["colToName"], (mevcut & set(PARTILER)) - {DIGER, "Bağımsız"}, {})
    adaylar = {}
    if ADAY_DOSYASI.exists():
        for a in json.loads(ADAY_DOSYASI.read_text(encoding="utf-8")):
            if a["secim"] == anahtar and a.get("bagimsiz"):
                adaylar[a["geomId"]] = max(a["bagimsiz"].values())
    yil = int(anahtar[:4])
    ilceler = ilce_agregeleri(agrege, yil)
    goreli = str(dosya.relative_to(ROOT))
    sayac = collections.Counter()
    kazanan_degisti = []
    for r in rec["iller"]:
        eski = r.get("kazanan")
        s = ayristir_satir(r, agrege["iller"].get(str(r["plaka"])), col_to_key, goreli)
        if s:
            sayac[s] += 1
            if eski != r.get("kazanan"):
                kazanan_degisti.append((r["ad"], eski, r["kazanan"]))
    for r in rec["ilceler"]:
        eski = r.get("kazanan")
        s = ayristir_satir(r, ilceler.get(r.get("geomId")), col_to_key, goreli, adaylar.get(r.get("geomId")))
        if s:
            sayac[s] += 1
            if eski != r.get("kazanan"):
                kazanan_degisti.append((r["ad"], eski, r["kazanan"]))
    kalan_diger_kazanan = [r["ad"] for lv in ("iller", "ilceler") for r in rec[lv] if r.get("kazanan") == DIGER]
    return sayac, kazanan_degisti, kalan_diger_kazanan


if __name__ == "__main__":
    uygula = len(sys.argv) > 1 and sys.argv[1] == "uygula"
    for anahtar in SECIMLER:
        if not (AGREGE_DIR / f"{anahtar}.json").exists():
            print(f"{anahtar}: agrege yok, atlandı")
            continue
        rec = load_election(anahtar)
        sayac, degisen, kalan = ayristir(anahtar, rec)
        print(f"{anahtar}: {dict(sayac)}")
        print(f"   kazananı değişen {len(degisen)}: {degisen[:8]}{' …' if len(degisen) > 8 else ''}")
        print(f"   hâlâ 'Diğer' kazanan {len(kalan)}: {kalan[:10]}")
        if uygula:
            save_election(anahtar, rec)
    if not uygula:
        print("(kontrol: hiçbir dosya yazılmadı; uygulamak için 'uygula')")
