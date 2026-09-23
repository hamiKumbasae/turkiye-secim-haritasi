"""
Baslik dosyasindaki (getSandikSecimSonucBaslikList) parti/ittifak adlarini
partiler.json anahtarlarina otomatik eslemeye calisir - once MEVCUT
(degistirilecek) veride o yil icin KULLANILAN anahtarlarla normalize edilmis
isim karsilastirmasi, sonra partiler.json'daki TUM anahtarlarin 'short'
alaniyla karsilastirma. Eslesmeyenler icin None doner (elle cozulmeli).
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.turkish_text import fold_party as fold  # noqa: E402

PARTILER = json.loads((ROOT / "data" / "normalized" / "partiler.json").read_text(encoding="utf-8"))

PARTI_COL_RE = re.compile(r"^(parti|ittifak)\d+_ALDIGI_OY$")


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


def build_party_mapping(col_to_name, existing_keys, extra_alias):
    """col_to_name: {column_NAME: ad} (parti/ittifak sutunlari icin).
    Returns {column_NAME: proje_anahtari}."""
    party_cols = {c: n for c, n in col_to_name.items() if PARTI_COL_RE.match(c)}
    names = sorted(set(party_cols.values()))
    mapping_by_name, unmatched = build_auto_map(names, existing_keys)
    for name in unmatched:
        if name in extra_alias:
            mapping_by_name[name] = extra_alias[name]
    still_unmatched = [n for n in names if n not in mapping_by_name]
    if still_unmatched:
        raise SystemExit(f"ESLENEMEYEN PARTI ADLARI (extra_alias ile cozulmeli): {still_unmatched}")
    return {c: mapping_by_name[n] for c, n in party_cols.items()}


def proper_case_tr(s: str) -> str:
    """YSK'nin TUM BUYUK isimlerini projenin kullandigi Turkce Baslik Harfli
    forma cevirir (orn. 'RECEP TAYYİP ERDOĞAN' -> 'Recep Tayyip Erdoğan')."""
    tr_lower_map = str.maketrans("İIŞĞÜÇÖ", "iışğüçö")
    out = []
    for w in s.split(" "):
        if not w:
            continue
        first, rest = w[0], w[1:]
        rest_lower = rest.translate(tr_lower_map).lower()
        first_upper = {"i": "İ"}.get(first.lower(), first.upper())
        out.append(first_upper + rest_lower)
    return " ".join(out)
