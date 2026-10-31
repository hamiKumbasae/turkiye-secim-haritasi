package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.Level;
import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;

@Schema(description = "Headline figures of a province, district or neighbourhood (no party breakdown)")
public record UnitSummaryDto(
        Level level,
        @Schema(example = "34") Integer plateCode,
        @Schema(example = "Ümraniye") String name,
        @Schema(example = "TR-D-34-037", description = "Map geometry id (districts, neighbourhoods)") String geomId,
        Long registeredVoters,
        Long validVotes,
        Integer ballotBoxes,
        @Schema(example = "91.45") BigDecimal turnout,
        @Schema(example = "AK Parti") String winner,
        Integer seats) {
}
