# Türkiye Seçim Haritası

1950-2024 arası tüm genel seçim, yerel seçim, referandum ve cumhurbaşkanlığı seçimi
sonuçlarını gösteren interaktif harita.

## Nasıl açılır

**Tek dosya.** Tüm veri (~17 MB) doğrudan `index.html`'in içine gömülü — sunucu,
internet bağlantısı veya kurulum gerekmez. `index.html`'e çift tıklamanız yeterli,
tarayıcınızda direkt açılır ve internet olmasa da çalışır.

(Not: Sayfa açılışta Google Fonts'tan bir yazı tipi çekmeye çalışır — internet yoksa
bu sessizce atlanır ve tarayıcının varsayılan yazı tipiyle devam eder, harita/veri
işlevselliğini etkilemez.)

## Web'e yayınlama (GitHub Pages)

Bu klasör tek başına statik bir site — repo'ya push edilip Settings → Pages'ten
yayınlanabilir, build adımı gerekmez. Aynı `index.html` hem yerelde hem canlıda
değişiklik yapmadan çalışır.

## Veriyi güncellemek

Bu `index.html`, ayrı veri dosyalarını (`secim_tarihi_data.json`, GeoJSON'lar vb.)
tek dosyada birleştiren bir üretim script'inin çıktısıdır. Veri güncellenince bu
dosya elle düzenlenmez, script yeniden çalıştırılıp `index.html` yeniden üretilir.

## Veri kaynağı ve kapsam

Ayrıntılı kaynak listesi, kapsam sınırları ve bilinen veri kalitesi notları için
`~/Desktop/2023_Secim_Verileri/OKUBENI.md` dosyasına bakın — bu sitedeki veri
oradaki `1950_2023_tam_veri_seti.json` ile birebir aynıdır.
