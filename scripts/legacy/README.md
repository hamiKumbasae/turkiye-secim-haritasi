# Tarihsel script'ler — artık kullanılmıyor

Bu klasördeki script'ler, `raw → normalized → build` mimarisi kurulmadan
ÖNCEKİ akışa ait. İkisi de artık **yanlış yönde** çalışıyor: `index.html`'i
"kaynak" sayıp oradan veri okuyorlar, oysa güncel mimaride `index.html`
`scripts/build.py`'nin **ürettiği** dosya.

İkisi de yanlışlıkla çalıştırılmayı zorlaştırmak için `--i-know-this-is-backwards`
bayrağı olmadan çalışmayı reddediyor.

- **`normalize_from_old_index.py`** (eski adı `scripts/normalize.py`) — bir
  kerelik geçiş kanıtı olarak yazıldı (2026-09-22, commit `895494e`): eski,
  elle üretilmiş `index.html`'den `data/normalized/` + `geo/normalized/`'i
  kayıpsız olarak çıkardı. O geçiş tamamlandı, script artık gerekmiyor.
- **`gom_ve_sikistir.py`** — mahalle pipeline'ının ilk sürümünde, yeni bir
  yılın mahalle verisini doğrudan `index.html`'in gömülü blobuna spliceleyen
  script. Yerini `scripts/mahalle-veri-pipeline/transform/import_mahalle.py`
  aldı (o, `data/normalized/mahalle/` + `geo/normalized/mahalle_geo.json`'a
  yazıp `scripts/build.py`'yi tetikliyor — mimariyle tutarlı).

Silinmediler, çünkü nasıl çalıştıklarını anlamak (özellikle osm_id bazında
geometri tekilleştirme mantığı) gelecekte faydalı olabilir. Ama aktif iş
akışının bir parçası değiller — normal geliştirme sırasında bu klasöre hiç
girmeniz gerekmez.
