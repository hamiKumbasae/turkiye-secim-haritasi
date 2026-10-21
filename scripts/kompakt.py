"""
Mahalle yayin dosyalarinin kompakt bicimi (site/build.py ve scripts/build.py yazarken kullanir).

Kaynak (data/normalized/mahalle/, geo/normalized/mahalle_geo.json) ve public_files() mantiksal
bicimde kalir; yalniz yayina yazilan/gomulen dosya kucultulur, tarayici (data-loader.js) ayni
mantiksal bicime geri acar. Iki donusum de kayipsizdir (tests/kompakt_test.py):

data/mahalle_votes/<secim>.json  ->  {"bicim": "mahalle-oy/1", "partiler": [...], "ilceler":
    {geomId: {mahalleId: [secmen, oyKullanan, gecerliOy, sandik, kazananSira, oy0, oy1, ...]}}}
    oyN partiler[N]'nin oyu; o mahallede parti yoksa null (sondaki null'lar yazilmaz).
    oran = oy / gecerliOy * 100 ve katilim = oyKullanan / secmen * 100 (2 ondalik) tarayicida
    hesaplanir; kaynakta 2,4 milyon oranin hepsi bu formulle birebir ayni (yazarken denetlenir).

geo/mahalle/<geomId>.json  ->  TopoJSON (Topology). Komsu mahallelerin ortak sinirlari bir kez
    yazilir (arc paylasimi); koordinatlar zaten 4 ondalik oldugu icin 1e-4 olcekle tamsayiya
    cevrilip delta kodlanir, yani nicemleme kaybi yok. Nesne: objects.mahalle (GeometryCollection),
    her geometrinin id'si mahalle kimligi, properties.ad adi.
"""
BICIM_OY = "mahalle-oy/1"
OLCEK = 10_000  # 1e-4 derece


# ---------------------------------------------------------------- oy
def _oran(pay, payda):
    return round(pay / payda * 100, 2) if payda and pay is not None else None


def oy_kompakt(ilceler: dict) -> dict:
    sayac = {}
    for satirlar in ilceler.values():
        for v in satirlar.values():
            for p, o in v["oy"].items():
                sayac[p] = sayac.get(p, 0) + (o["oy"] or 0)
    partiler = sorted(sayac, key=lambda p: (-sayac[p], p))
    sira = {p: i for i, p in enumerate(partiler)}
    out = {}
    for g in sorted(ilceler):
        satirlar = {}
        for m in sorted(ilceler[g]):
            v = ilceler[g][m]
            if set(v) != {"secmen", "oyKullanan", "gecerliOy", "sandik", "katilim", "kazanan", "oy"}:
                raise ValueError(f"{g}/{m}: beklenmeyen alanlar {sorted(v)}")
            if v["katilim"] != _oran(v["oyKullanan"], v["secmen"]):
                raise ValueError(f"{g}/{m}: katılım oy kullanan/seçmen'den hesaplanamıyor ({v['katilim']})")
            oylar = [None] * len(partiler)
            for p, o in v["oy"].items():
                if set(o) != {"oy", "oran"} or o["oy"] is None or o["oran"] != _oran(o["oy"], v["gecerliOy"]):
                    raise ValueError(f"{g}/{m}/{p}: oran oy/geçerli oy'dan hesaplanamıyor ({o})")
                oylar[sira[p]] = o["oy"]
            while oylar and oylar[-1] is None:
                oylar.pop()
            kaz = None if v["kazanan"] is None else sira[v["kazanan"]]
            satirlar[m] = [v["secmen"], v["oyKullanan"], v["gecerliOy"], v["sandik"], kaz] + oylar
        out[g] = satirlar
    return {"bicim": BICIM_OY, "partiler": partiler, "ilceler": out}


def oy_ac(k: dict) -> dict:
    """oy_kompakt'in tersi (testler; tarayicidaki karsiligi data-loader.js: mahalleOyAc)."""
    partiler = k["partiler"]
    out = {}
    for g, satirlar in k["ilceler"].items():
        out[g] = {}
        for m, s in satirlar.items():
            secmen, kullanan, gecerli, sandik, kaz = s[:5]
            oy = {partiler[i]: {"oran": _oran(n, gecerli), "oy": n} for i, n in enumerate(s[5:]) if n is not None}
            out[g][m] = {"gecerliOy": gecerli, "katilim": _oran(kullanan, secmen),
                         "kazanan": None if kaz is None else partiler[kaz], "oy": oy,
                         "oyKullanan": kullanan, "sandik": sandik, "secmen": secmen}
    return out


# ---------------------------------------------------------------- TopoJSON
def _halkalar(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return c
    if t == "LineString":
        return []
    raise ValueError(f"desteklenmeyen geometri: {t}")


def geo_topo(satirlar: dict) -> dict:
    """{mahalleId: {ad, geometry}} -> TopoJSON Topology (kayipsiz, arc paylasimli)."""
    def q(pt):
        return (round(pt[0] * OLCEK), round(pt[1] * OLCEK))

    ids = sorted(satirlar)
    tum = [q(p) for m in ids for geom in [satirlar[m]["geometry"]]
           for p in (geom["coordinates"] if geom["type"] == "LineString"
                     else [p for poly in _halkalar(geom) for ring in poly for p in ring])]
    x0, y0 = min(p[0] for p in tum), min(p[1] for p in tum)

    # yollar: halkalar (kapali, son nokta tekrarsiz) ve cizgiler (acik)
    def yol(coords):
        return [(x - x0, y - y0) for x, y in map(q, coords)]

    yapilar = {}
    for m in ids:
        geom = satirlar[m]["geometry"]
        if geom["type"] == "LineString":
            yapilar[m] = ("L", yol(geom["coordinates"]))
        else:
            yapilar[m] = (geom["type"], [[yol(ring)[:-1] for ring in poly] for poly in _halkalar(geom)])

    # birlesim noktalari: ayni nokta farkli komsularla ikinci kez goruldugunde (topojson-server join)
    komsu, birlesim = {}, set()

    def ziyaret(p, a, b):
        cift = komsu.get(p)
        if cift is None:
            komsu[p] = (a, b)
        elif cift != (a, b) and cift != (b, a):
            birlesim.add(p)

    for tip, veri in yapilar.values():
        if tip == "L":
            birlesim.update((veri[0], veri[-1]))
            for i in range(1, len(veri) - 1):
                ziyaret(veri[i], veri[i - 1], veri[i + 1])
        else:
            for poly in veri:
                for ring in poly:
                    n = len(ring)
                    for i in range(n):
                        ziyaret(ring[i], ring[i - 1], ring[(i + 1) % n])

    arcs, anahtar, halka = [], {}, {}

    def arc_ekle(nokta):
        t = tuple(nokta)
        if t in anahtar:
            return anahtar[t]
        ters = t[::-1]
        if ters in anahtar:
            return ~anahtar[ters]
        anahtar[t] = len(arcs)
        arcs.append(nokta)
        return anahtar[t]

    def kanonik(ring):
        i = min(range(len(ring)), key=lambda j: ring[j])
        return ring[i:] + ring[:i]

    def halka_arclari(ring):
        kes = [i for i, p in enumerate(ring) if p in birlesim]
        if not kes:  # komsusuyla birlesim noktasi olmayan halka: aynisi (ya da tersi) varsa paylasilir
            r = kanonik(ring)
            t = tuple(r)
            if t in halka:
                return [halka[t]]
            tt = tuple(kanonik(ring[::-1]))
            if tt in halka:
                return [~halka[tt]]
            halka[t] = len(arcs)
            arcs.append(r + r[:1])
            return [halka[t]]
        r = ring[kes[0]:] + ring[:kes[0]]
        kes = [i - kes[0] for i in kes]
        sinir = kes + [len(r)]
        r = r + r[:1]
        return [arc_ekle(r[a:b + 1]) for a, b in zip(sinir, sinir[1:])]

    def cizgi_arclari(line):
        kes = [i for i, p in enumerate(line) if p in birlesim]
        return [arc_ekle(line[a:b + 1]) for a, b in zip(kes, kes[1:])]

    geometriler = []
    for m in ids:
        tip, veri = yapilar[m]
        if tip == "L":
            g = {"type": "LineString", "arcs": cizgi_arclari(veri)}
        else:
            polys = [[halka_arclari(ring) for ring in poly] for poly in veri]
            g = {"type": tip, "arcs": polys[0] if tip == "Polygon" else polys}
        g["id"] = m
        g["properties"] = {"ad": satirlar[m]["ad"]}
        geometriler.append(g)

    delta = []
    for a in arcs:
        d, px, py = [], 0, 0
        for x, y in a:
            d.append([x - px, y - py])
            px, py = x, y
        delta.append(d)
    return {"type": "Topology",
            "transform": {"scale": [1 / OLCEK, 1 / OLCEK], "translate": [x0 / OLCEK, y0 / OLCEK]},
            "objects": {"mahalle": {"type": "GeometryCollection", "geometries": geometriler}},
            "arcs": delta}


def topo_ac(topo: dict) -> dict:
    """geo_topo'nun tersi (testler; tarayicidaki karsiligi data-loader.js: topoAc).
    Halka baslangic noktasi degisebilir (ayni poligon)."""
    tx, ty = (round(v * OLCEK) for v in topo["transform"]["translate"])
    arcs = []
    for a in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append([(x + tx) / OLCEK, (y + ty) / OLCEK])
        arcs.append(pts)

    def cizgi(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts

    out = {}
    for g in topo["objects"]["mahalle"]["geometries"]:
        t = g["type"]
        if t == "Polygon":
            c = [cizgi(r) for r in g["arcs"]]
        elif t == "MultiPolygon":
            c = [[cizgi(r) for r in p] for p in g["arcs"]]
        else:
            c = cizgi(g["arcs"])
        out[g["id"]] = {"ad": g["properties"]["ad"], "geometry": {"type": t, "coordinates": c}}
    return out


def yayin_nesnesi(rel: str, obj):
    """public_files() nesnesinin yayina yazilan bicimi."""
    if rel.startswith("data/mahalle_votes/"):
        return oy_kompakt(obj)
    if rel.startswith("geo/mahalle/"):
        return geo_topo(obj)
    return obj
