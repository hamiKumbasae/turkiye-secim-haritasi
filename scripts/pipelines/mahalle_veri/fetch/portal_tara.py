"""
Acik veri portallarinda mahalle/koy siniri veri seti arar ve sonucu GitHub Actions notu (::notice) olarak yazar.
Indirme yapmaz; yalniz ne oldugunu, bicimini ve lisansini listeler.

- CKAN portallari: package_search (mahalle, sinir, idari) -> veri seti adi, lisans, kaynak bicimleri.
- Diger sayfalar: HTML'den anahtar sozcuk gecen satirlar ve baglantilar.
Kullanim: python3 portal_tara.py
"""
import html
import json
import re
import ssl
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (turkiye-secim-haritasi; github.com/hamiKumbasae/turkiye-secim-haritasi)"
CKAN = ["https://acikveri.manisa.bel.tr", "http://acikveri.manisa.bel.tr"]
SAYFALAR = ["https://tucbskontrol.csb.gov.tr/TUCBSAcikVeri", "https://atlas.gov.tr/"]
TERIMLER = ["mahalle", "sınır", "idari", "köy"]
ANAHTAR = re.compile(r"mahalle|k[öo]y|idari|s[ıi]n[ıi]r|administrative|boundar", re.I)


def al(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/html, */*"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        return r.status, r.read().decode("utf-8", "replace")


def notu(baslik, mesaj):
    mesaj = mesaj.replace("\n", " | ")[:3500]
    print(f"::notice title={baslik}::{mesaj}", flush=True)


def ckan(portal):
    bulunan = {}
    for t in TERIMLER:
        try:
            _, govde = al(f"{portal}/api/3/action/package_search?rows=50&q={urllib.parse.quote(t)}")
            for p in json.loads(govde)["result"]["results"]:
                bicim = sorted({(r.get("format") or "?").lower() for r in p.get("resources", [])})
                bulunan[p["name"]] = f"{p.get('title')} [{','.join(bicim)}] lisans={p.get('license_title') or p.get('license_id')}"
        except Exception as e:  # noqa: BLE001
            notu(f"CKAN {portal}", f"'{t}' aramasi basarisiz: {str(e)[:200]}")
            return
    notu(f"CKAN {portal}", f"{len(bulunan)} veri seti: " + " ; ".join(f"{k}: {v}" for k, v in bulunan.items()) if bulunan
         else "eslesen veri seti yok")


def sayfa(url):
    try:
        durum, govde = al(url)
    except Exception as e:  # noqa: BLE001
        notu(f"Sayfa {url}", f"acilamadi: {str(e)[:200]}")
        return
    metin = html.unescape(re.sub(r"<[^>]+>", "\n", govde))
    satirlar = sorted({s.strip() for s in metin.splitlines() if s.strip() and ANAHTAR.search(s) and len(s.strip()) < 200})
    baglantilar = sorted({b for b in re.findall(r'href="([^"]+)"', govde) if ANAHTAR.search(b)})
    notu(f"Sayfa {url}", f"HTTP {durum}, {len(govde)} bayt; anahtar satirlar: {satirlar[:40]}; baglantilar: {baglantilar[:20]}")


def main():
    for p in CKAN:
        ckan(p)
    for s in SAYFALAR:
        sayfa(s)


if __name__ == "__main__":
    main()
