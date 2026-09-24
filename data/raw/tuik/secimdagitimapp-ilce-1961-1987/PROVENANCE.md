# TÜİK — 1961-1987 Milletvekili Genel Seçimleri, il ve ilçe sonuçları

**Kaynak:** TÜİK Seçim Dağıtım uygulaması,
`https://biruni.tuik.gov.tr/secimdagitimapp/secim.zul` → "Seçim çevresi ve
ilçelere göre milletvekili genel seçimi sonuçları" tablosu (yıl listesi
1961-2023; **1950/1954/1957 yok**). Her rapor tek bir ilin tüm ilçelerini
verir: kayıtlı seçmen, oy kullanan, geçerli oy, her parti/bağımsız için oy
(1983 ve 1987'de ayrıca sandık sayısı). Uygulama raporu
`rapory.tuik.gov.tr/<zaman-damgası>.html` olarak üretir (cp1254 HTML).

**İndirilme tarihi:** 2026-09-24. 7 seçim × 67 il = 469 dosya,
`scripts/pipelines/genel_ilce_1961_1987/fetch_tuik_ilce.py` ile (aynı
script'le yeniden üretilebilir; mevcut dosyaları atlar).

## Dosyalar

`<yıl>/<NN>-<il>.html` — `NN` TÜİK listesindeki sıra; 1961-1987'deki 67 ilin
plaka numarasıyla birebir aynı (01 Adana … 67 Zonguldak). İl adları TÜİK'in
yazımıyla (`afyon`, `icel`, `kmaras` = 1983/87'de "K,Maraş").

## Birincil basılı karşılığı (çapraz doğrulama)

Uygulamadaki rakamlar DİE'nin basılı yayınlarıyla aynı; örneklem kontrolleri
birebir tuttu (Adana 1977 ilçeleri, Adıyaman 1961-1977, Seyhan/Ceyhan vb.).
Bu PDF'ler boyutları nedeniyle depoya konmadı, pinlendi:

| Yayın | URL | Boyut | sha256 |
|---|---|---|---|
| DİE, *Milletvekili Genel Seçimi Sonuçları (İl ve İlçe Sonuçları) 1961-1965-1969-1973-1977* | https://kutuphane.tuik.gov.tr/pdf/0014128.pdf | 10 799 904 | `0d122d886214238edfb5e51029859ea1cba4a543a984a850d3c415dbcf00ffe8` |
| DİE, *Milletvekili Genel Seçimi Sonuçları (İl ve İlçe Sonuçları) 1983-1987-1991-1995* | https://kutuphane.tuik.gov.tr/pdf/0014049.pdf | 20 326 714 | `a38f96c0980bbf25d3eeec952e15111090346a9ae14695466957381ae30ce833` |
| DİE Yayın No. 513, *1950-1965 Milletvekili ve 1961, 1964 Cumhuriyet Senatosu Üye Seçimleri Sonuçları* (1965 için il/ilçe/sandık; 1950-1965 il) | https://kutuphane.tuik.gov.tr/pdf/0015202.pdf | 95 041 533 | `37add4d2469ac1cd81b08534ef90805af6a6985eda2abd4199bb0541732e1cec` |
| TÜİK Yayın No. 3685, *Milletvekili Genel Seçimleri 1923-2011* (Tablo 23: 1950-1977 il sonuçları; kaynakçası DİE yayın numaralarını listeler) | https://www.ysk.gov.tr/doc/dosyalar/1923-2011-MVSecimleri-Tuik.pdf | 4 525 020 | `695d769c6c9a5e984810ea32adc663deabbd642f4c52b5d94eeea44550fbb90d` |

Diğer ilgili DİE yayınları (indirilmedi): `0015147` (1961 il/ilçe/sandık
bölgesi), `0015118` (1961 il ve ilçe), `0015301` (1969), `0015450` (1973),
`0015631` (1977), `0013195` (1987 ilçe), `0013722` (1995 ilçe).

## Bilinen özellikler (hata değil)

- **İlçe toplamı ≠ il toplamı.** DİE 1965 yayınının açıklaması: il toplamları
  YSK'nin Resmî Gazete ilanından, ilçe rakamları ilçe seçim kurullarının
  birleştirme tutanaklarından; itiraz süresinde düzeltilmeyen toplama
  hataları olduğu gibi yayımlanmış. 428 il×yıl×alan kaydında fark var,
  çoğu ±%1'in altında. 1987 il toplamlarına gümrük kapısı oyları da dahil.
- Parti oylarının toplamı bazı ilçelerde geçerli oydan birkaç oy farklı
  (kaynağın kendisi, 587 satır, büyük çoğunluğu ±100 oy).
- **İl düzeyi seçmen sayısı şüpheli olan iki kayıt:** 1973 Ankara (resmî il
  seçmeni 786 398 → katılım %85,7; ilçelerin toplamı 985 132 → %68,4) ve 1973
  Kastamonu (285 894 → %49,8; ilçe toplamı 222 934 → %63,9). İlçe satırları
  kendi içinde tutarlı; muhtemelen il düzeyindeki resmî rakamda hata var.
  Proje il satırlarına dokunmadı, `sources.yml`'de kayıtlı.

## Nasıl işlendi

`scripts/pipelines/genel_ilce_1961_1987/` (bkz. README). İl satırlarının
değerleri değiştirilmedi; sadece `ilceler` listesi ve `ilceSayisi` yazıldı.

## Bütünlük

`checksums.sha256` — 2026-09-24 itibarıyla.
