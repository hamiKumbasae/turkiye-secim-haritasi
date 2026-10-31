package tr.secimharitasi.common.dto;

import java.math.BigDecimal;

/** Bir seçeneğin (parti, aday, Evet/Hayır) bir yerdeki oyu. oy NULL olabilir: yalnız kazananı bilinen kayıtlar. */
public record OyDto(int partiId, String parti, String kisa, Long oy, BigDecimal oran) {
}
