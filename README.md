# Türkiye Seçim Haritası

*Türkçe | [English](README.en.md)*

1950–2024 arasındaki bütün genel seçim, yerel seçim, referandum ve cumhurbaşkanlığı seçimi sonuçlarını
il, ilçe ve 2009'dan sonra mahalle düzeyinde gösteren interaktif harita.

**Site:** https://hamikumbasae.github.io/turkiye-secim-haritasi/ · **Açık veri:** [veri.html](https://hamikumbasae.github.io/turkiye-secim-haritasi/veri.html) · **Yöntem:** [yontem.html](https://hamikumbasae.github.io/turkiye-secim-haritasi/yontem.html)

> **Durum: tamamlandı.** v1.0 12 Ekim 2026'da kapandı; son bakım 21 Ekim 2026. Yeni bir seçim olduğunda
> eklenir; bilinçli olarak kapsam dışı bırakılanlar [aşağıda](#kapsam-sınırları).

## Kapsam

| | Seçim | Düzey |
|---|---|---|
| Genel | 20 (1950–2023) | il; ilçe 1961'den beri |
| Yerel | 15 (1950–2024) | il, ilçe; 1968, 1973, 1977 ve 1984'ten beri belediye meclisi ve il genel meclisi |
| Referandum | 7 (1961–2017) | il, ilçe |
| Cumhurbaşkanlığı | 4 (2014–2023, 2023'te iki tur) | il, ilçe |

Mahalle (muhtarlık) sonuçları 2009–2024 arasındaki 15 seçimde var. Mahalle sınırıyla haritaya yerleşen seçmen
payı 2014–2024'te %93–94, 2009–2011'de %87–88. Her seçim, o tarihteki il ve ilçe sınırlarıyla çizilir.

## Özellikler

- **Harita modları:** kazanan, katılım, parti oy oranı ve değişim (aynı türdeki önceki seçime göre yüzde puan).
- **Seçim geçmişi:** genel seçimde bir il ya da ilçeye tıklayınca o yerin bütün genel seçimlerdeki eğrisi.
- **Karşılaştır:** iki seçim yan yana, senkron yakınlaştırma.
- **Göm:** o anki görünüm için iframe kodu (`&gom=1`, isteğe bağlı `&tema=acik|koyu`).
- **Paylaşılabilir bağlantı:** seçim, il, ilçe, mahalle, mod ve parti adresin `#` kısmında.
- **Açık veri:** seçim başına il+ilçe, mahalle ve meclis CSV'leri, JSON, toplu zip ve SHA256SUMS (CC BY-SA 4.0).
- **Erişilebilirlik:** renk körü dostu palet (Okabe–Ito), klavyeyle gezinme, ekran okuyucu etiketleri.

## İnternetsiz kullanım

[Sürümler](https://github.com/hamiKumbasae/turkiye-secim-haritasi/releases) sayfasından
`turkiye-secim-haritasi-tek-dosya.zip`'i indirip `index.html`'e çift tıklayın. Bütün veri dosyanın içinde (~38 MB),
sunucu gerekmez. Dosya depoda tutulmaz; her sürüme otomatik eklenir. Kendiniz üretmek için:
`python3 scripts/build.py`.

## Proje yapısı

```
data/raw/            Dış kaynakların checksum'lı ham kopyaları (YSK, TÜİK, Resmî Gazete, ikincil kaynaklar)
data/kaynaklar/      Kaynak başına ayrıştırılmış veri (her değerin kökenini izlemek için)
data/normalized/     Sitenin okuduğu veri: elections/<tür>/<seçim>.json, mahalle/, meclis_harita/, ek/
geo/normalized/      Güncel il, ilçe ve mahalle sınırları
geo/historical/      Tarihsel il/ilçe sınırları ve ilçe eşleme tabloları
site/                Ön yüz (src/), Pages derlemesi (build.py → site/dist/), Playwright testleri
scripts/             Yayın (export_static, kompakt, build, acik_veri), doğrulama, denetim ve veri hatları (pipelines/)
tests/               Analitik doğrulama, Node ve tarayıcı testleri
docs/rapor/          Kapsam tablosu, veri denetimi ve eşleştirme raporları
backend/             Spring Boot mikroservisleri + MySQL 8, Docker (data-loader, election-api, gateway)
backend/election-api-lite/  Tek servislik Spring Boot API, MariaDB üzerinde (ör. Raspberry Pi ev sunucusu)
chatbot/             Türkçe soru → SQL sohbet botu (yerel LLM ya da Claude, SQL güvenlik katmanı, değerlendirme seti)
```

Harita sunucu istemez. Aynı veri `scripts/db_yukle.py` ile MariaDB/MySQL'e yüklenir; API ve sohbet botu oradan okur.

Her veri klasörünün kendi `PROVENANCE.md`'si var. Kaynakların tam listesi: [`SOURCES.md`](SOURCES.md) (okunabilir)
ve [`sources.yml`](sources.yml) (makine-okunur; her seçimin birincil kaynağı ve bilinen sorunları).

**Tek ön yüz, iki dağıtım.** `python3 site/build.py` GitHub Pages sitesini üretir; veri ayrı dosyalardan
gerektikçe indirilir (`pages.yml` main'e her push'ta yayımlar). `python3 scripts/build.py` aynı dosyaları
tek bir `index.html`'e gömer. Mahalle oyları ve sınırları yayında kompakt biçimdedir (`scripts/kompakt.py`;
sınırlar kayıpsız TopoJSON), tarayıcı açarken eski biçime çevirir.

## Geliştirme

```bash
pip install -r requirements.txt          # pyyaml, shapely (Python 3.13)
python3 site/build.py                    # site/dist/
python3 -m http.server -d site/dist 8000 # http://localhost:8000
```

| Kontrol | Komut |
|---|---|
| Yapısal doğrulama (build'i durdurur) | `python3 scripts/validate.py` |
| Yayın verisi | `python3 scripts/validate_public_data.py` |
| Veri denetimi (yeni bulguda başarısız) | `python3 scripts/veri_denetimi.py --kontrol docs/rapor/veri_denetimi` |
| Analitik doğrulama, senkron, tekrarlanabilirlik | `python3 tests/validate_elections.py` |
| Node testleri (önce `site/build.py`) | `node --test tests/*.test.cjs` |
| Site testleri | `cd site && npm ci && npm test` |

Hepsi her push ve PR'da `.github/workflows/validate.yml` ile çalışır.

**Veri güncellemek.** `data/normalized/` altındaki dosyayı değiştirin, değişen klasör için
`python3 scripts/regenerate_checksums.py <klasör>` çalıştırın, sonra kontrolleri çalıştırıp commit'leyin.
Veri düzeltildiyse denetim listesini yenileyin:
`python3 scripts/veri_denetimi.py --md docs/rapor/VERI_DENETIMI.md --csv-klasor docs/rapor/veri_denetimi`.

**Yeni seçim (mahalle).** YSK açık verisi yalnız GitHub Actions'tan erişilebilir; çekme ve eşleştirme adımları
[`scripts/pipelines/mahalle_veri/`](scripts/pipelines/mahalle_veri/README.md) altında.

**Tarihsel sınırlar.** Yalnız `scripts/pipelines/historical_geo/tarihsel_sinirlari_uret.py` ile yeniden üretin;
adımları doğru sırayla ve idempotent çalıştırır. Ayrıntı: [`geo/historical/idari/README.md`](geo/historical/idari/README.md).

**Bir değerin kaynağı.** `python3 scripts/kaynak.py 1995 İstanbul Fatih` (liste: `--liste`).

## Veri kalitesi

Değerler kaynaktaki gibi tutulur. Kaynak kendi içinde tutarsızsa değer değiştirilmez; sitede, CSV'nin "not"
sütununda ve [`docs/rapor/VERI_DENETIMI.md`](docs/rapor/VERI_DENETIMI.md)'de açıklanır. Başlıcaları:

- **Katılım %100'ü aşan mahalleler** (~26 bin kayıt, YSK verisinde): katılım "hesaplanamıyor" gösterilir, oylar aynen kalır.
- **İl toplamı ilçe toplamını tutmayan 53 kayıt:** fark resmî yayının kendisinde (TÜİK tablosunun il satırı kendi
  ilçe satırlarını tutmuyor); il kaydında `ilceFarki` ve not var.
- **Elle düzeltmeler** yalnız kanıt kesinse yapılır ve eski değer kayıtta saklanır: Kocaeli 2002 il seçmeni
  (yazım hatası, 100.000 fark), 1979 Senato'da Kütahya ve Manisa (PDF sütun kayması). Ayrıntı: `sources.yml`.

## Kapsam sınırları

Seçim başına kapsam, kalite ve en iyi kaynak: [`docs/rapor/KAPSAM_TABLOSU.md`](docs/rapor/KAPSAM_TABLOSU.md).
Nerelere bakıldığı: [`data/kaynaklar/ARASTIRMA_KAYDI.md`](data/kaynaklar/ARASTIRMA_KAYDI.md).

- **1950, 1954, 1957 genel seçimleri** yalnız il düzeyinde; ülke çapında ilçe kaynağı yok.
- **1950–1977 yerel başkanlık sonuçları** Vikipedi'ye dayanır. 1950 ve 1955'te başkanı meclis seçtiği için ilçede yalnız kazanan parti var.
  1963–1977'de DİE kitabının başkanlık tablosunda okunup iç kontrolden geçen satırlar kayda işlendi (sayılar kitaptan; teyitli
  satır payı 1963 %25, 1968 %50, 1973 %75, 1977 %65). Kalanlar yalnız Vikipedi. Kitapta "Bağımsızlar" bütün bağımsız
  adayların toplamıdır; kazanan oy sırasından değil, 1973'te kitabın kazanan sütunundan, öteki yıllarda aday bazında belirlenir.
- **1963–1984 yerel meclis sonuçları:** taranmış DİE kitabında okunamayan ya da doğrulanamayan satırlar boş (1984: belediye
  meclisi %21, il genel meclisi %11; 1977: %26 ve %19, belediye meclisinde 8 ilin sayfaları taramada yok; 1973: %17 ve %16;
  1968: %34 ve %23; 1963: %71 ve %39). 1963 ve 1968 belediye meclisinde parti oyları toplamı çoğu yerde geçerli oydan az
  basılmış; bu satırlar notlu.
- **Ayrıştırılmamış "Diğer":** küçük partilerin kaynakta tek toplam olduğu yerler. 2009–2024 yerel ve 2011–2023 genel
  seçimlerde YSK verisiyle, 1994–2004 yerelde DİE kitabıyla partilere ayrıldı; 10 kayıtta kazanan hâlâ "Diğer" (sitede notlu).
- **Kaba eşlemeler:** birden çok eski ilçeden pay alan bazı yeni ilçeler (ör. Çukurova, Körfez) en büyük paya göre
  tek ilçeye bağlı (`geo/historical/idari/ilce_eslesme/*.csv`, güven `kaba`).
- **Ankara Merkez (1961–1983):** ayrı ilçeydi ama sınırı kaynakta yok; haritada poligonu yok.
- **2009 yerel, Ağın ve Kadışehri:** haritada iptal edilen 29 Mart sonucu; 7 Haziran yenilemesi `data/normalized/ek/yenileme_ara/`'da.
  Kadışehri ilçe merkezi belediye meclisinin yenileme sonucu YSK açık verisinde ve Vikipedi'de yok.
- **2002 Siirt:** iptal edilip 9 Mart 2003'te yenilenen seçimin resmî sonucu (hata değil).
- **2011:** BDP destekli bağımsızlar yedi ilde "BDP", diğer illerde "Bağımsız" içinde.
- Bazı ham kaynakların orijinal çıktısı saklanmamış: [`NOTICE.md`](NOTICE.md).

Seçim takvimi ve her seçimin bu projedeki durumu: [`SECIM_TAKVIMI.md`](SECIM_TAKVIMI.md).

## Lisans

- **Kod:** MIT ([LICENSE](LICENSE)).
- **Veri:** CC BY-SA 4.0. Mahalle sınırlarının OpenStreetMap'ten gelenleri ODbL (© OpenStreetMap katkıcıları), Bursa ve
  Sakarya belediyelerinden gelenleri kendi açık veri lisanslarıyla; TKGM'den gelenler bu lisansın dışında.
  Ayrıntı: [LICENSE-DATA.md](LICENSE-DATA.md).
