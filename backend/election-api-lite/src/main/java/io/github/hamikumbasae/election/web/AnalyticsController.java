package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PartyHistoryDto;
import io.github.hamikumbasae.election.dto.RankingEntryDto;
import io.github.hamikumbasae.election.service.AnalyticsService;
import io.github.hamikumbasae.election.service.AnalyticsService.Order;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Analytics", description = "Party history over time and top-N rankings")
public class AnalyticsController {

    private final AnalyticsService analytics;

    public AnalyticsController(AnalyticsService analytics) {
        this.analytics = analytics;
    }

    @GetMapping("/history")
    @Operation(summary = "A party's results in one place across elections",
            description = "Province by plate, or a district of it by name (district boundaries and ids change "
                    + "over time, names do not). Example: party=AK Parti&plate=34&district=Ümraniye")
    public PartyHistoryDto history(
            @Parameter(description = "Party, candidate or option as stored, case-insensitive (AK Parti, CHP, Evet)")
            @RequestParam @NotBlank @Size(max = 255) String party,
            @RequestParam @Min(1) @Max(81) int plate,
            @Parameter(description = "District name within the province; case and Turkish letters are ignored (umraniye = Ümraniye)")
            @RequestParam(required = false) @Size(max = 255) String district,
            @RequestParam(required = false) ElectionType type,
            @Parameter(description = "Keep elections where the party is listed with 0 votes")
            @RequestParam(defaultValue = "false") boolean includeZero) {
        return analytics.partyHistory(party, plate, district, type, includeZero);
    }

    @GetMapping("/elections/{code}/rankings/turnout")
    @Operation(summary = "Highest (or lowest) turnout",
            description = "level=province|district|neighbourhood. Scope districts with plate, neighbourhoods with district.")
    public List<RankingEntryDto> turnout(
            @PathVariable String code,
            @RequestParam(defaultValue = "district") Level level,
            @RequestParam(required = false) @Min(1) @Max(81) Integer plate,
            @Parameter(description = "District geometry id (required for level=neighbourhood)")
            @RequestParam(required = false) @Pattern(regexp = ResultController.GEOM_ID) String district,
            @RequestParam(defaultValue = "desc") Order order,
            @Parameter(description = "Ignore units with fewer registered voters")
            @RequestParam(defaultValue = "0") @Min(0) long minVoters,
            @RequestParam(defaultValue = "10") @Min(1) @Max(100) int limit) {
        return analytics.turnoutRanking(code, level, plate, district, order, minVoters, limit);
    }

    @GetMapping("/elections/{code}/rankings/party")
    @Operation(summary = "Strongest (or weakest) units for a party by vote share")
    public List<RankingEntryDto> party(
            @PathVariable String code,
            @RequestParam @NotBlank @Size(max = 255) String party,
            @RequestParam(defaultValue = "province") Level level,
            @RequestParam(required = false) @Min(1) @Max(81) Integer plate,
            @RequestParam(required = false) @Pattern(regexp = ResultController.GEOM_ID) String district,
            @RequestParam(defaultValue = "desc") Order order,
            @RequestParam(defaultValue = "0") @Min(0) long minVoters,
            @RequestParam(defaultValue = "10") @Min(1) @Max(100) int limit) {
        return analytics.partyRanking(code, party, level, plate, district, order, minVoters, limit);
    }
}
