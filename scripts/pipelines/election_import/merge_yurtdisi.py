"""
fetch_yurtdisi.js ciktisindaki "ulkeler" agrege satirini ilgili
data/normalized/*.json dosyasinin [key]['yurtdisi'] alt-nesnesine isler.
SADECE gecerliOy/kullanilanOy/oy{} guncellenir - secmen/katilim/sandik
BILINCLI OLARAK DOKUNULMADAN eski (Habertürk) kaynagindan kalir (bkz.
fetch_yurtdisi.js basindaki not - YSK'nin per-temsilcilik sorgu yolu bu
alanlar icin guvenilmez sonuc veriyor).

Kullanim: python3 merge_yurtdisi.py <yurtdisi_raw.json>
"""
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from party_map_helper import build_auto_map  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

BASLIK_DIR = ROOT / "scripts" / "pipelines" / "mahalle_veri" / "parti-sutun-eslemeleri"
CB_ALIAS = json.loads((ROOT / "scripts" / "pipelines" / "election_import" / "cb_name_alias.json").read_text(encoding="utf-8"))

TARGETS = {
    "2015Haziran": ("genel", "baslik_2015Haziran.json"),
    "2015Kasim": ("genel", "baslik_2015Kasim.json"),
    "2018": ("genel", "baslik_2018.json"),
    "2017referandum": ("referandum", "baslik_2017referandum.json"),
    "2018cb": ("cb", "baslik_2018cb.json"),
}

PARTI_COL_RE = re.compile(r"^(parti|ittifak)\d+_ALDIGI_OY$")
BAGIMSIZ_NUMBERED_RE = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def proper_case_tr(s: str) -> str:
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


def build_oy_genel(row, baslik, major):
    col_to_name = {r["column_NAME"]: r["ad"] for r in baslik if PARTI_COL_RE.match(r["column_NAME"])}
    names = sorted(set(col_to_name.values()))
    mapping, unmatched = build_auto_map(names, major)
    if unmatched:
        # major disi (minor) partiler zaten "Diger"e gidecek - tam eslenmesi
        # sart degil, sadece raporlanir.
        print(f"  (bilgi: {unmatched} major disi, Diger'e eklendi)")
    oy, diger, bagimsiz = {}, 0, 0
    for col, name in col_to_name.items():
        v = row.get(col) or 0
        if not v:
            continue
        key = mapping.get(name)
        if key is not None and key in major:
            oy[key] = oy.get(key, 0) + v
        else:
            diger += v
    for i in range(1, 51):
        v = row.get(f"bagimsiz{i}_ALDIGI_OY") or 0
        bagimsiz += v
    if bagimsiz:
        if "Bağımsız" in major:
            oy["Bağımsız"] = oy.get("Bağımsız", 0) + bagimsiz
        else:
            diger += bagimsiz
    if diger:
        oy["Diğer"] = diger
    return oy


def build_oy_referandum(row):
    return {"Evet": row.get("bagimsiz1_ALDIGI_OY") or 0, "Hayır": row.get("bagimsiz2_ALDIGI_OY") or 0}


def build_oy_cb(row, baslik):
    col_to_name = {r["column_NAME"]: r["ad"] for r in baslik if BAGIMSIZ_NUMBERED_RE.match(r["column_NAME"])}
    oy = {}
    for col, raw_name in col_to_name.items():
        v = row.get(col) or 0
        if not v:
            continue
        name = CB_ALIAS.get(raw_name, proper_case_tr(raw_name))
        oy[name] = oy.get(name, 0) + v
    return oy


def main():
    raw = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    updated = []
    for key, (kind, baslik_fname) in TARGETS.items():
        entry = raw.get(key)
        if not entry or not entry.get("ulkeler"):
            print(f"{key}: veri yok, atlandi")
            continue
        row = entry["ulkeler"]
        secim = load_election(key)
        major = set(secim["majorPartiler"])

        if kind == "genel":
            baslik = json.loads((BASLIK_DIR / baslik_fname).read_text(encoding="utf-8"))
            oy_raw = build_oy_genel(row, baslik, major)
        elif kind == "referandum":
            oy_raw = build_oy_referandum(row)
        elif kind == "cb":
            baslik = json.loads((BASLIK_DIR / baslik_fname).read_text(encoding="utf-8"))
            oy_raw = build_oy_cb(row, baslik)
        else:
            raise SystemExit(f"bilinmeyen tur: {kind}")

        total = sum(oy_raw.values())
        oy = {k: {"oy": v, "oran": round(v / total * 100, 2) if total else None} for k, v in oy_raw.items()}

        yd = secim.setdefault("yurtdisi", {})
        yd["gecerliOy"] = row["gecerli_OY_TOPLAMI"]
        yd["kullanilanOy"] = row["oy_KULLANAN_SECMEN_SAYISI"]
        yd["oy"] = oy
        # secmen/katilim/sandik BILINCLI olarak DOKUNULMUYOR (bkz. dosya basi not)

        save_election(key, secim)
        updated.append(key)
        print(f"{key}: yurtdisi.gecerliOy={yd['gecerliOy']} kullanilanOy={yd['kullanilanOy']} parti_sayisi={len(oy)}")

    print("Guncellenen:", updated)


if __name__ == "__main__":
    main()
