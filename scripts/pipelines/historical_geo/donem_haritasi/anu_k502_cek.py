"""
AMS K502 (Turkey 1:250.000, 1. baski 1953) paftalarini ANU Open Research deposundan ceker.

Kaynak: Australian National University, Map Collection (openresearch-repository.anu.edu.au), DSpace 7.
Paftalar "Prepared by Army Map Service, Corps of Engineers, US Army"; depoda "Copyright Expired",
"Open Access". 1950 il sinirlarini dogrulamak icin donem haritasi olarak kullanilir.

Gelistirme ortamindan erisilmiyor; GitHub Actions'ta calisir (.github/workflows/donem-haritasi-cek.yml).

Kullanim:
  python3 anu_k502_cek.py CIKTI listele
  python3 anu_k502_cek.py CIKTI indir [PAFTA,PAFTA,...]     # bos: hepsi; ornek "NJ 37-6,NJ 35-4"
Cikti: CIKTI/liste.csv (uuid, baslik, pafta, yil, dosya, boyut, url) ve CIKTI/<pafta>.jpg
"""
import csv
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://openresearch-repository.anu.edu.au/server/api"
UA = {"User-Agent": "turkiye-secim-haritasi (github.com/hamiKumbasae/turkiye-secim-haritasi)"}


def al(url, ikili=False, deneme=4):
    for i in range(deneme):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                veri = r.read()
            return veri if ikili else json.loads(veri)
        except Exception as e:  # noqa: BLE001
            if i == deneme - 1:
                raise
            print(f"  tekrar ({e}): {url}", flush=True)
            time.sleep(5 * (i + 1))


def meta(obj, alan):
    v = (obj.get("metadata") or {}).get(alan) or []
    return v[0]["value"] if v else ""


def ara():
    bulunan, sayfa = {}, 0
    while True:
        q = urllib.parse.urlencode({"query": "K502", "dsoType": "ITEM", "size": 100, "page": sayfa})
        d = al(f"{API}/discover/search/objects?{q}")
        sr = d["_embedded"]["searchResult"]
        for o in sr["_embedded"].get("objects", []):
            it = o["_embedded"]["indexableObject"]
            baslik = meta(it, "dc.title") or it.get("name", "")
            if "Turkey" in baslik and "K502" in baslik:
                bulunan[it["uuid"]] = it
        sp = sr["page"]
        print(f"sayfa {sp['number'] + 1}/{sp['totalPages']} ({sp['totalElements']} sonuç)", flush=True)
        sayfa += 1
        if sayfa >= sp["totalPages"]:
            return bulunan


def jpeg(uuid):
    for b in al(f"{API}/core/items/{uuid}/bundles")["_embedded"]["bundles"]:
        if b["name"] != "ORIGINAL":
            continue
        for bs in al(b["_links"]["bitstreams"]["href"])["_embedded"]["bitstreams"]:
            if bs["name"].lower().endswith((".jpg", ".jpeg")):
                return bs["name"], bs.get("sizeBytes"), f"{API}/core/bitstreams/{bs['uuid']}/content"
    return None, None, None


def main():
    cikti, mod = pathlib.Path(sys.argv[1]), sys.argv[2]
    secili = {p.strip() for p in (sys.argv[3] if len(sys.argv) > 3 else "").split(",") if p.strip()}
    cikti.mkdir(parents=True, exist_ok=True)
    satirlar = []
    for uuid, it in sorted(ara().items(), key=lambda x: meta(x[1], "dc.title")):
        baslik = meta(it, "dc.title")
        pafta = meta(it, "local.identifier.sheetNumber") or (re.search(r"Sheet ([A-Z]{2} ?\d+-\d+)", baslik) or [None, ""])[1]
        ad, boyut, url = jpeg(uuid)
        satirlar.append({"uuid": uuid, "baslik": baslik, "pafta": pafta, "yil": meta(it, "dc.date.issued"),
                         "notlar": " | ".join(m["value"] for m in (it.get("metadata") or {}).get("local.description.notes", [])),
                         "dosya": ad, "boyut": boyut, "url": url})
        print(f"{pafta:10s} {meta(it, 'dc.date.issued')}  {baslik}", flush=True)
    with open(cikti / "liste.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]))
        w.writeheader()
        w.writerows(satirlar)
    print(f"::notice title=K502::{len(satirlar)} Türkiye paftası listelendi")
    if mod != "indir":
        return
    for s in satirlar:
        if not s["url"] or (secili and s["pafta"] not in secili):
            continue
        hedef = cikti / (s["pafta"].replace(" ", "") + ".jpg")
        hedef.write_bytes(al(s["url"], ikili=True))
        print(f"indirildi {hedef.name} {hedef.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
