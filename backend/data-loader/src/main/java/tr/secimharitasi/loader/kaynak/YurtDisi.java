package tr.secimharitasi.loader.kaynak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.Map;

/** Yurt dışı ve gümrük oyları (2015 sonrası). Kaynakta kazanan ve seçmen sayısı yok. */
@JsonIgnoreProperties(ignoreUnknown = true)
public record YurtDisi(Integer kullanilanOy, Integer gecerliOy, BigDecimal katilim, Map<String, OyKaydi> oy) {

    public YurtDisi {
        oy = oy == null ? Map.of() : new LinkedHashMap<>(oy);
    }
}
