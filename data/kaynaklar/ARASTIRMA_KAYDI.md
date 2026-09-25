# Kaynak araştırma kaydı

Nerelere bakıldığının kalıcı kaydı: bulunan **ve bulunamayan** kaynaklar.
Amaç aynı kaynağa haftalar sonra yeniden dönmemek. Bu dosyada rakam yok;
yalnız künye, kapsam ve sonuç var. Görev tanımı: `YAPILACAKLAR.md`.

Güvenilirlik: **A** birincil/resmî · **B** güçlü ikincil (akademik, dönemin
ulusal gazetesi, yayımlanmış kitap) · **C** destekleyici ikincil (yerel tarih,
belediye yayını) · **D** zayıf/keşif (Wikipedia, blog, kullanıcı tablosu).

Tekrar bakılmalı mı: **Hayır** = kapandı · **Elle** = otomatik erişim yok,
bakıp bakmamak kullanıcının kararı · **Evet** = açık iz.

---

## Genel seçimler — KAPANDI (2026-09-25)

| Yıl | İl | İlçe | Durum |
|---|---|---|---|
| 1950, 1954, 1957 | var (YSK) | **yok** | Ulusal ilçe kaynağı bulunamadı; il düzeyinde kalıyor (kullanıcı kararı) |
| 1961–1983 | var | var (TÜİK) | Tam; Ankara "Merkez" haritada çizilmiyor (tarihsel sınırı yok) |
| 1987–2002 | var | var | Tam |

**1961–2002 ilçe denetimi (2026-09-25):** Her ilin ilçe satırları mevcut,
`ilceSayisi` alanı satır sayısıyla birebir, tüm alanlar dolu, gömülü
`index.html` normalize veriyle aynı. Parti oyları toplamının geçerli oydan
farklı olduğu satırlar (1961: 169, 1973: 155, 1977: 91, diğer yıllar ≤27)
basılı DİE kitaplarında da aynı; en büyük farklar sayfa görüntüsüyle
doğrulandı: 1961 Ağlasun (0014128 s. 76–77), 1983 Çardak (0014049 s. 96,
ANAP hücresi boş), 1995 Bozüyük, 1995 Marmaris (katılım basılıda %100,1).
Kaynak hatası; tahminle doldurulmadı. Bkz.
`data/raw/tuik/secimdagitimapp-ilce-1961-1987/PROVENANCE.md`.

## Kaynak günlüğü

| ID | Kaynak | Tür | Güv. | Yıllar | Kontrol edilen | Sonuç | Tekrar? |
|---|---|---|---|---|---|---|---|
| PRIMARY-001 | YSK 1950–1977 arşivi (ysk.gov.tr/…/3007) ve `1950MilletvekiliSecimi/1950_Secim_Sonuclari.pdf` | Resmî | A | 1950–1977 | İlçe sonuçları | Yalnız il; repoda (`data/raw/ysk/1950-1977/`, `1950-tbmm-crosscheck/`) | Hayır |
| PRIMARY-002 | TBMM seçim sorgu | Resmî | A | 1950–1957 | İlçe sonuçları | Yalnız il (seçim çevresi) | Hayır |
| PRIMARY-003 | DİE Yayın No. 513, *1950-1965 Milletvekili ve 1961, 1964 Cumhuriyet Senatosu Üye Seçimleri Sonuçları* (1966, xxxvii+1385 s.), kutuphane.tuik.gov.tr/pdf/0015202.pdf | Resmî | A | 1950–1965 | İlçe sonuçları | 1950–1957 yalnız il; ilçe/sandık yalnız 1965. Kütüphane kayıtlarındaki "il ve ilçe" ibaresi 1965'i kastediyor | Hayır |
| PRIMARY-004 | DİE *İl ve İlçe Sonuçları* 1961–1977 (0014128) ve 1983–1995 (0014049) | Resmî | A | 1961–1995 | Parti toplamı ≠ geçerli oy satırları | Basılı kaynakta da aynı | Hayır |
| PRIMARY-005 | TÜİK Yayın No. 3685, *Milletvekili Genel Seçimleri 1923-2011* | Resmî | A | 1950–1977 | İlçe sonuçları | Yalnız il | Hayır |
| SECONDARY-001 | Türkçe Wikipedia seçim maddeleri | Ansiklopedi | D | 1950–1957 | İlçe sonuçları | Yalnız il; keşif aracı olarak kullanıldı | Hayır |
| SECONDARY-002 | Erol Tuncer / TESAV, *1954 Seçimleri* (2011, 464 s.) ve *1957 Seçimleri* | Kitap | B | 1954, 1957 | İlçe dağılımı | Yayıncı tanıtımına göre il ve bölge düzeyi; ilçe anılmıyor. İçindekiler görülmedi | Elle (basılı kitap) |
| SECONDARY-003 | Erol Tuncer, *1950 Seçimleri* | Kitap | B | 1950 | İlçe dağılımı | Önceki oturumda potansiyel kaynak olarak not edildi, içeriği görülmedi | Elle (basılı kitap) |
| ACADEMIC-001 | Tülay Aydın, "1957 Genel Seçimleri: Taşrada Değişen Siyaset Dengesi", *Gaziantep Üniv. Sosyal Bilimler Dergisi* 22(3), 2023 | Makale | B | 1957 | Ülke çapı ilçe verisi | 10 il, il düzeyi; kaynakçada ilçe düzeyinde resmî yayın yok | Hayır |
| ACADEMIC-002 | Tek-il çalışmaları (DergiPark/ResearchGate): Niğde 1950–60, Kars 1950–57, Sakarya 1957, Kütahya 1957, İçel, Konya, Maraş 1957, Buldan (Denizli) sempozyum bildirisi | Makale | B–C | 1950–1957 | İlçe tablosu | Parçalı kaynak: bazıları yerel gazete ve BCA'ya dayanıyor; ilçe tablosu içerip içermedikleri tek tek açılmadı | Evet, yalnız il il toplama kararı verilirse |
| NEWS-001 | Gaste Arşivi (gastearsivi.com) | Gazete arşivi | B | 1954 | Seçim sonrası sayılar | Otomatik erişime kapalı (403) | Elle |
| ARCHIVE-001 | Internet Archive (archive.org) | Dijital arşiv | – | 1950–1957 | DİE/İstatistik Umum Müdürlüğü seçim yayını | İlgili kayıt yok | Hayır |
| ARCHIVE-002 | HathiTrust | Dijital kütüphane | – | 1950–1965 | DİE yayınları | Katalog 403; IUCAT'a göre Yayın 513 orada (içeriği PRIMARY-003 ile biliniyor) | Hayır |
| GITHUB-001 | GitHub seçim veri setleri | Kullanıcı verisi | D | 1950–1977 | Hazır ilçe seti | Önceki oturumlarda tarandı; güvenilir tam set yok | Yalnız yeni repo çıkarsa |
