package io.github.hamikumbasae.election.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "GeoJSON FeatureCollection (RFC 7946)")
public record GeoJsonFeatureCollection(@Schema(example = "FeatureCollection") String type, List<GeoJsonFeature> features) {

    public static GeoJsonFeatureCollection of(List<GeoJsonFeature> features) {
        return new GeoJsonFeatureCollection("FeatureCollection", features);
    }
}
