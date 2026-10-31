package tr.secimharitasi.loader.ek;

import java.math.BigDecimal;
import java.util.Map;

/**
 * Bir seçimde bir belde. oy: seçenek adı -> oy (null olabilir); aynı seçeneğe düşen yazımlar yazarken toplanır.
 *
 * @param ilceId adından eşleşebildiyse ilçe birimi, yoksa null
 * @param kaynak wikipedia | tuik | ysk
 */
public record BeldeKaydi(String secimId, int plaka, String ilceId, String ilceAd, String beldeAd, Integer beldeKod,
                         Integer secmen, Integer oyKullanan, Integer gecerliOy, Integer gecersizOy, Integer sandik,
                         BigDecimal katilim, String kazanan, String aday, boolean sadeceKazanan, String kaynak,
                         String kontrol, String not, Map<String, Long> oy) {
}
