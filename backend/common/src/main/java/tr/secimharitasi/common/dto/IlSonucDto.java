package tr.secimharitasi.common.dto;

import java.math.BigDecimal;
import java.util.List;

/** Bir seçimde bir ilin sonucu. plaka 0 = yurt dışı ve gümrük oyları. */
public record IlSonucDto(String secimId, int plaka, String ad, Integer secmen, Integer oyKullanan, Integer gecerliOy,
                         Integer gecersizOy, Integer sandik, BigDecimal katilim, String kazanan, Integer toplamVekil,
                         String not, List<OyDto> oylar) {
}
