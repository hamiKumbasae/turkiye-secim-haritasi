"""
Istanbul'un 1961-1992 arasindaki ilce sinirlarini (3806 sayili Kanundan once) bosluksuz kurar ve
bu donemin secimlerini o sinirlara baglar. build_istanbul_1992_2008.py'nin geriye dogru devami.

Donemler (Istanbul'da ilce kuran kanunlar):
  309  (RG 04.09.1963)  Gaziosmanpasa <- Eyup
  3392 (RG 04.07.1987)  Buyukcekmece <- Catalca; Kucukcekmece <- Bakirkoy; Pendik <- Kartal;
                        Umraniye <- Uskudar + Beykoz; Kagithane
  3644 (RG 20.05.1990)  Bayrampasa <- Eyup
  3806 (RG 03.06.1992)  Avcilar, Bagcilar, Bahcelievler, Gungoren, Maltepe, Sultanbeyli, Tuzla
  3949 (RG 29.12.1993)  Esenler
  5747 (RG 22.03.2008)  Arnavutkoy, Atasehir, Basaksehir, Beylikduzu, Cekmekoy, Esenyurt, Sancaktepe,
                        Sultangazi

Yontem (tahmin yok; her atama kaynakli, cikarimlar ayrica isaretli):
  1. Her bugunku ilce ya butunuyle tek bir eski ilceye aittir (ZINCIR: kanun ek listesi ya da
     nufus sayimi zinciri; dayanagi yazili), ya da mahalle mahalle atanir. Mahalle tablosu
     geo/historical/idari/istanbul_1961_1992_mahalle.json: 2008'de kurulan ilceler (1961-1992) ile
     Kagithane ve Umraniye (1961-1987); her mahallenin donem donem ilcesi ve dayanagi. 1992-2008
     arasi build_istanbul_1992_2008.py'nin tablosundan gelir.
  2. Secim tarihindeki ilce secimde ayri satir degilse (kurulmus ama secime ayri girmemis: 1987
     genel ve referandumunda 3392 ilceleri, 1988 referandumunda Kucukcekmece ve Pendik) birim,
     o ilcenin kurulusundan bir gun onceki ilcesinin satirina katilir.
  3. Bir bugunku ilcenin tek bir mahallesinin bile o tarihteki ilcesi belirsizse bugunku ilce o
     secimde tarali kalir (hicbir satira katilmaz).
  4. Mahalle poligonlari (geo/normalized/mahalle_geo.json) bugunku ilceye kirpilir, bosluk en
     yakin mahallenin satirina verilir (build_istanbul_1992_2008.paylastir); parcalarin birlesimi
     bugunku ilce poligonuna esittir.
  5. Her satirin poligonu = ona dusen butun bugunku ilceler + parcalar. Tek bir bugunku ilceye
     esit olan satir bugunku id'sini korur; digerleri HIST-Istanbul-<Ad>-<bilesim ozeti> alir
     (ayni bilesim her secimde ayni id).
  6. Yalniz geo/historical/idari/ilce_bolusumu.json -> uygulananSecimler'deki secimler baglanir
     (secimler 2002'den geriye tek tek acilir); digerlerinin satirlari degismez.

Kapsam disi: 1963-1977 yerel secimleri (Istanbul il merkezi belediyesi satiri, HISTY-*; koyler
belediye secimine girmez) ve Yalova satiri (1995'te il oldu; il katmaninda).

Ciktilar:
  geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson (HIST-Istanbul-<Ad>-<yil>)
  geo/historical/district_splits.json (hideIds)
  geo/historical/idari/istanbul_1961_1992.json (secim secim satir bilesimleri, tarali ilceler)
  data/normalized/elections (Istanbul satirlarinin geomId'si; oy degismez)

Sonra: apply_idari_merges.py (harita notlari), build_meclis_harita.py (1984/1989 meclis kayitlari
baskanlik satirlarinin geomId'sini alir), scripts/build.py.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/build_istanbul_1961_1992.py
"""
import datetime
import hashlib
import json
import pathlib
import re
import sys

import shapely
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
import build_istanbul_1992_2008 as b9208  # noqa: E402
from common.election_io import load_election, save_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
TABLO = IDARI / "istanbul_1961_1992_mahalle.json"
KAYIT = IDARI / "istanbul_1961_1992.json"
MODERN, MAHALLE_GEO, HIST_GEO, SPLITS = b9208.MODERN, b9208.MAHALLE_GEO, b9208.HIST_GEO, b9208.SPLITS
PLAKA = 34
BASLANGIC = "1961-01-01"
DONEM9208 = ("1992-06-03", "2008-03-22")
KIMLIK = re.compile(r"^HIST-Istanbul-[A-Za-z]+-[0-9a-f]{6}$")
UYGULANAN = IDARI / "ilce_bolusumu.json"

# secim -> tarih (meclis kayitlari build_meclis_harita.py ile baskanlik satirlarindan kurulur)
SECIMLER = {
    "1961referandum": "1961-07-09", "1961": "1961-10-15", "1965": "1965-10-10", "1969": "1969-10-12",
    "1973": "1973-10-14", "1977": "1977-06-05", "1982referandum": "1982-11-07", "1983": "1983-11-06",
    "1984yerel": "1984-03-25", "1987referandum": "1987-09-06", "1987": "1987-11-29",
    "1988referandum": "1988-09-25", "1989yerel": "1989-03-26", "1991": "1991-10-20",
}

# 1961'den sonra kurulan ilceler: kurulus tarihi (ilce secimde ayri satir degilse birim bir gun
# onceki ilcesine gider)
KURULUS = {
    "Gaziosmanpaşa": "1963-09-04", "Büyükçekmece": "1987-07-04", "Küçükçekmece": "1987-07-04",
    "Pendik": "1987-07-04", "Ümraniye": "1987-07-04", "Kağıthane": "1987-07-04", "Bayrampaşa": "1990-05-20",
    "Avcılar": "1992-06-03", "Bağcılar": "1992-06-03", "Bahçelievler": "1992-06-03", "Güngören": "1992-06-03",
    "Maltepe": "1992-06-03", "Sultanbeyli": "1992-06-03", "Tuzla": "1992-06-03", "Esenler": "1993-12-29",
}
# satiri olmayan eski ilce (kurulus disi): 1984 yerelde Eminonu satiri yok, alan Fatih'te kalir
SATIRSIZ = {"Eminönü": "Fatih"}

K = "{} sayılı Kanun ek ({}) sayılı liste"
AUDIT = "geo/historical/NATIONWIDE_DISTRICT_AUDIT.md (3806 dalgası: kaymakamlık tarihçeleri)"
SAYIM = "geo/historical/idari/sayim_kaniti.json (DİE 1960/1985/1990 GNS köy bağlılığı)"
# butunuyle tek eski ilceye bagli bugunku ilceler: kod -> [(baslangic, bitis, ilce, dayanak)];
# son bitis kurulus tarihidir (ondan sonra kendisi)
ZINCIR = {
    "004": [(BASLANGIC, "1987-07-04", "Bakırköy", "Küçükçekmece'nin parçası (3392 öncesi): " + SAYIM),
            ("1987-07-04", "1992-06-03", "Küçükçekmece",
             K.format(3392, 49) + ": Avcılar (Merkez), Ambarlı, Firuz, Gümüşpala, Cihangir Denizköşkler, "
             "Mustafa Kemalpaşa, Üniversite (3806 ek (1) Avcılar listesinin 8 mahallesi)")],
    "005": [(BASLANGIC, "1992-06-03", "Bakırköy", "3806 ek (2); " + AUDIT + "; 3392 Küçükçekmece listesinde yok")],
    "006": [(BASLANGIC, "1992-06-03", "Bakırköy", "3806 ek (4); " + AUDIT + "; 3392 Küçükçekmece listesinde yok")],
    "009": [(BASLANGIC, "1990-05-20", "Eyüp", K.format(3644, 56) + ": 11 mahallenin tamamı Eyüp Belediyesinden")],
    "014": [(BASLANGIC, "1987-07-04", "Çatalca", K.format(3392, 50) + ": Çatalca'nın Büyükçekmece bucağındaki 14 köy "
                                                 "ve bucak merkezi")],
    "017": [(BASLANGIC, "1992-06-03", "Bakırköy",
             "3949 ek (3) Esenler mahalleleri 3806 ek (3) Güngören listesinde 'Esenler Bölgesi' olarak var; Güngören "
             "Bakırköy'den (" + AUDIT + "); 3392 Küçükçekmece listesinde yok"),
            ("1992-06-03", "1993-12-29", "Güngören", "3806 ek (3) sayılı liste")],
    "021": [(BASLANGIC, "1963-09-04", "Eyüp", K.format(309, 1) + ": Eyüp'ün Göktepe bucağı köyleri")],
    "022": [(BASLANGIC, "1992-06-03", "Bakırköy", "3806 ek (3); " + AUDIT)],
    "026": [(BASLANGIC, "1987-07-04", "Bakırköy", SAYIM)],
    "027": [(BASLANGIC, "1992-06-03", "Kartal", "3806 ek (5); " + AUDIT)],
    "028": [(BASLANGIC, "1987-07-04", "Kartal", K.format(3392, 48) + ": köyler Kartal'dan; " + SAYIM)],
    "032": [(BASLANGIC, "1992-06-03", "Kartal", "3806 m. 1/6 (merkezi Sultanbeyli kasabası); " + AUDIT +
             "; DİE 1960/1985/1990 GNS: Sultanbeyli Kartal Şamandıra bucağında")],
    "036": [(BASLANGIC, "1987-07-04", "Kartal", "Pendik'in parçası (3392 öncesi): " + SAYIM),
            ("1987-07-04", "1992-06-03", "Pendik",
             K.format(3392, 48) + ": Tuzla, Aydınlı, Aydıntepe, İçmeler, Şifa, Esenyalı; 3806 ek (6) Tuzla listesi")],
}
# mahalle tablosu kapsamindan sonra kendi adini alan ilceler (1987'de kurulan, mahalle tablosu 1961-1987)
SONRA_KENDISI = {"024": "Kağıthane", "037": "Ümraniye"}

KM2 = b9208.KM2


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def gun_once(t):
    return (datetime.date.fromisoformat(t) - datetime.timedelta(days=1)).isoformat()


def ascii_ad(ad):
    return ad.translate(str.maketrans("İıĞğÜüŞşÖöÇçÂâ", "IiGgUuSsOoCcAa"))


class Atama:
    """bugunku ilce + mahalle -> t tarihindeki ilce (None: belirsiz)."""

    def __init__(self, mahalle_geo):
        self.tablo = oku(TABLO)["ilceler"] if TABLO.exists() else {}
        self.ad = {g: {k: v["ad"] for k, v in mahalle_geo[g].items()} for g in mahalle_geo if g.startswith("TR-D-34-")}
        self.kod_ad = {k: a for a, k in b9208.ILCELER.items() if k}
        fatih = sorted({v for v in self.ad["TR-D-34-020"].values()})
        self.m9208 = dict(b9208.MAHALLE)
        self.m9208["020"] = {m: ("Eminönü" if m in b9208.EMINONU else "Fatih", b9208.FATIH_DAYANAK) for m in fatih}
        # tablo: mahalle anahtari -> donemler / belirsiz
        self.don = {}
        for g, k in self.tablo.items():
            d = {}
            for m in k["mahalleler"]:
                d[m["id"].removeprefix("mg:")] = [(x["baslangic"], x["bitis"], x["ilce"]) for x in m["donemler"]]
            for b in k.get("belirsiz", []):
                d.setdefault(b["id"].removeprefix("mg:"), []).append((b["baslangic"], b["bitis"], None))
            self.don[g] = d

    def mahalle_duzeyi(self, g):
        kod = g[-3:]
        return g in self.tablo or kod in self.m9208

    def ilce(self, g, anahtar, t):
        """anahtar: mahalle_geo anahtari (mahalle duzeyindeki ilceler) ya da None (butun)."""
        kod = g[-3:]
        if g in self.tablo and t < self.tablo[g]["bitis"]:
            aralik = [x for x in self.don[g].get(anahtar, []) if x[0] <= t < x[1]]
            if len(aralik) != 1:
                raise SystemExit(f"HATA {g} {anahtar} {t}: tabloda {len(aralik)} donem")
            return aralik[0][2]
        if kod in ZINCIR and t < ZINCIR[kod][-1][1]:
            return next(x[2] for x in ZINCIR[kod] if x[0] <= t < x[1])
        if kod in SONRA_KENDISI:
            return SONRA_KENDISI[kod]
        if kod in self.m9208 and (kod == "020" or DONEM9208[0] <= t < DONEM9208[1]):
            return self.m9208[kod][self.ad[g][anahtar]][0]
        if kod in b9208.BUTUN and DONEM9208[0] <= t < DONEM9208[1]:
            return b9208.BUTUN[kod][0]
        if kod in self.kod_ad and KURULUS.get(self.kod_ad[kod], BASLANGIC) <= t:
            return self.kod_ad[kod]
        return None  # kaynakli atama yok: tarali


def main():
    modern = {f["properties"]["id"]: b9208.temiz(shape(f["geometry"])) for f in oku(MODERN)["features"]
              if f["properties"]["id"].startswith("TR-D-34-")}
    mahalle_geo = oku(MAHALLE_GEO)
    atama = Atama(mahalle_geo)
    mgeom = {}

    def mahalleler(g):
        if g not in mgeom:
            mgeom[g] = {k: b9208.temiz(shape(v["geometry"])) for k, v in sorted(mahalle_geo[g].items())}
        return mgeom[g]

    parca_bellek = {}

    def parcalar(g, etiketler):
        """etiketler: {mahalle anahtari: satir adi} -> {satir adi: poligon}"""
        anahtar = (g, tuple(sorted(etiketler.items())))
        if anahtar not in parca_bellek:
            ms = mahalleler(g)
            bol = b9208.paylastir(modern[g], {k: (etiketler[k], ms[k]) for k in sorted(etiketler)})
            fark = unary_union(list(bol.values())).symmetric_difference(modern[g]).area / modern[g].area
            assert fark < 1e-6, (g, fark)
            parca_bellek[anahtar] = bol
        return parca_bellek[anahtar]

    uygulanan = set(oku(UYGULANAN).get("uygulananSecimler", [])) if UYGULANAN.exists() else set()
    secimler = {a: t for a, t in SECIMLER.items() if a in uygulanan}
    if not secimler:
        print("Istanbul 1961-1991 secimlerinden hicbiri uygulanmiyor; degisiklik yok")
        return
    kayitlar = {a: load_election(a) for a in secimler}
    sonuc, bilesim_id, uretilen = {}, {}, {}
    for secim, tarih in secimler.items():
        satirlar = {fold(r["ad"]): r["ad"] for r in kayitlar[secim]["ilceler"]
                    if r.get("plaka") == PLAKA and r["ad"] != "Yalova" and not r["ad"].startswith("İstanbul")}

        def satir(g, anahtar):
            t = tarih
            for _ in range(4):
                il = atama.ilce(g, anahtar, t)
                if il is None:
                    return None
                if fold(il) in satirlar:
                    return satirlar[fold(il)]
                if il in KURULUS and KURULUS[il] <= t:
                    t = gun_once(KURULUS[il])  # kurulmus ama secime ayri girmemis
                    continue
                if il in SATIRSIZ and fold(SATIRSIZ[il]) in satirlar:
                    return satirlar[fold(SATIRSIZ[il])]
                raise SystemExit(f"HATA {secim} {g} {anahtar}: '{il}' satiri yok")
            raise SystemExit(f"HATA {secim} {g} {anahtar}: zincir")

        # her bugunku ilce: butun (satir adi) ya da mahalle etiketleri; belirsizse tarali
        bilesenler, tarali = {}, {}
        for g in sorted(modern):
            if atama.mahalle_duzeyi(g):
                et = {k: satir(g, k) for k in mahalleler(g)}
                bos = sorted(atama.ad[g][k] for k, v in et.items() if v is None)
                if bos:
                    tarali[g] = bos
                    continue
                if len(set(et.values())) == 1:
                    bilesenler.setdefault(next(iter(et.values())), []).append((g, None))
                else:
                    for s in sorted(set(et.values())):
                        bilesenler.setdefault(s, []).append((g, et))
            else:
                s = satir(g, None)
                if s is None:
                    tarali[g] = ["(bütün ilçe)"]
                    continue
                bilesenler.setdefault(s, []).append((g, None))

        secim_sonuc = {}
        for s, bs in sorted(bilesenler.items()):
            if len(bs) == 1 and bs[0][1] is None:
                secim_sonuc[s] = {"geomId": bs[0][0], "bugunkuIlceler": [bs[0][0]]}
                continue
            if s in b9208.SABIT_ID and [g for g, _ in bs] == ["TR-D-34-020"]:
                # Eminonu/Fatih: 1961-2008 ayni sinir (split_eminonu_fatih.py poligonlari)
                secim_sonuc[s] = {"geomId": b9208.SABIT_ID[s], "bugunkuIlceler": ["TR-D-34-020"]}
                continue
            imza = json.dumps([[g, sorted(et.items()) if et else None] for g, et in bs] + [s], ensure_ascii=False)
            if imza not in bilesim_id:
                sid = f"HIST-Istanbul-{ascii_ad(s).replace(' ', '')}-{hashlib.sha1(imza.encode()).hexdigest()[:6]}"
                geoms, paylar = [], {}
                for g, et in bs:
                    if et is None:
                        geoms.append(modern[g])
                    else:
                        p = parcalar(g, et)[s]
                        geoms.append(p)
                        paylar[g] = round(p.area / modern[g].area, 4)
                ids = sorted(g for g, _ in bs)
                u = unary_union(geoms)
                yabanci = unary_union([v for k, v in modern.items() if k not in ids])
                u = delikleri_doldur(u, bilesen_delikleri([modern[i] for i in ids]), yabanci)
                u = shapely.set_precision(u, 1e-5)
                bilesim_id[imza] = sid
                uretilen[sid] = {"geom": u, "ids": ids, "paylar": paylar, "ad": s,
                                 "mahalleler": {g: sorted(atama.ad[g][k] for k, v in et.items() if v == s)
                                                for g, et in bs if et}, "secimler": []}
            sid = bilesim_id[imza]
            uretilen[sid]["secimler"].append(secim)
            secim_sonuc[s] = {"geomId": sid, "bugunkuIlceler": uretilen[sid]["ids"]}
        sonuc[secim] = {"tarih": tarih, "satirlar": secim_sonuc,
                        "tarali": {g: m for g, m in sorted(tarali.items())}}
        print(secim, len(secim_sonuc), "satir;", "tarali:", ", ".join(sorted(tarali)) or "yok")

    # yaz: geometri
    hist = oku(HIST_GEO)
    feats = {f["properties"]["id"]: f for f in hist["features"] if not KIMLIK.match(f["properties"]["id"])}
    for sid, u in sorted(uretilen.items()):
        feats[sid] = {"type": "Feature", "properties": {"id": sid, "plaka": PLAKA}, "geometry": mapping(u["geom"])}
    hist["features"] = sorted(feats.values(), key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    splits = oku(SPLITS)
    sp = [e for e in splits[str(PLAKA)] if not KIMLIK.match(e["syntheticId"])]
    for sid, u in sorted(uretilen.items()):
        sonra = min((k for k in KURULUS.values() if k > secimler[u["secimler"][-1]]), default="2008")
        sp.append({"hideIds": u["ids"], "splitYear": int(sonra[:4]), "syntheticId": sid})
    splits[str(PLAKA)] = sp
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")

    # secim satirlari
    def bagla(rec, s_sonuc):
        degisen = []
        for r in rec["ilceler"]:
            if r.get("plaka") != PLAKA or r["ad"] not in s_sonuc:
                continue
            yeni = s_sonuc[r["ad"]]["geomId"]
            if r.get("geomId") != yeni:
                degisen.append(f"{r['ad']}: {r.get('geomId')} -> {yeni}")
                r["geomId"] = yeni
        return degisen

    for secim, rec in kayitlar.items():
        d = bagla(rec, sonuc[secim]["satirlar"])
        if d:
            save_election(secim, rec)

    KAYIT.write_text(json.dumps({
        "not": "build_istanbul_1961_1992.py ile üretilir; elle düzenlenmez.",
        "yontem": __doc__.split("Yontem")[1].split("Kapsam disi")[0].strip(),
        "zincir": {f"TR-D-34-{k}": [{"baslangic": a, "bitis": b, "ilce": i, "dayanak": d} for a, b, i, d in v]
                   for k, v in ZINCIR.items()},
        "sentetikler": {sid: {"ad": u["ad"], "bugunkuIlceler": u["ids"], "paylar": u["paylar"],
                              "mahalleler": u["mahalleler"], "secimler": u["secimler"],
                              "alanKm2": round(u["geom"].area * KM2, 1)} for sid, u in sorted(uretilen.items())},
        "secimler": sonuc,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi:", KAYIT.relative_to(ROOT), len(uretilen), "sentetik")


if __name__ == "__main__":
    main()
