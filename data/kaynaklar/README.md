# Kaynak katmanı: her kaynak, her seçim, ayrı dosya

Bu klasör, seçimlerin kendisini (haritanın kullandığı birleşik veri) veri
kaynaklarından **ayrı** tutar. Her dosya **tek bir kaynağın tek bir seçim için
verdiği her şeydir**: birleştirilmemiş, düzeltilmemiş, kaynaktaki adlar ve
kısaltmalar olduğu gibi, yanında eşlenen parti anahtarı.

```
data/raw/<kaynak>/...                 ham indirilen dosyalar (HTML, wikitext, PDF)
data/kaynaklar/<kaynak>/<tür>/<seçim>.json   ayrıştırılmış, kaynak başına   <- bu klasör
data/normalized/elections/<tür>/<seçim>.json birleşik veri (harita bunu okur)
data/normalized/ek/<tür>/<seçim>.json        projede başka karşılığı olmayan ek kayıtlar
```

| Kaynak | Klasör | Seçimler | Ham veri |
|---|---|---|---|
| TÜİK (resmî) | `tuik/genel/` | 1961-2007 genel, il + ilçe (+ 1991'den itibaren şehir/köy kırılımı) | `data/raw/tuik/` |
| Wikipedia (ikincil) | `wikipedia/{genel,yerel,senato,cumhurbaskanligi}/` | 1923-2024, il sayfaları | `data/raw/wikipedia/il-sayfalari/` |
| mertnuhoglu (ikincil) | `mertnuhoglu/genel/` | 1991-2007 ilçe, TÜİK'ten önceki hâli (dondurulmuş) | `data/raw/third-party/mertnuhoglu/` |

## Birleşik veride köken

Birden fazla kaynaktan beslenen satırlarda `kaynak` alanı vardır:

```json
"kaynak": {"ana": "mertnuhoglu",
           "farklar": [{"alan": "oy.YENP95", "kaynak": "tuik", "eski": null, "yeni": 487}],
           "tuikHam": "data/raw/tuik/secimdagitimapp-ilce-1991-2023/1995/01-adana.html"}
"kaynak": {"ana": "mertnuhoglu", "teyit": ["tuik"], ...}     // tüm değerler birebir aynı
"kaynak": {"ana": "wikipedia", "sayfa": "...", "revid": 37769080, ...}
```

`kaynak` alanı olmayan satırlar, seçimin `sources.yml`'deki kaynağından gelir
(il: `primary`, ilçe: `ilce_source` / `ilce_base` / `primary`).

TÜİK'e özgü şehir/köy kırılımı 1991-2007 ilçe ve il satırlarında `sehirKoy`
alanında durur (kaynağı her zaman `tuik`).

## Sorgu

```bash
.venv/bin/python scripts/kaynak.py --liste                # her seçim, il/ilçe kaynağı
.venv/bin/python scripts/kaynak.py 1995 İstanbul Fatih    # tek ilçe, alan alan köken
.venv/bin/python scripts/kaynak.py 1961senato             # ek kayıt
```

## Yeniden üretmek

```bash
python3 scripts/pipelines/wikipedia_arsiv/extract_yerel.py
python3 scripts/pipelines/wikipedia_arsiv/extract_genel_senato.py
python3 scripts/pipelines/tuik_arsiv/extract_tuik_ilce.py
```
