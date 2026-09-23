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

Mahalle/muhtarlık düzeyi oy verisi (15 seçim, açık haliyle ~75MB) sayfa
açılışında DEĞİL, kullanıcı gerçekten bir ilçeye tıklayıp o yılın mahalle
verisine indiğinde, sadece o yıl için lazy-load edilir (bkz. `src/js/
data-loader.js` + `map.js`). Mahalle poligonları (`mahalle_geo.json`, ~17MB
açık, yıllar arası paylaşımlı) hâlâ eager yükleniyor — bu bilinçli bir
basitleştirme: il/ilçe bazında da bölünebilirdi ama görece küçük olduğu ve
her yeni seçimde büyümediği (sadece yeni ilçe eklenince büyür) için şimdilik
gerekli görülmedi.

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

src/index.template.html   HTML iskeleti (veri hariç, placeholder'lı)
src/styles/main.css        Uygulamanın tüm CSS'i
src/js/*.js                 Uygulamanın JS'i, 11 dosyaya bölünmüş (data-loader,
                             election-config, state, seatbar, map, tooltip,
                             detail-panel, search, nav, table, app)
scripts/build.py            Yukarıdakileri birleştirip index.html üretir
scripts/validate.py         build.py'ye gömülü hızlı yapısal kontrol (gate)
tests/validate_elections.py Ayrı, yavaş/analitik kontrol seti
.github/workflows/validate.yml  Her push/PR'da validate.py + validate_elections.py +
                                 build.py + "index.html güncel mi" kontrolü

index.html (repo kökü)   TEK GERÇEK/ÇALIŞAN DOSYA — build.py'nin çıktısı, commit'lenir
```

`src/js/*.js` gerçek ES modülleri değil — build.py bunları tanımlı bir
sırayla tek `<script>` içine metin olarak birleştirir (aynı paylaşımlı
closure/state korunur). Kaynakta ayrı dosyalar, dağıtımda hâlâ tek dosya.

Her klasörün kendi `PROVENANCE.md`'si var (nereden geldiği, nasıl
doğrulandığı). Kaynakların tam listesi için bkz. [`SOURCES.md`](SOURCES.md)
(okunabilir) ve [`sources.yml`](sources.yml) (makine-okunur, her seçimin
birincil/yedek kaynağı + bilinen sorunlar).

## Veriyi güncellemek

1. `data/normalized/`, `geo/normalized/`, `src/styles/`, `src/js/` veya
   `src/index.template.html` altındaki ilgili dosyayı düzenleyin (yeni bir
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
`scripts/legacy/` altındaki iki script (mimarinin eski, ters yönlü hâline
ait) artık kullanılmıyor, sadece tarihsel referans.

## Web'e yayınlama (GitHub Pages)

`index.html` repo kökünde olduğu için GitHub Pages'in "Deploy from a branch"
modu (kök dizin) ek bir adım gerektirmeden çalışır — Settings → Pages'ten
etkinleştirmeniz yeterli.

## Bilinen kapsam sınırları

- 1950-1977 genel seçimlerinde (ve 1961/1982/1987/1988/2007 referandumlarında)
  ilçe düzeyi veri yok, sadece il düzeyi — bu dönemde "seçim çevresi" il'in
  kendisiydi, ilçe bazlı sistem hiç var olmadı (kaynak eksikliği değil).
- 1957/1961 genel seçimlerinde Sakarya'nın vekil dağılımı yok (YSK'nin
  1950-1977 arşivinde bu il hiç yok, bkz. `data/raw/ysk/1950-1977/PROVENANCE.md`).
- 2002 Siirt ilçe kırılımı bozuk (kaynak hatası, düzeltilemedi — bkz. `sources.yml`).
- 2014 yerel seçiminde BDP il/ilçe verisi hatalı (gerçek oylar mahalle
  düzeyinde "HDP" altında bulundu, il/ilçe düzeyi düzeltilmedi).
- 2010 referandumunun ilçe düzeyi oy SAYILARI tahmini (`~300 oy/sandık`
  varsayımı) — yüzdeler gerçek.
- `data/raw/{haberturk,wikipedia}/` ve `data/raw/ysk/`'nin mahalle-düzeyi
  kısmı şu an boş — bu kaynakların orijinal ham çıktısı hiç saklanmamış veya
  yeniden üretilmedi. Ayrıntı: [`NOTICE.md`](NOTICE.md).

Tam liste ve her seçimin ayrıntısı için [`SOURCES.md`](SOURCES.md).
- 1984 öncesi 6 yerel seçimin (1950, 1955, 1963, 1968, 1973, 1977) sadece
  il merkezi düzeyi var, ilçeler yok — bkz.
  [`SECIM_TAKVIMI.md`](SECIM_TAKVIMI.md) (1950-2024 arası tüm seçimlerin tam
  takvimi ve bu projedeki kapsam durumu).
