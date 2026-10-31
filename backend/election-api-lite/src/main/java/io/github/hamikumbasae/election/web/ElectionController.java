package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.dto.ElectionDto;
import io.github.hamikumbasae.election.dto.ElectionSummaryDto;
import io.github.hamikumbasae.election.service.ElectionService;
import io.github.hamikumbasae.election.service.ResultService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/elections")
@Tag(name = "Elections", description = "Election catalogue and nationwide totals")
public class ElectionController {

    private final ElectionService elections;
    private final ResultService results;

    public ElectionController(ElectionService elections, ResultService results) {
        this.elections = elections;
        this.results = results;
    }

    @GetMapping
    @Operation(summary = "List elections", description = "Chronological. Filter by type and/or year.")
    public List<ElectionDto> list(
            @Parameter(description = "general, local, presidential, referendum (Turkish names accepted)")
            @RequestParam(required = false) ElectionType type,
            @RequestParam(required = false) @Min(1950) @Max(2100) Integer year) {
        return elections.list(type, year);
    }

    @GetMapping("/{code}")
    @Operation(summary = "Get one election by code", description = "Codes look like 2023, 2024yerel, 2017referandum, 2023cb1tur.")
    public ElectionDto get(@PathVariable String code) {
        return elections.get(code);
    }

    @GetMapping("/{code}/summary")
    @Operation(summary = "Nationwide totals by party",
            description = "Computed from all province rows plus the abroad row; cached.")
    public ElectionSummaryDto summary(@PathVariable String code) {
        return results.summary(code);
    }
}
