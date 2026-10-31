package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PartyHistoryDto;
import io.github.hamikumbasae.election.dto.RankingEntryDto;
import io.github.hamikumbasae.election.repository.AnalyticsRepository;
import io.github.hamikumbasae.election.repository.AnalyticsRepository.HistoryRow;
import io.github.hamikumbasae.election.repository.AnalyticsRepository.RankedUnit;
import io.github.hamikumbasae.election.repository.AnalyticsRepository.RankingScope;
import io.github.hamikumbasae.election.service.AnalyticsService.Order;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static io.github.hamikumbasae.election.TestData.ADEM_YAVUZ_2023;
import static io.github.hamikumbasae.election.TestData.E2002;
import static io.github.hamikumbasae.election.TestData.E2023;
import static io.github.hamikumbasae.election.TestData.E2024;
import static io.github.hamikumbasae.election.TestData.UMRANIYE_2023;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AnalyticsServiceTest {

    @Mock
    ElectionService elections;
    @Mock
    AnalyticsRepository repository;

    AnalyticsService service;

    @BeforeEach
    void setUp() {
        service = new AnalyticsService(elections, repository);
    }

    @Test
    void historyIsChronologicalAndDropsZeroVoteRows() {
        when(elections.byId()).thenReturn(Map.of(24, E2023, 46, E2024, 18, E2002, 5,
                new ElectionCatalog.Entry(5, new io.github.hamikumbasae.election.dto.ElectionDto("1991",
                        ElectionType.GENERAL, "20 Ekim 1991", 1991, java.time.LocalDate.of(1991, 10, 20), 450))));
        when(repository.partyHistory("AK Parti", 34, "Ümraniye", null)).thenReturn(List.of(
                new HistoryRow(46, "AK Parti", "Ümraniye", "TR-D-34-037", "AK Parti", 174_553, new BigDecimal("42.45"), 1),
                new HistoryRow(5, "AK Parti", "Ümraniye", "HIST-1", "ANAP", 0, new BigDecimal("0.00"), 9),
                new HistoryRow(18, "AK Parti", "Ümraniye", "HIST-2", "AK Parti", 140_135, new BigDecimal("44.56"), 1),
                new HistoryRow(24, "AK Parti", "Ümraniye", "TR-D-34-037", "AK Parti", 191_623, new BigDecimal("39.95"), 1)));

        PartyHistoryDto history = service.partyHistory(" AK Parti ", 34, "Ümraniye", null, false);

        assertThat(history.level()).isEqualTo(Level.DISTRICT);
        assertThat(history.place()).isEqualTo("Ümraniye");
        assertThat(history.points()).extracting("electionCode").containsExactly("2002", "2023", "2024yerel");
        assertThat(history.points().get(1).share()).isEqualByComparingTo("39.95");

        assertThat(service.partyHistory("AK Parti", 34, "Ümraniye", null, true).points()).hasSize(4);
    }

    @Test
    void historyUsesTheStoredPartySpelling() {
        when(elections.byId()).thenReturn(Map.of(24, E2023));
        when(repository.partyHistory("chp", 6, null, ElectionType.GENERAL)).thenReturn(List.of(
                new HistoryRow(24, "CHP", "Ankara", null, "CHP", 1_000, new BigDecimal("40.00"), 1)));

        PartyHistoryDto history = service.partyHistory("chp", 6, "  ", ElectionType.GENERAL, false);
        assertThat(history.party()).isEqualTo("CHP");
        assertThat(history.level()).isEqualTo(Level.PROVINCE);
    }

    @Test
    void historyWithoutVotesIsNotFound() {
        when(elections.byId()).thenReturn(Map.of());
        when(repository.partyHistory("XYZ", 34, null, null)).thenReturn(List.of());
        assertThatThrownBy(() -> service.partyHistory("XYZ", 34, null, null, false))
                .isInstanceOf(NotFoundException.class).hasMessageContaining("province 34");
    }

    @Test
    void turnoutRankingNumbersTheRows() {
        when(elections.require("2023")).thenReturn(E2023);
        RankingScope scope = new RankingScope(24, Level.DISTRICT, 34, null);
        when(repository.byTurnout(scope, true, 0, 2)).thenReturn(List.of(
                new RankedUnit(UMRANIYE_2023, new BigDecimal("91.45"), 534_091L),
                new RankedUnit(UMRANIYE_2023, new BigDecimal("90.00"), 1L)));

        List<RankingEntryDto> ranking = service.turnoutRanking("2023", Level.DISTRICT, 34, null, Order.DESC, 0, 2);

        assertThat(ranking).extracting(RankingEntryDto::rank).containsExactly(1, 2);
        assertThat(ranking.getFirst().geomId()).isEqualTo("TR-D-34-037");
    }

    @Test
    void neighbourhoodRankingIsScopedToADistrict() {
        when(elections.require("2023")).thenReturn(E2023);
        RankingScope scope = new RankingScope(24, Level.NEIGHBOURHOOD, null, "TR-D-34-037");
        when(repository.byPartyShare(scope, "CHP", false, 100, 5)).thenReturn(List.of(
                new RankedUnit(ADEM_YAVUZ_2023, new BigDecimal("16.00"), 1_750L)));

        List<RankingEntryDto> ranking = service.partyRanking("2023", "CHP", Level.NEIGHBOURHOOD, null,
                "TR-D-34-037", Order.ASC, 100, 5);
        assertThat(ranking.getFirst().plateCode()).isEqualTo(34);
    }

    @Test
    void invalidScopesAreRejectedBeforeTouchingTheDatabase() {
        assertThatThrownBy(() -> service.turnoutRanking("2023", Level.ABROAD, null, null, Order.DESC, 0, 10))
                .isInstanceOf(BadRequestException.class);
        assertThatThrownBy(() -> service.turnoutRanking("2023", Level.NEIGHBOURHOOD, null, null, Order.DESC, 0, 10))
                .isInstanceOf(BadRequestException.class).hasMessageContaining("district");
        assertThatThrownBy(() -> service.turnoutRanking("2023", Level.PROVINCE, 34, null, Order.DESC, 0, 10))
                .isInstanceOf(BadRequestException.class);
        verifyNoInteractions(repository);
    }

    @Test
    void unknownPartyInRankingIsNotFound() {
        when(elections.require("2023")).thenReturn(E2023);
        when(repository.byPartyShare(new RankingScope(24, Level.PROVINCE, null, null), "XYZ", true, 0, 10))
                .thenReturn(List.of());
        assertThatThrownBy(() -> service.partyRanking("2023", "XYZ", Level.PROVINCE, null, null, Order.DESC, 0, 10))
                .isInstanceOf(NotFoundException.class);
    }
}
