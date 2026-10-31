package io.github.hamikumbasae.election.web;

import io.github.hamikumbasae.election.dto.GeoJsonFeature;
import io.github.hamikumbasae.election.dto.GeoJsonFeatureCollection;
import io.github.hamikumbasae.election.service.GeoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Pattern;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Duration;

@RestController
@RequestMapping("/api/v1/geo")
@Tag(name = "Geo", description = "Neighbourhood boundaries as GeoJSON")
public class GeoController {

    public static final String GEO_JSON = "application/geo+json";

    private final GeoService geo;

    public GeoController(GeoService geo) {
        this.geo = geo;
    }

    @GetMapping(value = "/districts/{districtGeomId}/neighbourhoods", produces = {GEO_JSON, "application/json"})
    @Operation(summary = "All neighbourhood boundaries of a district as a FeatureCollection",
            description = "With election=<code>, each feature also carries winner, winnerShare and turnout, "
                    + "ready for a choropleth map.")
    public ResponseEntity<GeoJsonFeatureCollection> district(
            @PathVariable @Pattern(regexp = ResultController.GEOM_ID) String districtGeomId,
            @Parameter(description = "Election code to join results, e.g. 2023")
            @RequestParam(required = false) String election) {
        return ResponseEntity.ok().cacheControl(CacheControl.maxAge(Duration.ofHours(1)).cachePublic())
                .body(geo.districtNeighbourhoods(districtGeomId, election));
    }

    @GetMapping(value = "/districts/{districtGeomId}/neighbourhoods/{geomId}", produces = {GEO_JSON, "application/json"})
    @Operation(summary = "One neighbourhood boundary as a Feature")
    public ResponseEntity<GeoJsonFeature> neighbourhood(
            @PathVariable @Pattern(regexp = ResultController.GEOM_ID) String districtGeomId,
            @PathVariable @Pattern(regexp = ResultController.GEOM_ID) String geomId) {
        return ResponseEntity.ok().cacheControl(CacheControl.maxAge(Duration.ofHours(1)).cachePublic())
                .body(geo.neighbourhood(districtGeomId, geomId));
    }
}
