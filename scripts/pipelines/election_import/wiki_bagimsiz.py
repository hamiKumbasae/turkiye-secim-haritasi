"""
Yerel secim (belediye baskanligi) kayitlarinda YSK agregesine aktarilmamis bagimsiz aday oylarini,
depodaki Vikipedi il sayfalarinin ham kopyalarindan (data/raw/wikipedia/il-sayfalari/yerel/<secim>/)
tamamlar.

Sorun: eski fetch_yerel_v2.js calismasi YSK'nin bagimsiz aday sutunlarini aktarmiyordu (sonradan
ballot_votes.js ile duzeltildi, ama veri yeniden cekilmedi). Bu satirlarda parti oylari toplami
gecerli oydan az, oranlar eksik toplama gore hesaplanmis ve bazen kazanan yanlis (ornek 2024
Vakfikebir: kazanan bagimsiz Fuat Kocal %38,21, kayitta AK Parti %81,46).

Kapsam farki: kayitlarimiz YSK'nin ilce toplamidir (ilce belediyesi + beldeler); Vikipedi tablosu
yalniz ilce (ya da il merkezi / buyuksehir) belediyesini verir. Bu yuzden kaydin parti oylari
korunur, yalniz:
  - 'Bağımsız' = Vikipedi'deki bagimsiz adaylarin toplami (en cok aradaki fark kadar),
  - aradaki kalan fark 'Diğer'e eklenir (parti oylari toplami = gecerli oy),
  - oranlar gecerli oya gore yeniden hesaplanir,
  - kazanan Vikipedi'nin "secildi" isaretinden alinir (kapsam farki yuzunden oy toplamindan
    belirlenemez: ornek 2024 Kirklareli merkez MHP kazandi, beldelerle birlikte CHP onde gorunuyor);
    isaret yoksa en yuksek tekil bagimsiz aday en guclu partiyi geciyorsa 'Bağımsız', degilse
    en guclu parti,
  - kaynak.bagimsizTamamlama alanina Vikipedi revizyonu ve adaylar yazilir.
Vikipedi'de ilce bulunamazsa ya da bagimsiz aday yoksa yalniz fark 'Diğer'e eklenir
(kaynak.digerTamamlama).

Kullanim:
  .venv/bin/python scripts/pipelines/election_import/wiki_bagimsiz.py <secim> [kontrol|uygula]
"""
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

WIKI = ROOT / "data/raw/wikipedia/il-sayfalari/yerel"
# Vikipedi parti adi -> partiler.json anahtari (kazanan eslemesi icin)
PARTI = {
    "Adalet ve Kalkınma Partisi": "AK Parti", "Cumhuriyet Halk Partisi": "CHP", "Milliyetçi Hareket Partisi": "MHP",
    "İYİ Parti": "İYİ Parti", "Yeniden Refah Partisi": "YENİDEN REFAH", "Halkların Eşitlik ve Demokrasi Partisi": "DEM Parti",
    "Halkların Demokratik Partisi": "HDP", "Barış ve Demokrasi Partisi": "BDP", "Demokratik Toplum Partisi": "DTP",
    "Saadet Partisi": "SP", "Büyük Birlik Partisi": "BBP", "Demokratik Sol Parti": "DSP", "Demokrat Parti (2007)": "DP",
    "Hür Dava Partisi": "HÜDAPAR", "Zafer Partisi": "ZP", "Türkiye İşçi Partisi (2017)": "TİP",
    "Demokrasi ve Atılım Partisi": "DEVA", "Gelecek Partisi": "Gelecek Partisi", "Bağımsız Türkiye Partisi": "BTP",
    "Sol Parti (Türkiye)": "SOL PARTİ", "Vatan Partisi (Türkiye)": "VATAN", "Bağımsız": "Bağımsız",
}


def temizle(line):
    line = re.sub(r"<ref[^>]*/>", "", line)
    line = re.sub(r"<ref[^>]*>.*?</ref>", "", line)
    return re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", line)


def satir(line):
    """(parti, aday, oy, secildi) ya da None"""
    m = re.search(r"\{\{Siyasi parti haritarenk\|(.*?)\}\}", temizle(line))
    if not m:
        return None
    f = [x.strip() for x in m.group(1).split("|")]
    if len(f) < 3 or not re.fullmatch(r"[\d.]+", f[2]):
        return None
    return f[0], f[1], int(f[2].replace(".", "")), len(f) > 4 and f[4] == "1"


def sade(s):
    s = unicodedata.normalize("NFKD", s.replace("ı", "i").replace("İ", "i")).lower()
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


def bolumler(metin):
    """{sade_ad: [(parti, aday, oy, secildi)]}: '===[[Ilce]]===' ve '==X Belediyesi==' bolumleri."""
    out, ad, satirlar = {}, None, None
    for line in metin.splitlines():
        m = re.match(r"^(={2,3})\s*(.+?)\s*\1\s*$", line)
        if m:
            if ad and satirlar:
                out.setdefault(ad, satirlar)
            baslik = m.group(2)
            link = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", baslik)
            if link:
                ad = sade((link.group(2) or link.group(1)).split(",")[0])
            elif baslik.endswith("Belediyesi"):
                ad = "__il__"
            else:
                ad = None
            satirlar = []
            continue
        if ad is not None:
            s = satir(line)
            if s:
                satirlar.append(s)
    if ad and satirlar:
        out.setdefault(ad, satirlar)
    return out


def il_sayfalari(secim):
    idx = json.loads((WIKI / secim / "_index.json").read_text(encoding="utf-8"))["sayfalar"]
    sayfa = {}
    for baslik, bilgi in idx.items():
        m = re.match(r"(.+?)'(?:da|de|ta|te|nda|nde) ", baslik)
        if m and (WIKI / secim / bilgi["dosya"]).exists():
            sayfa[sade(m.group(1))] = (bolumler((WIKI / secim / bilgi["dosya"]).read_text(encoding="utf-8")), bilgi)
    return sayfa


def duzelt(secim, uygula):
    rec = load_election(secim)
    il_ad = {r["plaka"]: r["ad"] for r in rec["iller"]}
    sayfa = il_sayfalari(secim)
    rapor = []
    for lv in ("iller", "ilceler"):
        for r in rec[lv]:
            v = r.get("gecerliOy")
            oy = r.get("oy") or {}
            if not v or not oy or any(x.get("oy") is None for x in oy.values()):
                continue
            fark = v - sum(x["oy"] for x in oy.values())
            if fark <= 0:
                continue
            sp = sayfa.get(sade(il_ad.get(r["plaka"], "")))
            bol = None
            if sp:
                anahtar = "__il__" if lv == "iller" or r["ad"] == "Merkez" else sade(r["ad"])
                bol = sp[0].get(anahtar)
            bag = sorted([(a, o) for p, a, o, _ in (bol or []) if p == "Bağımsız"], key=lambda x: -x[1])
            secilen = next((p for p, _, _, s in (bol or []) if s), None)
            bag_top = min(sum(o for _, o in bag), fark)
            ek = {}
            if bag_top:
                ek["Bağımsız"] = bag_top
            if fark - bag_top:
                ek["Diğer"] = fark - bag_top
            eski_kazanan = r.get("kazanan")
            partiler = {p: x["oy"] for p, x in oy.items() if p not in ("Diğer", "Bağımsız")}
            en_parti = max(partiler, key=partiler.get) if partiler else eski_kazanan
            kazanan = "Bağımsız" if bag and bag[0][1] > partiler.get(en_parti, 0) else en_parti
            if secilen:
                k = PARTI.get(secilen)
                kazanan = k if k in oy or k in ek else ("Diğer" if "Diğer" in oy or "Diğer" in ek else eski_kazanan)
            rapor.append((lv, r["plaka"], r["ad"], round(fark / v * 100, 1), ek, eski_kazanan, kazanan, bag[:1]))
            if uygula:
                for p, o in ek.items():
                    oy.setdefault(p, {"oy": 0})
                    oy[p]["oy"] += o
                for x in oy.values():
                    x["oran"] = round(x["oy"] / v * 100, 2)
                r["kazanan"] = kazanan
                if not isinstance(r.get("kaynak"), dict):
                    r["kaynak"] = {}
                k = r["kaynak"]
                if bag_top:
                    k["bagimsizTamamlama"] = {
                        "kaynak": "Vikipedi il sayfası (YSK sonuçları), " + sp[1]["url"],
                        "adaylar": [[a, o] for a, o in bag],
                        "not": "YSK agregesine aktarılmamış bağımsız aday oyları; kazanan aday düzeyinde belirlendi",
                    }
                if ek.get("Diğer"):
                    k["digerTamamlama"] = {"oy": ek["Diğer"], "not": "parti oyları toplamı ile geçerli oy arasındaki fark"}
    if uygula:
        save_election(secim, rec)
    return rapor


if __name__ == "__main__":
    secim = sys.argv[1]
    uygula = len(sys.argv) > 2 and sys.argv[2] == "uygula"
    for satir in duzelt(secim, uygula):
        print(*satir)
