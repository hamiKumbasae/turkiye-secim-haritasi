# YSK — 1950-1977 Milletvekili Genel Seçimleri (il bazlı arşiv)

**Kaynak:** `https://www.ysk.gov.tr/tr/1950-1977-yillari-arasi-milletvekili-genel-secimleri/3007`
("Seçim Çevrelerine Göre Seçim Sonuçları" sekmesi). Sayfanın kendi notu:

> "1950-1977 Milletvekili Genel Seçimleri çalışması Türkiye İstatistik Kurumu
> verileri esas alınarak hazırlanmıştır."

Yani bu, **YSK'nin TÜİK verisine dayanarak hazırladığı resmi arşiv** —
projenin önceden aradığı "pre-2009 için TÜİK kaynağı" tam olarak bu.

**İndirilme tarihi:** 2026-09-22, `https://www.ysk.gov.tr/doc/dosyalar/docs/
Milletvekili/1950-1977/<İl>.pdf` deseninden 66 il + `Turkiye.pdf` (ulusal
özet, referans için, entegrasyonda kullanılmadı — il verilerinden türetilen
toplamlar zaten ulusal "Genel Bilgiler" sekmesiyle çapraz doğrulandı).

## Bilinen boşluk: Sakarya

**Sakarya bu arşivde YOK** — YSK'nin il seçim dropdown'ında 67 değil 66 il
listeleniyor, Sakarya hiç yer almıyor (muhtemelen YSK'nin kendi arşiv
hazırlama sürecindeki bir eksiklik, bizim tarafımızdan açıklanamıyor).
Sonuç: Sakarya'nın 1950-1977 verisi bu güncellemeden ETKİLENMEDİ, eski
(Wikipedia kaynaklı, vekil dağılımı olmayan) haliyle kaldı. Ulusal toplam
sandalye sayıları (`data/normalized/genel_secimler.json`'daki
`toplamSandalye`) YSK'nin resmi ulusal rakamı olarak girildi (Sakarya dahil,
gerçek); il bazlı vekil toplamı bu yüzden 1957/1961'de resmi rakamdan
Sakarya'nın sandalye sayısı kadar düşük çıkar — bu **tahmin değil, bilinen
bir kapsam sınırı** (bkz. `sources.yml`'deki known_issues).

## Yapısal not (2026-09-24'te düzeltildi)

1950-1977 Türkiye'sinde "seçim çevresi" il'in kendisiydi (il-genelinde
liste usulü). Önceden buradan "ilçe düzeyi veri hiç var olmadı" sonucu
çıkarılmıştı — **bu yanlış**: oylar ilçe seçim kurullarında sayılıp
birleştirildiği için DİE sonuçları il ve ilçe bazında yayımladı. 1961-1977
(ve 1983/1987) ilçe verisi TÜİK'ten eklendi, bkz.
`data/raw/tuik/secimdagitimapp-ilce-1961-1987/PROVENANCE.md`. Bu arşivde
eksik olan Sakarya da TÜİK'in kaynağında mevcut (il satırı henüz
güncellenmedi). 1950/1954/1957 için resmî ilçe kaynağı bulunamadı.

## Dosyalar

- `<İl>.pdf` (66 dosya) — YSK'nin kendi dosya adlandırması (ASCII, bazıları
  küçük harfle: `istanbul.pdf`, `izmir.pdf`, `isparta.pdf`, `icel.pdf`).
  `il_dosya_adi_eslemesi.txt`, dosya adını gerçek il etiketine çevirir.
- `Turkiye.pdf` — ulusal özet (referans, entegre edilmedi).
- `il_dosya_adi_eslemesi.txt` — `Etiket|dosyaadi.pdf` formatında eşleme.

## Nasıl işlendi

`scripts/pipelines/genel_1950_1977/` — `parse_ysk_pdfs.py` (pdfplumber ile
tablo hücrelerini konumuna göre okur, bazı PDF'lerdeki font/render
kaynaklı karakter ikizlenmesini düzeltir) + `merge_into_normalized.py`
(`data/normalized/genel_secimler.json`'a işler, parti eşlemesi yapar,
her il/yıl için vekil toplamının YSK'nin belirttiği milletvekili sayısıyla
tam eşleştiğini doğrular — eşleşmezse build durur). Ayrıntı için o
klasörün README.md'sine bakın.

## Bütünlük

`checksums.sha256` — 2026-09-22 itibarıyla.
