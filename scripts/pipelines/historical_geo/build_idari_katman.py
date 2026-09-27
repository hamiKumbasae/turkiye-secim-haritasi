"""
Tarihsel idari cografya katmani - FAZ 1 (kurulus olaylari + secim kaniti).

Girdiler:
  data/kaynaklar/icisleri/il_ilce_kurulus_2018.json   Icisleri kurulus listesi (resmi)
  data/raw/ysk/acikveri-il-ilce-listesi.json          guncel il/ilce adlari (YSK)
  data/raw/ysk/acikveri-ilce-geomid-eslemesi.json     YSK ilce -> geomId
  data/secim_takvimi.json                             secim tarihleri
  data/normalized/elections/*/*.json                  secimlerdeki ilce satirlari (kanit)
  geo/historical/district_splits.json                 repoda dogrulanmis HIST-* birlesimleri
  geo/historical/metro_merkez_1961_1987.json          (kanun/kaynak ayrintisi)
  geo/historical/idari/elle_olaylar.json              kaynakli elle olaylar (Kirsehir 1954-1957 vb.)

Ciktilar (geo/historical/idari/):
  administrative_events.json      her idari olay bir kayit
  district_lineage.json           her guncel ilcenin (geomId) tarihsel kaydi
  election_admin_snapshots.json   her secim tarihindeki idari yapi (URETILIR, elle duzenlenmez)
  faz1_rapor.json                 tutarlilik denetimi

Kurallar:
  - Tahmin yok. Soy (hangi eski ilceden ayrildi) kaynakta yoksa
    lineageStatus = "unresolved"; modern sinir gecmise tasinmaz.
  - Kanun tarihi secim etkisi DEGILDIR: 3392 sayili Kanunla 04.07.1987'de
    kurulan ilceler 29.11.1987 secimine ayri girmedi. Her birim icin ilce
    duzeyli secimlerden (genel, referandum, cumhurbaskanligi) `ilkSecim`
    ayrica tutulur. Yerel secim satirlari ilce degil BELEDIYEDIR (buyuksehir
    alt kademe belediyeleri ilce olmadan once de satir olarak var); ilce
    varligina kanit sayilmaz.
  - Eslestirme ada gore degil geomId'ye gore; ad degisiklikleri ayri olay.
    Yazim farklari ('Samandağ'/'Samandağı', 'Merkez'/'Aydın merkez',
    'Sincanlı (Sinanpaşa)'/'Sinanpaşa') ad degisikligi sayilmaz.

Kullanim:
  python3 scripts/pipelines/historical_geo/build_idari_katman.py
"""
import collections
import difflib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402

IDARI = ROOT / "geo/historical/idari"
AY = {"Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6, "Temmuz": 7, "Ağustos": 8,
      "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12}
ERA_DOSYALARI = ["era1950", "era1954", "era1957_1987", "era1991", "era1995", "era1999"]
ILCE_DUZEYLI = {"genel", "referandum", "cumhurbaskanligi"}
BASLANGIC = "0000-00-00"


def oku(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def yaz(ad, veri, girinti=None):
    (IDARI / ad).write_text(json.dumps(veri, ensure_ascii=False, indent=girinti,
                                       separators=None if girinti else (",", ":")), encoding="utf-8")


def anahtar(ad):
    """Ad karsilastirmasi: fold + parantez ici ve bosluk atilir ('Aziziye (Ilıca)' -> 'AZIZIYE')."""
    return fold(re.sub(r"\(.*?\)", "", ad or "")).replace(" ", "")


def ad_takmalari(ad, il_adi):
    """Bir satir adinin karsilastirma bicimleri: parantez disi ve ici ayri;
    il adi + 'merkez' -> 'MERKEZ'."""
    out = set()
    parcalar = [re.sub(r"\(.*?\)", "", ad)] + re.findall(r"\((.*?)\)", ad)
    for p in parcalar:
        a = fold(p).replace(" ", "").replace("19MAYIS", "ONDOKUZMAYIS")
        il = fold(il_adi).replace(" ", "")
        if a.endswith("MERKEZ") and a[:-6] in ("", il):
            a = "MERKEZ"
        if a:
            out.add(a)
    return out


def ayni_ad(a, b):
    if a & b:
        return True
    return any(difflib.SequenceMatcher(None, x, y).ratio() >= 0.85 for x in a for y in b)


# --- secim tarihleri ------------------------------------------------------------
def _tarihler(metin):
    """'13 Ağustos - 15 Ekim 1950 (3 aşamalı)' -> ('1950-08-13', '1950-10-15')."""
    t = re.sub(r"\(.*?\)", "", metin).strip()
    yil = re.search(r"(\d{4})\s*$", t).group(1)
    out = []
    for p in (p.strip() for p in t.split(" - ")):
        m = re.match(r"(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?", p)
        out.append(f"{m.group(3) or yil}-{AY[m.group(2)]:02d}-{int(m.group(1)):02d}")
    return out[0], out[-1]


def secimler():
    out = []
    for s in oku("data/secim_takvimi.json")["ana_kategoriler"]:
        bas, son = _tarihler(s["tarih"])
        tur = s["tur"]
        out.append({"anahtar": s["veri_anahtari"].split(".", 1)[1],
                    "tur": "cumhurbaskanligi" if tur.startswith("cumhurba") else tur,
                    "tarih": son, "tarihAraligi": [bas, son] if bas != son else None, "takvimMetni": s["tarih"]})
    return sorted(out, key=lambda s: (s["tarih"], s["anahtar"]))


# --- guncel birimler ------------------------------------------------------------------
def guncel_birimler():
    liste = oku("data/raw/ysk/acikveri-il-ilce-listesi.json")
    esle = {**oku("data/raw/ysk/acikveri-ilce-geomid-eslemesi.json"), **GEOMID_EK}
    il_plaka, il_adi, ilceler = {}, {}, {}
    for pl, v in liste.items():
        il_plaka[anahtar(v["il_ADI"])] = int(pl)
        il_adi[int(pl)] = v["il_ADI"]
        for i in v["ilceler"]:
            g = esle.get(f"{pl}-{i['ilce_ID']}")
            if g:
                ilceler[g] = {"plaka": int(pl), "ad": i["ilce_ADI"], "il": v["il_ADI"]}
    il_plaka.update({anahtar("AFYON"): 3, anahtar("İÇEL"): 33})
    return il_plaka, il_adi, ilceler


# Icisleri 2018 adi -> guncel YSK adi (2018 sonrasi ad degisiklikleri)
AD_GUNCEL = {("İSTANBUL", "EYÜP"): "EYÜPSULTAN"}
# YSK geomId eslemesinde eksik guncel ilceler: poligon ve secim satirlari (1991-2007
# 'Aydınlar', yerel 'Aydınlar (Tillo)') ayni geomId'yi kullaniyor
GEOMID_EK = {"56-771": "TR-D-56-007"}


# --- secim kaniti --------------------------------------------------------------------------
def histk_tabanlari():
    """apply_idari_merges.py'nin sentetikleri (HISTK-*) -> taban geomId. Bu katman kaynak
    kanitini anlatir; haritaya yansitma (HISTK) bu katmandan uretildigi icin geri okunmaz."""
    p = ROOT / "geo/historical/idari/merge_plan.json"
    if not p.exists():
        return {}
    return {sid: e["taban"] for sid, e in json.loads(p.read_text(encoding="utf-8"))["sentetikler"].items()}


def secim_kaniti(secim_listesi):
    """ilce duzeyli secimlerden {geomId: [(tarih, anahtar, ad, plaka)]};
    tum secimlerden {anahtar: {iller, ilceler}}. HISTK satirlari tabanlariyla okunur."""
    taban = histk_tabanlari()
    gorunum = collections.defaultdict(list)
    satirlar = {}
    for s in secim_listesi:
        try:
            kayit = load_election(s["anahtar"])
        except FileNotFoundError:
            continue
        il_satir = collections.defaultdict(list)
        for r in kayit.get("ilceler") or []:
            if (r.get("geomId") or "") in taban:
                r = dict(r, geomId=taban[r["geomId"]])
            il_satir[r["plaka"]].append({"ad": r["ad"], "geomId": r.get("geomId")})
            if r.get("geomId") and s["tur"] in ILCE_DUZEYLI:
                gorunum[r["geomId"]].append((s["tarih"], s["anahtar"], r["ad"], r["plaka"]))
        satirlar[s["anahtar"]] = {"iller": sorted({r["plaka"] for r in kayit.get("iller") or []}),
                                  "ilceler": dict(il_satir)}
    return gorunum, satirlar


def ad_gruplari(gor, il_adi, guncel_il=""):
    """Ayni birimin yazim farklarini tek grupta toplar. Dondurur [{ad, adVaryantlari, ilk, son}]
    (grup sirasi ilk gorunuse gore)."""
    gruplar = []
    for t, k, ad, pl in sorted(gor):
        tk = ad_takmalari(ad, il_adi.get(pl, ""))
        if guncel_il and tk & ad_takmalari(guncel_il, guncel_il) - {"MERKEZ"} or tk & ad_takmalari(guncel_il + " merkez", guncel_il):
            # il olmadan onceki adi il adi olan merkez ilce ('Aksaray' -> 'Merkez')
            tk = tk | {"MERKEZ"}
        g = next((g for g in gruplar if ayni_ad(g["_t"], tk)), None)
        if g is None:
            gruplar.append({"_t": set(tk), "ad": ad, "adVaryantlari": [ad], "ilk": k, "son": k, "ilkTarih": t, "sonTarih": t})
        else:
            g["_t"] |= tk
            g["son"], g["sonTarih"] = k, t
            if ad not in g["adVaryantlari"]:
                g["adVaryantlari"].append(ad)
    for g in gruplar:
        g.pop("_t")
    return gruplar


def il_parcalari(gor):
    out = []
    for t, k, ad, pl in sorted(gor):
        if out and out[-1]["plaka"] == pl:
            out[-1]["son"], out[-1]["sonTarih"] = k, t
        else:
            out.append({"plaka": pl, "ilk": k, "son": k, "ilkTarih": t, "sonTarih": t})
    return out


def geometri_kurali(l):
    """Henuz ayri olmayan ilcenin alani nereye katilir:
    merge_into:<id> (repoda dogrulanmis HIST birlesimi ya da kanunla tek kaynakli ayrilma),
    unresolved_multi_parent (birden cok ilceden birim aldi; koy duzeyi cozulmedi),
    unresolved (soy bilinmiyor)."""
    if l["oncekiBirimler"]:
        return "merge_into:" + l["oncekiBirimler"][0]["tarihselBirim"]
    k = l.get("kanunSoyu")
    if k and k["tekKaynak"] and k["eskiIlceler"][0]["geomId"]:
        return "merge_into:" + k["eskiIlceler"][0]["geomId"]
    if k and (k.get("guven") == "orta" or not any(e["ad"] for e in k["eskiIlceler"])):
        return "unresolved"
    if k:
        return "unresolved_multi_parent"
    return "unresolved"


# --- ana ------------------------------------------------------------------------------------
def main():
    secim_listesi = secimler()
    tarih_of = {s["anahtar"]: s["tarih"] for s in secim_listesi}
    il_plaka, il_adi, guncel = guncel_birimler()
    ic = oku("data/kaynaklar/icisleri/il_ilce_kurulus_2018.json")
    elle = oku("geo/historical/idari/elle_olaylar.json")
    splits = oku("geo/historical/district_splits.json")
    metro = {m["syntheticId"]: m for m in oku("geo/historical/metro_merkez_1961_1987.json")}
    gorunum, satirlar = secim_kaniti(secim_listesi)
    ilce_secimleri = [s for s in secim_listesi if s["tur"] in ILCE_DUZEYLI and satirlar.get(s["anahtar"], {}).get("ilceler")]

    # --- Icisleri kayitlarini geomId'ye bagla
    ad_geom = collections.defaultdict(list)
    merkez_geom = {}
    for g, v in guncel.items():
        ad_geom[(v["plaka"], anahtar(v["ad"]))].append(g)
        if "MERKEZ" in ad_takmalari(v["ad"], v["il"]):
            merkez_geom[v["plaka"]] = g
    il_kurulus, ilce_kurulus, eslesmeyen = {}, {}, []
    for k in ic["kayitlar"]:
        pl = il_plaka.get(anahtar(k["il"]))
        if pl is None:
            eslesmeyen.append({"il": k["il"], "ad": k["ad"], "neden": "il adı tanınmadı"})
            continue
        if k["tur"] == "il":
            il_kurulus[pl] = k
            if pl in merkez_geom:
                # il satiri merkez ilcenin kurulusu ancak il 1923 oncesinden varsa;
                # sonradan il olan yerlerde merkez ilce ilden once baska ile bagli ilceydi
                ilce_kurulus[merkez_geom[pl]] = dict(k, merkezIlce=True) if k["cumhuriyetOncesi"] else \
                    {"merkezIlce": True, "cumhuriyetOncesi": None, "kurulus": None, "kanun": None, "resmiGazete": None,
                     "not": f"İl {k['kurulus']} tarihinde {k['kanun']} ile kuruldu; merkez ilçe il olmadan önce başka ile "
                            "bağlı ilçeydi. İlçe olarak kuruluş tarihi bu kaynakta yok."}
            continue
        ad = AD_GUNCEL.get((k["il"], k["ad"]), k["ad"])
        gs = ad_geom.get((pl, anahtar(ad)), [])
        if len(gs) == 1:
            ilce_kurulus[gs[0]] = dict(k, adGuncel=ad) if ad != k["ad"] else k
        else:
            eslesmeyen.append({"il": k["il"], "ad": k["ad"], "neden": f"{len(gs)} geomId"})

    def il_var_mi(pl, tarih):
        """Il o tarihte var miydi: Icisleri kurulusu + elle olaylar (onceki varlik,
        kaldirilma, yeniden kurulus) tarih sirasiyla."""
        k = il_kurulus.get(pl)
        if k is None:
            return None
        cizelge = [(BASLANGIC if k["cumhuriyetOncesi"] else k["kurulus"], True)]
        for o in elle["olaylar"]:
            if o.get("plaka") == pl and o["unitType"] == "province":
                cizelge.append((o["effectiveDate"] or BASLANGIC, o["eventType"] != "abolished"))
        durum = False
        for d, var in sorted(cizelge):
            if d <= tarih:
                durum = var
        return durum

    # --- repoda dogrulanmis soy: modern geomId -> tarihsel birim(ler)
    bilinen = collections.defaultdict(list)
    for girdiler in splits.values():
        for e in girdiler:
            if e["syntheticId"].startswith(("HISTK-", "HISTY-")):
                continue  # apply_idari_merges.py / ekle_il_merkezi_satirlari.py ciktisi
            m = metro.get(e["syntheticId"], {})
            for h in e["hideIds"]:
                bilinen[h].append({"tarihselBirim": e["syntheticId"], "birlesimParcalari": e["hideIds"],
                                   "bolunmeYili": e["splitYear"], "kural": "union",
                                   "kaynak": "geo/historical/district_splits.json",
                                   **({"kanun": m["law"], "kaynaklar": m["sources"]} if m else {})})

    # --- kanun ek listelerinden soy (Faz 2): yeni ilce geomId -> eski ilce(ler)
    kanunla, tarihsel_kanun, sinir_duzeltmeleri = {}, {}, []
    for f in sorted((ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus").glob("*.json")):
        kd = json.loads(f.read_text(encoding="utf-8"))
        for h in kd.get("digerHukumler", []):
            # kanunun ilce kurmak disindaki hukumleri (7033/2: Kusadasi Izmir -> Aydin)
            sinir_duzeltmeleri.append({"id": f"kanun-{kd['kanun']}-madde-{h['madde']}", "unit": h.get("unit"),
                                       "unitType": "district", "eventType": h["eventType"],
                                       "effectiveDate": h["effectiveDate"], "provinceBefore": h.get("provinceBefore"),
                                       "provinceAfter": h.get("provinceAfter"), "lawNumber": kd["kanun"],
                                       "officialGazette": kd["resmiGazete"], "text": h["metin"],
                                       "source": str(f.relative_to(ROOT)), "confidence": "high"})
        for i in kd["ilceler"]:
            kayit = {"kanun": kd["kanun"], "kanunAdi": kd["ad"], "resmiGazete": kd["resmiGazete"],
                     "listeNo": i["listeNo"], "rgSayfalari": i["rgSayfalari"], "birimSayisi": i["satirSayisi"],
                     "eskiIlceler": [{k: e.get(k) for k in ("ad", "geomId", "plaka", "birimSayisi")} for e in i["eskiIlceler"]],
                     # OCR'da dusen satir varsa tek kaynak kesin degil; 'orta' guvenli okuma
                     # (7033: blok duzeyi, satir denetimi yok) geometri kuralina cevrilmez
                     "tekKaynak": i["tekKaynak"] and not i.get("eksikSira") and i.get("guven") != "orta",
                     **({"guven": i["guven"], "okunanTekKaynak": i["tekKaynak"]} if i.get("guven") else {}),
                     **({"eksikSira": i["eksikSira"]} if i.get("eksikSira") else {}),
                     **({"kaynakYazilmamisBirim": i["kaynakYazilmamisSatir"]} if i.get("kaynakYazilmamisSatir") else {}),
                     "kaynak": str(f.relative_to(ROOT))}
            if i["yeniIlce"] and i["yeniIlce"]["geomId"].startswith("HIST-"):
                # kanunla kurulan birim sonradan bolunmus: kurulus sinirlari repodaki tarihsel
                # poligonda (3392: Pendik, Kucukcekmece, Buyukcekmece, Umraniye, Konak)
                tarihsel_kanun[i["yeniIlce"]["geomId"]] = dict(kayit, ad=i["ad"])
            elif i["yeniIlce"]:
                kanunla[i["yeniIlce"]["geomId"]] = kayit
            if i["ekHukum"]:
                sinir_duzeltmeleri.append({"id": f"kanun-{kd['kanun']}-{i['listeNo']}-ek", "unitType": "district",
                                           "eventType": "boundary_adjustment", "effectiveDate": kd["resmiGazete"]["tarih"],
                                           "lawNumber": kd["kanun"], "officialGazette": kd["resmiGazete"],
                                           "text": i["ekHukum"], "relatedNewDistrict": i["ad"],
                                           "source": str(f.relative_to(ROOT)), "confidence": "high",
                                           "not": "Kanunun aynı bendinde, yeni ilçe kurmanın yanında yapılan köy/belde nakli. "
                                                  "İlçeler arası naklin tarihsel sınıra etkisi köy düzeyinde; geometrisi çözülmedi."})

    # --- district_lineage
    lineage, rapor = [], collections.defaultdict(list)
    for g in sorted(guncel):
        v = guncel[g]
        k = ilce_kurulus.get(g)
        gor = sorted(gorunum.get(g, []))
        adlar = ad_gruplari(gor, il_adi, v["il"])
        iller = il_parcalari(gor)
        ilk = gor[0] if gor else None
        kurulus = k["kurulus"] if k else None
        # kanunla kurulmus ama ilce duzeyli secime ayri girmemis
        girmedi = [s["anahtar"] for s in ilce_secimleri
                   if kurulus and ilk and kurulus <= s["tarih"] < ilk[0] and v["plaka"] in {
                       r_pl for r_pl in satirlar[s["anahtar"]]["ilceler"]}]
        merkez_donusumu = False
        once = [x for x in gor if kurulus and x[0] < kurulus]
        if once:
            onceki_adlar = {a for x in once for a in ad_takmalari(x[2], il_adi.get(x[3], ""))}
            if "MERKEZ" in onceki_adlar:
                # 2008/2012 buyuksehir donusumu: eski "Merkez" ilcesi yeni adla (ayni ya da
                # bolunmus alanla) devam ediyor; Icisleri tarihi kurulus degil donusum tarihi
                merkez_donusumu = True
            elif kurulus >= "2012-01-01" and all(x[0] >= "2010-01-01" for x in once):
                # kaynak (TUIK/YSK) 2010-2011 sonuclarini sonradan kurulan ilcelere gore
                # yeniden toplamis; idari celiski degil
                rapor["kaynakSonrakiIlcelereGoreToplamis"].append(
                    {"geomId": g, "ad": v["ad"], "kurulus": kurulus, "secimler": [x[1] for x in once]})
            else:
                rapor["kurulustanOnceSecimdeGorunuyor"].append(
                    {"geomId": g, "ad": v["ad"], "kurulus": kurulus, "secimler": [x[1] for x in once],
                     "secimdekiAdlar": sorted({x[2] for x in once})})
        son_ilce_secimi = ilce_secimleri[-1]
        if gor and gor[-1][0] < son_ilce_secimi["tarih"] and k:
            eksik = [x["anahtar"] for x in ilce_secimleri if x["tarih"] > gor[-1][0]]
            rapor["secimVerisindenKayboldu"].append(
                {"geomId": g, "ad": v["ad"], "sonGorulen": gor[-1][1], "gorulmedigiSecimler": eksik,
                 "not": "İlçe bugün de mevcut (İçişleri 2018); sonraki seçim verisinde satırı yok — veri boşluğu."})
        if len(adlar) > 1:
            rapor["adDegisikligi"].append({"geomId": g, "adlar": [a["ad"] for a in adlar]})
        if len(iller) > 1:
            rapor["ilDegisikligi"].append({"geomId": g, "ad": v["ad"], "iller": [i["plaka"] for i in iller]})
        onceki = bilinen.get(g, [])
        kanun_soyu = kanunla.get(g)
        if onceki:
            durum = "repo_dogrulanmis"
        elif kanun_soyu and kanun_soyu.get("guven") == "orta":
            durum = "kanun_dogrulanmadi"
        elif kanun_soyu and not any(e["ad"] for e in kanun_soyu["eskiIlceler"]):
            durum = "kanun_kaynak_yazilmamis"   # 3949 Esenler: mahalle listesinde eski ilce yok
        elif kanun_soyu and any(e["geomId"] == g for e in kanun_soyu["eskiIlceler"]):
            # eski Merkez ilcenin halefi, onceki secimlerde ayni geomId ile (6360: Efeler, Menteşe)
            durum = "merkez_ilce"
        elif kanun_soyu:
            durum = "kanun_tek_kaynak" if kanun_soyu["tekKaynak"] else "kanun_cok_kaynak"
        elif k and (k.get("cumhuriyetOncesi") or (kurulus and kurulus < "1950-05-14")):
            durum = "1950_oncesi_mevcut"
        elif k and k.get("merkezIlce"):
            durum = "merkez_ilce"
        else:
            durum = "unresolved"
        kay = None
        if k:
            kay = {"tarih": kurulus, "cumhuriyetOncesi": k.get("cumhuriyetOncesi"), "kanun": k.get("kanun"),
                   "resmiGazete": k.get("resmiGazete"), "merkezIlce": bool(k.get("merkezIlce")),
                   "kaynak": "icisleri_il_ilce_kurulus_2018",
                   **({"not": k["not"]} if k.get("not") else {}),
                   **({"icisleriAdi": k["ad"]} if k.get("adGuncel") else {})}
        else:
            rapor["icisleriKaydiYok"].append({"geomId": g, "ad": v["ad"], "plaka": v["plaka"]})
        lineage.append({
            "geomId": g, "ad": v["ad"], "plaka": v["plaka"], "kurulus": kay,
            "ilkSecim": {"anahtar": ilk[1], "tarih": ilk[0], "adi": ilk[2]} if ilk else None,
            "kurulduAmaSecimeAyriGirmedi": girmedi,
            "merkezIlceDonusumu": merkez_donusumu,
            "adlar": adlar, "ilGecmisi": iller,
            "oncekiBirimler": onceki,
            "kanunSoyu": kanun_soyu,
            "lineageStatus": durum,
            **({"not": "Soy bilgisi (hangi eski ilçe/bucak/köylerden ayrıldığı) henüz kaynaklanmadı (Faz 2). "
                       "Tarihsel sınır uydurulmaz; ilçenin seçime ayrı girmediği tarihlerde bu alan 'unresolved'."}
               if durum == "unresolved" else {}),
        })

    # --- administrative_events
    olaylar = []
    for pl, k in sorted(il_kurulus.items()):
        yeniden = any(o.get("plaka") == pl and o["eventType"] == "reestablished" for o in elle["olaylar"])
        if yeniden:
            continue  # elle_olaylar.json'da (onceki varlik + kaldirilma + yeniden kurulus)
        olaylar.append({"id": f"il-{pl:02d}-kurulus", "unit": k["ad"], "unitType": "province", "plaka": pl,
                        "eventType": "existing_before_1923" if k["cumhuriyetOncesi"] else "created",
                        "effectiveDate": k["kurulus"], "lawNumber": k["kanun"], "officialGazette": k["resmiGazete"],
                        "source": "icisleri_il_ilce_kurulus_2018", "confidence": "high"})
    for l in lineage:
        k = l["kurulus"]
        if k and not (k["merkezIlce"] and k["tarih"] is None and not k["cumhuriyetOncesi"]):
            olaylar.append({
                "id": f"{l['geomId']}-kurulus", "unit": l["ad"], "unitType": "district", "geomId": l["geomId"],
                "eventType": ("existing_before_1923" if k["cumhuriyetOncesi"] else
                              "center_district_restructured" if l["merkezIlceDonusumu"] else "created"),
                "effectiveDate": k["tarih"], "lawNumber": k["kanun"], "officialGazette": k["resmiGazete"],
                "provinceAfter": l["plaka"],
                "predecessors": ([o["tarihselBirim"] for o in l["oncekiBirimler"]] or
                                 [{"district": e["ad"], "geomId": e["geomId"], "provincePlaka": e["plaka"],
                                   "unitsTransferred": e["birimSayisi"]} for e in (l["kanunSoyu"] or {}).get("eskiIlceler", [])]
                                 or None),
                **({"lineageSource": {k: l["kanunSoyu"][k] for k in ("kanun", "listeNo", "rgSayfalari", "kaynak")}}
                   if l["kanunSoyu"] else {}),
                "firstElectionAsSeparateUnit": l["ilkSecim"], "notYetInElections": l["kurulduAmaSecimeAyriGirmedi"],
                "lineageStatus": l["lineageStatus"], "source": "icisleri_il_ilce_kurulus_2018", "confidence": "high"})
        for a, b in zip(l["adlar"], l["adlar"][1:]):
            olaylar.append({"id": f"{l['geomId']}-ad-{b['ilk']}", "unit": l["ad"], "unitType": "district",
                            "geomId": l["geomId"], "eventType": "renamed", "nameBefore": a["ad"], "nameAfter": b["ad"],
                            "effectiveDate": None, "dateBounds": {"after": a["sonTarih"], "before": b["ilkTarih"]},
                            "source": "seçim verisi (aynı geomId, farklı ad)", "confidence": "medium",
                            "not": "Tarih ve kanun kaynaklanmadı; yalnızca iki seçim arasına sıkıştırıldı."})
        for a, b in zip(l["ilGecmisi"], l["ilGecmisi"][1:]):
            yeni = il_kurulus.get(b["plaka"])
            t = yeni["kurulus"] if yeni and yeni["kurulus"] and a["sonTarih"] < yeni["kurulus"] <= b["ilkTarih"] else None
            olaylar.append({"id": f"{l['geomId']}-il-{b['ilk']}", "unit": l["ad"], "unitType": "district",
                            "geomId": l["geomId"], "eventType": "province_changed", "provinceBefore": a["plaka"],
                            "provinceAfter": b["plaka"], "effectiveDate": t,
                            "dateBounds": {"after": a["sonTarih"], "before": b["ilkTarih"]},
                            "source": ("icisleri_il_ilce_kurulus_2018 (yeni ilin kuruluşu) + seçim verisi" if t else "seçim verisi"),
                            "confidence": "high" if t else "medium"})
    olaylar += sinir_duzeltmeleri
    olaylar += elle["olaylar"]

    # --- election_admin_snapshots
    era_plaka = {}
    for e in ERA_DOSYALARI:
        fs = oku(f"geo/historical/turkiye_il_sinirlari_{e}.geojson")["features"]
        era_plaka[f"geo/eras/{e}.geojson"] = sorted(f["properties"]["plaka"] for f in fs)
    era_plaka["geo/il_sinirlari.geojson"] = list(range(1, 82))
    snaps = {}
    for s in secim_listesi:
        t = s["tarih"]
        iller = [pl for pl in range(1, 82) if il_var_mi(pl, t)]
        il_geo = next((p for p, pls in era_plaka.items() if pls == iller), None)
        veri = satirlar.get(s["anahtar"], {})
        ilce_verisi = s["tur"] in ILCE_DUZEYLI and bool(veri.get("ilceler"))
        il_ilce, henuz, belirsiz = collections.defaultdict(list), [], []
        if ilce_verisi:
            for pl, rs in veri["ilceler"].items():
                il_ilce[pl] = [{"ad": r["ad"], "geomId": r["geomId"]} for r in rs]
        mevcut_geom = {r["geomId"] for rs in il_ilce.values() for r in rs}
        for l in lineage:
            g, k = l["geomId"], l["kurulus"] or {}
            kanunla = bool(k.get("cumhuriyetOncesi") or (k.get("tarih") and k["tarih"] <= t) or l["merkezIlceDonusumu"]
                           or (k.get("merkezIlce") and l["ilkSecim"]))
            gorulmus = bool(l["ilkSecim"] and l["ilkSecim"]["tarih"] <= t)
            # kanunla var ama arada ilce duzeyli bir secimde ayri gorulmemis
            yalanlanan = any(k.get("tarih") and k["tarih"] <= x["tarih"] <= t for x in
                             (dict(anahtar=a, tarih=tarih_of[a]) for a in l["kurulduAmaSecimeAyriGirmedi"]))
            if ilce_verisi:
                if g in mevcut_geom:
                    continue
                if gorulmus and not kanunla:
                    continue
            elif gorulmus or (kanunla and not yalanlanan):
                ilk_pl = l["ilGecmisi"][0]["plaka"] if l["ilGecmisi"] else l["plaka"]
                il_ilce[ilk_pl if il_var_mi(ilk_pl, t) else "ilBelirsiz"].append({"ad": l["ad"], "geomId": g})
                if not gorulmus:
                    belirsiz.append(g)
                continue
            henuz.append({"geomId": g, "ad": l["ad"], "bugunkuPlaka": l["plaka"],
                          "neden": ("kanunla kurulmuş, seçime henüz ayrı girmemiş" if kanunla else
                                    "henüz kurulmamış" if k.get("tarih") else "kuruluş tarihi bilinmiyor"),
                          "geometryRule": geometri_kurali(l)})
        uyumsuz = sorted(set(veri.get("iller", [])) ^ set(iller)) if veri.get("iller") else []
        snaps[s["anahtar"]] = {
            "tarih": t, "tarihAraligi": s["tarihAraligi"], "tur": s["tur"],
            "il": {"sayi": len(iller), "plakalar": iller, "secimVerisiyleUyumsuzPlaka": uyumsuz},
            "provinceGeometry": il_geo,
            "provinceGeometryStatus": "exact_existing_snapshot" if il_geo else "missing_snapshot_do_not_guess",
            "ilceKaynagi": ("seçim verisi (ilçe düzeyli satırlar)" if ilce_verisi else
                            "İçişleri kuruluş tarihleri + ilçe düzeyli seçim kanıtı (bu seçimde ilçe kırılımı yok ya da "
                            "yerel seçim: satırlar belediye). Kaldırılmış ilçeler bu kaynaklarda yok."),
            "ilceSayisi": sum(len(v) for v in il_ilce.values()),
            "ilceler": {str(k): v for k, v in sorted(il_ilce.items(), key=lambda kv: str(kv[0]))},
            "kanitsizKanunlaMevcut": belirsiz,
            "henuzKurulmamisVeyaAyriGirmemis": henuz,
        }
        if uyumsuz:
            rapor["ilSayisiUyumsuz"].append({"secim": s["anahtar"], "hesaplanan": len(iller),
                                             "veride": len(veri.get("iller", [])), "plakalar": uyumsuz})
        if not il_geo:
            rapor["ilSinirDosyasiYok"].append({"secim": s["anahtar"], "tarih": t, "ilSayisi": len(iller)})

    kaynaklar = [{"id": "icisleri_il_ilce_kurulus_2018", "type": "official", "title": ic["kaynak"]["yayin"],
                  "url": ic["kaynak"]["url"], "raw": ic["kaynak"]["ham"]}] + elle["kaynaklar"]
    for f in sorted((ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus").glob("*.json")):
        kd = json.loads(f.read_text(encoding="utf-8"))
        kaynaklar.append({"id": f"kanun_{kd['kanun']}", "type": "official",
                          "title": f"{kd['kanun']} sayılı {kd['ad']} (RG {kd['resmiGazete']['tarih']}, sayı {kd['resmiGazete']['sayi']})",
                          "url": kd["kaynaklar"]["rgUrl"], "raw": kd["kaynaklar"]["ekListeler"],
                          "extracted": str(f.relative_to(ROOT))})
    meta = {"schemaVersion": "1.0.0", "faz": 2,
            "policy": {"neverBackcastModernDistrictBeforeExistence": True, "unknownLineage": "unresolved",
                       "matchBy": "geomId", "lawDateIsNotElectionEffect": True,
                       "localElectionRowsAreMunicipalities": True},
            "sources": kaynaklar}
    yaz("administrative_events.json", {**meta, "events": olaylar}, 1)
    yaz("district_lineage.json", {**meta, "districts": lineage,
                                  "historicalUnits": [{"id": k, **v} for k, v in sorted(tarihsel_kanun.items())]}, 1)
    yaz("election_admin_snapshots.json", {**meta, "note": "build_idari_katman.py ile üretilir; elle düzenlenmez.",
                                         "elections": snaps})
    ozet = {"guncelIlce": len(guncel), "icisleriEslesen": len(ilce_kurulus), "icisleriEslesmeyen": eslesmeyen,
            "lineageStatus": dict(collections.Counter(l["lineageStatus"] for l in lineage)),
            "kurulduAmaSecimeAyriGirmedi": sum(1 for l in lineage if l["kurulduAmaSecimeAyriGirmedi"]),
            "merkezIlceDonusumu": sum(1 for l in lineage if l["merkezIlceDonusumu"]),
            "olay": dict(collections.Counter(o["eventType"] for o in olaylar)),
            **{k: len(v) for k, v in rapor.items()}}
    yaz("faz1_rapor.json", {"ozet": ozet, **rapor}, 1)
    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
