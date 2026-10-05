# Depoda olmayan kaynaklar (indirilecekler listesi)

Derlendiği tarih: 2026-10-05. Kaynak: depodaki Vikipedi sayfalarının kaynakçaları, PROVENANCE
dosyaları, `ARASTIRMA_KAYDI.md` ve web araması. TÜİK kütüphanesi ve YSK sitesi bu çalışma ortamından
erişilemediği için dosyalar **elle** indirilecek; bağlantılar tarayıcıda açılır. İndirilen dosya
eklenmeden önce içeriği ve SHA-256'sı kontrol edilir (bilinen SHA-256'lar aşağıda).

Eklenip eklenmeyeceği sonra kararlaştırılacak; bu liste yalnızca nerede ne olduğunu kaydeder.

## A. Veri boşluğunu doğrudan dolduranlar

### A1. YSK 1994 / 1999 / 2004 belediye meclisi ve il genel meclisi (belediye/ilçe düzeyi)

Depoda yalnız bu yılların **belediye başkanlığı** ve **büyükşehir** PDF'leri var
(`data/raw/ysk/mahalli-1994-1999-2004/`). Aynı YSK arşivinde meclis ve il genel meclisi dosyaları da
var ve hiç indirilmedi. Meclis verisi şu an taranmış DİE kitaplarından okunuyor; okunamayan satırlar
boş (kapsam tablosu: 1994 belediye meclisi %30, il genel meclisi %31 eksik; 1999 %20 / %12; 2004 %5 / %7).
YSK dosyaları dijital metin (arama sonucunda tablo başlığı metin olarak görünüyor:
"Seçim Çevresi: Antalya İlçe Belediye Sandık sayısı Kayıtlı seçmen sayısı").

| Yıl | Belediye meclisi (tümü) | İl genel meclisi (tümü) |
|---|---|---|
| 1994 | [1994Mahalli-BelediyeMeclis-Tumu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1994/BelediyeMeclis/Pdf/1994Mahalli-BelediyeMeclis-Tumu.pdf) | [1994Mahalli-ilGenel-Tumu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1994/ilGenel/Pdf/1994Mahalli-ilGenel-Tumu.pdf) |
| 1999 | [1999Mahalli-BelediyeMeclis-Tumu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1999/BelediyeMeclis/Pdf/1999Mahalli-BelediyeMeclis-Tumu.pdf) | [1999Mahalli-ilGenel-Tumu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1999/ilGenel/Pdf/1999Mahalli-ilGenel-Tumu.pdf) |
| 2004 | [2004Mahalli-BelediyeMeclis-Tumu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/2004/BelediyeMeclis/Pdf/2004Mahalli-BelediyeMeclis-Tumu.pdf) | [2004Mahalli-ilGenel-Tumu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/2004/ilGenel/Pdf/2004Mahalli-ilGenel-Tumu.pdf) |

"Tumu" dosyası açılmazsa il başına dosyalar: [`ysk_meclis_1994_2004_url.txt`](ysk_meclis_1994_2004_url.txt)
(474 URL, desenden üretildi, test edilmedi). Mac Terminal'de toplu indirme:

```sh
mkdir -p ~/Desktop/"seçimlerimin kodları"/ysk-meclis && cd ~/Desktop/"seçimlerimin kodları"/ysk-meclis
curl -fsSL https://raw.githubusercontent.com/hamiKumbasae/turkiye-secim-haritasi/main/data/kaynaklar/ysk_meclis_1994_2004_url.txt \
  | grep '^https' | xargs -n1 curl -fsSO -A "Mozilla/5.0"
```

### A2. YSK 7 Haziran 2009 yenileme seçimleri (ilçe başına)

Depoda 7 Haziran 2009 yenilemesinden yalnız Ağın ve Kadışehri başkanlığı var (Vikipedi'den;
`data/normalized/ek/yenileme_ara/2009yenileme_belediye_baskanligi.json`). Kadışehri belediye meclisi
README'de eksik olarak duruyor. YSK'de altı ilçenin dosyası var (Vikipedi kaynakçasından):

- [agin.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/7Haziran/agin.pdf) — Ağın (Elazığ)
- [kadisehri.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/7Haziran/kadisehri.pdf) — Kadışehri (Yozgat)
- [akyazi.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/7Haziran/akyazi.pdf) — Akyazı (Sakarya)
- [mecitozu.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/7Haziran/mecitozu.pdf) — Mecitözü (Çorum)
- [sarkikaraagac.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/7Haziran/sarkikaraagac.pdf) — Şarkikaraağaç (Isparta)
- [yaprakli.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/7Haziran/yaprakli.pdf) — Yapraklı (Çankırı)

Akyazı, Mecitözü, Şarkikaraağaç ve Yapraklı yenilemeleri depoda hiç yok (hangi seçimin
yenilendiği dosyadan görülecek).

### A3. YSK 1963–1977 mahalli seçimler, Türkiye toplamları

Depoda `data/raw/ysk/mahalli-1963-1977/` altında her yılın belediye başkanlığı ve il genel meclisi
özeti var. Belediye meclisi özeti yok; 1963–77 meclis tabloları DİE kitaplarından okunursa
Türkiye toplamı kontrolü için:

- [1973 belediye meclis üyeliği](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1973/KesinSecimSonuclari/1973_Belediye_Meclis_Uyeligi_Secimleri_Sonucu.pdf)
- [1977 belediye meclis üyeliği](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1977/KesinSecimSonuclari/1977_Belediye_Meclis_Uyeligi_Secimleri_Sonucu.pdf)
- 1963 ve 1968 için aynı desen denenebilir: `.../Mahalli/<yıl>/KesinSecimSonuclari/<yıl>_Belediye_Meclis_Uyeligi_Secimleri_Sonucu.pdf`

## B. Depoda kullanılmış ama tam dosyası olmayan kitaplar

Bunlardan yalnızca kullanılan sayfaların metni ya da bir kısmı depoda; tam PDF büyük olduğu için
konmamış. GitHub'da saklamak için 100 MB üstü olanlar 1963 kitabı gibi parçalanır
(`scripts/pipelines/tuik_arsiv/kitap_birlestir.py`).

| Kitap | Bağlantı | Depoda | Bilinen SHA-256 |
|---|---|---|---|
| DİE Yayın 513, *1950-1965 Milletvekili ve 1961, 1964 C. Senatosu Seçimleri Sonuçları* (95 MB) | [0015202](https://kutuphane.tuik.gov.tr/pdf/0015202.pdf) | yok (çapraz kontrol) | `37add4d2469ac1cd81b08534ef90805af6a6985eda2abd4199bb0541732e1cec` |
| DİE, *Milletvekili Genel Seçimi Sonuçları (İl ve İlçe) 1961-1977* (11 MB) | [0014128](https://kutuphane.tuik.gov.tr/pdf/0014128.pdf) | yok | `0d122d886214238edfb5e51029859ea1cba4a543a984a850d3c415dbcf00ffe8` |
| DİE, *Milletvekili Genel Seçimi Sonuçları (İl ve İlçe) 1983-1995* (20 MB) | [0014049](https://kutuphane.tuik.gov.tr/pdf/0014049.pdf) | yok | `a38f96c0980bbf25d3eeec952e15111090346a9ae14695466957381ae30ce833` |
| TÜİK Yayın 3685, *Milletvekili Genel Seçimleri 1923-2011* (4,5 MB) | [YSK kopyası](https://www.ysk.gov.tr/doc/dosyalar/1923-2011-MVSecimleri-Tuik.pdf) | yok | `695d769c6c9a5e984810ea32adc663deabbd642f4c52b5d94eeea44550fbb90d` |
| DİE, 1961 Milletvekili ve Senato (il, ilçe, sandık bölgesi) | [0015147](https://kutuphane.tuik.gov.tr/pdf/0015147.pdf) | sayfa metinleri (`tuik/senato-metin`) | `data/kaynaklar/tuik/senato/*.json` → `pdfSha256` |
| DİE, 1964 Kısmi Senato | [0015169](https://kutuphane.tuik.gov.tr/pdf/0015169.pdf) | sayfa metinleri | 〃 |
| DİE, 1966 Senato kısmi | [0015213](https://kutuphane.tuik.gov.tr/pdf/0015213.pdf) | sayfa metinleri | 〃 |
| DİE, 1968 Senato kısmi | [0015265](https://kutuphane.tuik.gov.tr/pdf/0015265.pdf) | sayfa metinleri | 〃 |
| DİE, 1973 Milletvekili ve Senato | [0015450](https://kutuphane.tuik.gov.tr/pdf/0015450.pdf) | sayfa metinleri | 〃 |
| DİE, 1975 Senato ve ara seçim | [0015581](https://kutuphane.tuik.gov.tr/pdf/0015581.pdf) | sayfa metinleri | 〃 |
| DİE, 1977 Milletvekili ve Senato | [0015631](https://kutuphane.tuik.gov.tr/pdf/0015631.pdf) | sayfa metinleri | 〃 |
| DİE, 1979 Senato ve ara seçim | [0015789](https://kutuphane.tuik.gov.tr/pdf/0015789.pdf) | sayfa metinleri | 〃 |
| DİE, 1960 Genel Nüfus Sayımı (il, ilçe, bucak, köy) | [0015128](https://kutuphane.tuik.gov.tr/pdf/0015128.pdf) | İstanbul sayfaları | `3e38c8d66e0bbfc7f07924a26c23b41b9ca1c17349428ef508ebd78c65060362` |
| DİE, 1985 Nüfus Sayımı İdari Bölünüş | [0013062](https://kutuphane.tuik.gov.tr/pdf/0013062.pdf) | İstanbul sayfaları | `feb485f5f062cb24636f27f1791369bbce7dc252383a3bf4d28c059e67101ca7` |
| DİE, 1990 Nüfus Sayımı İdari Bölünüş | [0013349](https://kutuphane.tuik.gov.tr/pdf/0013349.pdf) | İstanbul sayfaları | `f4003db9584ddf4faa26519c8cc88139e54d4f4b9ef2c9f1eed50fcab99eab85` |

## C. Hiç kullanılmamış, ilgili yayınlar (çapraz kontrol)

Genel seçim ilçe verisi TÜİK uygulamasından (secimdagitimapp) geldiği için bunlar yeni veri
getirmez; basılı karşılık ve kontrol için.

| Kitap / dosya | Bağlantı | Not |
|---|---|---|
| DİE, 1961 Milletvekili seçimi il ve ilçe sonuçları | [0015118](https://kutuphane.tuik.gov.tr/pdf/0015118.pdf) | Vikipedi kaynakçası |
| DİE, 1969 Milletvekili genel seçimi | [0015301](https://kutuphane.tuik.gov.tr/pdf/0015301.pdf) | secimdagitimapp PROVENANCE'ta anılıyor |
| DİE, 1987 Milletvekili genel seçimi, ilçe | [0013195](https://kutuphane.tuik.gov.tr/pdf/0013195.pdf) | 〃 |
| DİE, 1995 Milletvekili genel seçimi, ilçe | [0013722](https://kutuphane.tuik.gov.tr/pdf/0013722.pdf) | 〃 |
| YSK 1957 milletvekili seçimi sonuçları | [1957_Secim_Sonuclari.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/1957MilletvekiliSecimi/1957_Secim_Sonuclari.pdf) | 1950'nin karşılığı depoda (`ysk/1950-tbmm-crosscheck`); 1957 ilçe verisi içerip içermediği bakılmalı |
| YSK 1969 milletvekili seçimi sonuçları | [1969_Secim_Sonuclari.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/1969MilletvekiliSecimi/1969_Secim_Sonuclari.pdf) | |
| YSK 1977 milletvekili seçimi sonuçları | [1977_Secim_Sonuclari.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/1977MilletvekiliSecimi/1977_Secim_Sonuclari.pdf) | |
| YSK 2002 milletvekili seçimi il sonuçları | [2002_secim _sonuclari.pdf](https://www.ysk.gov.tr/doc/dosyalar/docs/2002MilletvekiliSecimi/2002_secim%20_sonuclari.pdf) | |
| YSK halkoylamaları 1961, 1982, 1987, 1988 | [1961](https://www.ysk.gov.tr/doc/dosyalar/docs/1961Referandum/9-Temmuz-1961-Halk-Oylamasi.pdf) · [1982](https://www.ysk.gov.tr/doc/dosyalar/docs/1982Referandum/7-Kasim-1982-Halk-Oylamasi.pdf) · [1987](https://www.ysk.gov.tr/doc/dosyalar/docs/1987Referandum/6-Eylul-1987-Halkoylamasi.pdf) · [1988](https://www.ysk.gov.tr/doc/dosyalar/docs/1988Referandum/25-Eylul-1988-Halk-Oylamasi.pdf) | Aynı sonuçlar TÜİK 0018260'ta depoda |
| YSK'deki DİE 1984 mahalli kitabı | [1984Mahalli-Tuik.pdf](https://www.ysk.gov.tr/doc/dosyalar/1984Mahalli-Tuik.pdf) | Depodaki 0012953 ile aynı kitabın başka taraması olabilir; 1984 OCR'i zayıf olduğu için ikinci tarama işe yarayabilir |
| YSK 1984 büyükşehir belediye başkanlığı kesin sonuç | [PDF](https://www.ysk.gov.tr/doc/dosyalar/docs/Mahalli/1984/KesinSecimSonuclari/1984-Buyuksehir-Belediye-Baskanligi-Secimleri-Sonucu.pdf) | |
| TÜİK, *Mahalli İdareler Seçimi 29.03.2009* | [açıklama bölümü](https://www.tuik.gov.tr/indir/secim_2009/aklama.pdf) | 2009 verisi YSK'den depoda; basılı karşılık |
| Başbakanlık İstatistik Genel Direktörlüğü yayını | [0015506](https://kutuphane.tuik.gov.tr/pdf/0015506.pdf) | Başlığı doğrulanamadı; 1950'lere ait olabilir, açıp bakılmalı |

## D. Demirbaş numarası bulunamayanlar (TÜİK kataloğunda aranmalı)

- TÜİK, *Milletvekili Genel Seçimi: İl ve İlçe Sonuçları* 1991, 1995, 1999, 2002, 2007, 2011
  ([SBB kütüphane kaydı](https://kutuphane.sbb.gov.tr/vufind/Record/48982?sid=251970)). İlçe verisi depoda
  secimdagitimapp'ten var; basılı karşılık.
- 1950 ve 1955 yerel seçimleri: DİE kitabı yok. Vikipedi'nin kaynağı Başbakanlık Cumhuriyet Arşivi
  (Fon 030.01, Yer No 52.312.7 / 51.309.3 / 51.309.8) — Devlet Arşivleri'nde aranmalı.
- 1950, 1954, 1957 genel seçim ilçe sonuçları: aranan her kaynakta yalnız il düzeyi
  (`ARASTIRMA_KAYDI.md`); C bölümündeki 1957 YSK dosyası ve 0015506 bu açıdan bir kez açılıp bakılmalı.
