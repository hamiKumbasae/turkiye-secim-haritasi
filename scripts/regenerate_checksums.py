"""
data/provenance/checksums.json (merkezi manifest) ve her klasorun kendi
checksums.sha256 dosyasini, o klasordeki GUNCEL dosya icerigine gore yeniden
uretir. Bu islem su ana kadar her oturumda elle/ayri Python komutlariyla
yapiliyordu (bkz. PROVENANCE.md dosyalarinin "sonra checksums.sha256'i
guncelleyin" notlari) - artik tek, tekrar kullanilabilir bir script.

PROVENANCE.md ve checksums.sha256'in kendisi HARIC, o klasordeki her dosya
icin sha256 hesaplanir. Tarama REKURSIF mi DEGIL mi, o klasorun manifestteki
DIGER klasorlerle ic ice olup olmadigina gore OTOMATIK belirlenir: eger baska
bir manifest klasoru bunun ALTINDA ise (orn. "data/raw/ysk" ALTINDA "data/raw/
ysk/1950-1977" ayri bir giris olarak varsa), o alt klasorlerin dosyalari
BURADAN HARIC TUTULUR (kendi ayri girislerinde zaten sayiliyorlar) - aksi
halde bir dosya iki farkli klasor girisinde BIRDEN cikardi. Eger hicbir alt
klasor ayrica manifestte YOKSA (orn. "data/normalized"in kendi alt-klasorleri
- elections/, mahalle/ - AYRI birer manifest girisi DEGIL), tum icerik
REKURSIF taranir - yoksa o klasorun asil (nested) dosyalarinin COGU atlanir.

Kullanim:
  python3 scripts/regenerate_checksums.py data/normalized
  python3 scripts/regenerate_checksums.py geo/historical
  python3 scripts/regenerate_checksums.py --all   # manifestteki TUM klasorler
"""
import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "provenance" / "checksums.json"
SKIP_NAMES = {"PROVENANCE.md", "checksums.sha256", ".DS_Store"}


def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regenerate_folder(folder: str, all_manifest_folders: list[str]) -> None:
    folder_path = ROOT / folder
    if not folder_path.is_dir():
        raise SystemExit(f"HATA: klasor yok: {folder_path}")

    # Bu klasorun ALTINDA, manifestte KENDI ayri girisi olan baska bir klasor
    # var mi? Varsa o alt klasorlerin icerigi HARIC tutulur (cift sayimi
    # onlemek icin), taranan dosyalar SADECE dogrudan bu klasordeki dosyalar
    # olur. Yoksa TUM icerik (alt klasorler dahil) rekursif taranir.
    child_folders = [g for g in all_manifest_folders if g != folder and g.startswith(folder + "/")]

    if child_folders:
        candidates = [p for p in folder_path.iterdir() if p.is_file()]
    else:
        candidates = [p for p in folder_path.rglob("*") if p.is_file()]

    files = sorted(p for p in candidates if p.name not in SKIP_NAMES)
    digests = {str(p.relative_to(folder_path)): sha256_of(p) for p in files}

    checksums_sha256 = folder_path / "checksums.sha256"
    lines = [f"{digests[name]}  ./{name}" for name in sorted(digests)]
    checksums_sha256.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["folders"][folder] = {
        "checksum_file": f"{folder}/checksums.sha256",
        "file_count": len(digests),
        "files": digests,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{folder}: {len(digests)} dosya -> {checksums_sha256} + {MANIFEST_PATH} güncellendi")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", help="orn. data/normalized, geo/historical")
    ap.add_argument("--all", action="store_true", help="manifestteki tum klasorleri yeniden uret")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_manifest_folders = sorted(manifest["folders"])

    if args.all:
        for folder in all_manifest_folders:
            regenerate_folder(folder, all_manifest_folders)
    elif args.folder:
        regenerate_folder(args.folder, all_manifest_folders)
    else:
        raise SystemExit("Ya bir klasor yolu ya da --all verin (bkz. -h)")


if __name__ == "__main__":
    main()
