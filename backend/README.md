# Backend: Spring Boot mikroservisleri

Seçim verisini MySQL'e yükleyen ve salt okunur bir REST API olarak sunan servisler. Repodaki veri, site ve
`scripts/` bu klasörden bağımsızdır; GitHub Pages sitesi eskisi gibi çalışır.

```
                      ┌──────────────┐
  tarayıcı / site ──▶ │   gateway    │ :8080  (dışarıya açık tek port; GET /api/**, POST /api/sohbet, /sohbet)
                      └──┬────────┬──┘
                         │        ▼
                         │   ┌──────────┐  araç çağrıları (GET)   ┌────────────────┐
                         │   │ chatbot  │ ──────────────────────▶ │ election-api   │
                         │   └────┬─────┘                         └────────────────┘
                         │        └──▶ Anthropic API (Claude Sonnet)
                         ▼
                      ┌──────────────┐      ┌──────────┐
                      │ election-api │ ───▶ │ MySQL 8  │ ◀── data-loader (tek seferlik: Flyway + yükleme)
                      └──────────────┘      └──────────┘          ▲
                         SELECT yetkili kullanıcı                 └── ../data/normalized, ../sources.yml,
                                                                       ../geo/normalized/mahalle_geo.json (salt okunur)
```

| Modül | Görevi |
|---|---|
| `common` | Ortak DTO'lar ve enum'lar (`SecimTuru`, `OylamaTuru`, `SecenekTipi`, `GecisTuru`) |
| `data-loader` | Flyway şeması (`db/migration`), `data/normalized` (seçimler, meclisler, mahalle, ek kayıtlar) + `sources.yml` → MySQL, tutarlılık kontrolleri |
| `election-api` | Spring Data JPA, yalnız GET uç noktaları, salt okunur veritabanı kullanıcısı |
| `gateway` | Spring Cloud Gateway: `/api/**` → election-api, `POST /api/sohbet` ve `/sohbet` → chatbot; CORS yalnız GitHub Pages için, yalnız GET/HEAD (`CorsFiltresi`) |
| `chatbot` | Türkçe soru-cevap: Claude soruyu anlar, sayıları yalnız election-api araçlarıyla okur (aşağıda) |

## Çalıştırma

Gerekenler: Docker (Docker Desktop). Java ve Maven gerekmez, derleme konteynerde yapılır.

```bash
cd backend
cp .env.example .env          # şifreleri değiştirin; .env depoya girmez
docker compose up --build
```

Sıra: MySQL sağlıklı olunca `data-loader` şemayı kurar ve veriyi yükleyip çıkar, ardından `election-api` ve
`gateway` açılır. İlk yükleme 2,4 milyon mahalle oy satırıyla birlikte 3-5 dakika sürer. Yükleyici kaynak
dosyaların SHA-256 özetini kaydeder; veri değişmediyse sonraki açılışlarda yükleme atlanır ve servisler hemen
açılır. Deneme:

```bash
curl http://localhost:8080/api/secimler?tur=genel
curl http://localhost:8080/api/secimler/2023/iller/34
curl "http://localhost:8080/api/partiler/107/sonuclar?zincir=true"
curl http://localhost:8080/api/secimler/2023/ilceler/TR-D-34-037/mahalleler
curl http://localhost:8080/api/secimler/2023/secilenler?plaka=34
```

Veri değiştiyse yeniden yüklemek için: `docker compose run --rm data-loader`; değişmemiş veriyi zorla
yüklemek için: `ZORLA_YUKLE=true docker compose run --rm data-loader`.
Her şeyi silmek için (veritabanı dahil): `docker compose down -v`.

## Sohbet (chatbot)

`http://localhost:8080/sohbet` sayfasından ya da doğrudan API'den soru sorulur:

```bash
curl -s -X POST localhost:8080/api/sohbet -H 'Content-Type: application/json' \
  -d '{"soru":"1977de İstanbulda CHPnin en yüksek oy aldığı ilçe hangisi?"}' | jq
# {"cevap": "...", "kaynaklar": [{"arac": "ilce_sonuclari", "sorgu": "/api/secimler/1977/iller/34/ilceler", ...}],
#  "haritaBaglantisi": "https://hamikumbasae.github.io/turkiye-secim-haritasi/#secim=1977&il=34&mod=parti&parti=CHP", ...}
```

- **Anahtar:** `.env` içinde `ANTHROPIC_API_KEY=...` (console.anthropic.com). Boşsa diğer servisler çalışır,
  `POST /api/sohbet` 503 döner. Model `ANTHROPIC_MODEL` ile değişir (varsayılan `claude-sonnet-5-5`).
- **Sayılar uydurulmaz:** Model veritabanına doğrudan erişmez ve sayı üretmez; soruyu anlayıp 13 aracı çağırır
  (`yer_ara`, `parti_ara`, `secimleri_listele`, `il_sonuclari`, `ilce_sonuclari`, `ilce_sonucu`,
  `mahalle_sonuclari`, `parti_sonuclari`, `en_guclu_iller`, `secilenler`, `beldeler`, `sandalyeler`,
  `harita_baglantisi`). Her araç bir election-api GET sorgusudur; yanıttaki `kaynaklar` bu sorguları listeler,
  sayfada açılıp kontrol edilebilir.
- **Tarafsızlık:** "Hangi parti daha iyi?", gelecek tahmini, yorum istekleri kibarca reddedilir ve veriyle
  cevaplanabilecek bir soru önerilir. Yalnız Türkçe.
- **Sınırlar:** soru en çok 500 karakter; bir soruda en çok 8 model turu; IP başına dakikada 10 soru
  (`SOHBET_DAKIKADA_ISTEK`). Her soru tek başınadır (konuşma geçmişi tutulmaz).
- **Değerlendirme:** `chatbot/src/test/resources/degerlendirme/sorular.yaml` veritabanından doğrulanmış
  beklenen cevaplarla 16 soru içerir. Gerçek modelle (ücretli, yaklaşık 16 soru × birkaç tur) çalıştırmak
  için sistem `docker compose up` ile açıkken başka bir terminalde: `./degerlendir.sh`.
  Birim testleri ve CI gerçek modeli çağırmaz.

## Testler

```bash
cd backend
./testler.sh                  # Maven konteynerde; MySQL testleri Testcontainers ile kendi MySQL 8.4'ünü açar
# ya da Java 21 + Maven kuruluysa: mvn verify
```

| Modül | Test | Kapsam |
|---|---|---|
| common | 17 | enum dönüşümleri, DTO'ların JSON gidiş-dönüşü |
| data-loader | 34 | kaynak okuma, meclis/Senato/ara seçim/belde/mahalle okuyucuları, ilçe adı eşleme, tutarlılık kuralları, ilçe yılları, kaynak özeti (birim); MySQL'de uçtan uca yükleme, veri düzeltilmeden yüklenir mi, tohumda olmayan parti, yeniden yükleme ve değişmeyen veride atlama (Testcontainers) |
| election-api | 18 | kontrolcüler, hata yanıtları, yalnız GET (MockMvc); servis mantığı (Mockito); MySQL'de bütün uç noktalar (Testcontainers) |
| gateway | 10 | CORS filtresi (birim); sahte bir arka servisle yönlendirme, yöntem kısıtı, CORS, sağlık ucu |

Docker yoksa MySQL testleri atlanır (başarısız sayılmaz). Docker 29 ve sonrası eski Docker API sürümlerini
reddettiği için `testler.sh`, Testcontainers'a API sürümünü (`1.44`) açıkça verir; bunu yapmazsa MySQL testleri
"Could not find a valid Docker environment (Status 400)" ile atlanır. `mvn verify` ile doğrudan çalıştırırken
aynı sorun çıkarsa: `echo api.version=1.44 > ~/.docker-java.properties`.

## Uç noktalar

| GET | Açıklama |
|---|---|
| `/api/secimler?tur=&oylama=&yil=&yilBaslangic=&yilBitis=` | Oylamalar (`tur`: genel, yerel, referandum, cumhurbaskanligi, senato, ara; `oylama`: milletvekili, baskanlik, belediye_meclisi, il_genel_meclisi, referandum, cumhurbaskanligi, senato) |
| `/api/secimler/{secimId}` | Tek oylama (`2023`, `2024yerel`, `2024yerel_bm`, `1961senato`, `2019istanbul_bb_yenileme`) |
| `/api/secimler/{secimId}/bagli-oylamalar` | Ana seçime bağlı ikincil oylamalar (meclisler, yenileme seçimleri) |
| `/api/secimler/{secimId}/iller` | Bütün il sonuçları, oylarla (plaka 0 = yurt dışı) |
| `/api/secimler/{secimId}/iller/{plaka}` | Bir il |
| `/api/secimler/{secimId}/iller/{plaka}/ilceler` | Bir ilin ilçeleri |
| `/api/secimler/{secimId}/ilceler/{ilceId}` | Bir ilçe (`TR-D-34-037`) |
| `/api/secimler/{secimId}/ilceler/{ilceId}/mahalleler` | Bir ilçenin mahalle/köy sonuçları (2009-2024), seçmene göre sıralı |
| `/api/secimler/{secimId}/beldeler?plaka=&ilceId=` | Belde belediyeleri |
| `/api/secimler/{secimId}/secilenler?plaka=` | Seçilen milletvekilleri / senatörler (eksik olabilir) |
| `/api/secimler/{secimId}/sandalyeler?plaka=&ilceId=` | Parti başına sandalye: il (milletvekili), ilçe (2024 belediye meclisi) |
| `/api/secimler/{secimId}/kapsam` | Kaynakta kaç kayıt bulundu / beklendi |
| `/api/iller` | İller |
| `/api/iller/{plaka}/ilceler?yil=` | İlçe birimleri; `yil` verilirse o yıl veride olanlar |
| `/api/partiler?tip=` | Partiler ve öteki seçenekler (`tip`: parti, aday, referandum, diger) |
| `/api/partiler/{partiId}` | Parti ve öncülleri (`onceki_parti_id` zinciri) |
| `/api/partiler/{partiId}/sonuclar?tur=&oylama=&yil=&yilBaslangic=&yilBitis=&plaka=&zincir=` | Seçimlere göre sonuç; `plaka` yoksa Türkiye geneli, `zincir=true` öncül partileri de katar. `oylama` verilmezse yalnız ana seçimler (meclis, Senato, ara seçim hariç; bunlar yalnız bazı illerde yapıldığı için toplamları "Türkiye geneli" sayılmaz) |
| `/api/partiler/{partiId}/secimler/{secimId}/en-guclu-iller?limit=` | Partinin en yüksek oranı aldığı iller |

Hatalar: bulunamayan kayıt 404, geçersiz parametre 400, `{"durum", "hata", "mesaj"}` biçiminde.

## Veri modeli ve kararlar

- **Şemanın sahibi data-loader'dır** (Flyway `V1__sema.sql`, ek veri için `V4__ek_veri.sql`). election-api şemayı değiştirmez, yalnız `SELECT`
  yetkili ayrı bir kullanıcıyla bağlanır (`mysql/init/01-okuma-kullanicisi.sh`).
- **Sabit `parti_id`.** Kimlikler `V2__partiler.sql` tohumunda bir kez verildi, yeniden yüklemede değişmez.
  Veriye yeni bir parti adı gelirse data-loader durur ve şu komutu önerir; çıkan dosya yeni bir migration olur:
  `python3 backend/tools/parti_tohumu.py --eksikler > backend/data-loader/src/main/resources/db/migration/V<sıradaki>__yeni_partiler.sql`
  (`V5__ek_veri_partileri.sql` böyle üretildi: 2026 ara seçimindeki 8 yeni parti.) Yalnız büyük/küçük harfi farklı
  yazımlar ('Yeniden Refah' / 'YENİDEN REFAH') `parti_takma_ad` tablosuyla aynı `parti_id`'ye bağlanır.
- **Parti devamlılığı:** `onceki_parti_id` + `gecis_turu` (`ad_degisikligi`, `halef`, `birlesme`) + `gecis_yili` +
  `gecis_kaynagi`. `V3__parti_gecisleri.sql` yalnız belgelenebilen bir geçiş içerir (Yeşil Sol Parti → DEM Parti,
  aynı tüzel kişilik). Yorum gerektiren "devamı sayılır" ilişkileri bilerek girilmedi; eklemek için yeni bir
  migration yazılır.
  - Sınır: tek `onceki_parti_id` sütunu birden çok partinin birleşmesini (ör. SHP'nin CHP'ye katılması) tam
    gösteremez. Gerekirse ayrı bir `parti_gecis(onceki, sonraki, tur, yil)` tablosu eklenmeli.
  - Kaynak verideki `DP` anahtarı hem 1946-1960 Demokrat Parti'yi hem de 2007'de DYP'nin aldığı adı taşıyor;
    veri düzeltilmediği için ikisi aynı `parti_id`'de.
- **İlçe yılları:** `baslangic_yili` / `bitis_yili`, birimin veride dolu bir satırla göründüğü ilk/son seçim yılıdır
  (yasal kuruluş tarihi değil). Güncel ilçelerde (`TR-D-...`) `bitis_yili` boştur. Henüz kurulmamış ilçeler için
  kaynakta tutulan boş satırlar (seçmen 0, oy 0) başlangıca sayılmaz ama yüklenir.
- **Tutarlılık kontrolleri veriyi DÜZELTMEZ**, `logs/tutarlilik.log`'a yazar, özet `veri_yukleme` tablosundadır:

  | Bulgu | Kural |
  |---|---|
  | `PARTI_TOPLAMI_GECERLI_OY_DEGIL` | Seçeneklerin oy toplamı ≠ geçerli oy (il, ilçe, yurt dışı) |
  | `ILCE_TOPLAMI_IL_TOPLAMINDAN_FARKLI` | İlçelerin geçerli oy toplamı il toplamından %0,5'ten fazla farklı (genel, referandum, CB; yerel seçimde il satırı başka bir yarışma olduğu için karşılaştırılmaz) |
  | `KATILIM_100_USTU`, `KAZANAN_OYLARDA_YOK` | adı üstünde |
  | `ILCENIN_ILI_YOK`, `YINELENEN_SATIR` | anahtar ihlali: satır yazılamaz, atlanır ve hata olarak loglanır |

  Toleranslar `.env`/ortam ile değiştirilebilir: `ILCE_TOLERANSI` (göreli), `PARTI_TOPLAM_TOLERANSI` (oy).
  Gerçek veride beklenen: ~1.600 parti toplamı ve ~90 ilçe toplamı bulgusu (çoğu taranmış eski yayınlarda, kaynak
  kökenli; ayrıntı için `docs/rapor/VERI_DENETIMI.md`). Mahalle satırları kontrol edilmez.

### Yüklenen veri

| Kaynak | Nereye | Satır |
|---|---|---|
| `elections/<tür>/*.json` | `secim`, `sonuc_il`/`oy_il`/`sandalye_il`, `sonuc_ilce`/`oy_ilce` | 46 seçim |
| `meclis_harita/*_bm.json`, `*_igm.json` | aynı tablolar; ayrı `secim` satırı (`oylama`: belediye_meclisi / il_genel_meclisi), `ana_secim_id` ile ana seçime bağlı | 26 oylama |
| `ek/senato/*.json` | `secim` (`tur='senato'`), il oyları, TÜİK ilçe oyları ya da yalnız ilçe birincisi, `secilen` (senatör) | 8 seçim, 510 senatör |
| `ek/yenileme_ara/*.json` | `secim` (`tur='ara'`); milletvekili ara seçimleri, belediye yenileme/ara seçimleri | 11 oylama |
| `mahalle/*.json` + `geo/normalized/mahalle_geo.json` (yalnız adlar) | `mahalle`, `sonuc_mahalle`, `oy_mahalle` | 602.285 sonuç, 2,4 milyon oy |
| `ek/beldeler/*.json`, `ek/belediye_meclisi/*.json` (belde satırları) | `sonuc_belde`, `oy_belde` | 30.019 |
| `ek/milletvekilleri/*.json` | `secilen` (milletvekili) | 9.279 |
| `meclis_2024.json` | `sandalye_ilce` | 110 ilçe |
| ek dosyalardaki kapsam/özet | `kaynak_kapsami` | 80 |

Bu sayılar, kaynakla satır satır doğrulanmış SQLite veritabanıyla (`scripts/veritabani/`, `veritabani` dalı)
tablo tablo karşılaştırıldı: satır sayıları ve oy toplamları bütün tablolarda aynı.

- **Ek kayıtlarda değiştirilen tek şey:** kaynakta "doğrulanamayan" diye işaretli alanlar (Senato ve ara seçim
  TÜİK satırlarında `dogrulanamayanAlanlar`) ve INT'e sığmayan, taranmış kitapta okuma hatası olduğu belli sayılar
  boş bırakılır; satırın `not_metni`'nde hangi alanın boşaltıldığı yazar.
- **Belde kimliği yoktur.** Kaynaklar arasında ortak belde anahtarı bulunmadığı için her `sonuc_belde` satırı bir
  seçimdeki bir beldedir. İlçeye adından bağlanır (aynı ilde aynı adla, istenen yıla en yakın seçimdeki birim);
  bağlanamayanlarda `ilce_id` boştur (30.019'un 28.365'i bağlandı). Taranmış kitaptan okunan satırlar `kontrol`
  sütununda doğrulama sonucunu taşır (`tutarli`, `tutarsiz`, `toplamTutmuyor` ...).
- **Senato ilçeleri:** TÜİK yayını yalnız bazı illerin ilçe oylarını veriyor; öteki ilçelerde yalnız birinci gelen
  parti (Vikipedi) bilinir (`sadece_kazanan`). 16 ilçe adı hiçbir ilçe birimine eşlenemedi, yüklenmedi.
- **1986 milletvekili ara seçimi:** Manisa'nın iki seçim çevresi il satırında toplanır.
- **Seçilen listeleri eksik:** ör. 2023'te 600 milletvekilinin 405'i (`/api/secimler/2023/kapsam`).
