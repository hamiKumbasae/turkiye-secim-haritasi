package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.time.LocalDate;

public record PartyHistoryPointDto(
        @Schema(example = "2023") String electionCode,
        ElectionType type,
        LocalDate date,
        @Schema(example = "191623") long votes,
        @Schema(example = "39.95") BigDecimal share,
        @Schema(example = "1", description = "Placing of the party in that unit") int rank,
        @Schema(example = "AK Parti") String winner,
        @Schema(description = "Geometry id the place had in that election (district boundaries change)") String geomId) {
}
