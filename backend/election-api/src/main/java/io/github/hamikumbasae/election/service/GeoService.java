package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.domain.NeighbourhoodGeometry;
import io.github.hamikumbasae.election.dto.GeoJsonFeature;
import io.github.hamikumbasae.election.dto.GeoJsonFeatureCollection;
import io.github.hamikumbasae.election.repository.NeighbourhoodGeometryRepository;
import io.github.hamikumbasae.election.repository.ResultRepository;
import io.github.hamikumbasae.election.repository.ResultRepository.UnitFilter;
import io.github.hamikumbasae.election.repository.UnitRow;
import io.github.hamikumbasae.election.repository.VoteRow;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/** Neighbourhood boundaries as GeoJSON, optionally joined with one election's results (choropleth-ready). */
@Service
public class GeoService {

    private final NeighbourhoodGeometryRepository geometries;
    private final ResultRepository results;
    private final ElectionService elections;

    public GeoService(NeighbourhoodGeometryRepository geometries, ResultRepository results, ElectionService elections) {
        this.geometries = geometries;
        this.results = results;
        this.elections = elections;
    }

    @Cacheable(cacheNames = "geo", key = "{#districtGeomId, #electionCode == null ? '' : #electionCode.toLowerCase()}")
    public GeoJsonFeatureCollection districtNeighbourhoods(String districtGeomId, String electionCode) {
        List<NeighbourhoodGeometry> shapes = geometries.findByDistrictGeomIdOrderByName(districtGeomId);
        if (shapes.isEmpty()) {
            throw new NotFoundException("No neighbourhood boundaries for district '" + districtGeomId + "'");
        }
        Map<String, UnitRow> rows = Map.of();
        Map<Integer, List<VoteRow>> votes = Map.of();
        String code = null;
        if (electionCode != null) {
            ElectionCatalog.Entry election = elections.require(electionCode);
            code = election.dto().code();
            rows = results.findUnits(new UnitFilter(election.id(), Level.NEIGHBOURHOOD, null, null, districtGeomId),
                            10_000, 0).stream()
                    .collect(Collectors.toMap(UnitRow::geomId, Function.identity(), (a, b) -> a));
            votes = results.findVotes(rows.values().stream().map(UnitRow::id).toList());
        }
        final String election = code;
        final Map<String, UnitRow> byGeom = rows;
        final Map<Integer, List<VoteRow>> votesByUnit = votes;
        List<GeoJsonFeature> features = shapes.stream()
                .map(s -> feature(s, election, byGeom.get(s.getGeomId()),
                        byGeom.containsKey(s.getGeomId()) ? votesByUnit.get(byGeom.get(s.getGeomId()).id()) : null))
                .toList();
        return GeoJsonFeatureCollection.of(features);
    }

    public GeoJsonFeature neighbourhood(String districtGeomId, String geomId) {
        NeighbourhoodGeometry s = geometries.findByDistrictGeomIdAndGeomId(districtGeomId, geomId)
                .orElseThrow(() -> new NotFoundException("No boundary for neighbourhood '" + geomId
                        + "' in district '" + districtGeomId + "'"));
        return feature(s, null, null, null);
    }

    private static GeoJsonFeature feature(NeighbourhoodGeometry s, String election, UnitRow row, List<VoteRow> votes) {
        Map<String, Object> props = new LinkedHashMap<>();
        props.put("geomId", s.getGeomId());
        props.put("districtGeomId", s.getDistrictGeomId());
        props.put("name", s.getName());
        if (election != null) {
            props.put("election", election);
            props.put("hasResult", row != null);
            if (row != null) {
                VoteRow top = votes == null || votes.isEmpty() ? null : votes.getFirst();
                props.put("winner", row.winner() != null ? row.winner() : top == null ? null : top.party());
                props.put("winnerShare", top == null ? null : top.share());
                props.put("turnout", row.turnout());
                props.put("registeredVoters", row.registeredVoters());
                props.put("validVotes", row.validVotes());
            }
        }
        return GeoJsonFeature.of(s.getGeomId(), s.getGeometry(), props);
    }
}
