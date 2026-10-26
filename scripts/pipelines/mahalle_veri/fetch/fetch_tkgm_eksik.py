"""
TKGM'nin ilk cekimde sinirini bos dondurdugu birimleri (data/raw/tkgm/mahalle/<plaka>.geojson icinde
geometry=null) yeniden sorar. Yalniz bu birimlerin bulundugu ilceler icin mahalleListe/<ilce id> istenir;
sinir artik doluysa ayni sadelestirmeyle (fetch_tkgm_mahalle.sadelestir) alinir.

Cikti: <cikti>/eksik_<plaka>.json = {"geri_gelen": {tkgm_id: geometry}, "hala_bos": [tkgm_id],
"listede_yok": [tkgm_id]}. Birlestirme yerelde yapilir (yalniz geometry=null olan ozellikler doldurulur).
Kullanim: python3 fetch_tkgm_eksik.py <cikti klasoru> <plaka,plaka,...>
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_tkgm_mahalle import BASE, ROOT, al, sadelestir  # noqa: E402

TKGM_DIR = ROOT / "data" / "raw" / "tkgm" / "mahalle"


def main():
    cikti = pathlib.Path(sys.argv[1])
    cikti.mkdir(parents=True, exist_ok=True)
    hatali = []
    for plaka in [int(p) for p in sys.argv[2].split(",")]:
        t0 = time.time()
        yol = TKGM_DIR / f"{plaka:02d}.geojson"
        if not yol.exists():
            continue
        bos = {}   # tkgm_id -> ilce_tkgm_id
        for ft in json.loads(yol.read_text(encoding="utf-8"))["features"]:
            if not ft.get("geometry"):
                bos[ft["properties"]["tkgm_id"]] = ft["properties"]["ilce_tkgm_id"]
        if not bos:
            continue
        geri, hala, gorulen = {}, [], set()
        try:
            for ilce_id in sorted(set(bos.values())):
                time.sleep(0.3)
                for fm in al(f"{BASE}/mahalleListe/{ilce_id}")["features"]:
                    tid = (fm.get("properties") or {}).get("id")
                    if tid not in bos:
                        continue
                    gorulen.add(tid)
                    g = sadelestir(fm.get("geometry"))
                    if g is None:
                        hala.append(tid)
                    else:
                        geri[str(tid)] = g
        except Exception as e:  # noqa: BLE001 - bir ilin hatasi digerlerini durdurmasin
            print(f"::error title=TKGM eksik {plaka:02d}::{str(e)[:200]}", flush=True)
            hatali.append(plaka)
        yok = sorted(t for t in bos if t not in gorulen)
        (cikti / f"eksik_{plaka:02d}.json").write_text(
            json.dumps({"geri_gelen": geri, "hala_bos": sorted(hala), "listede_yok": yok}, ensure_ascii=False,
                       separators=(",", ":")), encoding="utf-8")
        print(f"::notice title=TKGM eksik {plaka:02d}::bos {len(bos)}, geri gelen {len(geri)}, hala bos {len(hala)}, "
              f"listede yok {len(yok)}, {time.time() - t0:.0f} sn", flush=True)
    if hatali:
        raise SystemExit(f"tamamlanamayan iller: {hatali}")


if __name__ == "__main__":
    main()
