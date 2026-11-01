# Türkiye Seçim Haritası — çalışma notları

Yanıtlar Türkçe, kısa. Site: https://hamikumbasae.github.io/turkiye-secim-haritasi/

## Kurallar
- Commit kimliği: `git -c user.name="Hami Kumbasar" -c user.email="73480079+hamiKumbasae@users.noreply.github.com"`; mesaj sonu `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Depo/dal silme yok (kullanıcı yapar). "Block command line pushes" açılmaz.
- Tek dosyalık `index.html`/`yontem.html` commit'lenmez (100 MB sınırı); `python3 scripts/build.py` üretir, sürüm yayımlanınca `release-tek-dosya.yml` ekler.

## Yapı
- Ön yüz `site/src/`; Pages `python3 site/build.py` → `site/dist/` (`pages.yml`, main'e push'ta).
- Veri `data/normalized/` (seçimler, `mahalle/<seçim>.json`), geometri `geo/normalized/mahalle_geo.json`, tarihsel ilçeler `geo/historical/district_splits.json`.
- İl/ilçe katmanı (2026-11-01): `scripts/pipelines/ilce_katmani/` — `ilce_duzeltme_sec.py` (OSM `admin_level=6` mı HDX mi; TKGM hakem; `geo/normalized/ilce_duzeltme.json`) → `build_ilce_katmani.py --ham <ttezer dist/geojson/districts.geojson>` (düzlemsel bölümleme + ortak yay sadeleştirme, il = ilçelerin birleşimi; İstanbul aynen) → `tarihsel_yeniden_tabanla.py --eski <önceki ilçe dosyası>` (HIST birleşimleri + era il dosyaları) → mahalle eşleştirmesi (konum kuralı ilçe katmanına bağlı). OSM ilçe verisi `osm-ilce-cek.yml` → `osm-ilce-veri` dalı. `tarihsel_sinirlari_uret.py` main'de çalışmıyor (İstanbul adımı, seçim verisine de yazar). Rapor `docs/rapor/ILCE_KATMANI_2026-11-01.md`.
- Yayında mahalle oyları ve sınırları kompakt (`scripts/kompakt.py`: oy satır dizisi, oran/katılım istemcide; sınırlar kayıpsız TopoJSON); `data-loader.js` (`mahalleOyAc`, `topoAc`) açar. Kaynak biçimi değişmez. Tek dosya ~45 MB.
- Mahallede katılım >%100 (YSK kaynaklı): `map.js` katılımı boşaltır, `katilimHesaplanamaz` + `KATILIM_ASIM_NOTU`; açık veri CSV'sinde "not" sütunu.
- Kontroller: `scripts/validate.py`, `tests/validate_elections.py` (22), `node --test tests/*.test.cjs` (14; `kompakt.test.cjs` önce `site/build.py` ister), `cd site && node tests/loading.test.cjs` (30). Değişen veri klasörü için `scripts/regenerate_checksums.py <klasör>`.
- İl toplamı ilçeleri tutmayan 53 kayıt kaynak yayının kendisinde (TÜİK il satırı kendi ilçe satırlarını tutmuyor); il kaydında `ilceFarki` + `not`, denetimde belgeli. Kayda alan eklemek `tests/fixtures/known-validation-issues.json` parmak izini değiştirir.
- 1963–1977 meclis kitapları: `scripts/pipelines/tuik_arsiv/extract_mahalli_1963_1977.py <seçim> [tablo]` (KITAPLAR; görüntüden ikinci okuma `goruntu_okuma.py`, tesseract önbelleği `.cache/tuik/`) → katman → `merge_mahalli.ek_meclis` (yalnız o seçim; `main` başkanlığı da yazar) → `build_meclis_harita.py` (`DIE_YILLARI`) + `election-config.js` `OYLAMA_YILLARI`. Dört yıl yapıldı; 0015740 taramasında kitap s.189–194 yok. Başkanlık: `merge_baskanlik_1963_1977.py [--yaz]` (kitap "Bağımsızlar" = bağımsızların toplamı; kazanan 1973'te kitap sütunundan, öteki yıllarda kayıttan). Toplamdan geri hesaplama kapalı; 1968 yüzdesiz tablolar ve 1963 sağ yüz sütunları başlıktan; 1963 karşı sayfa eşleşmesi geçerli/oy kullanan %80–100. Kör okuma: 108 satır, kabul edilen 93'ü kitapla aynı.
- Ek kayıtlar (`data/normalized/ek/`): `build_ek_kayitlar.py` yeniden çalıştırılırsa sonradan güncellenen geomId'leri eski haline döndürür; değişikliği dosyaya hedefli uygula. Senato PDF sütun kaymaları `extract_senato.py` `ELLE_DUZELTME` tablosunda.
- Denetim: `python3 scripts/veri_denetimi.py --md docs/rapor/VERI_DENETIMI.md --csv-klasor docs/rapor/veri_denetimi`. CI `--kontrol docs/rapor/veri_denetimi` ile kayıtlı listede olmayan yeni bulguda başarısız olur; veri düzeltince listeyi bu komutla yenile.

- Servisler (1 Kasım 2026'da main'e girdi): `backend/` (#14; Docker, MySQL 8, data-loader/election-api/gateway, CI `backend.yml`), `backend/election-api-lite/` (#17; tek servis, MariaDB, CI `election-api-lite.yml`), `chatbot/` (#16; Python FastAPI, text-to-SQL, `pytest`), `scripts/db_yukle.py` (MariaDB'ye yükleme; Pi `evnas`, db `secim`). SQLite (`scripts/veritabani/`, #21) ve backend chatbot modülü (`backend/chatbot`, Claude API, #22) da main'de.

## Veri hattı (mahalle)
- YSK açık veri yalnız GitHub Actions'tan erişilir; sonuç `::notice` ile okunur (`gh api .../check-runs/<job>/annotations`), dosyalar veri dalına itilir, `git fetch origin +dal:refs/remotes/origin/dal` + `git checkout origin/dal -- yol`.
- İş akışları: `ysk-mahalle-cek.yml` (muhtarlık), `tkgm-mahalle-cek.yml`, `osm-mahalle-cek.yml`, `belediye-mahalle-cek.yml`, `osm-yer-cek.yml` (OSM köy/mahalle noktaları; elle, `iller` girdisiyle kısmi; `osm-yer-veri` dalına ekler), `osm-ilce-cek.yml` (OSM ilçe sınırları; aynı biçim, `osm-ilce-veri`). Actions artifact'ları geliştirme ortamından indirilemiyor (blob 403): veri dalı şart.
- Yerel başkanlık belde ayrımı (2026-11-01): `ysk-belde-baskan-cek.yml` → `ysk-belde-baskan-veri` dalı → `data/raw/ysk/acikveri-belde-agrege/<yıl>yerel_belediye_baskanligi.json`; `scripts/pipelines/election_import/belde_ayir_baskan.py [kontrol|uygula]` beldeli ilçeyi ilçe merkezi sonucuna çevirir (eski toplam `kaynak.yskSatiri`; Güzelyurt 2024 ve 2009 Akyazı/Koçarlı/Mecitözü/Şarkikaraağaç/Ağın/Kadışehri yenileme sonucu, `ysk-yenileme-2009-cek.yml`). `merge_yerel_v2.py` yeniden çalıştırılırsa bu betik de ardından çalıştırılmalı. Rapor `docs/rapor/KAZANAN_TUTARSIZLIK.md`.
- Eşleştirme: `scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py [kontrol|uygula] <seçimler>`; sıra belediye → mevcut → OSM → TKGM → OSM konumu (eski adlı TKGM birimi, yalnız bire bir ve ad destekli); sentetik (tarihsel) ilçeler halef havuzuyla. 15 seçimin hepsi işlendi (2009–2024). Eşleşmeyen muhtarlık haritada boş kalır (kullanıcı kararı; toplu "konumu belirsiz" alan yok). Yeniden çalıştırma tekrarlanabilir: daha önce verilmiş OSM sınırı yalnız aynı adlı muhtarlığa gider.
- Konum kuralı (2026-10-31): alanının yarısından çoğu ilçe kapsamının (ilçe poligonu + o ilçenin bantta duran TKGM birimleri, 2 km tampon) dışında kalan aday (TKGM/OSM/belediye/mevcut) alınmaz; başka ham kaynak (TKGM/belediye) aynı adlı aynı şekli aynı ilçeye veriyorsa alınır; liste `docs/rapor/mahalle_eslesme/konum_kurali.csv`. Bursa belediye dosyasında Harmancık↔Keles `ilce_adi` takası `BELEDIYE_ILCE_DUZELT`'te.
- Son işlem (`geometri_son_islem`, her `uygula`da ham sınırdan): aynı seçimde birlikte çizilen, anlamlı örtüşen iki TKGM biriminde örtüşme küçük birime kalır (büyükten çıkarılır); aynı sınırlı (IoU ≥ %95) TKGM birimleri tek kayıtta toplanır; poligonlar make_valid + 4 ondalık ızgara + delik yönü; kullanılmayan poligon silinir (TR-D-34-* hariç). Site `fill-rule: evenodd`.
- Lisanslar: TKGM açık lisans dışı; OSM ODbL; Bursa/Sakarya belediye lisansı (atıf). Bkz. `LICENSE-DATA.md`.

## Yönetim raporu
`docs/rapor/VERI_DENETIMI_YONETIM.md` (eylem planı tablosu orada; Claude Docs artifact silindi). Veri ve yöntem raporu: `docs/rapor/VERI_VE_YONTEM.md`.

## Durum
Proje kapandı (21 Ekim 2026; 1963–1977 meclis ve başkanlık işi 26 Ekim 2026'da tamamlandı, kullanıcı bundan sonra çalışma istemiyor). Yalnız yeni seçim (normal takvimde 2028 genel, 2029 yerel) ya da hata bildirimi olursa açılır.
- İsteğe bağlı, yapılmadı: 1994–1999 meclis/belde oy toplamları, 10 kayıtta kazanan "Diğer", Gaziantep belediye sınırları (SSL hatası), Hatay/Van için TUCBS e-Devlet başvurusu (kullanıcı).
