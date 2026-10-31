package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.Level;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "How one party did in one place across elections, oldest first")
public record PartyHistoryDto(
        @Schema(example = "AK Parti") String party,
        Level level,
        @Schema(example = "34") int plateCode,
        @Schema(example = "Ümraniye") String place,
        List<PartyHistoryPointDto> points) {
}
