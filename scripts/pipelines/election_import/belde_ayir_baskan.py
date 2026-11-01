"""
2009/2014/2019/2024 yerel secimlerinde ilce belediye baskanligi kayitlarini belde sandiklarindan arindirir.

Sorun (docs/rapor/KAZANAN_TUTARSIZLIK.md): data/raw/ysk/yerel-v2-agrege/ (fetch_yerel_v2.js) ilce
toplamini ilcedeki BUTUN belediye baskanligi sandiklarindan topluyordu; belde belediyeleri kendi
baskanlarini ayri bir yarista secer, bu sandiklardaki oylar baska adaylara verilmistir. Beldesi olan
her ilcede kaydin oylari, oranlari, secmeni, sandigi ve katilimi "ilce merkezi + beldeler" toplamiydi.

Yeni kaynak: data/raw/ysk/acikveri-belde-agrege/<yil>yerel_belediye_baskanligi.json
(.github/workflows/ysk-belde-baskan-cek.yml, fetch_belde_agrege.js, secimTuru=2). Birimler
"il-ilce-belde"; belde=0 ilce merkezi belediyesidir.

Kural (tahmin yok):
  - Yalniz YSK'de en az bir beldesi olan ilce ele alinir. Eski v2 ilce toplaminin sandik sayisi
    "ilce merkezi + beldeler" ile birebir ayni olmali (kok nedenin kaniti); kaydin gecerli oyu ve
    sandigi da v2 toplamiyla ayni olmali (kayit o toplamdan geliyor). Uymayan kayda dokunulmaz,
    nedeni raporlanir.
  - Ilce merkezi biriminde parti + bagimsiz oylari toplami gecerli oya esit olmali.
  - Yeni degerler: oy (parti sutunlari partiler.json anahtarlarina; bagimsizlar 'Bağımsız'),
    oran (gecerli oya gore), gecerliOy, secmen, sandik, katilim (oy kullanan / secmen).
  - Kazanan aday duzeyinde: partiler ve her bagimsiz aday (bagimsizN) ayri ayri. Bagimsizlarin
    toplami kazanandan fazla ama tek bagimsiz aday degilse 'not' yazilir.
    Eski kazanan yeni sonuctan farkliysa: eski kazanan karisik toplamin birincisiyse (gizli hata)
    duzeltilir; degilse (itiraz/yeniden sayim gibi baska bir resmi kaynaktan gelmis olabilir)
    eski kazanan korunur ve raporlanir (KORUNAN_KAZANAN).
  - Eski degerler kaynak.yskSatiri altinda (birim: "ilçe merkezi ve bağlı beldelerin toplamı"),
    yeni degerlerin kaynagi kaynak.ilceBelediyesi altinda (PR #18 ile ayni duzen).
  - kaynak.yskSatiri zaten olan kayitlar (PR #18'de Vikipedi'den duzeltilen 33 kayit) degistirilmez;
    yeni YSK verisiyle karsilastirilip fark raporlanir.
  - Il satiri: buyuksehir olmayan illerde il kaydi il merkezi ilcesinin kendi yarisidir (v2 'merkez:'
    turu); il merkezi ilcesi duzeltildiyse il satiri da ayni degerleri alir. Buyuksehir il satiri
    (secimTuru=6, ayri yaris) degismez.
  - Idempotent: kaynak.yskSatiri olan satir atlanir.

Kullanim (repo kokunden):
  python3 scripts/pipelines/election_import/belde_ayir_baskan.py [kontrol|uygula] [--rapor <csv>]
"""
import collections
import copy
import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common.election_io import load_election, save_election  # noqa: E402
from common.hist_geomid import resolve_historical_merkez  # noqa: E402
from party_map_helper import build_party_mapping  # noqa: E402

BELDE_DIR = ROOT / "data" / "raw" / "ysk" / "acikveri-belde-agrege"
V2_DIR = ROOT / "data" / "raw" / "ysk" / "yerel-v2-agrege"
GEOMID_MAP = json.loads((ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json").read_text(encoding="utf-8"))
SECIMLER = ["2009yerel", "2014yerel", "2019yerel", "2024yerel"]
ANAHTAR_DUZELTME = {"DEVA PARTİSİ": "DEVA"}
BAG_RE = re.compile(r"^bagimsiz(\d+)_ALDIGI_OY$")
PARTI_RE = re.compile(r"^(parti|ittifak)\d+_ALDIGI_OY$")
TOPLAM_BIRIM = "ilçe merkezi ve bağlı beldelerin toplamı"
# 2009'da Akyazı, Koçarlı, Mecitözü, Şarkikaraağaç ilçe belediyesi seçimi iptal edilip 7 Haziran 2009'da yenilendi
# (bianet, "Local elections repeated in 30 places"); açık veride ilçe merkezinin 29 Mart sandıkları yok.
SADECE_BELDE = ("yalnız bağlı beldelerin toplamı; ilçe merkezi belediyesinin başkanlık sandıkları YSK açık verisinde yok "
                "(29 Mart seçimi iptal edilip yenilendi)")
YONTEM = ("YSK açık veri sandık düzeyi, yalnız ilçe merkezi belediyesinin sandıkları (belde sandıkları hariç); "
          "kazanan aday düzeyinde (her bağımsız aday ayrı)")


def binlik(n):
    return f"{n:,}".replace(",", ".")


def birim_sonucu(b, col_to_key):
    t = b["toplam"]
    oy = collections.Counter()
    bag, bilinmeyen = {}, {}
    for col, v in t.items():
        if not v:
            continue
        m = BAG_RE.match(col)
        if m:
            bag[int(m.group(1))] = v
        elif PARTI_RE.match(col):
            if col not in col_to_key or not col_to_key[col]:
                bilinmeyen[col] = v  # baslik listesinde adi olmayan sutun
                continue
            oy[ANAHTAR_DUZELTME.get(col_to_key[col], col_to_key[col])] += v
    bag_top = sum(bag.values())
    if t.get("bagimsiz_TOPLAM_OY") and t["bagimsiz_TOPLAM_OY"] != bag_top:
        bag_top = None  # sutunlar tutarsiz
    gecerli = t.get("gecerli_OY_TOPLAMI", 0)
    if bag_top:
        oy["Bağımsız"] = bag_top
    return {"oy": oy, "bagimsizAdaylar": bag, "gecerli": gecerli, "gecersiz": t.get("gecersiz_OY_TOPLAMI", 0),
            "oyKullanan": t.get("oy_KULLANAN_SECMEN_SAYISI", 0), "secmen": t.get("secmen_SAYISI", 0),
            "sandik": b["sandik"], "bilinmeyen": bilinmeyen,
            "tutarli": not bilinmeyen and bag_top is not None and sum(oy.values()) == gecerli and gecerli > 0}


def aday_kazanan(s):
    adaylar = [(v, p) for p, v in s["oy"].items() if p != "Bağımsız"]
    adaylar += [(v, "Bağımsız") for v in s["bagimsizAdaylar"].values()]
    adaylar.sort(reverse=True)
    if not adaylar:
        return None, 0
    fark = adaylar[0][0] - (adaylar[1][0] if len(adaylar) > 1 else 0)
    return adaylar[0][1], fark


def v2_oylar(agg, col_to_key_v2):
    oy = collections.Counter()
    for col, v in (agg.get("oy") or {}).items():
        if not v:
            continue
        if BAG_RE.match(col):
            oy["Bağımsız"] += v
        else:
            oy[ANAHTAR_DUZELTME.get(col_to_key_v2[col], col_to_key_v2[col])] += v
    return oy


def ilce_geom(ilce_key, il_id, ilce_adi, yil, sandik):
    geom = GEOMID_MAP.get(ilce_key)
    if not geom:
        hist = resolve_historical_merkez(il_id, ilce_adi, yil)
        if hist and sandik > 0:
            geom = hist
    return geom


def yeni_kayit_degerleri(r, s, kazanan):
    g = s["gecerli"]
    adaylar = {p: v.get("aday") for p, v in r["oy"].items() if isinstance(v, dict) and v.get("aday")}
    oy = {p: {"oran": round(100 * o / g, 2), "oy": o, **({"aday": adaylar[p]} if p in adaylar else {})}
          for p, o in sorted(s["oy"].items()) if o}
    return {"oy": oy, "kazanan": kazanan, "gecerliOy": g, "secmen": s["secmen"], "sandik": s["sandik"],
            "katilim": round(100 * s["oyKullanan"] / s["secmen"], 2) if s["secmen"] else None}


def bagimsiz_notu(s, kazanan):
    bag = s["oy"].get("Bağımsız", 0)
    if not bag or kazanan == "Bağımsız" or len(s["bagimsizAdaylar"]) < 2:
        return None
    if bag <= s["oy"].get(kazanan, 0):
        return None
    return (f"'Bağımsız' satırı birden fazla bağımsız adayın oy toplamıdır ({binlik(bag)}); en çok oy alan "
            f"bağımsız aday {binlik(max(s['bagimsizAdaylar'].values()))} oy aldı. Kazanan aday bazında en çok "
            f"oyu alandır ({kazanan}).")


def uygula_kayit(r, s, kazanan, kaynak_yolu, birim_anahtari, belde_sayisi, belde_sandik, v2_dosya, ek=None):
    eski_kaynak = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
    eski = {"birim": TOPLAM_BIRIM,
            "oy": {p: (v.get("oy") if isinstance(v, dict) else v) for p, v in r["oy"].items()},
            "kazanan": r.get("kazanan")}
    for alan in ("gecerliOy", "secmen", "sandik", "katilim"):
        eski[alan] = r.get(alan)
    eski["kaynak"] = v2_dosya
    if eski_kaynak:
        eski["oncekiKaynak"] = copy.deepcopy(eski_kaynak)
    for alan in ("veriNotu", "not"):
        if r.get(alan):
            eski[alan] = r.pop(alan)
    yeni = yeni_kayit_degerleri(r, s, kazanan)
    r.update(yeni)
    ib = {"kaynak": f"{kaynak_yolu} (birim {birim_anahtari})", "yontem": YONTEM,
          "beldeSayisi": belde_sayisi, "beldeSandik": belde_sandik,
          "oyKullanan": s["oyKullanan"], "gecersizOy": s["gecersiz"]}
    if s["bagimsizAdaylar"]:
        ib["bagimsizAdaylar"] = {f"bagimsiz{k}": v for k, v in sorted(s["bagimsizAdaylar"].items())}
    if ek:
        ib.update(ek)
    r["kaynak"] = {"ana": "ysk", "ilceBelediyesi": ib, "yskSatiri": eski}
    n = bagimsiz_notu(s, kazanan)
    if n:
        r["not"] = n


def isle(secim, rapor, uygula):
    yil = int(secim[:4])
    kaynak_dosya = BELDE_DIR / f"{secim}_belediye_baskanligi.json"
    if not kaynak_dosya.exists():
        print(f"{secim}: {kaynak_dosya.name} yok, atlandı")
        return None
    A = json.loads(kaynak_dosya.read_text(encoding="utf-8"))
    V = json.loads((V2_DIR / f"{secim}.json").read_text(encoding="utf-8"))
    kaynak_yolu = str(kaynak_dosya.relative_to(ROOT))
    v2_dosya = str((V2_DIR / f"{secim}.json").relative_to(ROOT))
    rec = load_election(secim)
    mevcut = set()
    for lv in ("iller", "ilceler"):
        for r in rec[lv]:
            mevcut.update(r["oy"])
    mevcut -= {"Diğer", "Bağımsız"}
    col_to_key = build_party_mapping({b["column_NAME"]: b["ad"] for b in A["baslik"]}, mevcut, {})
    col_to_key_v2 = build_party_mapping(V["colToName"], mevcut, {})

    merkez, beldeler = {}, collections.defaultdict(list)
    for k, b in A["birimler"].items():
        ik = f"{b['ilId']}-{b['ilceId']}"
        if b["beldeId"]:
            beldeler[ik].append(b)
        else:
            merkez[ik] = b
    # geomId -> ilce anahtari (merge_yerel_v2.py ile ayni esleme ve ayni oncelik)
    geom_ik = {}
    for ik, agg in V["ilceler"].items():
        geom = ilce_geom(ik, agg["ilId"], agg["ilceAdi"], yil, agg.get("sandikSayisi", 0))
        if not geom:
            continue
        if geom in geom_ik and V["ilceler"][geom_ik[geom]].get("sandikSayisi", 0) > 0 and agg.get("sandikSayisi", 0) == 0:
            continue
        geom_ik[geom] = ik
    # Sonradan tarihsel geomId alan kayitlar (HIST-/HISTK-): beldeli ama eslenmeyen ilceyi kaydin v2 degerleriyle
    # (plaka + sandik + gecerli oy, tek aday) bul.
    kayit_geom = {r.get("geomId") for r in rec["ilceler"]}
    eslesmeyen = {ik for ik in beldeler if ik not in geom_ik.values() or
                  next(g for g, x in geom_ik.items() if x == ik) not in kayit_geom}
    deger_ik = {}
    for ik in eslesmeyen:
        v = V["ilceler"].get(ik) or {}
        aday = [r for r in rec["ilceler"] if r["plaka"] == v.get("ilId") and r.get("sandik") == v.get("sandikSayisi")
                and r.get("gecerliOy") == v.get("gecerli") and r.get("geomId") not in geom_ik]
        if len(aday) == 1:
            deger_ik[id(aday[0])] = ik

    sayac = collections.Counter()
    duzeltilen_ik = {}

    def satir(duzey, r, durum, **kw):
        rapor.append({"secim": secim, "duzey": duzey, "plaka": r.get("plaka"), "ad": r.get("ad"),
                      "geomId": r.get("geomId", ""), "durum": durum, **kw})

    for r in rec["ilceler"]:
        ik = geom_ik.get(r.get("geomId")) or deger_ik.get(id(r))
        if not ik or not beldeler.get(ik):
            continue
        sayac["beldeli_ilce"] += 1
        m = merkez.get(ik)
        bl = beldeler[ik]
        bsandik = sum(b["sandik"] for b in bl)
        v = V["ilceler"].get(ik) or {}
        if not m:
            sayac["merkez_birimi_yok"] += 1
            satir("ilce", r, "merkez_birimi_yok", kayitSandik=r.get("sandik"), v2Sandik=v.get("sandikSayisi"))
            if r.get("sandik") == v.get("sandikSayisi") and r.get("gecerliOy") == v.get("gecerli"):
                if yenileme_2009(secim, r, v2_dosya, len(bl), bsandik, ik):
                    sayac["yenileme_2009"] += 1
                    satir("ilce", r, "yenileme_2009", kazanan=r["kazanan"])
                    duzeltilen_ik[ik] = ("onceki", r)
                else:
                    r["ilceGeneliSonuc"] = SADECE_BELDE
            continue
        s = birim_sonucu(m, col_to_key)
        kazanan, fark = aday_kazanan(s)
        k = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
        if k.get("yskSatiri"):
            # PR #18 kaydi: karsilastir, degistirme
            farklar = []
            for alan, yv in (("gecerliOy", s["gecerli"]), ("sandik", s["sandik"]), ("secmen", s["secmen"])):
                if r.get(alan) != yv:
                    farklar.append(f"{alan} {r.get(alan)}→YSK {yv}")
            for p in sorted(set(s["oy"]) | {p for p in r["oy"]}):
                ro = (r["oy"].get(p) or {}).get("oy", 0)
                if ro != s["oy"].get(p, 0):
                    farklar.append(f"{p} {ro}→YSK {s['oy'].get(p, 0)}")
            ok_kazanan = r.get("kazanan") == kazanan
            ib = k.get("ilceBelediyesi") or {}
            yk = ib.get("yskKontrol") or {}
            sayac["onceki_duzeltme_" + ("ayni" if not farklar else ("kazanan_ayni_oy_farkli" if ok_kazanan else "kazanan_farkli"))] += 1
            satir("ilce", r, "onceki_duzeltme", kazanan=r.get("kazanan"), yskKazanan=kazanan, fark=fark,
                  farklar="; ".join(farklar), oyKullanan=s["oyKullanan"], kayitOyKullanan=yk.get("oyKullanan"))
            duzeltilen_ik[ik] = ("onceki", r)
            continue
        if v.get("sandikSayisi") != s["sandik"] + bsandik:
            sayac["v2_sandik_merkez_arti_belde_degil"] += 1
            satir("ilce", r, "v2_sandik_tutmuyor", v2Sandik=v.get("sandikSayisi"), merkezSandik=s["sandik"], beldeSandik=bsandik)
            continue
        if r.get("sandik") != v.get("sandikSayisi") or r.get("gecerliOy") != v.get("gecerli"):
            sayac["kayit_v2_degil"] += 1
            satir("ilce", r, "kayit_v2_toplami_degil", kayitSandik=r.get("sandik"), v2Sandik=v.get("sandikSayisi"),
                  kayitGecerli=r.get("gecerliOy"), v2Gecerli=v.get("gecerli"))
            continue
        ek = None
        if not s["tutarli"]:
            kalan = s["gecerli"] - sum(s["oy"].values())
            if s["bilinmeyen"] and 0 < kalan < sum(s["bilinmeyen"].values()) and kalan < 0.03 * s["gecerli"]:
                # Baslik listesinde adi olmayan sutunlar (2009: parti21-26) toplami tutmuyor; adlandirilmis
                # partiler aynen, gecerli oya kalan fark 'Diğer' (digerTamamlama duzeni). Kazanan farki kalandan buyuk olmali.
                kazanan, fark = aday_kazanan(s)
                if fark > kalan:
                    s["oy"]["Diğer"] = kalan
                    ek = {"digerTamamlama": {
                        "oy": kalan, "bilinmeyenSutunlar": dict(sorted(s["bilinmeyen"].items())),
                        "not": "YSK başlık listesinde adı olmayan sütunlar toplamı tutmuyor; adlandırılmış parti oyları aynen, "
                               "geçerli oya kalan fark 'Diğer'. Kazananla ikinci arasındaki fark bu kalandan büyük."}}
            if ek is None:
                sayac["ysk_tutarsiz"] += 1
                satir("ilce", r, "ysk_parti_toplami_gecerliye_esit_degil", bilinmeyenSutun=sum(s["bilinmeyen"].values()))
                r["ilceGeneliSonuc"] = TOPLAM_BIRIM
                continue
        eski_kaz = r.get("kazanan")
        durum = "duzeltildi"
        if kazanan != eski_kaz:
            v2oy = v2_oylar(v, col_to_key_v2)
            karisik_birinci = max(v2oy, key=v2oy.get) if v2oy else None
            kayit_birinci = max(r["oy"], key=lambda p: r["oy"][p]["oy"]) if r["oy"] else None
            # 'Bağımsız' kazanan karisik toplamdan yalniz digerAyristirma ile (oncekiKazanan) belirlenmis olabilir;
            # Vikipedi'nin "seçildi" isaretinden (bagimsizTamamlama) gelen bagimsiz kazanan korunur.
            karisik_bagimsiz = eski_kaz == "Bağımsız" and "oncekiKazanan" in (k.get("digerAyristirma") or {})
            if (eski_kaz in (karisik_birinci, kayit_birinci) and eski_kaz != "Bağımsız") or karisik_bagimsiz:
                durum = "duzeltildi_kazanan_degisti"
                ek = {**(ek or {}), "oncekiKazanan": eski_kaz,
                      "kazananNotu": "Önceki kazanan ilçe merkezi + belde toplamının birincisiydi; ilçe belediyesinin kendi sandıklarında birinci değil"}
            else:
                durum = "duzeltildi_kazanan_korundu"
                ek = {**(ek or {}), "yskKazanan": kazanan, "yskFark": fark,
                      "kazananNotu": "Kayıttaki kazanan YSK sandık toplamının birincisinden farklı; kayıttaki kazanan başka kaynaktan (aday düzeyinde) geldiği için korundu"}
                kazanan = eski_kaz
        satir("ilce", r, durum, eskiKazanan=eski_kaz, kazanan=kazanan, fark=fark, eskiGecerli=r.get("gecerliOy"),
              gecerli=s["gecerli"], eskiSandik=r.get("sandik"), sandik=s["sandik"], beldeSayisi=len(bl))
        uygula_kayit(r, s, kazanan, kaynak_yolu, f"{ik}-0", len(bl), bsandik, v2_dosya, ek)
        sayac[durum] += 1
        duzeltilen_ik[ik] = ("yeni", r)

    # il satirlari: buyuksehir olmayan illerde il merkezi ilcesinin kendi yarisi
    for r in rec["iller"]:
        va = V["iller"].get(str(r["plaka"])) or {}
        kind = va.get("kind") or ""
        if not kind.startswith("merkez:"):
            continue
        ilce_adi = kind.split(":", 1)[1]
        ik = next((k2 for k2, a in V["ilceler"].items() if a["ilId"] == r["plaka"] and a["ilceAdi"] == ilce_adi), None)
        if not ik or ik not in duzeltilen_ik:
            continue
        tur, ilce_r = duzeltilen_ik[ik]
        k = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
        if k.get("yskSatiri"):
            esit = all(r.get(a) == ilce_r.get(a) for a in ("gecerliOy", "sandik", "secmen", "kazanan", "oy"))
            sayac["il_onceki_duzeltme_" + ("ilceyle_ayni" if esit else "ilceden_farkli")] += 1
            satir("il", r, "onceki_duzeltme", farklar="" if esit else "il satırı ilçe satırından farklı")
            continue
        if tur != "yeni":
            satir("il", r, "il_atlandi_ilce_onceki_duzeltme")
            continue
        if r.get("sandik") != va.get("sandikSayisi") or r.get("gecerliOy") != va.get("gecerli"):
            sayac["il_kayit_v2_degil"] += 1
            satir("il", r, "il_kayit_v2_toplami_degil")
            continue
        eski_kaynak = k
        eski = {"birim": TOPLAM_BIRIM, "oy": {p: v["oy"] for p, v in r["oy"].items()}, "kazanan": r.get("kazanan")}
        for alan in ("gecerliOy", "secmen", "sandik", "katilim"):
            eski[alan] = r.get(alan)
        eski["kaynak"] = v2_dosya
        if eski_kaynak:
            eski["oncekiKaynak"] = copy.deepcopy(eski_kaynak)
        for alan in ("veriNotu", "not"):
            if r.get(alan):
                eski[alan] = r.pop(alan)
        for alan in ("oy", "kazanan", "gecerliOy", "secmen", "sandik", "katilim"):
            r[alan] = copy.deepcopy(ilce_r[alan])
        if ilce_r.get("not"):
            r["not"] = ilce_r["not"]
        r["kaynak"] = {"ana": "ysk", "ilceBelediyesi": copy.deepcopy(ilce_r["kaynak"]["ilceBelediyesi"]), "yskSatiri": eski}
        r["kaynak"]["ilceBelediyesi"]["not"] = "il merkezi belediyesi; il merkezi ilçesinin satırıyla aynı"
        sayac["il_duzeltildi"] += 1
        satir("il", r, "duzeltildi", eskiKazanan=eski["kazanan"], kazanan=r["kazanan"])
    yv = yenileme_2009_vikipedi(secim, rec, rapor)
    if yv:
        sayac["yenileme_2009_vikipedi"] += yv
    yn = yenileme_uygula(secim, rec, rapor)
    if yn:
        sayac["yenileme_sonucu"] += yn
    if uygula:
        save_election(secim, rec)
    return sayac


# 31 Mart seçimi iptal edilip yenilenen ilçe belediyeleri: harita geçerli (yenileme) sonucunu gösterir.
# (secim, ham dosya, birim, geomId, yenileme tarihi, ilk seçim tarihi, kazanan aday, ek kaynak)
YENILEMELER = [
    ("2024yerel", "2024yenileme_baskan.json", "68-754-0", "TR-D-68-005", "2 Haziran 2024", "31 Mart 2024",
     "Ünal Demircioğlu",
     "https://www.ntv.com.tr/turkiye/yenilenen-secimlerin-kesin-sonuclari-aciklandiak-parti-3-dem-parti-1-chp-2-mhp-1-belediye-kazandi,Jb0Dhi40fUm575vHcN9rhw"),
]


def yenileme_uygula(secim, rec, rapor):
    n = 0
    for (s_, dosya, birim, geom, tarih, ilk_tarih, aday, ek_kaynak) in YENILEMELER:
        if s_ != secim:
            continue
        r = next(x for x in rec["ilceler"] if x.get("geomId") == geom)
        k = r.get("kaynak") or {}
        if k.get("yenileme"):
            continue
        Y = json.loads((BELDE_DIR / dosya).read_text(encoding="utf-8"))
        mevcut = {p for x in rec["ilceler"] for p in x["oy"]} - {"Diğer", "Bağımsız"}
        col_to_key = build_party_mapping({b["column_NAME"]: b["ad"] for b in Y["baslik"]}, mevcut, {})
        s = birim_sonucu(Y["birimler"][birim], col_to_key)
        if not s["tutarli"]:
            raise SystemExit(f"{secim} {birim}: yenileme birimi tutarsız")
        kazanan, fark = aday_kazanan(s)
        ilk = {"tarih": ilk_tarih, "kazanan": r.get("kazanan"),
               "oy": {p: v["oy"] for p, v in r["oy"].items()}}
        for alan in ("gecerliOy", "secmen", "sandik", "katilim"):
            ilk[alan] = r.get(alan)
        if r.get("not"):
            ilk["not"] = r.pop("not")
        yeni = yeni_kayit_degerleri(r, s, kazanan)
        r.update(yeni)
        if kazanan in r["oy"]:
            r["oy"][kazanan]["aday"] = aday
        k["yenileme"] = {"tarih": tarih, "kaynak": f"{(BELDE_DIR / dosya).relative_to(ROOT)} (birim {birim})",
                         "ek": "data/normalized/ek/yenileme_ara/2024yenileme_belediye_baskanligi.json",
                         "ikinciKaynak": ek_kaynak, "oyKullanan": s["oyKullanan"], "gecersizOy": s["gecersiz"],
                         "ilkSecim": ilk}
        if k.get("ilceBelediyesi"):
            k["ilceBelediyesi"]["not"] = f"{ilk_tarih} seçiminin ilçe belediyesi sonucu; değerleri kaynak.yenileme.ilkSecim altında"
        r["kaynak"] = k
        r["not"] = (f"{ilk_tarih} seçimi iptal edildi ve {tarih}'te yenilendi; gösterilen yenileme sonucudur "
                    f"({kazanan}, {aday}). {ilk_tarih}'te ilçe belediyesinde birinci {ilk['kazanan']} idi.")
        rapor.append({"secim": secim, "duzey": "ilce", "plaka": r["plaka"], "ad": r["ad"], "geomId": geom,
                      "durum": "yenileme_sonucu", "eskiKazanan": ilk["kazanan"], "kazanan": kazanan, "fark": fark})
        n += 1
    return n


# 29 Mart 2009'da iptal edilip 7 Haziran 2009'da yenilenen ilçe belediyeleri. YSK açık verisinde yenileme seçimi
# yok (getSecimDetayList'te 2009'dan yalnız 4290; ysk-yenileme-2009-cek.yml, data/raw/ysk/yenileme-2009/).
# Değerler Vikipedi il sayfasının "7 Haziran Sonuçları" sütunundan (yenileme_2009.tablo); her parti oyu iki haber
# kaynağıyla (NTV ve CNN Türk, 7 Haziran 2009, arşiv kopyaları data/raw/web/yenileme-2009/) birebir karşılaştırılır.
# 29 Mart değerleri de Vikipedi'den; sandık ve seçmen YSK belediye meclisi verisindeki ilçe merkezi birimiyle eşleşmeli.
NTV_2009 = "https://web.archive.org/web/20220529224532/https://www.ntv.com.tr/turkiye/yenileme-secimleri-sonuclari,gkFPxeKiz0C80_Z42bJPtw"
CNNTURK_2009 = "https://web.archive.org/web/20090611085753/https://www.cnnturk.com/2009/turkiye/06/07/turkiye.yine.sandik.basindaydi/529889.0/index.html"
YENILEME_2009 = {  # ilce anahtari: (Vikipedi dosyasi, ilce, kazanan aday, haberdeki parti oylari, haberdeki oy kullanan, geçersiz)
    "54-23": ("sakaryada-2009-turkiye-yerel-secimleri.wiki", "Akyazı", "Yaşar Yazıcı",
              {"AK Parti": 11081, "SP": 10026, "MHP": 1553, "CHP": 154, "DP": 43, "DSP": 30, "BTP": 50}, 23184, 247),
    "9-373": ("aydinda-2009-turkiye-yerel-secimleri.wiki", "Koçarlı", "Cengiz Şen",
              {"MHP": 34, "CHP": 1745, "DP": 1217, "SP": 5, "AK Parti": 1512, "BTP": 1}, 4577, 63),
    "19-413": ("corumda-2009-turkiye-yerel-secimleri.wiki", "Mecitözü", "Selçuk Aksoy",
               {"MHP": 21, "CHP": 1918, "SP": 18, "AK Parti": 1649, "DSP": 4}, 3673, 63),
    "32-544": ("ispartada-2009-turkiye-yerel-secimleri.wiki", "Şarkikaraağaç", "Mevlüt Özdemir",
               {"MHP": 2878, "CHP": 42, "DP": 27, "SP": 78, "AK Parti": 2968, "BTP": 10}, 6237, 234),
}
UYGULA = False  # main() ayarlar; ek/yenileme_ara dosyası yalnız 'uygula'da yazılır
YENILEME_2009_EK = ROOT / "data" / "normalized" / "ek" / "yenileme_ara" / "2009yenileme_belediye_baskanligi.json"


def yenileme_2009(secim, r, v2_dosya, belde_sayisi, belde_sandik, ik):
    if secim != "2009yerel" or ik not in YENILEME_2009:
        return False
    from yenileme_2009 import WIKI, tablo  # noqa: E402
    dosya, ilce, aday, haber, haber_oyk, haber_gecersiz = YENILEME_2009[ik]
    secmen, sandik, t = tablo(dosya, ilce)
    m, h = t["mart"], t["haziran"]
    h["oy"] = {p: o for p, o in h["oy"].items() if o}
    m["oy"] = {p: o for p, o in m["oy"].items() if o}
    if h["oy"] != haber or h["gecerliOy"] + h["gecersizOy"] != haber_oyk or h["gecersizOy"] != haber_gecersiz:
        raise SystemExit(f"{ilce}: Vikipedi 7 Haziran sütunu haberle tutmuyor: {h['oy']} / {haber}")
    meclis = json.loads((BELDE_DIR / "2009yerel_belediye_meclisi.json").read_text(encoding="utf-8"))["birimler"][ik + "-0"]
    if meclis["sandik"] != sandik or meclis["toplam"]["secmen_SAYISI"] != secmen:
        raise SystemExit(f"{ilce}: Vikipedi sandık/seçmen YSK meclis ilçe merkezi birimiyle tutmuyor")
    idx = json.loads((WIKI / "_index.json").read_text(encoding="utf-8"))["sayfalar"]
    url = next(v["url"] for v in idx.values() if v["dosya"] == dosya)
    eski = {"birim": "yalnız bağlı beldelerin toplamı (ilçe merkezinin 29 Mart başkanlık sandıkları YSK açık verisinde yok)",
            "oy": {p: (v.get("oy") if isinstance(v, dict) else v) for p, v in r["oy"].items()}, "kazanan": r.get("kazanan")}
    for alan in ("gecerliOy", "secmen", "sandik", "katilim"):
        eski[alan] = r.get(alan)
    eski["kaynak"] = v2_dosya
    if isinstance(r.get("kaynak"), dict) and r["kaynak"]:
        eski["oncekiKaynak"] = copy.deepcopy(r["kaynak"])
    for alan in ("veriNotu", "not"):
        if r.get(alan):
            eski[alan] = r.pop(alan)
    r.pop("ilceGeneliSonuc", None)
    kazanan = max(h["oy"], key=h["oy"].get)
    mk = max(m["oy"], key=m["oy"].get)
    g = h["gecerliOy"]
    r["oy"] = {p: {"oran": round(100 * o / g, 2), "oy": o, **({"aday": h["adaylar"][p]} if h["adaylar"].get(p) else {})}
               for p, o in sorted(h["oy"].items()) if o}
    r.update({"kazanan": kazanan, "gecerliOy": g, "secmen": secmen, "sandik": sandik, "katilim": h["katilim"]})
    r["kaynak"] = {"ana": "wikipedia", "yenileme": {
        "tarih": "7 Haziran 2009", "kaynak": f"Vikipedi il sayfası, {url} (7 Haziran Sonuçları sütunu)",
        "ikinciKaynak": [NTV_2009, CNNTURK_2009],
        "kontrol": "her parti oyu, oy kullanan ve geçersiz oy iki haberle birebir; sandık ve seçmen YSK belediye meclisi "
                   f"ilçe merkezi birimiyle (data/raw/ysk/acikveri-belde-agrege/2009yerel_belediye_meclisi.json, birim {ik}-0) birebir",
        "oyKullanan": g + h["gecersizOy"], "gecersizOy": h["gecersizOy"],
        "ek": str(YENILEME_2009_EK.relative_to(ROOT)),
        "ilkSecim": {"tarih": "29 Mart 2009", "kaynak": "Vikipedi il sayfası (29 Mart Sonuçları sütunu)",
                     "kazanan": mk, "oy": dict(sorted(m["oy"].items())), "gecerliOy": m["gecerliOy"],
                     "gecersizOy": m["gecersizOy"], "katilim": m["katilim"], "sandik": sandik, "secmen": secmen}},
        "yskSatiri": eski}
    r["kaynak"]["yenileme"]["beldeSayisi"], r["kaynak"]["yenileme"]["beldeSandik"] = belde_sayisi, belde_sandik
    r["not"] = (f"29 Mart 2009 seçimi iptal edildi ve 7 Haziran 2009'da yenilendi; gösterilen yenileme sonucudur "
                f"({kazanan}, {aday}). 29 Mart'ta ilçe belediyesinde birinci {mk} idi. YSK açık verisinde bu seçim yok; "
                f"kaynak Vikipedi, NTV ve CNN Türk ile birebir.")
    if kazanan in r["oy"]:
        r["oy"][kazanan]["aday"] = aday
    # ek/yenileme_ara dosyasina birim (yoksa)
    ek = json.loads(YENILEME_2009_EK.read_text(encoding="utf-8"))
    if UYGULA and not any(b.get("geomId") == r["geomId"] for b in ek["birimler"]):
        il = {54: "Sakarya", 9: "Aydın", 19: "Çorum", 32: "Isparta"}[r["plaka"]]
        ek["birimler"].append({"il": il, "plaka": r["plaka"], "ilce": ilce, "geomId": r["geomId"], "beldeId": None,
                               "belde": None, "sandik": sandik, "secmen": secmen, "gecerliOy": g,
                               "gecersizOy": h["gecersizOy"], "katilim": h["katilim"],
                               "oy": dict(sorted(h["oy"].items(), key=lambda x: -x[1])),
                               "adaylar": h["adaylar"], "kazanan": kazanan, "kaynakUrl": url,
                               "ikinciKaynak": [NTV_2009, CNNTURK_2009]})
        ek["aciklama"] = ("7 Haziran 2009 yenileme seçimi — belediye başkanlığı (29 Mart'ta iptal edilen Ağın, Kadışehri, "
                          "Akyazı, Koçarlı, Mecitözü, Şarkikaraağaç)")
        ek["ozet"]["birim"] = ek["ozet"]["il"] = len(ek["birimler"])
        ek["kaynak"]["not"] += " Akyazı, Koçarlı, Mecitözü, Şarkikaraağaç: belde_ayir_baskan.py (NTV ve CNN Türk ile birebir)."
        YENILEME_2009_EK.write_text(json.dumps(ek, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return True


# Beldesi olmayan (ya da kaydı zaten Vikipedi'den gelen) 2009 yenileme ilçeleri: Ağın ve Kadışehri. Kayıt
# yenileme_2009.py ile 29 Mart sonucunu gösteriyordu; aynı yöntemle 7 Haziran sonucuna çevrilir, 29 Mart
# değerleri kaynak.yenileme.ilkSecim altında kalır.
# geomId: (Vikipedi dosyasi, ilce, kazanan aday, YSK meclis ilce merkezi birimi ya da None,
#          [(kaynak adi, URL, parti oylari, oy kullanan ya da None, gecersiz ya da None)], bilinen fark notu)
YENILEME_2009_VIKIPEDI = {
    "TR-D-23-001": ("elazigda-2009-turkiye-yerel-secimleri.wiki", "Ağın", "Mustafa Yentür", "23-10-0",
                    [("NTV", NTV_2009, {"MHP": 529, "DSP": 1, "CHP": 10, "DP": 1, "SP": 14, "AK Parti": 649, "BTP": 4}, None, None),
                     ("CNN Türk", CNNTURK_2009, {"AK Parti": 649, "MHP": 529, "SP": 14, "CHP": 10, "BTP": 4, "DSP": 1, "DP": 1}, 1236, 28)],
                    None),
    "TR-D-66-007": ("yozgatta-2009-turkiye-yerel-secimleri.wiki", "Kadışehri", "Davut Karadavut", None,
                    [("NTV", NTV_2009, {"AK Parti": 1195, "SP": 1000, "MHP": 9}, None, None)],
                    "NTV aynı toplamı (2.215) veriyor ama CHP 11 yazıyor ve DSP'yi yazmıyor (Vikipedi CHP 10, DSP 1); "
                    "AK Parti, SP ve MHP oyları birebir. CNN Türk haberinde Kadışehri yok. YSK açık verisinde Kadışehri "
                    "ilçe merkezinin 2009 başkanlık ve meclis sandıkları yok (yalnız Halıköy beldesi), sandık/seçmen "
                    "karşılaştırılamadı."),
}


def yenileme_2009_vikipedi(secim, rec, rapor):
    if secim != "2009yerel":
        return 0
    from yenileme_2009 import WIKI, tablo  # noqa: E402
    idx = json.loads((WIKI / "_index.json").read_text(encoding="utf-8"))["sayfalar"]
    meclis = json.loads((BELDE_DIR / "2009yerel_belediye_meclisi.json").read_text(encoding="utf-8"))["birimler"]
    n = 0
    for geom, (dosya, ilce, aday, birim, haberler, fark_notu) in YENILEME_2009_VIKIPEDI.items():
        r = next(x for x in rec["ilceler"] if x.get("geomId") == geom)
        k = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
        if k.get("yenileme"):
            continue
        secmen, sandik, t = tablo(dosya, ilce)
        m, h = t["mart"], t["haziran"]
        h["oy"] = {p: o for p, o in h["oy"].items() if o}
        m["oy"] = {p: o for p, o in m["oy"].items() if o}
        # 29 Mart kaydi bu sayfadan gelmis olmali
        if {p: v["oy"] for p, v in r["oy"].items()} != m["oy"] or r.get("gecerliOy") != m["gecerliOy"]:
            raise SystemExit(f"{ilce}: kayıttaki 29 Mart değerleri Vikipedi'yle aynı değil")
        for ad, url_h, oy, oyk, gecersiz in haberler:
            tam = fark_notu is None
            if (tam and oy != h["oy"]) or any(h["oy"].get(p) != v for p, v in oy.items()):
                raise SystemExit(f"{ilce}: {ad} parti oyları Vikipedi 7 Haziran sütunuyla tutmuyor")
            if oyk is not None and oyk != h["gecerliOy"] + h["gecersizOy"] or gecersiz is not None and gecersiz != h["gecersizOy"]:
                raise SystemExit(f"{ilce}: {ad} oy kullanan/geçersiz tutmuyor")
        kontrol = []
        if birim:
            mb = meclis[birim]
            if mb["sandik"] != sandik or mb["toplam"]["secmen_SAYISI"] != secmen:
                raise SystemExit(f"{ilce}: sandık/seçmen YSK meclis ilçe merkezi birimiyle tutmuyor")
            kontrol.append("sandık ve seçmen YSK belediye meclisi ilçe merkezi birimiyle "
                           f"(data/raw/ysk/acikveri-belde-agrege/2009yerel_belediye_meclisi.json, birim {birim}) birebir")
        kontrol.append(("her parti oyu" if fark_notu is None else "AK Parti, SP ve MHP oyları") + " "
                       + " ve ".join(a for a, *_ in haberler) + " haberiyle birebir")
        url = next(v["url"] for v in idx.values() if v["dosya"] == dosya)
        mk = max(m["oy"], key=m["oy"].get)
        ilk = {"tarih": "29 Mart 2009", "kaynak": "Vikipedi il sayfası (29 Mart Sonuçları sütunu)", "kazanan": r.get("kazanan"),
               "oy": {p: v["oy"] for p, v in r["oy"].items()}, "adaylar": {p: v.get("aday") for p, v in r["oy"].items() if v.get("aday")}}
        for alan in ("gecerliOy", "gecersizOy", "secmen", "sandik", "katilim"):
            if r.get(alan) is not None:
                ilk[alan] = r.get(alan)
        if k:
            ilk["oncekiKaynak"] = copy.deepcopy(k)
        for alan in ("veriNotu", "not"):
            if r.get(alan):
                ilk[alan] = r.pop(alan)
        kazanan = max(h["oy"], key=h["oy"].get)
        g = h["gecerliOy"]
        r["oy"] = {p: {"aday": h["adaylar"].get(p), "oran": round(100 * o / g, 2), "oy": o} if h["adaylar"].get(p)
                   else {"oran": round(100 * o / g, 2), "oy": o} for p, o in sorted(h["oy"].items())}
        r["oy"][kazanan]["aday"] = aday
        r.update({"kazanan": kazanan, "gecerliOy": g, "secmen": secmen, "sandik": sandik, "katilim": h["katilim"]})
        if "gecersizOy" in r:
            r["gecersizOy"] = h["gecersizOy"]
        y = {"tarih": "7 Haziran 2009", "kaynak": f"Vikipedi il sayfası, {url} (7 Haziran Sonuçları sütunu)",
             "ikinciKaynak": [u for _, u, *_ in haberler], "kontrol": "; ".join(kontrol),
             "oyKullanan": g + h["gecersizOy"], "gecersizOy": h["gecersizOy"],
             "ek": str(YENILEME_2009_EK.relative_to(ROOT)), "ilkSecim": ilk}
        if fark_notu:
            y["haberFarki"] = fark_notu
        r["kaynak"] = {"ana": "wikipedia", "yenileme": y}
        r["not"] = (f"29 Mart 2009 seçimi iptal edildi ve 7 Haziran 2009'da yenilendi; gösterilen yenileme sonucudur "
                    f"({kazanan}, {aday}). 29 Mart'ta birinci {mk} idi. YSK açık verisinde bu seçim yok; kaynak Vikipedi"
                    + (", NTV ve CNN Türk ile birebir." if fark_notu is None else
                       "; NTV kazananı ve ilk iki partinin oylarını doğruluyor, küçük partilerde 1 oy fark var."))
        rapor.append({"secim": secim, "duzey": "ilce", "plaka": r["plaka"], "ad": r["ad"], "geomId": geom,
                      "durum": "yenileme_2009", "eskiKazanan": ilk["kazanan"], "kazanan": kazanan})
        n += 1
    return n


def sandik_denetimi(secim, rec=None):
    """Beldesi olan her ilcede ilce belediye baskanligi kaydinin sandik sayisi YSK'deki ilce merkezi
    belediyesinin sandik sayisina esit olmali (merkez + belde degil). Donus: (kontrol edilen, hatalar)."""
    yil = int(secim[:4])
    dosya = BELDE_DIR / f"{secim}_belediye_baskanligi.json"
    if not dosya.exists():
        return 0, [f"{dosya.name} yok"]
    A = json.loads(dosya.read_text(encoding="utf-8"))
    V = json.loads((V2_DIR / f"{secim}.json").read_text(encoding="utf-8"))
    rec = rec or load_election(secim)
    merkez, belde_sandik = {}, collections.Counter()
    for b in A["birimler"].values():
        ik = f"{b['ilId']}-{b['ilceId']}"
        if b["beldeId"]:
            belde_sandik[ik] += b["sandik"]
        else:
            merkez[ik] = b["sandik"]
    geom_ik = {}
    for ik, agg in V["ilceler"].items():
        geom = ilce_geom(ik, agg["ilId"], agg["ilceAdi"], yil, agg.get("sandikSayisi", 0))
        if geom and not (geom in geom_ik and V["ilceler"][geom_ik[geom]].get("sandikSayisi", 0) > 0
                         and agg.get("sandikSayisi", 0) == 0):
            geom_ik[geom] = ik
    n, hatalar = 0, []
    for r in rec["ilceler"]:
        ib = ((r.get("kaynak") or {}).get("ilceBelediyesi") or {}) if isinstance(r.get("kaynak"), dict) else {}
        m = re.search(r"birim (\d+-\d+)-0\)", ib.get("kaynak") or (ib.get("yskKontrol") or {}).get("kaynak") or "")
        ik = m.group(1) if m else geom_ik.get(r.get("geomId"))
        if not ik or not belde_sandik.get(ik) or ik not in merkez:
            continue
        if r.get("ilceGeneliSonuc"):
            continue  # YSK'de ilce merkezi sonucu yok ya da tutarsiz; kayitta belgeli
        n += 1
        if r.get("sandik") != merkez[ik]:
            hatalar.append(f"{secim} {r['plaka']} {r['ad']}: kayıt {r.get('sandik')} sandık, ilçe merkezi {merkez[ik]}"
                           f" (+ belde {belde_sandik[ik]})")
    return n, hatalar


def main():
    global UYGULA
    uygula = UYGULA = len(sys.argv) > 1 and sys.argv[1] == "uygula"
    rapor_yolu = sys.argv[sys.argv.index("--rapor") + 1] if "--rapor" in sys.argv else None
    rapor = []
    for secim in SECIMLER:
        sayac = isle(secim, rapor, uygula)
        if sayac is not None:
            print(secim, dict(sorted(sayac.items())))
    for d in rapor:
        if d["durum"] not in ("duzeltildi",) and not (d["durum"] == "onceki_duzeltme" and not d.get("farklar")):
            print("  ", {k: v for k, v in d.items() if v not in (None, "")})
    if rapor_yolu:
        alanlar = []
        for d in rapor:
            for k in d:
                if k not in alanlar:
                    alanlar.append(k)
        with open(rapor_yolu, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=alanlar)
            w.writeheader()
            w.writerows(rapor)
    if not uygula:
        print("(kontrol: hiçbir dosya yazılmadı; uygulamak için 'uygula')")


if __name__ == "__main__":
    main()
