"""
1994/1999/2004 YSK il-bazli PDF'lerinin (parse_ysk_pdfs.py'nin sadece
"Merkez" satirini aldigi AYNI dosyalar) TUM ilce/belde kirilimini cikarir.

Normal il ("BelediyeBaskanligi") formati: "İlçe" sutunu sadece yeni bir
ilce grubu basladiginda dolu (orn. "Merkez (Adapazarı)", "Akyazı"), o
gruba ait beldeler "Belediye" sutununda, "İlçe" sutunu BOS satirlarla
listeleniyor. Bir belde adi BUGUNKU bir ilce adiyla (ayni plakada)
eslesirse (orn. "Serdivan", "Arifiye" - sonradan ayri ilce oldu) KENDI
kaydini olusturur; eslesmezse GRUBUN AIT OLDUGU ilcenin (Merkez dahil)
toplamina eklenir - bu da ya dogrudan modern isim eslemesiyle ya da
(eski "Merkez" 2008-2017 arasi bolunmusse) hist_geomid.py'nin sentetik
HIST-*-Merkez ID'siyle cozulur.

Buyuksehir formati: tek sutun ("Belediye"), "Ilce" ayrimi YOK - her satir
dogrudan modern ilce adiyla eslesmeye calisilir; eslesmeyenler (ozellikle
o donem henuz ayri ilce olmamis beldeler) COZULEMEDI olarak birikir,
hicbir ilceye dahil edilmez (guvenilir bir ebeveyn bilgisi yok) - kapsam
sinirlamasi olarak raporlanir.

Kullanim: python3 parse_ilce_belde.py <yil> <out.json>
"""
import json
import pathlib
import sys

import pdfplumber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "election_import"))
from party_map_helper import fold  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402
from common.hist_geomid import resolve_historical_merkez  # noqa: E402

RAW = ROOT / "data" / "raw" / "ysk" / "mahalli-1994-1999-2004"
MAPPING = json.loads((RAW / "il_dosya_eslemesi.json").read_text(encoding="utf-8"))

_GENEL2023 = load_election("2023")
MODERN_BY_PLAKA = {}
AD_BY_GEOMID = {}
for i in _GENEL2023["ilceler"]:
    MODERN_BY_PLAKA.setdefault(i["plaka"], {})[fold(i["ad"])] = i["geomId"]
    AD_BY_GEOMID[i["geomId"]] = i["ad"]


# 1989-1999 arasi eski ilden ayrilip YENI il olan ilceler - o donemin PDF'i
# hala eski ilin dosyasinda listeliyor olabilir, ama modern ilce artik YENI
# ilin plaka'sinda. Arama sirasinda once kendi plaka'si, sonra bu cocuk
# plaka'lar denenir.
PROVINCE_SPLIT_CHILDREN = {
    67: [78, 74],  # Zonguldak -> Karabuk(1995), Bartin(1991)
    6: [71],       # Ankara -> Kirikkale(1989)
    56: [72, 73],  # Siirt -> Batman(1990), Sirnak(1990)
    51: [68],      # Nigde -> Aksaray(1989)
    42: [70],      # Konya -> Karaman(1989)
    29: [69],      # Gumushane -> Bayburt(1989)
    34: [77],      # Istanbul -> Yalova(1995)
    36: [76],      # Kars -> Igdir(1992)
    1: [80],       # Adana -> Osmaniye(1996)
    14: [81],      # Bolu -> Duzce(1999)
    47: [73],      # Mardin -> Sirnak(1990)
    30: [73],      # Hakkari -> Sirnak(1990)
    18: [78],      # Cankiri -> Karabuk(1995, Eskipazar)
}

# YSK PDF'indeki eski yazim <-> modern ilce adi arasindaki bilinen kucuk
# imla farklari (fold sonrasi bile otomatik eslesmeyen, dogrulanmis tekil
# vakalar - fuzzy matching yerine acik/gozden gecirilebilir liste).
MANUAL_PLACE_ALIAS = {
    fold("Doğubeyazıt"): fold("Doğubayazıt"),
    fold("Arapkir"): fold("Arapgir"),
}

# 2012 6360 sayili Buyuksehir Kanunu ile "Merkez" ilcesi TEK bir yeni isimle
# degistirilen (birden fazla YENI ilceye BOLUNMEYEN) iller - dogrulandi
# (web arastirmasi + genel_secimler.json 2023'te bu tek isimden BASKA
# "Merkez"in yerini alabilecek ikinci bir yeni ilce yok). district_splits.json
# bunlari icermiyor cunku o dosya SADECE gercek COK-PARCALI bolunmeler icin
# (sentetik birlesim poligonu gerektiren) - bunlar basit 1:1 yeniden
# adlandirma, poligon zaten var, sadece isim eslemesi yeterli. Denizli (20)
# BILEREK YOK - Pamukkale VE Merkezefendi diye IKI ayri yeni ilceye bolundu,
# bu da district_splits.json tarzi gercek bir bolunme (henuz cozulmedi).
MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA = {
    9: "Efeler",         # Aydın
    48: "Menteşe",        # Muğla
    52: "Altınordu",      # Ordu
    59: "Süleymanpaşa",   # Tekirdağ
    61: "Ortahisar",      # Trabzon
}


def strip_suffix_no(s):
    """'Gazi(2)' -> 'Gazi' (buyuksehir tablolarindaki tekrarlanan-ad ek kodu)."""
    import re as _re
    return _re.sub(r"\(\d+\)\s*$", "", s).strip()


def match_place(plaka, name):
    """name'i once kendi plaka'sinda, sonra (varsa) bolunerek ayrilan yeni
    il(ler)in plaka'sinda arar - ham, '(N)' eki temizlenmis, boşluksuz ve
    bilinen imla-varyanti halleriyle."""
    base_candidates = [name, strip_suffix_no(name)]
    candidates = []
    for c in base_candidates:
        candidates.append(c)
        candidates.append(c.replace(" ", ""))
        fc = fold(c)
        if fc in MANUAL_PLACE_ALIAS:
            candidates.append(MANUAL_PLACE_ALIAS[fc])
    plakalar = [plaka] + PROVINCE_SPLIT_CHILDREN.get(plaka, [])
    for p in plakalar:
        modern = MODERN_BY_PLAKA.get(p, {})
        for cand in candidates:
            gid = modern.get(fold(cand))
            if gid:
                return gid
    return None


def to_int(s):
    s = (s or "").replace(".", "").strip()
    return int(s) if s else None


def extract_rows(path):
    with pdfplumber.open(path) as pdf:
        rows = []
        header = None
        for page in pdf.pages:
            for t in page.extract_tables():
                if not t:
                    continue
                if header is None:
                    header = t[0]
                    rows.extend(t[1:])
                else:
                    body = t[1:] if t[0] == header else t
                    rows.extend(body)
    return header, rows


def new_bucket():
    return {"sandik": 0, "secmen": 0, "katilan": 0, "gecerli": 0, "partiler": {}}


def add_row(bucket, val_row, party_cols, sandik_col, party_offset):
    secmen_col, katilan_col, gecerli_col = sandik_col + 1, sandik_col + 2, sandik_col + 3
    bucket["sandik"] += to_int(val_row[sandik_col]) or 0
    bucket["secmen"] += to_int(val_row[secmen_col]) or 0
    bucket["katilan"] += to_int(val_row[katilan_col]) or 0
    bucket["gecerli"] += to_int(val_row[gecerli_col]) or 0
    for j, pname in enumerate(party_cols):
        pname = (pname or "").strip().replace("\n", " ")
        if not pname:
            continue
        oy = to_int(val_row[party_offset + j])
        if oy:
            bucket["partiler"][pname] = bucket["partiler"].get(pname, 0) + oy


def resolve_ilce_label(plaka, label, year):
    """label: ham 'İlçe' hucre metni (orn. 'Merkez (Adapazarı)', 'Akyazı').
    Once parantez ipucunu, sonra dogrudan adi, sonra (Merkez ise) hist
    sentetik ID'yi dener. Bulunamazsa None."""
    hint = None
    base = label
    if "(" in label and label.endswith(")"):
        base, hint = label.split("(", 1)
        base = base.strip()
        hint = hint.rstrip(")").strip()
    if hint:
        gid = match_place(plaka, hint)
        if gid:
            return gid
    if base.upper().startswith("MERKEZ"):
        gid = resolve_historical_merkez(plaka, "MERKEZ", year)
        if gid:
            return gid
        yeni_ad = MERKEZ_TEK_ISIM_YENIDEN_ADLANDIRMA.get(plaka)
        if yeni_ad:
            gid = match_place(plaka, yeni_ad)
            if gid:
                return gid
    gid = match_place(plaka, base)
    if gid:
        return gid
    return None


def has_baskanlik_col(header):
    """2004 PDF'lerinde 'Gecerli oy' ile parti sutunlari arasina yeni bir
    'Başkanlık sayısı' sutunu girdi - 1999/1994'te yok. Varsa parti
    sutunlari 1 kayar."""
    return any("Başkanlık" in (h or "") for h in header)


def parse_belediye(path, plaka, year):
    header, rows = extract_rows(path)
    party_start = 7 if has_baskanlik_col(header) else 6
    party_cols = header[party_start:]
    merkez_idx = next((i for i, r in enumerate(rows) if (r[0] or "").strip().upper().startswith("MERKEZ")), None)
    if merkez_idx is None:
        raise ValueError(f"{path.name}: 'Merkez' satiri yok")

    buckets = {}
    unresolved = []
    current_label = None
    current_gid = None
    # 1994/1999: her birim 2 satir (deger+oran, oran satirinin sandik
    # hucresi BOS). 2004: her birim TEK satir (oran satiri hic yok). Ikisini
    # de tek kuralla kapsar: sandik hucresi DOLU olan HER satir bir birimdir;
    # bos olanlar (oran devam satirlari) atlanir - sabit adim/cift varsayimi
    # YOK, format farkina gore otomatik uyarlanir.
    for i in range(merkez_idx, len(rows)):
        val = rows[i]
        ilce_cell = (val[0] or "").strip()
        bel_cell = (val[1] or "").strip() if len(val) > 1 else ""
        if not (val[2] or "").strip():
            continue  # oran devam satiri veya bos ayrac - atla
        if ilce_cell:
            current_label = ilce_cell
            current_gid = resolve_ilce_label(plaka, current_label, year)
            target_gid = current_gid
            target_ad = ilce_cell.split("(")[0].strip()
        else:
            gid = match_place(plaka, bel_cell)
            if gid:
                target_gid, target_ad = gid, bel_cell
            else:
                target_gid, target_ad = current_gid, (current_label.split("(")[0].strip() if current_label else None)
        if target_gid is None:
            unresolved.append({"plaka": plaka, "ilce": current_label, "belde": bel_cell, "sandik": to_int(val[2])})
            continue
        buckets.setdefault(target_gid, {"ad": AD_BY_GEOMID.get(target_gid, target_ad), **new_bucket()})
        add_row(buckets[target_gid], val, party_cols, 2, party_start)
    return buckets, unresolved


def parse_buyuksehir(path, plaka, year):
    header, rows = extract_rows(path)
    party_start = 6 if has_baskanlik_col(header) else 5
    party_cols = header[party_start:]
    buckets = {}
    unresolved = []
    # ilk 2 satir (deger+oran) = buyuksehir toplami, atla - bu ikili her
    # yilda sabit. Sonraki birimler ise 1999/1994'te cift (deger+oran),
    # 2004'te tek satir - sandik hucresi dolu olan HER satir bir birim.
    # Buyuksehir tablosunda "Ilce" sutunu yok - Belediye(0) Sandik(1)
    # Secmen(2) Katilan(3) Gecerli(4).
    for i in range(2, len(rows)):
        val = rows[i]
        label = (val[0] or "").strip()
        if not label or not (val[1] or "").strip():
            continue
        gid = match_place(plaka, label)
        if gid is None:
            unresolved.append({"plaka": plaka, "ilce": None, "belde": label, "sandik": to_int(val[1])})
            continue
        buckets.setdefault(gid, {"ad": AD_BY_GEOMID.get(gid, strip_suffix_no(label)), **new_bucket()})
        add_row(buckets[gid], val, party_cols, 1, party_start)
    return buckets, unresolved


def main():
    year = sys.argv[1]
    out_path = pathlib.Path(sys.argv[2])
    mapping = MAPPING[year]

    result = {}
    all_unresolved = []
    errors = []
    for ad, info in mapping.items():
        kind = info["type"]
        fname = info["file"]
        plaka = info["plaka"]
        subdir = "BelediyeBaskanligi" if kind == "belediye" else "Buyuksehir"
        path = RAW / year / subdir / f"{fname}.pdf"
        try:
            if kind == "belediye":
                buckets, unresolved = parse_belediye(path, plaka, int(year))
            else:
                buckets, unresolved = parse_buyuksehir(path, plaka, int(year))
            for gid, b in buckets.items():
                result[gid] = b
            for u in unresolved:
                u["il"] = ad
            all_unresolved.extend(unresolved)
        except Exception as e:
            errors.append(f"{ad} ({path.name}): {e}")

    if errors:
        print(f"{len(errors)} HATA:")
        for e in errors:
            print(" ", e)
        raise SystemExit(1)

    out_path.write_text(
        json.dumps({"buckets": result, "unresolved": all_unresolved}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    total_unresolved_sandik = sum(u["sandik"] or 0 for u in all_unresolved)
    print(f"{year}: {len(result)} ilce/gomId bucket, {len(all_unresolved)} cozulemeyen satir (toplam {total_unresolved_sandik} sandik)")


if __name__ == "__main__":
    main()
