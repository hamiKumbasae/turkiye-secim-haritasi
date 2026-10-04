# 2007 referandumu — YSK resmi ilçe-bazlı "Birleştirme Tutanağı" PDF'leri

**Kaynak:** `https://www.ysk.gov.tr/tr/21-ekim-2007-anayasa-degisikligi-halkoylamasi/2762`
→ "Seçim Sonuçları" → "İlçe Bazında İl Sonuçları" sekmesi, 81 il için ayrı
PDF (`.../2007Referandum/KesinSonuclar/<il>.pdf`). 2026-09-22'de indirildi.

Her PDF, o ilin **imzalı resmi birleştirme tutanağı** — İl Seçim Kurulu
Başkanı ve üyelerinin imzasını taşıyan, ilçe bazında sandık/seçmen/katılım/
geçerli-geçersiz oy/Evet-Hayır dağılımı. Bu, projedeki EN AYRINTILI ve EN
RESMİ tek referandum kaynağı — 2010/2017'nin YSK mahalle-düzeyi verisinden
bile daha "resmi" (o veriler API'den, bunlar doğrudan imzalı tutanaktan).

## Font/kodlama sorunu

Bu PDF'lerin bir kısmında Türkçe **Ğ, İ, Ş** harfleri metin çıkarımında
kayboluyor veya boşluğa dönüşüyor (örn. "KARAİSALI" → "KARA SALI",
"ALADAĞ" → "ALADA "). **Sayısal hücreler etkilenmiyor.** Çözüm: hem PDF'ten
çıkan bozuk ilçe adı hem de projenin güvenilir ilçe listesi
(`scripts/pipelines/mahalle_veri/eslesme/ysk_ilce_matched.json`) bu üç
harften ve boşluklardan arındırılıp öyle karşılaştırılıyor — bkz.
`scripts/pipelines/referandum/parse_2007_ilce_pdfs.py`.

## Eşleşme sonucu (2026-09-22)

**906 / 923 ilçe satırı (%98,2) eşleşti**, dahil:
- 894 doğrudan isim eşleşmesi
- 12 "X Merkez" satırı, `geo/historical/district_splits.json`'daki hazır
  sentetik tarihsel geometriye (`HIST-<İl>-Merkez`) yönlendirilerek — bu
  ilçeler 2007'den SONRA (2008+) bölünmüş büyükşehir merkezleri, 2007'de
  hâlâ tek parçaydı
- 7 isim değişikliği/yazım farkı elle doğrulanıp düzeltildi (örn.
  Kazan→Kahramankazan, Eyüp→Eyüpsultan — YSK'nin canlı `getIlceList`
  API'siyle tek tek teyit edildi, tahmin değil)

**Eşleşmeyen 17 satır** (`unmatched.txt`'de kayıtlı):
- 10 "X Merkez" — o ilin büyükşehir-Merkez bölünmesi için
  `district_splits.json`'da henüz sentetik geometri yok (Aydın, Denizli,
  Hatay, Kocaeli, Mardin, Muğla, Ordu, Sakarya, Tekirdağ, Trabzon)
- 7 küçük/nadir ilçe (Kale/Antalya, Akköy/Denizli, Ilıca/Erzurum,
  Çağlıyancerit/Kahramanmaraş [belirsiz, 2 aday], Hadım/Konya,
  Ondokuzmayıs/Samsun, Aydınlar/Siirt) — `ysk_ilce_matched.json`
  referans listesinde yok (o liste mahalle-pipeline'ın kendi ihtiyacına
  göre oluşturulmuştu, her modern ilçeyi kapsamıyor)

Bu 17 satırın oyu **hiçbir yerde kaybolmadı** — ilgili ilin il-düzeyi
toplamında zaten var, sadece ilçe-düzeyi haritada o tek ilçe için ayrı
bir poligon boyanmıyor.

## Bütünlük doğrulaması

`merge_2007_ilce.py`, il başına ilçe toplamlarını mevcut il kaydıyla
karşılaştırdı: eşleşmeyen "Merkez"i olan 10 il dışında **hiçbir ilde**
%5'i aşan fark yok — bu, 906 ilçenin doğru eşleştiğinin dolaylı kanıtı.

## Dosyalar

- `<il>.pdf` (81 dosya) — YSK'nin dosya adlandırması (ASCII, bazıları
  büyük harf: `Kirikkale.pdf` gibi tutarsızlıklar YSK'nin kendi sitesinden)
- `il_dosya_adi_eslemesi.txt` — dosya adı → gerçek il etiketi eşlemesi
- `parsed.json` — `parse_2007_ilce_pdfs.py` çıktısı (81 il × ilçe listesi)

## Bütünlük

`checksums.sha256` — 2026-09-22.

## 04.10.2026 tamamlaması

81 PDF yeniden ayrıştırıldı: 923/923 ilçe eşleşti, eşleşmeyen satır kalmadı.
Eksik 17 kayıt için ad ve geometri kimlikleri 2007 genel seçiminin aynı yıl
ilçe listesinden alındı; oylar yalnız referandum PDF'lerinden geldi. Eski
906 kaydın seçim değerleri ve sonradan düzeltilmiş geometri bağları korundu.
Her yeni satırda Evet + Hayır = geçerli oy kontrolü uygulandı.
Üstteki 906/923 değerlendirmesi ilk aktarımın tarihsel kaydıdır.
