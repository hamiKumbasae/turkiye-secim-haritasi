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

src/index.template.html   Uygulamanın HTML/CSS/JS'i (veri hariç, ~66KB)
scripts/build.py           Yukarıdakileri birleştirip index.html üretir
scripts/validate.py         build.py'ye gömülü hızlı yapısal kontrol (gate)
tests/validate_elections.py Ayrı, yavaş/analitik kontrol seti

index.html (repo kökü)   TEK GERÇEK/ÇALIŞAN DOSYA — build.py'nin çıktısı, commit'lenir
```

Her klasörün kendi `PROVENANCE.md`'si var (nereden geldiği, nasıl
doğrulandığı). Kaynakların tam listesi için bkz. [`SOURCES.md`](SOURCES.md)
(okunabilir) ve [`sources.yml`](sources.yml) (makine-okunur, her seçimin
birincil/yedek kaynağı + bilinen sorunlar).

## Veriyi güncellemek

1. `data/normalized/` veya `geo/normalized/` altındaki ilgili dosyayı
   düzenleyin (yeni bir seçim ekliyorsanız yeni bir `data/normalized/
   mahalle/<yil>.json` gibi).
2. ```bash
   python3 scripts/build.py
   ```
   Bu, önce `scripts/validate.py`'nin yapısal kontrollerinden geçirir (hatalı
   veri build'i durdurur), sonra `index.html`'i yeniden üretir.
   Deterministiktir: aynı veriden iki kez çalıştırınca bayt-bayt aynı çıktı.
3. İsteğe bağlı, daha kapsamlı kontrol:
   ```bash
   python3 tests/validate_elections.py
   ```
4. `index.html`'i commit'leyin.

`scripts/mahalle-veri-pipeline/` klasörü, mahalle düzeyi verinin YSK Açık
Veri Portalı'ndan nasıl çekildiğinin/işlendiğinin kaydı — yeni bir seçim
eklerken oradaki script'ler `data/normalized/mahalle/` için ham girdiyi
üretir (bkz. o klasörün kendi README'si).

## Web'e yayınlama (GitHub Pages)

`index.html` repo kökünde olduğu için GitHub Pages'in "Deploy from a branch"
modu (kök dizin) ek bir adım gerektirmeden çalışır — Settings → Pages'ten
etkinleştirmeniz yeterli.

## Bilinen kapsam sınırları

- 1950-1961 genel seçimlerinde vekil/sandalye dağılımı yok (kaynakta hiç yok).
- 1965-1987 genel seçimlerinde ilçe düzeyi veri yok, sadece il düzeyi.
- 2002 Siirt ilçe kırılımı bozuk (kaynak hatası, düzeltilemedi — bkz. `sources.yml`).
- 2014 yerel seçiminde BDP il/ilçe verisi hatalı (gerçek oylar mahalle
  düzeyinde "HDP" altında bulundu, il/ilçe düzeyi düzeltilmedi).
- 2010 referandumunun ilçe düzeyi oy SAYILARI tahmini (`~300 oy/sandık`
  varsayımı) — yüzdeler gerçek.
- `data/raw/{ysk,haberturk,wikipedia}/` şu an boş — bu kaynakların orijinal
  ham çıktısı hiç saklanmamış veya yeniden üretilmedi. Ayrıntı: [`NOTICE.md`](NOTICE.md).

Tam liste ve her seçimin ayrıntısı için [`SOURCES.md`](SOURCES.md).
