package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.Level;
import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;

public record RankingEntryDto(
        @Schema(example = "1") int rank,
        Level level,
        Integer plateCode,
        @Schema(example = "Kırklareli") String name,
        String geomId,
        @Schema(example = "45.60", description = "Ranked value: turnout or party share, percent") BigDecimal value,
        @Schema(description = "Party votes (party rankings) or registered voters (turnout rankings)") Long votes,
        String winner) {
}
