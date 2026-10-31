package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PartyHistoryDto;
import io.github.hamikumbasae.election.dto.PartyHistoryPointDto;
import io.github.hamikumbasae.election.dto.RankingEntryDto;
import io.github.hamikumbasae.election.service.AnalyticsService;
import io.github.hamikumbasae.election.service.AnalyticsService.Order;
import io.github.hamikumbasae.election.service.BadRequestException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AnalyticsController.class)
class AnalyticsControllerTest {

    @Autowired
    MockMvc mvc;
    @MockitoBean
    AnalyticsService analytics;

    @Test
    void partyHistoryForADistrict() throws Exception {
        when(analytics.partyHistory("AK Parti", 34, "Ümraniye", ElectionType.GENERAL, false)).thenReturn(
                new PartyHistoryDto("AK Parti", Level.DISTRICT, 34, "Ümraniye", List.of(
                        new PartyHistoryPointDto("2023", ElectionType.GENERAL, LocalDate.of(2023, 5, 14), 191_623,
                                new BigDecimal("39.95"), 1, "AK Parti", "TR-D-34-037"))));

        mvc.perform(get("/api/v1/history").param("party", "AK Parti").param("plate", "34")
                        .param("district", "Ümraniye").param("type", "genel"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.place").value("Ümraniye"))
                .andExpect(jsonPath("$.points[0].electionCode").value("2023"))
                .andExpect(jsonPath("$.points[0].share").value(39.95));
    }

    @Test
    void historyNeedsPartyAndPlate() throws Exception {
        mvc.perform(get("/api/v1/history").param("plate", "34")).andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value(org.hamcrest.Matchers.containsString("party")));
        mvc.perform(get("/api/v1/history").param("party", "CHP")).andExpect(status().isBadRequest());
        mvc.perform(get("/api/v1/history").param("party", " ").param("plate", "34")).andExpect(status().isBadRequest());
        verifyNoInteractions(analytics);
    }

    @Test
    void turnoutRankingDefaultsToTopTenDistricts() throws Exception {
        when(analytics.turnoutRanking("2023", Level.DISTRICT, null, null, Order.DESC, 0, 10)).thenReturn(List.of(
                new RankingEntryDto(1, Level.DISTRICT, 38, "Hacılar", "TR-D-38-005", new BigDecimal("95.43"), 9_545L,
                        "AK Parti")));

        mvc.perform(get("/api/v1/elections/2023/rankings/turnout"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name").value("Hacılar"))
                .andExpect(jsonPath("$[0].value").value(95.43));
    }

    @Test
    void partyRankingAcceptsTurkishLevelAndOrder() throws Exception {
        when(analytics.partyRanking(eq("2023"), eq("CHP"), eq(Level.DISTRICT), eq(35), isNull(), eq(Order.ASC),
                eq(1000L), eq(3))).thenReturn(List.of());

        mvc.perform(get("/api/v1/elections/2023/rankings/party").param("party", "CHP").param("level", "ilce")
                        .param("plate", "35").param("order", "asc").param("minVoters", "1000").param("limit", "3"))
                .andExpect(status().isOk());
    }

    @Test
    void rankingLimitIsCapped() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/rankings/turnout").param("limit", "101"))
                .andExpect(status().isBadRequest());
        mvc.perform(get("/api/v1/elections/2023/rankings/turnout").param("order", "sideways"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void serviceValidationErrorsAre400() throws Exception {
        when(analytics.turnoutRanking(any(), any(), any(), any(), any(), anyLong(), anyInt()))
                .thenThrow(new BadRequestException("Neighbourhood rankings need a district geometry id"));

        mvc.perform(get("/api/v1/elections/2023/rankings/turnout").param("level", "neighbourhood"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("Neighbourhood rankings need a district geometry id"));
    }
}
