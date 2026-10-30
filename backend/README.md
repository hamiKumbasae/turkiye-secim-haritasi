# Backend: Spring Boot mikroservisleri

Seçim verisini MySQL'e yükleyen ve salt okunur bir REST API olarak sunan servisler. Repodaki veri, site ve
`scripts/` bu klasörden bağımsızdır; GitHub Pages sitesi eskisi gibi çalışır.

```
                      ┌──────────────┐
  tarayıcı / site ──▶ │   gateway    │ :8080  (dışarıya açık tek port; yalnız GET /api/**)
                      └──────┬───────┘
                             ▼
                      ┌──────────────┐      ┌──────────┐
                      │ election-api │ ───▶ │ MySQL 8  │ ◀── data-loader (tek seferlik: Flyway + yükleme)
                      └──────────────┘      └──────────┘          ▲
                         SELECT yetkili kullanıcı                 └── ../data/normalized, ../sources.yml (salt okunur)
```

| Modül | Görevi |
|---|---|
| `common` | Ortak DTO'lar ve enum'lar (`SecimTuru`, `SecenekTipi`, `GecisTuru`) |
| `data-loader` | Flyway şeması (`db/migration`), `data/normalized/elections` + `sources.yml` → MySQL, tutarlılık kontrolleri |
| `election-api` | Spring Data JPA, yalnız GET uç noktaları, salt okunur veritabanı kullanıcısı |
| `gateway` | Spring Cloud Gateway: `/api/**` → election-api; CORS yalnız GitHub Pages için, yalnız GET/HEAD (`CorsFiltresi`) |

## Çalıştırma

Gerekenler: Docker (Docker Desktop). Java ve Maven gerekmez, derleme konteynerde yapılır.

```bash
cd backend
cp .env.example .env          # şifreleri değiştirin; .env depoya girmez
docker compose up --build
```

Sıra: MySQL sağlıklı olunca `data-loader` şemayı kurar ve veriyi yükleyip çıkar (birkaç dakika), ardından
`election-api` ve `gateway` açılır. Deneme:

```bash
curl http://localhost:8080/api/secimler?tur=genel
curl http://localhost:8080/api/secimler/2023/iller/34
curl "http://localhost:8080/api/partiler/107/sonuclar?zincir=true"
```

Veriyi yeniden yüklemek için: `docker compose run --rm data-loader`.
Her şeyi silmek için (veritabanı dahil): `docker compose down -v`.

## Testler

```bash
cd backend
./testler.sh                  # Maven konteynerde; MySQL testleri Testcontainers ile kendi MySQL 8.4'ünü açar
# ya da Java 21 + Maven kuruluysa: mvn verify
```

| Modül | Test | Kapsam |
|---|---|---|
| common | 14 | enum dönüşümleri, DTO'ların JSON gidiş-dönüşü |
| data-loader | 20 | kaynak okuma, tutarlılık kuralları, ilçe yılları (birim); MySQL'de uçtan uca yükleme, veri düzeltilmeden yüklenir mi, tohumda olmayan parti, yeniden yükleme (Testcontainers) |
| election-api | 16 | kontrolcüler, hata yanıtları, yalnız GET (MockMvc); servis mantığı (Mockito); MySQL'de bütün uç noktalar (Testcontainers) |
| gateway | 10 | CORS filtresi (birim); sahte bir arka servisle yönlendirme, yöntem kısıtı, CORS, sağlık ucu |

Docker yoksa MySQL testleri atlanır (başarısız sayılmaz). Docker 29 ve sonrası eski Docker API sürümlerini
reddettiği için `testler.sh`, Testcontainers'a API sürümünü (`1.44`) açıkça verir; bunu yapmazsa MySQL testleri
"Could not find a valid Docker environment (Status 400)" ile atlanır. `mvn verify` ile doğrudan çalıştırırken
aynı sorun çıkarsa: `echo api.version=1.44 > ~/.docker-java.properties`.

## Uç noktalar

| GET | Açıklama |
|---|---|
| `/api/secimler?tur=&yil=&yilBaslangic=&yilBitis=` | Seçimler (`tur`: genel, yerel, referandum, cumhurbaskanligi) |
| `/api/secimler/{secimId}` | Tek seçim (`2023`, `2024yerel`, `2017referandum`, `2023cb2tur`) |
| `/api/secimler/{secimId}/iller` | Bütün il sonuçları, oylarla (plaka 0 = yurt dışı) |
| `/api/secimler/{secimId}/iller/{plaka}` | Bir il |
| `/api/secimler/{secimId}/iller/{plaka}/ilceler` | Bir ilin ilçeleri |
| `/api/secimler/{secimId}/ilceler/{ilceId}` | Bir ilçe (`TR-D-34-037`) |
| `/api/iller` | İller |
| `/api/iller/{plaka}/ilceler?yil=` | İlçe birimleri; `yil` verilirse o yıl veride olanlar |
| `/api/partiler?tip=` | Partiler ve öteki seçenekler (`tip`: parti, aday, referandum, diger) |
| `/api/partiler/{partiId}` | Parti ve öncülleri (`onceki_parti_id` zinciri) |
| `/api/partiler/{partiId}/sonuclar?tur=&yil=&yilBaslangic=&yilBitis=&plaka=&zincir=` | Seçimlere göre sonuç; `plaka` yoksa Türkiye geneli, `zincir=true` öncül partileri de katar |
| `/api/partiler/{partiId}/secimler/{secimId}/en-guclu-iller?limit=` | Partinin en yüksek oranı aldığı iller |

Hatalar: bulunamayan kayıt 404, geçersiz parametre 400, `{"durum", "hata", "mesaj"}` biçiminde.

## Veri modeli ve kararlar

- **Şemanın sahibi data-loader'dır** (Flyway `V1__sema.sql`). election-api şemayı değiştirmez, yalnız `SELECT`
  yetkili ayrı bir kullanıcıyla bağlanır (`mysql/init/01-okuma-kullanicisi.sh`).
- **Sabit `parti_id`.** Kimlikler `V2__partiler.sql` tohumunda bir kez verildi, yeniden yüklemede değişmez.
  Veriye yeni bir parti adı gelirse data-loader durur ve şu komutu önerir; çıkan dosya yeni bir migration olur:
  `python3 backend/tools/parti_tohumu.py --eksikler > backend/data-loader/src/main/resources/db/migration/V4__yeni_partiler.sql`
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
  Gerçek veride beklenen: ~700 parti toplamı ve ~90 ilçe toplamı bulgusu (çoğu taranmış eski yayınlarda, kaynak
  kökenli; ayrıntı için `docs/rapor/VERI_DENETIMI.md`).
- **Kapsam:** il ve ilçe düzeyindeki 46 ana seçim. Mahalle sonuçları, meclis seçimleri, Senato, ara seçimler,
  beldeler ve milletvekili listeleri henüz yüklenmiyor.
