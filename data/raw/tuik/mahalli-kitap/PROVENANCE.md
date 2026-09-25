# DİE — Mahalli İdareler Seçimi Sonuçları (taranmış kitaplar)

| Dosya | Yayın | Sayfa | Tablolar |
|---|---|---|---|
| `0012953.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 25.3.1984* (yayın no. 1109) | 162 | 1 İGM (ilçe) s.10-35 · 2 Büyükşehir (bağlı ilçe) s.38-39 · 3 Belediye başkanlığı (belediye) s.42-93 · 4 Belediye meclisi (belediye) s.96-147 · 5 Muhtarlık (kullanılmadı) |
| `0013280.pdf` | DİE, *Mahalli İdareler Seçimi Sonuçları 26.3.1989* | 300 | 1 İGM il 1984/1989 (kullanılmadı) · 2 İGM il+ilçe+şehir/köy s.17-115 · 3 Büyükşehir s.118-119 · 4 Belediye başkanlığı s.122-209 · 5 Belediye meclisi s.212-299 |

**Kaynak:** TÜİK Kütüphanesi (yordam kataloğu), `https://kutuphane.tuik.gov.tr/pdf/<demirbaş>.pdf`.
**İndirilme tarihi:** 2026-09-25. Dosyalar değiştirilmeden saklandı (checksum'lı).

Kitabın açıklamasına göre ilçe/belediye düzeyi değerler ilçe seçim kurullarının
DİE'ye gönderdiği birleştirme tutanaklarından değiştirilmeden alınmış; Türkiye
toplamları Resmî Gazete'deki YSK ilanından (1984: 26.5.1984/18412).

## Okuma

PDF'lerde taramanın OCR metin katmanı var (tesseract gerekmedi). Her tablo iki
yüzlü: sol sayfa (ad, sandık, seçmen, oy kullanan, katılım %, geçerli oy, ilk
partiler), sağ sayfa (kalan partiler, etiketsiz). Okuyucu:
`scripts/pipelines/tuik_arsiv/extract_mahalli.py` → `data/kaynaklar/tuik/yerel/<seçim>/<tablo>.json`.

Bilinen tarama kusurları:
- 1989 Tablo 2'nin ilk yaprakları karışık sırada taranmış: s.20+s.17, s.18+s.21 (script'te sabit).
- 1989'da kalın puntolu satırlarda OCR her karakteri iki kez yazmış ('776655' = 765) — geri çevrildi.
- 1984 OCR'i zayıf: yüzdelerde ondalık noktası düşmüş ('4 1 3' = 41,3), '*' = 4, bazı tireler kayıp.
  Her satır parti toplamı = geçerli oy ve yüzde kısıtlarıyla doğrulanır; tutmayanlar `kontrol.durum = tutarsiz`.
- 1984 belediye başkanlığı tablosunda Şanlıurfa'nın il satırı taramada yok (il sınırı ikinci MERKEZ satırından çıkarıldı).
