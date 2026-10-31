package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.GeoJsonFeature;
import io.github.hamikumbasae.election.dto.GeoJsonFeatureCollection;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.SearchHitDto;
import io.github.hamikumbasae.election.service.GeoService;
import io.github.hamikumbasae.election.service.NotFoundException;
import io.github.hamikumbasae.election.service.SearchService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Map;

import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest({SearchController.class, GeoController.class})
class SearchAndGeoControllerTest {

    @Autowired
    MockMvc mvc;
    @MockitoBean
    SearchService search;
    @MockitoBean
    GeoService geo;

    @Test
    void searchReturnsAPage() throws Exception {
        when(search.search("ümraniye", Level.DISTRICT, null, 0, 20)).thenReturn(PageResponse.of(List.of(
                new SearchHitDto(Level.DISTRICT, 34, "Ümraniye", "TR-D-34-037", null, null, 2009, 2024,
                        List.of("2009yerel", "2024yerel"))), 0, 20, 1));

        mvc.perform(get("/api/v1/search").param("q", "ümraniye").param("level", "district"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].geomId").value("TR-D-34-037"))
                .andExpect(jsonPath("$.content[0].elections[1]").value("2024yerel"))
                .andExpect(jsonPath("$.totalElements").value(1));
    }

    @Test
    void searchValidatesQueryLength() throws Exception {
        mvc.perform(get("/api/v1/search").param("q", "a")).andExpect(status().isBadRequest());
        mvc.perform(get("/api/v1/search")).andExpect(status().isBadRequest());
        verifyNoInteractions(search);
    }

    @Test
    void geometryIsGeoJsonWithTheStoredGeometryEmbeddedVerbatim() throws Exception {
        String polygon = "{\"type\":\"Polygon\",\"coordinates\":[[[29.1,41.0],[29.2,41.0],[29.2,41.1],[29.1,41.0]]]}";
        when(geo.neighbourhood("TR-D-34-037", "tTR-Y-34-037-M-0001")).thenReturn(
                GeoJsonFeature.of("tTR-Y-34-037-M-0001", polygon, Map.of("name", "ADEM YAVUZ MAH.")));

        mvc.perform(get("/api/v1/geo/districts/TR-D-34-037/neighbourhoods/tTR-Y-34-037-M-0001"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith("application/geo+json"))
                .andExpect(header().string("Cache-Control", org.hamcrest.Matchers.containsString("max-age=3600")))
                .andExpect(jsonPath("$.type").value("Feature"))
                .andExpect(jsonPath("$.geometry.type").value("Polygon"))
                .andExpect(jsonPath("$.geometry.coordinates[0][0][0]").value(29.1))
                .andExpect(jsonPath("$.properties.name").value("ADEM YAVUZ MAH."));
    }

    @Test
    void featureCollectionCanBeRequestedAsPlainJson() throws Exception {
        when(geo.districtNeighbourhoods("TR-D-34-037", "2023")).thenReturn(GeoJsonFeatureCollection.of(List.of(
                GeoJsonFeature.of("a", null, Map.of("winner", "AK Parti")))));

        mvc.perform(get("/api/v1/geo/districts/TR-D-34-037/neighbourhoods").param("election", "2023")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.type").value("FeatureCollection"))
                .andExpect(jsonPath("$.features[0].geometry").value(org.hamcrest.Matchers.nullValue()))
                .andExpect(jsonPath("$.features[0].properties.winner").value("AK Parti"));
    }

    @Test
    void missingGeometryIs404ProblemDetail() throws Exception {
        when(geo.neighbourhood("TR-D-34-037", "nope")).thenThrow(new NotFoundException("No boundary"));

        mvc.perform(get("/api/v1/geo/districts/TR-D-34-037/neighbourhoods/nope"))
                .andExpect(status().isNotFound())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_PROBLEM_JSON));
    }
}
