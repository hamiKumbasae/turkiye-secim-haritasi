package io.github.hamikumbasae.election.dto;

import io.github.hamikumbasae.election.domain.Level;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "A place matching the search, with the elections it has results for")
public record SearchHitDto(
        Level level,
        @Schema(example = "34") Integer plateCode,
        @Schema(example = "Ümraniye") String name,
        @Schema(example = "TR-D-34-037") String geomId,
        @Schema(description = "District geometry id (neighbourhoods)") String parentGeomId,
        @Schema(description = "District name (neighbourhoods)") String districtName,
        @Schema(example = "2009") Integer firstYear,
        @Schema(example = "2024") Integer lastYear,
        @Schema(description = "Codes of the elections with a result for this place, oldest first")
        List<String> elections) {
}
