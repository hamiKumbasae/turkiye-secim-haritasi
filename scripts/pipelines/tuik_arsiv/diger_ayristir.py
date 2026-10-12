"""
1994, 1999 ve 2004 yerel secimlerinde YSK arsivinin 'Diğer' toplamini DİE kitabindaki partilere ayirir.

YSK il/ilce arsivi kucuk partileri tek bir 'Diğer' satirinda verir; merge_mahalli.py ayni satirin
DİE kitabindaki karsiligini okuyup 'Diğer' icindeki partileri kaynak.tuik.digerDagilimi'na yazar
(yalniz kaynak, veriye islenmemisti). 'Diğer' bu yuzden bazi yerlerde kazanan gorunuyordu
(ornek 1994 Kiğı: 'Diğer' 828 = Bağımsız 751 + DSP 77; kazanan bagimsiz aday).

Kural (tahmin yok):
  - DİE satiri ic kontrolden gecmis olmali (kaynak.tuikKullanilmadi yok): sutun kaymasi toplami
    korur ama oylari yanlis partiye yazar, o yuzden kontrolden gecmeyen satirin dagilimi kullanilmaz;
  - dagilimin toplami YSK'nin 'Diğer' oyuna BIREBIR esit olmali (iki resmi kaynagin bagimsiz teyidi);
  - o zaman 'Diğer' kaldirilir, dagilimdaki her parti kendi oyu ve gecerli oya orani ile eklenir,
    kazanan en cok oy alan adlandirilmis parti olarak yeniden hesaplanir;
  - kaynak.digerAyristirma'ya ne yapildigi yazilir. Uymayan satira dokunulmaz.
Idempotent: ayrilmis satirda 'Diğer' kalmadigi icin ikinci calistirma bir sey degistirmez.
Yerel import (yerel_1994_1999_2004/, merge_mahalli.py) yeniden calistirilirsa bu betik de ardindan
calistirilmalidir.

Kullanim (repo kokunden):
  python3 scripts/pipelines/tuik_arsiv/diger_ayristir.py [kontrol|uygula]
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election, save_election  # noqa: E402

SECIMLER = ["1994yerel", "1999yerel", "2004yerel"]


def ayristir(rec):
    sayac = {"ayrildi": 0, "kazanan_degisti": 0, "uymadi": 0}
    for lv in ("iller", "ilceler"):
        for r in rec.get(lv) or []:
            oy = r.get("oy") or {}
            dig = oy.get("Diğer")
            if not dig:
                continue
            kaynak = r.get("kaynak") if isinstance(r.get("kaynak"), dict) else {}
            dagilim = (kaynak.get("tuik") or {}).get("digerDagilimi")
            gecerli = r.get("gecerliOy")
            if (not dagilim or "tuikKullanilmadi" in kaynak or not gecerli
                    or sum(dagilim.values()) != dig.get("oy") or set(dagilim) & (set(oy) - {"Diğer"})):
                sayac["uymadi"] += 1
                continue
            del oy["Diğer"]
            for parti, o in dagilim.items():
                if o:
                    oy[parti] = {"oran": round(o / gecerli * 100, 2), "oy": o}
            eski = r.get("kazanan")
            r["kazanan"] = max(oy, key=lambda p: oy[p].get("oy") or 0)
            r["oy"] = dict(sorted(oy.items()))
            kaynak["digerAyristirma"] = {
                "yontem": "YSK 'Diğer' toplamı, DİE kitabındaki dağılımla birebir tuttuğu için partilere ayrıldı",
                "digerOy": dig.get("oy"), "dagilim": dagilim}
            if eski != r["kazanan"]:
                kaynak["digerAyristirma"]["oncekiKazanan"] = eski
                sayac["kazanan_degisti"] += 1
            r["kaynak"] = kaynak
            sayac["ayrildi"] += 1
    return sayac


if __name__ == "__main__":
    uygula = len(sys.argv) > 1 and sys.argv[1] == "uygula"
    for anahtar in SECIMLER:
        rec = load_election(anahtar)
        s = ayristir(rec)
        print(f"{anahtar}: {s['ayrildi']} satır ayrıldı, {s['kazanan_degisti']} satırda kazanan değişti, "
              f"{s['uymadi']} satır kurala uymadığı için 'Diğer' kaldı")
        if uygula:
            save_election(anahtar, rec)
    if not uygula:
        print("(kontrol: hiçbir dosya yazılmadı; uygulamak için 'uygula')")
