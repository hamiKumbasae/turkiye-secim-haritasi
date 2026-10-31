package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.PartyResultDto;
import io.github.hamikumbasae.election.dto.UnitResultDto;
import io.github.hamikumbasae.election.dto.UnitSummaryDto;
import io.github.hamikumbasae.election.service.NotFoundException;
import io.github.hamikumbasae.election.service.ResultService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;

import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ResultController.class)
class ResultControllerTest {

    @Autowired
    MockMvc mvc;
    @MockitoBean
    ResultService results;

    private static UnitResultDto istanbul() {
        return new UnitResultDto("2023", Level.PROVINCE, 34, "İstanbul", null, null, 11_367_598L, null,
                10_075_874L, 30_849, new BigDecimal("90.53"), "AK Parti", 98,
                List.of(new PartyResultDto("AK Parti", 3_570_227, new BigDecimal("35.43"), 40, null)));
    }

    @Test
    void provinceByPlate() throws Exception {
        when(results.province("2023", 34)).thenReturn(istanbul());

        mvc.perform(get("/api/v1/elections/2023/provinces/34"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.level").value("province"))
                .andExpect(jsonPath("$.name").value("İstanbul"))
                .andExpect(jsonPath("$.results[0].votes").value(3_570_227))
                .andExpect(jsonPath("$.results[0].share").value(35.43))
                .andExpect(jsonPath("$.geomId").doesNotExist());
    }

    @Test
    void plateOutsideOneToEightyOneIsBadRequest() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/provinces/82")).andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("plate: must be less than or equal to 81"));
        mvc.perform(get("/api/v1/elections/2023/provinces/0")).andExpect(status().isBadRequest());
        mvc.perform(get("/api/v1/elections/2023/provinces/abc")).andExpect(status().isBadRequest());
        verifyNoInteractions(results);
    }

    @Test
    void districtsOfAProvince() throws Exception {
        when(results.districts("2023", 34)).thenReturn(List.of(new UnitSummaryDto(Level.DISTRICT, 34, "Ümraniye",
                "TR-D-34-037", 534_091L, 479_616L, 1_445, new BigDecimal("91.45"), "AK Parti", null)));

        mvc.perform(get("/api/v1/elections/2023/provinces/34/districts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].geomId").value("TR-D-34-037"))
                .andExpect(jsonPath("$[0].seats").doesNotExist());
    }

    @Test
    void neighbourhoodPaging() throws Exception {
        when(results.neighbourhoods("2023", "TR-D-34-037", 1, 10))
                .thenReturn(PageResponse.of(List.of(), 1, 10, 36));

        mvc.perform(get("/api/v1/elections/2023/districts/TR-D-34-037/neighbourhoods")
                        .param("page", "1").param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(36))
                .andExpect(jsonPath("$.totalPages").value(4));
    }

    @Test
    void invalidPagingIsBadRequest() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/districts/TR-D-34-037/neighbourhoods").param("size", "501"))
                .andExpect(status().isBadRequest());
        mvc.perform(get("/api/v1/elections/2023/districts/TR-D-34-037/neighbourhoods").param("page", "-1"))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(results);
    }

    @Test
    void malformedGeomIdIsBadRequest() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/districts/{id}", "TR D 34;drop"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void notFoundIsPropagated() throws Exception {
        when(results.district(anyString(), anyString())).thenThrow(new NotFoundException("No result"));
        when(results.province(anyString(), anyInt())).thenThrow(new NotFoundException("No result"));

        mvc.perform(get("/api/v1/elections/1950/districts/TR-D-34-037")).andExpect(status().isNotFound());
        mvc.perform(get("/api/v1/elections/1950/provinces/81")).andExpect(status().isNotFound());
    }
}
