# Veri Kaynakları

Bu belge, `index.html`'e gömülü 40 seçimin her birinin verisinin **nereden**
geldiğinin okunabilir özetidir. Makine-okunur, tam ayrıntılı hâli
[`sources.yml`](sources.yml)'dedir — her iki dosya da aynı 40 anahtarı kapsar
(anahtarlar `index.html` içindeki `secim_tarihi_data.json`'daki seçim
anahtarlarıyla birebir aynıdır, örn. `2023`, `2014yerel`, `2017referandum`,
`2023cb2tur`).

## Kaynak hiyerarşisi (öncelik sırası)

1. **YSK Açık Veri Portalı** (`acikveri.ysk.gov.tr`) — resmi, 2009 ve sonrası
   seçimleri kapsar. Bu depoda **mahalle/muhtarlık düzeyi** verinin tamamı ve
   **2014 Cumhurbaşkanlığı seçiminin il/ilçe düzeyi** doğrudan buradan.
2. **Habertürk** (`secim.haberturk.com`) — 2011 sonrası genel/yerel/CB
   seçimleri ile 2010/2017 referandumlarının il/ilçe düzeyi verisinin
   kaynağı. Resmi değil ama YSK'nin açıkladığı sonuçları raporluyor.
3. **Türkçe Wikipedia** (YSK kaynaklı tablolar) — 1950-2009 arası, Habertürk'ün
   kapsamadığı yıllar için il düzeyi veri.
4. **mertnuhoglu/secim_verileri** (GitHub, memurlar.net kaynaklı) — 1991-2007
   genel seçimlerinin ilçe düzeyi kırılımı (Wikipedia sadece il düzeyi veriyor).

> **Not:** `~/Desktop/2023_Secim_Verileri/OKUBENI.md` (bu projenin dışında,
> önceki bir oturumun ürettiği dış üretim script'inin notu) 2026-09-19'da
> "YSK'nin açık veri portalı sandık bazlı sonuçları toplu biçimde
> yayımlamıyor" diyordu. Bu **yanlıştı** — YSK'nin `getSecimSandikSonucList`
> uç noktası tam olarak bunu yapıyor ve genel kullanıma açık. Bu depoya
> 2026-09-21/22'de eklenen tüm mahalle-düzeyi veri ve 2014cb'nin ilçe düzeyi
> bu keşfin sonucu.

## Cumhurbaşkanlığı (4 seçim)

| Yıl | İl/İlçe kaynağı | Mahalle kaynağı |
|---|---|---|
| 2014cb | **YSK** (bu oturumda Wikipedia'nın yerine geçti) | YSK, 641/973 ilçe |
| 2018cb | Habertürk | YSK, 641/973 ilçe |
| 2023cb1tur | Habertürk | YSK, 641/973 ilçe |
| 2023cb2tur | Habertürk | YSK, 641/973 ilçe |

2014cb için: eski Wikipedia kaynağı sadece il düzeyindeydi. Bu oturumda YSK'den
gerçek ilçe verisi çekildi; ulusal toplamlar eski veriyle birebir örtüştüğü
doğrulandı.

## Genel Seçim / Milletvekili (20 seçim)

| Dönem | İl kaynağı | İlçe kaynağı | Bilinen sorun / kapsam sınırı |
|---|---|---|---|
| 2011, 2015×2, 2018, 2023 | Habertürk | Habertürk | — (mahalle düzeyi de YSK'den eklendi) |
| 1991, 1995, 1999, 2002, 2007 | Wikipedia | mertnuhoglu | **2002 Siirt**: kaynaktaki ilçe kırılımı bozuk, düzeltilmedi (bkz. aşağı) |
| 1965–1987 (6 seçim) | Wikipedia | — | İlçe verisi yok |
| 1950–1961 (4 seçim) | Wikipedia | — | İlçe verisi yok, **vekil/sandalye dağılımı da yok** (sadece kazanan parti + oran) |

**2002 Siirt sorunu:** mertnuhoglu kaynağındaki Siirt ilçe kırılımı, DEHAP'ın
o ildeki gerçek birinciliğini (il geneli %32,2) yansıtmıyor — Merkez ilçede
"AK Parti %86,71" gibi gerçek dışı bir değer var. Güvenilir alternatif ilçe
kaynağı bulunamadığı için bu hatalı sayılar tahminle değiştirilmedi, olduğu
gibi bırakıldı.

**1954 Bilecik:** kaynak tabloda satırı eksikti, ayrı bir Wikipedia
tablosundan bulunup eklendi.

**1961:** vekil dağılımı hesaplanamadı çünkü o yıla özgü "millî bakiye"
sistemi basit D'Hondt ile yeniden üretilemiyor.

**1957:** kaynak tablodaki vekil sütunu resmi 610 sandalye toplamıyla
uyuşmuyordu, güvenilmez kabul edilip atlandı.

## Yerel Seçim / Belediye Başkanlığı (9 seçim)

| Yıl | Kaynak | Not |
|---|---|---|
| 2024, 2019, 2014, 2009 | Habertürk / Wikipedia | Mahalle düzeyi YSK'den eklendi |
| 2004, 1999, 1994, 1989, 1984 | Wikipedia (il başına alt makaleler) | Katılım/seçmen verisi kaynakta yok |

**2014 BDP/HDP sorunu:** Habertürk kaynaklı il/ilçe verisinde BDP'nin oyu her
yerde 0 görünüyor (Diyarbakır dahil, oysa BDP o seçimi orada gerçekten
kazanmıştı). Bu oturumda YSK'den çekilen mahalle-düzeyi veride gerçek oylar
"HDP" sütunu altında bulundu ve mahalle katmanında BDP→HDP eşlemesiyle
düzeltildi. **İl/ilçe düzeyindeki orijinal kayıt henüz düzeltilmedi** —
sonraki yeniden-doğrulama aşamasının kapsamında.

## Referandum (7 halk oylaması)

| Yıl | Kaynak | Not |
|---|---|---|
| 2017 | Habertürk (il/ilçe) + YSK (mahalle) | — |
| 2010 | Habertürk (il/ilçe) + YSK (mahalle) | **İlçe düzeyi oy SAYILARI tahmini** (bkz. aşağı); mahalle düzeyi gerçek |
| 2007, 1988, 1987, 1982, 1961 | Wikipedia | İlçe verisi yok, gerçek oy sayıları (tahmin değil) |

**2010 referandum tahmini:** Habertürk kaynağı bu yıl için sadece oran +
sandık sayısı veriyordu, gerçek oy sayısı yoktu. İlçe/il oy sayıları **sandık
başına ~300 oy** varsayımıyla kabaca tahmin edildi (`status: estimated`,
`method: sandik_sayisi_x_300` — bkz. `sources.yml`). Yüzdeler gerçek, mutlak
sayılar yaklaşık. Bu oturumda eklenen mahalle-düzeyi YSK verisi bu tahminin
yerine geçmiyor (farklı granülerlik) ama kapsadığı mahalleler için gerçek
rakam sağlıyor.

## Yurtdışı seçmen verisi

2015 Haziran/Kasım, 2018, 2023 genel; 2017 referandumu; 2018, 2023 (1./2.
tur) CB seçimlerinde yurtdışı sandıklarının oyu Habertürk'ten ayrı bir panelde
tutuluyor, hiçbir ile atanmıyor (haritaya dahil değil). Tahmin yok, gerçek
rakamlar.

## Harita geometrisi

- **İl/ilçe sınırları:** `ttezer/turkiye-harita-verisi` (HDX kaynaklı),
  basitleştirilmiş.
- **Mahalle sınırları:** `ttezer/turkiye-harita-verisi` (25 il, belediye açık
  verisi/MAKS kaynaklı) + `osadikoglu/turkey-admin-units-osm` üzerinden
  OpenStreetMap (kalan 56 il).
- **Tarihsel dönüşümler** (Ardahan/Iğdır→Kars gibi sonradan-il-olan ilçelerin
  eski yıllarda ana ile birleştirilmesi, büyükşehir "Merkez" ilçe
  bölünmelerinin geri alınması): bunlar kaynak geometrisi değil, bu projenin
  kendi türetilmiş dönüşüm katmanı (`geo/historical/`).

## Kapsam dışı / henüz yapılmadı

- **TÜİK** (Türkiye İstatistik Kurumu) ile 2009 öncesi genel seçimlerin
  yeniden doğrulanması — ayrı, sonraki bir aşama.
- Wikipedia/Habertürk kaynaklı verilerin tek tek YSK/TÜİK ile çapraz
  doğrulanıp gerekirse değiştirilmesi.
- 2019 İstanbul BB Yenileme, 2024 Yenileme Seçimi, 2026 Ara Seçimi (tekil/özel
  seçimler) — henüz eklenmedi.
