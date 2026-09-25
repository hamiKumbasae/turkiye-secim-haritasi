"""
DIE Mahalli Idareler Secimi Sonuclari 1994 (0013623) ve 1999 (0014361)
taranmis kitaplari -> kaynak katmani, ocr_tablo.py'nin dogrulamali okumasiyla:

  data/kaynaklar/tuik/yerel/<secim>/<tablo>.json
  data/kaynaklar/tuik/yerel/<secim>/dogrulama_raporu.json

Kimlik (hangi belediye/ilce) - TAHMIN YOK, kanitla:
  YSK'nin il bazli resmi arsivi (data/raw/ysk/mahalli-1994-1999-2004/<yil>/
  BelediyeBaskanligi|Buyuksehir) her belediyeyi adiyla ve sandik/secmen
  sayisiyla veriyor. Bir belediyenin secmeni baskanlik, meclis ve (sehir
  satiri olarak) IGM tablolarinda aynidir. DIE satiri, (sandik, secmen) cifti
  YSK'de TEK bir belediyeye birebir esitse o belediyedir (`kimlik.yontem =
  "ysk_sandik_secmen"`). Esit degilse ad OCR'dan (`adKaynakta`), kimlik
  `cozulemedi` olarak kalir.

Ground truth: baskanlik tablosu YSK arsivinde de var. Ayni belediyede DIE'nin
okunan her alani YSK degeriyle karsilastirilir; `dogrulama_raporu.json` hangi
satir durumunda (tutarli, toplamTutarli, ...) OCR okumasinin YSK ile ne kadar
birebir oldugunu verir. Meclis/IGM tablolari icin guven bu olcume dayanir.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/extract_mahalli_ocr.py 1994yerel [tablo ...]
"""
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE.parent / "yerel_1994_1999_2004"))
import die_tablo  # noqa: E402
import ocr_tablo  # noqa: E402
from common.turkish_text import fold  # noqa: E402

ROOT = HERE.parent.parent.parent
RAW = ROOT / "data" / "raw" / "tuik" / "mahalli-kitap"
YSK = ROOT / "data" / "raw" / "ysk" / "mahalli-1994-1999-2004"
OUT = ROOT / "data" / "kaynaklar" / "tuik" / "yerel"
ONCU = ["sandik", "secmen", "oyKullanan", "gecerliOy"]

P94_SOL = ["ANAP", "BBP", "CHP", "DP"]
P94_SAG = ["DSP", "DYP", "İP", "MP92", "MHP", "RP", "SBP", "SHP", "YDP", "Bağımsız"]
KITAPLAR = {
    "1994yerel": {
        "demirbas": "0013623", "yil": "1994", "yayin": "DİE, Mahalli İdareler Seçimi Sonuçları 27.3.1994",
        "sol": ONCU + P94_SOL, "sag": P94_SAG, "partiler": P94_SOL + P94_SAG,
        "tablolar": {"il_genel_meclisi": (30, 251), "buyuksehir": (252, 261),
                     "belediye_baskanligi": (262, 473), "belediye_meclisi": (474, 685)},
    },
}
P99_SOL = ["ANAP", "BP", "BBP", "CHP", "DP", "DBP99"]
P99_SAG = ["DSP", "DEMTP", "DYP", "DEHAP", "DEPAR", "EMEP", "FP", "HADEP", "İP", "LDP", "MP92", "MHP", "ÖDP", "SİP", "YDP",
           "Bağımsız"]
KITAPLAR["1999yerel"] = {
    "demirbas": "0014361", "yil": "1999", "yayin": "DİE, Mahalli İdareler Seçimi Sonuçları 18.4.1999",
    "sol": ONCU + P99_SOL, "sag": P99_SAG, "partiler": P99_SOL + P99_SAG,
    # sutun sablonu: duzenli sayfalarin medyani + sayfa ofseti. (Denendi ve
    # YSK olcumuyle reddedildi: sayfa basliklarinin x'i - birkac px sapip
    # degeri komsu sutuna itiyor; sayi-sonu histogrami - seyrek sutunlarda gurultu.)
    # buyuksehir tablosunda DSP sol yuzde (7 + 15 sutun)
    "tabloSutun": {"buyuksehir": {"sol": ONCU + P99_SOL + ["DSP"], "sag": P99_SAG[1:]}},
    "tablolar": {"il_genel_meclisi": (38, 239), "buyuksehir": (242, 251),
                 "belediye_baskanligi": (254, 473), "belediye_meclisi": (476, 695)},
}
ACIKLAMA = {
    "il_genel_meclisi": "İl genel meclisi üyeleri seçimi sonuçları, il ve ilçelere göre (şehir/köy kırılımıyla)",
    "buyuksehir": "Büyükşehir belediye başkanlığı seçimi sonuçları, ilçe merkez ve alt kademe belediyelerine göre",
    "belediye_baskanligi": "Belediye başkanlığı seçimi sonuçları, belediyelere göre",
    "belediye_meclisi": "Belediye meclisi üyeleri seçimi sonuçları, belediyelere göre",
}
IL_AD = {fold(v["il_ADI"]).replace(" ", ""): int(k) for k, v in json.loads(
    (ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text(encoding="utf-8")).items()}
IL_AD.update({"ICEL": 33, "AFYON": 3, "SURFA": 63, "KMARAS": 46, "URFA": 63, "MARAS": 46})
from party_map import STATIC_MAP as YSK_PARTI  # noqa: E402  (YSK PDF basliklari -> parti anahtari)


def _sayi(s):
    s = (s or "").strip().replace(".", "")
    return int(s) if s.isdigit() else None


def ysk_referans(yil):
    """YSK il PDF'lerinden belediye listesi: [{plaka, ilce, belde, tip, sandik, secmen, kullanan, gecerli, oy}]."""
    import parse_ilce_belde as pib
    esl = json.loads((YSK / "il_dosya_eslemesi.json").read_text(encoding="utf-8"))[yil]
    out = []
    for il, e in esl.items():
        klasor = "Buyuksehir" if e["type"] != "belediye" else "BelediyeBaskanligi"
        f = YSK / yil / klasor / f"{e['file']}.pdf"
        if not f.exists():
            continue
        header, rows = pib.extract_rows(f)
        h = [(c or "").replace("\n", " ").strip() for c in header]
        i_s = next(i for i, c in enumerate(h) if c.startswith("Sandık"))
        partiler = [YSK_PARTI.get(c.upper(), YSK_PARTI.get(c, c)) for c in h[i_s + 4:]]
        ilce = None
        adsiz = 0
        for r in rows:
            if not r or len(r) < len(h) or _sayi(r[i_s + 1]) is None:
                continue
            if klasor == "BelediyeBaskanligi" and not any((x or "").strip() for x in r[:i_s]):
                adsiz += 1
                if adsiz == 2:  # 1. Turkiye, 2. il toplami (tum belediyeler)
                    out.append({"plaka": e["plaka"], "il": il, "ilce": None, "ad": il, "tip": "il", "yaris": "belediye",
                                "dosya": str(f.relative_to(ROOT)), "sandik": _sayi(r[i_s]), "secmen": _sayi(r[i_s + 1]),
                                "kullanan": _sayi(r[i_s + 2]), "gecerli": _sayi(r[i_s + 3]), "oy": {}})
                continue
            if klasor == "BelediyeBaskanligi":
                if (r[0] or "").strip():
                    ilce = r[0].strip()
                ad, tip = ((r[1] or "").strip(), "belde") if (r[1] or "").strip() else (ilce, "ilce")
            else:
                ad, tip = (r[0] or "").strip(), "ilce"
                ilce = ad
            if not ad:
                continue  # Turkiye / il toplami
            out.append({"plaka": e["plaka"], "il": il, "ilce": ilce, "ad": ad, "tip": tip, "dosya": str(f.relative_to(ROOT)),
                        "yaris": "buyuksehir" if klasor == "Buyuksehir" else "belediye",
                        "sandik": _sayi(r[i_s]), "secmen": _sayi(r[i_s + 1]), "kullanan": _sayi(r[i_s + 2]),
                        "gecerli": _sayi(r[i_s + 3]),
                        "oy": {p: _sayi(x) for p, x in zip(partiler, r[i_s + 4:]) if _sayi(x)}})
    return out


def kimlik(r, idx, plaka_baglam, gevsek=False):
    """(sandik, secmen) YSK'de bir belediyeye birebir esit VE bu belediye
    baglamdaki ilde VE en az bir baska alan (oy kullanan ya da gecerli oy)
    da birebir esitse o belediyedir. Kucuk beldelerde (sandik, secmen) ciftleri
    iller arasi cakisabildiginden (1994 Adana beldeleri <-> baska il beldeleri)
    tek basina yeterli sayilmaz."""
    v = r["v"]
    aday = [a for a in idx.get((v.get("sandik"), v.get("secmen")), [])
            if (plaka_baglam is None or a["plaka"] == plaka_baglam)
            and (gevsek or v.get("oyKullanan") == a["kullanan"] or v.get("gecerliOy") == a["gecerli"])]
    if gevsek:
        # IGM sehir satiri: oy kullanan / gecerli baska yarisin; yalnizca il
        # baglaminda (sandik, secmen) ciftinin TEKligi
        return (aday[0], "ysk_sandik_secmen_il_icinde") if len(aday) == 1 and plaka_baglam else (None, "cozulemedi")
    if len(aday) == 1:
        return aday[0], "ysk_sandik_secmen+kullanan|gecerli"
    if not aday and plaka_baglam:
        # buyuksehir ilcesi: YSK'de yalnizca BB yarisinin ilce kirilimi var; secmen
        # ayni, oy kullanan/gecerli baska yarisin -> il icinde (sandik, secmen) tekligi
        bb = [a for a in idx.get((v.get("sandik"), v.get("secmen")), [])
              if a["plaka"] == plaka_baglam and a["yaris"] == "buyuksehir"]
        if len(bb) == 1:
            return bb[0], "ysk_bb_ilce_sandik_secmen_il_icinde"
    if not aday:
        # il baglami kacmis olabilir (il satirinin adi OCR'da yok): baglamdan
        # bagimsiz, ama DORT alan birden (sandik, secmen, oy kullanan, gecerli) esitse
        dort = [a for a in idx.get((v.get("sandik"), v.get("secmen")), [])
                if v.get("oyKullanan") == a["kullanan"] and v.get("gecerliOy") == a["gecerli"]]
        if len(dort) == 1:
            return dort[0], "ysk_dort_alan"
    if len(aday) > 1:
        e = fold(r["etiket"]).replace(" ", "")
        tek = [a for a in aday if fold(a["ad"]).replace(" ", "") == e]
        if len(tek) == 1:
            return tek[0], "ysk_sandik_secmen+ad"
    return None, "cozulemedi"


def karsilastir(r, ref, partiler):
    """Okunan her alan YSK ile ayni mi (ground truth olcumu)."""
    v = r["v"]
    esit, fark = [], []
    for a, b in (("sandik", "sandik"), ("secmen", "secmen"), ("oyKullanan", "kullanan"), ("gecerliOy", "gecerli")):
        if v.get(a) is not None:
            (esit if v[a] == ref[b] else fark).append(a)
    for p in partiler:
        if v.get(p) is not None:
            (esit if (v[p] or 0) == ref["oy"].get(p, 0) else fark).append("oy." + p)
    return esit, fark


def kardes_kimlik(kayit, bask_yolu):
    """Meclis tablosu baskanlik tablosuyla ayni belediyeleri ayni sirada verir;
    (sandik, secmen) esit olan satirlar sirali hizalanir, kimlik oradan alinir."""
    if not bask_yolu.exists():
        return
    B = [b for b in json.loads(bask_yolu.read_text(encoding="utf-8"))["satirlar"] if b["tip"] != "turkiye"]
    j = 0
    for k in kayit:
        if k["tip"] == "turkiye":
            continue
        for jj in range(j, min(j + 25, len(B))):
            b = B[jj]
            if (b["sandik"], b["secmen"]) == (k["sandik"], k["secmen"]) and k["secmen"]:
                if b["kimlik"]["yontem"] != "cozulemedi" or b["tip"] == "il":
                    if k["kimlik"]["yontem"] == "cozulemedi" or (k["ad"] == b["ad"]):
                        k.update(tip=b["tip"], plaka=b["plaka"], ad=b["ad"], ilce=b["ilce"],
                                 kimlik={"yontem": "baskanlik_tablosu_sira+sandik_secmen", **{x: y for x, y in b["kimlik"].items() if x == "ysk"}})
                elif k["kimlik"]["yontem"] == "cozulemedi":
                    k.update(plaka=b["plaka"], adKaynakta=k["adKaynakta"] or b["adKaynakta"],
                             kimlik={"yontem": "baskanlik_tablosu_sira+sandik_secmen (ad yalnız OCR)"})
                j = jj + 1
                break


def igm_yapisi(kayit, idx):
    """IGM: her ilce/il satirinin altinda sehir + koy satirlari. Etiketler OCR'da
    kaybolabildiginden yapi SAYIDAN kurulur: X.sandik = A.sandik + B.sandik ve
    X.secmen = A.secmen + B.secmen ise A sehir, B koy. Sehir satiri ilce merkezi
    belediyesidir; (sandik, secmen) il icinde YSK'de tekse ilce kimligi oradan."""
    for i in range(len(kayit) - 2):
        a, b, c = kayit[i:i + 3]
        if all(isinstance(x.get(f), int) for x in (a, b, c) for f in ("sandik", "secmen")) \
                and a["sandik"] == b["sandik"] + c["sandik"] and a["secmen"] == b["secmen"] + c["secmen"]:
            if a["tip"] not in ("il", "turkiye"):
                a["tip"] = "ilce"
            b["tip"], c["tip"] = "sehir", "koy"
            for x in (b, c):
                x["yapi"] = "ust satırın şehir+köy toplamı (sandık ve seçmen)"
            if a["tip"] == "ilce" and a["kimlik"]["yontem"] == "cozulemedi":
                ref_r, yontem = kimlik({"v": {"sandik": b["sandik"], "secmen": b["secmen"]}, "etiket": ""}, idx,
                                       b["plaka"] or a["plaka"], gevsek=True)
                if ref_r:
                    b.update(ad=ref_r["ad"], plaka=ref_r["plaka"], kimlik={"yontem": yontem, "ysk": ref_r["dosya"]})
                    a.update(plaka=ref_r["plaka"], ad=ref_r["ilce"], ilce=ref_r["ilce"],
                             kimlik={"yontem": "alt_sehir_satiri_ysk_sandik_secmen", "ysk": ref_r["dosya"]})


def il_yapisi(kayit, alt_tipler):
    """Adi OCR'da kaybolmus il satiri: secmeni, altindaki birim satirlarinin
    kumulatif secmen toplamina BIREBIR esit olan satir. Plaka, alt satirlarin
    kimligi cozulmus olanlarinin cogunlugundan; sonra il sinirlari arasindaki
    satirlarin plakasi il satirininkiyle esitlenir."""
    for i, a in enumerate(kayit):
        if a["tip"] in ("il", "turkiye", "sehir", "koy") or not isinstance(a.get("secmen"), int):
            continue
        t, alt = 0, []
        for b in kayit[i + 1:]:
            if b["tip"] in ("il", "turkiye"):
                break
            if b["tip"] not in alt_tipler or not isinstance(b.get("secmen"), int):
                continue
            t += b["secmen"]
            alt.append(b)
            if t >= a["secmen"]:
                break
        if len(alt) >= 2 and t == a["secmen"]:
            pl = collections.Counter(b["plaka"] for b in alt if b["kimlik"]["yontem"] != "cozulemedi" and b["plaka"])
            a["tip"] = "il"
            a["yapi"] = f"altındaki {len(alt)} birimin seçmen toplamına birebir eşit"
            if pl:
                a["plaka"] = pl.most_common(1)[0][0]
    plaka = None
    for k in kayit:
        if k["tip"] == "il":
            plaka = k["plaka"]
        elif k["tip"] == "turkiye":
            plaka = None
        elif plaka and k["kimlik"]["yontem"] == "cozulemedi":
            k["plaka"] = plaka


def dikey_kontrol(kayit, partiler, tur):
    """Il satiri = altindaki birimlerin parti bazinda toplami mi (sutun kimligi
    kontrolu: yuzde/toplam kisitlari bir sutun kaymasini yakalayamaz, il
    toplami yakalar). Il satirina kontrol.dikey yazilir."""
    sonuc = collections.Counter()
    il = None
    gruplar = []
    for k in kayit:
        if k["tip"] in ("il", "turkiye"):
            il = k if k["tip"] == "il" else None
            if il:
                gruplar.append((il, []))
        elif il is not None and (k["tip"] in ("ilce", "belde", None) if tur == "belediye" else k["tip"] == "ilce"):
            gruplar[-1][1].append(k)
    for il, alt in gruplar:
        top = collections.Counter()
        for k in alt:
            top.update(k["oy"])
        fark = [p for p in partiler if il["oy"].get(p, 0) != top.get(p, 0)]
        tamam_tutarli = all(k["kontrol"]["durum"] == "tutarli" for k in alt + [il])
        il["kontrol"]["dikey"] = {"tutuyor": not fark, "farkliPartiler": fark, "altSatir": len(alt),
                                  "hepsiTutarli": tamam_tutarli}
        sonuc["tutuyor" if not fark else "fark"] += 1
        if tamam_tutarli:
            sonuc["hepsiTutarli_" + ("tutuyor" if not fark else "fark")] += 1
    return dict(sonuc)


AD_KUMESI = {}


def ad_kumesi(secim):
    """Il bazinda bilinen ilce/belde adlari (etiket birebir kimligi icin):
    YSK arsivindeki adlar + DIE oncesi harita verisindeki ilce adlari + belde
    kayitlari. Yalnizca BIREBIR (fold) esitlik kullanilir."""
    out = collections.defaultdict(dict)
    taban = ROOT / "data/kaynaklar/taban"
    y = taban / "yerel" / f"{secim}.json"
    if y.exists():
        for r in json.loads(y.read_text(encoding="utf-8"))["ilceler"]:
            out[r["plaka"]].setdefault(fold(r["ad"]).replace(" ", ""), (r["ad"], "ilce", r["ad"], str(y.relative_to(ROOT))))
    b = taban / "ek" / "beldeler" / f"{secim}.json"
    if b.exists():
        for r in json.loads(b.read_text(encoding="utf-8"))["kayitlar"]:
            out[r["plaka"]].setdefault(fold(r["belde"]).replace(" ", ""), (r["belde"], "belde", r.get("ilce"), str(b.relative_to(ROOT))))
    # ayni adli iki birim varsa (ilce + belde) belirsiz: kullanma
    return out


def isle(secim, tablolar=None):
    cfg = KITAPLAR[secim]
    AD_KUMESI.clear()
    AD_KUMESI.update(ad_kumesi(secim))
    pdf = die_tablo.ac(RAW / f"{cfg['demirbas']}.pdf")
    ref = ysk_referans(cfg["yil"])
    idx = collections.defaultdict(list)
    for x in ref:
        idx[(x["sandik"], x["secmen"])].append(x)
    rapor = {"ysk_referans_belediye": len(ref)}
    for tablo, (ilk, son) in cfg["tablolar"].items():
        if tablolar and tablo not in tablolar:
            continue
        cfg_t = dict(cfg, **cfg.get("tabloSutun", {}).get(tablo, {}))
        satirlar, eslesmeyen = ocr_tablo.tablo(pdf, cfg_t, ilk, son)
        kayit, gt = [], collections.defaultdict(collections.Counter)
        plaka = None
        for r in satirlar:
            durum, dog, ayr = ocr_tablo.dogrula(r["v"], r["yuzde"], cfg["partiler"])
            if durum == "tutarli" and r.get("konumSupheli"):
                # degerler kendi icinde tutarli ama bir hucre sutun kenarindan uzak:
                # deger + yuzdesi birlikte komsu sutuna kaymis olabilir (YSK olcumu:
                # 1999'daki 4 yanlis tutarli satirin 4'u de bu isaretle yakalaniyor)
                durum = "konumSupheli"
            f = fold(r["etiket"])
            il_etiket = IL_AD.get(f.replace(" ", ""))
            if il_etiket and r["etiket"].upper() == r["etiket"]:
                plaka = il_etiket
            sehir_satiri = tablo == "il_genel_meclisi" and re.match(r"^SEHIR(?!LER)", f)
            if tablo == "il_genel_meclisi" and not sehir_satiri:
                ref_r, yontem = None, "cozulemedi"
            else:
                ref_r, yontem = kimlik(r, idx, plaka, gevsek=bool(sehir_satiri))
            if not ref_r and yontem == "cozulemedi" and plaka and r["etiket"] and not il_etiket:
                ad_k = AD_KUMESI.get(plaka, {}).get(fold(r["etiket"]).replace(" ", ""))
                if ad_k:
                    ref_r, yontem = {"plaka": plaka, "ad": ad_k[0], "tip": ad_k[1], "ilce": ad_k[2], "yaris": "etiket",
                                     "dosya": ad_k[3]}, "etiket_birebir"
            if il_etiket and r["etiket"].upper() == r["etiket"]:
                ref_r, yontem = None, "il_etiketi"
            elif ref_r:
                plaka = ref_r["plaka"]
            tip = (ref_r["tip"] if ref_r else ("il" if yontem == "il_etiketi" else None))
            if tablo == "il_genel_meclisi" and re.match(r"^(SEHIR|KOY)", f):
                tip = "sehir" if f.startswith("SEHIR") else "koy"
                if sehir_satiri and ref_r and kayit and kayit[-1]["tip"] in (None, "ilce"):
                    # sehir satiri ilce merkezi belediyesi: ust satir o ilcenin tamamidir
                    kayit[-1].update(tip="ilce", plaka=ref_r["plaka"], ad=ref_r["ilce"], ilce=ref_r["ilce"],
                                     kimlik={"yontem": "alt_sehir_satiri_ysk_sandik_secmen", "ysk": ref_r["dosya"]})
            elif tablo == "il_genel_meclisi" and tip is None and yontem != "il_etiketi" and not re.search(r"TURKIYE|TURKEY", f):
                tip = "ilce"
            elif re.search(r"TURKIYE|TURKEY", f):
                tip, plaka = "turkiye", None
            v = r["v"]
            k = {"tip": tip, "plaka": ref_r["plaka"] if ref_r else plaka,
                 "ad": ref_r["ad"] if ref_r else None, "ilce": ref_r["ilce"] if ref_r else None,
                 "adKaynakta": r["etiket"] or None,
                 "kimlik": {"yontem": yontem, **({"ysk": ref_r["dosya"]} if ref_r else {})},
                 "sandik": v.get("sandik"), "secmen": v.get("secmen"), "oyKullanan": v.get("oyKullanan"),
                 "katilim": r["yuzde"].get("oyKullanan"), "gecerliOy": v.get("gecerliOy"),
                 "oy": {p: v[p] for p in cfg["partiler"] if isinstance(v.get(p), int) and v[p]},
                 "yuzde": {p: r["yuzde"][p] for p in cfg["partiler"] if isinstance(r["yuzde"].get(p), float) and r["yuzde"][p]},
                 "kontrol": {"durum": durum, **ayr, **({"sagSayfaYok": True} if r["sagYok"] else {}),
                             **({"konumSupheli": r["konumSupheli"]} if r.get("konumSupheli") else {})},
                 "dogrulama": dog, "sayfa": r["sayfa"]}
            if r["karakter"]:
                k["karakter"] = r["karakter"]
            k["kazanan"] = max(k["oy"], key=k["oy"].get) if k["oy"] else None
            if ref_r and ref_r["yaris"] == "etiket":
                k["kimlik"]["not"] = "kaynaktaki ad, bilinen bir ilçe/belde adıyla birebir aynı (YSK'de bu birim yok)"
            if ref_r and ref_r["yaris"] == "buyuksehir":
                k["kimlik"]["not"] = "YSK satırı büyükşehir yarışının ilçe kırılımı; kimlik için kullanıldı, oylar karşılaştırılmadı"
            if ref_r and tablo == "belediye_baskanligi" and ref_r["yaris"] == "belediye" and ref_r["tip"] != "il":
                esit, fark = karsilastir(r, ref_r, cfg["partiler"])
                k["yskKarsilastirma"] = {"esit": len(esit), "farkli": fark}
                gt[durum]["satir"] += 1
                gt[durum]["birebir" if not fark else "farkli"] += 1
                gt[durum]["alan_esit"] += len(esit)
                gt[durum]["alan_farkli"] += len(fark)
            kayit.append(k)
        if tablo in ("belediye_meclisi",):
            kardes_kimlik(kayit, OUT / secim / "belediye_baskanligi.json")
        if tablo == "il_genel_meclisi":
            igm_yapisi(kayit, idx)
            il_yapisi(kayit, ("ilce",))
        else:
            il_yapisi(kayit, ("ilce", "belde", None))
        dikey = dikey_kontrol(kayit, cfg["partiler"], "il_genel_meclisi" if tablo == "il_genel_meclisi" else "belediye")
        say = lambda f: sum(1 for x in kayit if f(x))  # noqa: E731
        ozet = {"satir": len(kayit), "durum": dict(collections.Counter(x["kontrol"]["durum"] for x in kayit)),
                "tip": dict(collections.Counter(str(x["tip"]) for x in kayit)),
                "kimlikCozulen": say(lambda x: x["kimlik"]["yontem"] not in ("cozulemedi",)),
                "dikey": dikey,
                "eslesmeyenSayfa": eslesmeyen}
        veri = {"secim": secim, "tablo": tablo, "aciklama": ACIKLAMA[tablo],
                "kaynak": {"ana": "tuik", "yayin": cfg["yayin"], "demirbas": cfg["demirbas"],
                           "url": f"https://kutuphane.tuik.gov.tr/pdf/{cfg['demirbas']}.pdf",
                           "ham": f"data/raw/tuik/mahalli-kitap/{cfg['demirbas']}.pdf", "sayfalar": [ilk, son],
                           "okuma": "scripts/pipelines/tuik_arsiv/ocr_tablo.py (değer tahmini yok; alan bazında doğrulama)"},
                "partiler": cfg["partiler"], "ozet": ozet, "satirlar": kayit}
        (OUT / secim).mkdir(parents=True, exist_ok=True)
        (OUT / secim / f"{tablo}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
        rapor[tablo] = {"ozet": ozet, **({"yskGroundTruth": {d: dict(c) for d, c in gt.items()}} if gt else {})}
        print(secim, tablo, json.dumps(rapor[tablo], ensure_ascii=False)[:600])
    p = OUT / secim / "dogrulama_raporu.json"
    eski = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    eski.update(rapor)
    p.write_text(json.dumps(eski, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    secim = sys.argv[1]
    isle(secim, sys.argv[2:] or None)


if __name__ == "__main__":
    main()
