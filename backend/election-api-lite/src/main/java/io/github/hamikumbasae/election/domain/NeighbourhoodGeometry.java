package io.github.hamikumbasae.election.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

import java.io.Serializable;
import java.util.Objects;

/** Neighbourhood (mahalle) boundary, stored as a GeoJSON geometry string in {@code mahalle.geometri}. */
@Entity
@Immutable
@Table(name = "mahalle")
@IdClass(NeighbourhoodGeometry.Key.class)
public class NeighbourhoodGeometry {

    @Id
    @Column(name = "ilce_geom_id")
    private String districtGeomId;

    @Id
    @Column(name = "geom_id")
    private String geomId;

    @Column(name = "ad")
    private String name;

    @Column(name = "geometri", columnDefinition = "LONGTEXT")
    private String geometry;

    protected NeighbourhoodGeometry() {
    }

    public NeighbourhoodGeometry(String districtGeomId, String geomId, String name, String geometry) {
        this.districtGeomId = districtGeomId;
        this.geomId = geomId;
        this.name = name;
        this.geometry = geometry;
    }

    public String getDistrictGeomId() {
        return districtGeomId;
    }

    public String getGeomId() {
        return geomId;
    }

    public String getName() {
        return name;
    }

    public String getGeometry() {
        return geometry;
    }

    public static class Key implements Serializable {
        private String districtGeomId;
        private String geomId;

        public Key() {
        }

        public Key(String districtGeomId, String geomId) {
            this.districtGeomId = districtGeomId;
            this.geomId = geomId;
        }

        @Override
        public boolean equals(Object o) {
            return o instanceof Key k && Objects.equals(districtGeomId, k.districtGeomId)
                    && Objects.equals(geomId, k.geomId);
        }

        @Override
        public int hashCode() {
            return Objects.hash(districtGeomId, geomId);
        }
    }
}
