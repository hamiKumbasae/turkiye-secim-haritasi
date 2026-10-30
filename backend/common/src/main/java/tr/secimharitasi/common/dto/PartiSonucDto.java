package tr.secimharitasi.common.dto;

import java.math.BigDecimal;
import tr.secimharitasi.common.SecimTuru;

/**
 * Bir partinin bir seçimdeki sonucu. plaka null ise Türkiye geneli (il satırlarının toplamı, yurt dışı hariç).
 * Zincirli sorguda partiId, o seçimde yarışan önceki partinin kimliğidir.
 */
public record PartiSonucDto(String secimId, SecimTuru tur, int yil, int partiId, String parti, Integer plaka,
                            String yer, Long oy, Long gecerliOy, BigDecimal oran) {
}
