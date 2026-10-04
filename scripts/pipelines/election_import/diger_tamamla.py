"""
Parti oylari toplami gecerli oydan biraz az olan il/ilce kayitlarinda (fark en cok ESIK), aradaki
farki 'Diğer' satirina ekler. Kaynaklar cogu zaman yalniz buyuk partileri ve bagimsizlari ayri
verir; kalan kucuk partilerin oylari kayitta hic yoktu ve oranlar bu eksik toplama gore
hesaplanmisti (ornek 2011 genel: ilcelerin cogunda %0,2 eksik).

Kural:
  - yalniz 0 < (gecerli oy - parti toplami) <= gecerli oy x ESIK olan kayitlar; daha buyuk farklar
    kaynakla incelenmeli (bkz. wiki_bagimsiz.py ve data/validation),
  - 'Diğer' yoksa eklenir, varsa artirilir; oranlar gecerli oya gore yeniden hesaplanir,
  - halk oylamalari (yalniz Evet/Hayir) ve cumhurbaskanligi secimleri (tum adaylar ayri) disarida,
  - kazanan degismez (fark en cok %5; bilinmeyen partilerin toplami tek bir kazanan degildir),
  - kaynak.digerTamamlama alanina eklenen oy yazilir.
Parti toplami gecerli oydan fazla olan kayitlara dokunulmaz.

Kullanim:
  .venv/bin/python scripts/pipelines/election_import/diger_tamamla.py [kontrol|uygula]
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_all_elections, save_election  # noqa: E402

ESIK = 0.05


def tamamla(rec):
    sayi = 0
    for lv in ("iller", "ilceler"):
        for r in rec.get(lv, []):
            v = r.get("gecerliOy")
            oy = r.get("oy") or {}
            if not v or not oy or any(x.get("oy") is None for x in oy.values()):
                continue
            fark = v - sum(x["oy"] for x in oy.values())
            if fark <= max(1, v * 0.0001) or fark > v * ESIK:
                continue
            oy.setdefault("Diğer", {"oy": 0})
            oy["Diğer"]["oy"] += fark
            for x in oy.values():
                x["oran"] = round(x["oy"] / v * 100, 2)
            if not isinstance(r.get("kaynak"), dict):
                r["kaynak"] = {}
            r["kaynak"]["digerTamamlama"] = {
                "oy": fark, "not": "parti oyları toplamı ile geçerli oy arasındaki fark (kaynakta ayrı verilmeyen partiler)"}
            sayi += 1
    return sayi


if __name__ == "__main__":
    uygula = len(sys.argv) > 1 and sys.argv[1] == "uygula"
    toplam = 0
    for key, rec in load_all_elections().items():
        if rec.get("tur") in ("referandum", "cumhurbaskanligi"):
            continue
        n = tamamla(rec)
        if n:
            print(key, n)
            toplam += n
            if uygula:
                save_election(key, rec)
    print("toplam", toplam)
