-- election-api entegrasyon testi verisi. Partiler Flyway tohumundan: CHP=2, AK Parti=38, YEŞİL SOL=103, DEM Parti=107
INSERT INTO secim (secim_id, tur, yil, tarih_metni, toplam_sandalye, birincil_kaynak, kaynak_durumu) VALUES
('2018', 'genel', 2018, '24 Haziran 2018', 600, 'YSK', 'official'),
('2023', 'genel', 2023, '14 Mayıs 2023', 600, 'YSK', 'official'),
('2024yerel', 'yerel', 2024, '31 Mart 2024', NULL, 'YSK', 'official');

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
