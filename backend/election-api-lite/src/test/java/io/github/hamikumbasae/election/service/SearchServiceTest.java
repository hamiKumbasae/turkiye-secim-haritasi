package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.SearchHitDto;
import io.github.hamikumbasae.election.repository.SearchRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;

import static io.github.hamikumbasae.election.TestData.E2002;
import static io.github.hamikumbasae.election.TestData.E2023;
import static io.github.hamikumbasae.election.TestData.E2024;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class SearchServiceTest {

    @Mock
    ElectionService elections;
    @Mock
    SearchRepository repository;
    @InjectMocks
    SearchService service;

    @Test
    void labelsNeighbourhoodHitsWithTheirDistrictAndSortsElections() {
        when(repository.search("ümraniye", null, null, 20, 0)).thenReturn(new SearchRepository.HitPage(List.of(
                new SearchRepository.Hit(Level.DISTRICT, 34, "Ümraniye", "TR-D-34-037", null, List.of(46, 24)),
                new SearchRepository.Hit(Level.NEIGHBOURHOOD, null, "ÜMRANİYE KÖYÜ", "k1", "TR-D-03-001", List.of(18))),
                2));
        when(repository.districtNames(List.of("TR-D-03-001")))
                .thenReturn(Map.of("TR-D-03-001", new SearchRepository.DistrictName("Başmakçı", 3)));
        when(elections.byId()).thenReturn(Map.of(24, E2023, 46, E2024, 18, E2002));

        PageResponse<SearchHitDto> page = service.search(" ümraniye ", null, null, 0, 20);

        assertThat(page.totalElements()).isEqualTo(2);
        SearchHitDto district = page.content().getFirst();
        assertThat(district.elections()).containsExactly("2023", "2024yerel");
        assertThat(district.firstYear()).isEqualTo(2023);
        assertThat(district.lastYear()).isEqualTo(2024);
        SearchHitDto village = page.content().get(1);
        assertThat(village.plateCode()).isEqualTo(3);
        assertThat(village.districtName()).isEqualTo("Başmakçı");
    }

    @Test
    void restrictsToOneElection() {
        when(elections.require("2023")).thenReturn(E2023);
        when(repository.search("kadıköy", Level.DISTRICT, 24, 5, 5)).thenReturn(new SearchRepository.HitPage(List.of(), 0));
        assertThat(service.search("kadıköy", Level.DISTRICT, "2023", 1, 5).content()).isEmpty();
    }

    @Test
    void tooShortQueryIsBadRequest() {
        assertThatThrownBy(() -> service.search(" a ", null, null, 0, 20)).isInstanceOf(BadRequestException.class);
        verifyNoInteractions(repository);
    }
}
