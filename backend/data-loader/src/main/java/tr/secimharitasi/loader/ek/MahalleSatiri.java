package tr.secimharitasi.loader.ek;

import java.math.BigDecimal;
import java.util.Map;
import tr.secimharitasi.loader.kaynak.OyKaydi;

/** mahalle/&lt;secim&gt;.json içindeki bir mahalle/köy (muhtarlık) satırı. */
public record MahalleSatiri(String ilceId, String mahalleId, Integer secmen, Integer oyKullanan, Integer gecerliOy,
                            Integer sandik, BigDecimal katilim, String kazanan, Map<String, OyKaydi> oy) {
}
