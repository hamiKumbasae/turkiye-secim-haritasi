package tr.secimharitasi.common.dto;

import java.math.BigDecimal;
import java.util.List;

/**
 * Bir seçimde bir belde belediyesinin sonucu. Beldelerin kaynaklar arasında ortak kimliği yoktur.
 *
 * @param kaynak  wikipedia (yalnız kazanan), tuik (taranmış kitap), ysk
 * @param kontrol taranmış kitap satırının doğrulama sonucu: tutarli, tutarsiz, toplamTutmuyor ... (yoksa null)
 */
public record BeldeSonucDto(String secimId, int plaka, String ilceId, String ilceAd, String beldeAd, Integer beldeKod,
                            Integer secmen, Integer oyKullanan, Integer gecerliOy, BigDecimal katilim, String kazanan,
                            String aday, boolean sadeceKazanan, String kaynak, String kontrol, String not,
                            List<OyDto> oylar) {
}
