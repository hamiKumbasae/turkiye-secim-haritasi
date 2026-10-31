package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Mahalle/köy (muhtarlık); ad mahalle_geo.json'dan. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "mahalle")
@IdClass(MahalleId.class)
public class Mahalle {

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Id
    @Column(name = "mahalle_id")
    private String mahalleId;

    @Column(name = "ad")
    private String ad;

    protected Mahalle() {
    }

    public Mahalle(String ilceId, String mahalleId, String ad) {
        this.ilceId = ilceId;
        this.mahalleId = mahalleId;
        this.ad = ad;
    }

    public String getIlceId() {
        return ilceId;
    }

    public String getMahalleId() {
        return mahalleId;
    }

    public String getAd() {
        return ad;
    }
}
