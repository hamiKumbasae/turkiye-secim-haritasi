# Seçim Takvimi (1950-2024)

Bu belge, [`data/secim_takvimi.json`](data/secim_takvimi.json)'un okunabilir
özeti — "1950-2024 arasında Türkiye'de kaç seçim oldu, hangileri bu projede
var?" sorusuna cevap.

## Özet

| Tür | 1950-2024 arası toplam | Bu projede veri var |
|---|---|---|
| Genel seçim (milletvekili) | 20 | 20 / 20 |
| Yerel seçim (mahalli idareler) | 15 | 15 / 15 |
| Referandum | 7 | 7 / 7 |
| Cumhurbaşkanlığı (halk oyuyla, 2014+) | 4 | 4 / 4 |
| **Toplam (4 ana kategori)** | **46** | **46 / 46** |

2026-09-22'de yapılan bir taramada 6 yerel seçimin (1950-1977) eksik olduğu
tespit edildi ve aynı oturumda **il merkezi düzeyinde** eklendi (bkz. aşağı).
Proje artık 4 ana kategoride (genel/yerel/referandum/cumhurbaşkanlığı)
**eksiksiz**.

## Eklendi: 1984 öncesi 6 yerel seçim (il merkezi düzeyi)

`yerel_secimler.json` önceden sadece 1984'ten başlıyordu (9 seçim). Bu
oturumda 1950, 1955, 1963, 1968, 1973, 1977 için **il merkezinin kendi
belediye başkanlığı yarışı** Türkçe Wikipedia'nın il-bazlı alt
makalelerinden (`<İl>'da <yıl> Türkiye yerel seçimleri`) çekilip eklendi —
aynı kaynak/güvenilirlik seviyesi, projenin zaten 1984-2004 için kullandığı
yöntemle birebir aynı ("Wikipedia (il başına alt makaleler)", bkz.
`SOURCES.md`).

| Yıl | Tarih | İl sayısı | Not |
|---|---|---|---|
| 1950 | 3 Eylül 1950 | 63/63 | Dolaylı sistem: başkan, meclisin kendi içinden seçiliyordu — çoğu ilde sadece meclis sandalye dağılımı var, gerçek oy sayısı yalnızca 2 ilde (Ağrı, Bursa) |
| 1955 | 13 Kasım 1955 | 66/66 | 1954'te kurulan Nevşehir, Adıyaman ve Sakarya il; Kırşehir Nevşehir'in ilçesi (2026-10-05'te düzeltildi). Aynı dolaylı sistem; CHP ve Cumhuriyetçi Millet Partisi bu seçime hiç katılmadı (tarihi olgu) |
| 1963 | 17 Kasım 1963 | 67/67 | İlk tek dereceli (doğrudan) yerel seçim; ana makalenin karşılaştırma tablosuyla 66/67 örtüştü (İstanbul'da bilinen bir diskalifiye vakası hariç, ayrıntı `sources.yml`'de) |
| 1968 | 2 Haziran 1968 | 67/67 | Ana makale karşılaştırma tablosuyla 67/67 birebir örtüştü |
| 1973 | 9 Aralık 1973 | 67/67 | Ana makale karşılaştırma tablosuyla VE düz metin özetiyle (32/22/8 CHP/AP/Bağımsız) birebir örtüştü |
| 1977 | 11 Aralık 1977 | 67/67 | Ana makale karşılaştırma tablosuyla 67/67 örtüştü; bilinen tarihi sonuçlarla (Diyarbakır'da Mehdi Zana, Konya'da Keçeciler) tutarlı |

**Kapsam sınırı:** Sadece **il merkezi** eklendi — `ilceler` bu 6 yıl için
boş bırakıldı (Adıyaman'ın Besni'si gibi diğer ilçeler dahil değil). Bu,
aynı depodaki 1950-1977 GENEL seçim verisinin zaten kullandığı bir kapsam
sınırlamasıyla tutarlı (bkz. README: "Bu dönemde 'seçim çevresi' = il'in
kendisi"). İlçe düzeyini eklemek ayrı ve büyük bir iş — il alt makaleleri
teknik olarak ilçe tabloları da içeriyor (görüldü), ama güvenilir şekilde
ayrıştırıp haritanın `geomId` şemasıyla eşlemek (tarihsel ilçe sınırı
değişiklikleri dahil) bu oturumun kapsamı dışında bırakıldı.

4 yeni parti `partiler.json`'a eklendi: **TSİP** (Türkiye Sosyalist İşçi
Partisi), **SDP** (Sosyalist Devrim Partisi), **MKP** (Millî Kalkınma
Partisi), **KARMA** (parti değil, birden fazla partinin/bağımsızın ortak
çıkardığı karma aday listesi — sadece 1955 Adana'da görüldü).

Ayrıntılı kaynak/doğrulama notları için `sources.yml`'deki
`1950yerel`...`1977yerel` girişlerine bakın.

## Kapsam dışı bırakılan kategoriler

Sorulan "ara seçim" de dahil, aşağıdaki üç kategori bilinçli olarak bu
projenin (ve dolayısıyla `secim_takvimi.json`'un `ana_kategoriler`
listesinin) **dışında** tutuldu — çünkü haritanın kendi tanımlı kapsamına
(README: "genel seçim, yerel seçim, referandum ve cumhurbaşkanlığı
seçimi") girmiyorlar. `data/secim_takvimi.json`'un `kapsam_disi_kategoriler`
alanında ayrıca belgelendiler:

- **Ara seçimler** — Genel seçimler arasında boşalan tek tek milletvekili
  koltuklarını doldurmak için birkaç ilde aynı gün yapılan küçük ölçekli
  seçimler (bütün ülkede sandık açılmıyor). 1950-2024 arasında **en az**
  1951, 1966, 1968, 1975, 1979, 1986, 1992, 2003 yıllarında yapıldı — ama bu
  liste **kesin/eksiksiz değil**: ikincil kaynaklar birbiriyle çelişiyor
  (biri "1936'dan bu yana toplam 59 ara seçim" derken, taranan tablo
  satırları çok daha yüksek bir toplam gösteriyor). Tam/kesin bir ara seçim
  takvimi ayrı bir araştırma oturumu gerektirir.
- **Cumhuriyet Senatosu üye seçimleri (1961-1980)** — TBMM'nin artık var
  olmayan ikinci kanadının üçte-bir yenileme seçimleri, 8 seçim günü
  (1961, 1964, 1966, 1968, 1973, 1975, 1977, 1979). Kurum 1982 Anayasası'yla
  tamamen kaldırıldı.
- **Tekil il/ilçe yenileme seçimleri** — Projenin kendi `SOURCES.md`'si
  zaten şunları "henüz eklenmedi" olarak not etmişti: 2019 İstanbul
  Büyükşehir Belediyesi yenileme seçimi (23 Haziran 2019, YSK'nin 31 Mart
  sonucunu iptaliyle), "2024 Yenileme Seçimi" ve "2026 Ara Seçimi" — bu
  ikisinin ayrıntısı bu oturumda araştırılmadı.

## Kaynaklar

- Bu depodaki 40 seçim: `data/normalized/{cumhurbaskanligi,genel_secimler,yerel_secimler,referandumlar}.json`
  (zaten `SOURCES.md`/`sources.yml` ile YSK/Habertürk/Wikipedia çapraz
  doğrulamalı)
- Eksik 6 yerel seçim + kapsam dışı kategoriler: `en.wikipedia.org/wiki/Elections_in_Turkey`,
  `tr.wikipedia.org/wiki/Türkiye_ara_seçimleri_listesi`, `tr.wikipedia.org/wiki/1955_Türkiye_yerel_seçimleri`,
  `ysk.gov.tr/tr/2-haziran-1968-mahalli-i̇dareler-genel-secimleri/80091` — bunlar **birincil kaynakla
  (YSK/TÜİK arşivi) henüz teyit edilmedi**, sadece bu boşluğun tespiti için kullanıldı.
