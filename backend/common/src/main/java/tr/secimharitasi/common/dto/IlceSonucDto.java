package tr.secimharitasi.common.dto;

import java.math.BigDecimal;
import java.util.List;

/** Bir seçimde bir ilçenin sonucu. ad ve plaka o seçimdeki değerlerdir (ilçeler zamanla il/ad değiştirebilir). */
public record IlceSonucDto(String secimId, String ilceId, int plaka, String ad, Integer secmen, Integer oyKullanan,
                           Integer gecerliOy, Integer gecersizOy, Integer sandik, BigDecimal katilim, String kazanan,
                           String baskan, boolean sadeceKazanan, String not, List<OyDto> oylar) {
}
