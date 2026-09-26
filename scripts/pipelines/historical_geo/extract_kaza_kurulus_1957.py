"""
7033 sayili "Yeniden (78) Kaza Kurulmasi ve Izmir Vilayetine Bagli Kusadasi
Kazasinin Aydin Vilayetine Baglanmasi Hakkinda Kanun" (RG 27.06.1957, 9644)
ek cetvelleri -> kaynak katmani (Faz 2: soy).

Bu sayi 1987/1990 kanunlarindan farkli dizilmis, bu yuzden ayri okuyucu:
  - Kanun metni ve cetveller ayni sayida; mevzuat.gov.tr'de PDF metni yok.
  - Sayfalar iki sutunlu; OCR iki sutunu ayni satira karistiriyor -> kelimeler
    x konumuna gore (sayfa ortasindaki en bos dikey serit) sol/sag ayrilir.
  - Donem dili: Vilayet / Kaza / Nahiye. Her kaza blogu: "Vilâyeti Kazanın adı
    Merkezi" basligi + "<vilayet> <kaza> <merkez>" satiri + koy satirlari
    ("N <koy> X Vilâyeti Y Kazasının Z Nahiyesinden"; tekrarlar "»" ile).
  - PDF 25 sayfalik gazetenin uc kopyasi; yalniz ilk kopya okunur.

Soy blok duzeyinde cikarilir: bir kaza blogunda anilan BUTUN "Y Kazasının"
kaynaklari. "»" satirlari ustteki kaynagi tekrar eder, yeni kaynak getirmez.
Satir numaralari bu taramada guvenilir denetlenemedigi icin sonuc
`guven: orta` (1987/1990 listelerindeki satir satir denetim yok).

Yururluk: cetvel (1) 01.09.1957, (1/A) 01.04.1958, (1/B) 01.04.1959, (1/C)
01.04.1960; kesin tarih Icisleri kurulus listesinden alinir.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_kaza_kurulus_1957.py
"""
import collections
import json
import pathlib
import re
import sys

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from common.turkish_text import fold  # noqa: E402
from extract_ilce_kurulus_kanunu import benzer, il_ilce_adlari  # noqa: E402

KANUN = "7033"
RG = "data/raw/resmi_gazete/9644.pdf"
# gazete sayfa sirasi (ilk kopya): 17437 = PDF s.24, 17438-17454 = s.1-17
SAYFA_SIRASI = [24] + list(range(1, 18))
SONRAKI_GENEL = "1961"
OUT = ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus/7033.json"
CETVEL_TARIH = {"1": "1957-09-01", "1/A": "1958-04-01", "1/B": "1959-04-01", "1/C": "1960-04-01"}


def sutunlar(pg):
    """Sayfayi ortadaki en bos dikey seritten sol/sag ikiye boler; her sutun
    satirlarini (ust konuma gore) dondurur."""
    ws = pg.extract_words(keep_blank_chars=False)
    W = float(pg.width)
    kapsam = collections.Counter()
    for w in ws:
        for x in range(int(w["x0"]), int(w["x1"]) + 1):
            kapsam[x] += 1
    orta = min(range(int(W * 0.35), int(W * 0.65)), key=lambda x: (kapsam[x], abs(x - W / 2)))
    out = []
    for secici in (lambda w: w["x1"] <= orta, lambda w: w["x0"] >= orta):
        satir = collections.defaultdict(list)
        for w in ws:
            if secici(w):
                satir[round(w["top"] / 3.5)].append(w)
        out.append([" ".join(x["text"] for x in sorted(v, key=lambda w: w["x0"])) for _, v in sorted(satir.items())])
    return out


KAYNAK = re.compile(r"([^\s»(]+(?:\s+K\.)?)\s+Vil[âa]y[ae]ti\s*\(?\s*([^\s»]+(?:\s[^\s»]+)?)\s+K\s?a\s?z\s?a\s?s\s?[ıi]\s?n\s?[ıi]\s?n")
BASLIK = re.compile(r"Vil[âa]y\S*\s+Kaza\S*\s+ad\S*\s+Merkez", re.I)
CETVEL = re.compile(r"[\[(]\s*([1lI])\s*(?:/\s*([ABC]))?\s*[\])]\s*SAYILI\s+CETVEL", re.I)


def main():
    pdf = pdfplumber.open(ROOT / RG)
    il_liste = json.loads((ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text())
    il_adlari = {fold(v["il_ADI"]): int(k) for k, v in il_liste.items()}
    il_adlari.update({"AFYON": 3, "AFYON K": 3, "ICEL": 33, "HAKARI": 30, "MARAS": 46, "URFA": 63, "GANTEP": 27})
    sonraki = il_ilce_adlari(SONRAKI_GENEL, set(range(1, 82)))
    # Icisleri: bu kanunla kurulan ilceler (guncel il ve ad); blok basligi bunlardan
    # birine eslesmezse blok kullanilmaz
    icis = json.loads((ROOT / "data/kaynaklar/icisleri/il_ilce_kurulus_2018.json").read_text())["kayitlar"]
    kanun_ilceleri = [(k["il"], k["ad"], k["kurulus"]) for k in icis if k["kanun"] == KANUN]

    def il_bul(ad):
        a = fold(ad).replace(".", "")
        en = max(il_adlari, key=lambda k: benzer(a, k))
        return il_adlari[en] if benzer(a, en) >= 0.75 else None

    def ilce_bul(pl, ad, esik=0.75):
        adlar = sonraki.get(pl, {})
        if not adlar or not ad:
            return None, None
        en = max(adlar, key=lambda k: benzer(ad, k))
        return (en, adlar[en]) if benzer(ad, en) >= esik else (None, None)

    satirlar = []
    for no in SAYFA_SIRASI:
        for sutun in sutunlar(pdf.pages[no - 1]):
            satirlar += [(no, s) for s in sutun]

    ozet, bloklar = [], []
    cetvel, blok, bekle = "1", None, False
    for no, s in satirlar:
        m = CETVEL.search(s)
        if m:
            cetvel = "1" + (f"/{m.group(2).upper()}" if m.group(2) else "")
            continue
        if BASLIK.search(s):
            bekle = True
            continue
        if bekle:
            tok = [t for t in s.replace("'", "").split() if not re.match(r"^(Vil[âa]y\S*|K\.|\*)$", t)]
            if len(tok) >= 2 and il_bul(tok[0]):
                # yeni kaza adi Icisleri 7033 listesinde (herhangi bir ilde; il sonradan
                # degismis olabilir) eslesmeli
                aday = max(kanun_ilceleri, key=lambda k: benzer(tok[1], k[1]))
                gecerli = benzer(tok[1], aday[1]) >= 0.75
                blok = {"cetvel": cetvel, "il": tok[0], "plaka": il_bul(tok[0]), "ad": tok[1],
                        "merkez": " ".join(tok[2:]), "sayfa": no, "kaynaklar": collections.Counter(), "satir": 0,
                        "icisleri": aday if gecerli else None, "gecerli": gecerli}
                bloklar.append(blok)
                bekle = False
            continue
        m = re.match(r"^»?\s*(\d{1,2})\s+(\S+)\s+(\S+)\s+(\S.*)$", s)
        if m and blok is None and il_bul(m.group(2)):
            ozet.append({"sira": int(m.group(1)), "cetvel": cetvel, "il": m.group(2), "ad": m.group(3),
                         "merkez": m.group(4).strip(" *"), "sayfa": no})
            continue
        if blok is None:
            continue
        for k in KAYNAK.finditer(s):
            blok["kaynaklar"][(k.group(1), k.group(2).strip("( "))] += 1
        if re.match(r"^\d{1,3}\s+\S", s):
            blok["satir"] += 1

    ilceler = []
    gecersiz = [f"{b['il']} {b['ad']} (s.{b['sayfa']})" for b in bloklar if not b["gecerli"]]
    bloklar = [b for b in bloklar if b["gecerli"]]
    for i, b in enumerate(bloklar, 1):
        yeni_ad, yeni_g = ilce_bul(b["plaka"], b["ad"])
        kay = []
        for (vil, kaza), c in b["kaynaklar"].most_common():
            pl = il_bul(vil) or b["plaka"]
            ad, g = ilce_bul(pl, kaza)
            kay.append({"okunan": f"{vil} Vilâyeti {kaza} Kazası", "ad": ad, "geomId": g, "plaka": pl, "anilma": c})
        # ayni ilce farkli OCR yazimlariyla birden cok kez gelebilir: geomId'ye gore birlestir
        birlesik = collections.OrderedDict()
        for k in kay:
            anahtar = k["geomId"] or k["okunan"]
            if anahtar in birlesik:
                birlesik[anahtar]["anilma"] += k["anilma"]
            else:
                birlesik[anahtar] = dict(k)
        kay = list(birlesik.values())
        ilceler.append({
            "listeNo": i, "cetvel": b["cetvel"], "yururlukCetvel": CETVEL_TARIH.get(b["cetvel"]),
            "il": b["il"], "plaka": b["plaka"], "ad": b["ad"], "merkez": b["merkez"], "rgSayfalari": [b["sayfa"]],
            "yeniIlce": {"ad": yeni_ad, "geomId": yeni_g, "plaka": b["plaka"], "secim": SONRAKI_GENEL} if yeni_g else None,
            "satirSayisi": b["satir"],
            "eskiIlceler": [{"ad": k["ad"], "geomId": k["geomId"], "plaka": k["plaka"], "birimSayisi": k["anilma"],
                             "okunan": k["okunan"]} for k in kay],
            # baska ilden kaynak aniliyorsa blok karisik olabilir (sutun/baslik kaymasi):
            # tek kaynak sayilmaz
            "ilDisiAnilma": [k["okunan"] for k in kay if k["plaka"] != b["plaka"]],
            "tekKaynak": len(kay) == 1 and kay[0]["geomId"] is not None and kay[0]["plaka"] == b["plaka"],
            "icisleri": {"il": b["icisleri"][0], "ad": b["icisleri"][1], "kurulus": b["icisleri"][2]},
            "cozulemeyenKaynak": [k["okunan"] for k in kay if not k["geomId"]],
            "guven": "orta", "ekHukum": None, "eksikSira": [],
        })
    veri = {
        "kanun": KANUN, "ad": "Yeniden (78) Kaza Kurulması ve İzmir Vilâyetine Bağlı Kuşadası Kazasının Aydın "
                              "Vilâyetine Bağlanması Hakkında Kanun",
        "kabul": "1957-06-19", "resmiGazete": {"tarih": "1957-06-27", "sayi": 9644},
        "kaynaklar": {"ekListeler": RG, "maddeler": RG, "rgUrl": "https://www.resmigazete.gov.tr/arsiv/9644.pdf",
                      "mevzuatUrl": None},
        "guvenilirlik": "A (birincil/resmî); 1957 taraması zayıf OCR, iki sütunlu. Soy blok düzeyinde: kaza "
                        "bloğunda anılan tüm 'X Vilâyeti Y Kazasının' kaynakları; satır satır denetim yapılamadı "
                        "(guven: orta).",
        "digerHukumler": [{"madde": 2, "metin": "İzmir Vilâyetine bağlı Kuşadası kazası 1.IX.1957 tarihinde mer'i "
                                                "olmak üzere Aydın Vilâyetine bağlanmıştır.",
                           "eventType": "province_changed", "effectiveDate": "1957-09-01", "provinceBefore": 35,
                           "provinceAfter": 9, "unit": "Kuşadası"}],
        "ozetTablo": ozet,
        "ozet": {"ilce": len(ilceler), "tekKaynak": sum(1 for x in ilceler if x["tekKaynak"]),
                 "cokKaynak": sum(1 for x in ilceler if len(x["eskiIlceler"]) > 1),
                 "kaynaksiz": [x["ad"] for x in ilceler if not x["eskiIlceler"]],
                 "cozulemeyenKaynak": sum(len(x["cozulemeyenKaynak"]) for x in ilceler),
                 "geomIdsizYeniIlce": [x["ad"] for x in ilceler if not x["yeniIlce"]],
                 "ozetTabloSatir": len(ozet), "gecersizBaslik": gecersiz,
                 "icisleri7033": len(kanun_ilceleri),
                 "okunmayanIcisleri": sorted({k[1] for k in kanun_ilceleri} - {x["icisleri"]["ad"] for x in ilceler}),
                 "ilDisiAnilmali": sum(1 for x in ilceler if x["ilDisiAnilma"])},
        "ilceler": ilceler,
    }
    OUT.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(veri["ozet"], ensure_ascii=False))


if __name__ == "__main__":
    main()
