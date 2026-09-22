"""
Yavas/analitik dogrulama suti — scripts/validate.py'nin (hizli, yapisal)
tersine, burada ulusal toplam capraz kontrolleri, checksum dogrulamasi,
known_issues kontrolu, dosya boyutu tavani ve build tekrarlanabilirligi var.
build.py'ye gomulu DEGIL — ayri, elle veya CI'da calistirilir.

Kullanim:
  python3 tests/validate_elections.py
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_NORM = ROOT / "data" / "normalized"
DIST = ROOT / "index.html"

# GitHub'in tek dosya limiti 100MB; erken uyari icin cok daha dusuk bir esik.
DIST_SIZE_CEILING = 90 * 1024 * 1024

# 1965'ten itibaren, guvenilir resmi toplam sandalye sayisi bilinen genel
# secimler (bkz. sources.yml verification notlari). 1950-61 kasitli disarida
# (coverage: vekil verisi yok).
EXPECTED_SANDALYE = {
    "1965": 450, "1969": 450, "1973": 450, "1977": 450, "1983": 399, "1987": 450,
    "1991": 450, "1995": 550, "1999": 550, "2002": 550, "2007": 550, "2011": 550,
    "2015Haziran": 550, "2015Kasim": 550,
    # 2017 referandumuyla TBMM 550'den 600'e çıkarıldı — bu ilk kez 2018
    # seçiminde uygulandı (2023'ten değil).
    "2018": 600, "2023": 600,
}

# Resmi ulusal Evet/Hayir orani bilinen, ilce verisi olmayan referandumlar
# (Wikipedia kaynagi, bkz. sources.yml). +-0.05 puan tolerans (yuvarlama).
EXPECTED_REFERANDUM_ORAN = {
    "1982referandum": {"Evet": 91.37, "Hayır": 8.63},
}

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_checksums():
    prov = load_json(ROOT / "data" / "provenance" / "checksums.json")
    all_ok = True
    bad = []
    for folder, info in prov["folders"].items():
        for rel_path, expected_digest in info["files"].items():
            fpath = ROOT / folder / rel_path
            if not fpath.exists():
                all_ok = False
                bad.append(f"{folder}/{rel_path}: dosya yok")
                continue
            actual = hashlib.sha256(fpath.read_bytes()).hexdigest()
            if actual != expected_digest:
                all_ok = False
                bad.append(f"{folder}/{rel_path}: checksum uyusmuyor")
    check("checksums.json ile diskteki dosyalar eslesiyor", all_ok, "; ".join(bad[:5]))


def check_sandalye_totals():
    genel = load_json(DATA_NORM / "genel_secimler.json")
    all_ok = True
    bad = []
    for year, expected in EXPECTED_SANDALYE.items():
        secim = genel[year]
        declared = secim.get("toplamSandalye")
        summed = sum(
            sum(il.get("vekil", {}).values()) if isinstance(il.get("vekil"), dict) else 0
            for il in secim["iller"]
        )
        if declared != expected or summed != expected:
            all_ok = False
            bad.append(f"{year}: beklenen={expected} toplamSandalye={declared} iller_toplami={summed}")
    check(f"genel seçim sandalye toplamları ({len(EXPECTED_SANDALYE)} yıl)", all_ok, "; ".join(bad))


def check_referandum_oranlari():
    ref = load_json(DATA_NORM / "referandumlar.json")
    all_ok = True
    bad = []
    for key, expected in EXPECTED_REFERANDUM_ORAN.items():
        iller = ref[key]["iller"]
        toplam_oy = {}
        for il in iller:
            for parti, v in il.get("oy", {}).items():
                toplam_oy[parti] = toplam_oy.get(parti, 0) + v.get("oy", 0)
        grand_total = sum(toplam_oy.values())
        for parti, expected_oran in expected.items():
            actual_oran = 100 * toplam_oy.get(parti, 0) / grand_total if grand_total else 0
            if abs(actual_oran - expected_oran) > 0.05:
                all_ok = False
                bad.append(f"{key}/{parti}: beklenen={expected_oran} hesaplanan={actual_oran:.2f}")
    check(f"referandum ulusal oranları ({len(EXPECTED_REFERANDUM_ORAN)} seçim)", all_ok, "; ".join(bad))


def check_known_issue_2014yerel_bdp():
    """sources.yml'nin known_issues'ta belgelediği 2014yerel BDP=0 bug'ı hâlâ
    orada mı — belge ile veri arasında sessiz bir sürüklenme olmadığını doğrular
    (bug sessizce düzeltilmiş de olabilir, o zaman sources.yml güncellenmeli)."""
    yerel = load_json(DATA_NORM / "yerel_secimler.json")
    secim = yerel["2014yerel"]
    bdp_total = 0
    for il in secim["iller"]:
        bdp_total += il.get("oy", {}).get("BDP", {}).get("oy", 0)
    # documented bug: BDP toplami 0 olmali. 0 DEGILSE, sources.yml'deki
    # known_issues artik gecersiz demektir — bu da bir FAIL, cunku belge
    # veriyle senkron degil.
    check(
        "2014yerel BDP known_issue hâlâ sources.yml ile tutarlı",
        bdp_total == 0,
        f"BDP toplamı artık {bdp_total} (sources.yml'in known_issues'ı güncellenmeli)",
    )


def check_dist_size():
    if not DIST.exists():
        check("index.html boyut tavanı", False, "dosya yok — önce scripts/build.py çalıştırın")
        return
    size = DIST.stat().st_size
    check(
        f"index.html boyutu GitHub 100MB sınırının altında (şu an {size/1024/1024:.1f}MB)",
        size < DIST_SIZE_CEILING,
    )


def check_index_in_sync_with_sources():
    """Diskteki (commit'li) index.html, data/normalized/ + geo/normalized/'den
    TAZE bir build.py çalıştırmasıyla üretilenle aynı mı? Kaynak dosyaları
    değiştirip index.html'i yeniden üretmeyi/commit'lemeyi unutmak — build.py
    zaten çalıştığı için check_reproducibility bunu YAKALAMAZ (iki taze build'i
    birbiriyle karşılaştırır, commit'li dosyayla değil). Bu kontrol commit'li
    dosyanın hash'ini build ÖNCESİ alıp build SONRASIYLA karşılaştırır."""
    if not DIST.exists():
        check("index.html kaynaklarla senkron", False, "dosya yok")
        return
    before = hashlib.sha256(DIST.read_bytes()).hexdigest()
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], cwd=ROOT, capture_output=True)
    after = hashlib.sha256(DIST.read_bytes()).hexdigest() if DIST.exists() else None
    ok = r.returncode == 0 and after == before
    check(
        "index.html kaynaklarla (data/normalized/, geo/normalized/) senkron",
        ok,
        "index.html eski — scripts/build.py çalıştırıp sonucu commit edin" if not ok else "",
    )


def check_reproducibility():
    r1 = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], cwd=ROOT, capture_output=True)
    h1 = hashlib.sha256(DIST.read_bytes()).hexdigest() if DIST.exists() else None
    r2 = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], cwd=ROOT, capture_output=True)
    h2 = hashlib.sha256(DIST.read_bytes()).hexdigest() if DIST.exists() else None
    ok = r1.returncode == 0 and r2.returncode == 0 and h1 is not None and h1 == h2
    check("build.py iki kez çalıştırıldığında bayt-bayt aynı çıktı üretiyor", ok)


def main():
    check_checksums()
    check_sandalye_totals()
    check_referandum_oranlari()
    check_known_issue_2014yerel_bdp()
    check_dist_size()
    check_index_in_sync_with_sources()
    check_reproducibility()

    failed = [name for name, ok, _ in results if not ok]
    print()
    if failed:
        print(f"{len(failed)}/{len(results)} kontrol BAŞARISIZ: {failed}")
        sys.exit(1)
    print(f"Tüm kontroller geçti ({len(results)}/{len(results)}).")


if __name__ == "__main__":
    main()
