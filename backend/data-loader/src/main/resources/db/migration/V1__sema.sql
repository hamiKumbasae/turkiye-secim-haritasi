-- Türkiye Seçim Haritası — MySQL 8 şeması (Flyway V1)
-- Şemanın sahibi data-loader'dır; election-api yalnız okur (spring.jpa.hibernate.ddl-auto=validate).
-- Metin sütunları utf8mb4_0900_as_cs: büyük/küçük harf ve aksan duyarlı, böylece kaynaktaki
-- 'YENİDEN REFAH' ile 'Yeniden Refah' gibi farklı anahtarlar çakışmaz.

CREATE TABLE secim (
    secim_id         VARCHAR(40)  NOT NULL,
    tur              VARCHAR(20)  NOT NULL,
    yil              SMALLINT     NOT NULL,
    tarih_metni      VARCHAR(100) NOT NULL,
    yarisma_turu     VARCHAR(40)  NULL,
    sonuc_temeli     VARCHAR(40)  NULL,
    toplam_sandalye  INT          NULL,
    birincil_kaynak  VARCHAR(100) NULL,
    kaynak_durumu    VARCHAR(20)  NULL,
    CONSTRAINT pk_secim PRIMARY KEY (secim_id),
    CONSTRAINT ck_secim_tur CHECK (tur IN ('genel', 'yerel', 'referandum', 'cumhurbaskanligi')),
    INDEX ix_secim_tur_yil (tur, yil)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- plaka 0 = yurt dışı ve gümrük oyları
CREATE TABLE il (
    plaka SMALLINT    NOT NULL,
    ad    VARCHAR(60) NOT NULL,
    CONSTRAINT pk_il PRIMARY KEY (plaka)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- İlçe birimi: güncel ilçeler 'TR-D-<plaka>-<no>', tarihsel birimler 'HIST...'.
-- baslangic_yili/bitis_yili: birimin veride göründüğü ilk/son seçim yılı. bitis_yili NULL = bugün de var.
-- (Kuruluş/kapanış tarihi değildir; veri 1950'de başladığı için daha eski ilçeler 1950/1961 görünür.)
CREATE TABLE ilce (
    ilce_id        VARCHAR(100) NOT NULL,
    plaka          SMALLINT     NOT NULL,
    ad             VARCHAR(100) NOT NULL,
    guncel         BOOLEAN      NOT NULL,
    baslangic_yili SMALLINT     NOT NULL,
    bitis_yili     SMALLINT     NULL,
    CONSTRAINT pk_ilce PRIMARY KEY (ilce_id),
    CONSTRAINT fk_ilce_il FOREIGN KEY (plaka) REFERENCES il (plaka),
    CONSTRAINT ck_ilce_yil CHECK (bitis_yili IS NULL OR bitis_yili >= baslangic_yili),
    INDEX ix_ilce_plaka (plaka, baslangic_yili, bitis_yili)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- Parti ve öteki oy seçenekleri (aday, Evet/Hayır, Diğer/Bağımsız). parti_id SABİTTİR:
-- V2 tohumunda elle verilir, yeniden yüklemede değişmez. Ad değişikliği / halef / birleşme
-- onceki_parti_id ile bağlanır (V3).
CREATE TABLE parti (
    parti_id        INT          NOT NULL,
    ad              VARCHAR(120) NOT NULL,
    kisa            VARCHAR(40)  NULL,
    tip             VARCHAR(20)  NOT NULL,
    renk            VARCHAR(9)   NULL,
    onceki_parti_id INT          NULL,
    gecis_turu      VARCHAR(20)  NULL,
    gecis_yili      SMALLINT     NULL,
    gecis_kaynagi   VARCHAR(500) NULL,
    CONSTRAINT pk_parti PRIMARY KEY (parti_id),
    CONSTRAINT uq_parti_ad UNIQUE (ad),
    CONSTRAINT fk_parti_onceki FOREIGN KEY (onceki_parti_id) REFERENCES parti (parti_id),
    CONSTRAINT ck_parti_tip CHECK (tip IN ('parti', 'aday', 'referandum', 'diger')),
    CONSTRAINT ck_parti_gecis CHECK (
        (onceki_parti_id IS NULL AND gecis_turu IS NULL)
        OR (onceki_parti_id IS NOT NULL AND gecis_turu IS NOT NULL
            AND gecis_turu IN ('ad_degisikligi', 'halef', 'birlesme'))),
    CONSTRAINT ck_parti_kendisi CHECK (onceki_parti_id IS NULL OR onceki_parti_id <> parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE sonuc_il (
    secim_id         VARCHAR(40)  NOT NULL,
    plaka            SMALLINT     NOT NULL,
    ad               VARCHAR(60)  NOT NULL,
    secmen           INT          NULL,
    oy_kullanan      INT          NULL,
    gecerli_oy       INT          NULL,
    gecersiz_oy      INT          NULL,
    sandik           INT          NULL,
    katilim          DECIMAL(7, 2) NULL,
    kazanan_parti_id INT          NULL,
    toplam_vekil     INT          NULL,
    not_metni        TEXT         NULL,
    CONSTRAINT pk_sonuc_il PRIMARY KEY (secim_id, plaka),
    CONSTRAINT fk_sonuc_il_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id),
    CONSTRAINT fk_sonuc_il_il FOREIGN KEY (plaka) REFERENCES il (plaka),
    CONSTRAINT fk_sonuc_il_kazanan FOREIGN KEY (kazanan_parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE oy_il (
    secim_id VARCHAR(40)   NOT NULL,
    plaka    SMALLINT      NOT NULL,
    parti_id INT           NOT NULL,
    oy       INT           NULL,
    oran     DECIMAL(6, 2) NULL,
    CONSTRAINT pk_oy_il PRIMARY KEY (secim_id, plaka, parti_id),
    CONSTRAINT fk_oy_il_sonuc FOREIGN KEY (secim_id, plaka) REFERENCES sonuc_il (secim_id, plaka),
    CONSTRAINT fk_oy_il_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id),
    INDEX ix_oy_il_parti (parti_id, secim_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE sandalye_il (
    secim_id VARCHAR(40) NOT NULL,
    plaka    SMALLINT    NOT NULL,
    parti_id INT         NOT NULL,
    sandalye INT         NOT NULL,
    CONSTRAINT pk_sandalye_il PRIMARY KEY (secim_id, plaka, parti_id),
    CONSTRAINT fk_sandalye_il_sonuc FOREIGN KEY (secim_id, plaka) REFERENCES sonuc_il (secim_id, plaka),
    CONSTRAINT fk_sandalye_il_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE sonuc_ilce (
    secim_id          VARCHAR(40)  NOT NULL,
    ilce_id           VARCHAR(100) NOT NULL,
    plaka             SMALLINT     NOT NULL,
    ad                VARCHAR(100) NOT NULL,
    secmen            INT          NULL,
    oy_kullanan       INT          NULL,
    gecerli_oy        INT          NULL,
    gecersiz_oy       INT          NULL,
    sandik            INT          NULL,
    katilim           DECIMAL(7, 2) NULL,
    kazanan_parti_id  INT          NULL,
    baskan            VARCHAR(200) NULL,
    sadece_kazanan    BOOLEAN      NOT NULL DEFAULT FALSE,
    not_metni         TEXT         NULL,
    CONSTRAINT pk_sonuc_ilce PRIMARY KEY (secim_id, ilce_id),
    CONSTRAINT fk_sonuc_ilce_secim FOREIGN KEY (secim_id) REFERENCES secim (secim_id),
    CONSTRAINT fk_sonuc_ilce_ilce FOREIGN KEY (ilce_id) REFERENCES ilce (ilce_id),
    CONSTRAINT fk_sonuc_ilce_il FOREIGN KEY (plaka) REFERENCES il (plaka),
    CONSTRAINT fk_sonuc_ilce_kazanan FOREIGN KEY (kazanan_parti_id) REFERENCES parti (parti_id),
    INDEX ix_sonuc_ilce_plaka (secim_id, plaka),
    INDEX ix_sonuc_ilce_ilce (ilce_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

CREATE TABLE oy_ilce (
    secim_id VARCHAR(40)   NOT NULL,
    ilce_id  VARCHAR(100)  NOT NULL,
    parti_id INT           NOT NULL,
    oy       INT           NULL,
    oran     DECIMAL(6, 2) NULL,
    aday     VARCHAR(400)  NULL,          -- kaynakta bazen açıklama metniyle birlikte (169 karaktere kadar)
    CONSTRAINT pk_oy_ilce PRIMARY KEY (secim_id, ilce_id, parti_id),
    CONSTRAINT fk_oy_ilce_sonuc FOREIGN KEY (secim_id, ilce_id) REFERENCES sonuc_ilce (secim_id, ilce_id),
    CONSTRAINT fk_oy_ilce_parti FOREIGN KEY (parti_id) REFERENCES parti (parti_id),
    INDEX ix_oy_ilce_parti (parti_id, secim_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;

-- Her yükleme çalışmasının özeti (tutarlılık bulgularının ayrıntısı log dosyasında)
CREATE TABLE veri_yukleme (
    yukleme_id      BIGINT       NOT NULL AUTO_INCREMENT,
    baslangic       DATETIME(3)  NOT NULL,
    bitis           DATETIME(3)  NULL,
    durum           VARCHAR(20)  NOT NULL,
    secim_sayisi    INT          NULL,
    il_satiri       INT          NULL,
    ilce_satiri     INT          NULL,
    oy_satiri       INT          NULL,
    bulgu_sayisi    INT          NULL,
    atlanan_satir   INT          NULL,
    CONSTRAINT pk_veri_yukleme PRIMARY KEY (yukleme_id)
) DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_as_cs;
