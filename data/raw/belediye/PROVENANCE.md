# Belediye açık veri portalları — mahalle sınırları

**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_belediye_mahalle.py` (CKAN `package_show` + kaynak dosya).
**Çekildi:** 2026-10-21, GitHub Actions üzerinde (`.github/workflows/belediye-mahalle-cek.yml`).
Her il için `<plaka>.meta.json` portal, paket, lisans ve kaynak adresini saklar.

| Dosya | Kurum | Lisans | Kaynak | Güncelleme |
|---|---|---|---|---|
| 16.geojson | Bursa Büyükşehir Belediyesi | Bursa Açık Veri Lisansı (acikyesil.bursa.bel.tr/license) | acikyesil.bursa.bel.tr, "Mahalle Sınırları" | 2026-08-27 |
| 54.geojson | Sakarya Büyükşehir Belediyesi (CBS Şube Müdürlüğü) | Sakarya Açık Veri Lisansı (veri.sakarya.bel.tr/license) | veri.sakarya.bel.tr, "Mahalle Sınırları" | 2025-08-07 |

Her iki lisans da kopyalama, yayımlama, değiştirme ve ticari kullanıma izin verir; koşul kaynağın atıfla
gösterilmesi ve mümkünse lisansa bağlantı verilmesidir (aynı lisansla paylaşma şartı yok).

Gaziantep Büyükşehir'in "Mahalle Sınır Alanları" veri seti, portalın SSL sertifika zinciri eksik olduğu için
indirilemedi (o ilde eşleşmeyen seçmen zaten ~3 bin).

## Dönüşüm

Dosyalar olduğu gibi saklanır. Eşleştirme betiği (`transform/tkgm_muhtarlik_esle.py`, `belediye_yukle`)
koordinatları WGS84'e çevirir, 0.0001° ile sadeleştirir. Bursa dosyası EPSG:2320 (ED50) etiketli ama
koordinatları TUREF/TM30 (EPSG:5254): 2320 olarak okununca aynı adlı TKGM sınırlarına göre medyan ~180 m
kayıyor, 5254 ile kayma 10 m'nin altına iniyor; bu yüzden 5254 kullanılır. Haritadaki anahtar `b<plaka>-<kimlik>`.
Belediye verisi olan ilçelerde bu sınırlar ilk sırada kullanılır.
