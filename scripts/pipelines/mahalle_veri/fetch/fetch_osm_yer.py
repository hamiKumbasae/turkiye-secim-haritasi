"""
OpenStreetMap'teki koy/mahalle yer noktalarini (place=village/hamlet/neighbourhood/quarter/...) il il ceker.

Amac: TKGM bircok koyu eski adiyla tutuyor (Bismil 'Akbaş' -> TKGM 'Alibociyan'); YSK muhtarligi guncel
adla geldigi icin ad eslemesi kurulamiyor. OSM noktasi guncel adi (name) ve cogu zaman eski adi
(old_name) tasir; eslestirme betigi noktanin hangi TKGM biriminin icine dustugune bakar. Sinir cizilmez,
yalniz mevcut resmi poligonun hangi muhtarliga ait oldugu bulunur.

Kaynak: Overpass API (overpass-api.de; yedek: overpass.kumi.systems). Il alani ISO3166-2 etiketiyle.
Dugum olarak isaretli yerler dogrudan, alan (way/relation) olarak isaretli yerler merkez noktasiyla.
Lisans: ODbL 1.0, (c) OpenStreetMap katkicilari.

Cikti: <cikti>/<plaka>.json; [{osm, tur, lon, lat, place, ad, adlar}] - ad = name (yoksa name:tr), adlar =
butun ad etiketleri (name, name:tr, old_name, alt_name, official_name, loc_name, int_name ...).
Kullanim: python3 fetch_osm_yer.py <cikti klasoru> <plaka,plaka,...>
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

SUNUCULAR = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
UA = "turkiye-secim-haritasi (github.com/hamiKumbasae/turkiye-secim-haritasi)"
YERLER = "village|hamlet|neighbourhood|quarter|suburb|town|city|isolated_dwelling|locality|farm"
AD_ETIKETLERI = ("name", "name:tr", "old_name", "old_name:tr", "alt_name", "alt_name:tr", "official_name",
                 "loc_name", "short_name", "int_name", "name:ku", "name:diq", "name:hy", "name:el", "name:ar")

SORGU = """[out:json][timeout:900];
area["ISO3166-2"="TR-{plaka:02d}"]["admin_level"="4"]->.il;
nwr(area.il)["place"~"^({yerler})$"];
out center tags;"""


def al(sorgu, deneme=6):
    for i in range(deneme):
        url = SUNUCULAR[i % len(SUNUCULAR)]
        try:
            veri = urllib.parse.urlencode({"data": sorgu}).encode()
            req = urllib.request.Request(url, data=veri, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=960) as r:
                d = json.loads(r.read().decode("utf-8"))
            # Overpass zaman asiminda HTTP 200 ve bos sonuc + 'remark' doner: hata say, tekrar dene
            if not d.get("elements") and "error" in (d.get("remark") or "").lower():
                raise RuntimeError(d["remark"][:200])
            return d
        except Exception as e:  # noqa: BLE001
            print("  tekrar:", url, str(e)[:150], flush=True)
            if i == deneme - 1:
                raise
            time.sleep(30 * (i + 1))


def main():
    cikti = pathlib.Path(sys.argv[1])
    cikti.mkdir(parents=True, exist_ok=True)
    hatali = []
    for plaka in [int(p) for p in sys.argv[2].split(",")]:
        t0 = time.time()
        try:
            d = al(SORGU.format(plaka=plaka, yerler=YERLER))
        except Exception as e:  # noqa: BLE001 - bir ilin hatasi digerlerini durdurmasin
            print(f"::error title=OSM yer {plaka:02d}::{str(e)[:200]}", flush=True)
            hatali.append(plaka)
            continue
        yerler = []
        for el in d.get("elements", []):
            t = el.get("tags", {})
            nokta = (el.get("lon"), el.get("lat")) if el["type"] == "node" else \
                ((el.get("center") or {}).get("lon"), (el.get("center") or {}).get("lat"))
            adlar = {k: t[k] for k in AD_ETIKETLERI if t.get(k)}
            if nokta[0] is None or not adlar:
                continue
            yerler.append({"osm": el["id"], "tur": el["type"][0], "lon": round(nokta[0], 5), "lat": round(nokta[1], 5),
                           "place": t.get("place"), "ad": t.get("name") or t.get("name:tr"), "adlar": adlar})
        if not yerler:
            print(f"::error title=OSM yer {plaka:02d}::hic yer donmedi", flush=True)
            hatali.append(plaka)
            continue
        yerler.sort(key=lambda y: (y["tur"], y["osm"]))
        (cikti / f"{plaka:02d}.json").write_text(json.dumps(yerler, ensure_ascii=False, separators=(",", ":")),
                                                encoding="utf-8")
        eski = sum(1 for y in yerler if any(k.startswith("old_name") for k in y["adlar"]))
        print(f"::notice title=OSM yer {plaka:02d}::{len(yerler)} yer, eski adli {eski}, {time.time() - t0:.0f} sn",
              flush=True)
        time.sleep(5)
    if hatali:
        raise SystemExit(f"cekilemeyen iller: {hatali}")


if __name__ == "__main__":
    main()
