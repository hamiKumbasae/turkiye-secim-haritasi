# Veri denetimi raporu

`python3 scripts/veri_denetimi.py` çıktısı. Veri değiştirilmez; bulgular kaynak ya da işleme kökenli olabilir.

## Denetlenen kayıtlar

| Düzey | Kayıt |
|---|---|
| mahalle | 438.520 |
| ilçe | 49.075 |
| birim | 35.952 |
| tuik | 7.639 |
| il | 6.191 |
| turkiye | 8 |

## Özet

| Bulgu | Tür | Sayı | Düzeylere göre |
|---|---|---|---|
| `KATILIM_100_USTU` | hata/kaynak | 18289 | birim 72, il 6, mahalle 18184, tuik 27 |
| `GECERLI_SECMENDEN_FAZLA` | hata/kaynak | 10648 | birim 56, ilçe 107, mahalle 10460, tuik 25 — 107 tanesi zaten belgeli |
| `OY_TOPLAMI_TUTMUYOR` | hata | 1203 | birim 625, il 97, ilçe 321, tuik 159, turkiye 1 — 374 tanesi zaten belgeli |
| `ORAN_HESAPLA_TUTMUYOR` | hata | 200 | il 184, ilçe 14, mahalle 2 — 119 tanesi zaten belgeli |
| `OY_NEGATIF_YA_DA_KESIRLI` | hata | 2 | il 2 |
| `KAZANAN_DIGER` | eksik | 3099 | ilçe 10, mahalle 3089 |
| `KAZANAN_EN_COK_OY_DEGIL` | bilgi | 414 | il 26, ilçe 60, mahalle 328 |
| `SECMEN_YOK_OY_VAR` | bilgi | 247 | birim 10, il 47, ilçe 190 |
| `KATILIM_COK_DUSUK` | bilgi | 181 | birim 2, il 5, ilçe 12, mahalle 162 |
| `IL_ILCE_TOPLAMI` | hata | 54 | il 54 |
| `MAHALLE_SECMEN_SICRAMASI` | bilgi | 194 | mahalle 194 |

## `KATILIM_100_USTU` (18289)

Katılım %100'ü aşıyor: oy kullanan kayıtlı seçmenden fazla. YSK sandık verisinde de görülür (listede kayıtlı olmayan görevliler o sandıkta oy kullanabiliyor); küçük birimlerde oranı büyütür. Sitede katılım oranı anlamlı değil.

Dosyalara göre: mahalle/2023cb1tur.json 2720, mahalle/2023.json 2693, mahalle/2018.json 2476, mahalle/2023cb2tur.json 2292, mahalle/2015Kasim.json 1867, mahalle/2015Haziran.json 1705, mahalle/2024yerel.json 893, mahalle/2014yerel.json 714, mahalle/2018cb.json 648, mahalle/2019yerel.json 562, mahalle/2011.json 541, mahalle/2017referandum.json 469 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| mahalle/2009yerel.json | Akyurt / KARAYATAK MAH. | katılım %102.7, seçmen 37, oy kullanan 38, geçerli parti oyu 34 |
| mahalle/2009yerel.json | Çubuk / KARAMAN MAH. | katılım %103.7, seçmen 27, oy kullanan 28, geçerli parti oyu 28 |
| mahalle/2009yerel.json | Çubuk / KIZILÖZ MAH. | katılım %104.44, seçmen 45, oy kullanan 47, geçerli parti oyu 46 |
| mahalle/2009yerel.json | Çubuk / TUĞLA MAH. | katılım %107.41, seçmen 27, oy kullanan 29, geçerli parti oyu 29 |
| mahalle/2009yerel.json | Kahramankazan / GÜNBAŞI MAH. | katılım %101.59, seçmen 63, oy kullanan 64, geçerli parti oyu 64 |
| mahalle/2009yerel.json | Kahramankazan / KIŞLA MAH. | katılım %100.78, seçmen 129, oy kullanan 130, geçerli parti oyu 129 |
| mahalle/2009yerel.json | Kalecik / AKCATAŞ MAH. | katılım %102.53, seçmen 79, oy kullanan 81, geçerli parti oyu 79 |
| mahalle/2009yerel.json | Kalecik / ŞEYHMAHMUT MAH. | katılım %117.65, seçmen 17, oy kullanan 20, geçerli parti oyu 20 |
| mahalle/2009yerel.json | Kalecik / TAVŞANCIK MAH. | katılım %107.56, seçmen 119, oy kullanan 128, geçerli parti oyu 127 |
| mahalle/2009yerel.json | Keçiören / BAĞLUM GÜZELYURT MAH. | katılım %100.57, seçmen 174, oy kullanan 175, geçerli parti oyu 168 |
| mahalle/2009yerel.json | Pursaklar / KARAKÖY MAH. | katılım %105.56, seçmen 36, oy kullanan 38, geçerli parti oyu 38 |
| mahalle/2009yerel.json | Sincan / ADALET MAH. | katılım %124.67, seçmen 2331, oy kullanan 2906, geçerli parti oyu 2797 |
| mahalle/2009yerel.json | Sincan / ÇİÇEKTEPE MAH. | katılım %101.94, seçmen 103, oy kullanan 105, geçerli parti oyu 105 |
| mahalle/2009yerel.json | Sincan / ESENLER MAH. | katılım %101.54, seçmen 65, oy kullanan 66, geçerli parti oyu 65 |
| mahalle/2009yerel.json | Sincan / KESİKTAŞ MAH. | katılım %102.33, seçmen 86, oy kullanan 88, geçerli parti oyu 86 |
| … | 18274 kayıt daha | |

## `GECERLI_SECMENDEN_FAZLA` (10648)

Geçerli oy kayıtlı seçmenden fazla (katılım %100 üstüyle aynı kökten).

Dosyalara göre: mahalle/2023cb1tur.json 1951, mahalle/2023cb2tur.json 1883, mahalle/2023.json 1835, mahalle/2018.json 1757, mahalle/2015Kasim.json 1455, mahalle/2015Haziran.json 1281, mahalle/2024yerel.json 298, elections/yerel/1984yerel.json 66, ek/belediye_meclisi/1999yerel.json 37, ek/beldeler/1999yerel.json 25, ek/il_genel_meclisi/1999yerel.json 12, elections/yerel/1963yerel.json 11 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| mahalle/2015Haziran.json | Çukurova / MEMİŞLİ MAH. | seçmen 50, geçerli 52 |
| mahalle/2015Haziran.json | Karaisalı / KARAHASANLI MAH. | seçmen 15, geçerli 18 |
| mahalle/2015Haziran.json | Karaisalı / KARAKUYU MAH. | seçmen 34, geçerli 36 |
| mahalle/2015Haziran.json | Karataş / İNNEPLİHÜYÜĞÜ MAH. | seçmen 128, geçerli 129 |
| mahalle/2015Haziran.json | Karataş / DEVELİÖREN MAH. | seçmen 28, geçerli 30 |
| mahalle/2015Haziran.json | Yüreğir / KÖPRÜGÖZÜ MAH. | seçmen 18, geçerli 26 |
| mahalle/2015Haziran.json | Yüreğir / KAMIŞLI MAH. | seçmen 40, geçerli 44 |
| mahalle/2015Haziran.json | Çelikhan / ALTINTAŞ KÖYÜ | seçmen 17, geçerli 18 |
| mahalle/2015Haziran.json | Çelikhan / PINARBAŞI-ÇAMLIYAYLA MAH. | seçmen 24, geçerli 29 |
| mahalle/2015Haziran.json | Çelikhan / BOZGEDİK KÖYÜ | seçmen 19, geçerli 21 |
| mahalle/2015Haziran.json | Dinar / ELDERE KÖYÜ | seçmen 28, geçerli 29 |
| mahalle/2015Haziran.json | Dinar / ALACAATLI KÖYÜ | seçmen 14, geçerli 16 |
| mahalle/2015Haziran.json | Emirdağ / TOPDERE KÖYÜ | seçmen 23, geçerli 24 |
| mahalle/2015Haziran.json | Emirdağ / DAĞINIK KÖYÜ | seçmen 23, geçerli 24 |
| mahalle/2015Haziran.json | Emirdağ / LEYLEKLİ KÖYÜ | seçmen 19, geçerli 20 |
| … | 10633 kayıt daha | |

## `OY_TOPLAMI_TUTMUYOR` (1203)

Parti oylarının toplamı geçerli oya eşit değil: bir partinin oyu eksik ya da fazla.

Dosyalara göre: ek/belediye_meclisi/1994yerel.json 195, ek/belediye_meclisi/1999yerel.json 166, ek/il_genel_meclisi/1999yerel.json 133, elections/yerel/1984yerel.json 116, ek/beldeler/1999yerel.json 90, ek/beldeler/1994yerel.json 67, elections/genel/1961.json 65, ek/il_genel_meclisi/1994yerel.json 56, elections/yerel/1994yerel.json 39, ek/belediye_meclisi/1984yerel.json 36, ek/belediye_meclisi/1989yerel.json 34, elections/yerel/1973yerel.json 30 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| ek/beldeler/1989yerel.json | Kırşehir / Kırşehir / Karahıdır | parti toplamı 467, geçerli 844 (fark -377) |
| ek/beldeler/1989yerel.json | Tekirdağ / Tekirdağ / Karacakılavuz | parti toplamı 2058, geçerli 2053 (fark +5) |
| ek/beldeler/1994yerel.json | Afyon / Sincanlı (Sinanpaşa) / Akören | parti toplamı 1098, geçerli 1241 (fark -143) |
| ek/beldeler/1994yerel.json | Afyon / Sincanlı (Sinanpaşa) / Nuhköy | parti toplamı 443, geçerli 919 (fark -476) |
| ek/beldeler/1994yerel.json | Afyon / Sincanlı (Sinanpaşa) / Serban | parti toplamı 711, geçerli 1420 (fark -709) |
| ek/beldeler/1994yerel.json | Afyon / Sincanlı (Sinanpaşa) / Tınaztepe | parti toplamı 1581, geçerli 1793 (fark -212) |
| ek/beldeler/1994yerel.json | Afyon / Sultandağı / Dereçine | parti toplamı 1222, geçerli 1617 (fark -395) |
| ek/beldeler/1994yerel.json | Afyon / Sultandağı / Karapınar | parti toplamı 1037, geçerli 1153 (fark -116) |
| ek/beldeler/1994yerel.json | Afyon / Sultandağı / Kırca | parti toplamı 606, geçerli 983 (fark -377) |
| ek/beldeler/1994yerel.json | Afyon / Sultandağı / Yakasinek | parti toplamı 994, geçerli 1318 (fark -324) |
| ek/beldeler/1994yerel.json | Aksaray / Ortaköy / Harmandalı | parti toplamı 826, geçerli 1044 (fark -218) |
| ek/beldeler/1994yerel.json | Aksaray / Ortaköy / Ozancık | parti toplamı 880, geçerli 885 (fark -5) |
| ek/beldeler/1994yerel.json | Aksaray / Ortaköy / Sarıkaman | parti toplamı 711, geçerli 1187 (fark -476) |
| ek/beldeler/1994yerel.json | Amasya / Amasya / Doğantepe | parti toplamı 782, geçerli 983 (fark -201) |
| ek/beldeler/1994yerel.json | Amasya / Amasya / Ezinepazar | parti toplamı 795, geçerli 1125 (fark -330) |
| … | 1188 kayıt daha | |

## `ORAN_HESAPLA_TUTMUYOR` (200)

Yazılı oran, oy sayısından hesaplanan orandan farklı.

Dosyalara göre: elections/genel/1954.json 49, elections/genel/1999.json 44, elections/genel/2002.json 25, elections/genel/1950.json 18, elections/genel/2007.json 16, elections/yerel/1977yerel.json 14, elections/genel/1957.json 10, elections/yerel/1999yerel.json 8, elections/genel/1995.json 4, elections/genel/1961.json 2, elections/yerel/1973yerel.json 2, mahalle/2009yerel.json 2 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| elections/genel/1950.json | plaka 4 / Ağrı | Bağımsız: yazılı %0.3, hesaplanan %0.84 |
| elections/genel/1950.json | plaka 12 / Bingöl | Bağımsız: yazılı %14.0, hesaplanan %6.09 |
| elections/genel/1950.json | plaka 13 / Bitlis | Bağımsız: yazılı %9.0, hesaplanan %16.46 |
| elections/genel/1950.json | plaka 15 / Burdur | Bağımsız: yazılı %13.3, hesaplanan %31.48 |
| elections/genel/1950.json | plaka 17 / Çanakkale | Bağımsız: yazılı %0.0, hesaplanan %0.16 |
| elections/genel/1950.json | plaka 26 / Eskişehir | CHP: yazılı %34.4, hesaplanan %34.61 |
| elections/genel/1950.json | plaka 29 / Gümüşhane | Bağımsız: yazılı %18.4, hesaplanan %16.43 |
| elections/genel/1950.json | plaka 36 / Kars | Bağımsız: yazılı %0.2, hesaplanan %0.70 |
| elections/genel/1950.json | plaka 39 / Kırklareli | CHP: yazılı %45.4, hesaplanan %46.08 |
| elections/genel/1950.json | plaka 40 / Kırşehir | Bağımsız: yazılı %4.8, hesaplanan %5.02 |
| elections/genel/1950.json | plaka 42 / Konya | CHP: yazılı %37.8, hesaplanan %40.28 |
| elections/genel/1950.json | plaka 43 / Kütahya | CHP: yazılı %39.1, hesaplanan %37.03 |
| elections/genel/1950.json | plaka 46 / Kahramanmaraş | Bağımsız: yazılı %7.5, hesaplanan %22.14 |
| elections/genel/1950.json | plaka 47 / Mardin | Bağımsız: yazılı %7.6, hesaplanan %34.68 |
| elections/genel/1950.json | plaka 51 / Niğde | CHP: yazılı %41.6, hesaplanan %43.17 |
| … | 185 kayıt daha | |

## `OY_NEGATIF_YA_DA_KESIRLI` (2)

Oy sayısı negatif ya da tam sayı değil.

Dosyalara göre: ek/senato/1979senato.json 2

| Dosya | Birim | Ayrıntı |
|---|---|---|
| ek/senato/1979senato.json | Kütahya | TİP: 0.7 |
| ek/senato/1979senato.json | Manisa | TİP: 0.5 |

## `KAZANAN_DIGER` (3099)

Kazanan 'Diğer' (ayrıştırılmamış küçük partiler toplamı).

Dosyalara göre: mahalle/2019yerel.json 1996, mahalle/2014yerel.json 952, mahalle/2009yerel.json 138, elections/yerel/1999yerel.json 6, elections/yerel/1994yerel.json 4, mahalle/2011.json 3

| Dosya | Birim | Ayrıntı |
|---|---|---|
| elections/yerel/1994yerel.json | plaka 19 / Osmancık |  |
| elections/yerel/1994yerel.json | plaka 19 / Oğuzlar |  |
| elections/yerel/1994yerel.json | plaka 34 / Küçükçekmece |  |
| elections/yerel/1994yerel.json | plaka 59 / Malkara |  |
| elections/yerel/1999yerel.json | plaka 14 / Dörtdivan |  |
| elections/yerel/1999yerel.json | plaka 53 / Çamlıhemşin |  |
| elections/yerel/1999yerel.json | plaka 58 / Gürün |  |
| elections/yerel/1999yerel.json | plaka 61 / Beşikdüzü |  |
| elections/yerel/1999yerel.json | plaka 61 / Of |  |
| elections/yerel/1999yerel.json | plaka 66 / Çayıralan |  |
| mahalle/2009yerel.json | Merkez / SITKIYE MAH. |  |
| mahalle/2009yerel.json | Elmadağ / YEŞİLDERE FATİH MAH. |  |
| mahalle/2009yerel.json | Haymana / KAYABAŞI MAH. |  |
| mahalle/2009yerel.json | Haymana / SEYRAN MAH. |  |
| mahalle/2009yerel.json | Alanya / BÜYÜKHASBAHÇE MAH. |  |
| … | 3084 kayıt daha | |

## `KAZANAN_EN_COK_OY_DEGIL` (414)

Kazanan, en çok oy alan parti değil. Resmi sonuç sandık toplamından farklı olabilir (itiraz, yeniden sayım, aday düzeyinde belirlenen kazanan); tek tek bakılmalı.

Dosyalara göre: mahalle/2024yerel.json 281, mahalle/2023.json 28, elections/yerel/1968yerel.json 19, elections/yerel/2024yerel.json 17, elections/yerel/1973yerel.json 11, mahalle/2015Haziran.json 11, elections/yerel/1963yerel.json 8, elections/yerel/1977yerel.json 7, mahalle/2018.json 6, elections/genel/1999.json 4, elections/genel/1995.json 3, elections/yerel/2009yerel.json 3 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| elections/genel/1950.json | plaka 47 / Mardin | kazanan CHP 44882, en çok oy Bağımsız 47771 |
| elections/genel/1950.json | plaka 52 / Ordu | kazanan CHP 61111, en çok oy DP 61184 |
| elections/genel/1965.json | plaka 49 / Muş | kazanan Bağımsız 10701, en çok oy Diğer 12027 |
| elections/genel/1969.json | plaka 56 / Siirt | kazanan AP 19225, en çok oy Diğer 19274 |
| elections/genel/1969.json | plaka 62 / Tunceli | kazanan AP 9972, en çok oy Diğer 16541 |
| elections/genel/1987.json | plaka 21 / Diyarbakır | kazanan SHP 76074, en çok oy Diğer 86094 |
| elections/genel/1987.json | plaka 65 / Van | kazanan ANAP 43927, en çok oy Diğer 63680 |
| elections/genel/1995.json | plaka 40 / Kırşehir | kazanan ANAP 24351, en çok oy Diğer 25522 |
| elections/genel/1995.json | plaka 62 / Tunceli | kazanan CHP 8434, en çok oy Diğer 9857 |
| elections/genel/1995.json | plaka 76 / Iğdır | kazanan HADEP 10863, en çok oy Diğer 11286 |
| elections/genel/1999.json | plaka 24 / Erzincan | kazanan MHP 27745, en çok oy Diğer 28575 |
| elections/genel/1999.json | plaka 31 / Hatay | kazanan MHP 128387, en çok oy Diğer 145779 |
| elections/genel/1999.json | plaka 58 / Sivas | kazanan FP 88827, en çok oy Diğer 99246 |
| elections/genel/1999.json | plaka 62 / Tunceli | kazanan Bağımsız 8052, en çok oy Diğer 9466 |
| elections/yerel/1955yerel.json | plaka 11 / Bilecik | kazanan DP 7, en çok oy Bağımsız 11 |
| … | 399 kayıt daha | |

## `SECMEN_YOK_OY_VAR` (247)

Kayıtlı seçmen sayısı yok ya da 0, ama oy var; katılım hesaplanamaz.

Dosyalara göre: elections/yerel/1984yerel.json 96, elections/yerel/1994yerel.json 79, elections/yerel/1955yerel.json 26, elections/yerel/1999yerel.json 14, ek/il_genel_meclisi/1984yerel.json 8, meclis_harita/1984yerel_igm.json 6, meclis_harita/1984yerel_bm.json 3, ek/belediye_meclisi/1984yerel.json 3, elections/yerel/1977yerel.json 2, elections/yerel/1989yerel.json 2, elections/genel/1957.json 1, elections/genel/1961.json 1 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| elections/genel/1957.json | plaka 54 / Sakarya | seçmen 0, oy 119167 |
| elections/genel/1961.json | plaka 54 / Sakarya | seçmen 0, oy 133389 |
| elections/genel/1965.json | plaka 54 / Sakarya | seçmen 0, oy 125039 |
| elections/genel/1969.json | plaka 54 / Sakarya | seçmen 0, oy 120124 |
| elections/genel/1973.json | plaka 54 / Sakarya | seçmen 0, oy 136455 |
| elections/genel/1977.json | plaka 54 / Sakarya | seçmen 0, oy 194390 |
| elections/yerel/1950yerel.json | plaka 16 / Bursa | seçmen None, oy 19258 |
| elections/yerel/1955yerel.json | plaka 4 / Ağrı | seçmen None, oy 21 |
| elections/yerel/1955yerel.json | plaka 10 / Balıkesir | seçmen None, oy 27 |
| elections/yerel/1955yerel.json | plaka 11 / Bilecik | seçmen None, oy 18 |
| elections/yerel/1955yerel.json | plaka 12 / Bingöl | seçmen None, oy 1219 |
| elections/yerel/1955yerel.json | plaka 15 / Burdur | seçmen None, oy 4568 |
| elections/yerel/1955yerel.json | plaka 17 / Çanakkale | seçmen None, oy 1800 |
| elections/yerel/1955yerel.json | plaka 18 / Çankırı | seçmen None, oy 22 |
| elections/yerel/1955yerel.json | plaka 21 / Diyarbakır | seçmen None, oy 10647 |
| … | 232 kayıt daha | |

## `KATILIM_COK_DUSUK` (181)

Katılım %20'nin altında; kaynak ya da eşleştirme hatası olabilir.

Dosyalara göre: mahalle/2010referandum.json 123, elections/referandum/2010referandum.json 12, mahalle/2015Haziran.json 9, mahalle/2015Kasim.json 6, mahalle/2018.json 5, mahalle/2023.json 5, mahalle/2023cb1tur.json 5, elections/yerel/1955yerel.json 4, mahalle/2011.json 4, mahalle/2019yerel.json 2, mahalle/2014cb.json 1, mahalle/2018cb.json 1 …

| Dosya | Birim | Ayrıntı |
|---|---|---|
| elections/referandum/2010referandum.json | plaka 30 / Hakkari | katılım %9.05, seçmen 128572 |
| elections/referandum/2010referandum.json | plaka 4 / Doğubayazıt | katılım %12.04, seçmen 59064 |
| elections/referandum/2010referandum.json | plaka 21 / Kocaköy | katılım %15.51, seçmen 8174 |
| elections/referandum/2010referandum.json | plaka 21 / Lice | katılım %8.5, seçmen 15483 |
| elections/referandum/2010referandum.json | plaka 21 / Silvan | katılım %18.32, seçmen 43591 |
| elections/referandum/2010referandum.json | plaka 30 / Merkez | katılım %4.99, seçmen 43522 |
| elections/referandum/2010referandum.json | plaka 30 / Yüksekova | katılım %2.66, seçmen 56589 |
| elections/referandum/2010referandum.json | plaka 30 / Çukurca | katılım %4.13, seçmen 5183 |
| elections/referandum/2010referandum.json | plaka 47 / Nusaybin | katılım %10.45, seçmen 58614 |
| elections/referandum/2010referandum.json | plaka 65 / Başkale | katılım %14.19, seçmen 28853 |
| elections/referandum/2010referandum.json | plaka 73 / Cizre | katılım %11.33, seçmen 54333 |
| elections/referandum/2010referandum.json | plaka 73 / Silopi | katılım %16.9, seçmen 47047 |
| elections/yerel/1955yerel.json | plaka 14 / Bolu | katılım %14.7, seçmen 5255 |
| elections/yerel/1955yerel.json | plaka 35 / İzmir | katılım %12.17, seçmen 138114 |
| elections/yerel/1955yerel.json | plaka 39 / Kırklareli | katılım %16.8, seçmen 8440 |
| … | 166 kayıt daha | |

## `IL_ILCE_TOPLAMI` (54)

İl kaydı, ilçelerinin toplamından %1'den fazla farklı (seçmen ya da geçerli oy).

Dosyalara göre: elections/genel/1973.json 11, elections/genel/1977.json 8, elections/genel/1995.json 7, elections/genel/1999.json 7, elections/referandum/1987referandum.json 5, elections/referandum/1988referandum.json 4, elections/genel/1987.json 3, elections/genel/2002.json 3, elections/referandum/1982referandum.json 3, elections/genel/1965.json 1, elections/genel/1969.json 1, elections/genel/1991.json 1

| Dosya | Birim | Ayrıntı |
|---|---|---|
| elections/genel/1965.json | Mersin | seçmen: il 212437, ilçeler toplamı 207443 (-2.4%) |
| elections/genel/1969.json | Hakkari | seçmen: il 38391, ilçeler toplamı 36392 (-5.2%) |
| elections/genel/1973.json | Ankara | seçmen: il 786398, ilçeler toplamı 985132 (+25.3%) |
| elections/genel/1973.json | Artvin | seçmen: il 102190, ilçeler toplamı 101053 (-1.1%) |
| elections/genel/1973.json | Aydın | seçmen: il 283572, ilçeler toplamı 288250 (+1.6%) |
| elections/genel/1973.json | Bitlis | seçmen: il 60300, ilçeler toplamı 67415 (+11.8%) |
| elections/genel/1973.json | Gaziantep | seçmen: il 268722, ilçeler toplamı 239914 (-10.7%) |
| elections/genel/1973.json | Gümüşhane | geçerli oy: il 78124, ilçeler toplamı 80132 (+2.6%) |
| elections/genel/1973.json | Hatay | seçmen: il 251734, ilçeler toplamı 248906 (-1.1%) |
| elections/genel/1973.json | Kastamonu | seçmen: il 285894, ilçeler toplamı 222934 (-22.0%) |
| elections/genel/1973.json | Nevşehir | seçmen: il 106628, ilçeler toplamı 102140 (-4.2%) |
| elections/genel/1973.json | Nevşehir | geçerli oy: il 60572, ilçeler toplamı 57866 (-4.5%) |
| elections/genel/1973.json | Niğde | seçmen: il 183728, ilçeler toplamı 189114 (+2.9%) |
| elections/genel/1977.json | Ankara | seçmen: il 1328719, ilçeler toplamı 1358336 (+2.2%) |
| elections/genel/1977.json | Ankara | geçerli oy: il 897872, ilçeler toplamı 908521 (+1.2%) |
| … | 39 kayıt daha | |

## `MAHALLE_SECMEN_SICRAMASI` (194)

Aynı mahallenin seçmeni ardışık iki seçim arasında 5 kattan fazla değişiyor (eşleştirme hatası ya da gerçek nüfus değişimi).

Dosyalara göre: mahalle/2014cb.json 34, mahalle/2019yerel.json 34, mahalle/2017referandum.json 23, mahalle/2024yerel.json 22, mahalle/2010referandum.json 20, mahalle/2018.json 18, mahalle/2018cb.json 14, mahalle/2023.json 13, mahalle/2014yerel.json 12, mahalle/2015Haziran.json 4

| Dosya | Birim | Ayrıntı |
|---|---|---|
| mahalle/2010referandum.json | Bolvadin / TAŞAĞIL MAH. | önceki seçimde 386, bu seçimde 56 |
| mahalle/2010referandum.json | Merkez / MURAT MAH. | önceki seçimde 1987, bu seçimde 382 |
| mahalle/2010referandum.json | Gemlik / HAMİDİYE MAH. | önceki seçimde 9461, bu seçimde 185 |
| mahalle/2010referandum.json | İnegöl / HAMİDİYE MAH. | önceki seçimde 9348, bu seçimde 145 |
| mahalle/2010referandum.json | İnegöl / OSMANİYE MAH. | önceki seçimde 3287, bu seçimde 105 |
| mahalle/2010referandum.json | İnegöl / TURGUTALP MAH. | önceki seçimde 6976, bu seçimde 254 |
| mahalle/2010referandum.json | Mustafakemalpaşa / HAMİDİYE MAH. | önceki seçimde 4530, bu seçimde 113 |
| mahalle/2010referandum.json | Yenişehir / ÜÇKUYU MAH. | önceki seçimde 478, bu seçimde 3702 |
| mahalle/2010referandum.json | Nizip / BELKIS MAH. | önceki seçimde 5365, bu seçimde 92 |
| mahalle/2010referandum.json | Şehitkamil / BOYNO MAH. | önceki seçimde 8542, bu seçimde 151 |
| mahalle/2010referandum.json | Tarsus / REŞADİYE MAH. | önceki seçimde 2545, bu seçimde 235 |
| mahalle/2010referandum.json | Merkez / KOCAHIDIR MAH. | önceki seçimde 2747, bu seçimde 206 |
| mahalle/2010referandum.json | Kalkandere / SOĞUKSU MAH. | önceki seçimde 288, bu seçimde 53 |
| mahalle/2010referandum.json | Divriği / DEMİRDAĞ MAH. | önceki seçimde 656, bu seçimde 52 |
| mahalle/2010referandum.json | Merkez / DÖRTEYLÜL MAH. | önceki seçimde 4546, bu seçimde 48 |
| … | 179 kayıt daha | |
