"""
Ilce kurulus kanunlarinin ek listeleri -> kaynak katmani (Faz 2: soy).

Her kanun icin iki birincil kaynak:
  - mevzuat.gov.tr metni (data/raw/mevzuat/<kanun>.pdf): Madde 1'in bentleri;
    "(N) sayili liste" -> hangi ilde hangi ilce kuruldu. Metin temiz.
  - Resmi Gazete asil sayisi (data/raw/resmi_gazete/<sayi>.pdf): ek listeler;
    her satir: birim (koy/kasaba/mahalle), eski ilcesi, eski bucagi. Taranmis,
    OCR'li (gurultulu: 'Akyurl', 'LlSTE', kalin basliklarda cift harf).

Cikti: data/kaynaklar/resmi_gazete/ilce_kurulus/<kanun>.json
  her yeni ilce: il, ad, liste no, satirlar [{birim, tur, eskiIlce, eskiBucak,
  eskiIlceGeomId}], eskiIlceler ozeti, tekKaynak (butun birimler tek ilceden mi).

Eski ilce adi OCR'dan okunur ve o ilin kanundan SONRAKI ilk genel secimindeki
ilce adlariyla (yeni kurulanlar haric) bulanik eslenir; eslenemeyen satir
`eskiIlce: null` ve `okunan` ile kalir (tahmin yok).

Kullanim:
  .venv/bin/python scripts/pipelines/historical_geo/extract_ilce_kurulus_kanunu.py 3644
"""
import collections
import difflib
import json
import pathlib
import re
import sys

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common.election_io import load_election  # noqa: E402
from common.turkish_text import fold  # noqa: E402

KANUNLAR = {
    "3644": {"ad": "130 İlçe Kurulması Hakkında Kanun", "kabul": "1990-05-09",
             "resmiGazete": {"tarih": "1990-05-20", "sayi": 20523}, "rgPdf": "data/raw/resmi_gazete/20523.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3644.pdf", "sonrakiGenel": "1991", "oncekiGenel": "1987",
             "adsizIl": {"Çamoluk": [28, 29], "Doğankent": [28, 29]}},
    "3392": {"ad": "103 İlçe Kurulması Hakkında Kanun", "kabul": "1987-06-19",
             "resmiGazete": {"tarih": "1987-07-04", "sayi": 19507}, "rgPdf": "data/raw/resmi_gazete/19507.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3392.pdf", "sonrakiGenel": "1991", "oncekiGenel": "1987",
             "adsizIl": {},
             # kanundaki ad -> sonraki secimdeki ad; Icisleri 2018 listesi bu ilceleri 3392 ile
             # guncel adlariyla veriyor (DEMRE, CUMAYERİ)
             "sonrakiAd": {"Kale": "Demre", "Cumaova": "Cumayeri"}},
    "2963": {"ad": "Altı İlçe Kurulması ve Ankara İli Merkez İlçesinin Kaldırılması Hakkında Kanun",
             "kabul": "1983-11-29", "resmiGazete": {"tarih": "1983-11-30", "sayi": 18237, "mukerrer": 2},
             "rgPdf": "data/raw/resmi_gazete/18237_2.pdf", "rgUrl": "https://www.resmigazete.gov.tr/arsiv/18237_2.pdf",
             "mevzuatPdf": None, "sonrakiGenel": "1987", "oncekiGenel": "1983", "adsizIl": {},
             "sayfaSayisi": 9,   # PDF 9 sayfalik ekin uc kopyasi; ilk kopya
             # mevzuat.gov.tr'de PDF metni yok; Madde 1 (a)-(f) bentleri RG 18237 (2. mukerrer)
             # s. 2'den aynen aktarildi
             "bentlerElle": {
                 1: {"il": "Ankara", "ad": "Mamak", "madde": "a) Ekli 1 sayılı listede adları yazılı köyleri kapsamak ve merkezi Mamak olmak üzere Ankara İli Çankaya İlçesinden ayrılarak Mamak adıyla", "ekHukum": None},
                 2: {"il": "Ankara", "ad": "Gölbaşı", "madde": "b) Ekli 2 sayılı listede adları yazılı köyleri kapsamak ve merkezi Gölbaşı olmak üzere Ankara İli Çankaya İlçesi Gölbaşı Bucağında Gölbaşı adıyla", "ekHukum": None},
                 3: {"il": "Ankara", "ad": "Keçiören", "madde": "c) Ekli 3 sayılı listede adları yazılı köyleri kapsamak ve merkezi Keçiören olmak üzere Ankara İli Altındağ İlçesinden ayrılarak Keçiören adıyla", "ekHukum": None},
                 4: {"il": "Ankara", "ad": "Sincan", "madde": "d) Ekli 4 sayılı listede yazılı köyleri kapsamak ve merkezi Sincan olmak üzere Ankara İli Yenimahalle İlçesi Sincan Bucağında Sincan adıyla", "ekHukum": None},
                 5: {"il": "Adana", "ad": "Düziçi", "madde": "e) Ekli 5 sayılı listede adları yazılı köyleri kapsamak ve merkezi Haruniye olmak üzere Adana İli Bahçe İlçesi Haruniye Bucağında Düziçi adıyla", "ekHukum": None},
                 6: {"il": "Muğla", "ad": "Dalaman", "madde": "f) Ekli 6 sayılı listede adları yazılı köyleri kapsamak ve merkezi Dalaman olmak üzere Muğla İli Köyceğiz İlçesinden ayrılarak Dalaman adıyla", "ekHukum": None},
             },
             "digerHukumler": [
                 {"madde": 2, "metin": "Ankara ili Merkez İlçesi kaldırılmış ve bu ilçe sınırları içinde kalan alan "
                                       "Ankara İli Altındağ İlçesine bağlanmıştır.",
                  "eventType": "abolished", "effectiveDate": "1983-11-30", "unit": "Merkez (Ankara)",
                  "provinceBefore": 6, "provinceAfter": 6, "mergedInto": "Altındağ",
                  "not": "1961-1983 seçim verisindeki Ankara 'Merkez' satırı bu ilçedir (geomId yok). Sınırı kaynakta "
                         "yok; alanı Altındağ'a katıldı, aynı kanunla Altındağ'dan Keçiören ayrıldı."}]},
    "3578": {"ad": "4 İl ve 5 İlçe Kurulması Hakkında Kanun", "kabul": "1989-06-15",
             "resmiGazete": {"tarih": "1989-06-21", "sayi": 20202}, "rgPdf": "data/raw/resmi_gazete/20202.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3578.pdf", "sonrakiGenel": "1991", "oncekiGenel": "1987",
             # 2. bent il adi vermiyor ("Pazaryolu adıyla")
             "adsizIl": {"Pazaryolu": [25, 29]},
             "digerHukumler": [
                 {"madde": 2, "metin": "Ankara İline bağlı Kırıkkale, Niğde İline bağlı Aksaray, Gümüşhane İline bağlı "
                                       "Bayburt ve Konya İline bağlı Karaman ilçe merkezleri merkez olmak üzere dört il "
                                       "kurulmuştur (ekli (6)-(9) sayılı listeler).",
                  "eventType": "provinces_created", "effectiveDate": "1989-06-21",
                  "unit": "Kırıkkale, Aksaray, Bayburt, Karaman"}]},
    "3647": {"ad": "İki İl İle Beş İlçe Kurulması ve 190 Sayılı Kanun Hükmünde Kararnamenin Eki Cetvellerde "
                   "Değişiklik Yapılması Hakkında Kanun", "kabul": "1990-05-16",
             "resmiGazete": {"tarih": "1990-05-18", "sayi": 20522, "mukerrer": 1},
             "rgPdf": "data/raw/resmi_gazete/20522_1.pdf", "rgUrl": "https://www.resmigazete.gov.tr/arsiv/20522_1.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3647.pdf", "sonrakiGenel": "1991", "oncekiGenel": "1987", "adsizIl": {},
             "digerHukumler": [
                 {"madde": 2, "metin": "Siirt İline bağlı Batman ve Şırnak ilçe merkezleri merkez olmak üzere Batman ve "
                                       "Şırnak illeri kurulmuştur (ekli (6)-(7) sayılı listeler).",
                  "eventType": "provinces_created", "effectiveDate": "1990-05-18", "unit": "Batman, Şırnak"},
                 {"madde": 2, "metin": "Hakkâri İli Çukurca İlçesi Çığlı Bucağına bağlı Andaç ve Ortaköy köyleri "
                                       "Uludere İlçesi Ortabağ Bucağına bağlanmak (Şırnak ilinin kuruluş bendi).",
                  "eventType": "boundary_adjustment", "effectiveDate": "1990-05-18", "unit": "Çukurca → Uludere"}]},
    "4200": {"ad": "Üç İlçe ve Bir İl Kurulması ile 190 Sayılı Kanun Hükmünde Kararnamenin Eki Cetvellerde "
                   "Değişiklik Yapılması Hakkında Kanun", "kabul": "1996-10-24",
             "resmiGazete": {"tarih": "1996-10-28", "sayi": 22801}, "rgPdf": "data/raw/resmi_gazete/22801.pdf",
             "mevzuatPdf": "data/raw/mevzuat/4200.pdf", "sonrakiGenel": "1999", "oncekiGenel": "1995", "adsizIl": {},
             "digerHukumler": [
                 {"madde": 2, "metin": "Ekli (4) sayılı listede adları yazılı ilçe, bucak, kasaba ve köyler bağlanmak ve "
                                       "Adana iline bağlı Osmaniye İlçe Merkezi merkez olmak suretiyle Osmaniye adıyla "
                                       "bir il kurulmuştur.",
                  "eventType": "provinces_created", "effectiveDate": "1996-10-28", "unit": "Osmaniye"}]},
    "2585": {"ad": "Urfa İli Viranşehir İlçesinin Ceylanpınar Bucağında Ceylanpınar Adıyla, İzmir İli Menemen İlçesi "
                   "Aliağa Bucağında Aliağa Adıyla Yeniden İki İlçe Kurulması Hakkında Kanun", "kabul": "1982-01-14",
             "resmiGazete": {"tarih": "1982-01-21", "sayi": 17581}, "rgPdf": "data/raw/resmi_gazete/17581.pdf",
             "mevzuatPdf": None, "sonrakiGenel": "1983", "oncekiGenel": "1977", "adsizIl": {},
             "bicim": "cetvel", "sayfaSayisi": 4,
             # Madde 1, RG 17581 s. 4'ten aynen
             "bentlerElle": {
                 1: {"il": "Urfa", "ad": "Ceylanpınar", "madde": "Ekli (1) sayılı cetvelde adları yazılı köyleri kapsamak üzere Urfa İli Viranşehir İlçesi Ceylanpınar Bucağında Ceylanpınar adıyla", "ekHukum": None},
                 2: {"il": "İzmir", "ad": "Aliağa", "madde": "ekli (2) sayılı cetvelde adları yazılı köyleri kapsamak Üzere İzmir İli Menemen İlçesi Aliağa Bucağında Aliağa adıyla", "ekHukum": None}}},
    "3949": {"ad": "3 İlçe Kurulması Hakkında Kanun", "kabul": "1993-12-27",
             "resmiGazete": {"tarih": "1993-12-29", "sayi": 21803}, "rgPdf": "data/raw/resmi_gazete/21803.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3949.pdf", "sonrakiGenel": "1995", "oncekiGenel": "1991", "adsizIl": {},
             # kaynak ilce adi listede kanun ANINDAKI ad; ayni kanunun 2. maddesi bunlari
             # yeniden adlandiriyor (Narlibahce 1992'de kuruldu, 1991 secim listesinde yok)
             "kaynakAdEsleme": {"Narlıbahçe": "Narlıdere", "Cumaova": "Cumayeri"},
             # listeler ilce basina degil tur basina: Guzelbahce (1) mahalle + (2) koy,
             # Esenler (3) mahalle, Gumusova (4) koy -> ayni ilcenin listeleri birlestirilir
             "bentlerElle": {
                 1: {"il": "İzmir", "ad": "Güzelbahçe", "madde": "Ekli (1) sayılı listede adları yazılı mahalleler merkez olmak, ekli (2) sayılı listede adları yazılı köyler bağlanmak ve aynı adla bir belediye kurulmak üzere İzmir ilinde Güzelbahçe adıyla", "ekHukum": None},
                 2: {"il": "İzmir", "ad": "Güzelbahçe", "madde": "(bkz. liste 1)", "ekHukum": None},
                 3: {"il": "İstanbul", "ad": "Esenler", "madde": "Ekli (3) sayılı listede adları yazılı mahalleler merkez olmak ve aynı adla bir belediye kurulmak üzere İstanbul İlinde Esenler adıyla", "ekHukum": None},
                 4: {"il": "Bolu", "ad": "Gümüşova", "madde": "Ekli (4) sayılı listede adları yazılı köyler bağlanmak ve aynı adla bir belediye kurulmak üzere Bolu ilinde Gümüşova adıyla", "ekHukum": None}},
             "digerHukumler": [
                 {"madde": 2, "metin": "İzmir İli Narlıbahçe ilçesinin ve belediyesinin adı Narlıdere olarak değiştirilmiştir.",
                  "eventType": "renamed", "effectiveDate": "1993-12-29", "unit": "Narlıbahçe → Narlıdere"},
                 {"madde": 2, "metin": "Bolu İli Cumaova ilçesinin ve belediyesinin adı Cumayeri olarak değiştirilmiştir.",
                  "eventType": "renamed", "effectiveDate": "1993-12-29", "unit": "Cumaova → Cumayeri"}]},
    "1055": {"ad": "Abana ve Bozkurt adları ile iki ilçe kurulması hakkında Kanun", "kabul": "1968-07-03",
             "resmiGazete": {"tarih": "1968-07-17", "sayi": 12952}, "rgPdf": "data/raw/resmi_gazete/12952.pdf",
             "mevzuatPdf": None, "sonrakiGenel": "1969", "oncekiGenel": "1965", "adsizIl": {},
             # Cetvel (1) yalniz koy adlarini veriyor; koylerin eski ilcesi yazilmamis
             "kaynakSutunuYok": True,
             "bentlerElle": {
                 1: {"il": "Kastamonu", "ad": "Abana", "madde": "Kastamonu ilinin Abana ve Pazaryeri kasabaları merkez olmak ve ilişik 1 sayılı cetvelde gösterilen köyleri kapsamak üzere, Abana ve Bozkurt adları altında iki ilçe kurulmuştur.", "ekHukum": None},
                 2: {"il": "Kastamonu", "ad": "Bozkurt", "madde": "(bkz. Abana; merkezi Pazaryeri kasabası)", "ekHukum": None}},
             "digerHukumler": [
                 {"madde": 1, "metin": "Bozkurt ilçesi Pazaryeri kasabası merkez olmak üzere 17.07.1968'de kuruldu. 1961 ve "
                                       "1965 seçim verisindeki Kastamonu 'Bozkurt' satırları bu ilçe olamaz (veri adı ya "
                                       "da eşlemesi doğrulanmalı).",
                  "eventType": "data_conflict_note", "effectiveDate": "1968-07-17", "unit": "Bozkurt (Kastamonu)"}]},
    "KHK 584": {"ad": "Bir İl ve İki İlçe Kurulması ile 190 Sayılı Kanun Hükmünde Kararnamenin Eki Cetvellerde "
                        "Değişiklik Yapılması Hakkında Kanun Hükmünde Kararname",
                "kabul": "1999-12-03", "resmiGazete": {"tarih": "1999-12-09", "sayi": 23901},
                "rgPdf": "data/raw/resmi_gazete/23901.pdf", "mevzuatPdf": None,
                "sonrakiGenel": "2002", "oncekiGenel": "1999", "adsizIl": {},
                # KHK'nin ilk sayfasi bu PDF'te yok; bentler ek listelerin basliklarindan
                # (il, ilce) ve Icisleri kaydindan (KHK 584: Kaynasli, Derince, Duzce ili)
                "bentlerElle": {
                    1: {"il": "Bolu", "ad": "Kaynaşlı", "madde": "(1) sayılı liste: Bolu İli Kaynaşlı İlçesine bağlanan köyler", "ekHukum": None},
                    2: {"il": "Kocaeli", "ad": "Derince", "madde": "(2) sayılı liste: Kocaeli İli Derince İlçesine bağlanan köyler", "ekHukum": None}},
                "digerHukumler": [
                    {"madde": 2, "metin": "Düzce ili kurulmuştur (merkez ilçe ile bu ile bağlanan ilçeler; ekli (3) sayılı liste).",
                     "eventType": "provinces_created", "effectiveDate": "1999-12-09", "unit": "Düzce"}]},
    "3806": {"ad": "Onüç İlçe ve İki İl Kurulması ile 190 sayılı Kanun Hükmünde Kararnamenin Eki Cetvellerde "
                   "Değişiklik Yapılması Hakkında Kanun", "kabul": "1992-05-27",
             "resmiGazete": {"tarih": "1992-06-03", "sayi": 21247, "mukerrer": 1},
             "rgPdf": "data/raw/resmi_gazete/21247_1.pdf", "rgUrl": "https://www.resmigazete.gov.tr/arsiv/21247_1.pdf",
             "mevzuatPdf": "data/raw/mevzuat/3806.pdf", "sonrakiGenel": "1995", "oncekiGenel": "1991", "adsizIl": {},
             "sonrakiAd": {"Narlıbahçe": "Narlıdere"},
             # bent numarasi liste numarasina esit degil (6. bent Sultanbeyli'nin listesi yok);
             # liste -> ilce eslemesi mevzuat metninden
             "bentlerElle": {
                 1: {"il": "İstanbul", "ad": "Avcılar", "madde": "3806 Madde 1: ekli (1) sayılı liste — İstanbul İlinde Avcılar", "ekHukum": None},
                 2: {"il": "İstanbul", "ad": "Bağcılar", "madde": "3806 Madde 1: ekli (2) sayılı liste — İstanbul İlinde Bağcılar", "ekHukum": None},
                 3: {"il": "İstanbul", "ad": "Güngören", "madde": "3806 Madde 1: ekli (3) sayılı liste — İstanbul İlinde Güngören", "ekHukum": None},
                 4: {"il": "İstanbul", "ad": "Bahçelievler", "madde": "3806 Madde 1: ekli (4) sayılı liste — İstanbul İlinde Bahçelievler", "ekHukum": None},
                 5: {"il": "İstanbul", "ad": "Maltepe", "madde": "3806 Madde 1: ekli (5) sayılı liste — İstanbul İlinde Maltepe", "ekHukum": None},
                 6: {"il": "İstanbul", "ad": "Tuzla", "madde": "3806 Madde 1: ekli (6) sayılı liste — İstanbul İlinde Tuzla", "ekHukum": None},
                 7: {"il": "İzmir", "ad": "Çiğli", "madde": "3806 Madde 1: ekli (7) sayılı liste — İzmir İlinde Çiğli", "ekHukum": None},
                 8: {"il": "İzmir", "ad": "Gaziemir", "madde": "3806 Madde 1: ekli (8) sayılı liste — İzmir İlinde Gaziemir", "ekHukum": None},
                 9: {"il": "İzmir", "ad": "Balçova", "madde": "3806 Madde 1: ekli (9) sayılı liste — İzmir İlinde Balçova", "ekHukum": None},
                 10: {"il": "İzmir", "ad": "Narlıbahçe", "madde": "3806 Madde 1: ekli (10) sayılı liste — İzmir İlinde Narlıbahçe", "ekHukum": None},
                 11: {"il": "Kars", "ad": "Damal", "madde": "3806 Madde 1: ekli (11) sayılı liste — Kars İlinde Damal", "ekHukum": None},
                 12: {"il": "Kars", "ad": "Karakoyunlu", "madde": "3806 Madde 1: ekli (12) sayılı liste — Kars İlinde Karakoyunlu", "ekHukum": None},
             },
             "digerHukumler": [
                 {"madde": 1, "metin": "6. Merkezi Sultanbeyli Kasabası olmak üzere İstanbul İlinde Sultanbeyli (ek listesi yok; "
                                       "hangi birimlerin bağlandığı bu kanunda yazılmamış).",
                  "eventType": "created_without_list", "effectiveDate": "1992-06-03", "unit": "Sultanbeyli"},
                 {"madde": 2, "metin": "Kars İline bağlı Ardahan ve Iğdır ilçe merkezleri merkez olmak üzere Ardahan ve Iğdır "
                                       "illeri kurulmuştur (ekli (13)-(14) sayılı listeler).",
                  "eventType": "provinces_created", "effectiveDate": "1992-06-03", "unit": "Ardahan, Iğdır"}]},
    "KHK 550": {"ad": "Sekiz İlçe ve Üç İl Kurulması ve 190 Sayılı Kanun Hükmünde Kararnamenin Eki Cetvellerde "
                        "Değişiklik Yapılması Hakkında Kanun Hükmünde Kararname",
                "kabul": "1995-06-03", "resmiGazete": {"tarih": "1995-06-06", "sayi": 22305},
                "rgPdf": "data/raw/resmi_gazete/22305.pdf", "mevzuatPdf": None,
                "sonrakiGenel": "1995", "oncekiGenel": "1991", "adsizIl": {},
                # Madde 1 bentleri 'adıyla' ile bitmiyor; RG 22305 s. 1'den aynen aktarildi.
                # (9)-(11) sayili listeler yeni illerin (Karabuk, Kilis, Yalova) dokumu: il
                # degisiklikleri secim verisinden tarihleriyle zaten cikiyor, okunmaz.
                "bentlerElle": {
                 1: {"il": "Gaziantep", "ad": "Musabeyli", "madde": "1. Ekli (1) sayılı listede adları yazılı köyler bağlanmak ve merkezi Musabeyli Bucak Merkezi olan Murathüyüğü Köyü olmak ve Musabeyli adıyla bir belediye kurulmak üzere Gaziantep İlinde Musabeyli", "ekHukum": None},
                 2: {"il": "Gaziantep", "ad": "Polateli", "madde": "2. Ekli (2) sayılı listede adları yazılı köyler bağlanmak ve merkezi Polateli Bucak Merkezi olan Güldüzü Köyü olmak ve Polateli adıyla bir belediye kurulmak üzere Gaziantep İlinde Polateli", "ekHukum": None},
                 3: {"il": "Gaziantep", "ad": "Elbeyli", "madde": "3. Ekli (3) sayılı listede adları yazılı köyler bağlanmak ve merkezi Elbeyli Bucak Merkezi olmak ve aynı adla bir belediye kurulmak üzere Gaziantep İlinde Elbeyli adıyla", "ekHukum": None},
                 4: {"il": "İstanbul", "ad": "Çınarcık", "madde": "4. Ekli (4) sayılı listede adları yazılı kasaba ve köyler bağlanmak ve merkezi Çınarcık Bucak Merkezi olmak üzere, İstanbul İlinde Çınarcık", "ekHukum": None},
                 5: {"il": "İstanbul", "ad": "Çiftlikköy", "madde": "5. Ekli (5) sayılı listede adları yazılı bucak, kasaba ve köyler bağlanmak ve merkezi Çiftlikköy Kasabası olmak üzere İstanbul İlinde Çiftlikköy", "ekHukum": None},
                 6: {"il": "Kocaeli", "ad": "Altınova", "madde": "6. Ekli (6) sayılı listede adları yazılı kasaba ve köyler bağlanmak ve merkezi Altınova Kasabası olmak üzere Kocaeli İlinde Altınova", "ekHukum": None},
                 7: {"il": "Bursa", "ad": "Armutlu", "madde": "7. Ekli (7) sayılı listede adları yazılı köyler bağlanmak ve merkezi Armutlu Bucak Merkezi olmak üzere Bursa ilinde Armutlu", "ekHukum": None},
                 8: {"il": "İstanbul", "ad": "Termal", "madde": "8. Ekli (8) sayılı listede adları yazılı köyler bağlanmak ve merkezi Termal Kasabası olmak üzere İstanbul İlinde Termal", "ekHukum": None},
                },
                "digerHukumler": [
                    {"madde": 2, "metin": "Zonguldak iline bağlı Karabük, Gaziantep iline bağlı Kilis ve İstanbul "
                                          "iline bağlı Yalova ilçe merkezleri merkez olmak üzere Karabük, Kilis ve "
                                          "Yalova illeri kurulmuştur (ekli (9)-(11) sayılı listeler).",
                     "eventType": "provinces_created", "effectiveDate": "1995-06-06", "unit": "Karabük, Kilis, Yalova"}]},
}
OUT = ROOT / "data/kaynaklar/resmi_gazete/ilce_kurulus"


def pdf_metin(p):
    with pdfplumber.open(ROOT / p) as pdf:
        return [pg.extract_text() or "" for pg in pdf.pages]


def tekle(s):
    """Kalin puntoda cift yazilmis kelimeler: 'ööpprrüübbaaşşıı' -> 'öprübaşı'."""
    # 'LLÎİSSTTEE': cift harfler OCR'da farkli aksanla okunabiliyor, fold ile karsilastirilir
    return " ".join(w[0::2] if len(w) >= 4 and len(w) % 2 == 0 and fold(w[0::2]) == fold(w[1::2]) else w
                    for w in s.split())


def benzer(a, b):
    return difflib.SequenceMatcher(None, fold(a).replace(" ", ""), fold(b).replace(" ", "")).ratio()


def maddeler(metin):
    """Madde 1 bentleri: {liste_no: {il, ad, madde, ekHukum}}. Bentler numaraya gore
    degil 'adıyla,' bitisine gore bolunur (3392'de 94. bent Resmi Gazete'de '4.'
    basilmis). ekHukum: bentte ilce kurmanin yaninda yapilan birim nakli (orn.
    3644/76: Belkaya Kasabasi Karapinar'dan Eregli'ye; 3644/69: Karakecili
    Kirikkale iline) - mevcut ilcelerin tarihsel sinirini da etkiler."""
    # satir sonu heceleme: 'Köprü-\nköy' -> 'Köprüköy'
    t = re.sub(r"(\w)[-\u00ad]\s*\n\s*(\w)", r"\1\2", metin)
    t = re.sub(r"\s+", " ", t)
    bas = t.find("Madde 1")
    son = t.find("Madde 2", bas)
    t = t[bas:son]
    out = {}
    for govde in re.split(r"(?<=adıyla)[,.;]", t):
        # bendin kendi listesi SON referanstir (onune dipnot girebiliyor: 3392/14 oncesinde
        # "ekli (57) sayılı listede yer alan..." dipnotu)
        lms = list(re.finditer(r"[Ee]kli\s*\((\d+)\)\s*[Ss]ayılı listede", govde))
        if not lms:
            continue
        lm = lms[-1]
        on = govde[:lm.start()]
        bent_no = list(re.finditer(r"(?:^|\s)\d+\s*\.\s", on))
        govde = govde[bent_no[-1].end():].strip() if bent_no else re.sub(
            r"^\s*(?:Madde 1\s*[–-]\s*)?", "", govde).strip()
        lm = list(re.finditer(r"[Ee]kli\s*\((\d+)\)\s*[Ss]ayılı listede", govde))[-1]
        ad = re.search(r"([^\s,]+)\s+[İIi]linde\s+(.+?)\s+adıyla$", govde) or re.search(r"()(\S+)\s+adıyla$", govde)
        ilce_il = re.search(r"kurulan İlçe (\S+) İline bağlanmak", govde)
        out[int(lm.group(1))] = {"il": (ad.group(1) if ad else None) or (ilce_il.group(1) if ilce_il else None),
                                 "ad": ad.group(2) if ad else None,
                                 "madde": govde[:900], "ekHukum": govde[:lm.start()].strip(" ,") or None}
    return out


def il_ilce_adlari(secim, plakalar):
    """{plaka: {ad: geomId}} - o secimdeki ilce satirlari."""
    kayit = load_election(secim)
    out = collections.defaultdict(dict)
    for r in kayit["ilceler"]:
        if r["plaka"] in plakalar:
            out[r["plaka"]][r["ad"]] = r.get("geomId")
    return out


def ayristir(kanun):
    cfg = KANUNLAR[kanun]
    bentler = cfg.get("bentlerElle") or maddeler("\n".join(pdf_metin(cfg["mevzuatPdf"])))
    sayfalar = pdf_metin(cfg["rgPdf"])[:cfg.get("sayfaSayisi")]
    il_adlari = {fold(v["il_ADI"]).replace(" ", ""): int(k)
                 for k, v in json.loads((ROOT / "data/raw/ysk/acikveri-il-ilce-listesi.json").read_text()).items()}
    il_adlari.update({"AFYON": 3, "ICEL": 33})
    sonraki = il_ilce_adlari(cfg["sonrakiGenel"], set(range(1, 82)))
    # kanundan ONCEKI secimin adlari: kaynak ilce sonradan il olmus olabilir (3392: Bayburt,
    # Bartin); onceki adlar oncelikli
    onceki_secim = il_ilce_adlari(cfg["oncekiGenel"], set(range(1, 82)))
    # kanundan SONRA kurulan ilce kaynak olamaz (3806: 1995 listesindeki Esenler 1993'te kuruldu;
    # 'Esenler' bir bucak adi olarak geciyordu). Kurulus tarihi Icisleri kaydindan (idari katman).
    kurulus_of, donusum = {}, set()
    lin = ROOT / "geo/historical/idari/district_lineage.json"
    if lin.exists():
        for d_ in json.loads(lin.read_text(encoding="utf-8"))["districts"]:
            kurulus_of[d_["geomId"]] = (d_.get("kurulus") or {}).get("tarih")
            if d_.get("merkezIlceDonusumu") or (d_.get("kurulus") or {}).get("merkezIlce"):
                donusum.add(d_["geomId"])
    onceki_geom = {g for adlar in onceki_secim.values() for g in adlar.values()}

    def sonra_kurulan(g):
        # kanundan once secimde gorunmuyor, Icisleri kurulusu kanundan sonra ve merkez
        # ilce donusumu (2008/2012 'Merkez' -> yeni ad) degil
        t_ = kurulus_of.get(g)
        return bool(t_ and t_ > cfg["resmiGazete"]["tarih"] and g not in onceki_geom and g not in donusum)
    # bu kanunla kurulan ilceler (il bazinda): kaynak ilce olamazlar
    yeni_adlar = {(il_adlari.get(fold(b["il"] or "").replace(" ", "")), fold(b["ad"])) for b in bentler.values()}

    listeler = collections.defaultdict(lambda: {"satirlar": [], "altBasliklar": [], "sayfalar": set()})
    if cfg.get("bicim") == "cetvel":
        cetvel_oku(sayfalar, listeler)
        sayfalar = []
    liste = None
    varsayilan_ilce = None
    onceki = None
    bitti = False
    baslik_bekle = False
    for no, sayfa in enumerate(sayfalar, start=1):
        if bitti:
            break
        for satir in sayfa.split("\n"):
            s = tekle(satir.strip())
            m = re.search(r"\(\s*(\d+J?)\s*\)?\s*SAY[IİŞ]L[IİŞ]\s*L\S{0,2}STE", s) or \
                re.match(r"^[(\[]?\s*(\d+)\s*[)\]]?\s*Say[ıi]l[ıi]\s+Liste\s*$", s)
            if m:
                baslik_bekle = True
                liste, varsayilan_ilce = int(m.group(1).replace("J", "3")), None
                if liste not in bentler and not re.search(r"\(\s*\d+\s*\)", s) and int(str(liste)[0]) in bentler:
                    liste = int(str(liste)[0])   # kapanis parantezi eksik '(21 Sayılı Liste' = (2)
                if liste > max(bentler):
                    liste = None   # ilce listeleri bitti (KHK 550: (9)-(11) yeni il dokumu)
                    bitti = True
                    break
                listeler[liste]["sayfalar"].add(no)
                continue
            if liste is None:
                continue
            if baslik_bekle:
                baslik_bekle = False
                listeler[liste]["altBasliklar"].append(s)
            if liste == max(bentler) and re.search(r"^İLAN|^YARGI|^YÜRÜTME|^Kanun No|^TBMM|Karar No\s*:", s):
                liste = None
                break
            if liste == max(bentler) and re.search(r"YÜRÜTME|YARGI|İLANLAR|Fihrist|FİHRİST|TARİHİ .*SAYISI|DOLARI|DÖVİZ|EFEKTİF", s):
                liste = None   # ek listeler bitti
                break
            if re.search(r"Alınarak|Belediyesinden", s):
                listeler[liste]["altBasliklar"].append(s)
                m = re.search(r"(\S+)\s+İlçe(?:si)?\s+Belediyesinden", s) or re.search(r"İl[iı]\s+(.+?)\s+İlçesi", s)
                varsayilan_ilce = m.group(1) if m else None
                continue
            if re.search(r"İlçesine\s+Ba[gğ]lanan", s):
                # yeni alt blok ('B) İzmir İli Buca İlçesine Bağlanan Köyler'): ilce sutunlu
                listeler[liste]["altBasliklar"].append(s)
                varsayilan_ilce = None
                continue
            m = re.match(r'^["\'`]?([0-9IlJS|)O]{1,3})[-.,]?\s+((?!\d+\.\s)["\'`(—–-]?[0-9A-Za-zÇĞİÖŞÜçğıöşüÂâÎî].*)$', s)
            numara = None
            if m and not re.search(r"Sayfa|RESM|kurulmuştur", s):
                # sira numarasinda OCR: 'I' 'l' 'J' '|' ')' = 1, 'S' = 5, 'O' = 0 ('3)' = 31); tek
                # satirlik hatalar sonra komsu satirlardan duzeltilir
                ham_no = m.group(1).translate(str.maketrans({"I": "1", "l": "1", "J": "1", "|": "1", ")": "1", "S": "5", "O": "0"}))
                if ham_no.isdigit():
                    numara = int(ham_no)
            if numara is not None:
                govde = m.group(2)
                # tekrar isareti: '—' satir basinda ya da '"' / '»' satir sonunda (3949)
                tire = bool(re.match(r"^[—–-]\s*", govde)) or bool(re.search(r'\s["»]\s*$', govde))
                govde = re.sub(r"^[—–-]\s*", "", govde)
                govde = re.sub(r'\s["»]\s*$', "", govde)
                # iki sutunlu mahalle listesi: '1. Adatepe 11. Efeler'
                parca = re.split(r"\s(\d{1,3})\.\s", govde, maxsplit=1)
                satir_listesi = [(numara, parca[0], m.group(1))]
                if len(parca) == 3:
                    satir_listesi.append((int(parca[1]), parca[2], parca[1]))
                for nm, gv, hn in satir_listesi:
                    listeler[liste]["satirlar"].append({"sira": nm, "ham": gv, "hamNo": hn, "tire": tire,
                                                        "varsayilanIlce": varsayilan_ilce, "sayfa": no})
                listeler[liste]["sayfalar"].add(no)
            elif (listeler[liste]["satirlar"] and len(s.split()) <= 3 and len(listeler[liste]["satirlar"][-1]["ham"].split()) <= 2
                  and not re.search(r"Sayfa|RESM|SAYILI|Bağlanan|Birim|Sıra|No\.|Adı", s)):
                # iki satira kaymis satir: '45. Tem renli' / 'Muradiye Çaldıran'
                listeler[liste]["satirlar"][-1]["ham"] += " " + s
                listeler[liste]["satirlar"][-1]["devamSatiri"] = True
            elif listeler[liste]["satirlar"] or re.search(r"Birim Ad|A\s?d\s?ı\s+İlçesi", onceki or ""):
                # numarasi tamamen dusmus satir: sonra ilce/bucak sutunu eslenirse kabul edilir
                if len(s.split()) >= 3 and not re.search(r"Sayfa|RESM|SAYILI|Bağlanan|Birim|Sıra|No\.", s):
                    listeler[liste]["satirlar"].append({"sira": None, "ham": s, "varsayilanIlce": varsayilan_ilce,
                                                        "sayfa": no, "numarasiz": True})
            onceki = s

    sonuc = []
    for n in sorted(bentler):
        b = bentler[n]
        pl = il_adlari.get(fold(b["il"] or "").replace(" ", ""))
        plakalar = [pl] if pl else cfg["adsizIl"].get(b["ad"], [])
        adaylar = {ad: g for kaynak in (sonraki, onceki_secim) for p in plakalar for ad, g in kaynak.get(p, {}).items()
                   if (p, fold(ad)) not in yeni_adlar and not sonra_kurulan(g)}
        for eski_ad, yeni_ad in cfg.get("kaynakAdEsleme", {}).items():
            if yeni_ad in adaylar:
                adaylar[eski_ad] = adaylar[yeni_ad]
        adaylar_ek = {}
        # il disindan birim alan ilceler (3644/20 Yedisu <- Tunceli/Pulumur): diger illerin
        # adlari yalnizca daha yuksek benzerlik ve tek aday ile kabul edilir
        genel = collections.defaultdict(list)
        for p, adlar in sonraki.items():
            if p in plakalar:
                continue
            for ad, g in adlar.items():
                if fold(ad) != "MERKEZ" and (p, fold(ad)) not in yeni_adlar:
                    genel[ad].append((p, g))
        satirlar = []
        ham_satirlar = []
        if cfg.get("kaynakSutunuYok"):
            listeler.clear()   # ek listede eski ilce sutunu yok: soy bu kaynaktan cikmaz
        for r in listeler.get(n, {}).get("satirlar", []):
            onceki_sira = ham_satirlar[-1]["sira"] if ham_satirlar else 0
            if "S" in (r.get("hamNo") or "") and r["sira"] != onceki_sira + 1:
                # 'S' 5 ya da 8 (6, 3) olabilir: siradaki numarayi veren okuma secilir
                for rakam in "5863":
                    alt = r["hamNo"].replace("S", rakam).translate(str.maketrans({"I": "1", "l": "1", "|": "1", ")": "1", "O": "0"}))
                    if alt.isdigit() and int(alt) == onceki_sira + 1:
                        r = dict(r, sira=int(alt))
                        break
            if r.get("numarasiz"):
                if satir_coz(r, adaylar)["eskiIlce"] is None:
                    continue  # liste satiri degil
                r = dict(r, sira=(ham_satirlar[-1]["sira"] + 1) if ham_satirlar else 1)
            ham_satirlar.append(r)
        # tek satirda bozuk okunan sira: komsulari n-1 ve n+1 ise n
        for i in range(1, len(ham_satirlar) - 1):
            a, b_, c_ = ham_satirlar[i - 1]["sira"], ham_satirlar[i]["sira"], ham_satirlar[i + 1]["sira"]
            if b_ != a + 1 and c_ == a + 2:
                ham_satirlar[i] = dict(ham_satirlar[i], sira=a + 1, siraDuzeltildi=True)
        tire_stili = any(r.get("tire") for r in ham_satirlar)
        for r in ham_satirlar:
            c = satir_coz(r, adaylar)
            if r.get("numarasiz"):
                c["numarasiOkunamadi"] = True
            if r.get("siraDuzeltildi"):
                c["siraDuzeltildi"] = True
            if c["eskiIlce"] is None:
                # OCR bozuk ilce adi ('Ancak' = Arıcak, 'Çat' = Çal): ayni ilde, en iyi aday
                # ikinciden acikca ayrisiyorsa daha dusuk esik
                c = satir_coz(r, adaylar, esik=0.6, fark=0.15)
                if c["eskiIlce"]:
                    c["dusukEsik"] = True
            if c["eskiIlce"] is None and tire_stili and satirlar and satirlar[-1]["eskiIlce"] and len(r["ham"].split()) <= 3:
                # '—' ile gosterilen liste: ilce/bucak sutunu bos = ust satirla ayni
                c = dict(c, birim=r["ham"], eskiIlce=satirlar[-1]["eskiIlce"], eskiBucak=satirlar[-1]["eskiBucak"],
                         ustSatirIleAyni=True)
                if satirlar[-1].get("ilDisi"):
                    c["ilDisi"] = satirlar[-1]["ilDisi"]
            if c["eskiIlce"] is None and len(r["ham"].split()) <= 3 and not r.get("varsayilanIlce") and \
                    re.search(r"Mahalle|Belediyesine\s+Ba[gğ]lanan", " ".join(listeler.get(n, {}).get("altBasliklar", [])), re.I):
                # mahalle listesinde eski ilce yazilmamis (3392/49 Kucukcekmece): tahmin yok
                c = dict(c, birim=r["ham"], tur="mahalle", kaynakYazilmamis=True)
                satirlar.append(c)
                continue
            if c["eskiIlce"] is None:
                d = satir_coz(r, {a: v[0][1] for a, v in genel.items() if len(v) == 1}, esik=0.9)
                if d["eskiIlce"]:
                    d["ilDisi"] = genel[d["eskiIlce"]][0][0]
                    adaylar_ek[d["eskiIlce"]] = genel[d["eskiIlce"]][0][1]
                    c = d
            satirlar.append(c)
        say = collections.Counter(r["eskiIlce"] for r in satirlar)
        ilce_plaka = {r["eskiIlce"]: r.get("ilDisi", pl) for r in satirlar if r["eskiIlce"]}
        ilceler = [{"ad": a, "geomId": adaylar.get(a) or adaylar_ek.get(a), "birimSayisi": c,
                    **({"plaka": ilce_plaka[a]} if a else {})} for a, c in say.most_common()]
        cozulen = [i for i in ilceler if i["ad"]]
        # sira kontrolu: her alt liste 1'den baslar; iki sutunlu listelerde numaralar
        # karisik gelir (1, 15, 2, 16...), bu yuzden blok icinde kume olarak bakilir
        eksik_sira, blok = [], []
        for x in [r["sira"] for r in satirlar] + [1]:
            if x == 1 and blok:
                eksik_sira += sorted(set(range(1, max(blok) + 1)) - set(blok))
                blok = []
            blok.append(x)
        # yeni ilcenin kendisi: kanundan sonraki ilk genel secimdeki satiri (geomId); ad
        # sonradan degismis olabilir (Yenihisar -> Didim), eslesme o secimin adiyla
        hedef_ad = cfg.get("sonrakiAd", {}).get(b["ad"], b["ad"])

        def ad_benzer(ad):   # 'Didim (Yenihisar)': parantez ici/disi ayri karsilastirilir
            return max(benzer(hedef_ad, x) for x in [re.sub(r"\(.*?\)", "", ad)] + re.findall(r"\((.*?)\)", ad))
        yeni = [(ad_benzer(ad), ad, g, p) for p in plakalar for ad, g in sonraki.get(p, {}).items()]
        yeni = max(yeni, default=None)
        if not yeni or yeni[0] < 0.8:
            # kanundan hemen sonra baska ile gecen ilce (3644/106 Guclukonak: Siirt -> Sirnak)
            tum = [(ad_benzer(ad), ad, g, p) for p, adlar in sonraki.items() for ad, g in adlar.items()]
            iyi = sorted((x for x in tum if x[0] >= 0.9), reverse=True)
            # tek aday ya da en iyisi ikinciden acikca onde ('Polateli' vs Ankara 'Polatlı')
            if iyi and (len(iyi) == 1 or iyi[0][0] - iyi[1][0] >= 0.05):
                yeni = iyi[0]
        yeni_geom = {"ad": yeni[1], "geomId": yeni[2], "plaka": yeni[3], "secim": cfg["sonrakiGenel"]} \
            if yeni and yeni[0] >= 0.8 else None
        sonuc.append({
            "listeNo": n, "il": b["il"], "plaka": pl, "ad": b["ad"], "yeniIlce": yeni_geom, "madde": b["madde"], "ekHukum": b["ekHukum"],
            "rgSayfalari": sorted(listeler.get(n, {}).get("sayfalar", [])),
            "altBasliklar": listeler.get(n, {}).get("altBasliklar", []),
            "satirSayisi": len(satirlar), "eskiIlceler": ilceler,
            "tekKaynak": len(cozulen) == 1 and not any(i["ad"] is None for i in ilceler),
            # OCR'da dusen satir varsa tek kaynak kesin degil (dusen birim baska ilceden olabilir)
            "eksikSira": eksik_sira,
            "cozulemeyenSatir": sum(1 for r in satirlar if r["eskiIlce"] is None and not r.get("kaynakYazilmamis")),
            "kaynakYazilmamisSatir": sum(1 for r in satirlar if r.get("kaynakYazilmamis")),
            "satirlar": satirlar,
        })
    # ayni ilcenin birden cok listesi (3949: Guzelbahce mahalle + koy listeleri) birlestirilir
    birlesik = collections.OrderedDict()
    for x in sonuc:
        k = (x["plaka"], x["ad"])
        if k not in birlesik:
            birlesik[k] = x
            continue
        y = birlesik[k]
        y["satirlar"] += x["satirlar"]
        y["rgSayfalari"] = sorted(set(y["rgSayfalari"]) | set(x["rgSayfalari"]))
        y["altBasliklar"] += x["altBasliklar"]
        y["listeNo"] = f"{y['listeNo']}+{x['listeNo']}"
        say = collections.Counter(r["eskiIlce"] for r in y["satirlar"])
        geo = {e["ad"]: (e["geomId"], e.get("plaka")) for e in y["eskiIlceler"] + x["eskiIlceler"]}
        y["eskiIlceler"] = [{"ad": a, "geomId": geo.get(a, (None, None))[0], "birimSayisi": c,
                             **({"plaka": geo.get(a, (None, None))[1]} if a else {})} for a, c in say.most_common()]
        y["satirSayisi"] = len(y["satirlar"])
        y["eksikSira"] += x["eksikSira"]
        y["cozulemeyenSatir"] += x["cozulemeyenSatir"]
        y["kaynakYazilmamisSatir"] += x["kaynakYazilmamisSatir"]
        cozulen = [i for i in y["eskiIlceler"] if i["ad"]]
        y["tekKaynak"] = len(cozulen) == 1 and not any(i["ad"] is None for i in y["eskiIlceler"])
    return cfg, list(birlesik.values())


def cetvel_oku(sayfalar, listeler):
    """1960-1980'lerin 'CETVEL No. : N' bicimi: satir 'N <köy> [X İli Y İlçesi Z Bucağından]';
    kaynak yazili degilse ('»' ya da bos) ustteki satirin kaynagi gecerli. Satirlar
    genel satir_coz'un anlayacagi '<köy> <ilçe> <bucak>' bicimine cevrilir."""
    liste, kaynak, bucak = None, None, None
    for no, sayfa in enumerate(sayfalar, start=1):
        for satir in sayfa.split("\n"):
            s = satir.strip()
            m = re.search(r"CETVEL\s*No\.?\s*:?\s*(\d+)", s, re.I)
            if m:
                liste, kaynak, bucak = int(m.group(1)), None, None
                continue
            if liste is None:
                continue
            m = re.match(r"^(\d{1,3})\s+(.+)$", s)
            if not m:
                continue
            govde = m.group(2)
            k = re.search(r"(\S+)\s+(?:[İI1l][lıi1]{1,2})\s+(\S+)\s+İlçesi(?:\s+(\S+)\s+Bu)?", govde)  # 'İli' OCR: '111' 
            if k:
                kaynak, bucak = k.group(2), k.group(3) or "Merkez"
                ad = govde[:k.start()].strip()
            else:
                ad = re.sub(r"[»>*]+\s*$", "", govde).strip()
            if not kaynak:
                continue
            listeler[liste]["satirlar"].append({"sira": int(m.group(1)), "ham": f"{ad} {kaynak} {bucak}",
                                                "hamNo": m.group(1), "tire": not k, "varsayilanIlce": None,
                                                "sayfa": no, "cetvelKaynakYazili": bool(k)})
            listeler[liste]["sayfalar"].add(no)


def satir_coz(r, adaylar, esik=0.8, fark=0.0):
    """'Arpalı Sürmene Köprübaşı' -> birim, eski ilce, eski bucak. Ilce sutunu
    adaylara bulanik eslenir; en iyi eslesme >= esik ve (fark > 0 ise) ikinci en
    iyi FARKLI adaydan en az `fark` kadar yuksekse kabul."""
    tok = r["ham"].replace("’", "'").split()
    tur = "belde" if "(B)" in r["ham"] else None
    en_iyi, puanlar = None, collections.defaultdict(float)
    for k in (1, 2, 3):        # bucak kelime sayisi ('Marmara Ereğli si')
        for m in (1, 2):       # ilce kelime sayisi
            if len(tok) < k + m + 1:
                continue
            aday = " ".join(tok[-(k + m):-k])
            for ad in adaylar:
                sk = benzer(aday, ad)
                puanlar[ad] = max(puanlar[ad], sk)
                if sk >= esik and (en_iyi is None or sk > en_iyi[0] + 1e-9):
                    en_iyi = (sk, ad, " ".join(tok[:-(k + m)]), " ".join(tok[-k:]))
    if en_iyi and fark:
        ikinci = max((v for a, v in puanlar.items() if a != en_iyi[1]), default=0)
        if en_iyi[0] - ikinci < fark:
            en_iyi = None
    if en_iyi:
        _, ilce, birim, bucak = en_iyi
        return {"sira": r["sira"], "birim": birim.replace("(B)", "").strip(), "tur": tur, "eskiIlce": ilce,
                "eskiBucak": bucak, "okunan": r["ham"], "sayfa": r["sayfa"]}
    if r["varsayilanIlce"]:
        ad = max(adaylar, key=lambda a: benzer(a, r["varsayilanIlce"]), default=None)
        if ad and benzer(ad, r["varsayilanIlce"]) >= 0.8:
            return {"sira": r["sira"], "birim": r["ham"], "tur": "mahalle", "eskiIlce": ad, "eskiBucak": None,
                    "okunan": r["ham"], "altBaslik": r["varsayilanIlce"], "sayfa": r["sayfa"]}
    return {"sira": r["sira"], "birim": None, "tur": tur, "eskiIlce": None, "eskiBucak": None,
            "okunan": r["ham"], "sayfa": r["sayfa"]}


def main():
    kanun = sys.argv[1]
    cfg, sonuc = ayristir(kanun)
    OUT.mkdir(parents=True, exist_ok=True)
    veri = {
        "kanun": kanun, "ad": cfg["ad"], "kabul": cfg["kabul"], "resmiGazete": cfg["resmiGazete"],
        "kaynaklar": {"ekListeler": cfg["rgPdf"], "maddeler": cfg["mevzuatPdf"] or cfg["rgPdf"],
                      "rgUrl": cfg.get("rgUrl") or f"https://www.resmigazete.gov.tr/arsiv/{cfg['resmiGazete']['sayi']}.pdf",
                      "mevzuatUrl": f"https://www.mevzuat.gov.tr/mevzuatmetin/1.5.{kanun}.pdf" if cfg["mevzuatPdf"] else None},
        "digerHukumler": cfg.get("digerHukumler", []),
        "guvenilirlik": "A (birincil/resmî); ek listeler taranmış OCR — eski ilçe adı o ilin sonraki genel seçimdeki "
                        "ilçe adlarıyla bulanık eşlendi, eşlenemeyen satır null bırakıldı",
        "ozet": {"ilce": len(sonuc), "tekKaynak": sum(1 for s in sonuc if s["tekKaynak"]),
                 "cokKaynak": sum(1 for s in sonuc if len([i for i in s["eskiIlceler"] if i["ad"]]) > 1),
                 "satir": sum(s["satirSayisi"] for s in sonuc),
                 "cozulemeyenSatir": sum(s["cozulemeyenSatir"] for s in sonuc),
                 "kaynakYazilmamisSatir": sum(1 for s in sonuc for r in s["satirlar"] if r.get("kaynakYazilmamis")),
                 "satirsizListe": [s["listeNo"] for s in sonuc if not s["satirSayisi"]],
                 "eksikSatirliListe": [s["listeNo"] for s in sonuc if s["eksikSira"]],
                 "geomIdsizYeniIlce": [s["ad"] for s in sonuc if not s["yeniIlce"]]},
        "ilceler": sonuc,
    }
    (OUT / f"{kanun.replace(' ', '_')}.json").write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(veri["ozet"], ensure_ascii=False))


if __name__ == "__main__":
    main()
