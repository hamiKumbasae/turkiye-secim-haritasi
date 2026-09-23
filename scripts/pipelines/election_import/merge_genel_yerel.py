"""
fetch_and_aggregate.js ciktisini data/normalized/genel_secimler.json veya
yerel_secimler.json'a isler - Haberturk kaynakli il/ilce kayitlarinin
YERINE gecer. Parti-bazli (partiN_ALDIGI_OY/ittifakN_ALDIGI_OY) - parti
adi->proje anahtari eslemesi party_map_helper ile otomatik + MANUAL_ALIAS
extra ile yapiliyor. TUM bagimsizN_ALDIGI_OY sutunlari tek 'Bagimsiz'
kovasinda toplanir (il bazinda farkli kisiler oldugu icin isim korunmuyor -
projenin zaten butun yillarda kullandigi konvansiyon).

Kullanim: python3 merge_genel_yerel.py <dosya: genel|yerel> <key> <agrege.json> [extra_alias.json]
"""
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from party_map_helper import build_auto_map, build_party_mapping, fold  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402
from common.hist_geomid import resolve_historical_merkez  # noqa: E402

GEOMID_MAP_PATH = ROOT / "data" / "raw" / "ysk" / "acikveri-ilce-geomid-eslemesi.json"
_GENEL2023 = load_election("2023")
IL_ADI_BY_PLAKA = {i["plaka"]: i["ad"] for i in _GENEL2023["iller"]}
ILCE_ADI_BY_GEOMID = {i["geomId"]: i["ad"] for i in _GENEL2023["ilceler"]}

BAGIMSIZ_COL_RE = re.compile(r"^bagimsiz\d+_ALDIGI_OY$")


def build_record(ad, plaka, agg, col_to_key, major, vekil=None, toplam_vekil=0):
    oy = {}
    diger_oy = 0
    bagimsiz_oy = 0
    for col, v in agg["oy"].items():
        if not v:
            continue
        if BAGIMSIZ_COL_RE.match(col):
            bagimsiz_oy += v
            continue
        key = col_to_key.get(col)
        if key is None:
            # build_party_mapping() normalde HER parti sutununu esler (esles-
            # tiremediginde SystemExit atar) - buraya dusmek beklenmez, ama
            # dusulurse oyu sessizce KAYBETMEK yerine Diger'e ekle (bkz.
            # merge_yerel_v2.py'deki ayni kontrol - iki script farkli
            # davraniyordu, bu kopya kodun kazayla ayrildigi bir yerdi).
            diger_oy += v
            continue
        if key in major:
            oy[key] = oy.get(key, {"oy": 0}); oy[key]["oy"] += v
        else:
            diger_oy += v
    if bagimsiz_oy:
        if "Bağımsız" in major:
            oy.setdefault("Bağımsız", {"oy": 0})
            oy["Bağımsız"]["oy"] += bagimsiz_oy
        else:
            diger_oy += bagimsiz_oy
    if diger_oy:
        oy["Diğer"] = {"oy": diger_oy}

    total = sum(v["oy"] for v in oy.values())
    for k in oy:
        oy[k]["oran"] = round(oy[k]["oy"] / total * 100, 2) if total else None
    kazanan = max(oy.items(), key=lambda kv: kv[1]["oy"])[0] if oy else None

    return {
        "ad": ad,
        "gecerliOy": agg["gecerli"],
        "ilceSayisi": 0,
        "katilim": round(agg["oyKullanan"] / agg["secmen"] * 100, 2) if agg.get("secmen") else None,
        "kazanan": kazanan,
        "oy": oy,
        "plaka": plaka,
        "sandik": agg.get("sandikSayisi", 0),
        "secmen": agg["secmen"],
        "toplamVekil": toplam_vekil,
        "vekil": vekil or {},
    }


def main():
    # dosya argumani artik sadece geriye-uyumluluk icin okunuyor - hangi
    # dosyaya yazilacagi artik anahtarin kendisinden (common/election_io.py
    # tur_of()) otomatik cikariliyor.
    dosya = sys.argv[1]  # "genel" | "yerel"
    key = sys.argv[2]
    agrege = json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
    extra_alias = json.loads(pathlib.Path(sys.argv[4]).read_text(encoding="utf-8")) if len(sys.argv) > 4 else {}
    geomid_map = json.loads(GEOMID_MAP_PATH.read_text(encoding="utf-8"))

    secim = load_election(key)
    major = set(secim["majorPartiler"])

    existing_keys = set()
    for il in secim["iller"]:
        existing_keys.update(il["oy"].keys())
    existing_keys.discard("Bağımsız")
    existing_keys.discard("Diğer")

    col_to_key = build_party_mapping(agrege["colToName"], existing_keys, extra_alias)

    old_ilce_sayisi = {i["plaka"]: i["ilceSayisi"] for i in secim["iller"]}
    # Sandik-duzeyi oy API'si sandalye dagilimi icermiyor - il kaydinin
    # vekil/toplamVekil alanlari, bu script calismadan ONCEKI (zaten dogru,
    # baska bir kaynaktan gelen) degerlerden korunur, yoksa build_record'un
    # varsayilanlariyla (0/{}) SESSIZCE sifirlanir (bkz. PROVENANCE.md'deki
    # "Genel secim vekil/sandalye alani korunmasi" notu - bu koruma daha once
    # elle/tek seferlik yapilmisti, artik her calistirmada otomatik).
    old_vekil = {i["plaka"]: (i.get("vekil") or {}, i.get("toplamVekil") or 0) for i in secim["iller"]}
    sandik_by_il = {}
    for agg in agrege["ilceler"].values():
        sandik_by_il[agg["ilId"]] = sandik_by_il.get(agg["ilId"], 0) + agg.get("sandikSayisi", 0)

    new_iller = []
    for il_id_str, agg in agrege["iller"].items():
        plaka = int(il_id_str)
        ad = IL_ADI_BY_PLAKA.get(plaka, agg["ilAdi"].title())
        vekil, toplam_vekil = old_vekil.get(plaka, ({}, 0))
        rec = build_record(ad, plaka, agg, col_to_key, major, vekil=vekil, toplam_vekil=toplam_vekil)
        rec["ilceSayisi"] = old_ilce_sayisi.get(plaka, 0)
        rec["sandik"] = sandik_by_il.get(plaka, 0)
        new_iller.append(rec)
    new_iller.sort(key=lambda x: x["plaka"])

    secim_yili = int(re.match(r"\d{4}", key).group())
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
        # HIST- sentetik ID'ler icin duz isim, GERCEK modern geomId'ler icin
        # zaten bilinen modern ad (resolve_historical_merkez artik bazi
        # illerde - tek isimle yeniden adlandirilanlar - sentetik degil
        # DOGRUDAN modern geomId dondurebiliyor, bkz. hist_geomid.py).
        if geomId.startswith("HIST-"):
            ad = geomId.replace("HIST-", "").replace("-", " ")
        else:
            ad = ILCE_ADI_BY_GEOMID.get(geomId) or agg["ilceAdi"].title()
        # Ayni geomId'ye BIRDEN FAZLA YSK ilce ID'si duserse (orn. eski
        # "<Il> MERKEZ" tarihsel olarak modern bir ilceye cozulurken, o
        # modern ilcenin KENDI guncel ID'si de ayni secimde ayri bir satir
        # olarak var ama oy=0 donuyor cunku o donemde henuz yoktu) - GERCEK
        # veriyi (sandik>0) tercih et, cift kayit birakma.
        existing = ilceler_by_geomid.get(geomId)
        if existing is not None and existing.get("sandik", 0) > 0 and agg.get("sandikSayisi", 0) == 0:
            continue
        rec = build_record(ad, agg["ilId"], agg, col_to_key, major)
        rec["geomId"] = geomId
        ilceler_by_geomid[geomId] = rec
    new_ilceler = sorted(ilceler_by_geomid.values(), key=lambda x: (x["plaka"], x["ad"]))

    secim["iller"] = new_iller
    secim["ilceler"] = new_ilceler
    save_election(key, secim)

    print(f"{key}: {len(new_iller)} il, {len(new_ilceler)} ilce guncellendi.")
    print("parti eslemesi (sutun->anahtar, benzersiz adlar):")
    seen = set()
    for col, k in sorted(col_to_key.items()):
        name = agrege["colToName"][col]
        if name in seen:
            continue
        seen.add(name)
        print(f"  {name} -> {k}")
    if hist_used:
        print(f"{len(hist_used)} ilce tarihsel HIST-geomId ile eklendi: {hist_used}")
    if unmatched_ilce:
        print(f"UYARI: {len(unmatched_ilce)} ilce gercek oy verisi olmasina ragmen geomId'ye eslenemedi:")
        for u in unmatched_ilce:
            print("  ", u)


if __name__ == "__main__":
    main()
