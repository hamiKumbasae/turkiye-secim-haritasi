"""Mevcut kaynaklı 1992-2008 atamalarını 1987-1992 için geriye bağlar.

Yeni kaynak veya sınır tahmini üretmez. 3392/3644/3806/3949 zincirleri
build_istanbul_1961_1992.ZINCIR'dan alınır; daha eski mahalle bağlılığı
kanıtlanmamış alanlar açıkça belirsiz kalır. Yalnız 1989 yerel ve 1991
genel kayıtları etkinleştirilir. Diğer dönemler ayrıca doğrulanmalıdır.
"""
import json
from build_istanbul_1961_1992 import IDARI, ZINCIR, BASLANGIC
import build_istanbul_1992_2008 as b


def main():
    mg = json.loads(b.MAHALLE_GEO.read_text())
    kodlar = {a: k for a, k in b.ILCELER.items() if k}
    tablo = {}
    for kod in sorted((set(b.MAHALLE) | set(b.BUTUN)) - {'020'}):
        g = f'TR-D-34-{kod}'
        rows = []
        for mid, m in sorted(mg[g].items()):
            parent, source = b.MAHALLE[kod][m['ad']] if kod in b.MAHALLE else b.BUTUN[kod]
            intervals = []
            # İki kaynaklı Ümraniye'nin 1987 öncesi bağlılığı bu kanıttan çıkmaz.
            for a, z in [(BASLANGIC, '1987-07-04'), ('1987-07-04', '1990-05-20'),
                         ('1990-05-20', '1992-06-03')]:
                chain = ZINCIR.get(kodlar.get(parent), [])
                old = next((x for x in chain if x[0] <= a < x[1]), None)
                target = old[2] if old else parent
                basis = source + ('; önceki birim zinciri: ' + old[3] if old else '')
                if target == 'Ümraniye' and a < '1987-07-04':
                    target = None
                    basis = '1987 öncesi Üsküdar/Beykoz mahalle bölüşümü henüz kaynaklanmadı'
                intervals.append({'baslangic': a, 'bitis': z, 'ilce': target, 'dayanak': basis})
            rows.append({'id': 'mg:' + mid, 'ad': m['ad'], 'donemler': intervals})
        tablo[g] = {'bitis': '1992-06-03', 'mahalleler': rows}
    (IDARI / 'istanbul_1961_1992_mahalle.json').write_text(json.dumps({
        'not': __doc__, 'ilceler': tablo}, ensure_ascii=False, indent=1))
    (IDARI / 'ilce_bolusumu.json').write_text(json.dumps({
        'not': 'Genel çok kaynaklı bölüşüm henüz kaynaklanmadı. İstanbul kendi tablosundan üretilir.',
        'uygulananSecimler': ['1989yerel', '1991'], 'ilceler': {}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
