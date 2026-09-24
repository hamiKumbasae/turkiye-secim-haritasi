"""
Wikipedia parti linki / kisaltmasi -> partiler.json anahtari.

Oncelik link hedefi (makale adi) - kisaltma ayni partiye farkli yillarda
farkli (ya da ayni kisaltma farkli partilere) verilebildigi icin daha
guvenilir. Link yoksa kisaltmaya bakilir. Eslenemeyen -> None (kaynak
katmaninda ham hali saklanir, birlestirmede "Diğer"e duser).
"""
from common.turkish_text import fold

LINK = {
    "Cumhuriyet Halk Partisi": "CHP",
    "Adalet Partisi (1961-1981)": "AP",
    "Adalet Partisi (1923)": "AP23",
    "Bağımsız siyasetçi": "Bağımsız",
    "Bağımsız": "Bağımsız",
    "Millî Selamet Partisi": "MSP", "Milli Selamet Partisi": "MSP",
    "Demokratik Parti (Türkiye)": "DEMP73",
    "Milliyetçi Hareket Partisi": "MHP",
    "Yeni Türkiye Partisi (1961)": "YTP61",
    "Yeni Türkiye Partisi (2002)": "YTP02",
    "Cumhuriyetçi Köylü Millet Partisi": "CKMP",
    "Cumhuriyetçi Güven Partisi": "CGP",
    "Güven Partisi": "CGP",
    "Millet Partisi (1962)": "MP62",
    "Millet Partisi (1948)": "MP50",
    "Millet Partisi (1992)": "MP92",
    "Türkiye İşçi Partisi (1961)": "TİP",
    "Demokrat Parti (1946)": "DP",
    "Demokrat Parti (1970)": "DEMP73",
    "Demokrat Parti (2007)": "DP",
    "Türkiye Sosyalist İşçi Partisi": "TSİP",
    "Türkiye Birlik Partisi": "BP69",
    "Birlik Partisi": "BP69",
    "Sosyalist Devrim Partisi": "SDP",
    "Karma Liste": "KARMA",
    "Türkiye Köylü Partisi": "TKöyP",
    "Millî Kalkınma Partisi": "MKP", "Milli Kalkınma Partisi": "MKP",
    "Cumhuriyetçi Millet Partisi": "CMP",
    "Hürriyet Partisi (Türkiye)": "HP57", "Hürriyet Partisi": "HP57",
    "Vatan Partisi (1954)": "VP57",
    "Anavatan Partisi": "ANAP",
    "Doğru Yol Partisi": "DYP",
    "Sosyaldemokrat Halkçı Parti": "SHP",
    "Sosyal Demokrasi Partisi": "SODEP",
    "Halkçı Parti": "HP", "Halkçı Parti (Türkiye)": "HP",
    "Milliyetçi Demokrasi Partisi": "MDP",
    "Refah Partisi": "RP",
    "Demokratik Sol Parti": "DSP",
    "Milliyetçi Çalışma Partisi": "MÇP",
    "Islahatçı Demokrasi Partisi": "IDP",
    "Fazilet Partisi": "FP",
    "Adalet ve Kalkınma Partisi": "AK Parti",
    "Saadet Partisi": "SP",
    "Büyük Birlik Partisi": "BBP",
    "Halkın Demokrasi Partisi": "HADEP",
    "Demokratik Halk Partisi": "DEHAP",
    "Demokratik Toplum Partisi": "DTP",
    "Barış ve Demokrasi Partisi": "BDP",
    "Halkların Demokratik Partisi": "HDP",
    "Halkların Eşitlik ve Demokrasi Partisi": "DEM Parti",
    "İyi Parti": "İYİ Parti", "İYİ Parti": "İYİ Parti",
    "Yeniden Refah Partisi": "YENİDEN REFAH",
    "Genç Parti": "GP",
    "Bağımsız Türkiye Partisi": "BTP",
    "Demokratik Bölgeler Partisi": "DBP99",
    "Hür Dava Partisi": "HÜDAPAR",
    "Türkiye Komünist Partisi (2001)": "TKP",
    "Vatan Partisi (2015)": "VATAN",
    "İşçi Partisi (Türkiye)": "İP",
    "Zafer Partisi": "ZP",
    "Demokratik Sol Parti (Türkiye)": "DSP",
    "Anadolu Partisi": "Anadolu Partisi",
    "Gelecek Partisi": "Gelecek Partisi",
    "Demokrasi ve Atılım Partisi": "DEVA",
    "Emek Partisi": "EMEP",
    "Yeni Parti (1993)": "YENP95",
    "Değişim Partisi": "DEĞTP",
    "Memleket Partisi": "MEMLEKET",
    "Yurt Partisi": "YURT-P",
    "Liberal Demokrat Parti (Türkiye)": "LDP",
    "Halkın Yükselişi Partisi": "HYP",
    "Hak ve Özgürlükler Partisi": "HAK-PAR",
    "Millî Yol Partisi": "MİLLİYOL", "Milli Yol Partisi": "MİLLİYOL",
    "Sol Parti": "SOL PARTİ",
    "Türkiye İşçi Partisi (2017)": "TİP",
    "Yeşil Sol Parti": "YEŞİL SOL",
}

ABBR = {
    "CHP": "CHP", "AP": "AP", "BĞMSZ": "Bağımsız", "BAĞIMSIZ": "Bağımsız", "BAĞ": "Bağımsız",
    "MSP": "MSP", "MHP": "MHP", "YTP": "YTP61", "CKMP": "CKMP", "GP": "CGP", "CGP": "CGP",
    "MP": "MP62", "TİP": "TİP", "TSİP": "TSİP", "BP": "BP69", "TBP": "BP69", "SDP": "SDP",
    "KARMA": "KARMA", "TKP": "TKöyP", "MKP": "MKP", "CMP": "CMP",
    "ANAP": "ANAP", "DYP": "DYP", "SHP": "SHP", "SODEP": "SODEP", "HP": "HP", "MDP": "MDP",
    "RP": "RP", "DSP": "DSP", "MÇP": "MÇP", "IDP": "IDP", "FP": "FP", "AKP": "AK Parti",
    "AK PARTİ": "AK Parti", "SP": "SP", "SAADET": "SP", "BBP": "BBP", "HADEP": "HADEP",
    "DEHAP": "DEHAP", "DTP": "DTP", "BDP": "BDP", "HDP": "HDP", "DEM": "DEM Parti",
    "İYİ": "İYİ Parti", "YRP": "YENİDEN REFAH", "DBP": "DBP99", "HÜDA PAR": "HÜDAPAR",
    "ZP": "ZP", "DEVA": "DEVA", "EMEP": "EMEP", "TKH": "TKH",
}

# Link olmadan duz yazilmis parti/ittifak/aday adlari (link hedefi degil, gorunen metin)
AD = {
    "Cumhuriyet Halk Partisi": "CHP", "Cumhuriyet Halk Fırkası": "CHP",
    "Anavatan Partisi": "ANAP", "Doğru Yol Partisi": "DYP", "Refah Partisi": "RP",
    "Demokratik Sol Parti": "DSP", "Milliyetçi Hareket Partisi": "MHP",
    "Sosyaldemokrat Halkçı Parti": "SHP", "Sosyal Demokrat Halkçı Parti": "SHP",
    "Fazilet Partisi": "FP", "Cumhuriyetçi Köylü Millet Partisi": "CKMP",
    "Halkın Demokrasi Partisi": "HADEP", "Demokratik Halk Partisi": "DEHAP",
    "Adalet ve Kalkınma Partisi": "AK Parti", "Özgürlük ve Dayanışma Partisi": "ÖDP",
    "Yeniden Doğuş Partisi": "YDP", "Yeniden Doğuş Partisi (Türkiye)": "YDP",
    "Halkın Kurtuluş Partisi": "HKP", "Komünist Parti (Türkiye)": "KP", "Komünist Parti": "KP",
    "Sol Parti (Türkiye)": "SOL PARTİ", "SOL Parti": "SOL PARTİ", "SOL": "SOL PARTİ",
    "Merkez Parti": "MEP", "Demokratik Halk Partisi (Türkiye)": "DEHAP",
    "Aydınlık Türkiye Partisi": "ATP", "Demokrat Türkiye Partisi": "DEMTP",
    "Cumhur İt.": "Cumhur İttifakı", "Cumhur İttifakı": "Cumhur İttifakı", "CUMHUR": "Cumhur İttifakı",
    "Millet İt.": "Millet İttifakı", "Millet İttifakı": "Millet İttifakı", "MİLLET": "Millet İttifakı",
    "ATA": "Ata İttifakı", "Ata İttifakı": "Ata İttifakı", "MEMLEKET": "MEMLEKET",
    "S. Güç Bir.": "Sosyalist Güç Birliği İttifakı", "Sosyalist Güç Birliği İttifakı": "Sosyalist Güç Birliği İttifakı",
    "Emek ve Özgürlük İttifakı": "Emek ve Özgürlük İttifakı", "EMEK": "Emek ve Özgürlük İttifakı",
    "Recep Tayyip Erdoğan": "Recep Tayyip Erdoğan", "Erdoğan": "Recep Tayyip Erdoğan",
    "Muharrem İnce": "Muharrem İnce", "İnce": "Muharrem İnce",
    "Meral Akşener": "Meral Akşener", "Akşener": "Meral Akşener",
    "Selahattin Demirtaş": "Selahattin Demirtaş", "Demirtaş": "Selahattin Demirtaş",
    "Temel Karamollaoğlu": "Temel Karamollaoğlu", "Karamollaoğlu": "Temel Karamollaoğlu",
    "Doğu Perinçek": "Doğu Perinçek", "Perinçek": "Doğu Perinçek",
    "Kemal Kılıçdaroğlu": "Kemal Kılıçdaroğlu", "Kılıçdaroğlu": "Kemal Kılıçdaroğlu",
    "Sinan Oğan": "Sinan Oğan", "Oğan": "Sinan Oğan",
    "Ekmeleddin İhsanoğlu": "Ekmeleddin İhsanoğlu", "İhsanoğlu": "Ekmeleddin İhsanoğlu",
    "Halkçı Parti": "HP", "Yurt Partisi": "YP",
    "Türkiye Komünist Partisi": "TKP", "Büyük Birlik Partisi": "BBP", "Saadet Partisi": "SP",
    "Demokrat Parti": "DP", "Genç Parti": "GP", "Bağımsız Türkiye Partisi": "BTP",
    "İşçi Partisi": "İP", "Liberal Demokrat Parti": "LDP", "Emek Partisi": "EMEP",
    "Barış ve Demokrasi Partisi": "BDP", "Halkların Demokratik Partisi": "HDP",
    "İyi Parti": "İYİ Parti", "Vatan Partisi": "VATAN", "Hür Dava Partisi": "HÜDAPAR",
    "Yeniden Refah Partisi": "YENİDEN REFAH", "Zafer Partisi": "ZP", "Türkiye İşçi Partisi": "TİP",
    "Yeşil Sol Parti": "YEŞİL SOL", "Memleket Partisi": "MEMLEKET", "Demokratik Toplum Partisi": "DTP",
    "Millî Selamet Partisi": "MSP", "Milli Selamet Partisi": "MSP", "Cumhuriyetçi Güven Partisi": "CGP",
    "Türkiye Birlik Partisi": "TBP73", "Demokratik Parti": "DEMP73", "Milliyetçi Çalışma Partisi": "MÇP",
    "Milliyetçi Demokrasi Partisi": "MDP", "Sosyal Demokrasi Partisi": "SODEP",
    "Islahatçı Demokrasi Partisi": "IDP", "Yeni Demokrasi Hareketi": "YDH", "Yeni Parti": "YENP95",
    "Demokratik Barış Hareketi": "DBP99", "Demokrasi ve Barış Partisi": "DEPAR",
    "Sosyalist İktidar Partisi": "SİP", "Hak ve Eşitlik Partisi": "HEPAR", "Anadolu Partisi": "Anadolu Partisi",
    "Halkın Sesi Partisi": "HAS", "Millet Partisi": "MP92", "Türkiye Köylü Partisi": "TKöyP",
    "Cumhuriyetçi Millet Partisi": "CMP", "Hürriyet Partisi": "HP57", "Vatan Partisi (1954)": "VP57",
}
# Ayni ad farkli donemde farkli parti: (ad, ilk_yil, son_yil) -> anahtar
AD_DONEM = [
    ("Adalet Partisi", 1961, 1981, "AP"), ("Yeni Türkiye Partisi", 1961, 1970, "YTP61"),
    ("Yeni Türkiye Partisi", 2002, 2004, "YTP02"), ("Demokrat Parti", 1946, 1960, "DP"),
    ("Millet Partisi", 1948, 1960, "MP50"), ("Millet Partisi", 1962, 1977, "MP62"),
    ("Halkçı Parti", 1983, 1985, "HP"), ("Türkiye Birlik Partisi", 1966, 1972, "BP69"),
    ("Yurt Partisi", 2018, 9999, "YURT-P"), ("Demokratik Parti", 1970, 1980, "DEMP73"),
    ("Türkiye Komünist Partisi", 1920, 1990, None), ("Türkiye İşçi Partisi", 1961, 1980, "TİP"),
    ("Vatan Partisi", 1954, 1960, "VP57"), ("Hürriyet Partisi", 1955, 1958, "HP57"),
]
_LINK_F = {fold(k): v for k, v in LINK.items()}
_AD_F = {fold(k): v for k, v in AD.items()}
_AD_DONEM_F = [(fold(a), y0, y1, k) for a, y0, y1, k in AD_DONEM]


# Ayni kisaltma farkli donemlerde farkli parti: (kisaltma, ilk_yil, son_yil) -> anahtar
ABBR_DONEM = [
    ("GP", 2002, 9999, "GP"), ("MP", 1946, 1958, "MP50"), ("MP", 1992, 9999, "MP92"),
    ("DP", 1946, 1960, "DP"), ("DP", 1970, 1981, "DEMP73"), ("DP", 2007, 9999, "DP"),
    ("TKP", 2001, 9999, "TKP"), ("HP", 1955, 1958, "HP57"), ("YTP", 2002, 9999, "YTP02"),
    ("TİP", 2017, 9999, "TİP"),
]


def _ad_ile(ad, yil):
    f = fold(ad or "")
    if not f:
        return None
    if yil:
        for a, y0, y1, k in _AD_DONEM_F:
            if f == a and y0 <= yil <= y1:
                return k
    return _AD_F.get(f) or _LINK_F.get(f)


def parti_anahtari(link, kisaltma, yil=None, ad=None):
    """(anahtar, yontem) - yontem: 'link' | 'ad' | 'kisaltma' | None.
    Oncelik: link hedefi > gorunen ad > kisaltma (link/ad yoksa kisaltma
    parametresi ad olarak da denenir - bazi tablolarda tek hucre var)."""
    if link and fold(link) in _LINK_F:
        return _LINK_F[fold(link)], "link"
    if link:
        k = _ad_ile(link, yil)
        if k:
            return k, "link"
    for cand in (ad, kisaltma):
        k = _ad_ile(cand, yil)
        if k:
            return k, "ad"
    k = (kisaltma or "").upper().replace(".", "").strip()
    if yil:
        for ab, y0, y1, key in ABBR_DONEM:
            if k == ab and y0 <= yil <= y1:
                return key, "kisaltma"
    if k in ABBR:
        return ABBR[k], "kisaltma"
    if k.startswith("BAĞIMSIZ") or k.startswith("BĞMSZ"):
        return "Bağımsız", "kisaltma"
    return None, None
