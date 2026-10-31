package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir ilçede bir partinin meclis üyesi sayısı. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "sandalye_ilce")
@IdClass(SandalyeIlceId.class)
public class SandalyeIlce {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "sandalye")
    private Integer sandalye;

    protected SandalyeIlce() {
    }

    public SandalyeIlce(String secimId, String ilceId, Integer partiId, Integer sandalye) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.partiId = partiId;
        this.sandalye = sandalye;
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

    public Integer getSandalye() {
        return sandalye;
    }
}
