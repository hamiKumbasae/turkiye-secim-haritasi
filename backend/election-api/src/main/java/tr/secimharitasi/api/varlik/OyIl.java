package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir seçimde bir ilde bir seçeneğin oyu. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "oy_il")
@IdClass(OyIlId.class)
public class OyIl {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "plaka")
    private Integer plaka;

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "oy")
    private Integer oy;

    @Column(name = "oran")
    private java.math.BigDecimal oran;

    protected OyIl() {
    }

    public OyIl(String secimId, Integer plaka, Integer partiId, Integer oy, java.math.BigDecimal oran) {
        this.secimId = secimId;
        this.plaka = plaka;
        this.partiId = partiId;
        this.oy = oy;
        this.oran = oran;
    }

    public String getSecimId() {
        return secimId;
    }

    public Integer getPlaka() {
        return plaka;
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
