"""
DIE Cumhuriyet Senatosu secim kitaplarinin "il ve ilceler itibariyle" ozet
tablolarini (taranmis, OCR metinli) kaynak katmanina cikarir:

  data/kaynaklar/tuik/senato/<secim>.json      (1966senato, 1968senato, ...)
  data/kaynaklar/tuik/genel/<ara-secim>.json   (ayni kitaptaki milletvekili ara secimi, varsa)

Kitaplar buyuk (7-218 MB) oldugu icin depoya konmaz; her birinin URL'si ve
sha256'si `KITAPLAR`'da sabitlenir, PDF'ler --pdf-dir ile verilen klasorden
okunur (yoksa indirilir). Depoya giren: bu script + cikarilan JSON + sayfa
metinleri (data/raw/tuik/senato-metin/<demirbas>/<sayfa>.txt).

Okuma: die_tablo.sayfa_tablosu (kelime koordinatlari). Her satir icin
dogrulama:
  (1) partiler + bagimsiz == muteber oy      (satir ici)
  (2) ilcelerin toplami == il toplami        (sutun bazinda)
  (3) il toplami == Wikipedia il sonucu      (bagimsiz ikinci kaynak)
(1) tutmayan satirda, satirin rakam parcalari kisitla yeniden bolunur
(tek cozum varsa kabul, `kisitlaCozuldu`); yine tutmazsa satir kaynaktaki
haliyle `tutarsiz` isaretlenir (kaynagin kendi hatasi olabilir - 1966 Ankara
gibi, Wikipedia da ayni farki gosteriyor).

Kullanim:
  .venv/bin/python scripts/pipelines/tuik_arsiv/extract_senato.py --pdf-dir <klasor> [1966senato ...]
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE))
import die_tablo  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
OUT = ROOT / "data" / "kaynaklar" / "tuik"
METIN = ROOT / "data" / "raw" / "tuik" / "senato-metin"

# kitap -> ozet tablo yapilandirmasi. `tablolar`: [(ilk_sayfa, son_sayfa, secim_anahtari, sutunlar)]
# sutunlar: soldan saga TUM sayi sutunlari; "%" = okunup atilan yuzde sutunu.
KITAPLAR = {
    "1966senato": {
        "demirbas": "0015213", "sha256": None,
        "baslik": "DİE, Cumhuriyet Senatosu Üyeleri Kısmi Seçim Sonuçları, 5 Haziran 1966 (1967)",
        "tablolar": [(31, 37, "1966senato", ["secmen", "oyKullanan", "muteber", "AP", "CHP", "CKMP", "MP62", "TİP", "YTP61", "Bağımsız"]),
                     (38, 38, "1966ara", ["secmen", "oyKullanan", "muteber", "AP", "CHP", "CKMP", "MP62", "TİP", "YTP61", "Bağımsız"])],
    },
    "1968senato": {
        "demirbas": "0015265", "sha256": None,
        "baslik": "DİE, Cumhuriyet Senatosu Üyeleri Kısmi Seçim Sonuçları, 2 Haziran 1968 (1969)",
        "tablolar": [(20, 25, "1968senato", ["sandik", "secmen", "oyKullanan", "muteber", "%",
                                             "AP", "%", "CHP", "%", "CKMP", "%", "CGP", "%", "MP62", "%", "TİP", "%", "Bağımsız", "%"])],
    },
    "1973senato": {
        "demirbas": "0015450", "sha256": None,
        "baslik": "DİE, Milletvekili ve Cumhuriyet Senatosu Üyeleri Seçimi Sonuçları, 14 Ekim 1973 (1973)",
        # karsilikli sayfalar: sol (ad + ilk sutunlar) / sag (adsiz, kalan partiler)
        "cift": [(74, 86, "1973senato",
                  ["secmen", "oyKullanan", "%", "muteber", "AP", "%", "CHP", "%"],
                  ["CGP", "%", "DEMP73", "%", "MP62", "%", "MHP", "%", "MSP", "%", "TBP73", "%", "Bağımsız", "%"])],
    },
    "1975senato": {
        "demirbas": "0015581", "sha256": None,
        "baslik": "DİE, Cumhuriyet Senatosu Üyeleri ve Milletvekili Ara Seçim Sonuçları, 12 Ekim 1975 (1976)",
        "cift": [(26, 38, "1975senato",
                  ["secmen", "oyKullanan", "%", "muteber", "AP", "%"],
                  ["CHP", "%", "DEMP73", "%", "MHP", "%", "MSP", "%", "TBP73", "%", "Bağımsız", "%"])],
    },
    "1979senato": {
        "demirbas": "0015789", "sha256": None,
        "baslik": "DİE, Cumhuriyet Senatosu Üyeleri Üçtebir Yenileme ve Milletvekili Ara Seçimi Sonuçları, 14 Ekim 1979 (1980)",
        "cift": [(20, 32, "1979senato",
                  ["secmen", "oyKullanan", "%", "muteber", "AP", "%", "CHP", "%", "CGP", "%"],
                  ["MHP", "%", "MSP", "%", "SDP", "%", "TBP73", "%", "TİP", "%", "TSİP", "%", "Bağımsız", "%"]),
                 # ayni kitap, Bolum II: 14 Ekim 1979 milletvekili ara secimi (5 il), ayni duzen
                 (614, 616, "1979ara",
                  ["secmen", "oyKullanan", "%", "muteber", "AP", "%", "CHP", "%", "CGP", "%"],
                  ["MHP", "%", "MSP", "%", "SDP", "%", "TBP73", "%", "TİP", "%", "TSİP", "%", "Bağımsız", "%"])],
    },
    "1961senato": {
        "demirbas": "0015147", "sha256": None,
        "baslik": "DİE, Milletvekili ve Senato Üyesi Seçimi Sonuçları, 15.10.1961 — İl, ilçe ve sandık bölgeleri itibariyle (1964)",
        # MV ve Senato ayni satirda: MV sutunlari ("%" = okunup atilir; projede TUIK'ten zaten var)
        # + Senato: kullanan, muteber, AP, CHP, CKMP, YTP, bagimsiz. Il toplami ("Toplam - Total")
        # ilcelerden SONRA; il adi ilk ilce satirinda "ANTALYA (Mer.)".
        "mvCapali": [(9, 18, "1961senato", ["secmen", "oyKullanan", "muteber", "AP", "CHP", "CKMP", "YTP61", "Bağımsız"])],
    },
    "1964senato": {
        "demirbas": "0015169", "sha256": None,
        "baslik": "DİE, Kısmi Senato Üyeleri Seçimi Sonuçları, 7 Haziran 1964 (1963)",
        # ozet tablo yok: il il sandik listeleri; ilce basligi "DİYADİN (Merkez)",
        # ilce toplami "Toplam", il toplami "İl Genel Toplamı"
        "sandikListesi": [(9, 708, "1964senato", ["secmen", "oyKullanan", "muteber", "AP", "CHP", "CKMP", "YTP61", "Bağımsız"])],
    },
    "1977senato": {
        "demirbas": "0015631", "sha256": None,
        "baslik": "DİE, 5 Haziran 1977 Milletvekili Genel ve Cumhuriyet Senatosu Üyeleri Üçtebir Yenileme Seçimi Sonuçları (1977)",
        "cift": [(82, 92, "1977senato",
                  ["secmen", "oyKullanan", "%", "muteber", "AP", "%", "CHP", "%"],
                  ["CGP", "%", "DEMP73", "%", "MSP", "%", "MHP", "%", "TBP73", "%", "TİP", "%", "Bağımsız", "%"])],
    },
}
SUTUN_ONCE = ["secmen", "oyKullanan", "muteber"]


def pdf_yolu(demirbas, pdf_dir):
    p = pathlib.Path(pdf_dir) / f"{demirbas}.pdf"
    if not p.exists():
        url = f"https://kutuphane.tuik.gov.tr/pdf/{demirbas}.pdf"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (secim-haritasi arsiv)"})
        p.write_bytes(urllib.request.urlopen(req, timeout=1800).read())
    return p


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


BASLIK_KELIME = ("SECMEN", "SAYISI", "LISTESINDE", "KULLANAN", "MUTEBER", "SIYASI", "PARTILER", "SANDIK",
                 "BAGIM", "TABLO", "HAZIRAN", "EKIM", "SONUCLAR", "ILLER", "YAZILI", "SEHIR", "KOY",
                 "SENATORLUK", "BULUNAN", "YAPILMISTIR")


def satir_turu(etiket):
    """il / ilce / genel / None. OCR '»' isaretini ve 'İl' kelimesini her zaman
    tanimiyor; bu yuzden 'Toplam' gecen satir il (ya da genel), baslik
    kelimesi icermeyen diger etiketli satirlar ilce sayilir."""
    f = fold(etiket)
    if not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,}", etiket):
        return None
    if re.search(r"([A-Za-zÇĞİÖŞÜçğıöşü])\1\1", etiket):  # OCR'in uc kez bastigi baslik yazisi
        return None
    if "GENEL TOPLAM" in f or f.startswith("GENCI TOPLAM") or f.startswith("TURKIYE"):
        return "genel"
    if "TOPLAM" in f:
        return "il"
    if re.search(r"\s(IL)$", f) and f.split()[0] not in ("MERKEZ",):  # "A. KARAHİSAR İL" (TOPLAMI kaymis)
        return "il"
    if set(re.findall(r"[A-Z]+", f)) & set(BASLIK_KELIME):  # tam kelime ("Sandıklı", "Yenişehir" baslik degil)
        return None
    return "ilce"


def ad_temizle(etiket, tur):
    # "Merkez (Karaköse)", "Gökçeada (İmroz)": parantez oncesi asil ad
    s = re.split(r"\(", etiket)[0] if re.search(r"\w\s*\(", etiket) else etiket
    s = re.sub(r"[»•*'|!(),]", " ", s)
    # "<Il> İl Toplamı" ve OCR bozulmalari ("II", "fl", "tl", "Ü", "Il" ya da hic yok)
    s = re.sub(r"\s+\S{0,2}\s*(Toplam[ıi]?|TOPLAM[IİıÎ])\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+(Toplam[ıi]?|TOPLAM[IİıÎ])\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+(İL|IL|İl|il)$", "", s)  # "A. KARAHİSAR İL" (TOPLAMI alt satira kaymis)
    s = re.sub(r"\b(İlçesi|ilçesi|İLÇESİ|ilçe)\b", "", s)
    return " ".join(s.split()).strip(" .-—")


def _kisitla_coz(parcalar, n_once, n_parti):
    """Rakam parcalarini (sirali) n_once + n_parti + 1 sayiya bol; partiler+bagimsiz
    == muteber ve secmen >= kullanan >= muteber kisitlarini saglayan TEK cozum."""
    n = n_once + n_parti + 1
    cozum = []

    def rec(i, acc):
        if len(cozum) > 1:
            return
        if len(acc) == n:
            if i == len(parcalar):
                once, part = acc[:n_once], acc[n_once:]
                s, k, m = once[-3], once[-2], once[-1]
                if sum(part) == m and s >= k >= m:
                    cozum.append(list(acc))
            return
        if i >= len(parcalar):
            return
        if parcalar[i] == "—":
            rec(i + 1, acc + [0])
            return
        for j in range(i + 1, len(parcalar) + 1):
            grp = parcalar[i:j]
            if "—" in grp or not (1 <= len(grp[0]) <= 3) or any(len(x) != 3 for x in grp[1:]):
                break
            rec(j, acc + [int("".join(grp))])
    rec(0, [])
    return cozum[0] if len(cozum) == 1 else None


META = ("sandik", "secmen", "oyKullanan", "muteber")


def sutun_ayir(sutunlar):
    once = [c for c in sutunlar if c in META]
    partiler = [c for c in sutunlar if c not in META and c not in ("%", "Bağımsız")]
    return once, partiler


def tablo_oku(pdf, ilk, son, sutunlar):
    n = len(sutunlar)
    once, partiler = sutun_ayir(sutunlar)
    satirlar, sorunlu_sayfa, yon_kenar = [], [], {}
    filt = lambda e: satir_turu(e) in ("il", "ilce", "genel")  # noqa: E731
    bekleyen = []
    for no in list(range(ilk, son + 1)):
        pg = pdf.pages[no - 1]
        rows, kenar = die_tablo.sayfa_tablosu(pg, 180, n, filt)
        if rows is None:
            bekleyen.append(no)
            continue
        yon_kenar.setdefault(no % 2, kenar)
        satirlar += _kayitlar(rows, no, sutunlar, once, partiler)
    for no in bekleyen:  # temiz satiri olmayan sayfa: ayni yondeki sayfanin sutun kenarlari
        rows, _ = die_tablo.sayfa_tablosu(pdf.pages[no - 1], 180, n, filt, hazir_kenarlar=yon_kenar.get(no % 2))
        if rows is None:
            sorunlu_sayfa.append(no)
            continue
        for r in _kayitlar(rows, no, sutunlar, once, partiler):
            r["kenarlarBaskaSayfadan"] = True
            satirlar.append(r)
    satirlar.sort(key=lambda r: (r["sayfa"], r["y"]))
    return satirlar, sorunlu_sayfa


def _tr_baslik(s):
    """'AĞRI' -> 'Ağrı', 'İSTANBUL' -> 'İstanbul' (Turkce buyuk/kucuk harf)."""
    kucuk = str.maketrans("IİŞĞÜÇÖÂÎÛ", "ıişğüçöâîû")
    return " ".join(w[:1] + w[1:].translate(kucuk).lower() for w in s.split())


ILCE_BASLIK = re.compile(r"^([A-ZÇĞİÖŞÜÂÎÛ][A-ZÇĞİÖŞÜÂÎÛ .]+?)\s*\((Merkez|MERKEZ)\)\s*$")


def sandik_listesi_oku(pdf, ilk, son, sutunlar):
    """Ozet tablosu olmayan kitap (1964): sayfalari sirayla gez, il (sayfa
    basligi, harf aralikli) ve ilce ("AD (Merkez)" basligi) takip et; yalnizca
    "Toplam" (ilce) ve "İl Genel Toplamı" (il) satirlarini al."""
    once, partiler = sutun_ayir(sutunlar)
    n = len(sutunlar)
    satirlar, sorunlu, il, ilce, kenar = [], [], None, None, None
    for no in range(ilk, min(son, len(pdf.pages)) + 1):
        pg = pdf.pages[no - 1]
        words = pg.extract_words()
        satir = die_tablo._satirlar(words)
        if satir:
            bas = " ".join(w["text"] for w in sorted(satir[0], key=lambda w: w["x0"]))
            harfler = re.sub(r"[^A-ZÇĞİÖŞÜÂÎÛ ]", " ", bas)
            # harf aralikli il basligi: "A Ğ RI", "A M A S YA" (son iki harf bitisik olabilir)
            m = re.search(r"((?:\b[A-ZÇĞİÖŞÜÂÎÛ]{1,2}\s+){2,}[A-ZÇĞİÖŞÜÂÎÛ]{1,2}\b)", harfler)
            if m:
                yeni_il = re.sub(r"\s+", "", m.group(1))
                if yeni_il != il:
                    il, ilce = yeni_il, None
        basliklar = []
        for s_ in satir:
            t = " ".join(w["text"] for w in sorted(s_, key=lambda w: w["x0"])).strip()
            m = ILCE_BASLIK.match(t)
            if m:
                basliklar.append((s_[0]["top"], m.group(1).strip()))
        rows, k = die_tablo.sayfa_tablosu(pg, 180, n, None, hazir_kenarlar=kenar)
        if rows is None:
            sorunlu.append(no)
            continue
        kenar = k
        for etiket, vals, y, parca in rows:
            f = fold(etiket)
            onceki = [b for b in basliklar if b[0] < y]
            if onceki:
                ilce = onceki[-1][1]
            if f.endswith("GENEL TOPLAMI") or f == "IL GENEL TOPLAMI":
                tur, ad = "il", (il or "?")
            elif f == "TOPLAM" or f.endswith(" TOPLAM"):
                tur, ad = "ilce", (ilce or "?")
                if il and fold(ad) == fold(il):
                    ad = "Merkez"  # "ANTALYA (Merkez)": ilin merkez ilcesi
            else:
                continue
            v = dict(zip(sutunlar, vals))
            rec = {c: v.get(c) for c in once}
            rec["oy"] = {p_: v.get(p_) for p_ in partiler}
            rec["Bağımsız"] = v.get("Bağımsız")
            rec.update(tur=tur, adKaynakta=f"{ad} / {etiket}", ad=_tr_baslik(ad) if ad.isupper() else ad,
                       sayfa=no, y=round(y, 1), _parca=parca, _yuzde={})
            satirlar.append(rec)
    # sayfa sirasinda "İl Genel Toplamı" ilin SONUNDA; grupla() il satirini basta bekliyor
    out, bekleyen = [], []
    for r in satirlar:
        if r["tur"] == "ilce":
            bekleyen.append(r)
        else:
            out.append(r)
            out += bekleyen
            bekleyen = []
    return out, sorunlu


def sira_ile_adlandir(iller, ref_secim="1965"):
    """Sandik listesi kitabinda (1964) ilce basliklari guvenilir degil. DIE
    ilceleri 'Merkez once, sonra alfabetik' basar; ilin 'Toplam' satiri sayisi
    ayni ilin referans (TUIK 1965) ilce sayisina esitse adlar sirayla atanir.
    Kabul: basligi okunabilmis satirlarin >= %80'i ayni sirayla uyusmali.
    Il: okunabilen ilce adlarinin cogunlukla isaret ettigi plaka."""
    ref = json.loads((OUT / "genel" / f"{ref_secim}.json").read_text(encoding="utf-8"))
    by_plaka = collections.defaultdict(list)
    for c in ref["cevreler"]:
        by_plaka[c["plaka"]] += [i["ad"] for i in c["ilceler"]]
    ad_plaka = collections.defaultdict(set)
    for pl, adlar in by_plaka.items():
        for a in adlar:
            if fold(a) != "MERKEZ":
                ad_plaka[fold(a)].add(pl)
    il_ad = {c["plaka"]: c["cevre"] for c in ref["cevreler"]}
    for il in iller:
        # il kimligi ilce adlarindan
        oy = collections.Counter(next(iter(ad_plaka[fold(r["ad"])])) for r in il["ilceler"]
                                 if len(ad_plaka.get(fold(r["ad"]), ())) == 1)
        if oy:
            pl = oy.most_common(1)[0][0]
            if fold(il_ad[pl]) != fold(il["ad"]):
                il["adOcr"] = il["ad"]
                il["ad"] = _tr_baslik(il_ad[pl]) if il_ad[pl].isupper() else il_ad[pl]
                il["ilIlcelerdenBulundu"] = True
        else:
            pl = None
        adlar = by_plaka.get(pl) or []
        sira = ["Merkez"] + [a for a in adlar if fold(a) != "MERKEZ"]
        if pl and len(sira) == len(il["ilceler"]):
            okunan = [(r["ad"], a) for r, a in zip(il["ilceler"], sira) if r["ad"] != "?"]
            uyan = sum(1 for x, a in okunan if fold(x) == fold(a))
            if not okunan or uyan / len(okunan) >= 0.8:
                for r, a in zip(il["ilceler"], sira):
                    if fold(r["ad"]) != fold(a):
                        r["adBaslikta"] = r["ad"]
                    r["ad"] = a
                    r["adSiradan"] = True
            else:
                il["siraUyusmadi"] = f"{uyan}/{len(okunan)}"
        elif pl:
            il["ilceSayisiFarkli"] = f"kitapta {len(il['ilceler'])}, referansta {len(sira)}"


def _sayilara_bol(parca, n):
    """Token dizisini (rakam gruplari ve '—') n sayiya bolmenin TUM yollari."""
    if n == 0:
        if not parca:
            yield []
        return
    if not parca:
        return
    if parca[0] == "—":
        for rest in _sayilara_bol(parca[1:], n - 1):
            yield [0] + rest
        return
    if len(parca[0]) > 3:  # OCR bosluksuz birlestirmis ("181147"): tek basina bir sayi
        for rest in _sayilara_bol(parca[1:], n - 1):
            yield [int(parca[0])] + rest
        return
    for j in range(1, len(parca) + 1):
        grp = parca[:j]
        if "—" in grp or not (1 <= len(grp[0]) <= 3) or any(len(x) != 3 for x in grp[1:]):
            break
        for rest in _sayilara_bol(parca[j:], n - 1):
            yield [int("".join(grp))] + rest


def mv_capali_oku(pdf, ilk, son, partiler, mv_secim="1961"):
    """1961: MV ve Senato ayni satirda. Satirin ilk sayisi (secmen) projedeki TUIK
    MV il/ilce secmen sayisiyla eslenerek satirin KIMLIGI bulunur; MV degerleri
    bilindigi icin o tokenlar tuketilir, kalan tokenlar Senato
    (kullanan, muteber, partiler..., bagimsiz) olarak partiler+bag=muteber
    kisitiyla TEK anlamli bolunur."""
    # capa: TUIK kaynak katmani (DIE'nin kendi il ve ilce degerleri; YSK il satirlari DEGIL -
    # DIE il toplamlari YSK ilanindan farkli olabilir)
    src = json.loads((OUT / "genel" / f"{mv_secim}.json").read_text(encoding="utf-8"))
    esl = src["partiEslemesi"]
    mv_parti = ["AP", "CHP", "CKMP", "YTP61"]

    def ref_kaydi(x, plaka, ad):
        oy = collections.Counter()
        for h, v in x["partiler"].items():
            oy[esl[h]] += v or 0
        return {"plaka": plaka, "ad": ad, "secmen": x["secmen"], "gecerliOy": x["gecerliOy"],
                "oy": {k: {"oy": v} for k, v in oy.items()}}
    il_by_secmen, ilce_by_secmen = {}, collections.defaultdict(list)
    for c in src["cevreler"]:
        il_by_secmen[c["secmen"]] = ref_kaydi(c, c["plaka"], c["cevre"])
        for i in c["ilceler"]:
            ilce_by_secmen[i["secmen"]].append(ref_kaydi(i, c["plaka"], i["ad"]))
    kayitlar, sorunlu = [], []
    for no in range(ilk, son + 1):
        pg = pdf.pages[no - 1]
        for s_ in die_tablo._satirlar(pg.extract_words()):
            parca = ["—" if t[3] == "tire" else t[0] for t in die_tablo._tokenler(s_, 0) if t[3] != "yuzde"]
            while parca and parca[0] == "—":  # "Toplam - Total" etiketindeki tire
                parca = parca[1:]
            if len(parca) < 8:
                continue
            etiket = " ".join(w["text"] for w in sorted(s_, key=lambda w: w["x0"])
                              if re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", w["text"]))
            # kimlik: ilk 1-3 token secmen olabilir
            kimlik = None
            for j in (1, 2, 3):
                if j > len(parca) or "—" in parca[:j] or (j > 1 and not (1 <= len(parca[0]) <= 3)) or any(len(x) != 3 for x in parca[1:j]):
                    continue
                v = int("".join(parca[:j]))
                if v in il_by_secmen:
                    kimlik = ("il", il_by_secmen[v], j)
                elif len(ilce_by_secmen.get(v, [])) == 1:
                    kimlik = ("ilce", ilce_by_secmen[v][0], j)
                if kimlik:
                    break
            if not kimlik:
                continue
            tur, ref, j = kimlik
            # MV kisminin kalan degerleri: kullanan (katilimdan), gecerli, partiler (+ bagimsiz/diger)
            mvp = [ref["oy"].get(p, {}).get("oy") or 0 for p in mv_parti]
            mv_bag = sum((v.get("oy") or 0) for k, v in ref["oy"].items() if k not in mv_parti)
            kalan = parca[j:]
            senato, senato_fark = None, 0
            # MV: kullanan, gecerli, AP, CHP, CKMP, YTP, bagimsiz = 7 sayi; kullanan bilinmiyorsa serbest
            for i in range(1, len(kalan)):
                # MV: kullanan, gecerli, 4 parti [+ bagimsiz; bossa tiresiz hic basilmamis]
                on = list(_sayilara_bol(kalan[:i], 7)) + list(_sayilara_bol(kalan[:i], 6))
                if not any(o[1] == ref["gecerliOy"] and o[2:6] == mvp for o in on):
                    continue
                n_sen = 3 + len(partiler)
                adaylar = [c for c in _sayilara_bol(kalan[i:], n_sen) if c[0] >= c[1] > 0]
                adaylar += [c + [0] for c in _sayilara_bol(kalan[i:], n_sen - 1) if c[0] >= c[1] > 0]
                tam = [c for c in adaylar if sum(c[2:]) == c[1]]
                if len(tam) == 1:
                    senato = tam[0]
                    break
                if not tam and adaylar:
                    # kaynakta kucuk toplam farki olabilir: farki en kucuk TEK bolunme, fark kucukse
                    en = min(abs(sum(c[2:]) - c[1]) for c in adaylar)
                    yakin = [c for c in adaylar if abs(sum(c[2:]) - c[1]) == en]
                    if len(yakin) == 1 and en <= max(10, yakin[0][1] * 0.005):
                        senato = yakin[0]
                        senato_fark = en
                        break
            rec = {"tur": tur, "plaka": ref["plaka"], "ad": ref["ad"], "adKaynakta": etiket, "sayfa": no,
                   "y": round(s_[0]["top"], 1), "secmen": ref["secmen"], "mvKimlik": True}
            if senato:
                rec.update(oyKullanan=senato[0], muteber=senato[1],
                           oy=dict(zip(partiler, senato[2:2 + len(partiler)])), **{"Bağımsız": senato[-1]})
                if senato_fark:
                    rec["tutarsiz"] = f"partiler+bagimsiz muteberden {senato_fark} oy farkli (kaynakta)"
            else:
                rec.update(oyKullanan=None, muteber=None, oy={p: None for p in partiler}, **{"Bağımsız": None},
                           tutarsiz="senato kismi tek anlamli bolunemedi")
            kayitlar.append(rec)
    # il gruplari: plaka ile (sira bagimsiz)
    iller = []
    by = collections.defaultdict(list)
    for r in kayitlar:
        by[r["plaka"]].append(r)
    for pl, rs in sorted(by.items()):
        il = next((r for r in rs if r["tur"] == "il"), None)
        if il is None:
            sorunlu.append(f"plaka {pl}: il toplami satiri bulunamadi")
            continue
        iller.append(dict(il, ilceler=[r for r in rs if r["tur"] == "ilce"]))
    return iller, sorunlu


def toplam_sonda_grupla(satirlar):
    """Il toplami ilcelerden SONRA gelen tablo (1961): blok = ilceler + 'Toplam';
    il adi bloktaki '<IL> (Mer.)' satirindan, o satir 'Merkez' ilcesi."""
    iller, blok = [], []
    for r in satirlar:
        if r["tur"] != "il":
            blok.append(r)
            continue
        merkez = next((b for b in blok if re.search(r"\((Mer|Merkez|M)\.?\)", b["adKaynakta"])), None)
        ad = re.split(r"\s*\(", merkez["adKaynakta"])[0].strip() if merkez else "?"
        if merkez:
            merkez["ad"] = "Merkez"
        il = dict(r, ad=_tr_baslik(ad) if ad.isupper() else ad, ilceler=blok)
        iller.append(il)
        blok = []
    return iller


def _hizala(L, R):
    """Sirayi koruyan hizalama: sol ve sag satirlar y farkina gore eslenir,
    her iki taraftan satir atlanabilir. Ofset: ilk satirlarin farkinin medyani."""
    ofs = sorted(R[k][2] - L[k][2] for k in range(min(len(L), len(R), 5)))[min(len(L), len(R), 5) // 2]
    INF = float("inf")
    n, m = len(L), len(R)
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    geri = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    ATLA = 6.0
    for i in range(n + 1):
        for j in range(m + 1):
            if dp[i][j] == INF:
                continue
            if i < n and j < m:
                c = dp[i][j] + abs(R[j][2] - ofs - L[i][2])
                if c < dp[i + 1][j + 1]:
                    dp[i + 1][j + 1], geri[i + 1][j + 1] = c, (i, j, "e")
            if i < n and dp[i][j] + ATLA < dp[i + 1][j]:
                dp[i + 1][j], geri[i + 1][j] = dp[i][j] + ATLA, (i, j, "l")
            if j < m and dp[i][j] + ATLA < dp[i][j + 1]:
                dp[i][j + 1], geri[i][j + 1] = dp[i][j] + ATLA, (i, j, "r")
    out, i, j = [], n, m
    while (i, j) != (0, 0):
        pi, pj, t = geri[i][j]
        if t == "e":
            out.append((L[pi], R[pj]))
        i, j = pi, pj
    return list(reversed(out))


def cift_oku(pdf, ilk, son, sol, sag):
    """Karsilikli sayfa tablosu: sol sayfalar ilk, ilk+2, ... ; sag = sol+1.
    Satirlar sirayla eslenir (sag sayfa birkac puan kayik basildigi icin y ile
    degil); satir sayilari tutmazsa en yakin y (medyan ofsetle) kullanilir."""
    sutunlar = sol + sag
    once, partiler = sutun_ayir(sutunlar)
    filt = lambda e: satir_turu(e) in ("il", "ilce", "genel")  # noqa: E731
    satirlar, sorunlu = [], []
    kenar_sol = kenar_sag = None
    for no in range(ilk, son + 1, 2):
        L, kl = die_tablo.sayfa_tablosu(pdf.pages[no - 1], 180, len(sol), filt)
        R, kr = die_tablo.sayfa_tablosu(pdf.pages[no], 180, len(sag), None, etiketsiz=True)
        if L is not None:
            kenar_sol = kenar_sol or kl
        if R is not None:
            kenar_sag = kenar_sag or kr
        if L is None and kenar_sol:
            L, _ = die_tablo.sayfa_tablosu(pdf.pages[no - 1], 180, len(sol), filt, hazir_kenarlar=kenar_sol)
        if R is None and kenar_sag:
            R, _ = die_tablo.sayfa_tablosu(pdf.pages[no], 180, len(sag), None, hazir_kenarlar=kenar_sag, etiketsiz=True)
        if L is None or R is None:
            sorunlu.append(no)
            continue
        if len(L) == len(R):
            eslesme = list(zip(L, R))
        else:
            eslesme = _hizala(L, R)
            sorunlu.append(f"{no}: satir sayisi sol {len(L)} / sag {len(R)} (sirali hizalama)")
        rows = [(l[0], l[1] + r[1], l[2], None) for l, r in eslesme]
        satirlar += _kayitlar(rows, no, sutunlar, once, partiler)
    return satirlar, sorunlu


def _kayitlar(rows, no, sutunlar, once, partiler):
    out = []
    yuzdeli = "%" in sutunlar
    for etiket, vals, y, parca in rows:
        tur = satir_turu(etiket)
        if tur == "genel":
            continue
        v, yuzde, onceki = {}, {}, None
        for c, x in zip(sutunlar, vals):
            if c == "%":
                # yalnizca OCR'in ondalikli okudugu yuzdeler guvenilir ("0 7" gibi bozuklar atilir)
                if onceki and isinstance(x, float):
                    yuzde[onceki] = x
            else:
                v[c], onceki = x, c
        rec = {c: v.get(c) for c in once}
        rec["oy"] = {p_: v.get(p_) for p_ in partiler}
        rec["Bağımsız"] = v.get("Bağımsız")
        rec.update(tur=tur, adKaynakta=etiket, ad=ad_temizle(etiket, tur), sayfa=no, y=round(y, 1),
                   _parca=None if yuzdeli else parca, _yuzde=yuzde)
        out.append(rec)
    return out


def _yuzde_duzelt(r, partiler, yuzde):
    """Satir ici toplam tutmuyorsa basili yuzdelerle tek-deger OCR duzeltmesi.
    Kabul kosulu: IKI bagimsiz kisit (toplam = muteber VE yuzde tutarliligi)
    ayni anda saglanmali; aksi halde dokunulmaz."""
    m = r.get("muteber")
    adlar = partiler + ["Bağımsız"]
    deger = {p: (r["oy"].get(p) if p != "Bağımsız" else r["Bağımsız"]) for p in adlar}
    if not m or any(v is None for v in deger.values()):
        return None
    def uyar(v, pct, tab):
        return abs(v * 100 / tab - pct) <= 0.11
    # (a) muteber hatali: tum yuzdeler parti toplamina gore tutarli
    top = sum(deger.values())
    kontrollu = [p for p in adlar if p in yuzde and deger[p]]
    if len(kontrollu) >= 2 and all(uyar(deger[p], yuzde[p], top) for p in kontrollu) and \
            not all(uyar(deger[p], yuzde[p], m) for p in kontrollu):
        r["ocrDuzeltme"] = {"alan": "muteber", "okunan": m, "duzeltilen": top}
        r["muteber"] = top
        return True
    # (b) tek parti degeri hatali
    uymayan = [p for p in kontrollu if not uyar(deger[p], yuzde[p], m)]
    if len(uymayan) == 1:
        p = uymayan[0]
        yeni = m - (top - deger[p])
        if yeni >= 0 and uyar(yeni, yuzde[p], m):
            r["ocrDuzeltme"] = {"alan": p, "okunan": deger[p], "duzeltilen": yeni}
            if p == "Bağımsız":
                r["Bağımsız"] = yeni
            else:
                r["oy"][p] = yeni
            return True
    return None


def dogrula_satir(r, partiler, sutun_once):
    yuzde = r.pop("_yuzde", {}) or {}
    parca = r.pop("_parca")  # None: yuzde sutunlu tablo, kisitla cozum uygulanmaz
    part = [r["oy"][p] for p in partiler] + [r["Bağımsız"]]
    m = r.get("muteber")
    if m is not None and None not in r.values() and None not in part and sum(part) == m:
        return
    # bos (tiresiz) hucre: diger degerler muteberi tutuyorsa 0
    if m is not None and all(r.get(k) is not None for k in sutun_once) and sum(x or 0 for x in part) == m:
        for p in partiler:
            if r["oy"][p] is None:
                r["oy"][p] = 0
        if r["Bağımsız"] is None:
            r["Bağımsız"] = 0
        r["bosHucre0"] = True
        return
    if yuzde and _yuzde_duzelt(r, partiler, yuzde):
        return
    coz = _kisitla_coz(parca, len(sutun_once), len(partiler)) if parca else None
    if coz:
        for k, v in zip(sutun_once, coz):
            r[k] = v
        r["oy"] = dict(zip(partiler, coz[len(sutun_once):-1]))
        r["Bağımsız"] = coz[-1]
        r["kisitlaCozuldu"] = True
        return
    r["tutarsiz"] = f"partiler+bagimsiz={sum(x or 0 for x in part)} != muteber={m}"


def grupla(satirlar):
    iller, cur = [], None
    for r in satirlar:
        if r["tur"] == "il":
            cur = dict(r, ilceler=[])
            iller.append(cur)
        elif cur is not None:
            cur["ilceler"].append(r)
    return iller


def dikey_kontrol(iller, partiler, sutun_once):
    out = []
    for il in iller:
        for f in sutun_once + ["Bağımsız"]:
            s = sum((i.get(f) or 0) for i in il["ilceler"])
            if il.get(f) is not None and s != il[f]:
                out.append({"il": il["ad"], "alan": f, "ilDegeri": il[f], "ilceToplami": s})
        for p in partiler:
            s = sum((i["oy"].get(p) or 0) for i in il["ilceler"])
            if il["oy"].get(p) is not None and s != il["oy"][p]:
                out.append({"il": il["ad"], "alan": p, "ilDegeri": il["oy"][p], "ilceToplami": s})
    return out


ESDEGER = {"BP69": "TBP73", "GP": "CGP"}  # Wikipedia anahtari -> bu dosyadaki anahtar (ayni parti)


def wiki_kontrol(iller, secim):
    p = ROOT / "data" / "kaynaklar" / "wikipedia" / "senato" / f"{secim}.json"
    if not p.exists():
        return None
    w = json.loads(p.read_text(encoding="utf-8"))
    wiki = {}
    for k in w["kayitlar"]:
        if k["tur"] == "il_sonuc":
            c = collections.Counter()
            for a in k.get("adaylar") or k.get("partiler") or []:
                c[ESDEGER.get(a["parti"], a["parti"]) or "?"] += a["oy"]
            wiki[fold(k["il"])] = c
    tutan, farkli = 0, []
    for il in iller:
        c = wiki.get(fold(il["ad"]))
        if c is None:
            continue
        bizim = collections.Counter({k: v for k, v in il["oy"].items() if v})
        if il.get("Bağımsız"):
            bizim["Bağımsız"] = il["Bağımsız"]
        if +bizim == +c:
            tutan += 1
        else:
            farkli.append({"il": il["ad"], "fark": {k: (bizim.get(k, 0), c.get(k, 0)) for k in set(bizim) | set(c) if bizim.get(k, 0) != c.get(k, 0)}})
    return {"tutan": tutan, "farkli": farkli}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", required=True)
    ap.add_argument("secimler", nargs="*")
    a = ap.parse_args()
    for kitap_key, k in KITAPLAR.items():
        if a.secimler and kitap_key not in a.secimler:
            continue
        pdf_p = pdf_yolu(k["demirbas"], a.pdf_dir)
        pdf = die_tablo.ac(pdf_p)
        isler = [(ilk, son, secim, sutunlar, None) for ilk, son, secim, sutunlar in k.get("tablolar", [])]
        isler += [(ilk, son, secim, sol + sag, (sol, sag)) for ilk, son, secim, sol, sag in k.get("cift", [])]
        isler += [(ilk, son, secim, sutunlar, "sandik") for ilk, son, secim, sutunlar in k.get("sandikListesi", [])]
        isler += [(ilk, son, secim, sutunlar, "mv") for ilk, son, secim, sutunlar in k.get("mvCapali", [])]
        for ilk, son, secim, sutunlar, cift in isler:
            sutun_once, partiler = sutun_ayir(sutunlar)
            if cift == "mv":
                iller_mv, sorunlu = mv_capali_oku(pdf, ilk, son, partiler)
                satirlar = [r for il in iller_mv for r in [il] + il["ilceler"]]
            elif cift == "sandik":
                satirlar, sorunlu = sandik_listesi_oku(pdf, ilk, son, sutunlar)
            elif cift:
                satirlar, sorunlu = cift_oku(pdf, ilk, son, *cift)
                son = son + 1
            else:
                satirlar, sorunlu = tablo_oku(pdf, ilk, son, sutunlar)
            for r in satirlar:
                if not r.get("mvKimlik"):
                    dogrula_satir(r, partiler, sutun_once)
            iller = iller_mv if cift == "mv" else grupla(satirlar)
            if cift == "sandik":
                sira_ile_adlandir(iller)
            for il in iller:
                sayac = collections.Counter(r["ad"] for r in il["ilceler"])
                for r in il["ilceler"]:
                    # sandik listesinde ad basliktan gelir ve kayabilir: yalnizca sirayla
                    # dogrulanan ya da ilde tekil olarak okunan adlar guvenli
                    r["adGuvenli"] = (cift != "sandik") or bool(r.get("adSiradan")) or (r["ad"] != "?" and sayac[r["ad"]] == 1)
            dik = dikey_kontrol(iller, partiler, sutun_once)
            # dikey kontrolu tutmayan il/alanlar: degerler "dogrulanamadi"
            for x in dik:
                for il in iller:
                    if il["ad"] == x["il"]:
                        il.setdefault("dogrulanamayanAlanlar", []).append(x["alan"])
            wk = wiki_kontrol(iller, secim) if secim.endswith("senato") else None
            # sayfa metinleri (depoya giren ham iz)
            (METIN / k["demirbas"]).mkdir(parents=True, exist_ok=True)
            sayfa_listesi = sorted({r["sayfa"] for r in satirlar}) if cift == "sandik" else range(ilk, son + 1)
            for no in sayfa_listesi:
                (METIN / k["demirbas"] / f"{no:04d}.txt").write_text(pdf.pages[no - 1].extract_text() or "", encoding="utf-8")
            veri = {
                "secim": secim, "kaynak": "tuik", "yayin": k["baslik"],
                "yayinUrl": f"https://kutuphane.tuik.gov.tr/pdf/{k['demirbas']}.pdf",
                "pdfSha256": k["sha256"] or sha256(pdf_p), "sayfalar": [ilk, son],
                "metinKlasoru": str((METIN / k["demirbas"]).relative_to(ROOT)),
                "sutunlar": sutunlar, "partiSutunlari": partiler,
                "ozet": {"il": len(iller), "ilce": sum(len(i["ilceler"]) for i in iller),
                         "kisitlaCozulen": sum(1 for r in satirlar if r.get("kisitlaCozuldu")),
                         "ocrDuzeltilen": sum(1 for r in satirlar if r.get("ocrDuzeltme")),
                         "satirIciTutarsiz": sum(1 for r in satirlar if r.get("tutarsiz")),
                         "ilceToplamiIlToplamiTutmayan": len(dik), "okunamayanSayfa": sorunlu},
                "wikipediaIlKarsilastirmasi": wk,
                "ilceToplamiTutmayan": dik, "iller": iller,
            }
            alt = "senato" if secim.endswith("senato") else "genel"
            (OUT / alt).mkdir(parents=True, exist_ok=True)
            (OUT / alt / f"{secim}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
            print(secim, veri["ozet"], "wikipedia:", (wk or {}).get("tutan"), "tutan /", len((wk or {}).get("farkli", [])), "farkli")


if __name__ == "__main__":
    main()
