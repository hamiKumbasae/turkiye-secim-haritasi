# Türkiye Seçim Haritası

1950-2024 arası tüm genel seçim, yerel seçim, referandum ve cumhurbaşkanlığı
seçimi sonuçlarını gösteren interaktif harita — 15 seçimde mahalle/muhtarlık
düzeyine kadar iniyor.

## Nasıl açılır

**Tek dosya.** Bu depoyu indirin (Code → Download ZIP, ya da `git clone`) ve
`index.html`'e çift tıklayın — tüm veri (~21 MB, gzip sıkıştırılmış) doğrudan
dosyanın içine gömülü, sunucu veya internet bağlantısı gerekmez.

(Not: Sayfa açılışta Google Fonts'tan bir yazı tipi çekmeye çalışır — internet
yoksa bu sessizce atlanır, harita/veri işlevselliğini etkilemez.)

## Performans

`index.html`'e her yayın dosyası (seçim, mahalle oyları, ilçe başına mahalle poligonları, dönem
sınırları) ayrı gömülüdür ve yalnız gerektiğinde açılır: açılışta il sınırları ve gösterilen seçim,
ilçe sınırları arka planda, mahalleler o ilçeye inilince. Ölçüm (yerel Chromium, `file://`,
açılıştan harita çizilene dek): ~1,1 sn.

## Site özellikleri

- **Harita modları:** Kazanan, Katılım, Parti (oy oranı) ve **Değişim** (seçilen partinin aynı
  türdeki önceki seçime göre oy oranı farkı, yüzde puan; sınırı değişen ilçe karşılaştırılmaz).
- **Paylaşılabilir bağlantı:** seçim, il, ilçe/mahalle, mod, parti ve oylama türü adresin `#`
  kısmında (`#secim=1977&il=6&mod=parti&parti=CHP`); "Bağlantıyı kopyala" düğmesi.
- **Kaynaklar ve yöntem:** [`yontem.html`](yontem.html) — kaynaklar, tarihsel sınırlar, harita
  okuma, bilinen eksikler; sade dille.
- **CSV indirme:** tablo görünümünde ve Kaynaklar çekmecesinde; açık seçimin il ve ilçe sonuçları.
- **Erişilebilirlik:** renk körü dostu palet (Okabe–Ito), klavyeyle gezinme ve ekran okuyucu
  etiketleri, telefonda yatay kayma yok.

## Veri mimarisi: raw → normalized → build

Veri kaynağı ve uygulama kodu artık ayrı. Hiçbir sayı elle `index.html`
içinde düzenlenmez:

```
data/raw/          Dış kaynakların checksum'lı, pinlenmiş snapshot'ları
                    (mertnuhoglu/secim_verileri, eski proje çıktısı) —
                    canlı bağımlılık yok. Boşluklar NOTICE.md'de açık.
geo/raw/            ttezer/OSM için pin bilgisi (dosyaların kendisi değil,
                    çok büyükler — nasıl yeniden indirileceği belgeli)
geo/historical/     Tarihsel il/ilçe sınır dönüşümleri (bu projenin kendi
                    türetilmiş katmanı, kaynak geometri DEĞİL)

data/normalized/    Seçim türüne göre ayrılmış, kayıpsız veri
                    (cumhurbaskanligi/genel_secimler/yerel_secimler/
                    referandumlar/mahalle/meclis_2024)
geo/normalized/     Güncel, basitleştirilmiş il/ilçe/mahalle geometrisi

site/                     Sitenin ön yüzü (src/), Pages derlemesi (build.py -> site/dist/), testleri
scripts/export_static.py  Yayın dosyaları (data/elections/…, geo/…; public_files)
scripts/build.py          site/ ön yüzü + aynı yayın dosyalarını gömerek tek dosyalık index.html üretir
scripts/validate.py         build.py'ye gömülü hızlı yapısal kontrol (gate)
tests/validate_elections.py Ayrı, yavaş/analitik kontrol seti
.github/workflows/validate.yml  Her push/PR'da validate.py + validate_elections.py +
                                 build.py + "index.html güncel mi" kontrolü

index.html, yontem.html (repo kökü)  build.py'nin çıktısı, commit'lenir; çift tıklayınca açılır
```

**Tek repo, tek ön yüz.** Sitenin HTML/CSS/JS'i `site/src/` altındadır ve iki şekilde dağıtılır:
GitHub Pages sitesi (`python3 site/build.py` → `site/dist/`, veriyi `data/`, `geo/` dosyalarından
`fetch()` ile okur; `.github/workflows/pages.yml` main'e her birleştirmede yayınlar) ve repo
kökündeki tek dosyalık `index.html` (`python3 scripts/build.py`; aynı dosyaları aynı yollarla gömer,
çift tıklayınca açılır). Eskiden ayrı olan `turkiye-secim-atlasi` reposu buraya taşındı.

Her klasörün kendi `PROVENANCE.md`'si var (nereden geldiği, nasıl
doğrulandığı). Kaynakların tam listesi için bkz. [`SOURCES.md`](SOURCES.md)
(okunabilir) ve [`sources.yml`](sources.yml) (makine-okunur, her seçimin
birincil/yedek kaynağı + bilinen sorunlar).

## Veriyi güncellemek

1. `data/normalized/` ya da `geo/normalized/` altındaki ilgili dosyayı düzenleyin (ön yüz için
   bkz. yukarıdaki "Tek ön yüz") (yeni bir
   seçim ekliyorsanız yeni bir `data/normalized/mahalle/<yil>.json` gibi —
   mahalle verisi için elle yerine `scripts/pipelines/mahalle_veri/transform/
   import_mahalle.py` kullanın, aşağıya bakın).
2. ```bash
   pip install -r requirements.txt   # ilk kurulumda bir kez (pyyaml)
   python3 scripts/build.py
   ```
   Bu, önce `scripts/validate.py`'nin yapısal kontrollerinden geçirir (hatalı
   veri build'i durdurur), sonra `index.html`'i yeniden üretir.
   Deterministiktir: aynı veriden iki kez çalıştırınca bayt-bayt aynı çıktı.
3. İsteğe bağlı, daha kapsamlı kontrol:
   ```bash
   python3 tests/validate_elections.py
   ```
4. `index.html`'i commit'leyin. `.github/workflows/validate.yml` her push/PR'da
   aynı kontrolleri + "commit'li `index.html` kaynaklarla senkron mu" kontrolünü
   otomatik çalıştırır — eski/senkron olmayan bir `index.html` ana dala giremez.

`scripts/pipelines/mahalle_veri/` klasörü, mahalle düzeyi verinin YSK Açık
Veri Portalı'ndan nasıl çekildiğinin/işlendiğinin kaydı (kurulum: `cd
scripts/pipelines/mahalle_veri && npm install && npx playwright install
chromium`). Yeni bir seçim eklerken `transform/import_mahalle.py --year
<yil> --input mahalle_<yil>.json --build` komutu veriyi doğru yerlere
otomatik yerleştirip doğrular (bkz. o klasörün kendi README'si).

## Web'e yayınlama (GitHub Pages)

**Canlı site: https://hamikumbasae.github.io/turkiye-secim-haritasi/**

`.github/workflows/pages.yml`, main'e her birleştirmede `python3 site/build.py` ile siteyi
`site/dist/` altında üretir ve GitHub Pages'e yayınlar (derlenen site commit'lenmez). Bir kez:
Settings → Pages → Build and deployment → Source: **GitHub Actions**. Eski adres
(`hamikumbasae.github.io/turkiye-secim-atlasi/`) buraya yönlendirir.

Yerelde: `python3 site/build.py && python3 -m http.server -d site/dist 8000`; site testleri
`cd site && npm ci && npm test`.

## Lisans

- **Kod:** MIT — bkz. [LICENSE](LICENSE).
- **Veri** (`data/normalized/`, `geo/`, `index.html`'e gömülü veri): CC BY-SA 4.0;
  OpenStreetMap'ten türetilen mahalle sınırları ODbL (© OpenStreetMap katkıcıları) — bkz.
  [LICENSE-DATA.md](LICENSE-DATA.md).

## Veri kökeni

Her seçimin il/ilçe kaynağı `sources.yml`'de; birden fazla kaynaktan beslenen
satırlarda satırın kendi `kaynak` alanı var (hangi değer hangi kaynaktan, eski/yeni).
Kaynak başına ayrıştırılmış veri `data/kaynaklar/`, ham dosyalar `data/raw/`.

```bash
.venv/bin/python scripts/kaynak.py --liste
.venv/bin/python scripts/kaynak.py 1995 İstanbul Fatih
```

## Bilinen kapsam sınırları

- 1950/1954/1957 genel seçimlerinde ilçe düzeyi veri yok, sadece il düzeyi —
  resmî bir ilçe kaynağı bulunamadı (1961/1982/1987/1988 referandumlarının ilçe
  düzeyi TÜİK "Halk Oylaması Sonuçları" yayınından eklendi). 1961-1987 arası 7 genel seçimin ilçe düzeyi 2026-09-24'te
  TÜİK'ten eklendi (bkz. `scripts/pipelines/genel_ilce_1961_1987/`);
  "seçim çevresi il olduğu için ilçe kırılımı yok" varsayımı yanlıştı.
- 1957/1961 genel seçimlerinde Sakarya'nın vekil dağılımı yok (YSK'nin
  1950-1977 arşivinde bu il hiç yok, bkz. `data/raw/ysk/1950-1977/PROVENANCE.md`).
- 2002 Siirt: il ve ilçe sonuçları, iptal edilip 9 Mart 2003'te yenilenen seçimin resmî sonucudur (YSK ve TÜİK aynı rakamı veriyor; hata değil — bkz. `sources.yml`).
- 2014 yerel seçiminde BDP il/ilçe verisi hatalı (gerçek oylar mahalle
  düzeyinde "HDP" altında bulundu, il/ilçe düzeyi düzeltilmedi).
- 2010 referandumunun ilçe düzeyi oy SAYILARI tahmini (`~300 oy/sandık`
  varsayımı) — yüzdeler gerçek.
- `data/raw/{haberturk,wikipedia}/` ve `data/raw/ysk/`'nin mahalle-düzeyi
  kısmı şu an boş — bu kaynakların orijinal ham çıktısı hiç saklanmamış veya
  yeniden üretilmedi. Ayrıntı: [`NOTICE.md`](NOTICE.md).

Tam liste ve her seçimin ayrıntısı için [`SOURCES.md`](SOURCES.md).
- 1950 ve 1955 yerel seçimlerinde ilçeler için yalnız kazanan parti var (oy sayısı
  yok); 1963–1977 yerel seçimlerinde ilçe belediye başkanlığı satırları var — bkz.
  [`SECIM_TAKVIMI.md`](SECIM_TAKVIMI.md) (1950-2024 arası tüm seçimlerin tam
  takvimi ve bu projedeki kapsam durumu).

## 04.10.2026 durum güncellemesi

### Yapılanlar

- **1961–2007 ilçe haritaları:** 26 seçimin ilçe haritasında hiçbir bugünkü ilçe
  sonuçsuz (taralı) kalmıyor: 1961–2007 genel seçimleri, 1961/1982/1987/1988/2007
  referandumları ve 1963–2004 yerel seçimleri. Sonradan kurulan her ilçe, o seçimdeki
  ilçesinin poligonuna katılır (`scripts/pipelines/historical_geo/build_ilce_secim.py`).
  Her ilçenin nereye ve neden bağlandığı `geo/historical/idari/ilce_eslesme/<seçim>.csv`
  tablosunda; güven sütunu `kesin` (kanun/sayım kaynağı), `yaklasik` (%70 ve üzeri birim
  çoğunluğu) ya da `kaba` (en büyük pay veya en uzun sınır komşusu).
- **İstanbul 1961–1991:** mahalle düzeyinde eski ilçe sınırları (Arnavutköy Eyüp ile Çatalca
  arasında vb.); 1987 öncesi Ümraniye mahalleleri 1960 nüfus sayımının köy listesi ve komşuluk
  ile, Kağıthane Şişli'ye, Ümraniye Üsküdar'a bağlı (yaklaşık; 1940 ve 1963 İstanbul ilçe
  haritalarıyla görsel olarak karşılaştırıldı).
- **Dönem il sınırları seçim verisinden:** `era1957_1965`, `era1957_1987`, `era1991` ve yeni
  `era1994`, o seçimde her ilin satırlarına bağlı ilçelerin birleşimi
  (`build_il_sinirlari.py`); il ve ilçe haritası birebir örtüşür. Eski dosyalarda yanlış ilde
  olan 13 ilçe düzeldi (Cizre, İdil, Silopi, Gercüş, Hasankeyf → Mardin; Beytüşşebap,
  Uludere → Hakkâri; Ağaçören, Sarıyahşi → Ankara; Armutlu → Bursa; Altınova → Kocaeli;
  Eflani, Ovacık → Çankırı). Kaynarca 1958–1965'te Kocaeli'de; 1994 yerelde Ardahan ve Iğdır
  ayrı il.
- **İstanbul'da gereksiz çizgiler (1961–2007):** birleşim poligonlarında kaynak parçalar tam
  oturmadığı için ilçe içinde ortada biten çizgiler (sıfır genişlikli çatlaklar; ör. 1991–2007
  Eyüp, Ümraniye, Kartal, Üsküdar), komşular arasında ince beyaz kamalar ve ince örtüşme şeritleri
  vardı. `ortusmeleri_temizle.py` bunları temizler: örtüşmeler çıkarılır, ~30 m'den dar çatlaklar
  kapatılır, birlikte çizilen ilçeler arasındaki ince boşluklar komşu tarihsel ilçeye eklenir.
  Gerçek ilçe sınırları değişmez.
- **Veri düzeltmeleri:** 1994/1999/2004 yerelde Artvin Hopa'nın aynı oylarla iki kez geçen
  satırının kopyası silindi; 1994 ve 1999 yerelde Kaynaşlı belde satırının plakası 81 → 14
  (o tarihte Bolu).
- **Tek betikle yeniden üretim:** `scripts/pipelines/historical_geo/tarihsel_sinirlari_uret.py`
  bütün tarihsel sınır adımlarını doğru sırayla çalıştırır (seçim katmanını geri al →
  `apply_idari_merges.py` → İstanbul → her seçim için `build_ilce_secim.py` →
  `ortusmeleri_temizle.py` → il sınırları →
  meclis → rapor → checksum → `build.py`). İdempotenttir: main üzerinde çalıştırınca fark
  çıkmaz. Tek tek betikleri elle ve başka sırayla çalıştırmayın.
- **Önceki 04.10.2026 işleri:** 2007 referandumu resmî PDF'lerden 923 ilçeye tamamlandı;
  2009/2011 tarihî ana ilçe birleşimleri; Tillo'nun YSK meclis kayıtları eşleştirildi.
- **Yayın:** site artık bu repodan (`site/`) GitHub Actions ile yayınlanıyor; veri değişince
  ayrıca bir yere aktarmak gerekmiyor.
- Ayrıntı ve yöntem: [`geo/historical/idari/README.md`](geo/historical/idari/README.md);
  güncel sayılar `docs/rapor/ozet.json` ve yanındaki CSV'ler.

### Bilinen eksikler

- **Kaba eşlemeler:** her seçimde 15–20 civarı çok kaynaklı ilçe (ör. Çukurova, Körfez, Aliağa,
  Ondokuzmayıs) en büyük paya ya da komşuluğa göre bütünüyle tek ilçeye bağlı; köy düzeyinde
  kaynak bulunursa bölünerek düzeltilebilir.
- **Ankara Merkez (1961–1983):** ayrı ilçeydi ama sınırı kaynakta yok; haritada poligonu yok.
- **Meclis haritaları:** 1984 ve 1994 yerelde il genel meclisi / belediye meclisi oy verisi
  eksik (1984'te yaklaşık 190 ilçe boş); sınır değil, veri sorunu.
- **Küçük kayıt sorunları:** 1991'de İstanbul'da iki "Bakırköy" satırı (muhtemelen seçim
  çevresi bölünmesi, aynı poligon); 2004 yerelde poligonsuz "Karadeniz Ereğli" satırı (seçmen 0).
- **İncelenmeyenler:** 1950–1957 il sınırları (`era1950`, `era1954`) ve 2009 sonrası
  seçimlerin ilçe haritaları bu çalışmada denetlenmedi.
- 1950/1954/1957 genel seçimler il düzeyinde kalır (ülke çapında ilçe kaynağı yok).
