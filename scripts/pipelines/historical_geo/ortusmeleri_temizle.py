"""
Ayni haritada birlikte cizilen ilce poligonlari arasindaki ince ortusme seritlerini, catlaklari ve
bosluklari temizler.

Kaynak ilce geometrisindeki komsu ilceler ve onlardan uretilen tarihsel birlesimler (HIST-*, HISTK-*,
HIST<secim>-*) kenarlarda ince seritler hâlinde ust uste biniyordu. Haritada alttaki poligonun kenar
cizgisi ustteki poligonun dolgusu uzerinde gorunur kaliyor, ilce icinde ortada biten "gereksiz" cizgiler
olusuyordu (ornek 1995 Istanbul: Eyup ile Gaziosmanpasa, Esenler ile Gungoren).

Ayrica birlesimlerde kaynak parcalar tam oturmadigi icin poligonlarin icine giren sifir genislikli
catlaklar ve komsular arasinda ince beyaz kamalar (bosluk) kaliyordu; catlaklar ilce icinde ortada biten
tek cizgi olarak gorunuyordu (ornek 1991-2007 Istanbul: Eyup, Umraniye, Kartal, Uskudar).

Kural (yalniz ILLER'deki iller; "birlikte" = herhangi bir secimde ayni haritada cizilen poligonlar,
bugunku ilceler birbirleriyle her zaman birlikte):
  1. Ortusme: bugunku ilce kimlik sirasiyla kendinden onceki bugunku komsularla, tarihsel poligon
     (geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson) birlikte cizildigi bugunku ilcelerle ve
     kimligi kendinden once gelen tarihsel poligonlarla ortusen seridi birakir.
  2. Catlak: her poligon CATLAK (~30 m) ile morfolojik olarak kapatilir; eklenen alan birlikte cizildigi
     bir poligonun gercek alaninaysa alinmaz. Catlaga giren sifir genislikli komsu dili (DIL) alinir ve
     komsu o alani birakir. Poligonun kendi alani hic azalmaz.
  3. Bosluk: bir secimde birlikte cizilen poligonlarin birlesimindeki kucuk ve ince delikler (BOSLUK,
     BOSLUK_GENISLIK) en uzun ortak siniri olan tarihsel poligona eklenir (bugunku ilceler baska
     donemlerde de cizildigi icin dolgu almaz); dolgu sahibin birlikte cizildigi bir poligonla ortusmez.
  Kalan kirintilar (alan < KIRINTI) atilir; gercek adaciklar (Adalar) bundan buyuktur.
Adimlar birbirini etkileyebildigi icin degisiklik kalmayana dek (en cok 5 tur) tekrarlanir; esikler
(MIN_ORTUSME vb.) altindaki farklara dokunulmaz: betik idempotenttir.

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/ortusmeleri_temizle.py
"""
import collections
import json
import pathlib
import sys

from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_all_elections  # noqa: E402

MODERN = ROOT / "geo/normalized/turkiye_ilce_sinirlari.geojson"
HIST_GEO = ROOT / "geo/historical/turkiye_ilce_sinirlari_hist_splits.geojson"
ILLER = {34}
MIN_ORTUSME = 1e-9   # derece^2; bundan kucuk ortusmeye dokunulmaz
KIRINTI = 5e-7       # derece^2 (~5000 m2); en kucuk gercek parca (Adalar) ~6e-6
BOSLUK = 2e-5        # derece^2 (~0.2 km2); bundan buyuk delik (gol, baraj) bosluk sayilmaz
BOSLUK_GENISLIK = 1e-3  # derece (~100 m); ortalama genisligi bundan buyuk delik dolgu degil
CATLAK = 3e-4        # derece (~30 m); bundan dar catlaklar kapatilir
DIL = 1e-5           # derece (~1 m); catlaga giren komsu dilinin en buyuk ortalama genisligi


def oku(p):
    return json.loads(p.read_text(encoding="utf-8"))


def temiz(g):
    return g if g.is_valid else g.buffer(0)


def poligonlar(g):
    if g.geom_type == "Polygon":
        return [g]
    return [p for x in getattr(g, "geoms", []) for p in poligonlar(x)]


def birlestir(parcalar):
    parcalar = [p for p in parcalar if p.area >= KIRINTI]
    return parcalar[0] if len(parcalar) == 1 else MultiPolygon(parcalar)


def kapat(g, komsular):
    """Dar catlaklari kapatir: morfolojik kapamanin ekledigi ve hicbir komsunun gercekten kaplamadigi
    alan poligona eklenir. Komsunun catlaga giren sifir genislikli dili (ortalama genislik < DIL) catlakla
    birlikte alinir; o komsular sonra bu alani birakir. Donus: (yeni poligon, dili alinan komsular) ya da None."""
    # mitre sivri koseleri kirpabilir: poligonun kendi alani hic kaybedilmez
    kapali = unary_union([g.buffer(CATLAK, join_style=2).buffer(-CATLAK, join_style=2), g])
    ek = kapali.difference(g)
    dilli, engel = [], []
    for k, kg in komsular.items():
        if not kg.intersects(ek):
            continue
        o = kg.intersection(ek)
        if o.area > 0 and 2 * o.area / o.length < DIL:
            dilli.append(k)
        elif o.area > 0:
            engel.append(kg)
    # kapali sekil dogrudan alinir: sifir genislikli catlak (ayni poligonun iki parcasi arasi) alan
    # farki olarak gorunmez; yalniz komsunun gercekten kapladigi ek alan cikarilir
    y = kapali
    if engel:
        y = y.difference(unary_union(engel).difference(g))
    y = birlestir(poligonlar(temiz(y)))
    # sifir genislikli catlak alan eklemez, yalniz siniri kisaltir
    if y.area - g.area < MIN_ORTUSME and g.length - y.length < 1e-4:
        return None
    return y, dilli


def cikar(g, digerleri):
    """g'den digerleriyle ortusen seridi cikarir; ortusme yoksa None."""
    digerleri = [d for d in digerleri if d.intersects(g)]
    if not digerleri:
        return None
    o = unary_union(digerleri)
    if g.intersection(o).area < MIN_ORTUSME:
        return None
    return birlestir(poligonlar(temiz(g.difference(o))))


def bir_tur():
    md, hd = oku(MODERN), oku(HIST_GEO)
    feat = {f["properties"]["id"]: f for f in md["features"] if f["properties"]["plaka"] in ILLER}
    bugunku = set(feat)
    hfeat = {f["properties"]["id"]: f for f in hd["features"]}
    kumeler = {frozenset(i for i in bugunku if feat[i]["properties"]["plaka"] == il) for il in ILLER}
    for kayit in load_all_elections().values():
        for il in ILLER:
            kumeler.add(frozenset(r["geomId"] for r in kayit.get("ilceler") or []
                                  if r.get("plaka") == il and (r.get("geomId") in bugunku or r.get("geomId") in hfeat)))
    birlikte = collections.defaultdict(set)
    for kume in kumeler:
        for i in kume:
            birlikte[i] |= kume - {i}
    feat.update((h, hfeat[h]) for h in birlikte if h in hfeat)
    geo = {i: temiz(shape(feat[i]["geometry"])) for i in birlikte}
    degisen = collections.Counter()

    def yaz(i, g, neden):
        geo[i] = g
        feat[i]["geometry"] = mapping(g)
        degisen[("bugunku " if i in bugunku else "tarihsel ") + neden] += 1

    # 1. ortusmeler: bugunku ilce kimligi kendinden onceki bugunku komsulari, tarihsel poligon
    #    birlikte cizildigi bugunku ilceleri ve kimligi kendinden once gelen tarihsel poligonlari birakir
    for i in sorted(birlikte, key=lambda i: (i not in bugunku, i)):
        digerleri = [geo[o] for o in sorted(birlikte[i]) if (o in bugunku) != (i in bugunku) and o in bugunku
                     or (o in bugunku) == (i in bugunku) and o < i]
        y = cikar(geo[i], digerleri)
        if y is not None:
            yaz(i, y, "ortusme")

    # 2. catlaklar: hicbir komsuya tasmadan kapatilir
    for i in sorted(birlikte):
        sonuc = kapat(geo[i], {o: geo[o] for o in birlikte[i]})
        if sonuc is None:
            continue
        yaz(i, sonuc[0], "catlak")
        for k in sonuc[1]:
            y = cikar(geo[k], [geo[i]])
            if y is not None:
                yaz(k, y, "dil")

    # 3. birlikte cizilen poligonlarin arasinda kalan ince bosluklar: en uzun ortak siniri olan tarihsel
    #    poligona (bugunku ilceler baska donemlerde de cizilir); dolgu sahibin herhangi bir secimde birlikte
    #    cizildigi bir poligonla ortusmemeli
    for kume in sorted(kumeler, key=sorted):
        for p in poligonlar(unary_union([geo[i] for i in kume])):
            for r in p.interiors:
                b = Polygon(r)
                if not MIN_ORTUSME <= b.area <= BOSLUK or 2 * b.area / b.length > BOSLUK_GENISLIK:
                    continue
                kenar = b.exterior.buffer(1e-6)
                adaylar = [i for i in sorted(kume) if i not in bugunku and geo[i].intersects(kenar)
                           and not any(geo[o].intersection(b).area > MIN_ORTUSME for o in birlikte[i])]
                if adaylar:
                    sahip = max(adaylar, key=lambda i: geo[i].intersection(kenar).area)
                    y = birlestir(poligonlar(temiz(unary_union([geo[sahip], b]))))
                    if y.area - geo[sahip].area >= MIN_ORTUSME:  # yalniz noktada degen dolgu kirinti olur
                        yaz(sahip, y, "bosluk")

    if any(k.startswith("bugunku") for k in degisen):
        MODERN.write_text(json.dumps(md, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if any(k.startswith("tarihsel") for k in degisen):
        HIST_GEO.write_text(json.dumps(hd, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return degisen


def main():
    # catlak kapama ile ortusme cikarma birbirini etkileyebilir; degisiklik kalmayana dek tekrarla
    toplam = collections.Counter()
    for _ in range(5):
        degisen = bir_tur()
        if not degisen:
            break
        toplam.update(degisen)
    else:
        raise SystemExit(f"5 turda durulmadi: {dict(degisen)}")
    print("ortüşme temizlendi:", dict(toplam) or "değişiklik yok")


if __name__ == "__main__":
    main()
