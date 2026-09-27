# Arşiv: mahalle düzeyinde tarihsel ilçe bölüşümü (Faz 4b/4c)

**Durum:** Denendi, 2026-09-27'de haritadan kaldırıldı. Gerekçe: bölüştürülemeyen kısımlar
ilçelerin içinde yarım taralı parçalar bıraktı ve harita okunaksızlaştı. Yerine ilçe
düzeyinde kural kondu: birden çok eski ilçeden kurulan ilçe, ana kaynağı Merkez ilçe
(≥ %70) ise bütünüyle Merkez'e katılır; diğerleri bütün poligon hâlinde, nedeni yazılı
gösterilir (`scripts/pipelines/historical_geo/apply_idari_merges.py`).

Son çalışan hâl git etiketinde: **`arsiv/mahalle-bolusumu`** (commit 8b7fa5e).

## Ne yapıyordu

Birden çok eski ilçeden kurulan bir ilçenin (ör. Arnavutköy = Gaziosmanpaşa'nın 26 +
Çatalca'nın 18 + Küçükçekmece'nin 1 birimi) alanını, bugünkü mahalle poligonlarıyla eski
ilçeleri arasında paylaştırıyordu. Her eski ilçenin payı onun tarihsel poligonuna
eklenir, paylaştırılamayan kısım taralı çizilirdi.

## Kaynaklar

| Kaynak | Ne verir |
|---|---|
| Kuruluş kanunlarının ek listeleri (5747, 6360, 3392, 3644 ...; `data/kaynaklar/resmi_gazete/ilce_kurulus/`) | Yeni ilçeye giden her köy/mahalle/beldenin eski ilçesi ya da eski belediyesi |
| DİE 2004 yerel seçim kitabı Tablo 9 (`data/kaynaklar/tuik/yerel/2004yerel/`) | İlk kademe belediyesinin (beldenin) ilçesi |
| DİE 1999 ve 2004 yerel seçim kitapları | Sayımlarda olmayan beldeler (Bahçeşehir) |
| DİE nüfus sayımı kitapları: 1960 (0015128), 1985 (0013062), 1990 (0013349), TÜİK kütüphanesi | Köy/belde → ilçe/bucak bağlılığı; iki sayım arasında ilçe değiştiren köyler |
| Bugünkü mahalle poligonları (`geo/normalized/mahalle_geo.json`) | Paylaştırmanın geometrisi |

## Mantık (sıkıştırılmış)

1. Bugünkü mahalle adı kanundaki birimle eşleşir (aynı ad; belde "Merkez"i = belde adı;
   adında belde/birim adı geçen mahalle; "X Mahallesinin ... kısmı" satırlarından ad).
2. Birimin ilçesi dönem dönem: iki sayım arasındaki seçimlerde ancak iki sayımda da aynı
   ilçedeyse atanır (ör. Tayakadın 1960 Çatalca, 1985 Gaziosmanpaşa → 1961–1984 belirsiz).
3. İşaretli çıkarımlar: tek eski ilçenin içinde kalan eşleşmeyen alan (`cevrelenmis`);
   listedeki bütün birimler tek ilçedense geri kalan (`liste-tumleyeni`); merkez kasabanın
   adsız mahalleleri (`merkez-kasaba`).
4. Kalan alan `BELIRSIZ-*` (taralı), eski ilçesi o seçimde satır olmayan parça `PARCA-*`.

Güvenlik ilkesi: sayım dizini OCR'dan okunduğu için yalnız "aynı mı" sorusunu yanıtlar;
hata taralı alanı büyütür, yanlış ilçeye boyamaz.

## Sonuçlar (arşivlenmeden önce)

- İstanbul'da boş alan: 1961–1983 %25 → %6, 1995–2007 %11.7 → %2.1.
- İstanbul dışında mahalle poligonu olan 22 çok kaynaklı ilçede boş alan %11–26 azaldı.
- Çözülemeyen: 1987 öncesi Kağıthane, Ümraniye, Esenler (şehir içi mahallelerin eski
  ilçesi hiçbir kaynakta yok); büyükşehir dışı ~26 ilçe (köy poligonu yok).

## Dosyalar

- `scripts/build_mahalle_bolusumu.py` — bölüşüm (İstanbul için elle `DONEMSEL` tabloları,
  diğerleri sayım dizininden otomatik).
- `scripts/extract_sayim_koyleri.py` — sayım kitaplarından köy → ilçe dizini (kitapları
  TÜİK'ten indirip SHA-256 ile doğrular; `.cache/`).
- `veri.tar.gz` — üretilmiş çıktılar: `geo/historical/idari/mahalle_bolusumu.{json,geojson}`,
  `data/kaynaklar/tuik/nufus_sayimi/{1960,1985,1990}_koyler.json`.

## Geri getirmek

`git checkout arsiv/mahalle-bolusumu -- scripts/pipelines/historical_geo src/js tests`
ve `tar -xzf arsiv/mahalle-bolusumu/veri.tar.gz`, ardından `apply_idari_merges.py`,
`scripts/build.py`. Ön yüzdeki `BELIRSIZ-*`/`PARCA-*` çizimi ve ipuçları da o etikettedir.

## Hukuki not

DİE/TÜİK kitaplarının PDF'leri yalnız özel depoda ya da önbellekte tutulur. DİE 1999 yerel
seçim kitabında "izinsiz çoğaltılamaz ve dağıtılamaz" notu var; PDF'ler herkese açık bir
depoya konmamalı. Türetilmiş bilgi (köyün ilçesi) kaynak gösterilerek kullanılır.
