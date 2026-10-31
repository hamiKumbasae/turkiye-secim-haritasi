package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.swagger.v3.oas.annotations.media.Schema;

import java.time.LocalDate;

@Schema(description = "An election, referendum or presidential round")
public record ElectionDto(
        @Schema(example = "2023", description = "Stable identifier used in URLs") String code,
        ElectionType type,
        @Schema(example = "14 Mayıs 2023") String name,
        @Schema(example = "2023") Integer year,
        @Schema(example = "2023-05-14") LocalDate date,
        @Schema(example = "600", description = "Seats in parliament (general elections only)") Integer totalSeats) {
}
