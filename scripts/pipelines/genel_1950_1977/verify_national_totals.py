"""
verify_election.py — v0, SADECE ULUSAL TOPLAM DUZEYINDE.

data/normalized/genel_secimler.json'daki 1950-1977 yillarinin il kayitlarini
TOPLAYIP iki bagimsiz kaynakla karsilastirir:
  1. YSK'nin kendi "Turkiye Geneli Sonuclari" sayfasi (ysk_national_totals.json)
  2. (Sadece 1950 icin, kanitlanmis bir metodoloji ornegi olarak) TBMM'nin
     kendi secim veritabani (ayni dosyanin _tbmm_1950 anahtari)

Bu iki kaynak 1950 icin GERCEKTEN FARKLI rakamlar veriyor (dogrulanmis,
bkz. sources.yml discrepancies) — bu script bu farki COZMEYE calismiyor,
sadece olcup raporluyor. Ileride TBMM verisi diger 7 yil icin de eklenirse
buraya kolayca genisletilebilir.

Il/ilce seviyesi (asagi->yukari matematiksel zincir) SONRAKI bir asama,
burada YOK.

Kullanim:
  python3 verify_national_totals.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from merge_into_normalized import map_party  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402

TOTALS_PATH = pathlib.Path(__file__).resolve().parent / "ysk_national_totals.json"

YEARS = ["1950", "1954", "1957", "1961", "1965", "1969", "1973", "1977"]
# Yuzde farki bu esigin altindaysa "eslesiyor" sayilir (yuvarlama toleransi).
TOLERANCE_PCT = 0.5


def sum_project_votes(genel: dict, year: str) -> dict:
    """Il kayitlarindaki 'oy' dict'ini toplar. NOT: projenin var olan
    kurali geregi (bkz. merge_into_normalized.py), o yilin majorPartiler
    listesinde OLMAYAN partiler tek tek saklanmiyor, hepsi 'Diger'
    anahtaninda toplaniyor — yani 'bizim' taraf zaten bu sekilde
    gruplanmis geliyor, YSK/TBMM'nin ham (ungrouped) rakamiyla karsilastirmak
    icin karsi tarafi da AYNI sekilde gruplamak gerekiyor (asagida)."""
    totals = {}
    for il in genel[year]["iller"]:
        for party, info in il.get("oy", {}).items():
            totals[party] = totals.get(party, 0) + info["oy"]
    return totals


def compare(label: str, computed: dict, declared_raw: dict, major: set, year: str):
    """declared_raw: {ham_YSK/TBMM_kodu: {"oy": N, ...}}. major olmayan
    kodlar, 'bizim' tarafla adil karsilastirma icin 'Diger'de toplanir —
    boylece "majorPartiler'de yok, o yuzden 0 gorunuyor" yaniltmasi
    onlenir."""
    print(f"\n  --- {label} ---")
    grouped_declared = {}
    for raw_code, info in declared_raw.items():
        key = map_party(raw_code, year)
        bucket = key if key in major else "Diğer"
        grouped_declared[bucket] = grouped_declared.get(bucket, 0) + info["oy"]

    all_parties = set(computed) | set(grouped_declared)
    mismatches = []
    total_c = sum(computed.values())
    total_d = sum(grouped_declared.values())
    for party in sorted(all_parties):
        c = computed.get(party, 0)
        d = grouped_declared.get(party, 0)
        if d == 0 and c == 0:
            continue
        diff_pct = abs(c - d) / d * 100 if d else float("inf")
        flag = "  " if diff_pct <= TOLERANCE_PCT else "!!"
        print(f"  {flag} {party:20s} bizim={c:>10,} kaynak={d:>10,} fark=%{diff_pct:.2f}")
        if diff_pct > TOLERANCE_PCT:
            mismatches.append(party)
    diff_total_pct = abs(total_c - total_d) / total_d * 100 if total_d else float("inf")
    print(f"     {'TOPLAM (bu kaynagin kapsadigi partiler)':20s} bizim={total_c:>10,} kaynak={total_d:>10,} fark=%{diff_total_pct:.2f}")
    return mismatches


def main():
    genel = {y: load_election(y) for y in YEARS}
    totals = json.loads(TOTALS_PATH.read_text(encoding="utf-8"))

    report = {}
    for year in YEARS:
        major = set(genel[year]["majorPartiler"])
        computed = sum_project_votes(genel, year)
        computed_total = sum(computed.values())
        ysk = totals[year]
        print(f"\n=== {year} === (bizim toplam oy: {computed_total:,} | YSK ulusal özet oy kullanan: "
              f"{ysk['oy_kullanan']:,} | YSK ulusal özet geçerli oy: {ysk['gecerli_oy']})")
        mism = compare("YSK Türkiye Geneli (ulusal özet sayfası) ile karşılaştırma", computed, ysk["partiler"], major, year)
        report[year] = {"ysk_mismatches": mism}

        if year == "1950":
            tbmm = totals["_tbmm_1950"]["partiler"]
            mism_tbmm = compare("TBMM Seçim Veritabanı ile karşılaştırma (BİLİNEN ÇELİŞKİ, çözülmedi)",
                                 computed, tbmm, major, year)
            report[year]["tbmm_mismatches"] = mism_tbmm

    print("\n\n=== ÖZET ===")
    for year, r in report.items():
        ysk_ok = "OK" if not r["ysk_mismatches"] else f"FARK: {r['ysk_mismatches']}"
        line = f"{year}: YSK ile {ysk_ok}"
        if "tbmm_mismatches" in r:
            tbmm_ok = "OK" if not r["tbmm_mismatches"] else f"FARK: {r['tbmm_mismatches']}"
            line += f" | TBMM ile {tbmm_ok} (beklenen bir çelişki, bkz. sources.yml)"
        print(" ", line)


if __name__ == "__main__":
    main()
