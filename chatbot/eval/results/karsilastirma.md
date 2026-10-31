# Karşılaştırma: şablon, yerel modeller, Claude

`python eval/run_eval.py` her çalıştırmada bu dosyayı yeniden üretir (kaynak: `karsilastirma.json`, her küme/çalıştırma için en son sonuç). Yalnız gerçekten çalıştırılmış ölçümler burada görünür.

* **Doğruluk**: execution accuracy, tüm sorular (veri-yok soruları ret ile doğru sayılır).
* **Yanıtlanabilir**: veri olan sorularda doğruluk. **Ret**: veri-yok sorularında doğru ret.
  Şablon modunda şablona uymayan her soru reddedilir; bu yüzden oradaki ret sütunu tek başına bir başarı değildir.
* **Yanlış ret**: verisi olan bir sorunun reddedilmesi.
* **Şablon payı**: şablon katmanının yanıtladığı (ya da kuralla reddettiği) soruların payı; parantezde şablonun yanıtladıklarındaki doğruluk.
* **p50 / p95**: soru başına uçtan uca süre (SQL + veritabanı + yanıt metni). Maliyet yalnız Claude için, `--price-in/--price-out` ile tahmin.

## Soru bankası — test bölümü (n = 216)

| Çalıştırma | Doğruluk | Yanıtlanabilir | Ret (veri-yok) | Yanlış ret | Şablon payı | p50 | p95 | Token (girdi / çıktı) | Maliyet | Tarih |
|---|---|---|---|---|---|---|---|---|---|---|
| `template` | **%55,1** (119/216) | %47,0 | %100,0 | 88 | %50,0 (%91,7) | 7 ms | 20 ms | — | — | 2026-10-31 |

Kategori bazında (doğru / n):

| Kategori | `template` |
|---|---|
| bolge | 0/6 |
| capraz | 0/6 |
| cumhurbaskanligi | 10/12 |
| degisim | 4/12 |
| fark | 4/8 |
| il | 12/17 |
| ilce | 10/18 |
| katilim | 8/10 |
| mahalle | 5/11 |
| referandum | 5/9 |
| rekor-siralama | 0/7 |
| takip-belirsiz | 3/10 |
| turlar-arasi | 0/6 |
| ulusal-toplam | 8/14 |
| vekil | 5/14 |
| veri-yok | 32/32 |
| yerel | 7/14 |
| zaman-serisi | 6/10 |

## Orijinal 32 soruluk gold seti (n = 32)

| Çalıştırma | Doğruluk | Yanıtlanabilir | Ret (veri-yok) | Yanlış ret | Şablon payı | p50 | p95 | Token (girdi / çıktı) | Maliyet | Tarih |
|---|---|---|---|---|---|---|---|---|---|---|
| `template` | **%81,2** (26/32) | %81,2 | — | 6 | %81,2 (%100,0) | 14 ms | 24 ms | — | — | 2026-10-31 |

Kategori bazında (doğru / n):

| Kategori | `template` |
|---|---|
| cumhurbaskanligi | 5/5 |
| il | 2/2 |
| ilce | 3/4 |
| katilim | 2/3 |
| mahalle | 2/3 |
| referandum | 3/3 |
| ulusal-toplam | 2/3 |
| vekil | 4/4 |
| yerel | 1/2 |
| zaman-serisi | 2/3 |
