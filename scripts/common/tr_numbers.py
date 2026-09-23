"""
YSK PDF tablolarindaki Turkce-bicimli sayilari (bin ayiraci '.', ondalik
ayiraci ',') ayristirir - farkli pipeline'lardaki 6 kopyanin TEK hali.

strict=True (varsayilan, PDF ayristirma script'lerinin cogunda kullanilan
davranis): bos hucre -> None, GECERSIZ (sayi olmayan) hucre -> ValueError
YUKSELTIR - PDF formati beklenmedikse GURULTULU sekilde durur, sessizce
yanlis/eksik veri uretmez.

strict=False (referandum script'lerinde kullanilan davranis): bos VEYA
sayi-olmayan hucre -> None doner, hicbir zaman patlamaz - bazi referandum
PDF'lerinde sayisal olmayan (orn. '-') hucreler beklendigi durumlar icin.
"""


def to_int(s, strict=True):
    if s is None:
        return None
    s = s.replace(".", "").strip()
    if not s:
        return None
    if strict:
        return int(s)
    return int(s) if s.lstrip("-").isdigit() else None


def to_float(s):
    s = (s or "").replace(",", ".").strip()
    return float(s) if s else None
