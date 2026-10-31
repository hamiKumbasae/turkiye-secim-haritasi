package tr.secimharitasi.common;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.util.List;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.common.dto.IlSonucDto;
import tr.secimharitasi.common.dto.OyDto;
import tr.secimharitasi.common.dto.PartiDto;

class DtoJsonTest {

    private final ObjectMapper om = new ObjectMapper();

    @Test
    void ilSonucuJsonaVeGeriCevrilir() throws Exception {
        IlSonucDto il = new IlSonucDto("2023", 34, "İstanbul", 10, 9, 8, 1, 2, new BigDecimal("90.00"), "CHP", 98,
                null, List.of(new OyDto(5, "CHP", "CHP", 5L, new BigDecimal("62.50"))));
        String json = om.writeValueAsString(il);
        assertThat(om.readValue(json, IlSonucDto.class)).isEqualTo(il);
        JsonNode n = om.readTree(json);
        assertThat(n.get("oylar").get(0).get("oran").decimalValue()).isEqualByComparingTo("62.5");
    }

    @Test
    void partiTipleriKodOlarakYazilir() throws Exception {
        PartiDto p = new PartiDto(1, "DEM Parti", "DEM", SecenekTipi.PARTI, "#8b5cf6", 2, GecisTuru.AD_DEGISIKLIGI,
                2023, null, List.of());
        JsonNode n = om.readTree(om.writeValueAsString(p));
        assertThat(n.get("tip").asText()).isEqualTo("parti");
        assertThat(n.get("gecisTuru").asText()).isEqualTo("ad_degisikligi");
        assertThat(om.readValue(om.writeValueAsString(p), PartiDto.class)).isEqualTo(p);
    }
}
