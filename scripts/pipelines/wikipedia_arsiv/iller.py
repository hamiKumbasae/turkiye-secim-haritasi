"""
Wikipedia il sayfasi basligindaki il adi ("Seyhan'da 1950 ...") -> plaka.

Modern adlar data/raw/ysk/acikveri-il-ilce-listesi.json'dan. Tarihsel adlar
yalnizca ACIK bir halef ili varsa eslenir (Seyhan -> Adana, Kangiri ->
Cankiri ...). Sonradan kaldirilan iller (Ergani, Genc, Kozan, Siverek,
Catalca, Gelibolu, Biga, Sebinkarahisar, Cebel-i Bereket) plakasiz (None)
kalir: bugunku hicbir ilin tamamina karsilik gelmiyorlar.
"""
import json
import pathlib
import re

from common.turkish_text import fold

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent

TARIHSEL = {
    "Afyon": 3, "Afyonkarahisar": 3, "Bayazıt": 4, "Bozok": 66, "Canik": 55, "Dersim": 62,
    "Diyarbekir": 21, "Elaziz": 23, "Ertuğrul": 11, "Gaziayıntab": 27, "Kangırı": 18,
    "Karahisar-ı Şarki": 28, "Karesi": 10, "Konstantiniyye": 34, "Maraş": 46, "Menteşe": 48,
    "Saruhan": 45, "Seyhan": 1, "Urfa": 63, "Çoruh": 8, "İçel": 33, "İçel ve Mersin": 33,
    "Hakkâri": 30, "Mersin": 33, "Kahramanmaraş": 46, "Şanlıurfa": 63,
}
KALDIRILAN = {"Ergani", "Genç", "Kozan", "Siverek", "Çatalca", "Gelibolu", "Biga",
              "Şebinkarahisar", "Cebel-i Bereket"}

_MODERN = {}
for plaka, v in json.loads((ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text(encoding="utf-8")).items():
    _MODERN[fold(v["il_ADI"])] = int(plaka)
_TARIHSEL_F = {fold(k): v for k, v in TARIHSEL.items()}


def il_adi(baslik):
    """"Seyhan'da 1950 Türkiye yerel seçimleri" -> "Seyhan"; il sayfasi degilse None."""
    m = re.match(r"^(.+?)['’](?:d|t)[ae] ", baslik)
    return m.group(1) if m else None


def plaka(ad):
    if ad is None or ad in KALDIRILAN:
        return None
    f = fold(ad)
    return _TARIHSEL_F.get(f) or _MODERN.get(f)
