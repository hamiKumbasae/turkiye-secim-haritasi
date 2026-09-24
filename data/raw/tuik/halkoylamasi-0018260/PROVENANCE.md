# TÜİK — Halk Oylaması Sonuçları 2007, 1988, 1987, 1982, 1961

**Yayın:** TÜİK, *Halk Oylaması Sonuçları 2007, 1988, 1987, 1982, 1961*, Ankara 2008
(katalog demirbaş 0018260). **Kaynak URL:** https://kutuphane.tuik.gov.tr/pdf/0018260.pdf
**İndirilme:** 2026-09-24. 249 sayfa, dijital metin katmanlı (tarama değil).

## İçerik

Tablo 1: il sonuçları (5 halkoylaması). Tablo 2-6: **il ve ilçelere göre**
sonuç (2007, 1988, 1987, 1982, 1961). Her il ve ilçe için şehir ve bucak/köy
kırılımıyla birlikte sandık, kayıtlı seçmen, oy kullanan, katılım, geçersiz,
geçerli, Evet ve Hayır oyları.

## Metin katmanının kusurları (ayrıştırmada telafi edildi)

- Türkçe harfler glif koduyla çıkıyor: `(cid:248)`=İ, `(cid:249)`=Ş, `(cid:250)`=ş, `(cid:247)`=ğ.
- **"ı" harfi tamamen düşmüş** ("Fındıklı" → "Fndkl"). İlçe adları birleştirmede
  aynı dönemin TÜİK genel seçim ilçe adlarından düzeltildi; kaynak yazımı satırın
  `kaynak.adKaynakta` alanında duruyor.
- Binlik ayırıcı boşluk olduğu için bitişik sayılar, yayının kendi katılım oranına
  uyan tek bölünmeyle ayrıldı (`scripts/pipelines/tuik_arsiv/extract_halkoylamasi.py`).

## Doğrulama

1961, 1982, 1987, 1988: 67/67 il; TÜİK il toplamları (seçmen, geçerli, Evet)
projedeki YSK il satırlarıyla **birebir aynı**. İlçe sayıları: 636 / 640 / 645 / 674
(+ 1987 ve 1988'de "Gümrük Kapıları" satırı; ilçe değil, birleşik veriye alınmadı).

Kaynağın kendi tutarsızlıkları (düzeltilmedi): bazı illerde ilçe toplamı il
toplamını tutmuyor; birkaç ilçe satırında geçersiz+geçerli ≠ oy kullanan ya da
Evet+Hayır ≠ geçerli (satırın `kaynak.kaynakIciTutarsizlik` alanında).

## Nasıl kullanıldı

- Kaynak katmanı: `data/kaynaklar/tuik/referandum/<seçim>.json` (2007 dahil)
- Birleşik veri: 1961/1982/1987/1988 referandumlarının ilçe satırları
  (`scripts/pipelines/tuik_arsiv/merge_halkoylamasi_ilce.py`). 2007'ye dokunulmadı
  (ilçe düzeyi zaten YSK'den).
