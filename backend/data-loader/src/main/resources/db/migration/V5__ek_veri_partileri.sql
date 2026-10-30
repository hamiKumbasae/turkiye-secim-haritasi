-- Yeni seçenek adları (backend/tools/parti_tohumu.py --eksikler)
INSERT INTO parti (parti_id, ad, kisa, tip, renk) VALUES
(111, 'BAYRAK PARTISI', NULL, 'parti', NULL),
(112, 'BUYUK ANADOLU PARTISI', NULL, 'parti', NULL),
(113, 'BUYUK VATAN PARTISI', NULL, 'parti', NULL),
(114, 'HUR DEMOKRAT PARTI', NULL, 'parti', NULL),
(115, 'VATANDAS PARTISI', NULL, 'parti', NULL),
(116, 'A PARTİ', NULL, 'parti', NULL),
(117, 'MS.PARTİ', NULL, 'parti', NULL),
(118, 'YMP', NULL, 'parti', NULL);

-- Yalnız büyük/küçük harfi farklı yazımlar: aynı parti
INSERT INTO parti_takma_ad (ad, parti_id) VALUES
('Yeniden Refah', 102);
