package tr.secimharitasi.common.dto;

import java.math.BigDecimal;
import java.util.List;

/** Bir seçimde bir mahallenin/köyün (muhtarlık) sonucu, 2009-2024. katilim %100'ü aşabilir (YSK kaynaklı). */
public record MahalleSonucDto(String secimId, String ilceId, String mahalleId, String ad, Integer secmen,
                              Integer oyKullanan, Integer gecerliOy, Integer sandik, BigDecimal katilim,
                              String kazanan, List<OyDto> oylar) {
}
