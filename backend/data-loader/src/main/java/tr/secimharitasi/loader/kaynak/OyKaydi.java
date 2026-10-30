package tr.secimharitasi.loader.kaynak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.math.BigDecimal;

/** Kaynak JSON'da bir seçeneğin oyu: {"oy": 123, "oran": 45.6, "aday": "..."}. oy ve oran null olabilir. */
@JsonIgnoreProperties(ignoreUnknown = true)
public record OyKaydi(Long oy, BigDecimal oran, String aday) {
}
