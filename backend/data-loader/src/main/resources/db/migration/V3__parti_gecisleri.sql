-- Parti devamlılığı (onceki_parti_id). Yalnız kaynakla belgelenebilen ilişkiler girilir; yorum gerektiren
-- "devamı sayılır" ilişkileri (ör. kapatılan bir partinin yerine kurulan parti) burada bilerek YOK.
-- Yeni bir geçiş eklemek için bu dosyayı değiştirmeyin, yeni bir migration (V5__..., V6__...) yazın:
--   UPDATE parti SET onceki_parti_id = <önceki>, gecis_turu = 'ad_degisikligi' | 'halef' | 'birlesme',
--                    gecis_yili = <yıl>, gecis_kaynagi = '<kaynak>'
--   WHERE parti_id = <sonraki> AND ad = '<sonraki adı>';
--
-- Bilinen veri sınırı (veri DÜZELTİLMEDİ): kaynakta 'DP' anahtarı hem 1946-1960 Demokrat Parti'yi hem de
-- 2007'de Doğru Yol Partisi'nin aldığı Demokrat Parti adını taşıyor. Tek parti_id olduğu için DYP -> DP
-- geçişi girilmedi; girilseydi 1950'lerin DP sonuçları da DYP'nin devamı gibi görünürdü.

-- Yeşil Sol Parti, Ekim 2023'te Halkların Eşitlik ve Demokrasi Partisi (HEDEP) adını, Aralık 2023'te
-- 'DEM Parti' kısaltmasını aldı: aynı tüzel kişilik.
UPDATE parti
SET onceki_parti_id = 103,
    gecis_turu      = 'ad_degisikligi',
    gecis_yili      = 2023,
    gecis_kaynagi   = 'Yeşil Sol Parti -> HEDEP (Ekim 2023) -> DEM Parti (Aralık 2023), Yargıtay Cumhuriyet Başsavcılığı siyasi parti sicili'
WHERE parti_id = 107 AND ad = 'DEM Parti';
