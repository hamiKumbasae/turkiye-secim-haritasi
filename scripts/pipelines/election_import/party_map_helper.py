"""
Baslik dosyasindaki (getSandikSecimSonucBaslikList) parti/ittifak adlarini
partiler.json anahtarlarina otomatik eslemeye calisir - once MEVCUT
(degistirilecek) veride o yil icin KULLANILAN anahtarlarla normalize edilmis
isim karsilastirmasi, sonra partiler.json'daki TUM anahtarlarin 'short'
alaniyla karsilastirma. Eslesmeyenler icin None doner (elle cozulmeli).
"""
import json
import re
import unicodedata
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
PARTILER = json.loads((ROOT / "data" / "normalized" / "partiler.json").read_text(encoding="utf-8"))


def fold(s):
    if s is None:
        return ""
    s = s.strip()
    s = (s.replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g")
           .replace("Ü", "U").replace("ü", "u").replace("Ş", "S").replace("ş", "s")
           .replace("Ö", "O").replace("ö", "o").replace("Ç", "C").replace("ç", "c"))
    s = s.upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\bPARTISI\b|\bPARTI\b|\(.*?\)", "", s)
    s = s.replace(".", "").replace("-", " ").replace("'", "")
    s = " ".join(s.split())
    return s


# YSK baslik listesindeki kisa/farkli yazimlar icin bilinen manuel eslemeler
# (fold() sonrasi bile otomatik eslesmeyenler icin, birden fazla secimde
# tekrarlanan kaliplar).
MANUAL_ALIAS = {
    fold("MİLLET"): "MP92",       # "Millet Partisi" (1990'lar-2000'ler), MP92 anahtariyla ayni
    fold("SAADET"): "SP",          # "Saadet Partisi"
    fold("GENÇ PARTİ"): "GP",       # "Genç Parti" (Cem Uzan) - pipelines/genel_1983_2007'da dogrulandi
    fold("GENÇPARTİ"): "GP",        # bosluksuz yazim varyanti
    fold("ANAVATAN"): "ANAP",       # "Anavatan Partisi" tam yazimi = ANAP
    fold("BÜYÜK BİRLİK"): "BBP",    # "Büyük Birlik Partisi" tam yazimi = BBP
    fold("HÜDA PAR"): "HÜDAPAR",    # bosluklu yazim varyanti
    fold("MİLLİ YOL"): "MİLLİYOL",  # bosluklu yazim varyanti
    fold("ZAFER PARTİSİ"): "ZP",
    fold("CUMHUR İTTİFAKI"): "Cumhur İttifakı",
    fold("MİLLET İTTİFAKI"): "Millet İttifakı",
    fold("EMEK VE ÖZGÜRLÜK İTTİFAKI"): "Emek ve Özgürlük İttifakı",
    fold("ATA İTTİFAKI"): "Ata İttifakı",
    fold("SOSYALİST GÜÇ BİRLİĞİ İTTİFAKI"): "Sosyalist Güç Birliği İttifakı",
}


def build_auto_map(baslik_names, existing_keys):
    """baslik_names: set of party/ittifak 'ad' strings from baslik file.
    existing_keys: mevcut (bu yil icin zaten kullanilan) partiler.json anahtarlari.
    Returns (mapping dict {ad: key}, unmatched list)."""
    existing_fold = {fold(k): k for k in existing_keys}
    all_keys_fold = {fold(k): k for k in PARTILER.keys()}
    all_short_fold = {}
    for k, v in PARTILER.items():
        sf = fold(v.get("short", ""))
        if sf and sf not in all_short_fold:
            all_short_fold[sf] = k

    mapping = {}
    unmatched = []
    for name in baslik_names:
        nf = fold(name)
        if nf in MANUAL_ALIAS:
            mapping[name] = MANUAL_ALIAS[nf]
        elif nf in existing_fold:
            mapping[name] = existing_fold[nf]
        elif nf in all_keys_fold:
            mapping[name] = all_keys_fold[nf]
        elif nf in all_short_fold:
            mapping[name] = all_short_fold[nf]
        else:
            unmatched.append(name)
    return mapping, unmatched
