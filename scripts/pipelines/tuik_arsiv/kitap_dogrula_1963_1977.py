"""
1963-1977 yerel secim belediye baskanligi kayitlarini DIE kitaplariyla karsilastirir (yalniz rapor;
veriye dokunmaz).

Depodaki 1963yerel/1968yerel/1973yerel/1977yerel kayitlari Vikipedi il sayfalarindan gelir; o sayfalar
bu kitaplari kaynak gosterir. Bu betik her satirin (il satiri = il merkezi belediyesi, ilce satiri =
ilce merkezi belediyesi) sandik, secmen, gecerli oy ve parti oylarini kitabin taranmis metin katmaninda
arar.

Yontem (tahmin yok, yalniz arama):
  - Metin `pdftotext -layout` ile cikarilir (.cache/tuik/<demirbas>.txt). Satirdaki rakam disi her sey
    atilir (binlik bosluklari, ondalik isaretleri, tireler); sayi icindeki tipik OCR harfleri
    (i/ı/l/I/|/] -> 1, o/O -> 0, b -> 6, S -> 5) yalniz rakam iceren parcalarda cevrilir.
  - Her kitap icin satirin kitaptaki sutun sirasi bir "desen"dir; ornegin 1977 sol yuz:
    sandik, secmen, (oy kullanan + katilim), gecerli, AP oy+%, CHP oy+%, CGP oy+%. Oyu olmayan parti
    kitapta tiredir, desende yer almaz. Desen satirin rakam dizisinde sona dayali aranir (kitapta
    depoda olmayan bir partinin oyu varsa eslesmez). Bir tablo satiri OCR'de birden fazla satira
    bolunebildigi icin ardisik 1-3 satirin birlesimi de denenir.
  - 1963 kitabinda ad/sandik/secmen ve sonuc (gecerli + partiler) karsilikli sayfalarda; iki parca
    ayri aranir. 1973/1977'de partiler iki yuze bolunmus (sol: AP, CHP, CGP; sag: digerleri).
  - Eslesmeyen parcada her alan sirayla (sonra ikiserli) joker yapilir; tek bir joker ile eslesiyorsa
    o alanin kitaptaki okunusu raporlanir ("fark"). Kitaptaki okunusun kendisi de OCR hatasi olabilir;
    1973/1977'de kitabin basili yuzdesi okunusu destekliyorsa `yuzdeTutuyor: true`.

Sonuc: data/kaynaklar/tuik/yerel/<secim>/kitap_dogrulama.json ve docs/rapor/KITAP_DOGRULAMA_1963_1977.md

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/kitap_dogrula_1963_1977.py
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common.election_io import load_election  # noqa: E402
from kitap_birlestir import kitap_yolu  # noqa: E402

CACHE = ROOT / ".cache/tuik"
RAPOR = ROOT / "docs/rapor/KITAP_DOGRULAMA_1963_1977.md"

# desen ogeleri: "sandik", "secmen", "gecerli", "ARA" (\d+: oy kullanan vb.), "KAT" (katilim %),
# ("parti", yuzdeli_mi)
P = lambda *ad, yuzde=False: [(a, yuzde) for a in ad]  # noqa: E731
KITAPLAR = {
    "1963yerel": {
        "demirbas": "0015160", "kunye": "DİE, Mahalli Seçimler Sonuçları, 17 Kasım 1963 (Yayın No. 474, 1965)",
        "parcalar": {
            "kimlik": ["sandik", "secmen"],
            "sonuc": ["gecerli"] + P("AP", "CHP", "CKMP", "MP62", "TİP", "YTP61", "Bağımsız"),
        },
        "sona_dayali": {"sonuc"},
    },
    "1968yerel": {
        "demirbas": "0015244", "kunye": "DİE, Mahalli Seçimler Sonuçları, 2 Haziran 1968 (Yayın No. 555, 1969)",
        "parcalar": {
            "satir": ["sandik", "secmen", "ARA", "gecerli", "KAT"]
                     + P("AP", "BP69", "CHP", "CKMP", "CGP", "MP62", "TİP", "YTP61", "Bağımsız"),
        },
        "sona_dayali": {"satir"},
    },
    "1973yerel": {
        "demirbas": "0015468", "kunye": "DİE, Mahalli Seçimler Sonuçları, 9 Aralık 1973 (Yayın No. 716, 1974)",
        "sayfa": "BAŞKANLI",
        "parcalar": {
            "sol": ["sandik", "secmen", "ARA", "gecerli", "KAT"] + P("AP", "CHP", "CGP", yuzde=True),
            "sag": P("DEMP73", "MP62", "MHP", "MSP", "TBP73", "Bağımsız", yuzde=True),
        },
        "sona_dayali": {"sol", "sag"},
    },
    "1977yerel": {
        "demirbas": "0015740", "kunye": "DİE, Yerel Seçim Sonuçları, 11 Aralık 1977 (1979)",
        "sayfa": "BAŞKANLI",
        "parcalar": {
            "sol": ["sandik", "secmen", "ARA", "KAT", "gecerli"] + P("AP", "CHP", "CGP", yuzde=True),
            "sag": P("DEMP73", "MSP", "MHP", "SDP", "TBP73", "TİP", "TSİP", "Bağımsız", yuzde=True),
        },
        "sona_dayali": {"sol", "sag"},
    },
}
OCR = str.maketrans({"i": "1", "ı": "1", "l": "1", "I": "1", "|": "1", "]": "1", "o": "0", "O": "0",
                     "b": "6", "S": "5"})
SAYILI = re.compile(r"^[\dilIı|\]oObS.,]+$")


def metin(demirbas):
    CACHE.mkdir(parents=True, exist_ok=True)
    txt = CACHE / f"{demirbas}.txt"
    pdf = kitap_yolu(demirbas)
    if not txt.exists() or txt.stat().st_mtime < pdf.stat().st_mtime:
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
    return txt.read_text(encoding="utf-8", errors="ignore").split("\f")


def rakamlar(satir):
    parca = []
    for t in satir.split():
        if SAYILI.match(t) and re.search(r"\d", t):
            t = t.translate(OCR)
        parca.append(re.sub(r"\D", "", t))
    return "".join(parca)


def hucreler(satir):
    """layout satirini sutunlara (2+ bosluk) boler; ad ve tire hucreleri atilir, kalanlar rakam dizisi"""
    out = []
    harf = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂâÎî]")
    for h in re.split(r"\s{2,}", satir.strip()):
        if len(harf.findall(h)) >= 3:
            # ad iceren hucre ("65.6 Sami Öznur", "00 Adana"): adin oncesindeki/sonrasindaki sayi parcasi
            t = h.split()
            ilk = next(i for i, x in enumerate(t) if len(harf.findall(x)) >= 2 or i == len(t) - 1)
            son = max(i for i, x in enumerate(t) if len(harf.findall(x)) >= 2) if any(
                len(harf.findall(x)) >= 2 for x in t) else len(t) - 1
            parcalar = [" ".join(t[:ilk]), " ".join(t[son + 1:])]
        else:
            parcalar = [h]
        for x in parcalar:
            d = rakamlar(x)
            if d:
                out.append(d)
    return out


class Kitap:
    """kitabin aday satirlari: tek satir ve 2-3 ardisik satirin birlesimi"""

    def __init__(self, sayfalar, filtre):
        tek = {}  # birlesim boyu -> [(sayfa, metin, rakam_dizisi, hucreler)]
        for no, pg in enumerate(sayfalar, 1):
            if filtre and filtre not in " ".join(pg.splitlines()[:8]).upper():
                continue
            ss = [s for s in pg.splitlines() if s.strip()]
            diz = [rakamlar(s) for s in ss]
            hc = [hucreler(s) for s in ss]
            for k in (1, 2, 3):
                for i in range(len(ss) - k + 1):
                    d = "".join(diz[i:i + k])
                    if d:
                        tek.setdefault(k, []).append((no, " ⏎ ".join(x.strip() for x in ss[i:i + k]), d,
                                                      [h for x in hc[i:i + k] for h in x]))
        # once tek satirlar: eslesme en kisa birlesimde raporlanir
        self.satirlar = tek.get(1, []) + tek.get(2, []) + tek.get(3, [])
        self.indeks = {}
        for j, (_, _, _, hs) in enumerate(self.satirlar):
            for h in set(hs):
                self.indeks.setdefault(h, set()).add(j)


def degerler(row, desen):
    """desen -> ogeler: (etiket, deger, tur) tur: V (birebir hucre), VP (oy + yuzde), W (herhangi bir hucre)"""
    oy = {p: (v or {}).get("oy") for p, v in (row.get("oy") or {}).items()}
    out = []
    for o in desen:
        if o in ("ARA", "KAT"):
            out.append((o, None, "W"))
        elif isinstance(o, str):
            v = {"sandik": row.get("sandik"), "secmen": row.get("secmen"), "gecerli": row.get("gecerliOy")}[o]
            out.append((o, v, "V") if v is not None else (o, None, "W"))  # depoda yoksa herhangi bir hucre
        else:
            parti, yuzde = o
            v = oy.get(parti)
            if v:
                out.append((parti, v, "VP" if yuzde else "V"))
    return out


def akis_deseni(ogeler, sona):
    parca = []
    for et, v, tur in ogeler:
        if tur == "W":
            parca.append(r"\d{1,9}")
        else:
            parca.append(str(v) + (r"\d{1,4}" if tur == "VP" else ""))
    return re.compile("".join(parca) + ("$" if sona else ""))


def yuzde_tutar(oy, yz, gecerli):
    if not gecerli or not yz:
        return False
    return abs(100 * oy / gecerli - int(yz) / 10) <= 0.11 or abs(100 * oy / gecerli - int(yz)) <= 0.6


def hizala(C, E, k, sona, gecerli):
    """E'yi C'nin bitisik bir penceresine en fazla k farkla hizalar; (farklar, birebir_sayisi) listesi"""
    cozum = []

    def git(ci, ei, farklar, tam):
        if len(cozum) > 20:
            return
        if ei == len(E):
            if not sona or ci == len(C):
                cozum.append((list(farklar), tam))
            return
        et, v, tur = E[ei]
        if ci >= len(C):
            if tur != "W" and len(farklar) < k:
                git(ci, ei + 1, farklar + [{"alan": et, "depo": v, "kitap": None}], tam)
            return
        h = C[ci]
        if tur == "W":
            git(ci + 1, ei + 1, farklar, tam)
            return
        # kitapta okunamayan deger (taramada kesik/silik): hucre tuketmeden atlanir, fark sayilir
        if len(farklar) < k:
            git(ci, ei + 1, farklar + [{"alan": et, "depo": v, "kitap": None}], tam)
        if tur == "V":
            if h == str(v):
                git(ci + 1, ei + 1, farklar, tam + 1)
            elif len(farklar) < k:
                git(ci + 1, ei + 1, farklar + [{"alan": et, "depo": v, "kitap": int(h)}], tam)
            return
        # VP: [oy][yuzde] ya da birlesik [oy+yuzde]
        if h == str(v) and ci + 1 < len(C) and len(C[ci + 1]) <= 4:
            git(ci + 2, ei + 1, farklar, tam + 1)
        if h.startswith(str(v)) and 1 <= len(h) - len(str(v)) <= 4:
            git(ci + 1, ei + 1, farklar, tam + 1)
        # taramada oy sutunu kesik, yalniz yuzde okunuyor (1973 sag yuz): yuzde depodaki oyla tutarliysa
        if len(h) <= 4 and yuzde_tutar(v, h, gecerli):
            git(ci + 1, ei + 1, farklar, tam + 1)
        if len(farklar) < k:
            if h != str(v) and ci + 1 < len(C) and len(C[ci + 1]) <= 4:
                git(ci + 2, ei + 1, farklar + [{"alan": et, "depo": v, "kitap": int(h),
                                               "yuzdeTutuyor": yuzde_tutar(int(h), C[ci + 1], gecerli)}], tam)
            for n in range(1, 5):
                if len(h) > n and int(h[:-n]) != v and yuzde_tutar(int(h[:-n]), h[-n:], gecerli):
                    git(ci + 1, ei + 1, farklar + [{"alan": et, "depo": v, "kitap": int(h[:-n]),
                                                   "yuzdeTutuyor": True}], tam)

    for c0 in range(len(C)):
        git(c0, 0, [], 0)
    return cozum


def dogrula_parca(row, desen, kitap, sona):
    ogeler = degerler(row, desen)
    anlamli = [o for o in ogeler if o[2] != "W"]
    # parcada depodan deger yoksa (ornek: sag yuzde partisi olmayan satir) dogrulanacak bir sey yok
    if not anlamli or (len(desen) > 2 and all(o[0] in ("sandik", "secmen") for o in anlamli)):
        return {"durum": "bos"}
    rx = akis_deseni(ogeler, sona)
    on = str(anlamli[0][1])
    for no, s, d, _ in kitap.satirlar:
        if on in d and rx.search(d):
            return {"durum": "birebir", "sayfa": no, "kitapSatiri": s[:300]}
    if len(anlamli) < 3:
        return {"durum": "bulunamadi"}
    # aday satirlar: depodaki degerlerden en az ikisini hucre olarak iceren
    say = {}
    for o in anlamli:
        for j in kitap.indeks.get(str(o[1]), ()):
            say[j] = say.get(j, 0) + 1
    esik = 2 if len(anlamli) > 3 else 1
    adaylar_ = [j for j, n in say.items() if n >= esik]
    for k in (1, 2):
        bulunan = []
        for j in adaylar_:
            no, s, d, C = kitap.satirlar[j]
            for farklar, tam in hizala(C, ogeler, k, sona, row.get("gecerliOy")):
                if farklar and tam >= max(2, len(anlamli) - k):
                    bulunan.append({"sayfa": no, "kitapSatiri": s[:300], "farklar": farklar})
        if bulunan:
            # okunamadi (atlanan deger) en az olan hizalama: bastaki degeri atlamak her zaman mumkun
            # oldugu icin, okunan ama farkli bir hucre atlamaya tercih edilir
            eksik = lambda b: sum(f["kitap"] is None for f in b["farklar"])  # noqa: E731
            enaz = min(map(eksik, bulunan))
            bulunan = [b for b in bulunan if eksik(b) == enaz]
            tek = {json.dumps(b["farklar"], sort_keys=True) for b in bulunan}
            return {"durum": "fark" if len(tek) == 1 else "fark_belirsiz", **bulunan[0],
                    **({"secenekler": [json.loads(t) for t in sorted(tek)][:5]} if len(tek) > 1 else {})}
    # son adim: (sandik, secmen) yan yana hucre olarak bulunan satir -> ayni belediye, degerleri cok farkli
    sandik, secmen = row.get("sandik"), row.get("secmen")
    if any(o[0] == "sandik" for o in ogeler) and sandik and secmen and secmen >= 100:
        bulunan = []
        for j in kitap.indeks.get(str(secmen), ()):
            no, s, d, C = kitap.satirlar[j]
            if " ⏎ " in s:
                continue
            if any(C[i] == str(sandik) and C[i + 1] == str(secmen) for i in range(len(C) - 1)):
                bulunan.append({"sayfa": no, "kitapSatiri": s[:300], "kitapHucreleri": C})
        # ayni sandik/secmen meclis tablosunda da var; il fasikulunde baskanlik tablosu meclisten once
        if bulunan:
            return {"durum": "farkli", **min(bulunan, key=lambda b: b["sayfa"])}
    return {"durum": "bulunamadi"}


def satirlar(rec):
    for i in rec["iller"]:
        yield {"tur": "il_merkezi", "il": i["ad"], "ad": i["ad"], "row": i}
    il_ad = {i["plaka"]: i["ad"] for i in rec["iller"]}
    for r in rec["ilceler"]:
        yield {"tur": "ilce", "il": il_ad.get(r["plaka"], r["plaka"]), "ad": r["ad"], "row": r}


def pdf_yolu(demirbas):
    tek = f"data/raw/tuik/mahalli-kitap/{demirbas}.pdf"
    return tek if (ROOT / tek).exists() else tek + ".parca* (kitap_birlestir.py)"


DURUM_ACIKLAMA = [
    ("birebir", "Satırın bütün değerleri (sandık, seçmen, geçerli oy, her partinin oyu) kitapta aynen var."),
    ("kitap_ic_tutarsizlik", "Partilerin oyu kitapla aynı; yalnız geçerli oy farklı. Kitabın bastığı geçerli oy "
     "kendi parti toplamını tutmuyor (DİE açıklamasındaki tutanak farkı), depo ise geçerli oyu parti toplamı "
     "olarak almış. Depoda hata değil."),
    ("fark", "Satır kitapta bulundu, bir-iki alan farklı (aşağıda listeli)."),
    ("farkli", "Belediye kitapta sandık+seçmen ile bulundu ama oylar geniş ölçüde farklı (aşağıda listeli)."),
    ("kismi", "Bir kısmı doğrulandı (örnek: 1963'te sandık/seçmen ya da 1973/77'de sol yüz); kalan kısım "
     "taramada okunamıyor ya da bulunamadı. Okunan her değer birebir."),
    ("bulunamadi", "Kitabın metin katmanında satır bulunamadı (tarama/OCR)."),
]


def rapor_yaz():
    veriler = {s: json.loads((ROOT / f"data/kaynaklar/tuik/yerel/{s}/kitap_dogrulama.json").read_text(encoding="utf-8"))
               for s in KITAPLAR}
    L = ["# 1963–1977 yerel seçim: depo verisi ile DİE kitaplarının karşılaştırması", "",
         "Üreten: `scripts/pipelines/tuik_arsiv/kitap_dogrula_1963_1977.py` (yalnız rapor, veriye dokunmaz). "
         "Satır satır sonuç: `data/kaynaklar/tuik/yerel/<seçim>/kitap_dogrulama.json`.", "",
         "Karşılaştırılan: belediye başkanlığı seçimi, il satırı (il merkezi belediyesi) ve ilçe satırları "
         "(ilçe merkezi belediyesi). Depodaki bu yılların verisi Vikipedi il sayfalarından; o sayfalar bu "
         "kitapları kaynak gösteriyor. İl genel meclisi ve belediye meclisi depoda yok, karşılaştırılmadı.", "",
         "## Özet", "",
         "| Seçim | Kitap | Satır | " + " | ".join(d for d, _ in DURUM_ACIKLAMA) + " |",
         "|---|---|---:|" + "---:|" * len(DURUM_ACIKLAMA)]
    for s, v in veriler.items():
        o = v["ozet"]
        L.append(f"| {s} | {v['kitap']} | {o['satir']} | "
                 + " | ".join(str(o["durum"].get(d, 0)) for d, _ in DURUM_ACIKLAMA) + " |")
    L += ["", "Durumlar:", ""] + [f"- **{d}**: {a}" for d, a in DURUM_ACIKLAMA]
    L += ["", "Kitaptaki değer, kitabın kendi yüzdesiyle (1973/1977) ya da kendi toplamıyla tutuyorsa "
          "**destekli** sayılır: büyük olasılıkla depodaki (Vikipedi) değer yanlış. Destekli değilse fark "
          "tarama okumasından da gelebilir; sayfaya bakılmalı.", ""]
    for baslik, sec in (("Destekli farklar (depo değeri büyük olasılıkla yanlış)", True),
                        ("Desteksiz farklar (sayfaya bakılmalı; OCR olabilir)", False)):
        L += [f"## {baslik}", "", "| Seçim | İl | Belediye | Alan | Depo | Kitap | PDF sayfa |", "|---|---|---|---|---:|---:|---:|"]
        gorulen, gurultu = set(), 0
        for s, v in veriler.items():
            for k in v["satirlar"]:
                if k["durum"] != "fark":
                    continue
                for p in k["parcalar"].values():
                    for f in p.get("farklar", []):
                        if f["kitap"] is None:
                            continue
                        destek = bool(f.get("yuzdeTutuyor")) or (k.get("kitapToplamTutuyor") and not k["depoIcTutarlilik"]) \
                            or (k.get("kitapToplamTutuyor") and f["alan"] != "gecerli")
                        if destek != sec:
                            continue
                        # il satiri ile "Merkez" ilce satiri ayni belediye: bir kez yazilir
                        anahtar = (s, k["il"], f["alan"], f["depo"], f["kitap"], p["sayfa"])
                        if anahtar in gorulen:
                            continue
                        gorulen.add(anahtar)
                        if not sec and len(str(f["kitap"])) <= 1 < len(str(f["depo"])):
                            gurultu += 1  # tek rakamli okunus: hizalama bos/sacma bir hucreye oturmus
                            continue
                        ad = k["ad"] if k["tur"] == "ilce" else f"{k['ad']} (il merkezi)"
                        L.append(f"| {s[:4]} | {k['il']} | {ad} | {f['alan']} | {f['depo']} | {f['kitap']} | {p['sayfa']} |")
        if gurultu:
            L += ["", f"Ayrıca {gurultu} alanda kitap okunuşu tek rakam (taramadaki boş/kirli hücre); listelenmedi, "
                  "ayrıntısı JSON'da."]
        L.append("")
    L += ["## Oyları geniş ölçüde farklı satırlar", "",
          "Belediye kitapta sandık ve seçmen sayısıyla bulundu; kitap satırındaki sayılar (sütun sırasıyla; "
          "tireler okunmadığı için parti sütunu ayrıca kontrol edilmeli):", "",
          "| Seçim | İl | Belediye | Depo (geçerli; partiler) | Kitap satırı (sayılar) | PDF sayfa |", "|---|---|---|---|---|---:|"]
    for s, v in veriler.items():
        kayit = json.loads((ROOT / f"data/normalized/elections/yerel/{s}.json").read_text(encoding="utf-8"))
        for k in v["satirlar"]:
            if k["durum"] != "farkli":
                continue
            p = next(p for p in k["parcalar"].values() if p["durum"] == "farkli")
            satirlar_ = kayit["iller"] if k["tur"] == "il_merkezi" else kayit["ilceler"]
            row = next(r for r in satirlar_ if r["ad"] == k["ad"] and r["plaka"] == k["plaka"])
            depo = f"{row['gecerliOy']}; " + ", ".join(f"{a} {b['oy']}" for a, b in row["oy"].items())
            ad = k["ad"] if k["tur"] == "ilce" else f"{k['ad']} (il merkezi)"
            L.append(f"| {s[:4]} | {k['il']} | {ad} | {depo} | {' '.join(p['kitapHucreleri'])} | {p['sayfa']} |")
    L += ["", "## Yöntem ve sınırlar", "",
          "- Kitap metni `pdftotext -layout` ile okunur; satırın rakamları kitabın sütun sırasıyla aranır "
          "(tahmin ya da hesap yok). Eşleşmeyen satırda bir-iki alan joker yapılıp kitaptaki okunuş raporlanır.",
          "- Oyu olmayan parti kitapta tiredir; tireler taramada her zaman okunmadığı için aynı sıradaki iki "
          "parti sütunu birbirinden ayırt edilemez (değer ve sıra doğrulanır, sütun etiketi değil).",
          "- 1963 kitabında ad/sandık/seçmen ve sonuçlar karşılıklı sayfalarda; iki parça ayrı aranır.",
          "- 1973 kitabının sağ yüzünde DP oy sütunu taramada kesik; yalnız yüzdesi okunuyor, oy o yüzdeyle tutuyorsa kabul edilir.",
          "- Gözle doğrulanan örnekler (sayfa görüntüsü): 1968 Adana merkez geçerli 54 522, partiler toplamı 52 619 "
          "(kitap içi); 1963 Adıyaman muteber oy 4 563, partiler 4 337 (kitap içi); 1977 Bilecik Merkez AP 836 "
          "(%27,1; depoda 636); 1973 Afyonkarahisar Merkez bağımsız 6 434 (%65,6; depoda 5 302).", ""]
    RAPOR.write_text("\n".join(L), encoding="utf-8")
    print(RAPOR.relative_to(ROOT))


def main():
    ozet = {}
    for secim, cfg in KITAPLAR.items():
        sayfalar = metin(cfg["demirbas"])
        kitap = Kitap(sayfalar, cfg.get("sayfa"))
        rec = load_election(secim)
        kayitlar = []
        for s in satirlar(rec):
            row = s["row"]
            if not row.get("gecerliOy"):
                continue
            oy = {p: (v or {}).get("oy") or 0 for p, v in (row.get("oy") or {}).items()}
            sonuc = {"tur": s["tur"], "il": s["il"], "ad": s["ad"], "plaka": row["plaka"],
                     "geomId": row.get("geomId"), "parcalar": {},
                     "depoIcTutarlilik": sum(oy.values()) == row["gecerliOy"]}
            if "Diğer" in oy:
                sonuc["not"] = "depoda 'Diğer' kalemi var (Vikipedi'de ayrı verilmeyen partiler); kitapla birebir eşleşemez"
            for ad, desen in cfg["parcalar"].items():
                sonuc["parcalar"][ad] = dogrula_parca(row, desen, kitap, ad in cfg["sona_dayali"])
            durumlar = {p["durum"] for p in sonuc["parcalar"].values()} - {"bos"}
            sonuc["durum"] = ("birebir" if durumlar == {"birebir"} else
                              "farkli" if "farkli" in durumlar else
                              "fark" if "fark" in durumlar and durumlar <= {"birebir", "fark"} else
                              "bulunamadi" if durumlar == {"bulunamadi"} else "kismi")
            okunamayan = [f["alan"] for p in sonuc["parcalar"].values() for f in p.get("farklar", [])
                          if f["kitap"] is None]
            if okunamayan:
                sonuc["kitaptaOkunamayan"] = okunamayan
            gercek = [f for p in sonuc["parcalar"].values() for f in p.get("farklar", []) if f["kitap"] is not None]
            if sonuc["durum"] == "fark" and not gercek:
                sonuc["durum"] = "kismi"  # okunan her deger birebir, kalanlar taramada okunamiyor
            if sonuc["durum"] == "fark":
                farklar = gercek
                kitap_deger = {"gecerli": row["gecerliOy"], **oy}
                for f in farklar:
                    if f["kitap"] is not None:
                        kitap_deger[f["alan"]] = f["kitap"]
                sonuc["kitapToplamTutuyor"] = sum(v for k, v in kitap_deger.items() if k != "gecerli") \
                    == kitap_deger["gecerli"]
                if {f["alan"] for f in farklar} == {"gecerli"} and sonuc["depoIcTutarlilik"]:
                    # partilerin hepsi kitapla ayni; kitabin bastigi gecerli oy parti toplamindan farkli,
                    # depo (Vikipedi) gecerli oyu parti toplami olarak yazmis
                    sonuc["durum"] = "kitap_ic_tutarsizlik"
            kayitlar.append(sonuc)
        say = {}
        for k in kayitlar:
            say[k["durum"]] = say.get(k["durum"], 0) + 1
        alan_fark = sum(1 for k in kayitlar for p in k["parcalar"].values() if p["durum"] == "fark"
                        for f in p.get("farklar", []) if f["kitap"] is not None)
        ozet[secim] = {"kitap": cfg["kunye"], "satir": len(kayitlar), "durum": say, "farkliAlan": alan_fark}
        out = ROOT / f"data/kaynaklar/tuik/yerel/{secim}/kitap_dogrulama.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"secim": secim, "kitap": cfg["kunye"],
                                   "pdf": pdf_yolu(cfg["demirbas"]),
                                   "betik": "scripts/pipelines/tuik_arsiv/kitap_dogrula_1963_1977.py",
                                   "ozet": ozet[secim], "satirlar": kayitlar}, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
        print(secim, ozet[secim])
    rapor_yaz()
    return ozet


if __name__ == "__main__":
    main()
