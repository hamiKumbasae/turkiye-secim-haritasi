"""
Yavas/analitik dogrulama suti — scripts/validate.py'nin (hizli, yapisal)
tersine, burada ulusal toplam capraz kontrolleri, checksum dogrulamasi,
known_issues kontrolu, dosya boyutu tavani ve build tekrarlanabilirligi var.
build.py'ye gomulu DEGIL — ayri, elle veya CI'da calistirilir.

Kullanim:
  python3 tests/validate_elections.py
"""
import base64
import gzip
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

# Guvenilir resmi toplam sandalye sayisi bilinen genel secimler (bkz.
# sources.yml verification notlari). 1950/1954/1957/1961: YSK'nin resmi
# "Turkiye Geneli" rakamlari (scripts/genel-1950-1977-pipeline/) — il bazli
# vekil toplami Sakarya eksik oldugu icin 1957/1961'de bundan biraz dusuk
# cikar (bilinen, belgelenmis fark), o yuzden burada il toplamindan degil
# dogrudan resmi ulusal rakamdan kontrol ediliyor.
EXPECTED_SANDALYE = {
    "1950": 487, "1954": 541, "1957": 610, "1961": 450,
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


# data/raw/ altindaki her dosya ya checksums.json manifestinde olmali, ya da
# burada acikca "neden disarida" diye belirtilmeli - manifestte olmayan bir
# ham kaynak dosyasi degisirse checksum kontrolu bunu SESSIZCE atlar (bkz.
# check_checksums - sadece manifestte LISTELI dosyalari kontrol eder, eksik
# olani fark etmez). Bu kontrol o boslugu kapatiyor.
CHECKSUM_ALLOWLIST_DISI = {
    # Her klasorun kendi PROVENANCE.md/checksums.sha256'si manifestin
    # disinda tutuluyor (kendi kendini referans etmemesi icin) - bunlar
    # zaten check_checksums'in kapsami disi, burada ayrica saymaya gerek yok.
}


def check_raw_checksum_coverage():
    prov = load_json(ROOT / "data" / "provenance" / "checksums.json")
    manifest_files = set()
    for folder, info in prov["folders"].items():
        for rel_path in info["files"]:
            manifest_files.add(str((ROOT / folder / rel_path).resolve()))

    disk_files = set()
    for p in (ROOT / "data" / "raw").rglob("*"):
        if not p.is_file():
            continue
        if p.name in ("PROVENANCE.md", "checksums.sha256", ".DS_Store"):
            continue
        rel = str(p.resolve())
        if rel in CHECKSUM_ALLOWLIST_DISI:
            continue
        disk_files.add(rel)

    missing = sorted(disk_files - manifest_files)
    check(
        "data/raw/ altindaki her dosya checksums.json manifestinde",
        not missing,
        f"{len(missing)} dosya manifestte yok (ornek): " + "; ".join(m.replace(str(ROOT) + '/', '') for m in missing[:5]),
    )


# 1957/1961: YSK'nin 1950-1977 il arsivinde Sakarya YOK (bilinen, belgelenmis
# kaynak boslugu — bkz. scripts/genel-1950-1977-pipeline/PROVENANCE.md). Bu
# yuzden il-bazli vekil toplami resmi ulusal rakamdan Sakarya'nin sandalye
# sayisi kadar dusuk cikar; bu YILLAR icin sadece 'declared' (resmi rakam)
# kontrol edilir, il toplami degil.
SANDALYE_ILLER_TOPLAMI_ISTISNA = {"1957", "1961"}


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
        summed_ok = summed == expected or year in SANDALYE_ILLER_TOPLAMI_ISTISNA
        if declared != expected or not summed_ok:
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
    """sources.yml'de RESOLVED olarak belgelenen 2014yerel BDP=0 bug'ının
    (eski Habertürk kaynağında BDP oyu her yerde 0 görünüyordu, YSK'ye
    taşınırken düzeltildi — bkz. sources.yml known_issues) geri gelmediğini
    doğrular: BDP toplamı 0'dan büyük olmalı ve Diyarbakır'ı kazanmış olmalı
    (bilinen tarihsel sonuç, Gültan Kışanak)."""
    yerel = load_json(DATA_NORM / "yerel_secimler.json")
    secim = yerel["2014yerel"]
    bdp_total = 0
    diyarbakir_kazanan = None
    for il in secim["iller"]:
        bdp_total += il.get("oy", {}).get("BDP", {}).get("oy", 0)
        if il.get("plaka") == 21:
            diyarbakir_kazanan = il.get("kazanan")
    ok = bdp_total > 0 and diyarbakir_kazanan == "BDP"
    check(
        "2014yerel BDP known_issue hâlâ çözülmüş durumda (regresyon yok)",
        ok,
        f"BDP toplamı={bdp_total}, Diyarbakır kazananı={diyarbakir_kazanan} (beklenen: >0 ve BDP)",
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


def extract_embedded(html_text):
    """index.html'deki window.__EMBEDDED_GZ__ objesini {anahtar: cozülmüş JSON} olarak döner."""
    start_marker = "window.__EMBEDDED_GZ__ = "
    start = html_text.find(start_marker)
    end = html_text.find(";\n</script>", start)
    gz_obj = json.loads(html_text[start + len(start_marker):end])
    return {k: json.loads(gzip.decompress(base64.b64decode(v))) for k, v in gz_obj.items()}


def check_index_in_sync_with_sources():
    """Diskteki (commit'li) index.html, data/normalized/ + geo/normalized/'den
    TAZE bir build.py çalıştırmasıyla üretilenle AYNI VERİYİ mi taşıyor?
    Kaynak dosyaları değiştirip index.html'i yeniden üretmeyi/commit'lemeyi
    unutmak — build.py zaten çalıştığı için check_reproducibility bunu
    YAKALAMAZ (iki taze build'i birbiriyle karşılaştırır, commit'li dosyayla
    değil). Bu kontrol commit'li dosyanın içeriğini build ÖNCESİ alıp build
    SONRASIYLA karşılaştırır.

    NOT: BAYT karşılaştırması DEĞİL, DEKOMPRESE EDİLMİŞ JSON içeriği
    karşılaştırılıyor — gzip'in ham baytları, aynı içerik için bile farklı
    zlib sürümleri arasında (örn. yerel macOS ile CI'daki Ubuntu runner)
    FARKLI çıkabiliyor (mtime=0 olsa bile). İçerik aynıysa bu ortam farkı
    yanlış pozitif üretmemeli — gerçek "veri güncel mi" sorusu budur."""
    if not DIST.exists():
        check("index.html kaynaklarla senkron", False, "dosya yok")
        return
    before = extract_embedded(DIST.read_text(encoding="utf-8"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], cwd=ROOT, capture_output=True)
    after = extract_embedded(DIST.read_text(encoding="utf-8")) if DIST.exists() else None
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
    check_raw_checksum_coverage()
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
