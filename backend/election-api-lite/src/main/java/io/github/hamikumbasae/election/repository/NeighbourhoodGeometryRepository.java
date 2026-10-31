package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.NeighbourhoodGeometry;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface NeighbourhoodGeometryRepository
        extends JpaRepository<NeighbourhoodGeometry, NeighbourhoodGeometry.Key> {

    List<NeighbourhoodGeometry> findByDistrictGeomIdOrderByName(String districtGeomId);

    Optional<NeighbourhoodGeometry> findByDistrictGeomIdAndGeomId(String districtGeomId, String geomId);
}
