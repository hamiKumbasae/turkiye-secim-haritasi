package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Election;
import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.dto.ElectionDto;
import io.github.hamikumbasae.election.repository.ElectionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class ElectionServiceTest {

    private ElectionService service;

    @BeforeEach
    void setUp() {
        ElectionRepository repository = mock(ElectionRepository.class);
        when(repository.findAll()).thenReturn(List.of(
                new Election(24, "2023", "genel", "14 Mayıs 2023", 2023, 600),
                new Election(3, "2023cb1tur", "cumhurbaskanligi", "14 Mayıs 2023 (1. Tur)", 2023, null),
                new Election(5, "1950", "genel", "14 Mayıs 1950", 1950, 487),
                new Election(46, "2024yerel", "yerel", "31 Mart 2024", 2024, null)));
        service = new ElectionService(new ElectionCatalog(repository));
    }

    @Test
    void listsChronologicallyWithParsedDates() {
        List<ElectionDto> all = service.list(null, null);
        assertThat(all).extracting(ElectionDto::code).containsExactly("1950", "2023", "2023cb1tur", "2024yerel");
        assertThat(all.getFirst().date()).isEqualTo(LocalDate.of(1950, 5, 14));
    }

    @Test
    void filtersByTypeAndYear() {
        assertThat(service.list(ElectionType.GENERAL, 2023)).extracting(ElectionDto::code).containsExactly("2023");
        assertThat(service.list(ElectionType.PRESIDENTIAL, null)).extracting(ElectionDto::code)
                .containsExactly("2023cb1tur");
        assertThat(service.list(null, 1999)).isEmpty();
    }

    @Test
    void resolvesCodesCaseInsensitively() {
        assertThat(service.require("2024YEREL").id()).isEqualTo(46);
        assertThat(service.get("2023").totalSeats()).isEqualTo(600);
    }

    @Test
    void unknownCodeIsNotFound() {
        assertThatThrownBy(() -> service.get("2031")).isInstanceOf(NotFoundException.class)
                .hasMessageContaining("2031");
    }
}
