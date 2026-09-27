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
  - il satiri: kitabin il toplami, yalniz 'tutarli' ise.

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
           "ilçenin tamamıdır (şehir + köy).",
    "bm": "{yayin} — belediye meclisi üyeliği oyları, taranmış kitaptan okundu. Yalnız toplamları ve "
          "yüzdeleri tutan (doğrulanmış) satırlar gösterilir; diğerleri boş ve açıklamalı. İlçe sonucu "
          "yalnız ilçe belediyesinin meclisidir, belde meclisleri hariç.",
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
    ek_geom = {b["geomId"] for b in ek["birimler"] if b["geomId"]}

    # geomId'siz Merkez satirlari -> baskanlik kaydindaki tek aday satir
    merkez_hedef, rapor = {}, []
    for (pl, ilce) in sorted({(b["plaka"], b["ilce"]) for b in ek["birimler"] if not b["geomId"]}):
        aday = [r for r in ana["ilceler"] if r["plaka"] == pl and r["geomId"] not in ek_geom and (r.get("gecerliOy") or 0) > 0]
        if len(aday) == 1:
            merkez_hedef[(pl, ilce)] = aday[0]["geomId"]
        else:
            rapor.append((pl, ilce, [r["ad"] for r in aday]))

    geom_birim = collections.defaultdict(list)
    for b in ek["birimler"]:
        if kisa == "bm" and b.get("beldeId"):
            continue
        g = b["geomId"] or merkez_hedef.get((b["plaka"], b["ilce"]))
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
    iller = []
    for a in ana["iller"]:
        r = ek_il.get(a["plaka"])
        if not r or not dogrulanmis(r):
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
    return kayit, sayac


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for yil in DIE_YILLARI:
        for kisa in TURLER:
            kayit, sayac = kur_die(yil, kisa)
            (OUT / f"{yil}_{kisa}.json").write_text(json.dumps(kayit, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                                                  encoding="utf-8")
            print(f"{yil}_{kisa}: il {sum(1 for r in kayit['iller'] if r['oy'])}/{len(kayit['iller'])}, "
                  f"ilçe {sum(1 for r in kayit['ilceler'] if r['oy'])}/{len(kayit['ilceler'])} | eşleşme {dict(sayac)}")
    for yil in YILLAR:
        for kisa in TURLER:
            kayit, rapor, hedef, bag = kur(yil, kisa)
            (OUT / f"{yil}_{kisa}.json").write_text(json.dumps(kayit, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
                                                  encoding="utf-8")
            veri = sum(1 for r in kayit["ilceler"] if r["oy"])
            print(f"{yil}_{kisa}: il {sum(1 for r in kayit['iller'] if r['oy'])}/{len(kayit['iller'])}, "
                  f"ilçe {veri}/{len(kayit['ilceler'])}, Merkez bağlanan {len(hedef)}, bağlanmayan oy {bag}")
            for r in rapor:
                print("   bağlanmadı:", r)


if __name__ == "__main__":
    main()
