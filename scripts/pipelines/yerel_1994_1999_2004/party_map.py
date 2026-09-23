"""
1994/1999/2004 yerel secimlerinin YSK PDF'lerindeki parti kodlarini
partiler.json anahtarlarina esler - merge_into_normalized.py (il-duzeyi)
ve merge_ilce_belde.py (ilce/belde-duzeyi) AYNI eslemeyi paylasir.
"""

STATIC_MAP = {
    "ANAP": "ANAP", "BAĞIMSIZLAR": "Bağımsız", "BBP": "BBP", "BP": "BP",
    "CHP": "CHP", "DP": "DP", "DSP": "DSP", "DYP": "DYP", "MHP": "MHP",
    "MİLLET PARTİSİ": "MP92", "RP": "RP", "SBP": "SBP", "SHP": "SHP",
    "YDP": "YDP", "İP": "İP", "DBP": "DBP99", "DEHAP": "DEHAP",
    "DEPAR": "DEPAR", "DTP": "DEMTP", "EMEP": "EMEP", "FP": "FP",
    "HADEP": "HADEP", "LDP": "LDP", "SİP": "SİP", "ÖDP": "ÖDP",
    "AK PARTİ": "AK Parti", "ATP": "ATP", "BTP": "BTP", "GENÇ PARTİ": "GP",
    "SAADET PARTİSİ": "SP", "TKP": "TKP", "YTP": "YTP02",
}

# Guvenlik kontrolu: parti oylari toplami resmi 'gecerli oy sayisi'ndan
# %2'den fazla sapan bir kayit YAZILMAZ (pdfplumber'in bazi PDF'lerde
# gorulen nadir sutun-hizalama sorununa karsi - bkz. PROVENANCE.md).
MAX_GECERLI_OY_SAPMA = 0.02  # %2
