"""
Eski yerel secimlerde (1963-1989) il merkezinin sonucunu ilce haritasinda gosterir.

Yerel secim satirlari belediyedir: il merkezi belediyesinin (belediye baskanligi) sonucu il
satirinda durur, Merkez ilcenin ayri ilce satiri yoktur; bu yuzden ilce haritasinda merkez
ilce 'veri yok' kaliyordu (Adana, Antalya, Konya ...). Bu betik:

  1. Her yerel secimi ayni doneme en yakin genel secimle eslestirir (EŞLEŞME).
  2. Genel secimde 'Merkez' satiri olup yerel secimde olmayan her ilde, il satirinin sonucunu
     (oy, kazanan, secmen, katilim, sandik) birebir kopyalayan bir 'Merkez' satiri ekler;
     geometrisi genel secimdeki Merkez satirinin (o donemki) poligonudur. Merkez'den sonradan
     ayrilan ilceler apply_idari_merges.py ile bu poligona katilir.
  3. Il merkezi belediyesinin birden cok ilceyi kapsadigi uc ilde (1963-1977: Istanbul,
     Ankara, Izmir; SEHIR_ILCELERI) bu ilcelerin birlesimi olan tek bir poligon (HISTY-*)
     uretir ve satiri ona baglar.

Büyükşehir yillarinda (1984+) il satiri buyuksehir baskaninin sonucudur; o illerde merkez
ilceler zaten kendi satirlariyla var ve genel secimde 'Merkez' satiri yoktur, bu yuzden kural
kendiliginden uygulanmaz. Oy degerleri degismez; eklenen satirlar `ilMerkeziBelediyesi: true`
ile isaretlidir ve her calistirmada sifirdan uretilir (idempotent).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/ekle_il_merkezi_satirlari.py
  (ardindan apply_idari_merges.py, scripts/build.py)
"""
import json
import pathlib
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/pipelines/historical_geo"))
from common.election_io import load_election, save_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402
from dikis_deliklerini_doldur import bilesen_delikleri, delikleri_doldur, temiz  # noqa: E402

HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
SPLITS = ROOT / "geo/historical/district_splits.json"
MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
PLAN = ROOT / "geo/historical/idari/merge_plan.json"
ONEK = "HISTY-"

# yerel secim -> ayni doneme en yakin genel secim (ilce listesi ve Merkez poligonu buradan)
ESLESME = {"1963yerel": "1961", "1968yerel": "1969", "1973yerel": "1973", "1977yerel": "1977",
           "1984yerel": "1983", "1989yerel": "1987", "1994yerel": "1995", "1999yerel": "1999",
           "2004yerel": "2002"}
# il merkezi belediyesinin Merkez disinda kapsadigi ilceler (yerel secimde kendi satirlari yok;
# Wikipedia/YSK il sayfalarinda bu ilceler ayri belediye olarak gecmez)
SEHIR_ILCELERI = {
    34: {"yillar": {"1963yerel", "1968yerel", "1973yerel", "1977yerel"}, "ad": "İstanbul (il merkezi belediyesi)",
         "ilceler": ["Adalar", "Bakırköy", "Beşiktaş", "Beykoz", "Beyoğlu", "Eminönü", "Eyüp", "Fatih",
                     "Gaziosmanpaşa", "Kadıköy", "Sarıyer", "Şişli", "Üsküdar", "Zeytinburnu"]},
    6: {"yillar": {"1963yerel", "1968yerel", "1973yerel", "1977yerel"}, "ad": "Ankara (il merkezi belediyesi)",
        "ilceler": ["Merkez", "Altındağ", "Çankaya", "Yenimahalle"]},
    35: {"yillar": {"1963yerel", "1968yerel", "1973yerel", "1977yerel"}, "ad": "İzmir (il merkezi belediyesi)",
         "ilceler": ["Merkez", "Karşıyaka"]},
}
# buyuksehir belediyesi olan iller (il satiri buyuksehir baskaninin sonucu, merkez ilce satiri
# uretilmez): 1984 Istanbul, Ankara, Izmir (3030 sayili Kanun); 1986 Adana; 1987 Bursa,
# Gaziantep, Konya; 1988 Kayseri
BUYUKSEHIR = {"1984yerel": {34, 6, 35}, "1989yerel": {34, 6, 35, 1, 16, 27, 42, 38}}
# 1994-2004: 1993'te (504 sayili KHK) Antalya, Diyarbakir, Erzurum, Eskisehir, Kocaeli, Mersin,
# Samsun; 2000'de Sakarya buyuksehir oldu. Bu illerde Merkez ilce henuz bolunmedi: il satiri
# (buyuksehir baskani) Merkez'e cizilir ve 'buyuksehir' diye isaretlenir. Merkezi bolunmus
# buyuksehirlerde (Istanbul, Ankara, Izmir, Adana, Bursa, Gaziantep, Konya, Kayseri) genel
# secimde 'Merkez' satiri olmadigi icin kural kendiliginden uygulanmaz.
BUYUKSEHIR_ETIKET = {
    "1994yerel": {34, 6, 35, 1, 16, 27, 42, 38, 7, 21, 25, 26, 41, 33, 55},
    "1999yerel": {34, 6, 35, 1, 16, 27, 42, 38, 7, 21, 25, 26, 41, 33, 55},
    "2004yerel": {34, 6, 35, 1, 16, 27, 42, 38, 7, 21, 25, 26, 41, 33, 55, 54},
}
KOPYA = ("oy", "kazanan", "gecerliOy", "secmen", "katilim", "sandik")


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    splits = oku(SPLITS)
    hist = oku(HIST_GEO)
    modern = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in oku(MODERN)["features"]}
    histk_taban = {sid: e["taban"] for sid, e in oku(PLAN)["sentetikler"].items()} if PLAN.exists() else {}
    hist_parca = {e["syntheticId"]: set(e["hideIds"]) for v in splits.values() for e in v
                  if not e["syntheticId"].startswith(("HISTK-", ONEK))}
    hist_geo = {f["properties"]["id"]: temiz(shape(f["geometry"])) for f in hist["features"]
                if not f["properties"]["id"].startswith(("HISTK-", ONEK))}

    yeni_poligon, yeni_split, rapor, rapor_atla, rapor_cevrili = {}, [], [], [], []
    for yerel, genel in ESLESME.items():
        Y, G = load_election(yerel), load_election(genel)
        Y["ilceler"] = [r for r in Y["ilceler"] if not r.get("ilMerkeziBelediyesi")]   # idempotent
        var, kapsanan = {}, set()
        for r in Y["ilceler"]:
            var.setdefault(r["plaka"], set()).add(fold(r["ad"]).upper())
            g = histk_taban.get(r.get("geomId"), r.get("geomId"))
            if g:
                kapsanan |= hist_parca.get(g, {g}) | {g}
        genel_satir = {}
        for r in G.get("ilceler") or []:
            g = r.get("geomId")
            genel_satir.setdefault(r["plaka"], {})[r["ad"]] = histk_taban.get(g, g)
        for il in Y["iller"]:
            pl = il["plaka"]
            gs = genel_satir.get(pl, {})
            sehir = SEHIR_ILCELERI.get(pl)
            if sehir and yerel in sehir["yillar"]:
                adlar = [a for a in sehir["ilceler"] if a in gs and fold(a).upper() not in var.get(pl, set())]
                if not adlar:
                    continue
                parcalar = set()
                for a in adlar:
                    g = gs[a]
                    if g:
                        parcalar |= hist_parca.get(g, {g})
                parcalar = {x for x in parcalar if x in modern}
                # kendi (belediye) satiri olmayan ve dort yani sehir ilceleriyle cevrili ilce sehrin
                # parcasidir (orn. 1963-1977 Kagithane: Sisli, Besiktas, Eyup, Sariyer arasinda)
                dolu = delikleri_doldur(unary_union([modern[x] for x in parcalar]))
                cevrili = sorted(k for k, v in modern.items() if k.split("-")[2] == f"{pl:02d}" and k not in parcalar
                                 and k not in kapsanan and v.intersection(dolu).area > 0.95 * v.area)
                if cevrili:
                    parcalar |= set(cevrili)
                    rapor_cevrili.append((yerel, pl, cevrili))
                if parcalar & kapsanan:
                    rapor_atla.append((yerel, pl, "şehir ilçelerinden biri zaten satırlı"))
                    continue
                sid = f"{ONEK}{pl:02d}-{yerel}"
                yeni_poligon[sid] = (pl, parcalar)
                yeni_split.append((pl, {"hideIds": sorted(parcalar), "splitYear": int(yerel[:4]), "syntheticId": sid}))
                geom_id, ad, kapsam = sid, sehir["ad"], adlar
            else:
                if "Merkez" not in gs or "MERKEZ" in var.get(pl, set()) or not gs["Merkez"]:
                    continue
                if pl in BUYUKSEHIR.get(yerel, set()):
                    rapor_atla.append((yerel, pl, "büyükşehir: il satırı büyükşehir başkanı"))
                    continue
                g = gs["Merkez"]
                parcalar = hist_parca.get(g, {g})
                ortak = parcalar & kapsanan
                if ortak and not (parcalar - ortak):
                    # Merkez'in butun alani baska bir satira (belde) bagli: ikisi ayni poligonu ister
                    rapor_atla.append((yerel, pl, f"Merkez alanı başka satıra bağlı: {sorted(ortak)}"))
                    continue
                if ortak:
                    # Merkez icindeki belde (orn. 1989 Samsun Tekkekoy) kendi satiriyla: Merkez onu disarida birakir
                    sid = f"{ONEK}{pl:02d}-{yerel}-merkez"
                    kalan = {x for x in parcalar - ortak if x in modern}
                    yeni_poligon[sid] = (pl, kalan)
                    yeni_split.append((pl, {"hideIds": sorted(kalan), "splitYear": int(yerel[:4]), "syntheticId": sid}))
                    g = sid
                geom_id, ad, kapsam = g, "Merkez", ["Merkez"]
            bs = pl in BUYUKSEHIR_ETIKET.get(yerel, set())
            satir = {"ad": ad, "plaka": pl, "geomId": geom_id, "ilMerkeziBelediyesi": True,
                     **({"buyuksehirSonucu": True} if bs else {}),
                     **{k: il[k] for k in KOPYA if k in il},
                     "kaynak": {"ana": "il satırı",
                                "not": ("Büyükşehir" if bs else "İl merkezi") + " belediye başkanlığı sonucu (il satırından birebir); harita, "
                                       f"{genel} genel seçimindeki {', '.join(kapsam)} ilçe sınırlarıyla çizer."}}
            Y["ilceler"].append(satir)
            rapor.append((yerel, pl, ad, geom_id))
        save_election(yerel, Y)

    # HISTY poligonlari: bileşen modern ilcelerin birlesimi (dikis delikleri doldurulur)
    hist["features"] = [f for f in hist["features"] if not f["properties"]["id"].startswith(ONEK)]
    for sid, (pl, parcalar) in sorted(yeni_poligon.items()):
        geoms = [modern[x] for x in parcalar]
        hist["features"].append({"type": "Feature", "properties": {"id": sid, "plaka": pl},
                                 "geometry": mapping(delikleri_doldur(
                                     unary_union(geoms), bilesen_delikleri(geoms),
                                     unary_union([v for k, v in modern.items()
                                                  if k not in parcalar and k.split("-")[2] == f"{pl:02d}"])))})
    hist["features"].sort(key=lambda f: f["properties"]["id"])
    HIST_GEO.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for pl in list(splits):
        splits[pl] = [e for e in splits[pl] if not e["syntheticId"].startswith(ONEK)]
    for pl, e in yeni_split:
        splits.setdefault(str(pl), []).append(e)
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(rapor), "il merkezi satırı eklendi;", len(yeni_poligon), "şehir birleşimi (HISTY)")
    print("şehir poligonuna katılan (kendi satırı yok, şehirle çevrili):", rapor_cevrili)
    for y in ESLESME:
        print(" ", y, sum(1 for r in rapor if r[0] == y), "eklendi; atlanan:",
              [(pl, n) for yy, pl, n in rapor_atla if yy == y])


if __name__ == "__main__":
    main()
