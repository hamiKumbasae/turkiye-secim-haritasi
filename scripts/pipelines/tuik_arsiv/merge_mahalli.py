"""
DIE Mahalli Idareler Secimi Sonuclari kitaplarinin kaynak katmanini
(data/kaynaklar/tuik/yerel/<secim>/*.json, extract_mahalli.py) projeye isler:

  1. data/normalized/elections/yerel/<secim>.json  il merkezi / ilce belediye
     baskanligi satirlari (onceki tek kaynak: Turkce Wikipedia)
  2. data/normalized/ek/beldeler/<secim>.json       belde kayitlarina DIE sonucu
  3. data/normalized/ek/belediye_meclisi/<secim>.json, ek/il_genel_meclisi/<secim>.json
     (projede hic yoktu)

Koken kurali (1991-2007 genel birlestirmesiyle ayni):
  - Satirin TABANI Wikipedia (satir kimligi + aday adlari). DIE satiri kendi
    ic kontrolunden (parti toplami == gecerli oy) GECTIYSE oy/gecerli/secmen/
    sandik/katilim DIE'den alinir; farkli ya da Wikipedia'da olmayan her alan
    `kaynak.farklar`'a {alan, kaynak: "tuik", eski, yeni} olarak yazilir.
    Oylar birebir ayniysa `kaynak.teyit = ["tuik"]`.
  - DIE satiri ic kontrolden GECEMEDIYSE parti oylarina dokunulmaz; yalnizca
    katilim yuzdesiyle dogrulanan secmen / sandik / katilim eklenir ve neden
    `kaynak.tuikKullanilmadi`'da yazar.
  - Projede olmayan ilce satiri (DIE'de var, tutarli, modern ilce poligonu ada
    gore bulunuyor) `kaynak.ana = "tuik"` ile eklenir.
  - 1989'da Wikipedia MCP'yi 'MHP' etiketiyle vermis; DIE'de MCP. Bu bir etiket
    farki (kaynak.etiket), deger farki sayilmaz.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/merge_mahalli.py           # kuru calisma
  python3 scripts/pipelines/tuik_arsiv/merge_mahalli.py --write
"""
import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
from common.election_io import save_election  # noqa: E402
from extract_mahalli import KITAPLAR as _K1, _anahtar, _benzer  # noqa: E402
from extract_mahalli_ocr import KITAPLAR as _K2  # noqa: E402

KITAPLAR = {**_K1, **_K2}


def dad(d):
    """DIE satirinin eslemede kullanilacak adi: kimligi YSK'den cozulmusse
    YSK adi (1994/1999), degilse kaynaktaki (OCR) ad."""
    return d.get("ad") or d["adKaynakta"] or ""


def kullanilir(d):
    """1994/1999 OCR katmaninda kimligi cozulemeyen satir haritaya islenmez."""
    return (d.get("kimlik") or {}).get("yontem") != "cozulemedi"

ROOT = HERE.parent.parent.parent
SRC = ROOT / "data" / "kaynaklar" / "tuik" / "yerel"
EK = ROOT / "data" / "normalized" / "ek"
SECIMLER = ["1984yerel", "1989yerel", "1994yerel", "1999yerel", "2004yerel"]
TABAN = ROOT / "data" / "kaynaklar" / "taban"  # DIE birlestirmesi oncesi (git 1e1e8e8)
ETIKET = {"1989yerel": {"MHP": "MÇP"}}  # Wikipedia etiketi -> DIE partisi
# ayni yerin sonraki il kodu: modern ilce poligonu ararken eski il -> yeni il
AYRILAN = {68: 51, 69: 29, 70: 42, 71: 6, 72: 56, 73: 56, 74: 67, 75: 36, 76: 36, 77: 41, 78: 67, 79: 27,
           80: 1, 81: 14}
IL_ILCE = json.loads((ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text(encoding="utf-8"))
GEOM = json.loads((ROOT / "data/raw/ysk/acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))


def tr_baslik(s):
    kucuk = s.replace("I", "ı").replace("İ", "i").lower()
    return " ".join(w[:1].upper().replace("i", "İ").replace("ı", "I") + w[1:] if w else w
                    for w in kucuk.split(" ")).replace("İ", "İ")


def kaynak_katmani(secim, tablo):
    return json.loads((SRC / secim / f"{tablo}.json").read_text(encoding="utf-8"))


def sol_dogrulandi(r):
    """Sol sayfa (sandik/secmen/oy kullanan) kitabin katilim yuzdesiyle tutuyor mu."""
    s, k, kat = r.get("secmen"), r.get("oyKullanan"), r.get("katilim")
    return isinstance(s, int) and isinstance(k, int) and s > 0 and isinstance(kat, float) \
        and abs(100 * k / s - kat) <= 0.1 and k <= s


def modern_geom(ad_anahtar, era_plaka):
    """Ada gore modern ilce poligonu (ayni il ya da sonradan ondan ayrilan il)."""
    adaylar = []
    for pl, v in IL_ILCE.items():
        pl = int(pl)
        if pl != era_plaka and AYRILAN.get(pl) != era_plaka:
            continue
        for c in v["ilceler"]:
            if _anahtar(c["ilce_ADI"]) == ad_anahtar:
                adaylar.append(GEOM.get(f"{pl}-{c['ilce_ID']}"))
    adaylar = [g for g in adaylar if g]
    return adaylar[0] if len(adaylar) == 1 else None


def _varyantlar(ad):
    """'Sincanlı (Sinanpaşa)' -> {SINCANLI, SINANPASA}."""
    import re
    out = {_anahtar(ad)}
    for m in re.findall(r"\(([^)]*)\)", ad or ""):
        out.add(_anahtar(m))
    return out


def destekli(p, d):
    """Zayif ad eslesmesi icin sayisal dogrulama: en az bir parti oyu birebir
    ayni (>= 10) ya da gecerli oy %3 icinde. Belde kaydinda: kazananin oyu ayni."""
    po = {}
    for k, v in (p.get("oy") or {}).items() if isinstance(p.get("oy"), dict) else []:
        po[k] = v.get("oy") if isinstance(v, dict) else v
    if isinstance(p.get("oy"), int):
        return d["oy"].get(p.get("kazanan")) == p["oy"] or p["oy"] in d["oy"].values()
    if any(v >= 10 and v in po.values() for v in d["oy"].values()):
        return True
    pg, dg = p.get("gecerliOy"), d.get("gecerliOy")
    return bool(pg and dg and abs(pg - dg) <= 0.03 * max(pg, dg))


def eslestir(proje, die, esik=0.8, sira_esik=0.45):
    """(proje satirlari, DIE satirlari) -> [(p, d)] bire bir, ayni il icinde:
    1) ad (ya da parantezli diger ad) birebir, 2) benzerlik >= esik,
    3) kalanlar alfabetik sirayla hizalanir (kitap ilceleri alfabetik verir;
    OCR'i cok bozuk adlar - 'OüZİSI' = Düziçi - ancak sirayla bulunur)."""
    from extract_mahalli import _sirali_hizala
    ciftler, kp, kd = [], set(), set()
    pv = {id(p): _varyantlar(p["ad"]) for p in proje}
    dk = {id(d): _anahtar(dad(d)) for d in die}
    for p in proje:
        for d in die:
            if id(d) not in kd and dk[id(d)] in pv[id(p)]:
                ciftler.append((p, d))
                kp.add(id(p))
                kd.add(id(d))
                break
    adaylar = sorted(((max(_benzer(v, dk[id(d)]) for v in pv[id(p)]), id(p), id(d), p, d) for p in proje for d in die
                      if id(p) not in kp and id(d) not in kd), key=lambda x: -x[0])
    for b, ip, idd, p, d in adaylar:
        if b < esik:
            break
        if ip in kp or idd in kd:
            continue
        ciftler.append((p, d))
        kp.add(ip)
        kd.add(idd)
    kalan_p = sorted((p for p in proje if id(p) not in kp), key=lambda p: min(pv[id(p)]))
    kalan_d = [d for d in die if id(d) not in kd]
    if kalan_p and kalan_d and sira_esik:
        ref = [min(pv[id(p)]) for p in kalan_p]
        es = _sirali_hizala(ref, [dk[id(d)] for d in kalan_d], esik=sira_esik)
        j = 0
        # _sirali_hizala yalnizca hangi d'nin eslestigini doner; eslesen d'leri
        # sirayla eslesmemis p'lere yeniden bagla (ayni hizalamayi tekrarla)
        eslesen_d = [d for d, e in zip(kalan_d, es) if e]
        es_p = _sirali_hizala([dk[id(d)] for d in eslesen_d], ref, esik=sira_esik)
        eslesen_p = [p for p, e in zip(kalan_p, es_p) if e]
        for p, d in zip(eslesen_p, eslesen_d):
            if destekli(p, d):
                ciftler.append((p, d))
                j += 1
    return ciftler


def resmi_karsilastir(row, d, secim, tablo, sayac):
    """Satir zaten resmi kaynaktan (YSK arsivi, 2004): degerlere dokunulmaz, DIE
    yalnizca teyit / fark olarak yazilir. YSK satirinda kucuk partiler 'Diğer'
    altinda; DIE'deki dagilimi kaynak.tuik.digerDagilimi'nda."""
    tuik = {"kitap": KITAPLAR[secim]["demirbas"], "tablo": tablo, "sayfa": d["sayfa"], "adKaynakta": d["adKaynakta"],
            "katman": f"data/kaynaklar/tuik/yerel/{secim}/{tablo}.json"}
    ysk = {p: (v.get("oy") if isinstance(v, dict) else v) for p, v in (row.get("oy") or {}).items()}
    # YSK arsivindeki ilce satiri ilce merkezi + (modern ilceye denk gelmeyen)
    # beldelerinin TOPLAMI olabiliyor; ayrica buyuksehir ilcelerinde BB yarisi.
    # Hangi DIE birimiyle birebir tutuyorsa o yazilir.
    secenek = [("ilçe merkezi belediyesi", d)] + (d.get("_alternatifler") or [])
    for ad, dd in secenek:
        yv = {p: dd["oy"].get(p, 0) for p in ysk if p != "Diğer"}
        if "Diğer" in ysk:
            yv["Diğer"] = sum(o for p, o in dd["oy"].items() if p not in ysk)
        if all(ysk[p] == yv.get(p) for p in ysk) and row.get("gecerliOy") == dd["gecerliOy"]:
            d, tuik["birim"] = dd, ad
            if dd.get("_tablo"):
                tuik["tablo"] = dd["_tablo"]
            break
    dig = {p: o for p, o in d["oy"].items() if p not in ysk}
    die = {p: d["oy"].get(p, 0) for p in ysk if p != "Diğer"}
    if "Diğer" in ysk:
        die["Diğer"] = sum(dig.values())
        tuik["digerDagilimi"] = dict(sorted(dig.items(), key=lambda kv: -kv[1]))
    fark = [{"alan": "oy." + p, "ysk": ysk[p], "tuik": die[p]} for p in ysk if ysk[p] != die.get(p)]
    for alan in ("gecerliOy", "secmen", "sandik"):
        if row.get(alan) and d.get(alan) is not None and row[alan] != d[alan]:
            fark.append({"alan": alan, "ysk": row[alan], "tuik": d[alan]})
    kaynak = {"ana": "ysk", "tuik": tuik}
    if d["kontrol"]["durum"] != "tutarli":
        kaynak["tuikKullanilmadi"] = {"neden": "DİE satırı iç kontrolden geçmedi", "kontrol": d["kontrol"]}
    elif fark:
        # hicbir DIE birimi (merkez / merkez + beldeler / BB) YSK satiriyla birebir
        # tutmadi: YSK arsivindeki ilce satiri, sonradan ilce olmayan beldelerin bir
        # KISMINI toplayabiliyor; bu bir deger farki degil birim farki olabilir
        kaynak["tuikBirimFarki"] = {"not": "YSK satırı DİE'deki hiçbir birimle (ilçe merkezi, merkez + tüm bağlı beldeler, büyükşehir) birebir eşleşmedi; YSK satırının hangi belediyeleri topladığı kayıtlı değil. Değerler değiştirilmedi.",
                                    "karsilastirma": fark}
        sayac["ysk_fark"] += 1
    else:
        kaynak["teyit"] = ["tuik"]
        sayac["ysk_teyit"] += 1
    row["kaynak"] = kaynak


def satiri_isle(row, d, secim, tablo, sayac, resmi=False):
    """Proje satirina (yerinde) DIE satirini isle; kaynak alanini yaz."""
    if resmi:
        return resmi_karsilastir(row, d, secim, tablo, sayac)
    etiket = ETIKET.get(secim, {})
    eski_oy = {}
    for p, v in (row.get("oy") or {}).items():
        eski_oy[etiket.get(p, p)] = v
    tuik = {"kitap": KITAPLAR[secim]["demirbas"], "tablo": tablo, "sayfa": d["sayfa"], "adKaynakta": d["adKaynakta"],
            "katman": f"data/kaynaklar/tuik/yerel/{secim}/{tablo}.json"}
    if d.get("ocrDuzeltme"):
        tuik["ocrDuzeltme"] = d["ocrDuzeltme"]
    if d.get("yapisalOkuma"):
        tuik["yapisalOkuma"] = True
    kaynak = {"ana": "wikipedia", "tuik": tuik}
    if any(p in etiket for p in (row.get("oy") or {})):
        kaynak["etiket"] = {k: v for k, v in etiket.items() if k in row["oy"]}
    farklar = []

    def degis(alan, eski, yeni):
        if eski != yeni:
            farklar.append({"alan": alan, "kaynak": "tuik", "eski": eski, "yeni": yeni})

    tutarli = d["kontrol"]["durum"] == "tutarli"
    if sol_dogrulandi(d):
        for alan, yeni in (("sandik", d["sandik"]), ("secmen", d["secmen"]), ("katilim", d["katilim"])):
            eski = row.get(alan) or None
            degis(alan, eski, yeni)
            row[alan] = yeni
    if tutarli:
        g = d["gecerliOy"]
        yeni_oy = {}
        for p, o in d["oy"].items():
            e = eski_oy.get(p) or {}
            yeni_oy[p] = {"oy": o, "oran": round(100 * o / g, 2)}
            if e.get("aday"):
                yeni_oy[p]["aday"] = e["aday"]
        for p in sorted(set(eski_oy) | set(yeni_oy)):
            degis("oy." + p, (eski_oy.get(p) or {}).get("oy"), (yeni_oy.get(p) or {}).get("oy"))
        degis("gecerliOy", row.get("gecerliOy"), g)
        oy_farki = any(f["alan"].startswith("oy.") or f["alan"] == "gecerliOy" for f in farklar)
        row["oy"] = dict(sorted(yeni_oy.items()))
        row["gecerliOy"] = g
        row["kazanan"] = max(yeni_oy, key=lambda p: yeni_oy[p]["oy"]) if yeni_oy else None
        if not oy_farki:
            kaynak["teyit"] = ["tuik"]
        if any(v.get("aday") for v in row["oy"].values()):
            kaynak["adayKaynak"] = "wikipedia"
        sayac["tuik_oy"] += 1
    else:
        kaynak["tuikKullanilmadi"] = {"neden": "DİE satırı iç kontrolden geçmedi (parti toplamı ≠ geçerli oy); parti oyları Wikipedia'da bırakıldı",
                                      "kontrol": d["kontrol"]}
        sayac["tuik_tutarsiz"] += 1
    if farklar:
        kaynak["farklar"] = farklar
    row["kaynak"] = kaynak


def yeni_satir(d, secim, tablo, geom):
    g = d["gecerliOy"]
    oy = {p: {"oy": o, "oran": round(100 * o / g, 2)} for p, o in sorted(d["oy"].items())}
    return {"ad": d.get("ad") or tr_baslik(d["adKaynakta"].strip(" .'•*")), "geomId": geom, "plaka": d["plaka"],
            "sandik": d["sandik"], "secmen": d["secmen"], "katilim": d["katilim"], "gecerliOy": g,
            "oy": oy, "kazanan": max(oy, key=lambda p: oy[p]["oy"]) if oy else None,
            "toplamVekil": 0, "vekil": {},
            "kaynak": {"ana": "tuik", **({"adKaynak": "ysk (sandık+seçmen kimliği)"} if d.get("ad") else {"adOcr": True}),
                       "tuik": {"kitap": KITAPLAR[secim]["demirbas"], "tablo": tablo, "sayfa": d["sayfa"],
                                "adKaynakta": d["adKaynakta"], "katman": f"data/kaynaklar/tuik/yerel/{secim}/{tablo}.json"}}}


def alternatifler(d, bel, bb):
    """Ilce merkezi satirinin disindaki olasi DIE birimleri: merkez + bagli
    beldelerin toplami; buyuksehir tablosundaki ayni adli ilce satiri."""
    out = []
    i = next(k for k, x in enumerate(bel) if x is d or (x["sayfa"] == d["sayfa"] and x["adKaynakta"] == d["adKaynakta"]))
    grup = [d]
    for x in bel[i + 1:]:
        # 1994/1999: kimligi cozulemeyen satirlarin tipi bos; konumca ilce
        # grubunun icindeler. Yalnizca karsilastirma toplami icin (deger yazilmaz)
        if x["tip"] not in ("belde", None):
            break
        grup.append(x)
    if len(grup) > 1:
        top = collections.Counter()
        for x in grup:
            top.update(x["oy"])
        out.append(("ilçe merkezi + bağlı beldeler toplamı",
                    {**d, "oy": dict(top), "gecerliOy": sum(x["gecerliOy"] or 0 for x in grup),
                     "secmen": sum(x["secmen"] or 0 for x in grup), "sandik": sum(x["sandik"] or 0 for x in grup),
                     "adKaynakta": f"{d['adKaynakta']} + {len(grup) - 1} belde"}))
    for x in bb:
        if x["plaka"] == d["plaka"] and _anahtar(dad(x)) == _anahtar(dad(d)):
            out.append(("büyükşehir belediye başkanlığı (ilçedeki oylar)", dict(x, _tablo="buyuksehir")))
    return out


def ysk_satiri(secim, r, il=False):
    """2004: il satirlari ve katilimi olan ilce satirlari YSK resmi arsivinden."""
    return secim in ("1994yerel", "1999yerel", "2004yerel") and (il or bool(r.get("katilim")))


def yerel_isle(secim, rapor):
    rec = json.loads((TABAN / "yerel" / f"{secim}.json").read_text(encoding="utf-8"))
    bel = kaynak_katmani(secim, "belediye_baskanligi")["satirlar"]
    bb = kaynak_katmani(secim, "buyuksehir")["satirlar"]
    sayac = collections.Counter()
    # --- ilce satirlari
    bb_iller = {d["plaka"] for d in bb if d["tip"] == "il"}
    die_ilce = collections.defaultdict(list)
    for d in bel:
        # il merkezi belediyesi il satirina gider; buyuksehirde il satiri BB
        # yarisi oldugundan merkez belediyesi ilce satiridir (1984 Izmir 'Merkez')
        if d["tip"] == "ilce" and d["plaka"] and kullanilir(d) and (_anahtar(dad(d)) != "MERKEZ" or d["plaka"] in bb_iller):
            die_ilce[d["plaka"]].append(d)
    proje_ilce = collections.defaultdict(list)
    for r in rec["ilceler"]:
        proje_ilce[r["plaka"]].append(r)
    eslesmeyen_proje, eklenen, eklenemeyen = [], [], []
    kullanilan_geom = {r["geomId"] for r in rec["ilceler"]}
    for pl in sorted(set(die_ilce) | set(proje_ilce)):
        ciftler = eslestir(proje_ilce.get(pl, []), die_ilce.get(pl, []))
        for p, d in ciftler:
            if ysk_satiri(secim, p):
                d = dict(d, _alternatifler=alternatifler(d, bel, bb))
            satiri_isle(p, d, secim, "belediye_baskanligi", sayac, ysk_satiri(secim, p))
        esp = {id(p) for p, _ in ciftler}
        esd = {id(d) for _, d in ciftler}
        # donemde belde olup sonradan ilce olan birimler (2004 Kepez, Atakum ...):
        # ayni ilde birebir ayni adli DIE belde satiri
        beldeler = [d for d in bel if d["tip"] == "belde" and d["plaka"] == pl]
        for p in proje_ilce.get(pl, []):
            if id(p) in esp:
                continue
            d = next((d for d in beldeler if kullanilir(d) and _anahtar(dad(d)) in _varyantlar(p["ad"])), None)
            if d:
                satiri_isle(p, dict(d, _alternatifler=[]), secim, "belediye_baskanligi", sayac, ysk_satiri(secim, p))
                p["kaynak"]["tuik"]["birim"] = "dönemin beldesi (sonradan ilçe)"
                esp.add(id(p))
                sayac["belde_ilce"] += 1
        eslesmeyen_proje += [f"{pl}:{p['ad']}" for p in proje_ilce.get(pl, []) if id(p) not in esp]
        # adi okunamayan (kimligi cozulemeyen) DIE satiri, projedeki eslesmemis
        # satirla en az 3 partinin oyunda (>= 10) BIREBIR aynıysa ayni birimdir
        adsiz = [d for d in bel if d["plaka"] == pl and not kullanilir(d) and d["kontrol"]["durum"] == "tutarli"
                 and id(d) not in esd]
        for p in proje_ilce.get(pl, []):
            if id(p) in esp or not adsiz:
                continue
            po = {k: (v.get("oy") if isinstance(v, dict) else v) for k, v in (p.get("oy") or {}).items()}
            uyan = [d for d in adsiz if sum(1 for k, o in d["oy"].items() if o >= 10 and po.get(k) == o) >= 3]
            if len(uyan) == 1:
                d = uyan[0]
                satiri_isle(p, dict(d, _alternatifler=[]), secim, "belediye_baskanligi", sayac, ysk_satiri(secim, p))
                p["kaynak"]["tuik"]["kimlik"] = "adı okunamadı; ≥3 partinin oyu mevcut satırla birebir aynı"
                esp.add(id(p))
                esd.add(id(d))
                adsiz.remove(d)
                sayac["oy_esitligi_kimlik"] += 1
        for d in die_ilce.get(pl, []):
            if id(d) in esd:
                continue
            geom = modern_geom(_anahtar(dad(d)), pl)
            if d["kontrol"]["durum"] == "tutarli" and geom and geom not in kullanilan_geom:
                rec["ilceler"].append(yeni_satir(d, secim, "belediye_baskanligi", geom))
                kullanilan_geom.add(geom)
                eklenen.append(f"{pl}:{d['adKaynakta']}")
            else:
                eklenemeyen.append(f"{pl}:{d['adKaynakta']} ({'tutarsız' if d['kontrol']['durum'] != 'tutarli' else 'poligon yok/kullanılmış'})")
    # --- il satirlari: buyuksehirde BB yarisi, digerlerinde il merkezi belediyesi
    bb_il = {d["plaka"]: d for d in bb if d["tip"] == "il"}
    merkez = {}
    for d in bel:
        if d["tip"] == "ilce" and d["plaka"] and kullanilir(d) and _anahtar(dad(d)) == "MERKEZ" and d["plaka"] not in merkez:
            merkez[d["plaka"]] = d
    il_sayac = collections.Counter()
    for r in rec["iller"]:
        d, tablo = (bb_il[r["plaka"]], "buyuksehir") if r["plaka"] in bb_il else (merkez.get(r["plaka"]), "belediye_baskanligi")
        if d is None:
            il_sayac["dieYok"] += 1
            continue
        satiri_isle(r, d, secim, tablo, il_sayac, ysk_satiri(secim, r, il=True))
    rec.setdefault("kaynakNotu", {})
    rapor[secim] = {"ilceTuikOy": sayac["tuik_oy"], "ilceTuikTutarsiz": sayac["tuik_tutarsiz"],
                    "ilceYskTeyit": sayac["ysk_teyit"], "doneminBeldesi": sayac["belde_ilce"], "oyEsitligiKimlik": sayac["oy_esitligi_kimlik"], "ilceYskFark": sayac["ysk_fark"],
                    "ilYskTeyit": il_sayac["ysk_teyit"], "ilYskFark": il_sayac["ysk_fark"],
                    "ilTuikOy": il_sayac["tuik_oy"], "ilTuikTutarsiz": il_sayac["tuik_tutarsiz"], "ilDieYok": il_sayac["dieYok"],
                    "eklenenIlce": eklenen, "eklenemeyenDieIlce": eklenemeyen, "dieIleEslesmeyenProjeIlce": eslesmeyen_proje}
    del rec["kaynakNotu"]
    return rec


# --- ek dosyalar ------------------------------------------------------------------
def _birim(d, il_adlari):
    return {"il": il_adlari.get(d["plaka"]), "plaka": d["plaka"], "tip": d["tip"], "adKaynakta": d["adKaynakta"],
            "ustIlce": d.get("ustIlce"), "sandik": d["sandik"], "secmen": d["secmen"], "oyKullanan": d["oyKullanan"],
            "katilim": d["katilim"], "gecerliOy": d["gecerliOy"], "oy": d["oy"], "kazanan": d["kazanan"],
            "kontrol": d["kontrol"], "sayfa": d["sayfa"],
            **{a: d[a] for a in ("ad", "ilce", "kimlik", "dogrulama", "yuzde", "yapi", "karakter") if d.get(a)}}


def ek_meclis(secim, tablo, alt, il_adlari):
    k = kaynak_katmani(secim, tablo)
    birimler = [_birim(d, il_adlari) for d in k["satirlar"] if d["tip"] in ("ilce", "belde", "sehir", "koy")]
    iller = [_birim(d, il_adlari) for d in k["satirlar"] if d["tip"] == "il"]
    turkiye = next((_birim(d, il_adlari) for d in k["satirlar"] if d["tip"] == "turkiye"), None)
    veri = {"secim": secim, "tur": alt, "aciklama": k["aciklama"],
            "kaynak": {**k["kaynak"], "katman": f"data/kaynaklar/tuik/yerel/{secim}/{tablo}.json",
                       "not": k["kaynak"].get("not", "") + " Satır başına `kontrol.durum`: 'tutarli' = parti oyları toplamı geçerli oya eşit (1994/1999'da ayrıca her parti yüzdesi ve katılım tutuyor); diğer durumlar OCR ya da kaynak hatası içerebilir, değerler olduğu gibi bırakıldı (tahmin yok). 1994/1999: `dogrulama` alan bazında hangi kısıtla doğrulandığını, `kimlik` birimin nasıl tanındığını verir."},
            "partiler": k["partiler"], "ozet": k["ozet"], "turkiye": turkiye, "iller": iller, "birimler": birimler}
    (EK / alt).mkdir(parents=True, exist_ok=True)
    (EK / alt / f"{secim}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return veri["ozet"]


def ek_beldeler(secim):
    p = EK / "beldeler" / f"{secim}.json"
    veri = json.loads((TABAN / "ek" / "beldeler" / f"{secim}.json").read_text(encoding="utf-8"))
    die = [d for d in kaynak_katmani(secim, "belediye_baskanligi")["satirlar"] if d["tip"] == "belde" and d["plaka"] and kullanilir(d)]
    etiket = ETIKET.get(secim, {})
    wiki = collections.defaultdict(list)
    for r in veri["kayitlar"]:
        wiki[r["plaka"]].append(r)
    sayac = collections.Counter()
    yeni_kayit = []
    for pl in sorted({d["plaka"] for d in die} | set(wiki)):
        pr = [dict(r, ad=r["belde"]) for r in wiki.get(pl, [])]
        ciftler = eslestir(pr, [d for d in die if d["plaka"] == pl], esik=0.75)
        esd = set()
        for p_, d in ciftler:
            r = next(x for x in wiki[pl] if x is not None and x["belde"] == p_["belde"] and x.get("ilce") == p_.get("ilce"))
            esd.add(id(d))
            tuik = {"sandik": d["sandik"], "secmen": d["secmen"], "oyKullanan": d["oyKullanan"], "katilim": d["katilim"],
                    "gecerliOy": d["gecerliOy"], "oy": d["oy"], "kazanan": d["kazanan"], "kontrol": d["kontrol"]["durum"],
                    "adKaynakta": d["adKaynakta"], "sayfa": d["sayfa"]}
            k = r["kaynak"] if isinstance(r.get("kaynak"), dict) else {"ana": r.get("kaynak")}
            k["tuikKatman"] = f"data/kaynaklar/tuik/yerel/{secim}/belediye_baskanligi.json"
            if d["kontrol"]["durum"] == "tutarli":
                wk = etiket.get(r.get("kazanan"), r.get("kazanan"))
                fark = []
                if wk != d["kazanan"]:
                    fark.append({"alan": "kazanan", "kaynak": "tuik", "eski": r.get("kazanan"), "yeni": d["kazanan"]})
                if r.get("oy") is not None and r.get("oy") != d["oy"].get(d["kazanan"]):
                    fark.append({"alan": "oy", "kaynak": "tuik", "eski": r.get("oy"), "yeni": d["oy"].get(d["kazanan"])})
                if fark:
                    k["farklar"] = fark
                    r["kazanan"], r["oy"] = d["kazanan"], d["oy"].get(d["kazanan"])
                    sayac["fark"] += 1
                else:
                    k["teyit"] = ["tuik"]
                    sayac["teyit"] += 1
            else:
                sayac["tuikTutarsiz"] += 1
            r["tuik"] = tuik
            r["kaynak"] = k
        for d in die:
            if d["plaka"] == pl and id(d) not in esd and d["kontrol"]["durum"] == "tutarli":
                yeni_kayit.append({"belde": d.get("ad") or tr_baslik(d["adKaynakta"].strip(" .'•*")), "ilce": d.get("ustIlce") or d.get("ilce"), "plaka": pl,
                                   "kazanan": d["kazanan"], "oy": d["oy"].get(d["kazanan"]),
                                   "tuik": {"sandik": d["sandik"], "secmen": d["secmen"], "oyKullanan": d["oyKullanan"],
                                            "katilim": d["katilim"], "gecerliOy": d["gecerliOy"], "oy": d["oy"],
                                            "kazanan": d["kazanan"], "kontrol": "tutarli", "adKaynakta": d["adKaynakta"], "sayfa": d["sayfa"]},
                                   "kaynak": {"ana": "tuik", **({"adKaynak": "ysk (sandık+seçmen kimliği)"} if d.get("ad") else {"adOcr": True}), "tuikKatman": f"data/kaynaklar/tuik/yerel/{secim}/belediye_baskanligi.json"}})
                sayac["yeni"] += 1
    veri["kayitlar"] += yeni_kayit
    veri["kaynak"] = {"ana": "wikipedia", "tuik": {"kitap": KITAPLAR[secim]["demirbas"], "yayin": KITAPLAR[secim]["yayin"],
                                                   "katman": f"data/kaynaklar/tuik/yerel/{secim}/belediye_baskanligi.json",
                                                   "not": "Her kayıtta `tuik` = DİE kitabındaki tam sonuç; kazanan/oy DİE ile farklıysa `kaynak.farklar` (eski = Wikipedia). `kaynak.ana = tuik` kayıtlar Wikipedia'da olmayan beldeler (ad OCR'dan)."}}
    p.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    return dict(sayac)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rapor = {}
    il_adlari = {int(k): tr_baslik(v["il_ADI"]) for k, v in IL_ILCE.items()}
    for secim in SECIMLER:
        rec = yerel_isle(secim, rapor)
        r = rapor[secim]
        print(secim, {k: (v if not isinstance(v, list) else len(v)) for k, v in r.items()})
        print("  eklenen:", r["eklenenIlce"])
        print("  eklenemeyen DIE ilce:", r["eklenemeyenDieIlce"][:40])
        print("  DIE ile eslesmeyen proje ilce:", r["dieIleEslesmeyenProjeIlce"][:40])
        if a.write:
            save_election(secim, rec)
            print("  meclis:", ek_meclis(secim, "belediye_meclisi", "belediye_meclisi", il_adlari))
            print("  igm:", ek_meclis(secim, "il_genel_meclisi", "il_genel_meclisi", il_adlari))
            print("  beldeler:", ek_beldeler(secim))
    if a.write:
        (SRC / "birlestirme_raporu.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
