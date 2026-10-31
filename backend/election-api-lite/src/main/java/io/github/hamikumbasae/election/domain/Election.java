package io.github.hamikumbasae.election.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** One election ({@code secim} table). Read-only: the table is owned by the data loader. */
@Entity
@Immutable
@Table(name = "secim")
public class Election {

    @Id
    private Integer id;

    @Column(name = "kod", nullable = false)
    private String code;

    @Column(name = "tur", nullable = false)
    private String type;

    @Column(name = "ad")
    private String name;

    @Column(name = "yil")
    private Integer year;

    @Column(name = "toplam_sandalye")
    private Integer totalSeats;

    protected Election() {
    }

    public Election(Integer id, String code, String type, String name, Integer year, Integer totalSeats) {
        this.id = id;
        this.code = code;
        this.type = type;
        this.name = name;
        this.year = year;
        this.totalSeats = totalSeats;
    }

    public Integer getId() {
        return id;
    }

    public String getCode() {
        return code;
    }

    public ElectionType getType() {
        return ElectionType.fromDb(type);
    }

    public String getName() {
        return name;
    }

    public Integer getYear() {
        return year;
    }

    public Integer getTotalSeats() {
        return totalSeats;
    }
}
