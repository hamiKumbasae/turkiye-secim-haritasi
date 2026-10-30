-- Ek veri (Flyway V4): meclis seçimleri, Senato, ara/yenileme seçimleri, mahalle sonuçları, beldeler,
-- seçilen milletvekili/senatörler, 2024 belediye meclisi üye dağılımı ve kaynak kapsamı.

-- secim: yeni türler ve oylama bilgisi --------------------------------------------------------------
-- tur    : seçimin türü (genel, yerel, referandum, cumhurbaskanligi, senato, ara)
-- oylama : o sandıkta neyin oylandığı. Aynı günün ikincil oylamaları ayrı secim satırıdır ve ana seçime
--          ana_secim_id ile bağlanır: '2024yerel_bm' (belediye meclisi) -> '2024yerel'.
ALTER TABLE secim DROP CHECK ck_secim_tur;
ALTER TABLE secim
    ADD CONSTRAINT ck_secim_tur CHECK (tur IN ('genel', 'yerel', 'referandum', 'cumhurbaskanligi', 'senato', 'ara')),
    ADD COLUMN oylama       VARCHAR(30)  NULL AFTER tur,
    ADD COLUMN ana_secim_id VARCHAR(40)  NULL AFTER oylama,
    ADD COLUMN aciklama     VARCHAR(1000) NULL AFTER tarih_metni;

UPDATE secim SET oylama = CASE tur
    WHEN 'genel' THEN 'milletvekili'
    WHEN 'yerel' THEN 'baskanlik'
    ELSE tur END;

ALTER TABLE secim
    MODIFY oylama VARCHAR(30) NOT NULL,
    ADD CONSTRAINT ck_secim_oylama CHECK (oylama IN ('milletvekili', 'baskanlik', 'belediye_meclisi',
        'il_genel_meclisi', 'referandum', 'cumhurbaskanligi', 'senato')),
    ADD CONSTRAINT fk_secim_ana FOREIGN KEY (ana_secim_id) REFERENCES secim (secim_id),
    ADD INDEX ix_secim_ana (ana_secim_id);

-- parti: aynı partinin kaynaklarda farklı yazılan adları (yalnız büyük/küçük harf farkı gibi) ------------
CREATE TABLE parti_takma_ad (
    ad       VARCHAR(120) NOT NULL,
    parti_id INT          NOT NULL,
    CONSTRAINT pk_parti_takma_ad PRIMARY KEY (ad),
    CONSTRAINT fk_parti_takma_ad_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- Mahalle / köy (muhtarlık), 2009-2024 ----------------------------------------------------------------
-- mahalle_id kaynak kimliğidir (r... OSM, k... TKGM, ...); ad geo/normalized/mahalle_geo.json'dan.
CREATE TABLE mahalle (
    ilce_id    VARCHAR(100) NOT NULL,
    mahalle_id VARCHAR(100) NOT NULL,
    ad         VARCHAR(150) NULL,
    CONSTRAINT pk_mahalle PRIMARY KEY (ilce_id, mahalle_id),
    CONSTRAINT fk_mahalle_ilce FOREIGN KEY (ilce_id) REFERENCES ilce (ilce_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE sonuc_mahalle (
    secim_id         VARCHAR(40)   NOT NULL,
    ilce_id          VARCHAR(100)  NOT NULL,
    mahalle_id       VARCHAR(100)  NOT NULL,
    secmen           INT           NULL,
    oy_kullanan      INT           NULL,
    gecerli_oy       INT           NULL,
    sandik           INT           NULL,
    katilim          DECIMAL(8, 2) NULL,
    kazanan_parti_id INT           NULL,
    CONSTRAINT pk_sonuc_mahalle PRIMARY KEY (secim_id, ilce_id, mahalle_id),
    CONSTRAINT fk_sonuc_mahalle_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id),
    CONSTRAINT fk_sonuc_mahalle_mahalle FOREIGN KEY (ilce_id, mahalle_id) REFERENCES mahalle (ilce_id, mahalle_id),
    CONSTRAINT fk_sonuc_mahalle_kazanan FOREIGN KEY (kazanan_parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE oy_mahalle (
    secim_id   VARCHAR(40)   NOT NULL,
    ilce_id    VARCHAR(100)  NOT NULL,
    mahalle_id VARCHAR(100)  NOT NULL,
    parti_id   INT           NOT NULL,
    oy         INT           NULL,
    oran       DECIMAL(6, 2) NULL,
    CONSTRAINT pk_oy_mahalle PRIMARY KEY (secim_id, ilce_id, mahalle_id, parti_id),
    CONSTRAINT fk_oy_mahalle_sonuc FOREIGN KEY (secim_id, ilce_id, mahalle_id)
        REFERENCES sonuc_mahalle (secim_id, ilce_id, mahalle_id),
    CONSTRAINT fk_oy_mahalle_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- İlçe başına meclis üyesi (2024 belediye meclisi) ---------------------------------------------------
CREATE TABLE sandalye_ilce (
    secim_id VARCHAR(40)  NOT NULL,
    ilce_id  VARCHAR(100) NOT NULL,
    parti_id INT          NOT NULL,
    sandalye INT          NOT NULL,
    CONSTRAINT pk_sandalye_ilce PRIMARY KEY (secim_id, ilce_id, parti_id),
    CONSTRAINT fk_sandalye_ilce_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id),
    CONSTRAINT fk_sandalye_ilce_ilce FOREIGN KEY (ilce_id) REFERENCES ilce (ilce_id),
    CONSTRAINT fk_sandalye_ilce_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- Seçilen milletvekilleri ve senatörler (Vikipedi; eksik olabilir, bkz. kaynak_kapsami) ---------------
CREATE TABLE secilen (
    secilen_id         INT          NOT NULL AUTO_INCREMENT,
    secim_id           VARCHAR(40)  NOT NULL,
    plaka              SMALLINT     NOT NULL,
    gorev              VARCHAR(20)  NOT NULL,
    ad                 VARCHAR(150) NOT NULL,
    parti_id           INT          NULL,
    parti_adi_kaynakta VARCHAR(150) NULL,
    bolge              VARCHAR(50)  NULL,
    kisi_link          VARCHAR(200) NULL,
    CONSTRAINT pk_secilen PRIMARY KEY (secilen_id),
    CONSTRAINT fk_secilen_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id),
    CONSTRAINT fk_secilen_il FOREIGN KEY (plaka) REFERENCES il (plaka),
    CONSTRAINT fk_secilen_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id),
    CONSTRAINT ck_secilen_gorev CHECK (gorev IN ('milletvekili', 'senator')),
    INDEX ix_secilen_secim (secim_id, plaka),
    INDEX ix_secilen_ad (ad)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- Belde belediyeleri. Kaynaklar arasında ortak belde kimliği yok (eski yıllar taranmış kitaptan okunan
-- adlar, 2009 sonrası meclis kayıtlarında yalnız YSK belde kodu): her satır bir seçimdeki bir beldedir.
CREATE TABLE sonuc_belde (
    sonuc_belde_id   INT          NOT NULL AUTO_INCREMENT,
    secim_id         VARCHAR(40)  NOT NULL,
    plaka            SMALLINT     NOT NULL,
    ilce_id          VARCHAR(100) NULL,
    ilce_ad          VARCHAR(100) NULL,
    belde_ad         VARCHAR(150) NULL,
    belde_kod        INT          NULL,
    secmen           INT          NULL,
    oy_kullanan      INT          NULL,
    gecerli_oy       INT          NULL,
    gecersiz_oy      INT          NULL,
    sandik           INT          NULL,
    katilim          DECIMAL(8, 2) NULL,
    kazanan_parti_id INT          NULL,
    aday             VARCHAR(400) NULL,
    sadece_kazanan   BOOLEAN      NOT NULL DEFAULT FALSE,
    kaynak           VARCHAR(20)  NOT NULL,
    kontrol          VARCHAR(40)  NULL,
    not_metni        TEXT         NULL,
    CONSTRAINT pk_sonuc_belde PRIMARY KEY (sonuc_belde_id),
    CONSTRAINT fk_sonuc_belde_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id),
    CONSTRAINT fk_sonuc_belde_il FOREIGN KEY (plaka) REFERENCES il (plaka),
    CONSTRAINT fk_sonuc_belde_ilce FOREIGN KEY (ilce_id) REFERENCES ilce (ilce_id),
    CONSTRAINT fk_sonuc_belde_kazanan FOREIGN KEY (kazanan_parti_id) REFERENCES parti (parti_id),
    CONSTRAINT ck_sonuc_belde_kaynak CHECK (kaynak IN ('wikipedia', 'tuik', 'ysk')),
    INDEX ix_sonuc_belde_secim (secim_id, plaka)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE oy_belde (
    sonuc_belde_id INT NOT NULL,
    parti_id       INT NOT NULL,
    oy             INT NULL,
    CONSTRAINT pk_oy_belde PRIMARY KEY (sonuc_belde_id, parti_id),
    CONSTRAINT fk_oy_belde_sonuc FOREIGN KEY (sonuc_belde_id) REFERENCES sonuc_belde (sonuc_belde_id),
    CONSTRAINT fk_oy_belde_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- Kaynakta ne kadar veri bulunduğu (eksikliği sorgulanabilir kılar) -----------------------------------
CREATE TABLE kaynak_kapsami (
    secim_id VARCHAR(40)  NOT NULL,
    veri     VARCHAR(40)  NOT NULL,
    bulunan  INT          NULL,
    beklenen INT          NULL,
    durum    VARCHAR(20)  NULL,
    aciklama VARCHAR(1000) NULL,
    CONSTRAINT pk_kaynak_kapsami PRIMARY KEY (secim_id, veri),
    CONSTRAINT fk_kaynak_kapsami_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- veri_yukleme özetine ek sayılar
-- kaynak_ozeti: yüklenen dosyaların SHA-256 özeti; değişmediyse sonraki açılışta yükleme atlanır.
ALTER TABLE veri_yukleme
    ADD COLUMN mahalle_satiri INT         NULL,
    ADD COLUMN belde_satiri   INT         NULL,
    ADD COLUMN secilen_sayisi INT         NULL,
    ADD COLUMN kaynak_ozeti   VARCHAR(64) NULL;
