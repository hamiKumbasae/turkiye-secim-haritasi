package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir ilde bir partinin milletvekili sayısı. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "sandalye_il")
@IdClass(SandalyeIlId.class)
public class SandalyeIl {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "plaka")
    private Integer plaka;

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "sandalye")
    private Integer sandalye;

    protected SandalyeIl() {
    }

    public SandalyeIl(String secimId, Integer plaka, Integer partiId, Integer sandalye) {
        this.secimId = secimId;
        this.plaka = plaka;
        this.partiId = partiId;
        this.sandalye = sandalye;
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

    public Integer getSandalye() {
        return sandalye;
    }
}
