"""
Bazi iller (Malatya, Manisa, Kahramanmaras, Sanliurfa, Van, Samsun, Balikesir,
Mersin, Diyarbakir, Eskisehir, Antalya, Erzurum, Artvin) 2008-2017 arasinda
"Merkez" ilcelerini birden fazla modern ilceye boldu (buyuksehir kanunu
6360 vb.). YSK'nin acikveri API'si o eski "<Il> MERKEZ" ilcesini HALA
kendi (artik bosalmis/gecersiz) ilce_ID'siyle kayitli tutuyor - modern
973-ilce listesinde (2023 secimi baz alinarak) karsiligi yok, ama proje
zaten bu tam durum icin geo/historical/district_splits.json'da sentetik
"HIST-<Il>-Merkez" geomId'ler ve gercek poligonlar tutuyor (bkz.
geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson, build.py
tarafindan zaten gomuluyor).

Bu modul: verilen (plaka, YSK ilce adi "<IL> MERKEZ", secim_yili) icin,
secim_yili < splitYear ise HIST-*-Merkez geomId'sini dondurur.
"""
import json
import pathlib

ROOT = pathlib.Path("/Users/hamikumbasar/Desktop/Turkiye_Secim_Haritasi")
_splits = json.loads((ROOT / "geo" / "historical" / "district_splits.json").read_text(encoding="utf-8"))

# plaka -> [(syntheticId, splitYear), ...]
SPLITS_BY_PLAKA = {int(k): [(e["syntheticId"], e["splitYear"]) for e in v] for k, v in _splits.items()}

# 2012 6360 sayili Buyuksehir Kanunu ile "Merkez" ilcesi TEK bir yeni isimle
# degistirilen (COK-PARCALI bolunmeyen) iller - dogrulandi (2026-09-23,
# yerel-1994-1999-2004-pipeline/parse_ilce_belde.py'de kesfedildi, ayni
# eslemenin bir kopyasi). district_splits.json'daki 13 ilden FARKLI: bunlar
# sentetik birlesim poligonu GEREKTIRMIYOR, dogrudan modern ilcenin zaten
# var olan gercek geomId'sine eslenebiliyor. Etkilenen secimler: 2009yerel,
# 2011 genel, kismen 2014yerel/2014cb (2014'un basindaki secimler henuz
# yeni ilceler resmen olusmadan once olabilir). Denizli (20) BILEREK YOK -
# Pamukkale VE Merkezefendi diye IKI ayri ilceye bolundu, gercek cok-parcali
# bolunme, henuz cozulmedi.
MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA = {
    9: ("Efeler", 2014),         # Aydın
    48: ("Menteşe", 2014),        # Muğla
    52: ("Altınordu", 2014),      # Ordu
    59: ("Süleymanpaşa", 2014),   # Tekirdağ
    61: ("Ortahisar", 2012),      # Trabzon (6360 ile aynı anda, diger 2014)
    47: ("Artüklü", 2012),        # Mardin - web arastirmasiyla dogrulandi:
                                   # "Merkez ilcenin ismi Artuklu olarak
                                   # degistirilmistir" (basit 1:1 yeniden
                                   # adlandirma, Hatay/Van'in aksine COK-
                                   # PARCALI bolunme DEGIL - dogrulandi,
                                   # modern ilce listesinde Mardin'in TEK
                                   # yeni ilcesi Artuklu, digerleri onceden
                                   # de vardi).
}

# ARASTIRILDI VE COK-PARCALI BOLUNME OLDUGU DOGRULANDI (BASIT ISIM
# ESLEMESIYLE COZULEMEZ, gercek tarihsel poligon/HIST- birlesim gerekir,
# Denizli ile ayni kategori):
#  - Hatay (31): eski "Merkez" (Antakya Belediyesi) İKİ yeni ilceye bolundu
#    (Antakya + Defne, ikisi de eski Antakya Belediyesi mahallelerinden) +
#    ayrica Arsuz (Arsuz Belediyesi'nden) + Payas (Dortyol'un bir
#    parcasindan) - web arastirmasiyla dogrulandi (6360 sayili kanun metni).
#  - Van (65): eski "Merkez" resmi kaynakla dogrulanmis sekilde IKIYE
#    bolundu (Tusba + Ipekyolu, ikisi de 2012'de kuruldu) - web
#    arastirmasiyla dogrulandi.

_GENEL2023 = json.loads((ROOT / "data" / "normalized" / "genel_secimler.json").read_text(encoding="utf-8"))["2023"]
_MODERN_GEOMID_BY_PLAKA_AD = {}
for _i in _GENEL2023["ilceler"]:
    _MODERN_GEOMID_BY_PLAKA_AD.setdefault(_i["plaka"], {})[_i["ad"]] = _i["geomId"]


def resolve_historical_merkez(plaka: int, ilce_adi_ysk: str, secim_yili: int):
    """ilce_adi_ysk YSK'den geldigi haliyle (orn. 'MALATYA MERKEZ'). Eslesme
    yoksa None doner."""
    if not ilce_adi_ysk.upper().endswith("MERKEZ"):
        return None
    for synthetic_id, split_year in SPLITS_BY_PLAKA.get(plaka, []):
        if secim_yili < split_year and synthetic_id.endswith("-Merkez"):
            return synthetic_id
    if plaka in MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA:
        yeni_ad, split_year = MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA[plaka]
        if secim_yili < split_year:
            return _MODERN_GEOMID_BY_PLAKA_AD.get(plaka, {}).get(yeni_ad)
    return None
