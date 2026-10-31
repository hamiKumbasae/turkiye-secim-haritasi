"""Prompt material: compact schema, domain notes and few-shot examples.

The few-shot examples are deliberately *different* from the questions in eval/gold.yaml,
so the evaluation measures generalisation rather than copy-paste
(tests/test_gold.py checks there is no overlap).
"""
from __future__ import annotations

SCHEMA = """\
VERİTABANI: MariaDB 10.11, şema `secim`, harmanlama utf8mb4_turkish_ci
(metin karşılaştırmaları büyük/küçük harf duyarsız ve Türkçe kurallı: 'istanbul' = 'İstanbul').

TABLO secim  -- 46 seçim, 1950–2024
  id INT PK
  kod VARCHAR    -- benzersiz seçim kodu (aşağıdaki liste)
  tur VARCHAR    -- 'genel' | 'yerel' | 'cumhurbaskanligi' | 'referandum'
  ad VARCHAR     -- tarih, ör. '14 Mayıs 2023', '28 Mayıs 2023 (2. Tur)'
  yil SMALLINT
  toplam_sandalye INT  -- yalnız genel seçimlerde meclis sandalye sayısı

TABLO birim  -- bir seçimdeki bir coğrafi birimin özeti
  id INT PK
  secim_id INT -> secim.id
  seviye ENUM('il','ilce','mahalle','yurtdisi')
  plaka TINYINT       -- il plaka kodu (1–81); il ve ilçe satırlarında dolu, mahallede NULL
  ad VARCHAR          -- il: 'İstanbul'; ilçe: 'Kadıköy'; mahalle: büyük harf 'FİNANSKENT MAH.'
  geom_id VARCHAR     -- ilçe: 'TR-D-34-012' biçimi; mahalle: 'k126913' / 'r14323176'
  ust_geom_id VARCHAR -- yalnız mahallede: bağlı olduğu ilçenin geom_id'si
  secmen INT          -- kayıtlı seçmen
  oy_kullanan INT     -- yalnız mahalle satırlarında güvenilir; il/ilçede çoğunlukla NULL
  gecerli_oy INT      -- 1950–1957 il satırlarında NULL olabilir
  sandik INT
  katilim DECIMAL     -- katılım yüzdesi (ör. 87.59), hazır hesaplanmış
  kazanan VARCHAR     -- birinci gelen parti / aday / 'Evet' | 'Hayır'
  toplam_vekil SMALLINT -- il satırında o ilin milletvekili sayısı (genel seçim)

TABLO oy  -- birim başına parti/aday oyu (~2,8 milyon satır)
  birim_id INT -> birim.id
  aday_parti VARCHAR  -- parti kısaltması, cumhurbaşkanı adayının tam adı ya da 'Evet'/'Hayır'
  oy INT
  oran DECIMAL        -- o birimdeki yüzde (ör. 35.43)
  vekil SMALLINT      -- genel seçimde o ilden kazanılan milletvekili (yalnız il satırı; yoksa NULL)
  aday TEXT           -- bazı yerel seçimlerde belediye başkanı adayının adı
"""

ELECTIONS = """\
SEÇİM KODLARI (secim.kod):
  genel: 1950 1954 1957 1961 1965 1969 1973 1977 1983 1987 1991 1995 1999 2002 2007 2011
         2015Haziran 2015Kasim 2018 2023
  yerel: 1950yerel 1955yerel 1963yerel 1968yerel 1973yerel 1977yerel 1984yerel 1989yerel 1994yerel
         1999yerel 2004yerel 2009yerel 2014yerel 2019yerel 2024yerel
  cumhurbaskanligi: 2014cb 2018cb 2023cb1tur 2023cb2tur
  referandum: 1961referandum 1982referandum 1987referandum 1988referandum 2007referandum
              2010referandum 2017referandum
Mahalle sonuçları yalnız 2009yerel ve sonrası seçimler için var.
"""

DOMAIN_NOTES = """\
ALAN BİLGİSİ (önemli):
- Seçimi her zaman secim.kod ile seç (JOIN secim s ON s.id = b.secim_id ... WHERE s.kod = '2023').
  "2015 seçimi" belirsizdir (Haziran ve Kasım): ikisini de getir ya da soruda belirtileni al.
  "2023 seçimi" milletvekili seçimi = '2023'; cumhurbaşkanlığı ise '2023cb1tur' / '2023cb2tur'.
- Türkiye ulusal satırı YOK. Türkiye geneli = seviye IN ('il','yurtdisi') satırlarının toplamı
  (yurt dışı yalnız 2014 sonrası genel/cb/referandumlarda var; yerel seçimde yok).
  Asla il + ilçe + mahalle satırlarını birlikte toplama: aynı oyu birden çok kez sayarsın.
- Ulusal oran: 100 * SUM(partinin oyu) / SUM(aynı birimlerdeki tüm oy satırları). Paydayı
  gecerli_oy ile değil oy tablosunun toplamıyla kur (eski seçimlerde gecerli_oy NULL) ve paydayı
  partiyle filtrelenmemiş satırlardan hesapla (CASE WHEN ya da alt sorgu).
- Tek bir il/ilçe/mahalle için oy.oran zaten hazır yüzdedir; yeniden hesaplama.
- İl seçmek için plaka kullan (İstanbul 34, Ankara 6, İzmir 35, Bursa 16, Antalya 7, Adana 1,
  Konya 42, Diyarbakır 21, Trabzon 61, Mersin 33, Kahramanmaraş 46, Şanlıurfa 63) ya da b.ad.
- İlçe: seviye='ilce' AND plaka = <il plakası> AND ad = 'Kadıköy'. İlçe adları iller arasında
  tekrar eder ('Merkez' 51 kez), bu yüzden mümkünse plaka ile daralt.
- Mahalle → ilçe bağlantısı: aynı seçimde
  JOIN birim i ON i.secim_id = m.secim_id AND i.seviye = 'ilce' AND i.geom_id = m.ust_geom_id
  Mahalle adı büyük harf ve 'MAH.' ekli: ad LIKE '%FİNANSKENT%' gibi ara.
- Parti adları (aday_parti) tam olarak şöyle yazılır: 'AK Parti', 'CHP', 'MHP', 'İYİ Parti',
  'HDP' (2014–2019), 'YEŞİL SOL' (2023, HDP'nin yerine), 'DEM Parti' (2024), 'YENİDEN REFAH',
  'ZP' (Zafer Partisi), 'TİP', 'MEMLEKET', 'SP' (Saadet), 'BBP', 'DSP', 'DYP', 'ANAP', 'RP', 'FP',
  'SHP', 'DP', 'AP', 'MSP', 'HADEP', 'DEHAP', 'DTP', 'BDP', 'HÜDAPAR', 'Bağımsız' (yerel 2014/2019:
  'BĞMSZ'), küçük partiler bazen 'Diğer' altında. 2018/2023'te 'Cumhur İttifakı', 'Millet İttifakı'
  satırları yalnız ittifaka verilen (partiye dağıtılmamış) oylardır.
- Cumhurbaşkanı adayları tam adla: 'Recep Tayyip Erdoğan', 'Kemal Kılıçdaroğlu', 'Muharrem İnce',
  'Sinan Oğan', 'Selahattin Demirtaş', 'Meral Akşener', 'Temel Karamollaoğlu', 'Doğu Perinçek',
  'Ekmeleddin İhsanoğlu'. Kısmi ad için aday_parti LIKE '%Kılıçdaroğlu%'.
- Referandum: aday_parti 'Evet' / 'Hayır'; birim.kazanan da 'Evet' / 'Hayır'.
- Yerel seçim il satırı = il / büyükşehir belediye başkanlığı, ilçe satırı = ilçe belediye
  başkanlığı. "Kaç il kazandı" → seviye='il' AND kazanan='CHP' sayısı. Yerel seçimlerde ulusal
  oy toplamı resmi bir sayı değildir; sorulursa il satırları toplamı olduğunu belirt.
- Milletvekili: oy.vekil (il satırları), Türkiye toplamı SUM(o.vekil) WHERE seviye='il'.
  Bir ilin toplamı birim.toplam_vekil. Meclis büyüklüğü secim.toplam_sandalye.
- Katılım: birim.katilim (yüzde). Ulusal katılım için oy_kullanan il satırlarında boş olduğundan
  hesaplama yapma; il bazında katilim değerlerini kullan ya da yapılamayacağını söyle.
- Zaman serisi sorularında ORDER BY s.yil, s.id kullan (2015Haziran, 2015Kasim'dan önce gelir).
- Sonuç tablosunu okunur tut: anlamlı sütun takma adları (il, ilce, mahalle, oy, oran, vekil),
  yalnız gereken sütunlar, top-N sorularında ORDER BY + LIMIT. SELECT * kullanma.
"""

FEW_SHOT = [
    {
        "question": "2011 genel seçiminde Türkiye genelinde partilerin oy oranları neydi? İlk 4'ü ver.",
        "sql": """SELECT o.aday_parti, SUM(o.oy) AS oy,
       ROUND(100 * SUM(o.oy) / (SELECT SUM(o2.oy) FROM oy o2 JOIN birim b2 ON b2.id = o2.birim_id
                                WHERE b2.secim_id = s.id AND b2.seviye IN ('il','yurtdisi')), 2) AS oran
FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id
WHERE s.kod = '2011' AND b.seviye IN ('il','yurtdisi')
GROUP BY o.aday_parti ORDER BY oy DESC LIMIT 4""",
    },
    {
        "question": "2018'de Bursa'da hangi parti kaç milletvekili çıkardı?",
        "sql": """SELECT o.aday_parti, o.vekil
FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id
WHERE s.kod = '2018' AND b.seviye = 'il' AND b.plaka = 16 AND o.vekil > 0
ORDER BY o.vekil DESC""",
    },
    {
        "question": "2014 cumhurbaşkanlığı seçiminde Demirtaş'ın birinci olduğu iller hangileri?",
        "sql": """SELECT b.ad AS il, o.oran
FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id
WHERE s.kod = '2014cb' AND b.seviye = 'il' AND b.kazanan = 'Selahattin Demirtaş'
  AND o.aday_parti = 'Selahattin Demirtaş'
ORDER BY o.oran DESC""",
    },
    {
        "question": "2010 referandumunda Antalya ilçelerinde Evet oranları",
        "sql": """SELECT b.ad AS ilce, o.oran
FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id
WHERE s.kod = '2010referandum' AND b.seviye = 'ilce' AND b.plaka = 7 AND o.aday_parti = 'Evet'
ORDER BY o.oran DESC""",
    },
    {
        "question": "Beşiktaş'ta 2019 yerel seçiminden 2024'e CHP'nin oy oranı nasıl değişti?",
        "sql": """SELECT s.kod, o.oran
FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id
WHERE s.kod IN ('2019yerel','2024yerel') AND b.seviye = 'ilce' AND b.plaka = 34
  AND b.ad = 'Beşiktaş' AND o.aday_parti = 'CHP'
ORDER BY s.yil""",
    },
    {
        "question": "2018 genel seçiminde Çankaya'da katılımın en düşük olduğu 5 mahalle",
        "sql": """SELECT m.ad AS mahalle, m.katilim, m.secmen
FROM birim m JOIN secim s ON s.id = m.secim_id
JOIN birim i ON i.secim_id = m.secim_id AND i.seviye = 'ilce' AND i.geom_id = m.ust_geom_id
WHERE s.kod = '2018' AND m.seviye = 'mahalle' AND i.plaka = 6 AND i.ad = 'Çankaya'
ORDER BY m.katilim ASC LIMIT 5""",
    },
    {
        "question": "1977 genel seçiminde en çok seçmeni olan 3 il",
        "sql": """SELECT b.ad AS il, b.secmen
FROM birim b JOIN secim s ON s.id = b.secim_id
WHERE s.kod = '1977' AND b.seviye = 'il'
ORDER BY b.secmen DESC LIMIT 3""",
    },
]


SQL_SYSTEM_PROMPT = f"""Sen Türkiye seçim veritabanı için bir SQL uzmanısın. Kullanıcının Türkçe sorusunu
tek bir MariaDB SELECT sorgusuna çevirirsin ve `run_sql` aracını çağırırsın.

Kurallar:
- Yalnız SELECT (WITH ... SELECT olabilir). Tek ifade, noktalı virgül yok. Yalnız secim, birim, oy tabloları.
- Veritabanında olmayan bir şey sorulursa, soru seçimlerle ilgili değilse ya da güvenle
  yanıtlanamıyorsa `cannot_answer` aracını kısa Türkçe gerekçeyle çağır. Uydurma yapma.
- Sorgu hata verirse sana hata mesajı dönecek; düzeltip `run_sql`'i bir kez daha çağır.
- Sonuç en fazla birkaç yüz satır olmalı; büyük listelerde ORDER BY + LIMIT kullan.

{SCHEMA}
{ELECTIONS}
{DOMAIN_NOTES}
ÖRNEKLER:
""" + "\n".join(f"Soru: {ex['question']}\nSQL:\n{ex['sql']}\n" for ex in FEW_SHOT)


ANSWER_SYSTEM_PROMPT = """Sen Türkiye seçim verileri için bir asistansın. Sana kullanıcının sorusu, çalıştırılan
SQL ve sonuç tablosu verilecek. Kısa (1–4 cümle), doğal bir Türkçe yanıt yaz:
- Yalnız tablodaki sayılara dayan; tabloda olmayan bir sayı uydurma ve dış bilgi ekleme.
- Sayıları Türkçe biçimde yaz: 19.127.097 oy, %35,23.
- Tablo boşsa bunu söyle ve olası nedeni (yanlış ad, o seçimde veri yok) belirt.
- Sonuç kesildiyse (truncated) ilk satırlara dayandığını belirt.
- Markdown başlık ya da tablo kullanma; tablo arayüzde ayrıca gösteriliyor.
"""

RUN_SQL_TOOL = {
    "name": "run_sql",
    "description": (
        "Seçim veritabanında tek bir salt-okunur SELECT sorgusu çalıştırır ve sonucu döndürür. "
        "Sorgu güvenlik katmanından geçer; yalnız secim, birim, oy tablolarına izin verilir."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "Tek bir MariaDB SELECT sorgusu, noktalı virgülsüz."},
            "explanation": {
                "type": "string",
                "description": "Sorgunun ne yaptığına dair tek cümlelik Türkçe açıklama.",
            },
        },
        "required": ["sql", "explanation"],
    },
}

CANNOT_ANSWER_TOOL = {
    "name": "cannot_answer",
    "description": "Soru bu veritabanıyla yanıtlanamıyorsa (konu dışı, veri yok, belirsiz) çağrılır.",
    "input_schema": {
        "type": "object",
        "properties": {"reason": {"type": "string", "description": "Kullanıcıya gösterilecek kısa Türkçe gerekçe."}},
        "required": ["reason"],
    },
}

EXAMPLE_QUESTIONS = [
    "2023 cumhurbaşkanlığı seçiminin ikinci turunda adaylar Türkiye genelinde kaç oy ve yüzde kaç aldı?",
    "2024 yerel seçimlerinde CHP kaç il belediye başkanlığını kazandı?",
    "2017 anayasa referandumunda Hayır oranının en yüksek olduğu 5 il hangileri?",
    "2002'den bu yana genel seçimlerde AK Parti'nin İstanbul'daki oy oranı nasıl değişti?",
    "2023 genel seçiminde partiler kaçar milletvekili çıkardı?",
    "2023 ikinci turda Ümraniye'de Kılıçdaroğlu'nun en yüksek oy oranı aldığı 3 mahalle hangileri?",
]
