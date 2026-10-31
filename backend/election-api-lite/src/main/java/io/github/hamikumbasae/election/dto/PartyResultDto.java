package io.github.hamikumbasae.election.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;

@Schema(description = "Votes for one party, candidate or referendum option")
public record PartyResultDto(
        @Schema(example = "AK Parti") String party,
        @Schema(example = "3570227") long votes,
        @Schema(example = "35.43", description = "Share of valid votes, percent") BigDecimal share,
        @Schema(example = "40", description = "Seats won (general elections), null otherwise") Integer seats,
        @Schema(description = "Mayoral candidate (local elections), if known") String candidate) {
}
