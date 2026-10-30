package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** İl; plaka 0 = yurt dışı. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "il")
public class Il {

    @Id
    @Column(name = "plaka")
    private Integer plaka;

    @Column(name = "ad")
    private String ad;

    protected Il() {
    }

    public Il(Integer plaka, String ad) {
        this.plaka = plaka;
        this.ad = ad;
    }

    public Integer getPlaka() {
        return plaka;
    }

    public String getAd() {
        return ad;
    }
}
