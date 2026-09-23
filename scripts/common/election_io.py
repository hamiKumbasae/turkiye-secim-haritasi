"""
Paylasilan I/O yardimcisi: her secim kendi dosyasinda
(data/normalized/elections/<tur>/<anahtar>.json). Onceki mimaride 4 buyuk
birlesik dosya vardi (genel_secimler.json vb.) - o yapi 2026-09-23'te bu
seçim-basina dosya yapisina bolundu (bkz. data/normalized/PROVENANCE.md).
Tum pipeline script'leri (parse+merge) artik dogrudan bu birlesik dosyalari
DEGIL, bu modulun load_election/save_election fonksiyonlarini kullanmali -
boylece "1977'yi duzelt -> sadece 1977.json degisir" ozelligi korunur.

partiler.json, mahalle/*.json ve meclis_2024.json bu bolunmenin DISINDA -
onlar zaten ya paylasimli (partiler) ya da zaten seçim-basina ayri
(mahalle) tutuluyordu, degismedi.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA_NORM = ROOT / "data" / "normalized"
ELECTIONS_DIR = DATA_NORM / "elections"
TURLER = ["genel", "yerel", "referandum", "cumhurbaskanligi"]

# anahtar -> tur eslemesi icin dosya sistemine bakmiyoruz (henuz yaratilmamis
# olabilir) - anahtarin kendisinden cikariyoruz. Ayni kural build.py/
# election-config.js'deki YEAR_ORDER/YEREL_YEAR_ORDER/... listeleriyle
# tutarli olmali.
def tur_of(key: str) -> str:
    if key.endswith("yerel"):
        return "yerel"
    if key.endswith("referandum"):
        return "referandum"
    if key.endswith("cb") or key.endswith("cb1tur") or key.endswith("cb2tur"):
        return "cumhurbaskanligi"
    return "genel"


def election_path(key: str) -> pathlib.Path:
    return ELECTIONS_DIR / tur_of(key) / f"{key}.json"


def load_election(key: str) -> dict:
    p = election_path(key)
    if not p.exists():
        raise FileNotFoundError(f"{p} yok - once bu secimin bir kaydi olmali (yeni secim ekliyorsan once bos bir iskelet yaz)")
    return json.loads(p.read_text(encoding="utf-8"))


def save_election(key: str, record: dict) -> None:
    p = election_path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )


def load_all_elections() -> dict:
    """{anahtar: kayit} - tum turler, build.py/validate.py'nin eskiden
    genel_secimler.json vb. birlestirerek yaptigi islevin karsiligi."""
    out = {}
    for tur in TURLER:
        d = ELECTIONS_DIR / tur
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return out


def load_elections_by_tur() -> dict:
    """{tur: {anahtar: kayit}} - eskiden ayri genel_secimler.json/
    yerel_secimler.json/... dosyalarinin karsiligi, testlerin kullanimi icin."""
    out = {tur: {} for tur in TURLER}
    for tur in TURLER:
        d = ELECTIONS_DIR / tur
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            out[tur][f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return out
