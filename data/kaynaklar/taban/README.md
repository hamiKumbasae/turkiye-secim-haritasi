# Taban: DİE birleştirmesinden önceki harita verisi (dondurulmuş)

`yerel/<seçim>.json` = `data/normalized/elections/yerel/<seçim>.json` dosyasının
DİE "Mahalli İdareler Seçimi Sonuçları" kitaplarıyla birleştirilmeden önceki
hâli (git `1e1e8e8`). İçerik:

- 1984yerel, 1989yerel: Türkçe Wikipedia il alt makaleleri (il + ilçe)
- 2004yerel: il satırları ve ilçelerin ~%76'sı YSK resmî arşivi (PDF), kalan
  ilçeler Wikipedia (aday adı olan satırlar)

`scripts/pipelines/tuik_arsiv/merge_mahalli.py` her çalıştığında bu tabandan
başlar; böylece harita verisindeki `kaynak.farklar[].eski` değerleri her zaman
gerçek önceki kaynağı gösterir (DİE'nin kendi değerini değil).
