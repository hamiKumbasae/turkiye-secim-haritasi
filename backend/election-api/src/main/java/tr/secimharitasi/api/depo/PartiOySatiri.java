package tr.secimharitasi.api.depo;

import java.math.BigDecimal;

/**
 * Bir partinin bir seçimde bir ildeki (ya da plaka null ise yurt içi toplam) oyu.
 * gecerliOy il satırının geçerli oyudur; Türkiye toplamında servis ayrıca hesaplar.
 */
public record PartiOySatiri(String secimId, String tur, Integer yil, Integer partiId, Integer plaka, String yer,
                            Long oy, Long gecerliOy, BigDecimal oran) {
}
