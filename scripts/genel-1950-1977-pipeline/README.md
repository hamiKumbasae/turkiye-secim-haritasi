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
```

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
