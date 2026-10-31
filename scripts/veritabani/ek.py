"""data/normalized/ek/ ve meclis_2024.json'u veritabanina yukler (build_db.py cagirir).

- ek/milletvekilleri/<secim>.json  -> secilen (gorev='milletvekili'), kaynak_kapsami
- ek/senato/<yil>senato.json        -> secim (tur='senato'), sonuc_il/oy_il, sonuc_ilce/oy_ilce,
                                       secilen (gorev='senator'), kaynak_kapsami
- ek/yenileme_ara/*.json            -> secim (tur='ara'), sonuc_il/_ilce, sonuc_belde
- ek/beldeler/<secim>.json          -> sonuc_belde/oy_belde (belde belediye baskanligi)
- ek/belediye_meclisi/<secim>.json  -> yalniz belde satirlari sonuc_belde'ye (il ve ilce duzeyi
                                       meclis_harita/'dan zaten yuklu)
- ek/il_genel_meclisi/<secim>.json  -> yalniz kapsam ozeti (il/ilce meclis_harita/'dan; sehir/koy
                                       alt kirilimi yuklenmez)
- meclis_2024.json                  -> sandalye_ilce ('2024yerel_bm')
"""
import json
import re

from build_db import DATA, fold, j, oylar, yil_of

EK = DATA / "ek"
SKALER = {"secmen", "oyKullanan", "gecerliOy", "muteber", "sandik", "gecersizOy"}


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def dogrulanmis(r):
    """Kaynakta okunamayan (dogrulanamayan) alanlari NULL yapar; notu dondurur.
    'muteber' (eski yayinlarda gecerli oy) gecerliOy'a, ayri 'Bağımsız' alani oy'a tasinir."""
    r = dict(r)
    if "muteber" in r and "gecerliOy" not in r:
        r["gecerliOy"] = r["muteber"]
    oy = dict(r.get("oy") or {})
    if isinstance(r.get("Bağımsız"), int):
        oy.setdefault("Bağımsız", r["Bağımsız"])
    bozuk = list(r.get("dogrulanamayanAlanlar") or [])
    for alan in bozuk:
        if alan in SKALER:
            r[alan] = None
            if alan == "muteber":
                r["gecerliOy"] = None
        elif alan in oy:
            oy[alan] = None
    r["oy"] = oy
    notu = f"Kaynakta doğrulanamayan alanlar boş bırakıldı: {', '.join(bozuk)}" if bozuk else None
    return r, notu


def kapsam(y, sid, veri, bulunan=None, beklenen=None, durum=None, aciklama=None, ayrinti=None):
    y.con.execute("INSERT INTO kaynak_kapsami VALUES (?,?,?,?,?,?,?)",
                  (sid, veri, bulunan, beklenen, durum, aciklama, j(ayrinti)))


def secilenler(y, sid, kayitlar, gorev):
    satirlar = []
    for k in kayitlar:
        satirlar.append((sid, k["plaka"], gorev, k["ad"], y.sec.id(k.get("parti")), k.get("partiAdiKaynakta"),
                         k.get("bolge"), k.get("kisiLink"), j(k.get("kaynak"))))
    y.con.executemany(
        "INSERT INTO secilen(secim_id, plaka, gorev, ad, secenek_id, parti_adi_kaynakta, bolge, kisi_link,"
        " kaynak_json) VALUES (?,?,?,?,?,?,?,?,?)", satirlar)
    return len(satirlar)


SINIR = 10**12   # bundan buyuk sayi taranmis kitapta okuma hatasidir (SQLite INTEGER'a da sigmayabilir)


def sayi(v, bozuk, alan):
    if isinstance(v, (int, float)) and abs(v) >= SINIR:
        bozuk.append(alan)
        return None
    return v


def belde(y, sid, plaka, r, *, ilce_ad, belde_ad, kaynak, ilce_id=None, belde_kod=None, aday=None,
          kazanan=None, oy=None, sadece_kazanan=False, kontrol=None, notu=None, kaynak_bilgi=None):
    if ilce_id is None:
        ilce_id = y.ilce_bul(plaka, ilce_ad, yil_of(sid))
    bozuk = []
    r = {k: sayi(r.get(k), bozuk, k) for k in ("secmen", "oyKullanan", "gecerliOy", "gecersizOy", "sandik", "katilim")}
    oy = {p: {"oy": sayi(v.get("oy"), bozuk, p)} for p, v in oylar(oy)}
    if bozuk:
        notu = " | ".join(x for x in (notu, f"Okunamayan değer boş bırakıldı: {', '.join(bozuk)}") if x)
    cur = y.con.execute(
        "INSERT INTO sonuc_belde(secim_id, plaka, ilce_id, ilce_ad, belde_ad, belde_kod, secmen, oy_kullanan,"
        " gecerli_oy, gecersiz_oy, sandik, katilim, kazanan_id, aday, sadece_kazanan, kaynak, kontrol,"
        " not_metni, kaynak_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (sid, plaka, ilce_id, ilce_ad, belde_ad, belde_kod, r.get("secmen"), r.get("oyKullanan"),
         r.get("gecerliOy"), r.get("gecersizOy"), r.get("sandik"), r.get("katilim"), y.sec.id(kazanan),
         aday, int(sadece_kazanan), kaynak, kontrol, notu, j(kaynak_bilgi)),
    )
    bid = cur.lastrowid
    toplam = {}   # ayni secenege dusen birden cok ad (yazim farki) toplanir
    for p, v in oylar(oy):
        s, o = y.sec.id(p), v.get("oy")
        if s not in toplam:
            toplam[s] = o
        elif o is not None:
            toplam[s] = (toplam[s] or 0) + o
    y.con.executemany("INSERT INTO oy_belde VALUES (?,?,?)", [(bid, s, o) for s, o in toplam.items()])
    return ilce_id is not None


# --------------------------------------------------------------------------------------------
def milletvekilleri(y):
    n = 0
    for p in sorted((EK / "milletvekilleri").glob("*.json")):
        d = oku(p)
        sid = d["secim"]
        n += secilenler(y, sid, d["kayitlar"], "milletvekili")
        k = d.get("kapsam") or {}
        kapsam(y, sid, "milletvekilleri", k.get("bulunan"), k.get("beklenen"), k.get("durum"), k.get("not"), k)
    return f"milletvekili: {n:,} kişi"


def senato(y):
    n_kisi = n_ilce = n_birinci = n_eslesmeyen = 0
    for p in sorted((EK / "senato").glob("*.json")):
        d = oku(p)
        sid = d["secim"]
        y.secim(sid, "senato", "senato", f"{yil_of(sid)} Cumhuriyet Senatosu seçimi", aciklama=d.get("aciklama"))
        for r in d["iller"]:
            oy = {}
            for a in r.get("adaylar") or []:
                # partisiz satir kaynakta bagimsiz aday ('BĞMZ' kisaltmasi, partiAdi = kisi adi)
                parti = a.get("parti") or ("Bağımsız" if (a.get("kisaltma") or "").startswith("BĞMZ")
                                           else a.get("kisaltma") or a.get("partiAdi"))
                if a.get("oy") is not None:
                    oy[parti] = oy.get(parti, 0) + a["oy"]
            y.sonuc_il(sid, "senato", r["plaka"], r["il"], {**r, "oy": oy})
        # TUIK yayinindan ilce oylari (yalniz kitabi taranmis iller)
        tuik = (d.get("ilceOylariTuik") or {}).get("iller") or []
        gorulen = set()
        for il in tuik:
            for r in il.get("ilceler") or []:
                if not r.get("geomId") or r["geomId"] in gorulen:
                    continue
                gorulen.add(r["geomId"])
                r2, notu = dogrulanmis(r)
                y.sonuc_ilce(sid, "senato", r["geomId"], il["plaka"], r["ilce"], r2, notu=notu)
                n_ilce += 1
        # Vikipedi: ilcede birinci gelen parti (oy yok) - TUIK'te olmayan ilceler icin
        for r in d.get("ilceBirincileri") or []:
            iid = y.ilce_bul(r["plaka"], r["ilce"], yil_of(sid))
            if iid is None:
                n_eslesmeyen += 1
                continue
            if iid in gorulen:
                continue
            gorulen.add(iid)
            y.sonuc_ilce(sid, "senato", iid, r["plaka"], r["ilce"], {"oy": {}, "kaynak": r.get("kaynak")},
                         kazanan=r.get("birinciParti"), sadece_kazanan=True,
                         notu="Yalnız ilçede birinci gelen parti biliniyor (Vikipedi)")
            n_birinci += 1
        n_kisi += secilenler(y, sid, d.get("secilenler") or [], "senator")
        k = d.get("kapsam") or {}
        s = k.get("senator") or {}
        kapsam(y, sid, "senatorler", s.get("bulunan"), s.get("beklenen"), s.get("durum"), s.get("not"), k)
    return (f"senato: {n_kisi} senatör, {n_ilce} ilçe oy satırı (TÜİK), {n_birinci} ilçe yalnız birinci parti, "
            f"{n_eslesmeyen} ilçe adı eşleşmedi")


def il_cevrelerini_birlestir(iller):
    """Bir ilde birden cok secim cevresi varsa (1986: Manisa 1 ve 2) il satirinda toplanir;
    cevre satirlari kaynak bilgisinde aynen kalir."""
    gruplar = {}
    for r in iller:
        gruplar.setdefault(r["plaka"], []).append(r)
    for plaka, rs in gruplar.items():
        if len(rs) == 1:
            yield rs[0]
            continue
        top = {"il": rs[0]["il"], "plaka": plaka, "oy": {},
               "secimCevresi": " + ".join(str(r.get("secimCevresi")) for r in rs),
               "kaynak": {"cevreler": rs}}
        for alan in ("secmen", "oyKullanan", "gecerliOy", "gecersizOy", "muteber", "sandik"):
            vals = [r.get(alan) for r in rs]
            top[alan] = sum(vals) if all(v is not None for v in vals) else None
        for r in rs:
            for p, o in (r.get("oy") or {}).items():
                top["oy"][p] = top["oy"].get(p, 0) + (o or 0)
        yield top


def ara_secimler(y):
    n_secim = n_belde = 0
    ana_esle = {"2009yenileme_belediye_baskanligi": "2009yerel", "2019istanbul_bb_yenileme": "2019yerel",
                "2024yenileme_belediye_baskanligi": "2024yerel", "2024yenileme_belediye_meclisi": "2024yerel_bm"}
    for p in sorted((EK / "yenileme_ara").glob("*.json")):
        d = oku(p)
        sid = p.stem
        oylama = ("milletvekili" if "mv_ara" in sid else
                  "belediye_meclisi" if "meclisi" in sid else "baskanlik")
        tarih = re.match(r"\d{1,2} \S+ \d{4}", d.get("aciklama") or "")
        y.secim(sid, "ara", oylama, tarih.group() if tarih else str(yil_of(sid)),
                ana=ana_esle.get(sid), aciklama=d.get("aciklama"))
        for r in il_cevrelerini_birlestir(d.get("iller") or []):
            r2, notu = dogrulanmis(r)
            if r.get("secimCevresi"):
                notu = " | ".join(x for x in (f"Seçim çevresi: {r['secimCevresi']}", notu) if x)
            y.sonuc_il(sid, "ara", r["plaka"], r["il"], r2, notu=notu)
            for ri in r.get("ilceler") or []:
                if ri.get("geomId"):
                    r3, notu3 = dogrulanmis(ri)
                    y.sonuc_ilce(sid, "ara", ri["geomId"], r["plaka"], ri["ilce"], r3, notu=notu3)
        for r in d.get("birimler") or []:
            if r.get("beldeId") or r.get("belde"):
                belde(y, sid, r["plaka"], r, ilce_ad=r.get("ilce"), belde_ad=r.get("belde"), kaynak="ysk",
                      ilce_id=r.get("geomId"), belde_kod=r.get("beldeId"), kazanan=r.get("kazanan"),
                      oy=r.get("oy"))
                n_belde += 1
            else:
                y.sonuc_ilce(sid, "ara", r["geomId"], r["plaka"], r["ilce"], r)
        kapsam(y, sid, "yenileme_ara", aciklama=d.get("duzey"), ayrinti=d.get("ozet"))
        n_secim += 1
    return f"ara/yenileme: {n_secim} oylama, {n_belde} belde"


def beldeler(y):
    n = eslesen = tuik = 0
    for p in sorted((EK / "beldeler").glob("*.json")):
        d = oku(p)
        sid = d["secim"] if d["secim"] in y.secimler else p.stem
        for k in d["kayitlar"]:
            t = k.get("tuik")
            if t:
                r, oy, kaynak, sadece = t, t.get("oy"), "tuik", False
                tuik += 1
            else:
                r = {}
                oy = {k["kazanan"]: k.get("oy")} if k.get("kazanan") else {}
                kaynak, sadece = "wikipedia", True
            eslesen += belde(y, sid, k["plaka"], r, ilce_ad=k.get("ilce"), belde_ad=k["belde"], kaynak=kaynak,
                             aday=k.get("aday"), kazanan=k.get("kazanan"), oy=oy, sadece_kazanan=sadece,
                             kaynak_bilgi=k.get("kaynak"))
            n += 1
        c = d.get("kapsam") or {}
        kapsam(y, sid, "beldeler", c.get("bulunan"), c.get("beklenen"), c.get("durum"), c.get("not"), c)
    return f"belde başkanlığı: {n:,} kayıt ({tuik:,} tam oylu, TÜİK), {eslesen:,} ilçeye bağlandı"


def belediye_meclisi_beldeleri(y):
    n = eslesen = 0
    for p in sorted((EK / "belediye_meclisi").glob("*.json")):
        d = oku(p)
        sid = f"{p.stem}_bm"
        for r in d["birimler"]:
            if not (r.get("tip") == "belde" or r.get("beldeId") is not None or r.get("belde")):
                continue
            ysk = r.get("yskIlceId") is not None
            eslesen += belde(
                y, sid, r["plaka"], r, ilce_ad=r.get("ilce") or r.get("ustIlce"),
                belde_ad=r.get("belde") or r.get("ad") or r.get("adKaynakta"),
                ilce_id=r.get("geomId"), belde_kod=r.get("beldeId"), kaynak="ysk" if ysk else "tuik",
                kazanan=r.get("kazanan"), oy=r.get("oy"), kontrol=(r.get("kontrol") or {}).get("durum"),
                kaynak_bilgi={"sayfa": r.get("sayfa"), "adKaynakta": r.get("adKaynakta")} if not ysk else None)
            n += 1
        kapsam(y, sid, "belediye_meclisi", aciklama=d.get("aciklama"), ayrinti=d.get("ozet"))
    for p in sorted((EK / "il_genel_meclisi").glob("*.json")):
        d = oku(p)
        kapsam(y, f"{p.stem}_igm", "il_genel_meclisi", aciklama=d.get("aciklama"), ayrinti=d.get("ozet"))
    return f"belediye meclisi beldeleri: {n:,} kayıt, {eslesen:,} ilçeye bağlandı"


def meclis_2024(y):
    d = oku(DATA / "meclis_2024.json")
    satir = [("2024yerel_bm", iid, y.sec.id(parti), s) for iid, v in d.items() for parti, s in v["partiler"].items() if s]
    y.con.executemany("INSERT INTO sandalye_ilce VALUES (?,?,?,?)", satir)
    return f"2024 belediye meclisi üye dağılımı: {len(d)} ilçe, {sum(s for *_, s in satir):,} üye"


def yukle(y):
    return [milletvekilleri(y), senato(y), ara_secimler(y), beldeler(y), belediye_meclisi_beldeleri(y),
            meclis_2024(y)]
