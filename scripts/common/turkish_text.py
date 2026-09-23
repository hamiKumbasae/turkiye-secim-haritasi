"""
Turkce metin normalizasyonu - farkli pipeline'lardaki (YSK ilce/parti adi
eslestirme, OSM mahalle adi eslestirme) 5+ neredeyse birebir kopyasinin
TEK, paylasimli hali.
"""
import re
import unicodedata

SUFFIXES_MAHALLE = ["MAHALLESI", "MAH", "KOYU", "KOY", "BELDESI", "BELDE"]


def fold(s):
    """Karsilastirma icin Turkce diakritik/buyuk-kucuk/noktalama normalizasyonu
    ('İstanbul-Beşiktaş' -> 'ISTANBUL BESIKTAS')."""
    if s is None:
        return ""
    s = s.strip()
    s = (s.replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g")
           .replace("Ü", "U").replace("ü", "u").replace("Ş", "S").replace("ş", "s")
           .replace("Ö", "O").replace("ö", "o").replace("Ç", "C").replace("ç", "c"))
    s = s.upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace(".", "").replace("-", " ").replace("'", "")
    return " ".join(s.split())


def fold_party(s):
    """fold() + parti adlarina ozel: 'PARTİSİ'/'PARTİ' sozcukleri ve parantez
    ici metin kaldirilir ('Cumhuriyet Halk Partisi' -> 'CUMHURIYET HALK')."""
    s = fold(s)
    return re.sub(r"\bPARTISI\b|\bPARTI\b|\(.*?\)", "", s).strip()


def fold_mahalle(s):
    """fold() + mahalle/koy/belde EK sozcuklerini sondan kaldirir
    ('Kızılay Mahallesi' -> 'KIZILAY')."""
    parts = fold(s).split(" ")
    while parts and parts[-1] in SUFFIXES_MAHALLE:
        parts.pop()
    return " ".join(parts)
