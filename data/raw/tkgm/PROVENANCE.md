# TKGM mahalle/köy sınırları (81 il)

**Kaynak:** T.C. Tapu ve Kadastro Genel Müdürlüğü (TKGM), idari yapı servisi
`https://cbsapi.tkgm.gov.tr/megsiswebapi.v3/api/idariYapi` (Parsel Sorgu uygulamasının kullandığı,
herkese açık servis): `ilListe` → `ilceListe/<il id>` → `mahalleListe/<ilçe id>`.
**Script:** `scripts/pipelines/mahalle_veri/fetch/fetch_tkgm_mahalle.py`.
**Çekildi:** 30 büyükşehir 2026-10-19, kalan 51 il 2026-10-20 (run 39426266713); GitHub Actions üzerinde
(`.github/workflows/tkgm-mahalle-cek.yml`).

**Lisans:** Servisin yayımlanmış bir açık veri lisansı yoktur. Bu klasör ve bundan türetilen poligonlar
(`geo/normalized/mahalle_geo.json` içinde `k<tkgm_id>` anahtarlı olanlar) deponun CC BY-SA 4.0 /
ODbL kapsamının **dışındadır**; sitede kaynak gösterilerek kullanılır (bkz. `LICENSE-DATA.md`).

## İçerik

- `<plaka>.geojson`: her birim için `{tkgm_id, ad, ilce, ilce_tkgm_id, geomId}`; `geomId` projenin ilçe
  kimliği (ilçe adı `fold` ile eşlenir; Samsun "19 Mayıs" = Ondokuzmayıs ve "Kemalpaşa (Artvin)",
  eşleştirme scriptinde alias).
- `ozet_<plaka>.json`: il başına birim / geometrisiz birim sayısı, eşleşmeyen ilçe, süre.
- 81 il, 49.825 birim; 47.057'sinin geometrisi var (geri kalanı serviste boş döner).

Geometri sadeleştirildi: Douglas-Peucker 0.0001° (~10 m, topoloji korunarak), 4 ondalık basamak.

## Bilinen sınırlar

TKGM birimleri **kadastro mahallesidir**, güncel idari mahalle (muhtarlık) değildir. Şehir
merkezlerinde bir kadastro birimi birkaç idari mahalleyi kapsayabilir (ör. İstanbul Gaziosmanpaşa'da
4 birim); bazı köyler kadastro bölümlerine ayrılmıştır ("Büyüktatlar/Aliçli"); eski köy adları
parantez ya da tireyle yazılır ("Gerede(Çamalan)"). Bu yüzden site önce mevcut OSM/ttezer
poligonlarını kullanır, TKGM'yi yalnız boşlukları doldurmak için ekler
(`scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py`).
