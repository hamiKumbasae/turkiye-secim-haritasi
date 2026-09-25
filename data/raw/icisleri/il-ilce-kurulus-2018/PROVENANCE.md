# İçişleri Bakanlığı — İl ve İlçe Kuruluş Tarihleri 2018

| Dosya | Yayın | Sayfa |
|---|---|---|
| `il_ve_ilce_kurulus_tarihleri_2018.pdf` | T.C. İçişleri Bakanlığı İller İdaresi Genel Müdürlüğü, İl Genel İdaresi Daire Başkanlığı, İl İdaresi ve Mülki Bölümler Şubesi — *İl ve İlçe Kuruluş Tarihleri 2018* | 86 |

**Kaynak:** https://www.icisleri.gov.tr/kurumlar/icisleri.gov.tr/IcSite/illeridaresi/Bilgiler2/%C4%B0l%20ve%20%C4%B0l%C3%A7e%20Kurulu%C5%9F%20Tarihleri%202018.pdf
**İndirilme tarihi:** 2026-09-25. Dosya değiştirilmeden saklandı (checksum'lı).
**Güvenilirlik:** A (birincil/resmî).

## İçerik

Her il için: il satırı ve ilçeleri (alfabetik), her biri için kuruluş tarihi,
kanun numarası (KHK ise "NNN sayılı Kanun Hükmünde Kararname"), Resmî Gazete tarihi
ve sayısı; 1923 öncesi birimler için "Cumhuriyet öncesi". Metin katmanı dijital
(OCR değil).

Okuyucu: `scripts/pipelines/historical_geo/extract_icisleri_kurulus.py` →
`data/kaynaklar/icisleri/il_ilce_kurulus_2018.json` (81 il, 922 ilçe; merkez
ilçeler il satırıyla).

## Sınırlar

- Yalnızca 2018'de mevcut birimler, **güncel ad ve güncel ile göre**. Kaldırılan
  ilçeler, eski adlar ve il değişiklikleri yok.
- Yeniden kurulan illerde yalnızca son kuruluş var (Kırşehir: 12.06.1957, 7001;
  1954'te kaldırılmıştı).
- Sonradan il olan yerlerde il satırı ilin kuruluşudur, merkez ilçenin değil.
- Kuruluş tarihi, ilçenin seçime ayrı birim olarak girdiği tarih değildir
  (bkz. `geo/historical/idari/README.md`).
- 2018 sonrası ad değişikliği: Eyüp → Eyüpsultan (okuyucuda eşlendi).
