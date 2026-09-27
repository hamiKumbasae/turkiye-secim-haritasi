# 1950-1977 Genel Seçim Pipeline'ı (YSK/TÜİK)

`data/normalized/genel_secimler.json`'daki 1950,1954,1957,1961,1965,1969,
1973,1977 yıllarının il kayıtlarını (katılım, seçmen, geçerli oy, il bazında
milletvekili dağılımı) YSK'nin resmi, TÜİK kaynaklı arşiviyle güncelleyen
tek seferlik script'lerin kaydı (bkz. `data/raw/ysk/1950-1977/PROVENANCE.md`).

En büyük etkisi: **1950/1954/1957/1961'de önceden hiç olmayan
milletvekili (vekil) dağılımı** artık var — önceden bu 4 yıl için sadece
"kazanan parti + oy oranı" gösteriliyordu.

## Script'ler

```
parse_ysk_pdfs.py          data/raw/ysk/1950-1977/*.pdf'leri pdfplumber ile
                            yapısal JSON'a çevirir (hücre konumuna göre okur,
                            bazı PDF'lerdeki karakter ikizlenmesi hatasını düzeltir)

merge_into_normalized.py   Çıkan JSON'u data/normalized/genel_secimler.json'a
                            işler — parti eşlemesi yapar, her il/yıl için
                            vekil toplamının YSK'nin verdiği milletvekili
                            sayısıyla TAM eşleştiğini doğrular (eşleşmezse
                            hiçbir şey yazmadan durur), partiler.json'a yeni
                            parti renkleri ekler.

ysk_national_totals.json   YSK'nin "Türkiye Geneli" (ulusal özet — il-bazlı
                            PDF'lerden AYRI bir sayfa) rakamları + (sadece
                            1950 için) TBMM'nin seçim veritabanı rakamları.

verify_national_totals.py  data/normalized/genel_secimler.json'daki il
                            kayıtlarını toplayıp ysk_national_totals.json'daki
                            iki bağımsız kaynakla karşılaştırır (SADECE ulusal
                            toplam düzeyinde — il/ilçe zinciri henüz yok).
                            Farkları ÇÖZMEYE çalışmaz, sadece ölçüp raporlar.
```

## Çoklu kaynak doğrulaması (verify_national_totals.py)

`python3 verify_national_totals.py` çalıştırıldığında 8 yılın her biri için
il-bazlı toplamımızı YSK'nin kendi ulusal özet sayfasıyla (ve 1950 için
ayrıca TBMM'nin veritabanıyla) karşılaştırır. 1965/1969/1977 için toplamlar
neredeyse birebir örtüşüyor (%0-0,5 fark); 1950/1954/1957'de %1-1,7 fark var.

**En dikkat çekici bulgu:** 1950'de bizim il-bazlı toplamımız, YSK'nin
KENDİ ulusal özetinden çok TBMM'nin veritabanına yakın çıkıyor (DP/CHP/
Millet Partisi için %0,01-0,27 fark, YSK özetiyle %0,88-3,16 fark) — yani
YSK'nin kendi sitesindeki iki farklı sayfa (il-bazlı tablolar vs. ulusal
özet) bile birbiriyle tam tutarlı değil. Bu, `sources.yml`'de `1950` altında
`discrepancies` olarak kaydedildi, çözülmedi.

**Kapsam dışı (bilinçli, onay bekliyor):** Diğer 19 genel seçim yılı (1983-
2023) için TBMM/TÜİK ile aynı derinlikte çapraz doğrulama henüz yapılmadı.
İl/ilçe seviyesinde aşağıdan-yukarı matematiksel zincir doğrulaması
(mahalle→ilçe→il→Türkiye) da henüz yok.

## Yeniden çalıştırmak için

```bash
python3 parse_ysk_pdfs.py ../../data/raw/ysk/1950-1977 /tmp/parsed.json
python3 merge_into_normalized.py /tmp/parsed.json ../../data/raw/ysk/1950-1977/il_dosya_adi_eslemesi.txt
```

Ardından kök dizinde `python3 scripts/build.py` ile `index.html`'i yeniden
üretin ve `data/normalized/checksums.sha256` + `data/provenance/checksums.json`'ı
güncelleyin (checksum'lar veri her değiştiğinde yeniden hesaplanmalı).

## Bilinen sınırlar

- **Sakarya bu arşivde yok** (YSK'nin kendi dropdown'ında 67 değil 66 il —
  açıklanamayan bir eksiklik onların tarafında). Sakarya'nın verisi
  dokunulmadı, eski haliyle kaldı.
- **1957 ve 1961'de il bazlı vekil toplamı, resmi ulusal rakamdan biraz
  düşük** — tam olarak Sakarya'nın o yıllardaki sandalye sayısı kadar
  (bilinen, belgelenmiş fark; `toplamSandalye` alanı yine de doğru resmi
  ulusal rakamı taşıyor).
- Bu dönemde "seçim çevresi" = il'in kendisi (ilçe bazlı tekil-üyeli sistem
  yoktu) — yani ilçe düzeyi veri hiçbir zaman var olmadı, bu bir kaynak
  eksikliği değil.
- Parti eşlemesi (`STATIC_MAP` içinde) elle kuruldu; yeni/beklenmeyen bir
  parti kodu çıkarsa script `KeyError` ile durur (sessizce yanlış eşleme
  yapmaz).

## Doğrulama

Ankara ve Siirt için manuel olarak PDF'ler okunup mevcut (o zamanki)
projenin 1965-1977 verisiyle karşılaştırıldı — toplam sandalye sayıları
birebir örtüştü. `merge_into_normalized.py`'nin dahili bütünlük kontrolü
(vekil toplamı == YSK milletvekili sayısı) 66 il × 8 yıl için hatasız
geçti. Playwright ile tarayıcıda 1950/1961/1965 sekmeleri, Ankara detay
paneli ve tablo görünümü test edildi.

## İl kazananı: 1950, 1954, 1957 (2026-09-27)

Bu yıllarda çoğunluk usulü uygulandı ve il tek seçim çevresiydi. YSK tablolarındaki parti
"oy sayısı" karşılaştırılabilir değil: bağımsızların oyu birden çok adayın toplamı, ve bazı
illerde oy sayısı ile oy oranı çelişiyor (1950 Mardin: Bağımsızlar 47.771 oy ama %7,6;
DP 45.078 oy %42,8; CHP 44.882 oy %49,7). Bu yüzden il kazananı **en çok vekil kazanan
parti, eşitlikte resmî oy oranı yüksek olan**dır (`COGUNLUK_YILLARI`); ön yüz ayrıntı paneli
de bu yıllarda partileri aynı sırayla dizer. Değişen iller: 1950 Mardin (Bağımsız → CHP;
vekil CHP 3, DP 3, Bağımsız 1) ve Ordu (DP → CHP; vekil CHP 6, DP 2, oran %50–%50).
Kaynaktaki oy ve oran değerleri değiştirilmedi.
