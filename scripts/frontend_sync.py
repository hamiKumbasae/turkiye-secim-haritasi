"""
On yuzu turkiye-secim-atlasi reposundan bu repodaki frontend/ klasorune kopyalar.

Tek on yuz: site (HTML/CSS/JS, yontem.html) yalniz turkiye-secim-atlasi'nda gelistirilir. Bu repo
onun bir kopyasini frontend/ altinda tasir ve scripts/build.py ile veriyi gomerek tek dosyalik
index.html uretir (cift tiklayinca file:// ile acilir). frontend/KAYNAK.json kopyanin hangi atlas
commit'inden alindigini ve her dosyanin sha256'sini tutar; tests/validate_elections.py frontend/
altindaki dosyalar elle degistirilirse hata verir. On yuz degisikligi: once atlas'ta, sonra bu betik.

Kopyalananlar: src/ (sablon, CSS, JS), yontem.html, build.py (JS dosya sirasi ve yer tutucular icin,
frontend/atlas_build.py olarak).

Kullanim:
  .venv/bin/python scripts/frontend_sync.py [atlas_klasoru]   # varsayilan: ../turkiye-secim-atlasi
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEDEF = ROOT / "frontend"
KAYNAK_JSON = HEDEF / "KAYNAK.json"


def ozet(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dosyalar(atlas: pathlib.Path):
    """(atlas'taki yol, frontend/ altindaki yol)"""
    for p in sorted((atlas / "src").rglob("*")):
        if p.is_file():
            yield p, p.relative_to(atlas)
    yield atlas / "yontem.html", pathlib.Path("yontem.html")
    yield atlas / "build.py", pathlib.Path("atlas_build.py")


def manifest():
    return {str(p.relative_to(HEDEF)): ozet(p) for p in sorted(HEDEF.rglob("*"))
            if p.is_file() and p != KAYNAK_JSON and "__pycache__" not in p.parts}


def main():
    atlas = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "turkiye-secim-atlasi").resolve()
    if not (atlas / "src" / "index.template.html").exists():
        raise SystemExit(f"atlas reposu bulunamadı: {atlas}")
    commit = subprocess.run(["git", "-C", str(atlas), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    kirli = subprocess.run(["git", "-C", str(atlas), "status", "--porcelain", "src", "yontem.html", "build.py"],
                           capture_output=True, text=True).stdout.strip()
    if kirli:
        print("UYARI: atlas'ta commit'lenmemiş ön yüz değişikliği var; KAYNAK.json'daki commit tam karşılık gelmez:")
        print(kirli)
    if HEDEF.exists():
        shutil.rmtree(HEDEF)
    for src, rel in dosyalar(atlas):
        (HEDEF / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, HEDEF / rel)
    KAYNAK_JSON.write_text(json.dumps({
        "not": "Bu klasör turkiye-secim-atlasi'ndan kopyalanır (scripts/frontend_sync.py); elle değiştirmeyin.",
        "atlasRepo": "https://github.com/hamiKumbasae/turkiye-secim-atlasi",
        "atlasCommit": commit,
        "dosyalar": manifest(),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"frontend/ <- {atlas} ({commit[:7]}), {len(manifest())} dosya")


if __name__ == "__main__":
    main()
