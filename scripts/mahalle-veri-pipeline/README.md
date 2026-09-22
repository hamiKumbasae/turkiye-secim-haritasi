# Mahalle Düzeyi Veri Pipeline'ı

`index.html`'deki il→ilçe→mahalle haritasını besleyen mahalle (muhtarlık) düzeyi
seçim verisinin nasıl üretildiğinin kaydı. 15 seçim (4 Cumhurbaşkanlığı, 5 Genel,
4 Yerel, 2 Referandum) için bu pipeline'la veri çekilip haritaya gömüldü.

## Veri kaynakları

- **Oy verisi:** [YSK Açık Veri Portalı](https://acikveri.ysk.gov.tr) — resmi,
  genel kullanıma açık API (`getSecimSandikSonucList` uç noktası). Sandık/muhtarlık
  düzeyinde sonuç veriyor, 2009 sonrası tüm seçimleri kapsıyor. robots.txt yok,
  toplu/programatik erişimi yasaklayan bir politika bulunmuyor.
- **Mahalle sınırları (poligonlar):** İki kaynağın birleşimi —
  - [`ttezer/turkiye-harita-verisi`](https://github.com/ttezer/turkiye-harita-verisi)
    (25 ilde belediye açık verisi/MAKS kaynaklı, daha yoğun/güvenilir — tercih edilen)
  - [`osadikoglu/turkey-admin-units-osm`](https://github.com/osadikoglu/turkey-admin-units-osm)
    + OpenStreetMap (kalan 56 ilde, OSM'in mahalle-poligonu çizdiği yerler kadar)

## Kurulum

```bash
cd scripts/mahalle-veri-pipeline
npm install
npx playwright install chromium
```

## Pipeline aşamaları

```
eslesme/01_osm_mahalle_poligonlari.py   OSM'den (osmium ile ayrılmış .osm.pbf) mahalle poligonlarını çıkarır
eslesme/02_ttezer_mahalle_poligonlari.py ttezer'in il/ilçe bazlı dosyalarını tek GeoJSON'da birleştirir
eslesme/03_ysk_ilce_eslestir.py         YSK'nin ilçe listesini projenin kendi geomId şemasıyla eşleştirir
eslesme/04_hedef_ilce_listesi.py        Yukarıdakilerden, oy verisi çekilecek ilçe listesini (~651 ilçe) üretir
                                         (bkz. all_mahalle_targets.json — hazır, tekrar üretmeye gerek yok)

fetch/fetch_muhtarlik_votes.js          Aday-bazlı seçimler (CB, Referandum) için YSK'den muhtarlık verisi çeker
fetch/fetch_muhtarlik_parti.js          Parti-bazlı seçimler (Genel, Yerel) için çeker — ayrıca il başına
                                         parti→sütun eşlemesi gerekir (bkz. parti-sutun-eslemeleri/)

transform/build_mahalle_aday_bazli.py   Çekilen veriyi mahalle poligonlarıyla eşleştirip
transform/build_mahalle_parti_bazli.py  {geomId: [{id, ad, geometry, oy, ...}]} formatına çevirir

transform/import_mahalle.py             Yukarıdakinin çıktısını data/normalized/mahalle/<yıl>.json +
                                         geo/normalized/mahalle_geo.json'a otomatik yerleştirir, doğrular
```

Ara çıktılar (fetch/eslesme aşamalarının dosyaları) varsayılan olarak
`.work/` altında tutulur (`.gitignore`'da) — farklı bir konum için
`MAHALLE_WORKDIR` ortam değişkenini kullanın.

## Yeni bir seçim eklemek için (örn. 2028 sonrası)

1. `fetch/fetch_muhtarlik_votes.js` veya `fetch_muhtarlik_parti.js` içindeki
   `node ... <secimId> <secimTuru> <outFile> eslesme/all_mahalle_targets.json ['<majorMap>']`
   komutunu yeni seçimin `secimId`'siyle çalıştırın (secim_ID'yi bulmak için
   YSK'nin `getSecimDetayList` uç noktasına bakın).
2. Parti-bazlı bir seçimse, önce `getSandikSecimSonucBaslikList` ile o seçimin
   parti→sütun eşlemesini çıkarıp `transform/build_mahalle_parti_bazli.py`'deki
   `CONFIGS` sözlüğüne yeni bir giriş ekleyin (bkz. `parti-sutun-eslemeleri/`
   klasöründeki örnekler).
3. `transform/build_mahalle_aday_bazli.py <yil_anahtari>` veya
   `transform/build_mahalle_parti_bazli.py muhtarlik_..json <yil_anahtari>` ile
   işleyin — bu `mahalle_<yil_anahtari>.json` üretir.
4. ```bash
   python3 scripts/mahalle-veri-pipeline/transform/import_mahalle.py \
       --year <yil_anahtari> --input mahalle_<yil_anahtari>.json --build
   ```
   Bu, oy verisini `data/normalized/mahalle/<yil_anahtari>.json`'a, yeni
   geometriyi `geo/normalized/mahalle_geo.json`'a (osm_id bazında, var olanı
   koruyarak) otomatik yazar, `scripts/validate.py` ile doğrular ve
   `--build` ile kök `index.html`'i yeniden üretir. Elle dosya
   kopyalamaya gerek yok.

## Önemli notlar / bilinen sınırlar

- **Kapsam kentsel bölgelere kayık.** Mahalle poligonlarının çoğu büyükşehir/il
  merkezlerinden geliyor (ttezer + OSM'in en yoğun haritalandığı yerler); kırsal
  köylerin çoğunun poligonu yok. Ulusal parti oranları hesaplanırken bu örneklem
  her zaman muhalefet/CHP tarafına birkaç puan kaymış çıkıyor — bu beklenen bir
  sapma, veri hatası değil (bkz. 2017 referandumunda büyükşehirlerde gerçekten
  Hayır'ın önde bitmiş olması).
- **YSK'nin sisteminde 2009 öncesi hiçbir seçim yok** (portalın kendi beyanı:
  "since 2009"). Öncesi için proje il/ilçe düzeyinde Wikipedia/mertnuhoglu
  kaynaklarını kullanmaya devam ediyor, mahalle düzeyine inilemiyor.
- **Rate/hız:** Her `fetch_*` çalıştırması ~651 istek, istek başı ~120ms bekleme
  ile saniyede ~2-3 istek civarında — bu oturumda toplam ~5000 istek atıldı,
  hiç hata/blok alınmadı.
