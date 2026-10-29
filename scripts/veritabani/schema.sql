-- Türkiye Seçim Haritası — ilişkisel şema (SQLite)
-- Üretim: python3 scripts/veritabani/build_db.py   (ayrıntı: docs/VERITABANI.md)
--
-- Sözlük tabloları : secim, il, ilce, mahalle, secenek
-- Sonuç tabloları  : sonuc_il, sonuc_ilce, sonuc_mahalle   (seçmen, katılım, geçerli oy ...)
-- Oy tabloları     : oy_il, oy_ilce, oy_mahalle            (seçenek başına oy ve oran)
-- Sandalye         : sandalye_il, sandalye_ilce             (milletvekili; 2024 belediye meclisi)
-- Kişiler          : secilen                                (seçilen milletvekili ve senatörler)
-- Belde            : sonuc_belde, oy_belde                  (belde belediye başkanlığı ve meclisi)
-- Kapsam           : kaynak_kapsami                         (kaynakta kaç kayıt bulundu / beklendi)

PRAGMA foreign_keys = ON;

-- Bir oylama. Ana seçimler ('2023', '2024yerel', '2017referandum', '2023cb2tur') yanında
-- aynı günün ikincil oylamaları da ayrı satırdır: '2024yerel_bm' (belediye meclisi),
-- '2024yerel_igm' (il genel meclisi); ana seçime ana_secim_id ile bağlanır.
-- Senato ('1961senato') ve ara/yenileme seçimleri ('2019istanbul_bb_yenileme') de buradadır.
CREATE TABLE secim (
    secim_id        TEXT PRIMARY KEY,
    tur             TEXT NOT NULL CHECK (tur IN ('genel','yerel','referandum','cumhurbaskanligi','senato','ara')),
    oylama          TEXT NOT NULL CHECK (oylama IN ('milletvekili','baskanlik','belediye_meclisi',
                                                    'il_genel_meclisi','referandum','cumhurbaskanligi','senato')),
    ana_secim_id    TEXT REFERENCES secim(secim_id),
    yil             INTEGER NOT NULL,
    ad              TEXT NOT NULL,          -- kaynaktaki tarih/ad, ör. '14 Mayıs 2023'
    aciklama        TEXT,
    yarisma_turu    TEXT,                   -- yerel: municipal_indirect | mayor_direct | council_votes
    sonuc_temeli    TEXT,                   -- yerel: votes | council_seats | mixed
    toplam_sandalye INTEGER,
    mahalle_verisi  INTEGER NOT NULL DEFAULT 0   -- 1 = mahalle düzeyi sonuç var
);

-- İl. plaka 0 = yurt dışı / gümrük oyları
CREATE TABLE il (
    plaka INTEGER PRIMARY KEY,
    ad    TEXT NOT NULL                     -- en güncel seçimdeki adı
);

-- İlçe birimi. Güncel ilçeler 'TR-D-<plaka>-<no>', tarihsel/sentetik birimler 'HIST...'.
-- Aynı birim farklı seçimlerde farklı adla ya da farklı ilde görünebilir;
-- o seçimdeki ad/il sonuc_ilce'de tutulur, burada son görülen değerler var.
CREATE TABLE ilce (
    ilce_id TEXT PRIMARY KEY,
    plaka   INTEGER NOT NULL REFERENCES il(plaka),
    ad      TEXT NOT NULL,
    guncel  INTEGER NOT NULL                -- 1 = bugünkü 973 ilçeden biri
);

-- Mahalle / köy (muhtarlık). mahalle_id kaynak kimliği: r... (OSM), k... (TKGM) vb.
CREATE TABLE mahalle (
    mahalle_id TEXT NOT NULL,
    ilce_id    TEXT NOT NULL REFERENCES ilce(ilce_id),
    ad         TEXT,                        -- geometri dosyasındaki ad (yoksa NULL)
    PRIMARY KEY (ilce_id, mahalle_id)
);

-- Oy verilen seçenek: parti, cumhurbaşkanı adayı, referandum seçeneği ya da 'Diğer'/'Bağımsız'
CREATE TABLE secenek (
    secenek_id INTEGER PRIMARY KEY,
    ad         TEXT NOT NULL UNIQUE,        -- kaynaktaki anahtar, ör. 'AK Parti', 'CHP', 'Evet'
    kisa       TEXT,                        -- partiler.json kısaltması
    tip        TEXT NOT NULL CHECK (tip IN ('parti','aday','referandum','diger')),
    renk_acik  TEXT,
    renk_koyu  TEXT
);

-- Sonuç satırları: ortak alanlar ------------------------------------------
CREATE TABLE sonuc_il (
    secim_id    TEXT    NOT NULL REFERENCES secim(secim_id),
    plaka       INTEGER NOT NULL REFERENCES il(plaka),
    ad          TEXT    NOT NULL,           -- o seçimdeki il adı
    secmen      INTEGER,
    oy_kullanan INTEGER,
    gecerli_oy  INTEGER,
    gecersiz_oy INTEGER,
    sandik      INTEGER,
    katilim     REAL,
    kazanan_id  INTEGER REFERENCES secenek(secenek_id),
    toplam_vekil INTEGER,
    ilce_sayisi INTEGER,
    not_metni   TEXT,
    kaynak_json TEXT,                       -- kaynak/düzeltme bilgisi, JSON olarak aynen
    PRIMARY KEY (secim_id, plaka)
);

CREATE TABLE sonuc_ilce (
    secim_id    TEXT    NOT NULL REFERENCES secim(secim_id),
    ilce_id     TEXT    NOT NULL REFERENCES ilce(ilce_id),
    plaka       INTEGER NOT NULL REFERENCES il(plaka),   -- o seçimdeki il
    ad          TEXT    NOT NULL,                        -- o seçimdeki ilçe adı
    secmen      INTEGER,
    oy_kullanan INTEGER,
    gecerli_oy  INTEGER,
    gecersiz_oy INTEGER,
    sandik      INTEGER,
    katilim     REAL,
    kazanan_id  INTEGER REFERENCES secenek(secenek_id),
    baskan      TEXT,                       -- yerel: seçilen başkan adı (varsa)
    sadece_kazanan INTEGER NOT NULL DEFAULT 0,  -- 1 = yalnız kazanan biliniyor, oy yok
    buyuksehir_sonucu INTEGER NOT NULL DEFAULT 0,
    not_metni   TEXT,
    kaynak_json TEXT,
    PRIMARY KEY (secim_id, ilce_id)
);

CREATE TABLE sonuc_mahalle (
    secim_id    TEXT NOT NULL REFERENCES secim(secim_id),
    ilce_id     TEXT NOT NULL,
    mahalle_id  TEXT NOT NULL,
    secmen      INTEGER,
    oy_kullanan INTEGER,
    gecerli_oy  INTEGER,
    sandik      INTEGER,
    katilim     REAL,
    kazanan_id  INTEGER REFERENCES secenek(secenek_id),
    PRIMARY KEY (secim_id, ilce_id, mahalle_id),
    FOREIGN KEY (ilce_id, mahalle_id) REFERENCES mahalle(ilce_id, mahalle_id)
);

-- Oylar -------------------------------------------------------------------
CREATE TABLE oy_il (
    secim_id   TEXT    NOT NULL,
    plaka      INTEGER NOT NULL,
    secenek_id INTEGER NOT NULL REFERENCES secenek(secenek_id),
    oy         INTEGER,
    oran       REAL,
    PRIMARY KEY (secim_id, plaka, secenek_id),
    FOREIGN KEY (secim_id, plaka) REFERENCES sonuc_il(secim_id, plaka)
);

CREATE TABLE oy_ilce (
    secim_id   TEXT    NOT NULL,
    ilce_id    TEXT    NOT NULL,
    secenek_id INTEGER NOT NULL REFERENCES secenek(secenek_id),
    oy         INTEGER,
    oran       REAL,
    aday       TEXT,                        -- yerel: partinin belediye başkanı adayı
    sandalye   INTEGER,                     -- dolaylı seçimlerde meclis sandalyesi
    PRIMARY KEY (secim_id, ilce_id, secenek_id),
    FOREIGN KEY (secim_id, ilce_id) REFERENCES sonuc_ilce(secim_id, ilce_id)
);

CREATE TABLE oy_mahalle (
    secim_id   TEXT    NOT NULL,
    ilce_id    TEXT    NOT NULL,
    mahalle_id TEXT    NOT NULL,
    secenek_id INTEGER NOT NULL REFERENCES secenek(secenek_id),
    oy         INTEGER,
    oran       REAL,
    PRIMARY KEY (secim_id, ilce_id, mahalle_id, secenek_id),
    FOREIGN KEY (secim_id, ilce_id, mahalle_id)
        REFERENCES sonuc_mahalle(secim_id, ilce_id, mahalle_id)
) WITHOUT ROWID;

CREATE TABLE sandalye_il (
    secim_id   TEXT    NOT NULL,
    plaka      INTEGER NOT NULL,
    secenek_id INTEGER NOT NULL REFERENCES secenek(secenek_id),
    sandalye   INTEGER NOT NULL,
    PRIMARY KEY (secim_id, plaka, secenek_id),
    FOREIGN KEY (secim_id, plaka) REFERENCES sonuc_il(secim_id, plaka)
);

-- 2024 belediye meclisi üye dağılımı (ilçe başına)
CREATE TABLE sandalye_ilce (
    secim_id   TEXT    NOT NULL REFERENCES secim(secim_id),
    ilce_id    TEXT    NOT NULL REFERENCES ilce(ilce_id),
    secenek_id INTEGER NOT NULL REFERENCES secenek(secenek_id),
    sandalye   INTEGER NOT NULL,
    PRIMARY KEY (secim_id, ilce_id, secenek_id)
);

-- Seçilen kişiler: milletvekilleri (genel/ara seçim) ve Cumhuriyet Senatosu üyeleri.
-- Kaynak (Vikipedi) eksik olabilir; kaç kişi bulunduğu kaynak_kapsami'nda.
CREATE TABLE secilen (
    secilen_id   INTEGER PRIMARY KEY,
    secim_id     TEXT    NOT NULL REFERENCES secim(secim_id),
    plaka        INTEGER NOT NULL REFERENCES il(plaka),
    gorev        TEXT    NOT NULL CHECK (gorev IN ('milletvekili','senator')),
    ad           TEXT    NOT NULL,
    secenek_id   INTEGER REFERENCES secenek(secenek_id),   -- NULL: kaynakta parti yok
    parti_adi_kaynakta TEXT,
    bolge        TEXT,                                     -- çok bölgeli illerde seçim bölgesi
    kisi_link    TEXT,                                     -- Vikipedi madde adı
    kaynak_json  TEXT
);

-- Belde belediyeleri. Belde kimliği kaynaklar arasında ortak değil (eski yıllar taranmış
-- kitaptan okunan adlar, 2009 sonrası yalnız YSK belde kodu), bu yüzden ayrı bir belde
-- sözlüğü yok; her satır bir seçimdeki bir beldedir.
CREATE TABLE sonuc_belde (
    sonuc_belde_id INTEGER PRIMARY KEY,
    secim_id    TEXT    NOT NULL REFERENCES secim(secim_id),  -- başkanlık: '1994yerel', meclis: '1994yerel_bm'
    plaka       INTEGER NOT NULL REFERENCES il(plaka),
    ilce_id     TEXT    REFERENCES ilce(ilce_id),             -- adından eşleşebildiyse
    ilce_ad     TEXT,
    belde_ad    TEXT,                                         -- 2009 sonrası meclis kayıtlarında NULL
    belde_kod   INTEGER,                                      -- YSK belde kodu (2009 sonrası)
    secmen      INTEGER,
    oy_kullanan INTEGER,
    gecerli_oy  INTEGER,
    gecersiz_oy INTEGER,
    sandik      INTEGER,
    katilim     REAL,
    kazanan_id  INTEGER REFERENCES secenek(secenek_id),
    aday        TEXT,                                         -- kazanan başkan adayı
    sadece_kazanan INTEGER NOT NULL DEFAULT 0,               -- 1 = yalnız kazananın oyu biliniyor
    kaynak      TEXT NOT NULL,                                -- wikipedia | tuik | ysk
    kontrol     TEXT,      -- taranmış kitap satırının doğrulama sonucu: tutarli | toplamTutmuyor | tutarsiz ...
    not_metni   TEXT,
    kaynak_json TEXT
);

CREATE TABLE oy_belde (
    sonuc_belde_id INTEGER NOT NULL REFERENCES sonuc_belde(sonuc_belde_id),
    secenek_id     INTEGER NOT NULL REFERENCES secenek(secenek_id),
    oy             INTEGER,
    PRIMARY KEY (sonuc_belde_id, secenek_id)
);

-- Kaynakta ne kadar veri bulunduğu: eksikliği sorgulanabilir kılar
CREATE TABLE kaynak_kapsami (
    secim_id  TEXT NOT NULL REFERENCES secim(secim_id),
    veri      TEXT NOT NULL,          -- milletvekilleri | senatorler | beldeler | belediye_meclisi | il_genel_meclisi ...
    bulunan   INTEGER,
    beklenen  INTEGER,
    durum     TEXT,                   -- tam | eksik | NULL (beklenen bilinmiyor)
    aciklama  TEXT,
    ayrinti_json TEXT,
    PRIMARY KEY (secim_id, veri)
);

-- Sık kullanılan aramalar için indeksler (PK'lar zaten indeksli) -----------
CREATE INDEX ix_ilce_plaka        ON ilce(plaka);
CREATE INDEX ix_secim_ana         ON secim(ana_secim_id);
CREATE INDEX ix_secilen_secim     ON secilen(secim_id, plaka);
CREATE INDEX ix_secilen_ad        ON secilen(ad);
CREATE INDEX ix_sonuc_belde_secim ON sonuc_belde(secim_id, plaka);
CREATE INDEX ix_sonuc_ilce_plaka  ON sonuc_ilce(secim_id, plaka);
CREATE INDEX ix_sonuc_ilce_ilce   ON sonuc_ilce(ilce_id);
CREATE INDEX ix_oy_il_secenek     ON oy_il(secenek_id, secim_id);
CREATE INDEX ix_oy_ilce_secenek   ON oy_ilce(secenek_id, secim_id);
-- oy_mahalle(secenek_id) indeksi bilerek yok: dosyaya ~95 MB ekliyor, 2,4 milyon satırı
-- taramak ise SQLite'ta bir saniyenin altında. Gerekirse elle: CREATE INDEX ... ON oy_mahalle(secenek_id, secim_id);

-- Kolay sorgu için görünümler ---------------------------------------------
CREATE VIEW v_oy_il AS
SELECT s.secim_id, s.tur, s.oylama, s.yil, o.plaka, si.ad AS il, se.ad AS secenek, se.tip,
       o.oy, o.oran, (si.kazanan_id = o.secenek_id) AS kazandi
FROM oy_il o
JOIN secim s     ON s.secim_id = o.secim_id
JOIN sonuc_il si ON si.secim_id = o.secim_id AND si.plaka = o.plaka
JOIN secenek se  ON se.secenek_id = o.secenek_id;

CREATE VIEW v_oy_ilce AS
SELECT s.secim_id, s.tur, s.oylama, s.yil, sc.plaka, il.ad AS il, o.ilce_id, sc.ad AS ilce,
       se.ad AS secenek, se.tip, o.oy, o.oran, o.aday, (sc.kazanan_id = o.secenek_id) AS kazandi
FROM oy_ilce o
JOIN secim s       ON s.secim_id = o.secim_id
JOIN sonuc_ilce sc ON sc.secim_id = o.secim_id AND sc.ilce_id = o.ilce_id
JOIN il            ON il.plaka = sc.plaka
JOIN secenek se    ON se.secenek_id = o.secenek_id;

CREATE VIEW v_oy_mahalle AS
SELECT s.secim_id, s.tur, s.oylama, s.yil, i.plaka, il.ad AS il, o.ilce_id, i.ad AS ilce,
       o.mahalle_id, m.ad AS mahalle, se.ad AS secenek, o.oy, o.oran,
       (sm.kazanan_id = o.secenek_id) AS kazandi
FROM oy_mahalle o
JOIN secim s          ON s.secim_id = o.secim_id
JOIN sonuc_mahalle sm ON sm.secim_id = o.secim_id AND sm.ilce_id = o.ilce_id AND sm.mahalle_id = o.mahalle_id
JOIN mahalle m        ON m.ilce_id = o.ilce_id AND m.mahalle_id = o.mahalle_id
JOIN ilce i           ON i.ilce_id = o.ilce_id
JOIN il               ON il.plaka = i.plaka
JOIN secenek se       ON se.secenek_id = o.secenek_id;

CREATE VIEW v_secilen AS
SELECT s.secim_id, s.tur, s.yil, sl.gorev, sl.plaka, il.ad AS il, sl.bolge, sl.ad,
       se.ad AS parti, sl.parti_adi_kaynakta
FROM secilen sl
JOIN secim s ON s.secim_id = sl.secim_id
JOIN il      ON il.plaka = sl.plaka
LEFT JOIN secenek se ON se.secenek_id = sl.secenek_id;

CREATE VIEW v_oy_belde AS
SELECT s.secim_id, s.oylama, s.yil, b.plaka, il.ad AS il, b.ilce_ad, b.belde_ad, b.belde_kod,
       se.ad AS secenek, o.oy, (b.kazanan_id = o.secenek_id) AS kazandi, b.sadece_kazanan, b.kaynak
FROM oy_belde o
JOIN sonuc_belde b ON b.sonuc_belde_id = o.sonuc_belde_id
JOIN secim s       ON s.secim_id = b.secim_id
JOIN il            ON il.plaka = b.plaka
JOIN secenek se    ON se.secenek_id = o.secenek_id;
