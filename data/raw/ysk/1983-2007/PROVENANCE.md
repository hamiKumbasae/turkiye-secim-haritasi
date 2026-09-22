# YSK — 1983-2007 Milletvekili Genel Seçimleri, il-bazlı resmi arşiv

`data/normalized/genel_secimler.json`'daki 1983, 1987, 1991, 1995, 1999,
2002, 2007 yıllarının il kayıtlarını (katılım, seçmen, geçerli oy, il bazında
milletvekili dağılımı) Wikipedia'dan YSK'nin resmi arşivine yükselten
script'lerin kaydı — `../1950-1977/PROVENANCE.md` ile AYNI aile/yöntem,
2026-09-22'de aynı oturumda (1950-1977 pipeline'ından ilham alınarak) bulundu.

## Kaynak

`ysk.gov.tr/tr/1983-2007-yillari-arasi-milletvekili-genel-secimleri/3008`
sayfasının kendisi Angular SPA olduğu için sadece "Türkiye Geneli" ve aday
listesi PDF'lerine link veriyor — ama **aynı 1950-1977 arşivinin klasör
düzenini** (`Milletvekili/1983-2007/<İl>.pdf`, ASCII dosya adları) izliyor,
bu URL kalıbı sayfada linklenmemiş olsa da 81/81 il için çalışıyor (doğrudan
denenerek bulundu, bkz. `il_dosya_adi_eslemesi.txt`). Sakarya bu arşivde VAR
(1950-1977 arşivinin aksine — o arşivde 66/67 idi).

Her il PDF'i 1-3 sayfa (parti sayısına göre), 2 tablo: özet (7 satır × 7 yıl,
etiket sütunu yok) ve parti tablosu (parti başına 3 satır: Alınan oy sayısı /
Oy oranı / Kazandığı MV sayısı). Özet tablosu HER sayfada tekrarlanıyor —
sadece ilk sayfanınki kullanıldı, `parse_ysk_pdfs.py` bunu ayırıyor.

**"Geçerli oy sayısı" ikili:** Her il PDF'i hem "Geçerli oy sayısı" (gümrük
kapıları hariç) hem "Toplam geçerli oy sayısı" (gümrük dahil) veriyor. Parti
oylarının toplamı **Toplam** (gümrük dahil) ile eşleşiyor (Ankara 2007'de
doğrulandı: parti toplamı 2.459.587 = Toplam geçerli oy, 2.442.927 [gümrüksüz]
DEĞİL) — bu yüzden `gecerliOy` alanına Toplam değeri kondu.

## Doğrulama

- **529/529 il×yıl** için parti oyları toplamı resmi geçerli oy sayısıyla
  karşılaştırıldı: 495 tam eşleşti, 34'ünde (hepsi ±1-3 oy, çoğu 1999'da)
  kaynağın kendi küçük iç tutarsızlığı var — düzeltilmedi, sadece not edildi
  (1950-1977 pipeline'ında da aynı türde küçük farklar bulunmuştu).
- **Vekil toplamı bütünlüğü:** 529 il×yıldan 528'i, YSK'nin özet satırındaki
  "Milletvekili sayısı" ile parti-tablosu toplamının BİREBİR eşleştiğini
  doğruladı. Tek istisna: Bingöl 1983 (özet "3" diyor, parti tablosu toplamı
  "2" — bkz. `sources.yml`'deki `1983` girişinin `known_issues` alanı).
- **Ulusal toplam:** 7 yılın hepsinde, 67-81 ilin `toplamVekil` toplamı,
  bilinen resmi ulusal sandalye sayısıyla (399/450/450/550/550/550/550)
  birebir eşleşti.
- **İl sayısı büyümesi doğrulandı:** 1983/1987=67 il, 1991=74, 1995=79,
  1999=80, 2002/2007=81 — Türkiye'nin bilinen il sayısı artış tarihiyle
  (1989-1999 arası yeni iller) tutarlı.

## Parti eşlemesi

`merge_into_normalized.py`'deki `STATIC_MAP`, YSK'nin PDF'lerdeki kısa kodunu
projenin **önceden zaten kullandığı** (Wikipedia kaynaklı) anahtarla,
yıl-yıl karşılaştırılarak eşleştirildi — amaç parti kimliği atamasını
YENİDEN YORUMLAMAK değil, sadece kaynağı/sağlamlığı yükseltmek. 2 parti bu
turda ilk kez ayrı izlendi (önceden "Diğer"e karışıyorlardı): **MÇP**
(Milliyetçi Çalışma Partisi, 1987 — MHP'nin bu dönemki adı) ve **YENP95**
(Yeni Parti, 1995) — ikisi de major olmadığı için yine "Diğer"e giriyorlar,
sadece artık `partiler.json`'da kendi renkleriyle kayıtlılar. 1987'de ayrıca
IDP ve Bağımsızlar da ayrı izlendi (partiler.json'da zaten IDP/Bağımsız
anahtarları vardı).

## Kapsam dışı / henüz yapılmadı

- **İlçe düzeyi hâlâ GitHub kaynaklı** (2002/1999/1995/1991/2007 için
  `mertnuhoglu/secim_verileri`, memurlar.net kaynaklı) — bu YSK arşivi İL
  bazlı, ilçe kırılımı içermiyor (milletvekili "seçim çevresi" zaten il'in
  kendisi, ilçe bazlı ayrı bir sayım hiç yapılmadı — GitHub'daki ilçe verisi
  muhtemelen sandık/ilçe bazlı ham verinin bir başkası tarafından derlenmiş
  hâli). Resmi bir ilçe-bazlı alternatif bu oturumda ARANMADI/BULUNAMADI.
- 1987/1983 için ilçe verisi zaten yoktu (mertnuhoglu deposu o döneme
  uzanmıyor) — bu değişmedi.

## Yeniden çalıştırmak için

```bash
python3 scripts/genel-1983-2007-pipeline/parse_ysk_pdfs.py data/raw/ysk/1983-2007 /tmp/parsed.json
python3 scripts/genel-1983-2007-pipeline/merge_into_normalized.py /tmp/parsed.json data/raw/ysk/1983-2007/il_dosya_adi_eslemesi.txt
```

Ardından kök dizinde `python3 scripts/build.py` ile `index.html`'i yeniden
üretin ve `data/normalized/checksums.sha256` + `data/provenance/checksums.json`'ı
güncelleyin.
