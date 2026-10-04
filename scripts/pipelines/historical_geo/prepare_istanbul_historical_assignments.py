"""Mevcut kaynaklı 1992-2008 atamalarını 1961-1992 için geriye bağlar.

3392/3644/3806/3949 zincirleri build_istanbul_1961_1992.ZINCIR'dan alınır.
1987'de kurulan Ümraniye'nin (Üsküdar + Beykoz + kaynağı yazılmamış mahalleler)
1987 öncesi bağlılığı kanun listesinden çıkmaz; bu mahalleler 1960 sayımının köy
listesiyle (SAYIM_1960) bağlanır, adı sayımda olmayanlar komşu mahallelerin
çoğunluğuna verilir. Bu atamalar yaklaşıktır ('yaklasik': true); amaç 1961
haritasının genel olarak doğru görünmesi (1940/1963 ilçe haritalarıyla görsel
olarak karşılaştırıldı). Etkinleştirilen seçimler: 1961 genel, 1989 yerel,
1991 genel.
"""
import json

from shapely.geometry import shape
from shapely.ops import unary_union

from build_istanbul_1961_1992 import IDARI, ZINCIR, BASLANGIC
import build_istanbul_1992_2008 as b

SAYIM60 = "1960 sayımı (data/raw/tuik/nufus-sayimi-idari-bolunus/1960_0015128_istanbul.pdf)"
# (bugunku ilce kodu, mahalle) -> (1961 ilcesi, 1960 sayimindaki koy)
SAYIM_1960 = {
    ("016", "ALEMDAĞ MAH."): ("Üsküdar", "Alemdar köyü, Üsküdar Merkez bucağı"),
    ("016", "MERKEZ MAH."): ("Üsküdar", "Çekme köyü, Üsküdar Merkez bucağı"),
    ("016", "REŞADİYE MAH."): ("Üsküdar", "Reşadiye köyü, Üsküdar Merkez bucağı"),
    ("016", "SULTANÇİFTLİĞİ MAH."): ("Üsküdar", "Sultançiftliği köyü, Üsküdar Merkez bucağı"),
    ("016", "ÖMERLİ MAH."): ("Beykoz", "Ömerli bucak merkezi, Beykoz M. Şevketpaşa bucağı"),
    ("016", "HÜSEYİNLİ MAH."): ("Beykoz", "Hüseyinli köyü, Beykoz M. Şevketpaşa bucağı"),
    ("016", "KOÇULLU MAH."): ("Beykoz", "Koçullu köyü, Beykoz M. Şevketpaşa bucağı"),
    ("016", "SIRAPINAR MAH."): ("Beykoz", "Sırapınar köyü, Beykoz M. Şevketpaşa bucağı"),
    ("016", "CUMHURİYET MAH."): ("Beykoz", "Cumhuriyet köyü, Beykoz M. Şevketpaşa bucağı"),
    ("029", "SARIGAZİ MAH."): ("Kartal", "Sarıgazi köyü, Kartal Şamandıra bucağı"),
    ("029", "PAŞAKÖY MAH."): ("Kartal", "Paşaköy köyü, Kartal Şamandıra bucağı"),
}
# komsuluk icin butun hâlinde 1961 ilcesi bilinen bugunku ilceler
BUTUN_1961 = {"011": "Beykoz", "034": "Şile", "038": "Üsküdar", "023": "Kadıköy", "027": "Kartal",
              "032": "Kartal", "028": "Kartal", "037": "Üsküdar"}
ONCE = ("1961-01-01", "1987-07-04")


def komsuluk(mg, bos, bilinen):
    """bos: {(g, mid): geom}; bilinen: [(geom, ilce)] -> {(g, mid): (ilce, pay)}; iteratif."""
    sonuc = {}
    while bos:
        adaylar = []
        for k, geom in bos.items():
            tampon = geom.buffer(0.0015)
            pay = {}
            for g2, il in bilinen:
                if tampon.intersects(g2):
                    pay[il] = pay.get(il, 0) + tampon.intersection(g2).area
            if pay:
                il = max(pay, key=pay.get)
                adaylar.append((pay[il] / sum(pay.values()), k, il))
        if not adaylar:
            raise SystemExit(f"komşusu atanmamış mahalleler: {sorted(bos)}")
        adaylar.sort(reverse=True)
        pay, k, il = adaylar[0]  # en emin olani ata, komsularini yeniden hesapla
        sonuc[k] = (il, round(pay, 2))
        bilinen.append((bos.pop(k), il))
    return sonuc


def main():
    mg = json.loads(b.MAHALLE_GEO.read_text())
    modern = {f["properties"]["id"]: shape(f["geometry"]) for f in json.loads(b.MODERN.read_text())["features"]
              if f["properties"]["id"].startswith("TR-D-34-")}
    kodlar = {a: k for a, k in b.ILCELER.items() if k}
    tablo, umraniye = {}, {}
    for kod in sorted((set(b.MAHALLE) | set(b.BUTUN)) - {'020'}):
        g = f'TR-D-34-{kod}'
        rows = []
        for mid, m in sorted(mg[g].items()):
            parent, source = b.MAHALLE[kod][m['ad']] if kod in b.MAHALLE else b.BUTUN[kod]
            intervals = []
            for a, z in [(BASLANGIC, '1987-07-04'), ('1987-07-04', '1990-05-20'),
                         ('1990-05-20', '1992-06-03')]:
                if parent == 'Ümraniye' and a < '1987-07-04':
                    # iki kaynakli Umraniye: 1960 sayimi ya da komsuluk (asagida)
                    umraniye[(g, mid)] = m['ad']
                    intervals.append({'baslangic': a, 'bitis': z, 'ilce': None, 'dayanak': ''})
                    continue
                chain = ZINCIR.get(kodlar.get(parent), [])
                old = next((x for x in chain if x[0] <= a < x[1]), None)
                target = old[2] if old else parent
                basis = source + ('; önceki birim zinciri: ' + old[3] if old else '')
                intervals.append({'baslangic': a, 'bitis': z, 'ilce': target, 'dayanak': basis})
            rows.append({'id': 'mg:' + mid, 'ad': m['ad'], 'donemler': intervals})
        tablo[g] = {'bitis': '1992-06-03', 'mahalleler': rows}

    # 1987 oncesi Umraniye mahalleleri: once 1960 sayimi, sonra komsuluk
    atama = {}
    for (g, mid), ad in umraniye.items():
        if (g[-3:], ad) in SAYIM_1960:
            il, koy = SAYIM_1960[(g[-3:], ad)]
            atama[(g, mid)] = (il, f"Yaklaşık: {SAYIM60}: {koy}")
    bilinen = [(modern[f"TR-D-34-{k}"], il) for k, il in BUTUN_1961.items()]
    for g, t in tablo.items():
        for m in t['mahalleler']:
            k = (g, m['id'].removeprefix('mg:'))
            d = m['donemler'][0]
            il = atama[k][0] if k in atama else d['ilce']
            if il:
                bilinen.append((shape(mg[g][k[1]]['geometry']), il))
    bos = {k: shape(mg[k[0]][k[1]]['geometry']) for k in umraniye if k not in atama}
    for k, (il, pay) in komsuluk(mg, bos, bilinen).items():
        atama[k] = (il, f"Yaklaşık: 1960 sayımında adı yok; komşu sınırın %{round(pay * 100)} kadarı {il} "
                        "(1940/1963 ilçe haritalarıyla görsel olarak tutarlı)")
    for g, t in tablo.items():
        for m in t['mahalleler']:
            k = (g, m['id'].removeprefix('mg:'))
            if k in atama:
                d = m['donemler'][0]
                d['ilce'], d['dayanak'] = atama[k]
                d['yaklasik'] = True

    (IDARI / 'istanbul_1961_1992_mahalle.json').write_text(json.dumps({
        'not': __doc__, 'ilceler': tablo}, ensure_ascii=False, indent=1))
    (IDARI / 'ilce_bolusumu.json').write_text(json.dumps({
        'not': 'Genel çok kaynaklı bölüşüm henüz kaynaklanmadı. İstanbul kendi tablosundan üretilir.',
        'uygulananSecimler': ['1961referandum', '1961', '1965', '1969', '1973', '1977', '1982referandum', '1983', '1987referandum', '1987', '1988referandum', '1989yerel', '1991'], 'ilceler': {}}, ensure_ascii=False, indent=1))
    print("1987 öncesi Ümraniye mahalleleri:", len(umraniye), "→",
          {il: sum(1 for v in atama.values() if v[0] == il) for il in sorted({v[0] for v in atama.values()})})


if __name__ == '__main__':
    main()
