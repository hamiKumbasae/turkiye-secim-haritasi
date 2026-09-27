# YSK — 1984 ve 1989 mahalli idareler kesin sonuçları (il düzeyi)

`ysk.gov.tr/doc/dosyalar/docs/Mahalli/<yıl>/KesinSecimSonuclari/<yıl>-<Tür>-Secimleri-Sonucu.pdf`
— il genel meclisi üyeliği, belediye meclis üyeliği, belediye başkanlığı, büyükşehir belediye
başkanlığı; 2'şer sayfa, **il toplamları** (ilçe kırılımı yok). İndirilme: 2026-09-27, değiştirilmedi.

Kullanım: `scripts/pipelines/ysk_kesin/parse_mahalli_kesin.py` (metin katmanı, tahmin yok) →
`data/kaynaklar/ysk/mahalli-kesin/`. Haritadaki yerel meclis sekmelerinin **il** satırları, DİE
kitabının taranmış il satırı okunamadığında ya da doğrulanamadığında buradan gelir
(`scripts/pipelines/meclis_harita/build_meclis_harita.py`).

Kaynağın kendi hataları (değiştirilmedi): 1984 Çanakkale İGM'de oy kullanan seçmenden büyük
(807.475 > 217.865); 1984 belediye meclisi tablosunda illerin çoğunda parti oyları toplamı geçerli
oydan birkaç oy farklı — bu satırlar kullanılmaz. 1989 belediye meclisi başlığı SHP yerine 'SODEP'
yazıyor (oylar DİE'nin SHP sütunuyla 62 ilde birebir).

2004 için aynı dizinde dosya bulunamadı; 1994/1999 dosyaları `../mahalli-kesin-1994-1999/`.
