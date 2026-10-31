package io.github.hamikumbasae.election.it;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cache.CacheManager;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.everyItem;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.lessThanOrEqualTo;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * End-to-end checks against the real database, asserting published figures (YSK, 2023 and 2024).
 * Skipped automatically when the database is not available.
 */
@EnabledIfDatabaseAvailable
@SpringBootTest
@AutoConfigureMockMvc
class ElectionApiIT {

    @Autowired
    MockMvc mvc;
    @Autowired
    CacheManager caches;

    @Test
    void catalogueHasAll46Elections() throws Exception {
        mvc.perform(get("/api/v1/elections"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(46)))
                .andExpect(jsonPath("$[0].code").value("1950"))
                .andExpect(jsonPath("$[45].code").value("2024yerel"));
        mvc.perform(get("/api/v1/elections").param("type", "presidential"))
                .andExpect(jsonPath("$[*].code").value(org.hamcrest.Matchers.contains("2014cb", "2018cb", "2023cb1tur", "2023cb2tur")));
    }

    @Test
    void istanbul2023GeneralElection() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/provinces/34"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("İstanbul"))
                .andExpect(jsonPath("$.registeredVoters").value(11_367_598))
                .andExpect(jsonPath("$.seats").value(98))
                .andExpect(jsonPath("$.results[0].party").value("AK Parti"))
                .andExpect(jsonPath("$.results[0].votes").value(3_570_227))
                .andExpect(jsonPath("$.results[0].share").value(35.43))
                .andExpect(jsonPath("$.results[0].seats").value(40))
                .andExpect(jsonPath("$.results[1].party").value("CHP"))
                .andExpect(jsonPath("$.results[1].votes").value(2_848_069));
    }

    @Test
    void nationalSummaryAddsProvincesAndAbroad() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.provinces").value(81))
                .andExpect(jsonPath("$.includesAbroad").value(true))
                // 18,385,465 in Türkiye + 741,632 abroad
                .andExpect(jsonPath("$.results[0].party").value("AK Parti"))
                .andExpect(jsonPath("$.results[0].votes").value(19_127_097))
                .andExpect(jsonPath("$.results[0].seats").value(268))
                .andExpect(jsonPath("$.results[1].party").value("CHP"));
        assertThat(caches.getCache("summaries").get("2023")).isNotNull();
    }

    @Test
    void referendumSummary() throws Exception {
        mvc.perform(get("/api/v1/elections/2017referandum/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.results[*].party").value(org.hamcrest.Matchers.containsInAnyOrder("Evet", "Hayır")));
    }

    @Test
    void umraniyeDistrictAndNeighbourhoods() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/provinces/34/districts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(39)))
                .andExpect(jsonPath("$[*].name", hasItem("Ümraniye")));

        mvc.perform(get("/api/v1/elections/2023/districts/TR-D-34-037"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Ümraniye"))
                .andExpect(jsonPath("$.results[0].votes").value(191_623))
                .andExpect(jsonPath("$.results[0].share").value(39.95));

        mvc.perform(get("/api/v1/elections/2023/districts/TR-D-34-037/neighbourhoods").param("size", "5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(5)))
                .andExpect(jsonPath("$.totalElements", greaterThan(30)))
                .andExpect(jsonPath("$.content[0].name").value("ADEM YAVUZ MAH."))
                .andExpect(jsonPath("$.content[0].plateCode").value(34))
                .andExpect(jsonPath("$.content[0].results[0].party").value("AK Parti"));
    }

    @Test
    void partyHistoryInUmraniyeAcrossDistrictReorganisations() throws Exception {
        mvc.perform(get("/api/v1/history").param("party", "ak parti").param("plate", "34")
                        .param("district", "UMRANIYE").param("type", "general"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.party").value("AK Parti"))
                .andExpect(jsonPath("$.place").value("Ümraniye"))
                .andExpect(jsonPath("$.points[0].electionCode").value("2002"))
                .andExpect(jsonPath("$.points[0].share").value(44.56))
                .andExpect(jsonPath("$.points[0].geomId").value("HIST-Istanbul-Umraniye-9208"))
                .andExpect(jsonPath("$.points[-1].electionCode").value("2023"))
                .andExpect(jsonPath("$.points[-1].votes").value(191_623))
                .andExpect(jsonPath("$.points[-1].geomId").value("TR-D-34-037"));
    }

    @Test
    void rankings() throws Exception {
        mvc.perform(get("/api/v1/elections/2023/rankings/party").param("party", "CHP").param("limit", "3"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].name").value("Kırklareli"))
                .andExpect(jsonPath("$[0].value").value(45.60))
                .andExpect(jsonPath("$[1].name").value("İzmir"));

        mvc.perform(get("/api/v1/elections/2023/rankings/turnout").param("level", "district").param("limit", "5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(5)))
                .andExpect(jsonPath("$[*].value", everyItem(lessThanOrEqualTo(100.0))))
                .andExpect(jsonPath("$[0].name").value("Hacılar"));

        mvc.perform(get("/api/v1/elections/2024yerel/rankings/turnout").param("level", "neighbourhood")
                        .param("district", "TR-D-34-037").param("order", "asc").param("minVoters", "1000"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[*].votes", everyItem(greaterThanOrEqualTo(1000))));
    }

    @Test
    void turkishCaseInsensitiveSearch() throws Exception {
        for (String q : new String[]{"ümraniye", "ÜMRANİYE", "Ümraniye", "umraniye", "UMRANIYE"}) {
            mvc.perform(get("/api/v1/search").param("q", q).param("level", "district"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content[0].geomId").value("TR-D-34-037"))
                    .andExpect(jsonPath("$.content[0].lastYear").value(2024));
        }
        // Dotted and dotless I (and other Turkish letters) are folded, so text typed on any keyboard works.
        for (String q : new String[]{"istanbul", "ISTANBUL", "İSTANBUL"}) {
            mvc.perform(get("/api/v1/search").param("q", q).param("level", "province"))
                    .andExpect(jsonPath("$.content[0].name").value("İstanbul"))
                    .andExpect(jsonPath("$.content[0].elections", hasSize(46)));
        }
        for (String q : new String[]{"isparta", "ISPARTA", "ısparta"}) {
            mvc.perform(get("/api/v1/search").param("q", q).param("level", "province"))
                    .andExpect(jsonPath("$.content[0].name").value("Isparta"));
        }
        mvc.perform(get("/api/v1/search").param("q", "çamlıca").param("level", "neighbourhood").param("size", "3"))
                .andExpect(jsonPath("$.content[0].districtName").exists())
                .andExpect(jsonPath("$.totalElements", greaterThan(10)));
    }

    @Test
    void neighbourhoodGeoJson() throws Exception {
        mvc.perform(get("/api/v1/geo/districts/TR-D-34-037/neighbourhoods").param("election", "2023"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith("application/geo+json"))
                .andExpect(jsonPath("$.type").value("FeatureCollection"))
                .andExpect(jsonPath("$.features.length()", greaterThan(30)))
                .andExpect(jsonPath("$.features[0].geometry.type").value("Polygon"))
                .andExpect(jsonPath("$.features[0].properties.winner").value("AK Parti"));

        mvc.perform(get("/api/v1/geo/districts/TR-D-34-037/neighbourhoods/tTR-Y-34-037-M-0002"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.properties.name").value("ALTINŞEHİR MAH."));
    }

    @Test
    void errorsAndHealth() throws Exception {
        mvc.perform(get("/api/v1/elections/1999/abroad")).andExpect(status().isNotFound())
                .andExpect(jsonPath("$.detail", containsString("abroad")));
        mvc.perform(get("/api/v1/elections/2031/summary")).andExpect(status().isNotFound());
        mvc.perform(get("/api/v1/elections/2023/abroad")).andExpect(status().isOk())
                .andExpect(jsonPath("$.results[0].votes").value(741_632));
        mvc.perform(get("/actuator/health")).andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.components.db.status").value("UP"));
        mvc.perform(get("/v3/api-docs")).andExpect(status().isOk())
                .andExpect(jsonPath("$.info.title").value("Türkiye Election API"));
    }
}
