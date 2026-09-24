"""
Resmî Gazete'deki Yüksek Seçim Kurulu ara seçim bildirilerinden il / seçim
çevresi düzeyinde milletvekili ara seçim sonuçlarını çıkarır:

  data/kaynaklar/resmi_gazete/genel/<secim>.json   (1968ara, 1975ara, 1986ara)

Ham PDF'ler: data/raw/resmi_gazete/<sayı>.pdf (resmigazete.gov.tr/arsiv/<sayı>.pdf).
Gazete iki sütunlu basıldığı için her sayfa sol ve sağ yarı olarak ayrı okunur.
Her blok için doğrulama: partiler + bağımsız = geçerli oy. Ulusal toplam TESAV
"Milletvekili Ara Seçim Sonuçları" (DİE kaynaklı) ile karşılaştırılır.

Kullanım:
  .venv/bin/python scripts/pipelines/resmi_gazete/extract_ara_secim.py
"""
import collections
import json
import pathlib
import re
import sys

import pdfplumber

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "resmi_gazete"
OUT = ROOT / "data" / "kaynaklar" / "resmi_gazete" / "genel"

# secim -> (RG sayisi, tarih, bildiri sayfalari, bicim, parti kisaltmasi -> anahtar, TESAV ulusal toplami)
SECIMLER = {
    "1968ara": ("12922", "2 Haziran 1968", range(13, 18), "ili",
                {"AP": "AP", "CHP": "CHP", "CKMP": "CKMP", "GP": "CGP", "MP": "MP62", "TIP": "TİP", "BAGIMSIZ": "Bağımsız"},
                {"AP": 507241, "CHP": 295069, "CKMP": 23448, "CGP": 66079, "MP62": 85665, "TİP": 67502, "Bağımsız": 3578}),
    "1975ara": ("15394", "12 Ekim 1975", range(11, 18), "ili",
                {"AP": "AP", "CHP": "CHP", "DP": "DEMP73", "MSP": "MSP", "MHP": "MHP", "TBP": "TBP73", "BAGIMSIZ": "Bağımsız"},
                {"AP": 524001, "CHP": 409387, "DEMP73": 30654, "MHP": 24848, "MSP": 84706, "TBP73": 3014, "Bağımsız": 1211}),
    "1986ara": ("19247", "28 Eylül 1986", range(19, 26), "cevre",
                {"ANAVATAN PARTISI": "ANAP", "DOGRU YOL PARTISI": "DYP", "SOSYALDEMOKRAT HALKCI PARTI": "SHP",
                 "DEMOKRATIK SOL PARTI": "DSP", "REFAH PARTISI": "RP", "MILLIYETCI CALISMA PARTISI": "MÇP",
                 "ISLAHATCI DEMOKRASI PARTISI": "IDP", "BAGIMSIZ": "Bağımsız", "BAGIMSIZ ADAYLAR": "Bağımsız",
                 "RETAH PARTISI": "RP"},  # OCR: "ReTah"
                {"ANAP": 805267, "DYP": 590069, "SHP": 570055, "DSP": 213168, "RP": 137485, "MÇP": 55144,
                 "IDP": 15729, "Bağımsız": 5306}),
}
SAYI = r"(\d{1,3}(?:[. ]\d{3})+|\d+)"


def _tr_baslik(s):
    kucuk = str.maketrans("IİŞĞÜÇÖÂÎÛ", "ıişğüçöâîû")
    return " ".join(w[:1] + w[1:].translate(kucuk).lower() for w in s.split())


def kolon_metni(pg):
    w = pg.width
    return "\n".join((pg.crop((x0, 0, x1, pg.height)).extract_text() or "") for x0, x1 in [(0, w / 2), (w / 2, w)])


def sayi(s):
    return int(re.sub(r"[. ]", "", s))


def parti_kodu(satir):
    """'C. K M P.» » » 4.850' -> 'CKMP'; 'T. 1 P.' / 'T İ P.' -> 'TIP'; 'T3P.' -> 'TBP'."""
    bas = re.split(r"»|:|s[ıi]n[ıi]n|\bnin\b|geçerli", satir)[0]
    k = fold(re.sub(r"[^A-Za-zÇĞİÖŞÜçğıöşü13]", "", bas)).replace(" ", "")
    return {"T3P": "TBP", "TUP": "TBP", "T1P": "TIP", "TLP": "TIP", "TP": "TIP"}.get(k, k.replace("1", "I"))


def ili_bloklari(metin, ara_mi):
    """'İLİ: X' blok bicimi (1968, 1975). ara_mi(onceki_satirlar) -> blok MV ara secimi mi."""
    satirlar = metin.split("\n")
    bloklar, cur, bolum = [], None, None
    for s in satirlar:
        f = fold(s)
        if "MILLETVEKILI ARA SECIMI" in f or f.strip() == "MILLETVEKILI SECIMI":
            bolum = "mv"
        elif "SENATOSU UYELERI SECIMI" in f or "SENATOSU UYELERI SECIMI YAPILAN" in f:
            bolum = "senato"
        if cur is not None and (re.match(r"^\s*\d+\s*[—-]\s", s) or "KAZANAN" in f or "SECILEN" in f or "SECILENLER" in f):
            cur["kapali"] = True  # blok bitti (bolum numarali satir / secilenler)
        m = re.match(r"^\s*[İIÎ][LH][İIÎ]?\s*:?\s*([A-ZÇĞİÖŞÜÂÎÛ ]{3,}?)\s*[^A-Za-zÇĞİÖŞÜ]*$", s)
        if m:
            cur = {"il": m.group(1).strip(), "bolum": bolum, "oy": collections.Counter(), "satirlar": []}
            bloklar.append(cur)
            continue
        if cur is None or cur.get("kapali"):
            continue
        cur["satirlar"].append(s)
        s_ = re.sub(r"(?<=\s)T(?=\d)", "1", s)  # OCR: "T36.394" -> "136.394"
        # rakam yerine okunan harfler (yalnizca sayi grubunun icinde): "3S210" -> "35210"
        harfli = bool(re.search(r"(?<=\d)[SsOo](?=\d|\s*$)|(?<=\s)[Ss](?=\d{2})", s_))
        ham_m = re.search(r"([\dSsOo][\dSsOo. ]*[\dSsOo])\s*\*?\s*$", s_) if harfli else None
        s_ = re.sub(r"(?<=\d)[Ss](?=\d|\s*$)|(?<=\s)[Ss](?=\d{2})", "5", s_)
        s_ = re.sub(r"(?<=\d)[Oo](?=\d)", "0", s_)
        m = re.search(SAYI + r"\s*\*?\s*$", s_)
        if "KATILMA" in f:
            continue
        if not m:
            # sayisi alt satira kaymis parti satiri: "T. 1 P. » » » »" / ": 10 584"
            if "BAGIMSIZ" in f:
                cur["bekleyen"] = "BAGIMSIZ"
            elif "»" in s or re.search(r"s[ıi]n[ıi]n", s):
                cur["bekleyen"] = parti_kodu(s)
            continue
        v = sayi(m.group(1))
        if cur.get("bekleyen") and not re.search(r"s[ıi]n[ıi]n|»", s):
            k = cur.pop("bekleyen")
            cur["oy"][k] += v
            if harfli and ham_m:
                cur.setdefault("harfDuzeltilen", []).append((k, ham_m.group(1)))
            continue
        cur.pop("bekleyen", None)
        if "BAGIMSIZ" in f:
            cur["oy"]["BAGIMSIZ"] += v
            continue
        if ("SECMEN SAYI" in f) and "KULLANAN" not in f:
            cur.setdefault("secmen", v)
        elif "KULLANAN" in f:
            cur.setdefault("oyKullanan", v)
        elif "GECERLI" in f and ("OY PUSULASI SAYISI" in f) and ("SININ" not in f and "SINDEN" not in f and "SINE" not in f
                                                                  and "NIN" not in f and "»" not in s and "SININ" not in f):
            cur.setdefault("gecerliOy", v)
        elif "BAGIMSIZ" in f:
            cur["oy"]["BAGIMSIZ"] += v
        elif "»" in s or "SININ" in f or "NIN GECERLI" in f or "SINDEN" in f:
            k = parti_kodu(s)
            cur["oy"][k] += v
            if harfli and ham_m:
                cur.setdefault("harfDuzeltilen", []).append((k, ham_m.group(1)))
    return bloklar


def cevre_bloklari(metin):
    """1986 bicimi: 'N — X ili (k) Nolu Seçim Çevresi' / 'X İli Seçim Çevresi'."""
    bloklar, cur = [], None
    for s in metin.split("\n"):
        f = fold(s)
        m = re.match(r"^\s*\d+\s*[—-]\s*(.+?)\s+[İIi1l]l[iı]\s*(\((\d+)\)\s*Nolu)?\s*Seçim", s)
        if m and "SECIM CEVRES" in f:
            cur = {"il": m.group(1).strip(), "cevre": m.group(3), "oy": collections.Counter(), "satirlar": []}
            bloklar.append(cur)
            continue
        if cur is None:
            continue
        cur["satirlar"].append(s)
        m = re.search(SAYI + r"\s*$", s)
        if not m:
            continue
        v = sayi(m.group(1))
        ad = fold(re.sub(SAYI + r"\s*$", "", s)).strip(" .:-")
        if ad.startswith("KAYITLI SECMEN"):
            cur["secmen"] = v
        elif ad.startswith("OYUNU KULLANAN"):
            cur["oyKullanan"] = v
        elif ad.startswith("GECERLI OY SAYISI"):
            cur["gecerliOy"] = v
        elif "PARTI" in ad or ad.startswith("BAGIMSIZ"):
            ad = re.sub(r"^BUYUK", "BUYUK", ad)
            cur["oy"][ad] += v
    return bloklar


def isle(secim, sayi_, tarih, sayfalar, bicim, esleme, tesav):
    pdf = pdfplumber.open(RAW / f"{sayi_}.pdf")
    metin = "\n".join((kolon_metni(pdf.pages[i - 1]) if bicim == "ili" else (pdf.pages[i - 1].extract_text() or ""))
                      for i in sayfalar)
    if bicim == "ili":
        bloklar = [b for b in ili_bloklari(metin, None) if b["bolum"] == "mv"]
    else:
        bloklar = cevre_bloklari(metin)
    iller, eslenemeyen, ulusal = [], collections.Counter(), collections.Counter()
    gorulen = set()
    for b in bloklar:
        anahtar = (fold(b["il"]), b.get("cevre"))
        if anahtar in gorulen:  # ayni sayfa PDF'te iki kez (1968: s.14 = s.42)
            continue
        gorulen.add(anahtar)
        oy = {}
        for k, v in b["oy"].items():
            key = esleme.get(k)
            if key is None:
                eslenemeyen[k] += v
                key = k  # kaynaktaki adiyla
            oy[key] = oy.get(key, 0) + v
            ulusal[key] += v
        il_ad = {"UKFA": "URFA"}.get(b["il"].strip(), b["il"].strip())
        kayit = {"il": _tr_baslik(il_ad) if il_ad.isupper() else il_ad, "secimCevresi": b.get("cevre"), "secmen": b.get("secmen"),
                 "oyKullanan": b.get("oyKullanan"), "gecerliOy": b.get("gecerliOy"),
                 "oy": dict(sorted(oy.items(), key=lambda kv: -kv[1]))}
        hd = [(esleme.get(k, k), ham) for k, ham in b.get("harfDuzeltilen", [])]
        if b.get("gecerliOy") and sum(oy.values()) != b["gecerliOy"] and len(hd) == 1:
            # OCR rakam-harf karisikligi ("3S210"): yalnizca basili rakamlara uyan adaylar
            # (S -> 3/5/8, O -> 0) denenir; toplam = gecerli kisitina EN YAKIN olan alinir
            p_, ham = hd[0]
            import itertools
            yer = [i for i, ch in enumerate(ham) if ch in "SsOo"]
            secenek = []
            for comb in itertools.product(*[("3", "5", "8") if ham[i] in "Ss" else ("0",) for i in yer]):
                h = list(ham)
                for i, c in zip(yer, comb):
                    h[i] = c
                secenek.append(sayi("".join(h)))
            diger = sum(oy.values()) - oy[p_]
            yeni = min(secenek, key=lambda x: abs(diger + x - b["gecerliOy"]))
            if yeni != oy[p_]:
                kayit["ocrDuzeltme"] = {"alan": p_, "okunan": oy[p_], "duzeltilen": yeni,
                                        "neden": f"OCR '{ham}': rakam yerine harf; basili rakamlara uyan adaylardan toplam kisitina en yakini"}
                ulusal[p_] += yeni - oy[p_]
                oy[p_] = yeni
                kayit["oy"] = dict(sorted(oy.items(), key=lambda kv: -kv[1]))
        if b.get("gecerliOy") and sum(oy.values()) != b["gecerliOy"]:
            kayit["tutarsiz"] = f"partiler toplami {sum(oy.values())} != gecerli {b['gecerliOy']}"
        iller.append(kayit)
    tesav_fark = {k: (ulusal.get(k, 0), v) for k, v in tesav.items() if ulusal.get(k, 0) != v}
    veri = {"secim": secim, "tur": "milletvekili_ara_secimi", "tarih": tarih, "kaynak": "resmi_gazete",
            "yayin": f"Resmî Gazete sayı {sayi_} — Yüksek Seçim Kurulu bildirisi",
            "hamDosya": f"data/raw/resmi_gazete/{sayi_}.pdf", "url": f"https://www.resmigazete.gov.tr/arsiv/{sayi_}.pdf",
            "duzey": "il / seçim çevresi (ilçe kırılımı bildiride yok)",
            "tesavUlusalKarsilastirma": {"tutan": len(tesav) - len(tesav_fark), "farkli": tesav_fark},
            "eslenemeyenPartiler": dict(eslenemeyen), "iller": iller}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{secim}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(secim, len(iller), "il/cevre;", "tutarsiz:", [i["il"] for i in iller if i.get("tutarsiz")],
          "| TESAV farki:", tesav_fark, "| eslenemeyen:", dict(eslenemeyen))


EK_ACIKLAMA = {
    "1968ara": "2 Haziran 1968 milletvekili ara seçimi (Adana, Çorum, Diyarbakır, İstanbul, Urfa) — il düzeyi",
    "1975ara": "12 Ekim 1975 milletvekili ara seçimi (Amasya, Bursa, Eskişehir, Niğde, Urfa, Zonguldak) — il düzeyi",
    "1986ara": "28 Eylül 1986 milletvekili ara seçimi (11 seçim çevresi) — seçim çevresi düzeyi",
}


def ek_yaz(secim):
    """Kaynak katmanindan ek kayit: data/normalized/ek/yenileme_ara/<yil>mv_ara.json"""
    sys.path.insert(0, str(HERE.parent / "wikipedia_arsiv"))
    from iller import plaka
    d = json.loads((OUT / f"{secim}.json").read_text(encoding="utf-8"))
    ad = secim.replace("ara", "mv_ara")
    iller = []
    for i in d["iller"]:
        k = {"il": i["il"], "plaka": plaka(i["il"]), "secimCevresi": i["secimCevresi"],
             **{f: i[f] for f in ("secmen", "oyKullanan", "gecerliOy")}, "oy": i["oy"],
             "kaynak": {"ana": "resmi_gazete", "yayin": d["yayin"], "hamDosya": d["hamDosya"],
                        **({"ocrDuzeltme": i["ocrDuzeltme"]} if i.get("ocrDuzeltme") else {}),
                        **({"kaynakIciTutarsizlik": i["tutarsiz"]} if i.get("tutarsiz") else {})}}
        iller.append(k)
    veri = {"secim": ad, "tur": "yenileme_ara", "aciklama": EK_ACIKLAMA[secim], "duzey": d["duzey"],
            "kaynak": {"ana": "resmi_gazete", "yayin": d["yayin"], "url": d["url"], "hamDosya": d["hamDosya"],
                       "kaynakKatmani": f"data/kaynaklar/resmi_gazete/genel/{secim}.json"},
            "dogrulama": {"tesavUlusalToplam": d["tesavUlusalKarsilastirma"],
                          "not": "TESAV 'Milletvekili Ara Seçim Sonuçları' (DİE kaynaklı) ulusal toplamlarıyla karşılaştırma"},
            "eslenemeyenPartiler": d["eslenemeyenPartiler"], "iller": iller}
    hedef = ROOT / "data" / "normalized" / "ek" / "yenileme_ara" / f"{ad}.json"
    hedef.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    for secim, args in SECIMLER.items():
        isle(secim, *args)
        ek_yaz(secim)


if __name__ == "__main__":
    main()
