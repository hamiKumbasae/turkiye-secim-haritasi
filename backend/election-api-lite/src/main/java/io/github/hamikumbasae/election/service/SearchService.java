package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.SearchHitDto;
import io.github.hamikumbasae.election.repository.SearchRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import io.github.hamikumbasae.election.dto.ElectionDto;

import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;

@Service
public class SearchService {

    private final ElectionService elections;
    private final SearchRepository repository;

    public SearchService(ElectionService elections, SearchRepository repository) {
        this.elections = elections;
        this.repository = repository;
    }

    /**
     * Finds provinces, districts and neighbourhoods whose name contains {@code query}, ignoring case and
     * Turkish letters ("ISTANBUL", "istanbul" and "İstanbul" are the same, as are "umraniye" and "Ümraniye").
     * One hit per distinct place (level, name, geometry id); exact and prefix matches come first.
     */
    @Cacheable(cacheNames = "search",
            key = "{#query.trim(), #level, #electionCode, #page, #size}")
    public PageResponse<SearchHitDto> search(String query, Level level, String electionCode, int page, int size) {
        String q = query.trim();
        if (q.length() < 2) {
            throw new BadRequestException("Query must be at least 2 characters");
        }
        Integer electionId = electionCode == null ? null : elections.require(electionCode).id();
        SearchRepository.HitPage result = repository.search(q, level, electionId, size, (long) page * size);
        Map<String, SearchRepository.DistrictName> districts = repository.districtNames(result.hits().stream()
                .map(SearchRepository.Hit::parentGeomId).filter(Objects::nonNull).distinct().toList());
        Map<Integer, ElectionCatalog.Entry> byId = elections.byId();
        List<SearchHitDto> content = result.hits().stream().map(h -> {
            SearchRepository.DistrictName d = h.parentGeomId() == null ? null : districts.get(h.parentGeomId());
            Integer plate = h.plateCode() != null ? h.plateCode() : d == null ? null : d.plateCode();
            List<ElectionDto> found = h.electionIds().stream().map(byId::get).filter(Objects::nonNull)
                    .map(ElectionCatalog.Entry::dto)
                    .sorted(Comparator.comparing(ElectionDto::date, Comparator.nullsLast(LocalDate::compareTo)))
                    .toList();
            return new SearchHitDto(h.level(), plate, h.name(), h.geomId(), h.parentGeomId(),
                    d == null ? null : d.name(),
                    found.isEmpty() ? null : found.getFirst().year(),
                    found.isEmpty() ? null : found.getLast().year(),
                    found.stream().map(ElectionDto::code).toList());
        }).toList();
        return PageResponse.of(content, page, size, result.total());
    }
}
