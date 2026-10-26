# Türkiye Seçim Haritası — çalışma notları

Yanıtlar Türkçe, kısa. Site: https://hamikumbasae.github.io/turkiye-secim-haritasi/

## Kurallar
- Commit kimliği: `git -c user.name="Hami Kumbasar" -c user.email="73480079+hamiKumbasae@users.noreply.github.com"`; mesaj sonu `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Depo/dal silme yok (kullanıcı yapar). "Block command line pushes" açılmaz.
- Tek dosyalık `index.html`/`yontem.html` commit'lenmez (100 MB sınırı); `python3 scripts/build.py` üretir, sürüm yayımlanınca `release-tek-dosya.yml` ekler.

## Yapı
- Ön yüz `site/src/`; Pages `python3 site/build.py` → `site/dist/` (`pages.yml`, main'e push'ta).
- Veri `data/normalized/` (seçimler, `mahalle/<seçim>.json`), geometri `geo/normalized/mahalle_geo.json`, tarihsel ilçeler `geo/historical/district_splits.json`.
- Yayında mahalle oyları ve sınırları kompakt (`scripts/kompakt.py`: oy satır dizisi, oran/katılım istemcide; sınırlar kayıpsız TopoJSON); `data-loader.js` (`mahalleOyAc`, `topoAc`) açar. Kaynak biçimi değişmez. Tek dosya ~38 MB.
- Mahallede katılım >%100 (YSK kaynaklı): `map.js` katılımı boşaltır, `katilimHesaplanamaz` + `KATILIM_ASIM_NOTU`; açık veri CSV'sinde "not" sütunu.
- Kontroller: `scripts/validate.py`, `tests/validate_elections.py` (19), `node --test tests/*.test.cjs` (14; `kompakt.test.cjs` önce `site/build.py` ister), `cd site && node tests/loading.test.cjs` (30). Değişen veri klasörü için `scripts/regenerate_checksums.py <klasör>`.
- İl toplamı ilçeleri tutmayan 53 kayıt kaynak yayının kendisinde (TÜİK il satırı kendi ilçe satırlarını tutmuyor); il kaydında `ilceFarki` + `not`, denetimde belgeli. Kayda alan eklemek `tests/fixtures/known-validation-issues.json` parmak izini değiştirir.
- 1963–1977 meclis kitapları: `scripts/pipelines/tuik_arsiv/extract_mahalli_1963_1977.py <seçim> [tablo]` (KITAPLAR; görüntüden ikinci okuma `goruntu_okuma.py`, tesseract önbelleği `.cache/tuik/`) → katman → `merge_mahalli.ek_meclis` (yalnız o seçim; `main` başkanlığı da yazar) → `build_meclis_harita.py` (`DIE_YILLARI`) + `election-config.js` `OYLAMA_YILLARI`. 1973 ve 1977 yapıldı; 0015740 taramasında kitap s.189–194 yok.
- Ek kayıtlar (`data/normalized/ek/`): `build_ek_kayitlar.py` yeniden çalıştırılırsa sonradan güncellenen geomId'leri eski haline döndürür; değişikliği dosyaya hedefli uygula. Senato PDF sütun kaymaları `extract_senato.py` `ELLE_DUZELTME` tablosunda.
- Denetim: `python3 scripts/veri_denetimi.py --md docs/rapor/VERI_DENETIMI.md --csv-klasor docs/rapor/veri_denetimi`. CI `--kontrol docs/rapor/veri_denetimi` ile kayıtlı listede olmayan yeni bulguda başarısız olur; veri düzeltince listeyi bu komutla yenile.

## Veri hattı (mahalle)
- YSK açık veri yalnız GitHub Actions'tan erişilir; sonuç `::notice` ile okunur (`gh api .../check-runs/<job>/annotations`), dosyalar veri dalına itilir, `git fetch origin +dal:refs/remotes/origin/dal` + `git checkout origin/dal -- yol`.
- İş akışları: `ysk-mahalle-cek.yml` (muhtarlık), `tkgm-mahalle-cek.yml`, `osm-mahalle-cek.yml`, `belediye-mahalle-cek.yml`, `osm-yer-cek.yml` (OSM köy/mahalle noktaları; elle, `iller` girdisiyle kısmi; `osm-yer-veri` dalına ekler).
- Eşleştirme: `scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py [kontrol|uygula] <seçimler>`; sıra belediye → mevcut → OSM → TKGM → OSM konumu (eski adlı TKGM birimi, yalnız bire bir ve ad destekli); sentetik (tarihsel) ilçeler halef havuzuyla. 15 seçimin hepsi işlendi (2009–2024). Eşleşmeyen muhtarlık haritada boş kalır (kullanıcı kararı; toplu "konumu belirsiz" alan yok). Yeniden çalıştırma tekrarlanabilir: daha önce verilmiş OSM sınırı yalnız aynı adlı muhtarlığa gider.
- Lisanslar: TKGM açık lisans dışı; OSM ODbL; Bursa/Sakarya belediye lisansı (atıf). Bkz. `LICENSE-DATA.md`.

## Yönetim raporu
`docs/rapor/VERI_DENETIMI_YONETIM.md` (eylem planı tablosu orada; Claude Docs artifact silindi). Veri ve yöntem raporu: `docs/rapor/VERI_VE_YONTEM.md`.

## Durum
Proje kapandı (21 Ekim 2026). Yalnız yeni seçim (normal takvimde 2028 genel, 2029 yerel) ya da hata bildirimi olursa açılır.
- İsteğe bağlı, yapılmadı: 1994–1999 meclis/belde oy toplamları, 10 kayıtta kazanan "Diğer", 2009 Ağın/Kadışehri yenilemesi haritada, Gaziantep belediye sınırları (SSL hatası), Hatay/Van için TUCBS e-Devlet başvurusu (kullanıcı).
