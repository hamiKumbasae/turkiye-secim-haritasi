package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir seçimde bir mahallede bir seçeneğin oyu. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "oy_mahalle")
@IdClass(OyMahalleId.class)
public class OyMahalle {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Id
    @Column(name = "mahalle_id")
    private String mahalleId;

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "oy")
    private Integer oy;

    @Column(name = "oran")
    private java.math.BigDecimal oran;

    protected OyMahalle() {
    }

    public OyMahalle(String secimId, String ilceId, String mahalleId, Integer partiId, Integer oy, java.math.BigDecimal oran) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.mahalleId = mahalleId;
        this.partiId = partiId;
        this.oy = oy;
        this.oran = oran;
    }

    public String getSecimId() {
        return secimId;
    }

    public String getIlceId() {
        return ilceId;
    }

    public String getMahalleId() {
        return mahalleId;
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
}
