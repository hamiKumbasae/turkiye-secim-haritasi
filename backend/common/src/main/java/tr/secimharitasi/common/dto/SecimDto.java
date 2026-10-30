package tr.secimharitasi.common.dto;

import tr.secimharitasi.common.OylamaTuru;
import tr.secimharitasi.common.SecimTuru;

/**
 * @param secimId        '2023', '2024yerel', '2024yerel_bm', '1961senato', '2019istanbul_bb_yenileme'
 * @param oylama         sandıkta neyin oylandığı (milletvekili, baskanlik, belediye_meclisi ...)
 * @param anaSecimId     ikincil oylamalarda bağlı olduğu ana seçim ('2024yerel_bm' -> '2024yerel'), yoksa null
 * @param tarih          kaynaktaki tarih metni, ör. '14 Mayıs 2023'
 * @param birincilKaynak sources.yml'deki birincil kaynak kurumu (YSK, TÜİK ...)
 */
public record SecimDto(String secimId, SecimTuru tur, OylamaTuru oylama, String anaSecimId, int yil, String tarih,
                       String aciklama, Integer toplamSandalye, String birincilKaynak, String kaynakDurumu) {
}
