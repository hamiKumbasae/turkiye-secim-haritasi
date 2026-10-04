# site/ — Türkiye Seçim Tarihi Atlası ön yüzü

**Canlı site: https://hamikumbasae.github.io/turkiye-secim-haritasi/**

Sitenin tek ön yüzü burada. Eskiden ayrı bir repoda (`turkiye-secim-atlasi`) duruyordu.

```
src/index.template.html   HTML iskeleti (CSS/JS ve gömülü veri yer tutucuları)
src/styles/main.css       CSS
src/js/*.js               JS; build.py tanımlı bir sırayla tek <script> içine birleştirir
yontem.html               Kaynaklar ve yöntem sayfası
build.py                  Pages sitesini site/dist/ altına üretir
tests/loading.test.cjs    Playwright testleri (site/dist/ üzerinde)
```

## İki dağıtım, tek kod

- **GitHub Pages** (`python3 site/build.py` → `site/dist/`): yayın verisi `data/`, `geo/` altında ayrı
  dosyalar; sayfa yalnız gerekeni `fetch()` ile indirir. `.github/workflows/pages.yml` main'e her
  birleştirmede derleyip yayınlar; `site/dist/` commit'lenmez.
- **Tek dosya** (`python3 scripts/build.py` → repo kökündeki `index.html`): aynı dosyaları aynı yollarla
  `window.__EMBEDDED_GZ__` içine gömer; `src/js/data-loader.js` gömülü veri varsa onu okur. Çift
  tıklayınca (`file://`) açılır.

Yayın dosyaları `scripts/export_static.py` (`public_files`) ile, kayıtlardaki `kaynak` alanları
çıkarılarak üretilir.

## Yükleme

Açılışta yalnız il sınırları ve seçilen seçim indirilir (~170 KB sıkıştırılmış); ilçe sınırları arka
planda gelir. Mahalle poligonları ilçe başına ayrı dosyadadır (`geo/mahalle/<ilçe>.json`) ve yalnız o
ilçeye inilince indirilir. Hızlı seçim değişikliklerinde yalnız son isteğin sonucu uygulanır;
bağlantı hatalarında **Yeniden dene** sayfayı yenilemeden tekrarlar.

## Yerelde

```bash
python3 site/build.py                         # repo kökünden
python3 -m http.server -d site/dist 8000      # http://localhost:8000
cd site && npm ci && npm test                 # Playwright testleri
```
