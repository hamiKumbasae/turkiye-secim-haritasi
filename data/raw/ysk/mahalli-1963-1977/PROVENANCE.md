# YSK — 1963/1968/1973/1977 mahalli idareler, ULUSAL toplam (il kırılımı YOK)

`ysk.gov.tr/tr/mahalli-idareler-genel-secimleri-arsivi/2650` arşiv sayfasının
(Angular SPA — Playwright ile render edilip linkler çıkarıldı) her yıl için
verdiği 2 PDF'ten "Belediye Başkanlığı Seçimleri Sonucu" olanı indirildi
(`İl Genel Meclisi Üyeliği Seçimleri Sonucu` de vardı — ilgisiz, indirilmedi):

```
https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/<yıl>/KesinSecimSonuclari/<yıl>_Belediye_Baskanligi_Secimleri_Sonucu.pdf
```

**ÖNEMLİ — bu PDF'ler İL BAZLI DEĞİL, sadece TÜRKİYE GENELİ 1 sayfalık özet**
(kayıtlı seçmen, oy kullanan, geçerli oy, seçilen başkanlık sayısı + parti
başına ULUSAL oy/sandalye toplamı). `data/normalized/yerel_secimler.json`'a
işlenen 1963yerel/1968yerel/1973yerel/1977yerel verisi bu PDF'lerden DEĞİL,
Wikipedia'nın il-bazlı alt makalelerinden geliyor (bkz.
`data/raw/wikipedia/yerel-1950-1977/PROVENANCE.md`) — bu PDF'ler sadece
**çapraz doğrulama** amaçlı: 1977 PDF'indeki ulusal toplamlar (12.067.618
kayıtlı seçmen, 1.710 belediye başkanlığı vb.), Wikipedia'nın aynı yıl için
verdiği ulusal toplamla birebir örtüştü (bkz. `wiki_1977.wikitext`'in
kendi kaynakçası zaten aynı bu PDF'e atıf yapıyor).

Dosyalar: `<yıl>_belediye.pdf` (kullanılan), `<yıl>_ilgenel.pdf` (il genel
meclisi üyeliği sonucu — bu depoda henüz kullanılmadı, ileride ihtiyaç
olursa diye saklandı).

1950 ve 1955 için bu arşivde HİÇBİR PDF yok (YSK'nin arşiv sayfası 1963'ten
başlıyor) — doğrulandı, bkz. `SECIM_TAKVIMI.md`.
