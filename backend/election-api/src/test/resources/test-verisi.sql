-- election-api entegrasyon testi verisi. Partiler Flyway tohumundan: CHP=2, AK Parti=38, YEŞİL SOL=103, DEM Parti=107
INSERT INTO secim (secim_id, tur, oylama, ana_secim_id, yil, tarih_metni, toplam_sandalye, birincil_kaynak, kaynak_durumu) VALUES
('2018', 'genel', 'milletvekili', NULL, 2018, '24 Haziran 2018', 600, 'YSK', 'official'),
('2023', 'genel', 'milletvekili', NULL, 2023, '14 Mayıs 2023', 600, 'YSK', 'official'),
('2024yerel', 'yerel', 'baskanlik', NULL, 2024, '31 Mart 2024', NULL, 'YSK', 'official'),
('2024yerel_bm', 'yerel', 'belediye_meclisi', '2024yerel', 2024, '31 Mart 2024', NULL, NULL, NULL);

INSERT INTO il (plaka, ad) VALUES (0, 'Yurt Dışı'), (6, 'Ankara'), (34, 'İstanbul');

INSERT INTO ilce (ilce_id, plaka, ad, guncel, baslangic_yili, bitis_yili) VALUES
('TR-D-34-001', 34, 'Adalar', TRUE, 1961, NULL),
('TR-D-34-037', 34, 'Ümraniye', TRUE, 2009, NULL),
('HIST-Istanbul-Umraniye-fb42ce', 34, 'Ümraniye', FALSE, 1988, 1991);

INSERT INTO sonuc_il (secim_id, plaka, ad, secmen, gecerli_oy, katilim, kazanan_parti_id) VALUES
('2018', 34, 'İstanbul', 900, 800, 88.89, 38),
('2023', 0, 'Yurt Dışı', NULL, 100, 50.00, NULL),
('2023', 6, 'Ankara', 550, 500, 90.91, 38),
('2023', 34, 'İstanbul', 1100, 1000, 90.91, 2),
('2024yerel', 34, 'İstanbul', 1200, 1000, 83.33, 2);

INSERT INTO oy_il (secim_id, plaka, parti_id, oy, oran) VALUES
('2018', 34, 38, 500, 62.50), ('2018', 34, 2, 300, 37.50),
('2023', 0, 38, 60, 60.00), ('2023', 0, 2, 40, 40.00),
('2023', 6, 2, 200, 40.00), ('2023', 6, 38, 300, 60.00),
('2023', 34, 2, 450, 45.00), ('2023', 34, 38, 400, 40.00), ('2023', 34, 103, 150, 15.00),
('2024yerel', 34, 2, 510, 51.00), ('2024yerel', 34, 38, 390, 39.00), ('2024yerel', 34, 107, 100, 10.00);

INSERT INTO sonuc_ilce (secim_id, ilce_id, plaka, ad, gecerli_oy, kazanan_parti_id) VALUES
('2023', 'TR-D-34-001', 34, 'Adalar', 10, 2),
('2023', 'TR-D-34-037', 34, 'Ümraniye', 300, 38);

INSERT INTO oy_ilce (secim_id, ilce_id, parti_id, oy, oran) VALUES
('2023', 'TR-D-34-001', 2, 7, 70.00), ('2023', 'TR-D-34-001', 38, 3, 30.00),
('2023', 'TR-D-34-037', 38, 160, 53.33), ('2023', 'TR-D-34-037', 2, 140, 46.67);

-- Ek veri: mahalle, belde, seçilenler, sandalyeler, kapsam
INSERT INTO mahalle (ilce_id, mahalle_id, ad) VALUES
('TR-D-34-037', 'k1', 'FİNANSKENT MAH.'), ('TR-D-34-037', 'r2', NULL);

INSERT INTO sonuc_mahalle (secim_id, ilce_id, mahalle_id, secmen, gecerli_oy, katilim, kazanan_parti_id) VALUES
('2023', 'TR-D-34-037', 'k1', 100, 90, 92.00, 2),
('2023', 'TR-D-34-037', 'r2', 300, 280, 101.50, 38);

INSERT INTO oy_mahalle (secim_id, ilce_id, mahalle_id, parti_id, oy, oran) VALUES
('2023', 'TR-D-34-037', 'k1', 2, 50, 55.56), ('2023', 'TR-D-34-037', 'k1', 38, 40, 44.44),
('2023', 'TR-D-34-037', 'r2', 38, 200, 71.43), ('2023', 'TR-D-34-037', 'r2', 2, 80, 28.57);

INSERT INTO sonuc_belde (sonuc_belde_id, secim_id, plaka, ilce_id, ilce_ad, belde_ad, gecerli_oy, kazanan_parti_id,
                         aday, sadece_kazanan, kaynak, kontrol) VALUES
(1, '2024yerel', 34, 'TR-D-34-001', 'Adalar', 'Deneme Beldesi', 100, 2, 'Aday Bir', FALSE, 'ysk', NULL),
(2, '2024yerel', 6, NULL, 'Bilinmeyen', 'Öteki Belde', NULL, 38, NULL, TRUE, 'wikipedia', NULL);

INSERT INTO oy_belde (sonuc_belde_id, parti_id, oy) VALUES (1, 2, 60), (1, 38, 40), (2, 38, NULL);

INSERT INTO secilen (secim_id, plaka, gorev, ad, parti_id, parti_adi_kaynakta, bolge) VALUES
('2023', 34, 'milletvekili', 'Bir Vekil', 2, 'Cumhuriyet Halk Partisi', '1. bölge'),
('2023', 34, 'milletvekili', 'İki Vekil', NULL, NULL, '2. bölge'),
('2023', 6, 'milletvekili', 'Üç Vekil', 38, 'Adalet ve Kalkınma Partisi', NULL);

INSERT INTO kaynak_kapsami (secim_id, veri, bulunan, beklenen, durum, aciklama) VALUES
('2023', 'milletvekilleri', 3, 600, 'eksik', 'Test');

INSERT INTO sandalye_il (secim_id, plaka, parti_id, sandalye) VALUES ('2023', 34, 2, 50), ('2023', 34, 38, 48);
INSERT INTO sandalye_ilce (secim_id, ilce_id, parti_id, sandalye) VALUES
('2024yerel_bm', 'TR-D-34-037', 38, 25), ('2024yerel_bm', 'TR-D-34-037', 2, 20);
