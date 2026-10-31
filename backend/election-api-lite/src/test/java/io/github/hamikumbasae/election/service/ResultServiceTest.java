package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.ElectionSummaryDto;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.UnitResultDto;
import io.github.hamikumbasae.election.repository.ResultRepository;
import io.github.hamikumbasae.election.repository.ResultRepository.UnitFilter;
import io.github.hamikumbasae.election.repository.VoteRow;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static io.github.hamikumbasae.election.TestData.ADEM_YAVUZ_2023;
import static io.github.hamikumbasae.election.TestData.E2023;
import static io.github.hamikumbasae.election.TestData.ISTANBUL_2023;
import static io.github.hamikumbasae.election.TestData.UMRANIYE_2023;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ResultServiceTest {

    @Mock
    ElectionService elections;
    @Mock
    ResultRepository repository;

    ResultService service;

    @BeforeEach
    void setUp() {
        service = new ResultService(elections, repository);
        when(elections.require("2023")).thenReturn(E2023);
    }

    @Test
    void summarySharesAreRelativeToAllPartyVotes() {
        when(repository.nationalTotals(24)).thenReturn(
                new ResultRepository.NationalTotals(1_000L, 900L, new BigDecimal("86.75"), 81, true));
        when(repository.nationalPartyTotals(24)).thenReturn(List.of(
                new VoteRow(0, "AK Parti", 600, null, 268, null),
                new VoteRow(0, "CHP", 300, null, 169, null),
                new VoteRow(0, "Diğer", 100, null, null, null)));

        ElectionSummaryDto summary = service.summary("2023");

        assertThat(summary.results()).extracting(r -> r.share().toPlainString())
                .containsExactly("60.00", "30.00", "10.00");
        assertThat(summary.results().getFirst().seats()).isEqualTo(268);
        assertThat(summary.validVotes()).isEqualTo(900);
        assertThat(summary.provinces()).isEqualTo(81);
        assertThat(summary.includesAbroad()).isTrue();
    }

    @Test
    void summaryFallsBackToVoteSumWhenValidVotesAreMissing() {
        when(repository.nationalTotals(24)).thenReturn(new ResultRepository.NationalTotals(0, 0, null, 63, false));
        when(repository.nationalPartyTotals(24)).thenReturn(List.of(new VoteRow(0, "DP", 3, null, null, null)));

        assertThat(service.summary("2023").validVotes()).isEqualTo(3);
    }

    @Test
    void provinceResultCarriesPartiesInRepositoryOrder() {
        when(repository.findUnit(new UnitFilter(24, Level.PROVINCE, 34, null, null)))
                .thenReturn(Optional.of(ISTANBUL_2023));
        when(repository.findVotes(List.of(18590))).thenReturn(Map.of(18590, List.of(
                new VoteRow(18590, "AK Parti", 3_570_227, new BigDecimal("35.43"), 40, null),
                new VoteRow(18590, "CHP", 2_848_069, new BigDecimal("28.27"), 31, null))));

        UnitResultDto result = service.province("2023", 34);

        assertThat(result.name()).isEqualTo("İstanbul");
        assertThat(result.seats()).isEqualTo(98);
        assertThat(result.results()).extracting("party").containsExactly("AK Parti", "CHP");
        assertThat(result.results().getFirst().votes()).isEqualTo(3_570_227);
    }

    @Test
    void missingProvinceIsNotFound() {
        when(repository.findUnit(any())).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.province("2023", 81)).isInstanceOf(NotFoundException.class)
                .hasMessageContaining("province 81");
    }

    @Test
    void districtSeatsAreHidden() {
        when(repository.findUnit(new UnitFilter(24, Level.DISTRICT, null, "TR-D-34-037", null)))
                .thenReturn(Optional.of(UMRANIYE_2023));
        when(repository.findVotes(List.of(19094))).thenReturn(Map.of());

        UnitResultDto result = service.district("2023", "TR-D-34-037");
        assertThat(result.seats()).isNull();
        assertThat(result.results()).isEmpty();
    }

    @Test
    void neighbourhoodsArePagedAndInheritThePlateFromTheDistrictId() {
        UnitFilter filter = new UnitFilter(24, Level.NEIGHBOURHOOD, null, null, "TR-D-34-037");
        when(repository.countUnits(filter)).thenReturn(36L);
        when(repository.findUnits(filter, 10, 20L)).thenReturn(List.of(ADEM_YAVUZ_2023));
        when(repository.findVotes(List.of(500_000))).thenReturn(Map.of(500_000, List.of(
                new VoteRow(500_000, "AK Parti", 5483, new BigDecimal("50.14"), null, null))));

        PageResponse<UnitResultDto> page = service.neighbourhoods("2023", "TR-D-34-037", 2, 10);

        assertThat(page.totalElements()).isEqualTo(36);
        assertThat(page.totalPages()).isEqualTo(4);
        assertThat(page.content().getFirst().plateCode()).isEqualTo(34);
        assertThat(page.content().getFirst().results()).hasSize(1);
    }

    @Test
    void districtWithoutNeighbourhoodDataIsNotFound() {
        when(repository.countUnits(any())).thenReturn(0L);
        assertThatThrownBy(() -> service.neighbourhoods("2023", "HIST-X", 0, 50))
                .isInstanceOf(NotFoundException.class).hasMessageContaining("2009");
    }

    @Test
    void abroadMissingIsNotFound() {
        when(repository.findUnit(eq(new UnitFilter(24, Level.ABROAD, null, null, null)))).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.abroad("2023")).isInstanceOf(NotFoundException.class);
    }
}
