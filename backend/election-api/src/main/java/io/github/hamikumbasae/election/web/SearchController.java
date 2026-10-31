package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.SearchHitDto;
import io.github.hamikumbasae.election.service.SearchService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/search")
@Tag(name = "Search", description = "Find provinces, districts and neighbourhoods by name")
public class SearchController {

    private final SearchService search;

    public SearchController(SearchService search) {
        this.search = search;
    }

    @GetMapping
    @Operation(summary = "Search places by name (case- and Turkish-letter-insensitive)",
            description = "q=ümraniye, q=UMRANIYE, q=ISTANBUL, q=camlica ... Returns geometry ids for the result endpoints.")
    public PageResponse<SearchHitDto> search(
            @RequestParam @Size(min = 2, max = 100) String q,
            @RequestParam(required = false) Level level,
            @Parameter(description = "Restrict to one election code")
            @RequestParam(required = false) String election,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return search.search(q, level, election, page, size);
    }
}
