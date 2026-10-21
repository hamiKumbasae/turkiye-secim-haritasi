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
- Denetim: `python3 scripts/veri_denetimi.py --md docs/rapor/VERI_DENETIMI.md --csv-klasor docs/rapor/veri_denetimi`. CI `--kontrol docs/rapor/veri_denetimi` ile kayıtlı listede olmayan yeni bulguda başarısız olur; veri düzeltince listeyi bu komutla yenile.

## Veri hattı (mahalle)
- YSK açık veri yalnız GitHub Actions'tan erişilir; sonuç `::notice` ile okunur (`gh api .../check-runs/<job>/annotations`), dosyalar veri dalına itilir, `git fetch origin +dal:refs/remotes/origin/dal` + `git checkout origin/dal -- yol`.
- İş akışları: `ysk-mahalle-cek.yml` (muhtarlık), `tkgm-mahalle-cek.yml`, `osm-mahalle-cek.yml`, `belediye-mahalle-cek.yml`.
- Eşleştirme: `scripts/pipelines/mahalle_veri/transform/tkgm_muhtarlik_esle.py [kontrol|uygula] <seçimler>`; sıra belediye → mevcut → OSM → TKGM; sentetik (tarihsel) ilçeler halef havuzuyla. 15 seçimin hepsi işlendi (2009–2024).
- Lisanslar: TKGM açık lisans dışı; OSM ODbL; Bursa/Sakarya belediye lisansı (atıf). Bkz. `LICENSE-DATA.md`.

## Yönetim raporu
Claude Docs artifact `f24fac76-2c6f-4b0f-a2f3-dc33a09ee4ee` (eylem planı tablosu orada).

## Sıradaki işler (öncelik sırası)
- F: İl toplamı ilçeleri tutmayan 54 kayıt (çoğu 1973; 1982 Van).
- G: 1979 Senato'da iki kesirli oy.
- İsteğe bağlı: 1994–1999 meclis/belde oy toplamları, 1994/1999'da 10 ilçede kazanan "Diğer", 2009 Ağın/Kadışehri yenileme seçimi, Gaziantep belediye verisi (SSL hatası), Hatay/Van için TUCBS e-Devlet başvurusu (kullanıcı).
