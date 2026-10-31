package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.dto.ElectionDto;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class ElectionService {

    private final ElectionCatalog catalog;

    public ElectionService(ElectionCatalog catalog) {
        this.catalog = catalog;
    }

    /** Elections in chronological order, optionally filtered. */
    public List<ElectionDto> list(ElectionType type, Integer year) {
        return catalog.all().stream()
                .map(ElectionCatalog.Entry::dto)
                .filter(e -> type == null || e.type() == type)
                .filter(e -> year == null || Objects.equals(e.year(), year))
                .toList();
    }

    public ElectionDto get(String code) {
        return require(code).dto();
    }

    /** Resolves an election code ("2023", "2024yerel", ...) case-insensitively or throws 404. */
    public ElectionCatalog.Entry require(String code) {
        return catalog.all().stream()
                .filter(e -> e.dto().code().equalsIgnoreCase(code))
                .findFirst()
                .orElseThrow(() -> new NotFoundException("Election '" + code + "' not found. "
                        + "See GET /api/v1/elections for valid codes."));
    }

    public Map<Integer, ElectionCatalog.Entry> byId() {
        return catalog.all().stream().collect(Collectors.toMap(ElectionCatalog.Entry::id, Function.identity()));
    }
}
