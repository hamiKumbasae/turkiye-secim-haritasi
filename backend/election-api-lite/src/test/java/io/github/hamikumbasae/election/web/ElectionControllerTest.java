package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.dto.ElectionSummaryDto;
import io.github.hamikumbasae.election.dto.PartyResultDto;
import io.github.hamikumbasae.election.service.ElectionService;
import io.github.hamikumbasae.election.service.NotFoundException;
import io.github.hamikumbasae.election.service.ResultService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;

import static io.github.hamikumbasae.election.TestData.GENERAL_2023;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ElectionController.class)
class ElectionControllerTest {

    @Autowired
    MockMvc mvc;
    @MockitoBean
    ElectionService elections;
    @MockitoBean
    ResultService results;

    @Test
    void listsElectionsWithTypeFilterInEitherLanguage() throws Exception {
        when(elections.list(ElectionType.GENERAL, 2023)).thenReturn(List.of(GENERAL_2023));

        for (String type : List.of("general", "genel", "GENEL")) {
            mvc.perform(get("/api/v1/elections").param("type", type).param("year", "2023"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$[0].code").value("2023"))
                    .andExpect(jsonPath("$[0].type").value("general"))
                    .andExpect(jsonPath("$[0].date").value("2023-05-14"))
                    .andExpect(jsonPath("$[0].totalSeats").value(600));
        }
    }

    @Test
    void unknownTypeIsBadRequest() throws Exception {
        mvc.perform(get("/api/v1/elections").param("type", "mayoral"))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_PROBLEM_JSON));
    }

    @Test
    void yearOutOfRangeIsBadRequest() throws Exception {
        mvc.perform(get("/api/v1/elections").param("year", "1800"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400));
    }

    @Test
    void unknownElectionIsProblemDetail404() throws Exception {
        when(elections.get("2031")).thenThrow(new NotFoundException("Election '2031' not found."));

        mvc.perform(get("/api/v1/elections/2031"))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_PROBLEM_JSON))
                .andExpect(jsonPath("$.title").value("Not found"))
                .andExpect(jsonPath("$.detail").value("Election '2031' not found."))
                .andExpect(jsonPath("$.instance").value("/api/v1/elections/2031"));
    }

    @Test
    void summary() throws Exception {
        when(results.summary("2023")).thenReturn(new ElectionSummaryDto(GENERAL_2023, 64_190_652, 54_297_147,
                new BigDecimal("86.75"), 81, true,
                List.of(new PartyResultDto("AK Parti", 19_127_097, new BigDecimal("35.23"), 268, null))));

        mvc.perform(get("/api/v1/elections/2023/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.election.code").value("2023"))
                .andExpect(jsonPath("$.results[0].party").value("AK Parti"))
                .andExpect(jsonPath("$.results[0].share").value(35.23))
                .andExpect(jsonPath("$.results[0].candidate").doesNotExist());
    }

    @Test
    void databaseOutageIs503() throws Exception {
        when(results.summary("2023")).thenThrow(new DataAccessResourceFailureException("connection refused"));

        mvc.perform(get("/api/v1/elections/2023/summary"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.title").value("Database unavailable"));
    }

    @Test
    void corsAllowsTheGithubPagesSite() throws Exception {
        mvc.perform(options("/api/v1/elections")
                        .header("Origin", "https://hamikumbasae.github.io")
                        .header("Access-Control-Request-Method", "GET"))
                .andExpect(status().isOk())
                .andExpect(header().string("Access-Control-Allow-Origin", "https://hamikumbasae.github.io"));

        mvc.perform(options("/api/v1/elections")
                        .header("Origin", "https://evil.example")
                        .header("Access-Control-Request-Method", "GET"))
                .andExpect(status().isForbidden());
    }
}
