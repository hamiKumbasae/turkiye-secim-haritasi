"""
GitHub'in 100 MB dosya sinirini asan DIE kitaplarini parcalardan birlestirir.

data/raw/tuik/mahalli-kitap/ altinda 100 MB'tan buyuk PDF'ler bayt bayt bolunup
(`split -b 90000000 -d -a 1`) `<demirbas>.pdf.parca0`, `.parca1`, ... olarak saklanir.
Parcalar yan yana eklendiginde TUIK'ten indirilen dosyanin birebir kopyasi cikar;
bu betik onu .cache/tuik/<demirbas>.pdf olarak yazar ve SHA-256'yi dogrular.

Kullanim:
  python3 scripts/pipelines/tuik_arsiv/kitap_birlestir.py            # tum bolunmus kitaplar
  python3 scripts/pipelines/tuik_arsiv/kitap_birlestir.py 0015160    # tek kitap

Baska betikten:  from kitap_birlestir import kitap_yolu; kitap_yolu("0015160") -> pathlib.Path
"""
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
KLASOR = ROOT / "data/raw/tuik/mahalli-kitap"
CACHE = ROOT / ".cache/tuik"
# demirbas -> butun dosyanin SHA-256'si (TUIK kutuphanesinden indirilen dosya)
BUTUN_SHA256 = {
    "0015160": "69a3a5cc06e8c44d1e14d74a6d33a1534f7a592fdead659acd356a7a0a231255",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def kitap_yolu(demirbas):
    """Kitabin PDF yolunu dondurur; bolunmusse once birlestirir."""
    tek = KLASOR / f"{demirbas}.pdf"
    if tek.exists():
        return tek
    hedef = CACHE / f"{demirbas}.pdf"
    beklenen = BUTUN_SHA256[demirbas]
    if hedef.exists() and sha256(hedef) == beklenen:
        return hedef
    parcalar = sorted(KLASOR.glob(f"{demirbas}.pdf.parca*"), key=lambda p: int(p.suffix[len(".parca"):]))
    if not parcalar:
        raise SystemExit(f"{demirbas}: ne PDF ne parça var")
    CACHE.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(".pdf.tmp")
    with open(gecici, "wb") as out:
        for p in parcalar:
            out.write(p.read_bytes())
    if sha256(gecici) != beklenen:
        gecici.unlink()
        raise SystemExit(f"{demirbas}: birleştirilen dosyanın SHA-256'sı beklenenden farklı")
    gecici.replace(hedef)
    return hedef


def main():
    hedefler = sys.argv[1:] or sorted(BUTUN_SHA256)
    for d in hedefler:
        print(d, "->", kitap_yolu(d).relative_to(ROOT), "(SHA-256 doğrulandı)")


if __name__ == "__main__":
    main()
