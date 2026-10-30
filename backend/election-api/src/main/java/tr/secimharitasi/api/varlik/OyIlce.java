package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir seçimde bir ilçede bir seçeneğin oyu. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "oy_ilce")
@IdClass(OyIlceId.class)
public class OyIlce {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "oy")
    private Integer oy;

    @Column(name = "oran")
    private java.math.BigDecimal oran;

    @Column(name = "aday")
    private String aday;

    protected OyIlce() {
    }

    public OyIlce(String secimId, String ilceId, Integer partiId, Integer oy, java.math.BigDecimal oran, String aday) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.partiId = partiId;
        this.oy = oy;
        this.oran = oran;
        this.aday = aday;
    }

    public String getSecimId() {
        return secimId;
    }

    public String getIlceId() {
        return ilceId;
    }

    public Integer getPartiId() {
        return partiId;
    }

    public Integer getOy() {
        return oy;
    }

    public java.math.BigDecimal getOran() {
        return oran;
    }

    public String getAday() {
        return aday;
    }
}
