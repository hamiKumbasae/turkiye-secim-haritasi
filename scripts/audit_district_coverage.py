"""
KONTROL/DENETIM SCRIPTI: her ilce-duzeyi secim icin, o secimde veri
SATIRI OLMAYAN ama GUNCEL (modern, 973 ilcelik) ilce listesinde var olan
ilceleri il/yil bazinda listeler.

ONEMLI - bu script "hepsi bug" demiyor. Arastirma (bkz. PROVENANCE notu
asagida) gosterdi ki bu bosluklarin EN AZ IKI FARKLI kok nedeni var:

  1) GERCEK BOSLUK: o alanin o yil AYRI sayilmis bir oyu hic yoktu (orn.
     Istanbul'da Atasehir/Sancaktepe/Cekmekoy 1994'te - YSK'nin kendi
     1994 PDF'i bu alanlari ayri satir olarak HIC listelemiyor, oylari
     o zamanki ebeveyn ilcenin (Umraniye/Kadikoy) toplamina karisik).
     Bu durumda dogru davranis onceden UYGULANDI: harita bu ilceyi notr/
     tiklanamaz gosteriyor (bkz. frontend/src/js/map.js .il-path-nodata), UYDURMA
     sinir CIZILMIYOR.

  2) YANLIŞ ALARM (gercek boslukmus gibi GORUNEN ama aslinda boyle
     OLMAYAN durum): bazi buyuksehirlerde (orn. Antalya) o donemin "iki
     kademeli belediye" sisteminde "alt kademe belediye"lerin (Kepez,
     Konyaalti, Muratpasa) KENDI ayri, gercek oy sayimi VARDI - YSK'nin
     PDF'inde "(1) Alt kademe belediyesi" dipnotuyla ayrica listeleniyor.
     Bu iller MODERN ilce adiyla dogrudan eslesiyor oldugu icin zaten bu
     scriptte "eksik" olarak GORUNMEZ (veri SATIRI var) - ama sinirin
     TAM OLARAK dogru olup olmadigi (alt kademe belediye siniri = modern
     ilce siniri mi) ayrica dogrulanmamistir.

  3) SINIR HASSASIYETI (bu script TESPIT EDEMEZ): "gercek boslukmus"
     (1) gibi gorunen bir ilcenin oylari aslinda komsusunun toplamina
     dahil olabilir (orn. eski/buyuk Umraniye = bugunku Umraniye +
     Cekmekoy + Sancaktepe'nin bir kismi) - bu durumda o komsu ilcenin
     GOSTERILEN poligonu (modern, kucuk) GERCEK (1994) kapsadigi alandan
     daha kucuktur. Bunu duzeltmek mahalle-duzeyi 2008-oncesi idari
     sinir arsivi gerektirir (bu depoda yok) - otomatik tespit edilemez,
     il/ilce bazinda GERCEK arastirma (YSK PDF + idari tarih kaynaklari)
     gerekir.

Bu script SADECE (1) turu bosluklarin ENVANTERINI cikarir - "hangi il/
yilda hangi modern ilceler icin veri satiri yok" sorusuna kesin cevap
verir. (2)/(3) turleri icin il/yil bazinda elle arastirma/dogrulama
gerekir (bkz. data/raw/ysk/mahalli-1994-1999-2004/<yil>/Buyuksehir/*.pdf
- "(1) Alt kademe belediyesi" dipnotu icin PDF'e bakin).

Kullanim:
  python3 scripts/audit_district_coverage.py            # ozet tablo
  python3 scripts/audit_district_coverage.py --detail    # il/ilce detayi
  python3 scripts/audit_district_coverage.py --json out.json  # makine-okunur
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_all_elections  # noqa: E402

GEO_ILCE = ROOT / "geo" / "normalized" / "turkiye_ilce_sinirlari.geojson"
DISTRICT_SPLITS = ROOT / "geo" / "historical" / "district_splits.json"


def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


def modern_districts_by_plaka():
    geo = load_json(GEO_ILCE)
    by_plaka = {}
    names = {}
    for f in geo["features"]:
        props = f["properties"]
        by_plaka.setdefault(props["plaka"], set()).add(props["id"])
    return by_plaka


def modern_name_by_geomid(secimler):
    # En guncel (2023) kaydindan geomId -> ad eslemesi (rapor okunabilirligi icin)
    names = {}
    if "2023" in secimler:
        for d in secimler["2023"]["ilceler"]:
            if d.get("geomId"):
                names[d["geomId"]] = d["ad"]
    return names


def hidden_ids_by_plaka(splits, have_set_by_plaka):
    """plaka -> o secimde AKTIF olan (yani syntheticId'si o yilin veri
    satirlarinda GERCEKTEN kullanilan) birlesimlerin hideIds'lerinin
    BIRLESIMI - bkz. frontend/src/js/map.js hiddenModernIdsForProvince() ile AYNI
    mantik (frontend'in GERCEKTE ne gosterdigini yansitmasi icin)."""
    hidden = {}
    for plaka_str, entries in splits.items():
        plaka = int(plaka_str)
        have_set = have_set_by_plaka.get(plaka, set())
        ids = set()
        for e in entries:
            if e["syntheticId"] in have_set:
                ids.update(e["hideIds"])
        if ids:
            hidden[plaka] = ids
    return hidden


def audit():
    secimler = load_all_elections()
    modern_by_plaka = modern_districts_by_plaka()
    geomid_to_name = modern_name_by_geomid(secimler)
    splits = json.loads((ROOT / "geo" / "historical" / "district_splits.json").read_text(encoding="utf-8"))

    report = {}
    for key, secim in sorted(secimler.items()):
        ilceler = secim.get("ilceler") or []
        if not ilceler:
            continue
        by_plaka = {}
        for d in ilceler:
            by_plaka.setdefault(d["plaka"], []).append(d)
        have_set_by_plaka = {p: {r["geomId"] for r in rows if r.get("geomId")} for p, rows in by_plaka.items()}
        hidden_by_plaka = hidden_ids_by_plaka(splits, have_set_by_plaka)
        election_missing = {}
        for plaka, rows in by_plaka.items():
            modern_set = modern_by_plaka.get(plaka, set())
            have_set = have_set_by_plaka[plaka]
            # Gercek tarihsel birlesim (bkz. district_mahalle_merges.yaml /
            # apply_verified_district_merges.py) ile ZATEN dogru kapsanan
            # modern id'ler "eksik" SAYILMAZ - bunlar artik sentetik bir
            # poligonla dogru gosteriliyor, "veri yok" degil.
            missing = sorted(modern_set - have_set - hidden_by_plaka.get(plaka, set()))
            if missing:
                election_missing[plaka] = missing
        if election_missing:
            report[key] = election_missing
    return report, geomid_to_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", action="store_true", help="il/ilce bazinda tam liste")
    ap.add_argument("--json", metavar="PATH", help="makine-okunur JSON ciktisi da yaz")
    args = ap.parse_args()

    report, geomid_to_name = audit()

    total_elections = len(report)
    total_province_year_pairs = sum(len(v) for v in report.values())
    total_missing_geomids = sum(len(ids) for v in report.values() for ids in v.values())

    print(f"Ilce-duzeyi veri iceren, en az bir eksik modern ilcesi olan secim sayisi: {total_elections}")
    print(f"Toplam (il, secim) cifti: {total_province_year_pairs}")
    print(f"Toplam eksik modern ilce-geomId sayisi: {total_missing_geomids}")
    print()
    print(f"{'secim':<16}{'il sayisi':>10}{'eksik ilce':>12}")
    print("-" * 40)
    for key, by_plaka in report.items():
        n_missing = sum(len(v) for v in by_plaka.values())
        print(f"{key:<16}{len(by_plaka):>10}{n_missing:>12}")

    if args.detail:
        print()
        print("=" * 60)
        print("DETAY (il -> eksik ilce adlari)")
        print("=" * 60)
        for key, by_plaka in report.items():
            print(f"\n--- {key} ---")
            for plaka, ids in sorted(by_plaka.items()):
                names = [geomid_to_name.get(gid, gid) for gid in ids]
                print(f"  plaka {plaka}: {', '.join(names)}")

    if args.json:
        out = {key: {str(p): ids for p, ids in by_plaka.items()} for key, by_plaka in report.items()}
        pathlib.Path(args.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nJSON yazildi: {args.json}")


if __name__ == "__main__":
    main()
