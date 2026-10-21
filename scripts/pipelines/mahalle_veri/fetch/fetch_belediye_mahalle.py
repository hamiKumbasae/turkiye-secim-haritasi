"""
Belediyelerin acik veri portallarindaki (CKAN) mahalle siniri veri setlerini indirir; her portalin
lisans bilgisini de (package_show) saklar. Sinirlar oldugu gibi saklanir; sadelestirme eslestirmede.

Kaynaklar (KAYNAKLAR): Bursa BB (acikyesil.bursa.bel.tr), Sakarya BB (veri.sakarya.bel.tr),
Gaziantep BB (acikveri.gaziantep.bel.tr).
Cikti: <cikti>/<plaka>.geojson ve <cikti>/<plaka>.meta.json {portal, paket, lisans, lisans_url, kaynak_url, guncelleme}
Kullanim: python3 fetch_belediye_mahalle.py <cikti>
"""
import json
import pathlib
import sys
import urllib.request

UA = "Mozilla/5.0 (turkiye-secim-haritasi; github.com/hamiKumbasae/turkiye-secim-haritasi)"
KAYNAKLAR = [
    {"plaka": 16, "portal": "https://acikyesil.bursa.bel.tr", "paket": "mahalle-sinirlari"},
    {"plaka": 54, "portal": "https://veri.sakarya.bel.tr", "paket": "67faf6a1-18d6-440c-89ed-7c5374edf70e"},
    {"plaka": 27, "portal": "https://acikveri.gaziantep.bel.tr", "paket": "mahalle-sinir-alanlari"},
]


def al(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, */*"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    cikti = pathlib.Path(sys.argv[1])
    cikti.mkdir(parents=True, exist_ok=True)
    for k in KAYNAKLAR:
        try:
            paket = json.loads(al(f"{k['portal']}/api/3/action/package_show?id={k['paket']}"))["result"]
            aday = [r for r in paket["resources"] if "json" in (r.get("format", "") + r.get("url", "")).lower()]
            if not aday:
                raise RuntimeError("geojson kaynagi yok: " + str([(r.get("format"), r.get("url")) for r in paket["resources"]]))
            r = aday[0]
            veri = json.loads(al(r["url"]))
            if isinstance(veri, dict) and "features" not in veri:   # bazi API'ler {data: FeatureCollection} doner
                for v in veri.values():
                    if isinstance(v, dict) and "features" in v:
                        veri = v
                        break
            ozellik = veri.get("features", [])
            (cikti / f"{k['plaka']:02d}.geojson").write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
            meta = {"portal": k["portal"], "paket": paket.get("name"), "baslik": paket.get("title"),
                    "lisans": paket.get("license_title"), "lisans_id": paket.get("license_id"),
                    "lisans_url": paket.get("license_url"), "kaynak_url": r["url"],
                    "guncelleme": r.get("last_modified") or paket.get("metadata_modified"),
                    "kuruluş": (paket.get("organization") or {}).get("title")}
            (cikti / f"{k['plaka']:02d}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            alanlar = sorted((ozellik[0].get("properties") or {}).keys()) if ozellik else []
            gt = ozellik[0]["geometry"]["type"] if ozellik and ozellik[0].get("geometry") else None
            print(f"::notice title=Belediye {k['plaka']:02d}::{len(ozellik)} özellik, {gt}, alanlar {alanlar[:12]}, "
                  f"lisans {meta['lisans']} ({meta['lisans_url']})", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"::warning title=Belediye {k['plaka']:02d}::{str(e)[:300]}", flush=True)


if __name__ == "__main__":
    main()
