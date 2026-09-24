# Türkçe Wikipedia — il alt makaleleri (ham wikitext anlık görüntüsü)

**Kaynak:** tr.wikipedia.org, `Kategori:İllere göre <yıl> Türkiye <tür> seçimleri`
kategorilerinin tüm üyeleri ve her seçimin ulusal ana makalesi. MediaWiki API
(`action=query&prop=revisions`, ham wikitext) ile çekildi.

**İndirilme tarihi:** 2026-09-24. **Lisans:** CC BY-SA 4.0 (Wikipedia katkıcıları).

**Script:** `scripts/pipelines/wikipedia_arsiv/fetch_wikipedia.py` (mevcut
klasörleri atlar; `--yenile` ile yeniden çeker).

## Yapı

```
<tür>/<seçim>/_index.json     başlık -> {dosya, pageid, revid, timestamp, url}
<tür>/<seçim>/<slug>.wiki     o revizyondaki ham wikitext (değiştirilmedi)
<tür>/<seçim>/_ana_makale.wiki  seçimin ulusal ana makalesi
```

`<tür>`: `genel` (1923-2023, 27 seçim), `yerel` (1930-2024, 20 seçim),
`senato` (1961-1979, 8 seçim), `cumhurbaskanligi` (2014). Toplam 56 seçim,
3.579 sayfa. Seçim anahtarları `data/normalized` ile aynıdır (`1968yerel`,
`2015Haziran`, `1961senato` …).

Wikipedia değişebilen bir kaynaktır. Her sayfanın o anki hâli `revid` ile
kalıcı olarak bulunabilir: `https://tr.wikipedia.org/w/index.php?oldid=<revid>`.

## Neden burada

Wikipedia **ikincil** bir kaynaktır (`status: reported`). Bu arşivden haritaya
yalnızca projede **başka hiçbir kaynağı olmayan** kayıtlar alındı:

- 1950-1977 yerel seçimlerinin ilçe belediye başkanlıkları
  (`data/normalized/elections/yerel/*.json`, satır `kaynak.ana = "wikipedia"`)
- Senato, seçilen milletvekilleri, beldeler (`data/normalized/ek/`, haritaya bağlı değil)

Zaten resmi kaynağı olan seçimlerin sayfaları da arşivde tutuluyor. Bunlardan
hiçbir değer normalize veriye yazılmadı; yalnızca çapraz kontrol ve belde /
seçilen gibi projede olmayan bilgiler için saklanıyor.

Ayrıştırılmış hâl (her seçim, kaynağın verdiği her şey): `data/kaynaklar/wikipedia/`.
