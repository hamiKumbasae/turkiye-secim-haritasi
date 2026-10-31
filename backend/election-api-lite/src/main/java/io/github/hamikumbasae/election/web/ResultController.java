package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.UnitResultDto;
import io.github.hamikumbasae.election.dto.UnitSummaryDto;
import io.github.hamikumbasae.election.service.ResultService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/elections/{code}")
@Tag(name = "Results", description = "Province, district, neighbourhood and abroad results of one election")
public class ResultController {

    /** Geometry ids: TR-D-34-037 (district), HIST-Istanbul-Umraniye-9208 (historical district). */
    static final String GEOM_ID = "^[A-Za-z0-9._-]{1,191}$";

    private final ResultService results;

    public ResultController(ResultService results) {
        this.results = results;
    }

    @GetMapping("/provinces")
    @Operation(summary = "All provinces (headline figures, winner)")
    public List<UnitSummaryDto> provinces(@PathVariable String code) {
        return results.provinces(code);
    }

    @GetMapping("/provinces/{plate}")
    @Operation(summary = "Province result by plate code", description = "Parties sorted by votes.")
    public UnitResultDto province(@PathVariable String code,
                                  @Parameter(description = "Plate code 1-81, e.g. 34 for İstanbul")
                                  @PathVariable @Min(1) @Max(81) int plate) {
        return results.province(code, plate);
    }

    @GetMapping("/provinces/{plate}/districts")
    @Operation(summary = "Districts of a province (headline figures, winner)")
    public List<UnitSummaryDto> districts(@PathVariable String code, @PathVariable @Min(1) @Max(81) int plate) {
        return results.districts(code, plate);
    }

    @GetMapping("/districts/{geomId}")
    @Operation(summary = "District result by geometry id", description = "e.g. TR-D-34-037 (Ümraniye). Find ids via /search.")
    public UnitResultDto district(@PathVariable String code, @PathVariable @Pattern(regexp = GEOM_ID) String geomId) {
        return results.district(code, geomId);
    }

    @GetMapping("/districts/{geomId}/neighbourhoods")
    @Operation(summary = "Neighbourhood (mahalle) results of a district, paged",
            description = "Available for elections from 2009 on.")
    public PageResponse<UnitResultDto> neighbourhoods(
            @PathVariable String code,
            @PathVariable @Pattern(regexp = GEOM_ID) String geomId,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "50") @Min(1) @Max(500) int size) {
        return results.neighbourhoods(code, geomId, page, size);
    }

    @GetMapping("/abroad")
    @Operation(summary = "Votes cast abroad", description = "Only elections with a separate abroad count (2014 on).")
    public UnitResultDto abroad(@PathVariable String code) {
        return results.abroad(code);
    }
}
