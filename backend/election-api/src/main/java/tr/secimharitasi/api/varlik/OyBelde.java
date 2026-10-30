package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir beldede bir seçeneğin oyu. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "oy_belde")
@IdClass(OyBeldeId.class)
public class OyBelde {

    @Id
    @Column(name = "sonuc_belde_id")
    private Integer sonucBeldeId;

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "oy")
    private Integer oy;

    protected OyBelde() {
    }

    public OyBelde(Integer sonucBeldeId, Integer partiId, Integer oy) {
        this.sonucBeldeId = sonucBeldeId;
        this.partiId = partiId;
        this.oy = oy;
    }

    public Integer getSonucBeldeId() {
        return sonucBeldeId;
    }

    public Integer getPartiId() {
        return partiId;
    }

    public Integer getOy() {
        return oy;
    }
}
