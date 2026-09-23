"""
fetch_and_aggregate.js'nin urettigi agrege JSON'u (YSK acikveri, il+ilce
toplamlari) data/normalized/referandumlar.json'a isler - Haberturk kaynakli
il/ilce kayitlarinin YERINE gecer (Evet/Hayir kolonlari sabit, parti
eslemesi gerekmez).

Kullanim: python3 merge_referandum.py <key örn 2010referandum> <agrege.json>
"""
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from hist_geomid import resolve_historical_merkez  # noqa: E402

ROOT = pathlib.Path("/Users/hamikumbasar/Desktop/Turkiye_Secim_Haritasi")
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

GEOMID_MAP_PATH = ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json"

# Dogru Turkce buyuk/kucuk harf donusumu icin YSK'nin UPPERCASE isimlerini
# kullanmak yerine projenin KENDI (zaten dogru yazilmis) il/ilce adlarini
# esas al - plaka+ilceId uzerinden.
_GENEL2023 = load_election("2023")
IL_ADI_BY_PLAKA = {i["plaka"]: i["ad"] for i in _GENEL2023["iller"]}
ILCE_ADI_BY_GEOMID = {i["geomId"]: i["ad"] for i in _GENEL2023["ilceler"]}


def build_record(ad, plaka, agg, col_to_label):
    oy = {}
    for col, label in col_to_label.items():
        v = agg["oy"].get(col, 0)
        oy[label.capitalize() if label.upper() in ("EVET", "HAYIR") else label] = v
    # Evet/Hayir buyuk/kucuk harf normalize (colToName "EVET"/"HAYIR" veriyor, proje "Evet"/"Hayır" kullaniyor)
    norm_oy = {}
    for k, v in oy.items():
        if k.upper() == "EVET":
            norm_oy["Evet"] = v
        elif k.upper() == "HAYIR":
            norm_oy["Hayır"] = v
        else:
            norm_oy[k] = v
    total = sum(norm_oy.values())
    oy_with_oran = {}
    for k, v in norm_oy.items():
        oran = round(v / total * 100, 2) if total else None
        oy_with_oran[k] = {"oy": v, "oran": oran}
    kazanan = max(norm_oy.items(), key=lambda kv: kv[1])[0] if total else None
    return {
        "ad": ad,
        "gecerliOy": agg["gecerli"],
        "ilceSayisi": 0,  # asagida doldurulacak (sadece il kaydi icin)
        "katilim": round(agg["oyKullanan"] / agg["secmen"] * 100, 2) if agg.get("secmen") else None,
        "kazanan": kazanan,
        "oy": oy_with_oran,
        "plaka": plaka,
        "sandik": agg.get("sandikSayisi", 0),
        "secmen": agg["secmen"],
        "toplamVekil": 0,
        "vekil": {},
    }


def main():
    key = sys.argv[1]
    agrege = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    geomid_map = json.loads(GEOMID_MAP_PATH.read_text(encoding="utf-8"))

    secim = load_election(key)
    col_to_label = agrege["colToName"]

    # ilce sayisi per il (gecmis kayittan koru, il basina kac ilce oldugunu
    # zaten "iller" listesindeki eski ilceSayisi alaninda tutuyoruz)
    old_ilce_sayisi = {i["plaka"]: i["ilceSayisi"] for i in secim["iller"]}

    # il-duzeyi agrege'de "sandikSayisi" yok (sadece ilce agrege'de var) -
    # il basina ilcelerin sandik sayilarini toplayarak hesapla.
    sandik_by_il = {}
    for agg in agrege["ilceler"].values():
        sandik_by_il[agg["ilId"]] = sandik_by_il.get(agg["ilId"], 0) + agg.get("sandikSayisi", 0)

    new_iller = []
    for il_id_str, agg in agrege["iller"].items():
        plaka = int(il_id_str)
        ad = IL_ADI_BY_PLAKA.get(plaka, agg["ilAdi"].title())
        rec = build_record(ad, plaka, agg, col_to_label)
        rec["ilceSayisi"] = old_ilce_sayisi.get(plaka, 0)
        rec["sandik"] = sandik_by_il.get(plaka, 0)
        new_iller.append(rec)
    new_iller.sort(key=lambda x: x["plaka"])

    secim_yili = int(key[:4])
    ilceler_by_geomid = {}
    unmatched_ilce = []
    hist_used = []
    for ilce_key, agg in agrege["ilceler"].items():
        geomId = geomid_map.get(ilce_key)
        if not geomId:
            hist_id = resolve_historical_merkez(agg["ilId"], agg["ilceAdi"], secim_yili)
            if hist_id and agg["sandikSayisi"] > 0:
                geomId = hist_id
                hist_used.append((agg["ilAdi"], agg["ilceAdi"], hist_id))
        if not geomId:
            if agg["sandikSayisi"] > 0:
                unmatched_ilce.append((agg["ilAdi"], agg["ilceAdi"], agg["sandikSayisi"]))
            continue
        if geomId.startswith("HIST-"):
            ad = geomId.replace("HIST-", "").replace("-", " ")
        else:
            ad = ILCE_ADI_BY_GEOMID.get(geomId) or agg["ilceAdi"].title()
        existing = ilceler_by_geomid.get(geomId)
        if existing is not None and existing.get("sandik", 0) > 0 and agg.get("sandikSayisi", 0) == 0:
            continue
        rec = build_record(ad, agg["ilId"], agg, col_to_label)
        rec["geomId"] = geomId
        ilceler_by_geomid[geomId] = rec
    new_ilceler = sorted(ilceler_by_geomid.values(), key=lambda x: (x["plaka"], x["ad"]))

    total_evet = sum(i["oy"].get("Evet", {}).get("oy", 0) for i in new_iller)
    total_hayir = sum(i["oy"].get("Hayır", {}).get("oy", 0) for i in new_iller)
    total = total_evet + total_hayir

    secim["iller"] = new_iller
    secim["ilceler"] = new_ilceler
    if "toplamSonuc" in secim:
        secim["toplamSonuc"] = {
            "evet_oran": round(total_evet / total * 100, 2) if total else None,
            "hayir_oran": round(total_hayir / total * 100, 2) if total else None,
        }

    save_election(key, secim)

    print(f"{key}: {len(new_iller)} il, {len(new_ilceler)} ilce guncellendi.")
    print(f"Ulusal: Evet %{total_evet/total*100:.2f}, Hayir %{total_hayir/total*100:.2f}")
    if hist_used:
        print(f"{len(hist_used)} ilce tarihsel (bolunme-oncesi) HIST-geomId ile eklendi:")
        for u in hist_used:
            print("  ", u)
    if unmatched_ilce:
        print(f"UYARI: {len(unmatched_ilce)} ilce gercek oy verisi olmasina ragmen geomId'ye eslenemedi (il toplamina dahil, ilceler listesinde YOK):")
        for u in unmatched_ilce:
            print("  ", u)


if __name__ == "__main__":
    main()
