"""
Icisleri Bakanligi "Il ve Ilce Kurulus Tarihleri 2018" (Iller Idaresi Genel
Mudurlugu) -> kaynak katmani:

  data/raw/icisleri/il-ilce-kurulus-2018/il_ve_ilce_kurulus_tarihleri_2018.pdf
  -> data/kaynaklar/icisleri/il_ilce_kurulus_2018.json

Her il sayfasi: il satiri + ilce satirlari (sira, ad, kurulus tarihi, kanun
numarasi, Resmi Gazete tarihi-sayisi) ya da "CUMHURIYET ONCESI". Ozel
durumlar:
  - KHK ile kurulanlar: kanun numarasi bir ust satirda ("694 SAYILI KANUN"),
    hucrede "HUKMUNDE", alt satirda "KARARNAME" -> kanun = "KHK 694".
  - Kararnameyle kurulan (Mardin/Kiziltepe): kanun numarasi yok.
  - Hatay sayfa basliginin kapanis yildizi eksik ("*HATAY").

Liste yalnizca 2018'de MEVCUT birimleri, GUNCEL adlariyla ve GUNCEL illerine
gore verir: kaldirilan ilceler (orn. Eminonu), ad degisiklikleri ve il
degisiklikleri bu kaynakta yoktur. Il satiri, merkez ilcesi olan illerde
merkez ilcenin de kurulus kaydidir.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_icisleri_kurulus.py
"""
import json
import pathlib
import re

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
PDF = ROOT / "data/raw/icisleri/il-ilce-kurulus-2018/il_ve_ilce_kurulus_tarihleri_2018.pdf"
OUT = ROOT / "data/kaynaklar/icisleri/il_ilce_kurulus_2018.json"

TARIH = r"(\d{2}\.\d{2}\.\d{4})"
SATIR = re.compile(r"^(?:(\d+)\s+)?(.+?)\s+(?:(CUMHURİYET ÖNCESİ)|" + TARIH + r"\s+(?:(\S+)\s+)?" + TARIH + r"\s*-\s*(\d+))\s*$")
KHK = re.compile(r"^(\d+)\s+SAYILI KANUN$")
ATLA = {"KURULUŞ KANUN RESMİ GAZETE", "İLİ/İLÇESİ", "TARİHİ NUMARASI TARİHİ VE SAYISI", "KARARNAME",
        "KARARNAMEYLE", "KURULMUŞTUR"}


def iso(t):
    return "-".join(reversed(t.split("."))) if t else None


def oku():
    kayitlar, okunamayan = [], []
    il = None
    with pdfplumber.open(PDF) as pdf:
        for no, pg in enumerate(pdf.pages[1:], start=2):
            khk = None
            kararname = False
            for satir in (pg.extract_text() or "").split("\n"):
                satir = satir.strip()
                m = re.match(r"^\*([^*]+)\*?$", satir)
                if m:
                    il = m.group(1).strip()
                    continue
                if not satir or re.fullmatch(r"\d+", satir):
                    continue
                if satir == "KARARNAMEYLE":
                    kararname = True
                    continue
                if satir in ATLA:
                    continue
                m = KHK.match(satir)
                if m:
                    khk = m.group(1)
                    continue
                m = SATIR.match(satir)
                if not m:
                    okunamayan.append({"sayfa": no, "il": il, "satir": satir})
                    continue
                sira, ad, oncesi, yur, kanun, rg_t, rg_s = m.groups()
                if not sira and any(k["il"] == il and k["tur"] == "il" for k in kayitlar):
                    continue  # sayfa devaminda il satiri tekrar basilmis
                if kanun == "HÜKMÜNDE":
                    kanun = f"KHK {khk}"
                elif kanun is None and not oncesi:
                    kanun = "kararname" if kararname else None
                khk, kararname = None, False
                kayitlar.append({
                    "il": il, "tur": "ilce" if sira else "il", "sira": int(sira) if sira else None, "ad": ad.strip(),
                    "cumhuriyetOncesi": bool(oncesi), "kurulus": iso(yur), "kanun": kanun,
                    "resmiGazete": {"tarih": iso(rg_t), "sayi": int(rg_s)} if rg_t else None, "sayfa": no,
                })
    return kayitlar, okunamayan


def main():
    kayitlar, okunamayan = oku()
    iller = sorted({k["il"] for k in kayitlar})
    veri = {
        "kaynak": {
            "yayin": "T.C. İçişleri Bakanlığı İller İdaresi Genel Müdürlüğü, İl ve İlçe Kuruluş Tarihleri 2018",
            "url": "https://www.icisleri.gov.tr/kurumlar/icisleri.gov.tr/IcSite/illeridaresi/Bilgiler2/%C4%B0l%20ve%20%C4%B0l%C3%A7e%20Kurulu%C5%9F%20Tarihleri%202018.pdf",
            "ham": str(PDF.relative_to(ROOT)),
            "guvenilirlik": "A (birincil/resmî)",
            "not": "Yalnızca 2018'de mevcut birimler, güncel ad ve güncel ile göre. Kaldırılan ilçeler, ad ve il "
                   "değişiklikleri bu kaynakta yok. 'kurulus' listedeki kuruluş tarihidir; kanunun kabul/yayım "
                   "tarihinden farklı olabilir ve ilçenin seçime ayrı birim olarak ilk girdiği tarih değildir "
                   "(ör. 3392 sayılı Kanunla 04.07.1987'de kurulan ilçeler 29.11.1987 genel seçimine ayrı girmedi).",
        },
        "ozet": {"il": len(iller), "ilce": sum(1 for k in kayitlar if k["tur"] == "ilce"),
                 "okunamayan": len(okunamayan)},
        "okunamayan": okunamayan,
        "kayitlar": kayitlar,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(veri["ozet"])
    for o in okunamayan:
        print("  okunamadı:", o)


if __name__ == "__main__":
    main()
