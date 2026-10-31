package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.Level;
import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.util.List;

@Schema(description = "Full result of one unit, parties sorted by votes (descending)")
public record UnitResultDto(
        @Schema(example = "2023") String electionCode,
        Level level,
        @Schema(example = "34") Integer plateCode,
        @Schema(example = "İstanbul") String name,
        String geomId,
        @Schema(description = "District geometry id of a neighbourhood") String parentGeomId,
        Long registeredVoters,
        Long votesCast,
        Long validVotes,
        Integer ballotBoxes,
        @Schema(example = "90.53") BigDecimal turnout,
        String winner,
        Integer seats,
        List<PartyResultDto> results) {
}
