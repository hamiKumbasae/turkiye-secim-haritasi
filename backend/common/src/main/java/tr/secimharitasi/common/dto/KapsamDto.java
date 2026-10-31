package tr.secimharitasi.common.dto;

/**
 * Kaynakta ne kadar veri bulunduğu.
 *
 * @param veri  milletvekilleri, senatorler, beldeler, belediye_meclisi, il_genel_meclisi, yenileme_ara
 * @param durum tam | eksik | fazla | null (beklenen bilinmiyor)
 */
public record KapsamDto(String secimId, String veri, Integer bulunan, Integer beklenen, String durum,
                        String aciklama) {
}
