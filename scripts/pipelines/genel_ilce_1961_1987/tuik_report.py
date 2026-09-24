"""
TUIK secimdagitimapp "Secim cevresi ve ilcelere gore milletvekili genel secimi
sonuclari" raporunun (rapory.tuik.gov.tr'nin urettigi HTML, cp1254) tek bir
il icin ayristiricisi.

Rapor yapisi: bir baslik satiri (Kayitli secmen / Oy kullanan / Gecerli oy /
parti sutunlari), ardindan "Turkiye" satiri, sonra il satiri (girintisiz),
sonra ilce satirlari (bir hucre girintili). Her sayi satirinin altinda bir
yuzde satiri var - onlar atlanir (yuzdeleri biz sayilardan yeniden hesapliyoruz).
"""
import html
import re

_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_HAS_LETTER = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]")


def _clean(s):
    return re.sub(r"<[^>]+>|\s+", " ", html.unescape(s)).strip()


def _norm_header(h):
    return " ".join(h.split())


def parse_report(raw: bytes) -> dict:
    """{'il': (ad, {sutun: int}), 'ilceler': [(ad, {sutun: int}), ...], 'sutunlar': [...]}"""
    t = raw.decode("cp1254", "ignore")
    grid = [[_clean(c) for c in _CELL.findall(r)] for r in _ROW.findall(t)]
    header = None
    out = {"il": None, "ilceler": [], "sutunlar": None}
    for cells in grid:
        if header is None:
            if any("Kayıtlı" in c for c in cells):
                header = [_norm_header(c) for c in cells if c][1:]
                out["sutunlar"] = header
            continue
        nonempty = [c for c in cells if c != ""]
        if not nonempty or not _HAS_LETTER.search(nonempty[0]):
            continue  # yuzde satiri
        name, vals = nonempty[0], nonempty[1:]
        if name == "Türkiye":
            continue
        nums = [int(v) if re.fullmatch(r"\d+", v) else None for v in vals]
        rec = dict(zip(header, nums))
        if cells.index(name) == 0:
            out["il"] = (name, rec)
        else:
            out["ilceler"].append((name, rec))
    if out["il"] is None:
        raise ValueError("il satiri bulunamadi")
    return out


def column(rec: dict, prefix: str):
    """Baslik metni kaynakta degisebildigi icin sutunu onekiyle bul."""
    for k, v in rec.items():
        if k.startswith(prefix):
            return v
    return None


META_PREFIXES = ("Sandık", "Kayıtlı", "Oy kullanan", "Geçerli")


def party_columns(rec: dict):
    return {k: v for k, v in rec.items() if not k.startswith(META_PREFIXES)}
