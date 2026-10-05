# 1963–1977 yerel seçim: depo verisi ile DİE kitaplarının karşılaştırması

Üreten: `scripts/pipelines/tuik_arsiv/kitap_dogrula_1963_1977.py` (yalnız rapor, veriye dokunmaz). Satır satır sonuç: `data/kaynaklar/tuik/yerel/<seçim>/kitap_dogrulama.json`.

Karşılaştırılan: belediye başkanlığı seçimi, il satırı (il merkezi belediyesi) ve ilçe satırları (ilçe merkezi belediyesi). Depodaki bu yılların verisi Vikipedi il sayfalarından; o sayfalar bu kitapları kaynak gösteriyor. İl genel meclisi ve belediye meclisi depoda yok, karşılaştırılmadı.

## Özet

| Seçim | Kitap | Satır | birebir | kitap_ic_tutarsizlik | fark | farkli | kismi | bulunamadi |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1963yerel | DİE, Mahalli Seçimler Sonuçları, 17 Kasım 1963 (Yayın No. 474, 1965) | 687 | 225 | 294 | 61 | 0 | 101 | 6 |
| 1968yerel | DİE, Mahalli Seçimler Sonuçları, 2 Haziran 1968 (Yayın No. 555, 1969) | 686 | 287 | 285 | 38 | 34 | 26 | 16 |
| 1973yerel | DİE, Mahalli Seçimler Sonuçları, 9 Aralık 1973 (Yayın No. 716, 1974) | 687 | 506 | 30 | 49 | 3 | 93 | 6 |
| 1977yerel | DİE, Yerel Seçim Sonuçları, 11 Aralık 1977 (1979) | 688 | 554 | 14 | 28 | 15 | 74 | 3 |

Durumlar:

- **birebir**: Satırın bütün değerleri (sandık, seçmen, geçerli oy, her partinin oyu) kitapta aynen var.
- **kitap_ic_tutarsizlik**: Partilerin oyu kitapla aynı; yalnız geçerli oy farklı. Kitabın bastığı geçerli oy kendi parti toplamını tutmuyor (DİE açıklamasındaki tutanak farkı), depo ise geçerli oyu parti toplamı olarak almış. Depoda hata değil.
- **fark**: Satır kitapta bulundu, bir-iki alan farklı (aşağıda listeli).
- **farkli**: Belediye kitapta sandık+seçmen ile bulundu ama oylar geniş ölçüde farklı (aşağıda listeli).
- **kismi**: Bir kısmı doğrulandı (örnek: 1963'te sandık/seçmen ya da 1973/77'de sol yüz); kalan kısım taramada okunamıyor ya da bulunamadı. Okunan her değer birebir.
- **bulunamadi**: Kitabın metin katmanında satır bulunamadı (tarama/OCR).

Kitaptaki değer, kitabın kendi yüzdesiyle (1973/1977) ya da kendi toplamıyla tutuyorsa **destekli** sayılır: büyük olasılıkla depodaki (Vikipedi) değer yanlış. Destekli değilse fark tarama okumasından da gelebilir; sayfaya bakılmalı.

## Destekli farklar (depo değeri büyük olasılıkla yanlış)

| Seçim | İl | Belediye | Alan | Depo | Kitap | PDF sayfa |
|---|---|---|---|---:|---:|---:|
| 1963 | Adana | Adana (il merkezi) | Bağımsız | 877 | 336 | 11 |
| 1963 | Kırşehir | Kırşehir (il merkezi) | Bağımsız | 2153 | 2647 | 1061 |
| 1963 | Erzurum | Tortum | AP | 371 | 366 | 657 |
| 1963 | Erzurum | Tortum | Bağımsız | 366 | 371 | 657 |
| 1963 | Zonguldak | Devrek | Bağımsız | 1110 | 370 | 1765 |
| 1963 | Zonguldak | Ulus | AP | 200 | 254 | 1765 |
| 1963 | Zonguldak | Ulus | CHP | 254 | 200 | 1765 |
| 1963 | Çanakkale | Biga | Bağımsız | 750 | 375 | 443 |
| 1968 | Uşak | Uşak (il merkezi) | Bağımsız | 1546 | 1344 | 1426 |
| 1968 | Bursa | İznik | AP | 1526 | 1527 | 354 |
| 1968 | Hatay | Dörtyol | AP | 1181 | 1214 | 688 |
| 1968 | Hatay | Dörtyol | CHP | 1214 | 1181 | 688 |
| 1968 | Hatay | İskenderun | MP62 | 1 | 63 | 689 |
| 1968 | Hatay | Reyhanlı | Bağımsız | 3646 | 1823 | 688 |
| 1968 | Sakarya | Akyazı | AP | 1337 | 1693 | 1182 |
| 1968 | Trabzon | Of | AP | 547 | 514 | 1357 |
| 1973 | Adana | Adana (il merkezi) | Bağımsız | 1439 | 1660 | 53 |
| 1973 | Afyonkarahisar | Afyonkarahisar (il merkezi) | Bağımsız | 5302 | 6434 | 55 |
| 1973 | Ağrı | Ağrı (il merkezi) | Bağımsız | 553 | 771 | 57 |
| 1973 | Antalya | Antalya (il merkezi) | Bağımsız | 5883 | 6222 | 61 |
| 1973 | Aydın | Aydın (il merkezi) | Bağımsız | 103 | 181 | 63 |
| 1973 | Bingöl | Bingöl (il merkezi) | Bağımsız | 822 | 2078 | 67 |
| 1973 | Bursa | Bursa (il merkezi) | Bağımsız | 1391 | 2566 | 69 |
| 1973 | Çorum | Çorum (il merkezi) | Bağımsız | 4511 | 5109 | 73 |
| 1973 | Elazığ | Elazığ (il merkezi) | Bağımsız | 5179 | 11556 | 79 |
| 1973 | Mersin | Mersin (il merkezi) | Bağımsız | 5616 | 7140 | 89 |
| 1973 | Kastamonu | Kastamonu (il merkezi) | Bağımsız | 914 | 3043 | 95 |
| 1973 | Rize | Rize (il merkezi) | Bağımsız | 656 | 735 | 119 |
| 1973 | Sinop | Sinop (il merkezi) | Bağımsız | 1415 | 1475 | 123 |
| 1973 | Şanlıurfa | Şanlıurfa (il merkezi) | Bağımsız | 3960 | 4859 | 129 |
| 1973 | Van | Van (il merkezi) | Bağımsız | 3749 | 4666 | 131 |
| 1973 | Afyonkarahisar | Bolvadin | AP | 3643 | 3641 | 54 |
| 1973 | Eskişehir | Sivrihisar | AP | 1325 | 1315 | 80 |
| 1973 | Ordu | Fatsa | CHP | 2598 | 2597 | 118 |
| 1973 | Zonguldak | Bartın | CHP | 3418 | 3058 | 132 |
| 1977 | Adana | Adana (il merkezi) | MSP | 2195 | 2185 | 47 |
| 1977 | Bilecik | Bilecik (il merkezi) | AP | 636 | 836 | 60 |
| 1977 | Edirne | Edirne (il merkezi) | Bağımsız | 7 | 592 | 71 |
| 1977 | Şanlıurfa | Şanlıurfa (il merkezi) | Bağımsız | 20 | 302 | 121 |
| 1977 | Bilecik | Pazaryeri | CHP | 826 | 827 | 60 |
| 1977 | Bingöl | Genç | AP | 471 | 469 | 60 |
| 1977 | Bingöl | Genç | CHP | 469 | 471 | 60 |
| 1977 | Kars | Posof | AP | 274 | 327 | 86 |
| 1977 | Kars | Posof | CHP | 327 | 274 | 86 |
| 1977 | Kastamonu | İnebolu | AP | 877 | 1216 | 88 |
| 1977 | Kastamonu | İnebolu | CHP | 1216 | 877 | 88 |
| 1977 | Mardin | Silopi | AP | 1384 | 731 | 104 |
| 1977 | Muğla | Köyceğiz | AP | 1017 | 1043 | 104 |
| 1977 | Muğla | Köyceğiz | CHP | 1043 | 1017 | 104 |
| 1977 | Şanlıurfa | Akçakale | AP | 422 | 458 | 120 |
| 1977 | Şanlıurfa | Akçakale | CHP | 458 | 422 | 120 |
| 1977 | Mersin | Erdemli | AP | 2200 | 1944 | 80 |
| 1977 | Mersin | Erdemli | CHP | 1944 | 2200 | 80 |

## Desteksiz farklar (sayfaya bakılmalı; OCR olabilir)

| Seçim | İl | Belediye | Alan | Depo | Kitap | PDF sayfa |
|---|---|---|---|---:|---:|---:|
| 1963 | Adana | Adana (il merkezi) | gecerli | 53778 | 53237 | 11 |
| 1963 | Ağrı | Ağrı (il merkezi) | gecerli | 4407 | 2993 | 87 |
| 1963 | Bitlis | Bitlis (il merkezi) | gecerli | 3841 | 3942 | 345 |
| 1963 | Bitlis | Bitlis (il merkezi) | Bağımsız | 82 | 155 | 345 |
| 1963 | Bursa | Bursa (il merkezi) | gecerli | 52086 | 53827 | 411 |
| 1963 | Bursa | Bursa (il merkezi) | Bağımsız | 2028 | 3394 | 411 |
| 1963 | Çankırı | Çankırı (il merkezi) | gecerli | 4541 | 4810 | 471 |
| 1963 | Çankırı | Çankırı (il merkezi) | Bağımsız | 186 | 341 | 471 |
| 1963 | Çorum | Çorum (il merkezi) | Bağımsız | 507 | 794 | 495 |
| 1963 | Kastamonu | Kastamonu (il merkezi) | gecerli | 5661 | 5938 | 975 |
| 1963 | Kastamonu | Kastamonu (il merkezi) | Bağımsız | 1410 | 2731 | 975 |
| 1963 | Kırklareli | Kırklareli (il merkezi) | gecerli | 6519 | 3237 | 1045 |
| 1963 | Kocaeli | Kocaeli (il merkezi) | gecerli | 19933 | 20531 | 1077 |
| 1963 | Kocaeli | Kocaeli (il merkezi) | Bağımsız | 166 | 176 | 1077 |
| 1963 | Malatya | Malatya (il merkezi) | gecerli | 21222 | 7368 | 1171 |
| 1963 | Malatya | Malatya (il merkezi) | AP | 2253 | 21196 | 1171 |
| 1963 | Mardin | Mardin (il merkezi) | gecerli | 6500 | 7710 | 1259 |
| 1963 | Mardin | Mardin (il merkezi) | Bağımsız | 1195 | 1468 | 1259 |
| 1963 | Ankara | Şereflikoçhisar | gecerli | 3034 | 3004 | 135 |
| 1963 | Artvin | Yusufeli | Bağımsız | 238 | 142 | 1120 |
| 1963 | Aydın | Bozdoğan | AP | 1426 | 426 | 235 |
| 1963 | Balıkesir | Ayvalık | gecerli | 7131 | 6805 | 265 |
| 1963 | Balıkesir | Ayvalık | Bağımsız | 672 | 224 | 265 |
| 1963 | Bingöl | Solhan | Bağımsız | 189 | 39 | 327 |
| 1963 | Bolu | Gerede | gecerli | 1590 | 1690 | 365 |
| 1963 | Bolu | Gerede | YTP61 | 928 | 925 | 365 |
| 1963 | Edirne | Keşan | Bağımsız | 98 | 11 | 585 |
| 1963 | Kars | Iğdır | gecerli | 4144 | 4351 | 939 |
| 1963 | Konya | Ereğli | gecerli | 9342 | 5995 | 1097 |
| 1963 | Konya | Karapınar | gecerli | 3157 | 1275 | 1099 |
| 1963 | Konya | Karapınar | AP | 1275 | 11 | 1099 |
| 1963 | Konya | Kulu | gecerli | 2623 | 2660 | 1099 |
| 1963 | Konya | Kulu | Bağımsız | 4 | 1 | 1099 |
| 1963 | Kırklareli | Babaeski | AP | 1609 | 5550 | 1045 |
| 1963 | Malatya | Doğanşehir | CHP | 695 | 65 | 1171 |
| 1963 | Manisa | Akhisar | gecerli | 11951 | 12334 | 1195 |
| 1963 | Manisa | Akhisar | Bağımsız | 1208 | 1141 | 1195 |
| 1963 | Manisa | Demirci | gecerli | 3378 | 3319 | 1195 |
| 1963 | Manisa | Gördes | gecerli | 2024 | 2105 | 1195 |
| 1963 | Manisa | Gördes | CHP | 971 | 97 | 1195 |
| 1963 | Manisa | Salihli | AP | 5857 | 557 | 1195 |
| 1963 | Kahramanmaraş | Andırın | gecerli | 1054 | 1065 | 1235 |
| 1963 | Kahramanmaraş | Andırın | Bağımsız | 6 | 1 | 1235 |
| 1963 | Niğde | Aksaray | gecerli | 5662 | 5979 | 1349 |
| 1963 | Ordu | Gölköy | gecerli | 1521 | 1525 | 1371 |
| 1963 | Ordu | Gölköy | Bağımsız | 1182 | 112 | 1371 |
| 1963 | Rize | İkizdere | gecerli | 963 | 997 | 1397 |
| 1963 | Rize | İkizdere | Bağımsız | 628 | 287 | 1397 |
| 1963 | Siirt | Baykan | CHP | 64 | 276 | 391 |
| 1963 | Tokat | Turhal | gecerli | 4871 | 6145 | 1583 |
| 1963 | Tokat | Turhal | AP | 3636 | 363 | 1583 |
| 1963 | Zonguldak | Devrek | gecerli | 2511 | 1771 | 1765 |
| 1963 | Çanakkale | Biga | gecerli | 3393 | 3018 | 443 |
| 1968 | Bitlis | Bitlis (il merkezi) | sandik | 26 | 24 | 298 |
| 1968 | Bitlis | Bitlis (il merkezi) | secmen | 8059 | 6944 | 298 |
| 1968 | Elazığ | Elazığ (il merkezi) | Bağımsız | 10215 | 10242 | 514 |
| 1968 | Sakarya | Sakarya (il merkezi) | gecerli | 17853 | 18318 | 1182 |
| 1968 | Sakarya | Sakarya (il merkezi) | CGP | 928 | 628 | 1182 |
| 1968 | Samsun | Samsun (il merkezi) | sandik | 165 | 163 | 1202 |
| 1968 | Samsun | Samsun (il merkezi) | gecerli | 26357 | 27324 | 1202 |
| 1968 | Trabzon | Trabzon (il merkezi) | gecerli | 15883 | 16349 | 1356 |
| 1968 | Trabzon | Trabzon (il merkezi) | Bağımsız | 2243 | 2238 | 1356 |
| 1968 | Uşak | Uşak (il merkezi) | gecerli | 8453 | 8251 | 1426 |
| 1968 | Adana | Yumurtalık | gecerli | 628 | 636 | 16 |
| 1968 | Adana | Yumurtalık | CHP | 7 | 8 | 16 |
| 1968 | Aydın | Çine | gecerli | 2642 | 2700 | 208 |
| 1968 | Aydın | Çine | Bağımsız | 1371 | 1330 | 208 |
| 1968 | Bitlis | Ahlat | Bağımsız | 1120 | 1068 | 298 |
| 1968 | Bursa | İznik | gecerli | 2979 | 2980 | 354 |
| 1968 | Diyarbakır | Dicle | secmen | 1459 | 1439 | 474 |
| 1968 | Edirne | İpsala | gecerli | 1552 | 1536 | 500 |
| 1968 | Edirne | İpsala | Bağımsız | 88 | 44 | 500 |
| 1968 | Giresun | Bulancak | sandik | 15 | 14 | 636 |
| 1968 | Giresun | Bulancak | gecerli | 3220 | 3349 | 636 |
| 1968 | Hatay | İskenderun | gecerli | 14820 | 14882 | 689 |
| 1968 | Hatay | Reyhanlı | gecerli | 6449 | 4626 | 688 |
| 1968 | Isparta | Senirkent | gecerli | 3484 | 2661 | 706 |
| 1968 | Isparta | Senirkent | Bağımsız | 1798 | 268 | 706 |
| 1968 | Isparta | Şarkikaraağaç | gecerli | 1581 | 1617 | 706 |
| 1968 | Isparta | Şarkikaraağaç | CHP | 615 | 196 | 706 |
| 1968 | Isparta | Yalvaç | gecerli | 3524 | 3628 | 706 |
| 1968 | Isparta | Yalvaç | Bağımsız | 1552 | 60 | 706 |
| 1968 | Kocaeli | Karamürsel | CHP | 436 | 434 | 904 |
| 1968 | Kocaeli | Karamürsel | Bağımsız | 455 | 337 | 904 |
| 1968 | Konya | Çumra | gecerli | 3462 | 3710 | 918 |
| 1968 | Konya | Çumra | AP | 1562 | 1532 | 918 |
| 1968 | Kütahya | Simav | sandik | 16 | 14 | 958 |
| 1968 | Kütahya | Simav | gecerli | 2767 | 2901 | 958 |
| 1968 | Sakarya | Akyazı | gecerli | 2808 | 3164 | 1182 |
| 1968 | Tekirdağ | Şarköy | secmen | 3278 | 2266 | 1316 |
| 1968 | Tokat | Reşadiye | sandik | 5 | 3 | 1330 |
| 1968 | Trabzon | Maçka | sandik | 2 | 4 | 1356 |
| 1968 | Trabzon | Maçka | gecerli | 746 | 760 | 1356 |
| 1968 | Trabzon | Of | gecerli | 1193 | 1160 | 1357 |
| 1968 | Trabzon | Tonya | sandik | 11 | 619 | 1356 |
| 1968 | Trabzon | Tonya | secmen | 3704 | 187 | 1356 |
| 1968 | Zonguldak | Devrek | CHP | 1102 | 557 | 1484 |
| 1968 | Zonguldak | Devrek | Bağımsız | 70 | 1102 | 1484 |
| 1968 | Çanakkale | Eceabat | gecerli | 1123 | 1130 | 382 |
| 1968 | Çanakkale | Eceabat | Bağımsız | 652 | 632 | 382 |
| 1968 | Çanakkale | İmroz (Gökçeada) | gecerli | 1389 | 985 | 382 |
| 1968 | Çanakkale | İmroz (Gökçeada) | Bağımsız | 669 | 223 | 382 |
| 1973 | Adana | Adana (il merkezi) | gecerli | 72125 | 72122 | 52 |
| 1973 | Amasya | Amasya (il merkezi) | sandik | 212 | 54 | 56 |
| 1973 | Amasya | Amasya (il merkezi) | secmen | 59765 | 16728 | 56 |
| 1973 | Bolu | Bolu (il merkezi) | sandik | 30 | 47 | 66 |
| 1973 | Bolu | Bolu (il merkezi) | secmen | 9840 | 13314 | 66 |
| 1973 | Niğde | Niğde (il merkezi) | gecerli | 7310 | 7010 | 116 |
| 1973 | Niğde | Niğde (il merkezi) | Bağımsız | 405 | 394 | 117 |
| 1973 | Trabzon | Trabzon (il merkezi) | gecerli | 16579 | 16129 | 126 |
| 1973 | Trabzon | Trabzon (il merkezi) | Bağımsız | 510 | 712 | 127 |
| 1973 | Afyonkarahisar | Bolvadin | gecerli | 4615 | 4613 | 54 |
| 1973 | Eskişehir | Sivrihisar | gecerli | 2417 | 2407 | 80 |
| 1973 | Gümüşhane | Kelkit | sandik | 6 | 8 | 84 |
| 1973 | Kars | Posof | secmen | 3387 | 854 | 94 |
| 1973 | Kocaeli | Gölcük | sandik | 62 | 44 | 100 |
| 1973 | Kocaeli | Gölcük | secmen | 18614 | 12610 | 100 |
| 1973 | Ordu | Fatsa | gecerli | 4436 | 4435 | 118 |
| 1973 | Sinop | Durağan | gecerli | 952 | 958 | 122 |
| 1973 | Sinop | Durağan | AP | 327 | 326 | 122 |
| 1973 | Sivas | Gürün | secmen | 4246 | 3622 | 124 |
| 1973 | Van | Gürpınar | gecerli | 730 | 734 | 130 |
| 1973 | Van | Gürpınar | AP | 367 | 369 | 130 |
| 1973 | Zonguldak | Bartın | gecerli | 5818 | 5458 | 132 |
| 1977 | Sivas | Sivas (il merkezi) | secmen | 67190 | 7190 | 114 |
| 1977 | Aydın | Nazilli | Bağımsız | 503 | 129 | 57 |
| 1977 | Bilecik | Pazaryeri | gecerli | 1982 | 1983 | 60 |
| 1977 | Hatay | İskenderun | Bağımsız | 68 | 5328 | 79 |
| 1977 | Kayseri | Sarıoğlan | secmen | 1640 | 1670 | 90 |
| 1977 | Manisa | Alaşehir | secmen | 3196 | 13296 | 100 |
| 1977 | Siirt | Şırnak | CHP | 1022 | 102476 | 114 |
| 1977 | Tokat | Niksar | secmen | 10011 | 10 | 118 |
| 1977 | Tokat | Niksar | AP | 222 | 22239 | 118 |
| 1977 | Tunceli | Mazgirt | sandik | 9 | 3 | 120 |
| 1977 | Yozgat | Çekerek | MSP | 74 | 171355 | 123 |
| 1977 | Zonguldak | Karabük | gecerli | 21923 | 21907 | 124 |
| 1977 | Zonguldak | Karabük | Bağımsız | 32 | 21 | 125 |

Ayrıca 25 alanda kitap okunuşu tek rakam (taramadaki boş/kirli hücre); listelenmedi, ayrıntısı JSON'da.

## Oyları geniş ölçüde farklı satırlar

Belediye kitapta sandık ve seçmen sayısıyla bulundu; kitap satırındaki sayılar (sütun sırasıyla; tireler okunmadığı için parti sütunu ayrıca kontrol edilmeli):

| Seçim | İl | Belediye | Depo (geçerli; partiler) | Kitap satırı (sayılar) | PDF sayfa |
|---|---|---|---|---|---:|
| 1968 | Muğla | Muğla (il merkezi) | 4683; AP 2271, Bağımsız 56, CGP 335, CHP 2021 | 00 29 8981 5186 4704 577 2271 2021 | 1084 |
| 1968 | Adana | Tufanbeyli | 1205; AP 596, CHP 609 | 08 5 1442 1310 1211 908 609 596 | 16 |
| 1968 | Antalya | Kumluca | 1329; AP 699, Bağımsız 253, CGP 41, CHP 336 | 7 1999 1507 1 341 753 699 336 41 | 166 |
| 1968 | Balıkesir | Ayvalık | 4120; AP 2011, Bağımsız 845, CHP 1264 | 31 9422 4865 4359 516 2011 1264 239 845 | 230 |
| 1968 | Bilecik | Gölpazarı | 1630; AP 821, Bağımsız 11, CHP 798 | 02 8 2153 1824 1482 847 739 743 | 269 |
| 1968 | Bilecik | Osmaneli | 1307; AP 419, Bağımsız 131, CGP 41, CHP 716 | 6 1876 1471 1057 773 407 624 | 269 |
| 1968 | Bolu | Seben | 1034; AP 563, CHP 471 | 5 1183 1071 1006 905 551 455 | 313 |
| 1968 | Bolu | Yığılca | 475; Bağımsız 255, CHP 220 | 09 3 669 527 490 787 193 153 111 19 | 313 |
| 1968 | Edirne | Keşan | 5051; AP 2229, Bağımsız 803, CGP 85, CHP 1849, TİP 85 | 04 26 8630 4526 3886 524 1963 1711 141 71 | 501 |
| 1968 | Edirne | Lalapaşa | 319; AP 196, CHP 123 | 000 2 456 328 296 | 26 |
| 1968 | Edirne | Meriç | 807; AP 302, Bağımsız 20, CHP 485 | 4 1145 894 731 780 288 443 | 501 |
| 1968 | Erzincan | Çayırlı | 622; AP 118, Bağımsız 504 | 3 1061 796 698 750 45 192 | 536 |
| 1968 | Gaziantep | Yavuzeli | 433; AP 243, CGP 190 | 2 555 470 457 846 234 187 | 615 |
| 1968 | Isparta | Atabey | 1301; AP 436, Bağımsız 76, CHP 789 | 8 1894 547 | 706 |
| 1968 | Isparta | Eğirdir | 2621; AP 1119, CHP 1502 | 02 16 3522 2814 | 706 |
| 1968 | Isparta | Sütçüler | 656; AP 460, Bağımsız 196 | 06 5 1056 739 | 706 |
| 1968 | Kocaeli | Gebze | 2890; AP 961, Bağımsız 1658, CHP 198, TİP 73 | 01 15 4833 3146 2889 650 1053 599 | 905 |
| 1968 | Konya | Cihanbeyli | 1438; AP 597, CHP 841 | 04 12 2803 2204 1972 786 597 841 534 | 918 |
| 1968 | Konya | Ereğli | 11194; AP 5393, Bağımsız 4233, CHP 1568 | 07 54 17410 12567 11278 721 5193 | 919 |
| 1968 | Kırklareli | Vize | 1701; AP 888, Bağımsız 149, CGP 16, CHP 635, TİP 13 | 9 3000 1951 1771 650 873 543 17 1 | 881 |
| 1968 | Manisa | Saruhanlı | 2073; AP 910, CHP 1163 | 09 10 3339 2297 2250 687 828 | 1005 |
| 1968 | Kahramanmaraş | Göksun | 1502; AP 814, CHP 688 | 04 7 2188 1669 1405 762 692 99 614 | 1037 |
| 1968 | Kahramanmaraş | Pazarcık | 2285; AP 1048, Bağımsız 1237 | 05 11 3305 2470 2341 747 950 301 821 | 1037 |
| 1968 | Niğde | Aksaray | 8221; AP 3639, CHP 4301, TİP 52, YTP61 229 | 49 12043 8895 8214 738 3228 3780 105 109 46 | 1131 |
| 1968 | Niğde | Ortaköy | 1154; AP 508, CHP 646 | 5 1305 1180 1143 904 507 631 | 1131 |
| 1968 | Sivas | Şarkışla | 2393; AP 1126, CHP 1267 | 09 13 3407 2655 2559 779 1126 1267 75 | 1272 |
| 1968 | Tekirdağ | Çerkezköy | 1630; AP 768, Bağımsız 47, CHP 815 | 01 10 2330 1658 1527 711 784 | 1317 |
| 1968 | Tekirdağ | Çorlu | 6999; AP 2747, Bağımsız 1505, CHP 2747 | 02 32 10364 7778 5441 750 2771 2670 | 1317 |
| 1968 | Van | Gürpınar | 652; AP 357, Bağımsız 295 | 5 741 275 274 | 1451 |
| 1968 | İstanbul | Şile | 945; AP 485, Bağımsız 351, CHP 31, TİP 78 | 09 6 1488 1017 985 683 720 223 | 382 |
| 1968 | İstanbul | Yalova | 4387; AP 1638, Bağımsız 120, CHP 2081, CKMP 497, TİP 51 | 19 24 6761 | 740 |
| 1968 | İzmir | Bornova | 6697; AP 2987, CGP 661, CHP 2793, MP62 50, TİP 206 | 36 13170 7510 6838 570 2987 2793 742 82 234 | 757 |
| 1968 | Mersin | Silifke | 3369; AP 1185, CGP 254, CHP 1888, TİP 42 | 05 15 5435 4018 3624 739 1185 | 718 |
| 1968 | Muğla | Merkez | 4683; AP 2271, Bağımsız 56, CGP 335, CHP 2021 | 00 29 8981 5186 4704 577 2271 2021 | 1084 |
| 1973 | Tokat | Artova | 1003; AP 366, Bağımsız 300, CHP 337 | 4 1233 1058 1003 | 126 |
| 1973 | Tokat | Reşadiye | 1182; AP 690, Bağımsız 119, CHP 373 | 9 1586 1262 1182 796 690 | 126 |
| 1973 | Trabzon | Sürmene | 1878; Bağımsız 529, CHP 1349 | 12 3119 2053 1914 658 36 19 1349705 | 128 |
| 1977 | Elazığ | Elazığ (il merkezi) | 31728; AP 5399, Bağımsız 4719, CHP 4726, MHP 13410, MSP 3474 | 224 78569 36082 459 22732 5399237 4696207 | 70 |
| 1977 | İzmir | İzmir (il merkezi) | 189145; AP 79187, Bağımsız 119, CHP 104209, MHP 1328, MSP 2961, TSİP 442, TİP 899 | 1118 371920 196276 528 189145 79187419 140209551 | 84 |
| 1977 | Burdur | Bucak | 5328; AP 1900, CHP 1274, DEMP73 60, MHP 1972, MSP 122 | 32 9862 4981 505 4502 1554345 433 96 | 86 |
| 1977 | Burdur | Yeşilova | 1409; AP 228, Bağımsız 431, CHP 722, MSP 28 | 8 1943 1631 839 1459 228156 772529 | 62 |
| 1977 | Denizli | Kale | 1456; AP 438, Bağımsız 481, MHP 537 | 6 1963 1561 795 1456 438301 537369 | 68 |
| 1977 | Erzincan | Tercan | 945; AP 421, Bağımsız 110, MHP 399, MSP 15 | 17 5215 3344 641 2714 1384510 1330490 | 50 |
| 1977 | Gaziantep | İslahiye | 5807; AP 1150, Bağımsız 154, CHP 2544, MHP 1837, MSP 122 | 29 9656 6242 646 5730 1150201 2544444 12221 | 74 |
| 1977 | Kırklareli | Vize | 2769; AP 1122, CHP 1429, MHP 218 | 12 3791 2924 771 2796 1151412 1424509 221 79 | 90 |
| 1977 | Siirt | Sason | 981; AP 483, CHP 498 | 8 1980 1689 853 1618 781483 837517 | 62 |
| 1977 | Trabzon | Araklı | 2179; AP 913, CHP 1211, MSP 55 | 13 3739 2280 610 2179 913419 211556 | 118 |
| 1977 | Zonguldak | Ereğli | 11603; AP 2523, CHP 8261, MHP 143, MSP 464, TSİP 43, TİP 169 | 78 28089 12104 431 1163 2523217 861712 | 124 |
| 1977 | Çorum | Ortaköy | 913; AP 403, Bağımsız 390, CHP 120 | 4 1229 950 772 772 326422 173224 | 58 |
| 1977 | Çorum | Sungurlu | 6111; AP 2207, Bağımsız 220, CHP 3250, MSP 345, SDP 89 | 38 9945 6644 668 6120 2207361 3259532 | 66 |
| 1977 | Elazığ | Merkez | 31728; AP 5399, Bağımsız 4719, CHP 4726, MHP 13410, MSP 3474 | 224 78569 36082 459 22732 5399237 4696207 | 70 |
| 1977 | İzmir | İzmir (il merkezi belediyesi) | 189145; AP 79187, Bağımsız 119, CHP 104209, MHP 1328, MSP 2961, TSİP 442, TİP 899 | 1118 371920 196276 528 189145 79187419 140209551 | 84 |

## Yöntem ve sınırlar

- Kitap metni `pdftotext -layout` ile okunur; satırın rakamları kitabın sütun sırasıyla aranır (tahmin ya da hesap yok). Eşleşmeyen satırda bir-iki alan joker yapılıp kitaptaki okunuş raporlanır.
- Oyu olmayan parti kitapta tiredir; tireler taramada her zaman okunmadığı için aynı sıradaki iki parti sütunu birbirinden ayırt edilemez (değer ve sıra doğrulanır, sütun etiketi değil).
- 1963 kitabında ad/sandık/seçmen ve sonuçlar karşılıklı sayfalarda; iki parça ayrı aranır.
- 1973 kitabının sağ yüzünde DP oy sütunu taramada kesik; yalnız yüzdesi okunuyor, oy o yüzdeyle tutuyorsa kabul edilir.
- Gözle doğrulanan örnekler (sayfa görüntüsü): 1968 Adana merkez geçerli 54 522, partiler toplamı 52 619 (kitap içi); 1963 Adıyaman muteber oy 4 563, partiler 4 337 (kitap içi); 1977 Bilecik Merkez AP 836 (%27,1; depoda 636); 1973 Afyonkarahisar Merkez bağımsız 6 434 (%65,6; depoda 5 302).
