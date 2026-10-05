"""
Yerel secimlerin il genel meclisi (igm) ve belediye meclisi (bm) oylarini haritanin okudugu
secim kaydi bicimine (iller/ilceler satirlari, oy: {parti: {oy, oran}}) cevirir.

Kaynak: data/normalized/ek/{il_genel_meclisi,belediye_meclisi}/<yil>yerel.json (YSK acik veri,
sandik duzeyinden il/ilce/belde bazinda toplanmis). Kaynak degerleri degismez; yalniz toplanir.

Kurallar:
  - Iskelet: ayni yilin belediye baskanligi kaydinin (data/normalized/elections/yerel) ilce
    satirlari. Boylece harita cografyasi (geomId'ler) baskanlik haritasiyla ayni kalir.
  - il satiri: kaynagin il toplami. 2014'ten beri buyuksehirlerde il genel meclisi secilmez
    (6360 sayili Kanun); bu illerde igm il satiri sonucsuz ve notlu, ilce satiri yok.
  - igm ilce: ilcenin tamami = kaynakta ilce satiri + o ilcenin belde satirlari (il genel
    meclisinde secim cevresi ilcedir).
  - bm ilce: yalniz ilce belediyesi meclisi (kaynakta beldeId'siz satir); belde meclisleri
    ayri belediyedir, baskanlik haritasinda da ilce = ilce belediyesi.
  - Kaynakta geomId'si olmayan "<Il> Merkez" satirlari (2009; 2012-2013'te bolunen Merkez
    ilceler): baskanlik kaydinda o ilde meclis verisiyle eslesmeyen ve oyu olan TEK satir
    varsa ona baglanir; birden cok ya da hic yoksa baglanmaz (tahmin yok) ve raporlanir.
    Belde adlari kaynakta yok; sonradan ilce olan beldeler ayri cizilmez (igm'de ana ilceye
    dahil, bm'de gosterilmez).
  - kazanan: bm'de kaynagin kazanani; igm ilcede toplanan oylarin birincisi (esitlikte bos).
  - oran = oy / gecerliOy * 100 (2 ondalik); katilim = oyKullanan / secmen * 100.

1984-2004 (DIE "Mahalli Idareler Secimi Sonuclari" kitaplari, taranmis; bkz.
data/raw/tuik/mahalli-kitap/PROVENANCE.md): ek/ dosyalarinda geomId yok, satirlar ad/secmen ile
baskanlik kaydinin ilce satirlarina baglanir:
  - Yalniz kontrol.durum = 'tutarli' ve kimligi cozulmus (kimlik.yontem != 'cozulemedi') satirlar
    haritaya islenir (kitap okuyucusunun kurali); digerleri 'dogrulanamadi' notuyla bos kalir.
  - Anahtarlar (ayni il icinde, tek aday): (a) secmen: bm'de satirin kendi secmeni, igm'de ilce
    satirinin altindaki sehir satiri (ilce merkezi belediyesi) - baskanlik satirinin secmeniyle
    birebir; (b) ad: kaynaktaki ad, baskanlik satirinin adi ya da onun TUIK kaynagindaki adiyla
    birebir (buyuk/kucuk harf ve noktalama disinda). Iki anahtar farkli satira isaret ederse
    baglanmaz; ayni ilceye birden cok satir duserse hicbiri baglanmaz.
  - il satiri: once YSK kesin sonucu (data/kaynaklar/ysk/mahalli-kesin/, 1984/1989/1994; parti
    toplami gecerli oya esitse), yoksa kitabin il toplami ('tutarli' ise). YSK satirinin parti
    toplami tutmasa bile secmeni DIE il satirinkinden farkliysa DIE satiri baska ile ait sayilir
    ve kullanilmaz (1994'te 7 ilde DIE il satiri YSK ile tamamen farkli cikti).

1994/1999/2004 bosluklari: DIE satiri dogrulanamayan ya da eslesmeyen il/ilce satirlari YSK'nin ayni
yillar icin yayimladigi "Tumu" dosyalarindan doldurulur (data/kaynaklar/ysk/mahalli-meclis/, okuyucu
scripts/pipelines/ysk_kesin/parse_mahalli_meclis_tumu.py). Bu dosyalar TUIK'in ayni birlestirme
tutanaklarindan hazirladigi dijital tablolardir; DIE'nin dogrulanmis satirlariyla karsilastirmada
15.600 satirdan 1'i disinda birebir ayni. Kurallar (tahmin yok):
  - Yalniz parti toplami gecerli oya esit ('tutarli') satirlar.
  - Il satiri tutarli oldugu halde ilce(+belde) toplami il satirini tutmayan illerde (sutun kaymasi
    olabilir) YSK ilce satirlari kullanilmaz.
  - Eslesme DIE ile ayni: secmen (bm: ilce belediyesi satiri; igm: ilce satirinin altindaki Sehir
    satiri) ya da ad, ayni il icinde tek aday; ikisi farkli satira isaret ederse baglanmaz.
  - Doldurulan satira veriNotu yazilir.

Elle dogrulanmis satir onarimlari (Tillo YSK meclis kayitlari vb.) duzeltmeler.json'da durur ve
her calistirmada en son uygulanir; cikti dosyalari elle duzenlenmez.

Cikti: data/normalized/meclis_harita/<yil>yerel_<igm|bm>.json

Kullanim:
  .venv/bin/python scripts/pipelines/meclis_harita/build_meclis_harita.py
"""
import collections
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[3]
NORM = ROOT / "data" / "normalized"
OUT = NORM / "meclis_harita"
YILLAR = ["2009yerel", "2014yerel", "2019yerel", "2024yerel"]
DIE_YILLARI = ["1984yerel", "1989yerel", "1994yerel", "1999yerel", "2004yerel"]
NOT_DOGRULANAMADI = "DİE kitabındaki satır doğrulanamadı (tarama okuma hatası); gösterilmiyor."
NOT_ESLESMEDI = "Kaynakta bu birimle eşleşen satır bulunamadı."
DIE_ACIKLAMA = {
    "igm": "{yayin} — il genel meclisi üyeliği oyları, taranmış kitaptan okundu. Yalnız toplamları ve "
           "yüzdeleri tutan (doğrulanmış) satırlar gösterilir; diğerleri boş ve açıklamalı. İlçe sonucu "
           "ilçenin tamamıdır (şehir + köy). İl toplamları 1984–1994'te okunabilen illerde YSK kesin "
           "sonuçlarından.",
    "bm": "{yayin} — belediye meclisi üyeliği oyları, taranmış kitaptan okundu. Yalnız toplamları ve "
          "yüzdeleri tutan (doğrulanmış) satırlar gösterilir; diğerleri boş ve açıklamalı. İlçe sonucu "
          "yalnız ilçe belediyesinin meclisidir, belde meclisleri hariç. İl toplamları 1984–1994'te "
          "okunabilen illerde YSK kesin sonuçlarından.",
}
TURLER = {"igm": ("il_genel_meclisi", "İl Genel Meclisi"), "bm": ("belediye_meclisi", "Belediye Meclisi")}
BUYUKSEHIR_IGM_NOTU = "Bu ilde il genel meclisi seçimi yapılmadı (büyükşehir, 6360 sayılı Kanun)."


def oku(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def oy_bicimi(oy, gecerli):
    return {k: {"oy": v, "oran": round(v / gecerli * 100, 2) if gecerli else None}
            for k, v in sorted(oy.items(), key=lambda x: -x[1]) if v}


def birinci(oy):
    s = sorted(oy.items(), key=lambda x: -x[1])
    if not s or (len(s) > 1 and s[0][1] == s[1][1]):
        return None
    return s[0][0]


def katilim(r):
    return round(r["oyKullanan"] / r["secmen"] * 100, 2) if r.get("secmen") and r.get("oyKullanan") is not None else None


def topla(birimler):
    oy = collections.Counter()
    t = collections.Counter()
    for b in birimler:
        oy.update(b["oy"])
        for k in ("sandik", "secmen", "oyKullanan", "gecerliOy"):
            t[k] += b.get(k) or 0
    return oy, t


def kur(yil, kisa):
    dosya, adi = TURLER[kisa]
    ek = oku(NORM / "ek" / dosya / f"{yil}.json")
    ana = oku(NORM / "elections" / "yerel" / f"{yil}.json")
    # Başkanlık hattındaki eksik Tillo kaydı, bağımsız meclis kaynağını
    # gizlememeli. İskelet yalnız bu meclis görünümü için genişletilir.
    if not any(r.get("geomId") == "TR-D-56-007" for r in ana["ilceler"]):
        tillo = next((b for b in ek["birimler"] if b.get("geomId") == "TR-D-56-007"), None)
        if tillo:
            ana["ilceler"].append({"ad": tillo["ilce"], "plaka": 56, "geomId": "TR-D-56-007"})
    ek_geom = {b["geomId"] for b in ek["birimler"] if b["geomId"]}
    plan_path = ROOT / "geo/historical/idari/merge_plan.json"
    plan = oku(plan_path)["sentetikler"] if plan_path.exists() else {}
    kaynak_hedef = {}
    for r in ana["ilceler"]:
        g = r.get("geomId")
        base = plan.get(g, {}).get("taban") or SENTETIK_TABAN.get(g, g)
        if base and r.get("oy"):
            if base in kaynak_hedef and kaynak_hedef[base] != g:
                raise ValueError(f"{yil}: aynı kaynak ilçesi iki poligona bağlanıyor: {base}")
            kaynak_hedef[base] = g

    ek_hedefler = {kaynak_hedef.get(g, g) for g in ek_geom}

    # geomId'siz Merkez satirlari -> baskanlik kaydindaki tek aday satir
    merkez_hedef, rapor = {}, []
    for (pl, ilce) in sorted({(b["plaka"], b["ilce"]) for b in ek["birimler"] if not b["geomId"]}):
        aday = [r for r in ana["ilceler"] if r["plaka"] == pl and r["geomId"] not in ek_hedefler and (r.get("gecerliOy") or 0) > 0]
        if len(aday) == 1:
            merkez_hedef[(pl, ilce)] = aday[0]["geomId"]
        else:
            rapor.append((pl, ilce, [r["ad"] for r in aday]))

    geom_birim = collections.defaultdict(list)
    for b in ek["birimler"]:
        if kisa == "bm" and b.get("beldeId"):
            continue
        g = kaynak_hedef.get(b["geomId"], b["geomId"]) or merkez_hedef.get((b["plaka"], b["ilce"]))
        if g:
            geom_birim[g].append(b)

    ek_il = {r["plaka"]: r for r in ek["iller"]}
    iller = []
    for a in ana["iller"]:
        r = ek_il.get(a["plaka"])
        if not r:
            iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": {}, "kazanan": None, "vekil": {}, "toplamVekil": 0,
                          "not": BUYUKSEHIR_IGM_NOTU if kisa == "igm" and yil != "2009yerel" else "Bu ilde kaynakta sonuç yok."})
            continue
        iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": oy_bicimi(r["oy"], r["gecerliOy"]),
                      "kazanan": r["kazanan"], "gecerliOy": r["gecerliOy"], "secmen": r["secmen"],
                      "sandik": r["sandik"], "katilim": katilim(r), "ilceSayisi": a.get("ilceSayisi"),
                      "vekil": {}, "toplamVekil": 0})
    ilceler = []
    for a in ana["ilceler"]:
        if a["plaka"] not in ek_il:
            continue
        bs = geom_birim.get(a["geomId"], [])
        if not bs:
            ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"], "oy": {}, "kazanan": None,
                            "vekil": {}, "toplamVekil": 0})
            continue
        oy, t = topla(bs)
        kaz = bs[0]["kazanan"] if kisa == "bm" and len(bs) == 1 else birinci(oy)
        ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"], "oy": oy_bicimi(oy, t["gecerliOy"]),
                        "kazanan": kaz, "gecerliOy": t["gecerliOy"], "secmen": t["secmen"], "sandik": t["sandik"],
                        "katilim": katilim(t), "vekil": {}, "toplamVekil": 0})

    ulusal = collections.Counter()
    for r in ek["iller"]:
        ulusal.update(r["oy"])
    top = sum(ulusal.values())
    kazananlar = {r["kazanan"] for r in iller if r["kazanan"]}
    major = [p for p, v in ulusal.most_common() if p in kazananlar or v / top >= 0.01]

    kayit = {"ad": ana["ad"], "tur": "yerel", "oylama": kisa, "oylamaAdi": adi, "contestType": "council_votes",
             "resultBasis": "votes", "toplamSandalye": None, "majorPartiler": major,
             "kaynak": {"dosya": f"data/normalized/ek/{dosya}/{yil}.json", **ek["kaynak"]},
             "iller": iller, "ilceler": ilceler}
    baglanmayan = sum(b["gecerliOy"] for b in ek["birimler"] if not (b["geomId"] or merkez_hedef.get((b["plaka"], b["ilce"])))
                      and not (kisa == "bm" and b.get("beldeId")))
    return kayit, rapor, merkez_hedef, baglanmayan


def ad_norm(s):
    if not s:
        return None
    s = re.sub(r"\(.*?\)", "", s)
    if re.search(r"-[A-Z]{3,}", s):  # 'MERKEZ-CENTRAL'
        s = s.split("-")[0]
    s = unicodedata.normalize("NFC", s.replace("İ", "i").replace("I", "ı").lower())
    return re.sub(r"[^a-zçğıöşü]", "", s) or None


def dogrulanmis(r):
    return (r.get("kontrol") or {}).get("durum") == "tutarli" and (r.get("kimlik") or {}).get("yontem") != "cozulemedi"


YSK_KESIN = ROOT / "data" / "kaynaklar" / "ysk" / "mahalli-kesin"
IL_TAKMA = {"İÇEL": "MERSİN", "AFYON": "AFYONKARAHİSAR", "KMARAŞ": "KAHRAMANMARAŞ"}


def il_fold(s):
    s = unicodedata.normalize("NFC", s).replace("i", "İ").upper()
    s = re.sub(r"[^A-ZÇĞİÖŞÜ]", "", s)
    return IL_TAKMA.get(s, s)


def ysk_kesin(yil, kisa, ana):
    p = YSK_KESIN / f"{yil}_{kisa}.json"
    if not p.exists():
        return {}
    plaka = {il_fold(r["ad"]): r["plaka"] for r in ana["iller"]}
    out = {}
    for r in oku(p)["satirlar"]:
        pl = plaka.get(il_fold(r["ilKaynakta"]))
        if pl:
            out[pl] = r
    return out


YSK_TUMU = ROOT / "data" / "kaynaklar" / "ysk" / "mahalli-meclis"
NOT_YSK = ("Kaynak: YSK/TÜİK {yil} {tur} tablosu (dijital); DİE kitabının taranmış satırı okunamadığı için "
           "buradan alındı.")


def ysk_tumu(yil, kisa, ana, by_sec, by_ad):
    """YSK 'Tumu' tablosundan il satirlari {plaka: satir} ve ilce satirlari {geomId: satir}"""
    p = YSK_TUMU / f"{yil}_{kisa}.json"
    if not p.exists():
        return {}, {}, collections.Counter()
    S = oku(p)["satirlar"]
    plaka = {il_fold(r["ad"]): r["plaka"] for r in ana["iller"]}
    sayac = collections.Counter()
    iller, supheli = {}, set()
    for r in S:
        if r.get("tip") != "il" or r["kontrol"]["durum"] != "tutarli":
            continue
        pl = plaka.get(il_fold(r["il"]))
        if not pl:
            sayac["il eşleşmedi"] += 1
            continue
        iller[pl] = r
        alt = [x for x in S if x.get("il") == r["il"] and x.get("tip") in (("ilce", "belde") if kisa == "bm" else ("ilce",))]
        t = collections.Counter()
        for x in alt:
            t.update(x.get("oy") or {})
        if dict(t) != r["oy"]:
            supheli.add(pl)
    eslesen = collections.defaultdict(list)
    for i, r in enumerate(S):
        belde = kisa == "bm" and r.get("tip") == "belde"
        if (r.get("tip") != "ilce" and not belde) or r["kontrol"]["durum"] != "tutarli":
            continue
        pl = plaka.get(il_fold(r["il"] or ""))
        if not pl or pl in supheli:
            sayac["il toplamı tutmuyor (kullanılmadı)" if pl else "il eşleşmedi"] += 1
            continue
        sec = r.get("secmen")
        if kisa == "igm":
            alt = S[i + 1] if i + 1 < len(S) and S[i + 1].get("tip") == "sehir" else None
            sec = alt.get("secmen") if alt else None
        a = by_sec.get((pl, sec), set()) if sec else set()
        b = by_ad.get((pl, ad_norm(r["ad"])), set())
        a = next(iter(a)) if len(a) == 1 else None
        b = next(iter(b)) if len(b) == 1 else None
        if a and b and a != b:
            sayac["çelişki"] += 1
            continue
        if belde:
            # sonradan ilce olan belde (ornek Artvin Kemalpasa): yalniz ad ve secmen ayni satira isaret ederse
            if a and a == b:
                eslesen[a].append(r)
                sayac["belde (ad+seçmen)"] += 1
            continue
        g = a or b
        if not g:
            sayac["eşleşmedi"] += 1
            continue
        eslesen[g].append(r)
    for g in [g for g, v in eslesen.items() if len(v) > 1]:
        del eslesen[g]
        sayac["aynı ilçeye çok satır"] += 1
    return iller, {g: v[0] for g, v in eslesen.items()}, sayac


def kur_die(yil, kisa):
    dosya, adi = TURLER[kisa]
    ek = oku(NORM / "ek" / dosya / f"{yil}.json")
    ana = oku(NORM / "elections" / "yerel" / f"{yil}.json")
    by_sec, by_ad = collections.defaultdict(set), collections.defaultdict(set)
    for r in ana["ilceler"]:
        if r.get("secmen"):
            by_sec[(r["plaka"], r["secmen"])].add(r["geomId"])
        for a in (r["ad"], ((r.get("kaynak") or {}).get("tuik") or {}).get("adKaynakta")):
            if ad_norm(a):
                by_ad[(r["plaka"], ad_norm(a))].add(r["geomId"])
    B = ek["birimler"]
    eslesen = collections.defaultdict(list)
    sayac = collections.Counter()
    for i, r in enumerate(B):
        if r.get("tip") != "ilce" or not r.get("plaka") or (r.get("kimlik") or {}).get("yontem") == "cozulemedi":
            continue
        sec = r.get("secmen")
        if kisa == "igm":
            alt = B[i + 1] if i + 1 < len(B) and B[i + 1].get("tip") == "sehir" else None
            sec = alt.get("secmen") if alt else None
        a = by_sec.get((r["plaka"], sec), set()) if sec else set()
        b = by_ad.get((r["plaka"], ad_norm(r.get("ad") or r.get("adKaynakta"))), set())
        a = next(iter(a)) if len(a) == 1 else None
        b = next(iter(b)) if len(b) == 1 else None
        if a and b and a != b:
            sayac["çelişki"] += 1
            continue
        g = a or b
        if not g:
            sayac["eşleşmedi"] += 1
            continue
        sayac["ikisi" if a and b else ("seçmen" if a else "ad")] += 1
        eslesen[g].append(r)
    cift = [g for g, v in eslesen.items() if len(v) > 1]
    for g in cift:
        del eslesen[g]
    sayac["aynı ilçeye çok satır (bırakıldı)"] = len(cift)

    ek_il = {r["plaka"]: r for r in ek["iller"] if r.get("plaka")}
    ysk_il = ysk_kesin(yil, kisa, ana)
    ysk_il_tumu, ysk_ilce, ysk_sayac = ysk_tumu(yil, kisa, ana, by_sec, by_ad)
    not_ysk = NOT_YSK.format(yil=yil[:4], tur=adi.lower())
    iller = []
    for a in ana["iller"]:
        r = ek_il.get(a["plaka"])
        y = ysk_il.get(a["plaka"])
        if y and y["kontrol"]["durum"] == "tutarli":
            r = dict(y, kazanan=max(y["oy"], key=y["oy"].get))
            sayac["il: YSK"] += 1
        elif r and dogrulanmis(r) and y and y.get("secmen") and y["secmen"] != r.get("secmen"):
            r = None
            sayac["il: DİE başka ile ait (YSK seçmeni farklı)"] += 1
        elif r and dogrulanmis(r):
            sayac["il: DİE"] += 1
        if not r or not (r is not ek_il.get(a["plaka"]) or dogrulanmis(r)):
            t = ysk_il_tumu.get(a["plaka"])
            if t:
                sayac["il: YSK tablosu"] += 1
                iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": oy_bicimi(t["oy"], t["gecerliOy"]),
                              "kazanan": birinci(t["oy"]), "gecerliOy": t["gecerliOy"], "secmen": t["secmen"],
                              "sandik": t.get("sandik"), "katilim": t.get("katilim"), "ilceSayisi": a.get("ilceSayisi"),
                              "vekil": {}, "toplamVekil": 0, "veriNotu": not_ysk})
                continue
            iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": {}, "kazanan": None, "vekil": {}, "toplamVekil": 0,
                          "not": ("İl toplamı: " + NOT_DOGRULANAMADI) if r else "Kaynakta bu ilin satırı yok."})
            continue
        iller.append({"ad": a["ad"], "plaka": a["plaka"], "oy": oy_bicimi(r["oy"], r["gecerliOy"]),
                      "kazanan": r["kazanan"], "gecerliOy": r["gecerliOy"], "secmen": r["secmen"],
                      "sandik": r.get("sandik"), "katilim": r.get("katilim"), "ilceSayisi": a.get("ilceSayisi"),
                      "vekil": {}, "toplamVekil": 0})
    ilceler = []
    for a in ana["ilceler"]:
        v = eslesen.get(a["geomId"])
        if not v or not dogrulanmis(v[0]):
            t = ysk_ilce.get(a["geomId"])
            if t:
                sayac["ilçe: YSK tablosu"] += 1
                ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"],
                                "oy": oy_bicimi(t["oy"], t["gecerliOy"]), "kazanan": birinci(t["oy"]),
                                "gecerliOy": t["gecerliOy"], "secmen": t["secmen"], "sandik": t.get("sandik"),
                                "katilim": t.get("katilim"), "vekil": {}, "toplamVekil": 0, "veriNotu": not_ysk})
                continue
            ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"], "oy": {}, "kazanan": None,
                            "vekil": {}, "toplamVekil": 0, "not": NOT_DOGRULANAMADI if v else NOT_ESLESMEDI})
            continue
        r = v[0]
        ilceler.append({"ad": a["ad"], "plaka": a["plaka"], "geomId": a["geomId"], "oy": oy_bicimi(r["oy"], r["gecerliOy"]),
                        "kazanan": r["kazanan"], "gecerliOy": r["gecerliOy"], "secmen": r["secmen"],
                        "sandik": r.get("sandik"), "katilim": r.get("katilim"), "vekil": {}, "toplamVekil": 0})

    ulusal = collections.Counter()
    for r in iller:
        ulusal.update({k: v["oy"] for k, v in r["oy"].items()})
    top = sum(ulusal.values()) or 1
    kazananlar = {r["kazanan"] for r in iller + ilceler if r["kazanan"]}
    major = [p for p, v in ulusal.most_common() if p in kazananlar or v / top >= 0.01]
    major += sorted(kazananlar - set(major))
    kayit = {"ad": ana["ad"], "tur": "yerel", "oylama": kisa, "oylamaAdi": adi, "contestType": "council_votes",
             "resultBasis": "votes", "toplamSandalye": None, "majorPartiler": major,
             "rozet": "TÜİK (DİE) Resmî Yayın", "aciklama": DIE_ACIKLAMA[kisa].format(yayin=ek["kaynak"]["yayin"]),
             "kaynak": {"dosya": f"data/normalized/ek/{dosya}/{yil}.json", **ek["kaynak"]},
             "iller": iller, "ilceler": ilceler}
    sayac.update({f"YSK eşleşme: {k}": n for k, n in ysk_sayac.items()})
    if ysk_sayac or sayac.get("ilçe: YSK tablosu") or sayac.get("il: YSK tablosu"):
        kayit["aciklama"] += (" DİE satırı okunamayan il ve ilçeler YSK'nin aynı tutanaklardan hazırlanmış dijital "
                              "tablosundan dolduruldu (satırın notunda belirtilir).")
    return kayit, sayac


DUZELTMELER = pathlib.Path(__file__).with_name("duzeltmeler.json")
# birlesim_2009_sonrasi.py: ana ilcenin satiri sentetik birlesime baglaninca kaynaktaki (YSK) satir hala
# ana ilcenin bugunku geomId'siyle gelir (ornek HIST-Artvin-Hopa <- TR-D-08-005)
SENTETIK_TABAN = {
    "HIST-Artvin-Hopa": "TR-D-08-005",
    "HIST-Aksaray-Merkez": "TR-D-68-002",
    "HIST-Hakkari-Semdinli": "TR-D-30-003",
}


def duzelt(ad, kayit):
    """duzeltmeler.json'daki elle dogrulanmis satir onarimlarini en son uygular (idempotent)."""
    for d in oku(DUZELTMELER)["duzeltmeler"]:
        if d["dosya"] != ad:
            continue
        rows = [r for r in kayit["ilceler"] if r["plaka"] == d["plaka"] and r["ad"] == d["ad"]]
        if len(rows) != 1:
            raise SystemExit(f"duzeltme uygulanamadi: {ad} {d['plaka']} {d['ad']} ({len(rows)} satir)")
        rows[0].update(d["alanlar"])
        for k in d.get("sil", []):
            rows[0].pop(k, None)
    return kayit


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for yil in DIE_YILLARI:
        for kisa in TURLER:
            kayit, sayac = kur_die(yil, kisa)
            duzelt(f"{yil}_{kisa}", kayit)
            (OUT / f"{yil}_{kisa}.json").write_text(json.dumps(kayit, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                                                  encoding="utf-8")
            print(f"{yil}_{kisa}: il {sum(1 for r in kayit['iller'] if r['oy'])}/{len(kayit['iller'])}, "
                  f"ilçe {sum(1 for r in kayit['ilceler'] if r['oy'])}/{len(kayit['ilceler'])} | eşleşme {dict(sayac)}")
    for yil in YILLAR:
        for kisa in TURLER:
            kayit, rapor, hedef, bag = kur(yil, kisa)
            duzelt(f"{yil}_{kisa}", kayit)
            (OUT / f"{yil}_{kisa}.json").write_text(json.dumps(kayit, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                                                  encoding="utf-8")
            veri = sum(1 for r in kayit["ilceler"] if r["oy"])
            print(f"{yil}_{kisa}: il {sum(1 for r in kayit['iller'] if r['oy'])}/{len(kayit['iller'])}, "
                  f"ilçe {veri}/{len(kayit['ilceler'])}, Merkez bağlanan {len(hedef)}, bağlanmayan oy {bag}")
            for r in rapor:
                print("   bağlanmadı:", r)


if __name__ == "__main__":
    main()
