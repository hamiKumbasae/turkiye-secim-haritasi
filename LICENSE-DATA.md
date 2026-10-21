# Veri lisansı

Bu depodaki **kaynak kodu** MIT lisanslıdır (bkz. [LICENSE](LICENSE)). **Veri** ayrı lisanslıdır:

| Ne | Lisans |
|---|---|
| İşlenmiş seçim sonuçları ve tarihsel sınır çalışmaları (`data/normalized/`, `geo/historical/`, `geo/normalized/` ve `index.html`'e gömülü veri) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.tr) |
| OpenStreetMap'ten türetilen mahalle sınırları (`geo/normalized/mahalle_geo.json` içindeki OSM kaynaklı poligonlar) | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) — © OpenStreetMap katkıcıları |
| Bursa ve Sakarya büyükşehir belediyelerinin açık veri portallarından alınan mahalle sınırları (`data/raw/belediye/`, haritada `b` ile başlayan poligonlar) | Bursa Açık Veri Lisansı, Sakarya Açık Veri Lisansı — kullanım, değiştirme ve yeniden yayımlama serbest, kaynak gösterilmesi şartıyla |
| TKGM idari yapı servisinden alınan mahalle/köy sınırları (`data/raw/tkgm/` ve `geo/normalized/mahalle_geo.json` içindeki `k` ile başlayan poligonlar) | **Bu deponun açık veri lisansının dışındadır.** Kaynak: T.C. Tapu ve Kadastro Genel Müdürlüğü (TKGM); servisin yayımlanmış bir açık veri lisansı yoktur, sitede kaynak gösterilerek kullanılır. Yeniden kullanım için TKGM'nin koşullarına bakın. |

## Neden CC BY-SA 4.0

Sonuçların bir kısmı Vikipedi tablolarından derlendi (ör. 1950–1977 yerel seçimleri). Vikipedi içeriği
CC BY-SA lisanslıdır; bu yüzden derlenmiş veri de aynı lisansla, atıf ve aynı lisansla paylaşma
koşuluyla yayımlanır. Mahalle sınırlarının bir kısmı OpenStreetMap'ten gelir ve ODbL'ye tabidir.

## Nasıl atıf yapılır

> Türkiye Seçim Tarihi Atlası (https://hamikumbasae.github.io/turkiye-secim-haritasi/), CC BY-SA 4.0. Asıl kaynaklar: YSK, TÜİK.
> Mahalle sınırları: © OpenStreetMap katkıcıları (ODbL); bir kısmı T.C. Tapu ve Kadastro Genel Müdürlüğü (TKGM), Bursa ve Sakarya büyükşehir belediyeleri.

Veriyi değiştirip yayımlarsanız aynı lisansla (CC BY-SA 4.0; OSM'den türeyen sınırlar için ODbL)
paylaşmanız gerekir.

## Asıl kaynakların koşulları

Resmî seçim sonuçları kamuya açık kaynaklardan derlenmiştir (YSK, TÜİK, TBMM). Bu lisans yalnız bu
depodaki derleme, düzeltme ve dönüştürme çalışmasını kapsar; asıl kaynakların kendi koşulları
(ör. il/ilçe sınırlarının alındığı `ttezer/turkiye-harita-verisi`, belediye açık verisi) ayrıca
geçerlidir. Ayrıntılı kaynak listesi: [SOURCES.md](SOURCES.md), [sources.yml](sources.yml).
