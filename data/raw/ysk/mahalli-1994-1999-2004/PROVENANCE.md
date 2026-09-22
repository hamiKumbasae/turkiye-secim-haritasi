# YSK — 1994/1999/2004 yerel seçimleri, il-bazlı resmi arşiv (il merkezi düzeyi + ilçe/belde düzeyi)

`data/normalized/yerel_secimler.json`'daki `1994yerel`, `1999yerel`,
`2004yerel` anahtarlarının **il** kayıtlarını (ilçeler DEĞİL — bu depoda
zaten var, dokunulmadı) Wikipedia'dan YSK'nin resmi il-bazlı arşivine
yükselten script'lerin kaydı, 2026-09-22 (ikinci oturum, 1983-2007 genel
seçim yükseltmesinin hemen ardından).

## Kaynak — iki farklı dosya ailesi

- **Büyükşehir statüsündeki iller** (1994/1999: Ankara, İstanbul, İzmir,
  Adana, Bursa, Gaziantep, Konya, Kayseri, Antalya, Diyarbakır, Erzurum,
  Eskişehir, Samsun, Kocaeli — 2004'e Mersin ve Sakarya da eklendi):
  `ysk.gov.tr/doc/dosyalar/docs/Mahalli/<yıl>/Buyuksehir/Pdf/<yıl>Mahalli-Buyuksehir-<İl>.pdf`
  — PDF'in İLK satır çifti doğrudan büyükşehir toplamı (aradığımız kayıt),
  sonraki satırlar büyükşehir İÇİNDEKİ ilçe kırılımı (bu turda kullanılmadı).
- **Diğer tüm iller:**
  `ysk.gov.tr/doc/dosyalar/docs/Mahalli/<yıl>/BelediyeBaskanligi/Pdf/<yıl>Mahalli-BelediyeBsk-<İl>.pdf`
  — PDF, o ilin TÜM ilçe/belde belediye başkanlığı sonuçlarını (+ Türkiye ve
  il toplamlarını) içeriyor; "İlçe" sütunu **"Merkez"** (bazen "Merkez(2)",
  "Merkez (Antakya)" gibi varyantlarla) olan satır, il merkezinin kendi
  yarışı — aradığımız kayıt bu. Diğer ilçe/belde satırları bu turda
  kullanılmadı (aynı 1950-1977 yerel yükseltmesindeki kapsam sınırı).

Doğru "il merkezi = büyükşehir toplamı mı yoksa Merkez ilçesi mi" ayrımı,
**mevcut (Wikipedia kaynaklı) veriyle çapraz kontrol edilerek** doğrulandı:
Ankara 1994 için önceki veri zaten "RP, ~1.44M oy" gösteriyordu — bu büyükşehir
ölçeği, "Merkez ilçe" ölçeği değil (o çok daha küçük olurdu). Yeni veri
(1.439.838 geçerli oy, RP kazandı) bununla birebir örtüştü.

## Doğrulama

- **234/235 il×yıl** (75+79+81, iki istisna hariç — aşağı) için parti oyları
  toplamı resmi "geçerli oy sayısı" ile karşılaştırıldı, hepsi %2 tolerans
  içinde eşleşti (script'e gömülü otomatik güvenlik kontrolü — %2'den fazla
  sapan bir il YAZILMAZ, atlanır ve raporlanır).
- Ankara 1994 örneği manuel olarak PDF'ten okunup mevcut projenin verisiyle
  birebir karşılaştırıldı (kazanan, geçerli oy, tüm parti oy/oran değerleri).

## Bilinen istisnalar (dokunulmadı, eski Wikipedia verisiyle kaldı)

- **Gümüşhane 1994**: pdfplumber'ın bu spesifik PDF'te nadir bir sütun
  hizalama sorunu var (bazı hücreler beklenenden bir sütun kaymış geliyor,
  parti oyları toplamı resmi geçerli oydan ~2 kat çıkıyor) — otomatik
  güvenlik kontrolü bunu yakalayıp ATLADI, veri değiştirilmedi.

## Mersin/İçel 1994 ve 1999 — ilk denemede kaçırıldı, ikinci geçişte çözüldü

İlk geçişte Mersin'in "BelediyeBaskanligi" tablosu "Merkez" diye tek bir
ilçeyle değil, doğrudan "Akdeniz(1)"/"Toroslar(1)" gibi alt-birimlerle
başladığı için atlandı — hangi alt-birimin "il" kaydını temsil edeceği o
tablodan belirsizdi. Kullanıcının "belediyenin kendi tarihçe sayfasından
çöz" talimatı üzerine önce Mersin'in o dönemde büyükşehir olup olmadığı
kontrol edildi: **"Buyuksehir" PDF ailesinde Mersin/İçel için dosya VARDI**,
sadece `Mersin` değil, eski adıyla **küçük harfle `icel`** olarak kayıtlıydı
(`.../Buyuksehir/Pdf/1994Mahalli-Buyuksehir-icel.pdf`) — ilk taramada
denenen isim varyantları arasında bu yoktu. Bulununca doğrudan resmi
kaynaktan çözüldü, belediye web sitesine gitmeye gerek kalmadı:
- 1994: ANAP kazandı (176.698 geçerli oy, %37,3)
- 1999: DSP kazandı (215.615 geçerli oy, %19,4 — MHP'ye %18,2 ile çok yakın)

Bu, Mersin'in 1994/1999'da ZATEN büyükşehir statüsünde olduğunu doğruluyor
(2004'te "büyükşehir oldu" değil, sadece dosya adlandırması "İçel"den
"Mersin"e geçti — il'in kendisi 2002'de resmi olarak yeniden adlandırıldı).

## İlçe/belde düzeyi yükseltmesi (2026-09-23, dördüncü oturum)

Yukarıdaki iş SADECE "il" kaydını (il merkezinin/büyükşehirin kendi
yarışı) YSK'ye taşımıştı; "ilçeler" listesi hâlâ Wikipedia kaynaklıydı.
Kullanıcının "Wikipedia kaynaklarına YSK alternatifi var mı, varsa
kaynakları değiştir" talimatı üzerine, AYNI (zaten indirilmiş) PDF'lerin
ilçe/belde kırılımı da `scripts/yerel-1994-1999-2004-pipeline/
parse_ilce_belde.py` + `merge_ilce_belde.py` ile çıkarıldı.

**Format (normal il, "BelediyeBaskanligi"):** "İlçe" sütunu sadece yeni
bir ilçe grubu başladığında dolu (ör. "Merkez (Adapazarı)", "Akyazı");
o gruba bağlı beldeler "Belediye" sütununda, "İlçe" sütunu BOŞ satırlarla
listeleniyor. Bir belde adı BUGÜNKÜ bir ilçe adıyla (aynı plakada)
eşleşirse (ör. "Serdivan", "Arifiye" — sonradan ayrı ilçe oldu) KENDİ
kaydını alır; eşleşmezse GRUBUN ait olduğu ilçenin (Merkez dahil)
toplamına eklenir.

**Format (büyükşehir):** Tek sütun ("Belediye"), "İlçe" ayrımı YOK — her
satır doğrudan modern ilçe adıyla eşleştirilmeye çalışılır; eşleşmeyenler
(o dönem henüz ayrı ilçe olmamış beldeler, örn. İstanbul'un "Eyüp"
dışındaki bazı beldeleri) hiçbir ilçeye dahil edilmeden bırakıldı —
güvenilir bir ebeveyn bilgisi yok (kapsam sınırı olarak aşağıda).

**2004 format farkı (önemli bug):** 2004 PDF'lerinde bireysel ilçe/belde
satırlarının AYRI bir yüzde (oran) satırı YOK (sadece Türkiye/İl toplamı
satırlarında var) — ayrıca "Geçerli oy" ile parti sütunları arasına yeni
bir "Başkanlık sayısı" sütunu girmiş. İlk sürüm bunu fark etmeyip sabit
2'li satır-çifti varsayımıyla ilçelerin YARISINI "oran satırı" sanıp
atlıyordu (Kastamonu'da 20 ilçeden sadece 10'u okunuyordu) — düzeltildi:
artık "sandık sayısı" hücresi DOLU olan HER satır bir birim sayılıyor
(sabit adım yok), format farkına otomatik uyarlanıyor.

**Tarihsel/idari eşleme:**
- 13 ilin (Antalya, Diyarbakır, Erzurum, Eskişehir, Mersin, Malatya,
  Manisa, Kahramanmaraş, Samsun, Şanlıurfa, Van, Balıkesir, Artvin)
  "Merkez" ilçesi `geo/historical/district_splits.json`'daki sentetik
  HIST-*-Merkez geomId'lere çözülüyor.
- 1989-1999 arası eski ilden ayrılıp yeni il olan ilçeler (ör. Zonguldak
  → Karabük/Bartın, Bolu → Düzce, Siirt → Batman/Şırnak) için çocuk-il
  plakalarında da arama yapılıyor.
- Birkaç bilinen imla farkı (PDF'teki "Doğubeyazıt" vs modern
  "Doğubayazıt", "Arapkir" vs "Arapgir") elle eşlendi.
- **5 il — basit isim eşlemesiyle çözüldü (ek tur, aynı oturum):**
  Aydın→Efeler, Muğla→Menteşe, Ordu→Altınordu, Tekirdağ→Süleymanpaşa,
  Trabzon→Ortahisar. Bunlar da 2012 Büyükşehir Kanunu'yla "Merkez"
  ilçesini kaldırdı, ama (Denizli'nin aksine) TEK bir yeni isimle
  değiştirdi — birden fazla yeni ilçeye bölünmedi (web araştırmasıyla ve
  modern ilçe listesinde bu tek isimden başka ikinci bir aday olmadığı
  doğrulanarak teyit edildi). Bu yüzden `district_splits.json`'daki gibi
  yeni bir sentetik birleşim poligonu GEREKMEDİ — `MERKEZ_TEK_ISIM_
  YENIDEN_ADLANDIRMA` sözlüğüyle doğrudan modern ilçenin zaten var olan
  gerçek poligonuna eşlendi.

**Kapsam sınırı — sadece Denizli çözülemedi:** Bu il de aynı 2012
dalgasında "Merkez" ilçesini kaldırdı, ama yukarıdaki 5 ilin aksine İKİ
yeni ilçeye böldü (Pamukkale VE Merkezefendi) — `district_splits.json`'daki
13 il gibi gerçek bir sentetik birleşim poligonu gerektiriyor, salt bir
isim eşlemesi yetmiyor; bu oturumun kapsamı dışında bırakıldı. Denizli'nin
merkez ilçesi (+ ona bağlı birkaç küçük belde) eski Wikipedia kaydında
KALDI, üzerine yazılmadı.

**Sonuç (3 yıl toplamı):** 875+883+884=2642 ilçe kaydından 1999'u
(%75-76) artık YSK PDF'inden — bunun ~107 tanesi önceden Wikipedia'da
HİÇ karşılığı olmayan, tamamen YENİ eklenen ilçe kaydı (çoğu
büyükşehirlerin 2008-2014 split'lerinden doğan modern ilçeler, örn.
Kepez/Muratpaşa/Konyaaltı/Bağlar/Odunpazarı/Akdeniz/Atakum/Efeler/
Menteşe/Altınordu/Süleymanpaşa/Ortahisar, ya da Sakarya'nın Adapazarı/
Arifiye/Erenler/Serdivan'ı). Kalan ~%24-25 eski kaynakta kaldı (sadece
Denizli + tarihsel eşlemesi çözülemeyen dağınık küçük
beldeler, toplamda ulusal sandık sayısının %2'sinden azı).

**Doğrulama:** Playwright ile tarayıcıda gerçek render testi yapıldı
(1999yerel → Antalya → Kepez: "MHP %21.96 25.091 oy" gerçek veriyle
göründü; Sakarya → tüm 16 modern ilçe gerçek veriyle listelendi), 0 JS
hatası. Ayrıca Besni 1999'da önceki Wikipedia verisinin kazananı YANLIŞ
gösterdiği (CHP yazıyordu, gerçek/YSK sonucu DYP) fark edildi ve
düzeltildi — bu, sadece kapsamı değil doğruluğu da artıran bir örnek.

## Parti eşlemesi

`merge_into_normalized.py`'deki `STATIC_MAP`, genel-1983-2007-pipeline'daki
ile aynı yöntemle (mevcut Wikipedia-kaynaklı anahtarlarla karşılaştırılarak)
kuruldu. Bu turda partiler.json'a YENİ parti eklenmedi — tüm YSK kodları
zaten var olan anahtarlara eşlendi.

## Yeniden çalıştırmak için

```bash
# il duzeyi
python3 scripts/yerel-1994-1999-2004-pipeline/parse_ysk_pdfs.py 1994 data/raw/ysk/mahalli-1994-1999-2004/il_dosya_eslemesi.json data/raw/ysk/mahalli-1994-1999-2004 /tmp/parsed.json
python3 scripts/yerel-1994-1999-2004-pipeline/merge_into_normalized.py 1994 /tmp/parsed.json
# ilce/belde duzeyi
python3 scripts/yerel-1994-1999-2004-pipeline/parse_ilce_belde.py 1994 /tmp/ilce_1994.json
python3 scripts/yerel-1994-1999-2004-pipeline/merge_ilce_belde.py 1994 /tmp/ilce_1994.json
# (1999, 2004 icin tekrarlayin)
```

Ardından kök dizinde `python3 scripts/build.py` ile `index.html`'i yeniden
üretin ve checksum dosyalarını güncelleyin.
