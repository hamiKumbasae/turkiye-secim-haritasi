package io.github.hamikumbasae.election.dto;

import com.fasterxml.jackson.annotation.JsonRawValue;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.Map;

@Schema(description = "GeoJSON Feature (RFC 7946)")
public record GeoJsonFeature(
        @Schema(example = "Feature") String type,
        @Schema(example = "tTR-Y-34-037-M-0001") String id,
        @Schema(type = "object", description = "GeoJSON geometry, passed through as stored") @JsonRawValue String geometry,
        Map<String, Object> properties) {

    public static GeoJsonFeature of(String id, String geometry, Map<String, Object> properties) {
        return new GeoJsonFeature("Feature", id, geometry == null || geometry.isBlank() ? "null" : geometry, properties);
    }
}
