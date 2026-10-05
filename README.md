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

### Tarihsel ilçe sınırları

Bir seçimden sonra kurulan ilçe, o seçimde bağlı olduğu ilçenin poligonuna katılır. Her ilçenin
nereye ve neden bağlandığı `geo/historical/idari/ilce_eslesme/<seçim>.csv` tablosunda; güven
sütunu `kesin` (kanun/sayım kaynağı), `yaklasik` (%70 ve üzeri birim çoğunluğu) ya da `kaba`
(en büyük pay veya en uzun sınır komşusu). Dönem il sınırları (`geo/historical/turkiye_il_sinirlari_era*.geojson`) seçim
verisindeki ilçe-il bağlılığından üretilir.

Tarihsel sınırları yeniden üretmek için yalnız
`scripts/pipelines/historical_geo/tarihsel_sinirlari_uret.py` kullanın: bütün adımları doğru
sırayla çalıştırır (seçim katmanını geri al → `apply_idari_merges.py` → İstanbul → her seçim için
`build_ilce_secim.py` → `ortusmeleri_temizle.py` → il sınırları → meclis → rapor → checksum →
`build.py`) ve idempotenttir. Tek tek betikleri elle ve başka sırayla çalıştırmayın. Ayrıntı:
[`geo/historical/idari/README.md`](geo/historical/idari/README.md); güncel kapsam sayıları
`docs/rapor/`.

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
  resmî bir ilçe kaynağı bulunamadı. 1961–1987 genel seçimlerinin ve 1961/1982/1987/1988
  referandumlarının ilçe düzeyi TÜİK yayınlarından (bkz. `scripts/pipelines/genel_ilce_1961_1987/`).
- 1957/1961 Sakarya vekil dağılımı YSK'nin 1950–1977 arşivinde yok; ikincil arşivden tamamlandı
  (bkz. `data/normalized/PROVENANCE.md`).
- 2002 Siirt: il ve ilçe sonuçları, iptal edilip 9 Mart 2003'te yenilenen seçimin resmî sonucudur (YSK ve TÜİK aynı rakamı veriyor; hata değil — bkz. `sources.yml`).
- `data/raw/{haberturk,wikipedia}/` ve `data/raw/ysk/`'nin mahalle-düzeyi
  kısmı şu an boş — bu kaynakların orijinal ham çıktısı hiç saklanmamış veya
  yeniden üretilmedi. Ayrıntı: [`NOTICE.md`](NOTICE.md).
- 2009 yerelde Ağın ve Kadışehri başkanlık seçimi 29 Mart'ta iptal edilip 7 Haziran'da yenilendi:
  haritada 29 Mart sonucu (2019 İstanbul gibi), yenileme `data/normalized/ek/yenileme_ara/`'da.
- 1950 ve 1955 yerel seçimlerinde ilçeler için yalnız kazanan parti var (oy sayısı
  yok); 1963–1977 yerel seçimlerinde ilçe belediye başkanlığı satırları var — bkz.
  [`SECIM_TAKVIMI.md`](SECIM_TAKVIMI.md) (1950-2024 arası tüm seçimlerin tam
  takvimi ve bu projedeki kapsam durumu).

Tam liste ve her seçimin ayrıntısı için [`SOURCES.md`](SOURCES.md).

## Bilinen eksikler

Her seçimin (yerel seçimlerde başkanlık, belediye meclisi, il genel meclisi ayrı) il/ilçe kapsamı,
kalite sınıfı, en iyi kaynağı ve araştırma önceliği: [`docs/rapor/KAPSAM_TABLOSU.md`](docs/rapor/KAPSAM_TABLOSU.md)
(`python3 scripts/rapor/kapsam_tablosu.py` üretir). Nerelere bakıldığı:
[`data/kaynaklar/ARASTIRMA_KAYDI.md`](data/kaynaklar/ARASTIRMA_KAYDI.md).

Aşağıdakiler depodaki veriyle çözülemiyor; her biri yeni bir kaynak gerektirir:

- **Yerel meclis sonuçları (1984):** taranmış DİE kitabında okunamayan ya da toplamı tutmayan satırlar
  boş (belediye meclisi %48, il genel meclisi %44 eksik; sayılar kapsam tablosunda). 1994, 1999 ve 2004
  boşlukları YSK'nin dijital tablolarıyla dolduruldu; bu yıllarda kalan boş satırlar haritada sonradan
  bölünen il merkezleri (il genel meclisinde seçim çevresi bütün Merkez ilçesiydi) ve başkanlık
  haritasında birleştirilmiş beldeler. 1963–1977 meclis ve il genel meclisi sonuçlarının DİE kitapları
  depoda (`data/raw/tuik/mahalli-kitap/`) ama henüz okunmadı; 1950/1955 için DİE kitabı yok.
- **1963–1977 belediye başkanlığı (Vikipedi):** DİE kitaplarıyla karşılaştırıldı
  ([`docs/rapor/KITAP_DOGRULAMA_1963_1977.md`](docs/rapor/KITAP_DOGRULAMA_1963_1977.md)). Kitabın
  yüzdesi ya da toplamıyla desteklenen farklar ve oyları geniş ölçüde farklı satırlar orada listeli;
  veriye işlenmedi.
- **Kaba eşlemeler:** sonradan kurulan ve birden çok eski ilçeden pay alan bazı ilçeler (ör. Çukurova,
  Körfez, Aliağa, Ondokuzmayıs) en büyük paya ya da komşuluğa göre bütünüyle tek ilçeye bağlı
  (`geo/historical/idari/ilce_eslesme/*.csv`, güven `kaba`); köy düzeyinde kaynak bulunursa bölünebilir.
- **Ankara Merkez (1961–1983):** ayrı ilçeydi ama sınırı kaynakta yok; haritada poligonu yok.
- **2009 yerel, Kadışehri belediye meclisi:** ilçede 29 Mart seçimi iptal edilip 7 Haziran'da
  yenilendi; ilçe merkezi meclis sonucu YSK açık verisinde ve Vikipedi'de yok.
- 1950/1954/1957 genel seçimler il düzeyinde kalır (ülke çapında ilçe kaynağı bulunamadı).

Bilgi notu: 2011'de BDP adayları bağımsız girdi. İl satırı bu oyları "BDP" sayan yedi ilde
(Diyarbakır, Hakkari, Mardin, Muş, Van, Batman, Şırnak) ilçe satırları da "BDP"
(`election_import/etiket_2011_bdp.py`); diğer illerde blok adayları "Bağımsız" içinde.
