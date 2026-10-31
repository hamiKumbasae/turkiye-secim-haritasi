# What people ask about Turkish election results — research behind the question bank

Goal: find out which questions real users ask about Turkish election results, so the text-to-SQL chatbot is
evaluated (and later templated) on realistic traffic instead of on questions its author found interesting.
Output: [`eval/soru_bankasi.yaml`](../eval/soru_bankasi.yaml) (287 questions, verified SQL),
[`eval/soru_kaliplari.yaml`](../eval/soru_kaliplari.yaml) (25 ranked patterns, see [SORU_KALIPLARI.md](SORU_KALIPLARI.md)).

## Method

* ~30 web searches (Turkish, some English) for news result pages and their question-style headings
  ("X ne kadar oy aldı?", "hangi ilde kim kazandı?"), FAQ boxes, data-journalism maps, post-election
  analysis pieces, Wikipedia result pages and forum threads. 38 sources are tagged in the bank (S01–S38 below):
  23 were opened and read, 15 are used through their search-result title/snippet only (marked *snippet*).
* Ekşi Sözlük entries returned an error when fetched and Reddit (r/Turkey, r/turkeyjerky) is not reachable from
  this environment, so forum phrasing is under-represented; Ekşi titles that surfaced in search
  ("31 mart 2024 seçimi en şaşırtıcı sonucu") match the news-headline question types below.
* No text was copied: every question in the bank is a paraphrased, newly written Turkish question of a type
  seen in the sources. `frequency` (yüksek/orta/düşük) is a judgement of how often that question *type* recurs
  across the sources (headline/FAQ repetition across outlets), recorded with the source keys in `evidence`.
* Every answerable question got a hand-written SQL query that was executed on the local MariaDB copy; results are
  frozen in `eval/soru_bankasi_results.json` and re-checked by `tests/test_soru_bankasi.py`.

## Top question types (by pattern weight in the bank)

| # | Type | Typical phrasing (paraphrased) | Answerable |
|---|---|---|---|
| 1 | Result of one unit | "İskilip seçim sonuçları 2024", "Rize'de AKP kaç aldı?" — the news-site "il il / ilçe ilçe" page | yes |
| 2 | National vote / share | "Memleket Partisi ne kadar oy aldı?", "Erdoğan yüzde kaç aldı?" | yes (caveat 2018/2023) |
| 3 | How many places won | "CHP kaç il/büyükşehir/ilçe kazandı?", "hangi aday kaç ilde birinci?" | yes / partial |
| 4 | Top/bottom N units | "Erdoğan'ın en yüksek oy aldığı 10 il", "Kılıçdaroğlu'nun en az oy aldığı iller" | yes |
| 5 | Seats | "hangi parti kaç milletvekili çıkardı?", "Memleket vekil çıkardı mı?" | yes |
| 6 | Referendum Evet/Hayır | "İstanbul, Ankara, İzmir ne dedi?", "kaç ilde Hayır çıktı?" | yes |
| 7 | Margin / close races | "en az oy farkı hangi ilçelerde?", "kaç oy farkla kazandı?" | yes |
| 8 | Turnout | "katılımın en yüksek olduğu il", "üç büyükşehirde katılım" | yes / partial (national) |
| 9 | Time series | "AK Parti'nin seçim karnesi", "CHP en son ne zaman birinci oldu?" | yes |
| 10 | Swing & flips | "el değiştiren iller", "il il 1 Kasım–24 Haziran oy değişimleri", "kim kime oy kaptırdı" | yes |

Further recurring types: first vs second round (S15, S31), candidate vs party vote in the same province (S17),
referendum vs presidential vote (S04), abroad vote (S13, S25), regional and earthquake-zone aggregates (S26, S27),
leaders' home provinces (S16), and follow-ups/ambiguous questions ("2015 seçimi", "Erdoğan 2023'te yüzde kaç").

## What users want that the data cannot answer

43 bank questions (15 %) are deliberately unanswerable; the chatbot should call `cannot_answer`
("bu veri bende yok") instead of guessing:

* **Below the neighbourhood**: ballot-box results ("sandığımdan kaç oy çıktı", S19), electoral districts
  (İstanbul 1. bölge), abroad by country (S25), customs gates.
* **People, not places**: elected MPs' and mayors' names, candidate lists and biographies (names are stored only
  for 1950–1989 local races).
* **Voter profiles and polls**: age, gender, ethnicity, education, first-time voters (S28), poll leads, "who did
  İnce's voters go to" (S29) — these come from surveys, not results.
* **Races we do not store**: municipal/provincial council votes (the figure media call "Türkiye geneli yerel oy
  oranı", S20, S23), belde, muhtar, by-elections, senate, the 23 June 2019 İstanbul re-run, pre-1950.
* **Not results**: invalid-vote counts, objections/YSK decisions (S37), election calendar, legal reasons for the 7 %
  threshold, "why did X lose".

23 more questions are **partial**: the SQL is correct but the answer must carry a caveat (`reason` field).

## Data pitfalls found while writing the gold SQL

These are now in the prompt's domain notes (`secim_chatbot/prompts.py`):

1. **Alliance votes are not distributed.** In 2018/2023 the `Cumhur/Millet İttifakı` rows hold alliance-only votes,
   so party totals are below YSK's official figures (AK Parti 2018: 41.84 % vs official 42.56 %). Alliance
   membership is not stored (2023: DEVA, Gelecek, SP, DP ran on CHP lists and have no rows).
2. **`Diğer` is an aggregate** of small parties and can be the largest row (Tunceli 1999); never rank it.
3. **`birim.kazanan` ≠ top vote row** in 86 il/ilçe rows (excluding `Diğer`) (mazbata decisions, recounts): 1963 İstanbul, 2024 Kütahya
   (kazanan CHP, but the vote rows put MHP 27 votes ahead), Kırklareli, Hakkari and 14 districts in 2024. "Who won"
   must use `kazanan`; the 2024 cases are worth checking against YSK final results.
4. **Local elections = mayoral races only**; neighbourhood rows in local elections are the district mayoral vote;
   the 2019 İstanbul row is the annulled 31 March election.
5. **No abroad row for 2014cb** (the old note said "from 2014"); abroad exists from June 2015.
6. **Turnout**: no national row and `oy_kullanan` is empty at province level; a voter-weighted mean of provincial
   turnout is a close approximation (2023: 86.75 %). Neighbourhood turnout exceeds 100 % in thousands of rows.
7. **Independents**: in 2007/2011 DTP/BDP-backed independents appear partly under the party name (2007: DTP 12
   seats + Bağımsız 14). The old note's `'BĞMSZ'` spelling does not exist in the data.
8. **Names**: district renames (Eyüp → Eyüpsultan, with a historical geom_id before 2007); duplicated district
   names (51 × Merkez, Yenişehir in 3 provinces, Ereğli, Gölbaşı …) and neighbourhood names (13 × Atakent);
   suffixed historical party codes (`YTP61`, `MP62`, `MP92`) and `DP` meaning different parties in 1950 and 1973.
9. **1950–1957** have no district rows and use the list (majority) system: a party can show 100 % in a province.
10. No region / metropolitan / earthquake-zone flags; the bank hard-codes documented plate lists (marked partial).

## Sources

| Key | Source | Used as |
|---|---|---|
| S01 | Milliyet — 2024'te el değiştiren iller | https://www.milliyet.com.tr/galeri/2024-yerel-secimlerinde-hangi-illerde-partiler-el-degistirdi-iste-yerel-secim-sonuclarina-gore-el-degistiren-iller-7106379 |
| S02 | Cumhuriyet — Memleket Partisi ne kadar oy aldı, vekil çıkardı mı | https://www.cumhuriyet.com.tr/siyaset/memleket-partisi-ne-kadar-oy-aldi-memleket-partisi-milletvekili-cikardi-mi-muharrem-ince-ne-kadar-oy-aldi-2081685 |
| S03 | Journo — 2023 district maps (shares, margin) | https://www.journo.com.tr/turkey-elections-results-district-maps |
| S04 | Takvim — referandumda Hayır deyip Erdoğan'a oy veren iller (+ Hürriyet: Antalya'da 15 ilçe Hayır, *snippet*) | https://www.takvim.com.tr/guncel/2018/06/26/referandumda-hayir-deyip-24-haziran-secimlerinde-erdogana-oy-veren-iller-hangileri |
| S05 | BirGün — İstanbul ilçelerinde durum nasıl değişti (2024) | https://www.birgun.net/haber/detaylarla-istanbul-ilcelerde-durum-nasil-degisti-518795 |
| S06 | CNN Türk — 1950–2002 genel seçim haritaları | https://cnnturk.com/turkiye/1950-2002-genel-secim-haritasi-627728 |
| S07 | Gazete Birlik — CHP'nin belediye/büyükşehir/ilçe sayısı | https://www.gazetebirlik.com/gundem/chpnin-belediye-sayisi-kac-buyuksehir-sayisi-kac-oldu-hangi-illeri-aldi-ilce-sayisi-ne/1052194 |
| S08 | bianet — il il 1 Kasım–24 Haziran oy değişimleri | https://bianet.org/haber/il-il-1-kasim-24-haziran-partilerin-oy-degisimleri-198670 |
| S09 | Medyascope — 24 Haziran haritası: kim kime nerede oy kaptırdı | https://medyascope.tv/2018/06/26/24-haziran-secimleri-haritasinin-analizi-kim-kime-nerede-oy-kaptirdi-1-bolum-akp-mhp-iyi-parti/ |
| S10 | Wikipedia — Results breakdown, June 2015 | https://en.wikipedia.org/wiki/Results_breakdown_of_the_June_2015_Turkish_general_election |
| S11 | Hürriyet — 7 Haziran'dan 1 Kasım'a neler değişti | https://www.hurriyet.com.tr/bilgi/7-hazirandan-1-kasima-neler-degisti-40008997 |
| S12 | NTV — Türkiye geneli seçmen sayısı, katılımın en yüksek olduğu il | https://www.ntv.com.tr/2023-secim/turkiye-geneli-secmen-sayisi-2023-secimlerde-kac-kisi-oy-kullandi-ysk-secmen-sorgulama,_ijlMZ_YcEKDhvTdEGquUw |
| S13 | Evrensel — Seçim sonucunu yurt dışı oyları mı belirledi | https://www.evrensel.net/haber/491073/secim-sonucunu-yurt-disi-oylari-mi-belirledi |
| S14 | Gazete Birlik — en az oy farkı İstanbul'un hangi ilçelerinde | https://www.gazetebirlik.com/istanbul-haberleri/en-az-oy-farki-istanbulun-hangi-ilcelerinde-oldu-31-mart-2024/169893 |
| S15 | CNN Türk — Kılıçdaroğlu'nun oy kaybettiği ve en az oy aldığı iller | https://cnnturk.com/turkiye/kilicdaroglunun-oy-kaybettigi-ve-en-az-oy-aldigi-iller |
| S16 | CNN Türk — liderlerin memleketlerinde oylar | https://www.cnnturk.com/video/turkiye/liderlerin-memleketlerinde-oylar-nasil-2010583 |
| S17 | Serbestiyet — 73 ilde hem Erdoğan'ın hem AK Parti'nin oyları düştü | https://serbestiyet.com/haberler/73-ilde-hem-erdoganin-hem-ak-partinin-oylari-dustu-128549/ |
| S18 | Serbestiyet / Doğruluk Payı — genel seçimlerin en yüksek 10 oy oranı | https://serbestiyet.com/haberler/turkiye-genel-secimlerinin-en-yuksek-10-oy-orani-ak-parti-dort-secimle-birinci-sirada-122123/ |
| S19 | NTV — sandığımdan hangi adaya kaç oy çıktı | https://www.ntv.com.tr/2023-secim/galeri-sandigimdan-hangi-adaya-kac-oy-cikti-sandik-sonuclarini-nasil-ogrenirim-liderlerin-oy-kullandiklarin-sandiklarin-sonuclari,dYiPMvv9oUa9_xSigtxmzQ |
| S20 | Habertürk — CHP 47 yıl sonra birinci parti | https://www.haberturk.com/son-dakika-chp-47-yil-sonra-birinci-parti-oldu-3674251 |
| S21 | Memurlar.net — AK Parti'nin seçim karnesi | https://www.memurlar.net/haber/1065021/ak-parti-nin-secim-karnesi.html |
| S22 | Gazete Birlik — seçimle ilgili merak edilenler (FAQ) | https://www.gazetebirlik.com/gundem/secimlere-iliskin-bilgilere-nereden-ulasabilirim-secim-ile-ilgili-merak-edilenler-95798/95798 |
| S23 | Wikipedia — 2024 Turkish local elections | https://en.wikipedia.org/wiki/2024_Turkish_local_elections |
| S24 | NTV — Seçim 2023: hangi ilde kim kazandı (*snippet*) | https://www.ntv.com.tr/2023-secim/secim-2023-hangi-ilde-kim-kazandi,yYK8ww326UqGYpLeJOKj3A |
| S25 | CNN Türk — yurt dışı oyları ülke ülke (*snippet*) | https://cnnturk.com/dunya/14-mayis-secimlerinde-yurt-disi-oylarinda-son-durum-hangi-ulkede-kim-onde-iste-ulke-ulke-alinan-oy-oranlari-2006313 |
| S26 | Yeni Şafak — bölge bölge ittifak sonuçları (*snippet*) | https://www.yenisafak.com/secim-2023/karadeniz-bolgesi-ittifak-secim-sonuclari |
| S27 | NTV — deprem bölgesi seçim sonuçları (*snippet*) | https://www.ntv.com.tr/2023-secim/deprem-bolgesi-secim-sonuclari-aciklandi-28-mayis-2023-turkiye-cumhurbaskanligi-deprem-bolgesi-secim-sonucu-ve-oy-sonuclari,UiVYvXTWJUWrTb_BxxfnWg |
| S28 | Halk TV — ilk kez oy kullanacak genç sayısı (*snippet*) | https://halktv.com.tr/turkiye/bir-milyon-32-bin-610-genc-ilk-kez-oy-kullanacak-816532h |
| S29 | bianet — KONDA seçmen analizi (*snippet*) | https://bianet.org/haber/konda-secim-sonuclari-kutuplasmis-bir-turkiye-ortaya-cikariyor-280088 |
| S30 | Medyascope — İmamoğlu 39 ilçenin 28'inde önde (23 Haziran 2019) (*snippet*) | https://medyascope.tv/2019/06/24/ekrem-imamoglu-39-ilcenin-28inde-secim-yarisini-onde-tamamladi/ |
| S31 | Medyascope — Doğu ve Güneydoğu'da katılım düştü, iki tur farkı (*snippet*) | https://medyascope.tv/2023/05/29/dogu-ve-guneydoguda-secime-katilim-ortalama-yuzde-bes-dustu-erdogan-10-ilde-kilicdaroglu-sadece-sirnakta-oyunu-artirdi/ |
| S32 | GZT — Erdoğan'ın en yüksek oy aldığı 10 il (*snippet*) | https://www.gzt.com/gundem/cumhurbaskani-erdoganin-en-yuksek-oy-aldigi-10-il-belli-oldu-2037536 |
| S33 | NTV — seçim yarışını 1 oy farkla kazandı (*snippet*) | https://www.ntv.com.tr/turkiye/secim-yarisini-1-oy-farkla-kazandi,zJPU2-3jNUWXgFPHnMB6CA |
| S34 | Takvim — seçim barajı yüzde kaç, %50+1 (*snippet*) | https://www.takvim.com.tr/haberler/2023/05/14/14-mayis-2023-secim-baraji-yuzde-kac-secim-baraji-var-mi-nedir-ne-anlama-geliyor-501-ne-demek-2-tur-icin-oy-orani |
| S35 | Ekonomist — İYİ Parti'nin kazandığı tek il (*snippet*) | https://www.ekonomist.com.tr/haberler/iyi-parti-nin-kazandigi-tek-il--48901 |
| S36 | Milliyet — hangi ilde kaç seçmen var (*snippet*) | https://milliyet.com.tr/galeri/son-dakika-hangi-ilde-kac-secmen-oy-kullanacak-iste-il-il-secmen-sayisi-6934006 |
| S37 | Duvar English — YSK official results, re-runs in seven constituencies (*snippet*) | https://duvarenglish.com/turkeys-election-council-announces-official-results-rules-re-election-in-seven-constituencies-news-64303 |
| S38 | CNN Türk — il il oylar nasıl değişti (*snippet*) | https://cnnturk.com/turkiye/il-il-oylar-nasil-degisti-626338 |
