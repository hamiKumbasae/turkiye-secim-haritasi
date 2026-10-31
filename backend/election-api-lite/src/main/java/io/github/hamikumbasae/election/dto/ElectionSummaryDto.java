package io.github.hamikumbasae.election.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.util.List;

@Schema(description = "Nationwide totals, aggregated from every province row plus the abroad row")
public record ElectionSummaryDto(
        ElectionDto election,
        long registeredVoters,
        long validVotes,
        @Schema(description = "Turnout weighted by registered voters, percent") BigDecimal turnout,
        int provinces,
        boolean includesAbroad,
        List<PartyResultDto> results) {
}
