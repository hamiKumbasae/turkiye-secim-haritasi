package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Election;
import io.github.hamikumbasae.election.dto.ElectionDto;
import io.github.hamikumbasae.election.repository.ElectionRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;

/**
 * The 46 elections are tiny and static, so the whole table is cached as one entry and every
 * lookup by code is served from memory.
 */
@Component
public class ElectionCatalog {

    /** Election plus its database id (which never leaves the service layer). */
    public record Entry(int id, ElectionDto dto) {
    }

    private final ElectionRepository repository;

    public ElectionCatalog(ElectionRepository repository) {
        this.repository = repository;
    }

    @Cacheable("elections")
    public List<Entry> all() {
        return repository.findAll().stream()
                .map(ElectionCatalog::toEntry)
                .sorted(Comparator.comparing((Entry e) -> e.dto().date(), Comparator.nullsLast(LocalDate::compareTo))
                        .thenComparing(e -> e.dto().code()))
                .toList();
    }

    static Entry toEntry(Election e) {
        LocalDate date = ElectionDates.parse(e.getName());
        Integer year = e.getYear() != null ? e.getYear() : date != null ? date.getYear() : null;
        return new Entry(e.getId(), new ElectionDto(e.getCode(), e.getType(), e.getName(), year, date,
                e.getTotalSeats()));
    }
}
