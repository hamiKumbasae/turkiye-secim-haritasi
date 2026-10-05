"""
Tarihsel ilce/il sinirlarini dogru sirayla bastan uretir. Tek tek betikler birbirinin ciktisini
yeniden yazdigi icin (ornek: apply_idari_merges.py harita_notlari.json'u ve HISTK birlesimlerini
sifirdan kurar, build_ilce_secim.py bunlarin uzerine secim secim birlesim ekler) yalniz bu sira
tutarli sonuc verir:

  0. build_ilce_secim.py <secim> geri_al   secim katmanini (HIST<secim>-*) kaldirir; aksi halde 1. adim
                                           onun tabanindaki HISTK birlesimlerini kullanilmiyor sayip siler
  -  election_import/merkez_ilce_tamamla.py  2009-2011'de YSK aktarimindan dusen Merkez ilce satirlari
     election_import/etiket_2011_bdp.py    2011 BDP destekli bagimsizlarin ilce etiketi = il etiketi
  1. apply_idari_merges.py                 kanun kaynakli tek kaynakli birlesimler (HISTK-*)
     birlesim_2009_sonrasi.py              2009+ secimlerde henuz kurulmamis ilceler (HIST-*)
  2. prepare_istanbul_historical_assignments.py + build_istanbul_1961_1992.py
                                           Istanbul 1961-1991 ilce sinirlari (HIST-Istanbul-*)
  3. build_ilce_secim.py <secim>           her secim icin kalan ilceler (HIST<secim>-*); secimler
                                           geo/historical/idari/ilce_eslesme/*.csv'deki anahtarlar
  4. ortusmeleri_temizle.py               birlikte cizilen poligonlar arasindaki ince ortusme seritleri
                                           (Istanbul; haritada ilce icinde ortada biten cizgiler)
     build_il_sinirlari.py                 secim verisinden donem il sinirlari (era*.geojson)
  5. build_meclis_harita.py                meclis haritalari (baskanlik satirlarinin poligonlari)
  6. harita_durum_raporu.py, kapsam_tablosu.py, checksum, scripts/build.py

Betik idempotenttir: main uzerinde calistirildiginda hicbir dosya degismemelidir
(tests/validate_elections.py bunu dogrudan denemez; elle: calistir, git status bos olmali).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/tarihsel_sinirlari_uret.py
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HG = ROOT / "scripts/pipelines/historical_geo"
PY = sys.executable
SIRA = ["1961referandum", "1961", "1963yerel", "1965", "1968yerel", "1969", "1973yerel", "1973", "1977yerel",
        "1977", "1982referandum", "1983", "1984yerel", "1987referandum", "1987", "1988referandum", "1989yerel",
        "1991", "1994yerel", "1995", "1999yerel", "1999", "2002", "2004yerel", "2007", "2007referandum"]


def calistir(*args, cwd=ROOT):
    print("→", " ".join(str(a) for a in args), flush=True)
    r = subprocess.run([PY, *map(str, args)], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"HATA: {args[0]}")
    son = [s for s in r.stdout.strip().splitlines() if s.strip()][-1:] or [""]
    print("   ", son[0][:160])


def main():
    secimler = sorted(p.stem for p in (ROOT / "geo/historical/idari/ilce_eslesme").glob("*.csv"))
    bilinmeyen = set(secimler) - set(SIRA)
    if bilinmeyen:
        raise SystemExit(f"SIRA listesinde olmayan secim: {sorted(bilinmeyen)}")
    # 2009-2011'de YSK aktarimindan dusen Merkez ilce satirlari (veri; geometriden once)
    calistir(ROOT / "scripts/pipelines/election_import/merkez_ilce_tamamla.py")
    calistir(ROOT / "scripts/pipelines/election_import/etiket_2011_bdp.py")
    # 0. secim katmanini geri al: apply_idari_merges.py tabandaki HISTK birlesimlerini gormeli
    for s in [s for s in SIRA if s in secimler]:
        calistir(HG / "build_ilce_secim.py", s, "geri_al")
    calistir(HG / "apply_idari_merges.py")
    calistir(HG / "birlesim_2009_sonrasi.py")
    calistir("prepare_istanbul_historical_assignments.py", cwd=HG)
    calistir(HG / "build_istanbul_1961_1992.py")
    for s in [s for s in SIRA if s in secimler]:
        calistir(HG / "build_ilce_secim.py", s)
    calistir(HG / "ortusmeleri_temizle.py")
    calistir(HG / "build_il_sinirlari.py")
    calistir(ROOT / "scripts/pipelines/meclis_harita/build_meclis_harita.py")
    calistir(ROOT / "scripts/rapor/harita_durum_raporu.py")
    calistir(ROOT / "scripts/rapor/kapsam_tablosu.py")
    for klasor in ("geo/normalized", "geo/historical", "data/normalized"):
        calistir(ROOT / "scripts/regenerate_checksums.py", klasor)
    calistir(ROOT / "scripts/build.py")


if __name__ == "__main__":
    main()
