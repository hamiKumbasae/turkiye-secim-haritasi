# Referandum Pipeline'ı (YSK)

`data/normalized/referandumlar.json`'daki 7 referandumun kaynağını YSK'nin
resmi halkoylaması arşivine yükselten script'lerin kaydı (bkz. `data/raw/
ysk/referandum/` ve `data/raw/ysk/referandum-2007-ilce/`).

## Script'ler

```
parse_ysk_referandum_pdfs.py         1961/1982/1987/1988'in tek-sayfalık
                                      il-bazlı PDF'lerini okur (sütun sırası
                                      yıldan yıla değişir, başlık adına göre)

verify_and_merge_old_referandum.py   Yukarıdakini mevcut (Wikipedia kaynaklı)
                                      verilerle karşılaştırır — DEĞER
                                      DEĞİŞTİRMEZ, sadece doğrular + eksik
                                      sandık/geçersizOy alanlarını ekler

parse_2007_ilce_pdfs.py              2007'nin 81 il × ilçe-bazlı imzalı
                                      "Birleştirme Tutanağı" PDF'lerini okur.
                                      Font kodlama sorununu (Ğ/İ/Ş kayboluyor)
                                      "iki tarafı da aynı şekilde arındır"
                                      yöntemiyle çözer (bkz. dosya içi not)

merge_2007_ilce.py                   Yukarıdakini referandumlar.json'daki
                                      2007referandum'un (önceden boş)
                                      'ilceler' listesine işler
```

## Sonuçlar

- **1961/1982/1987/1988**: 4 yıl × 67 il = 268 karşılaştırmanın TAMAMI
  önceki Wikipedia verisiyle birebir eşleşti — değer değişmedi, kaynak
  Wikipedia'dan doğrudan YSK PDF'ine yükseltildi.
- **2007**: 923 ilçe satırından 906'sı (%98,2) eşleşti — önceden "ilçe
  verisi yok" olan bu referandum artık tam ilçe-düzeyi haritaya sahip.
  Kalan 17 satır (10 büyükşehir "Merkez"i + 7 küçük ilçe) dürüstçe
  belgelendi, oyları ilgili ilin toplamında hâlâ mevcut.
- **2010/2017**: bu pipeline'a dahil değil — zaten Habertürk (il/ilçe) +
  YSK mahalle-düzeyi (bkz. `scripts/mahalle-veri-pipeline/`) kaynaklı.

## Türkçe karakter tuzakları (iki kez karşılaşıldı, ikisi de burada çözüldü)

1. Python'un varsayılan `.upper()`'ı Türkçe i/I ayrımını bilmiyor
   ("Siirt".upper() → "SIIRT", olması gereken "SİİRT" değil) — il/ilçe adı
   eşlemesi yapan her fonksiyonda elle `i→İ, ı→I` çevrimi gerekiyor.
2. Bazı eski YSK PDF'lerinin fontunda Ğ/İ/Ş karakterleri hiç render
   edilmiyor (metne boşluk veya hiçbir şey olarak çıkıyor) — çözüm, bu
   üç harfi (ve boşlukları) KARŞILAŞTIRILAN HER İKİ taraftan da silip
   öyle eşleştirmek.
