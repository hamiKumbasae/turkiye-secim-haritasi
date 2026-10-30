package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Parti ve öteki oy seçenekleri. parti_id sabittir; onceki_parti_id devamlılığı tutar. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "parti")
public class Parti {

    @Id
    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "ad")
    private String ad;

    @Column(name = "kisa")
    private String kisa;

    @Column(name = "tip")
    private String tip;

    @Column(name = "renk")
    private String renk;

    @Column(name = "onceki_parti_id")
    private Integer oncekiPartiId;

    @Column(name = "gecis_turu")
    private String gecisTuru;

    @Column(name = "gecis_yili")
    private Integer gecisYili;

    @Column(name = "gecis_kaynagi")
    private String gecisKaynagi;

    protected Parti() {
    }

    public Parti(Integer partiId, String ad, String kisa, String tip, String renk, Integer oncekiPartiId, String gecisTuru, Integer gecisYili, String gecisKaynagi) {
        this.partiId = partiId;
        this.ad = ad;
        this.kisa = kisa;
        this.tip = tip;
        this.renk = renk;
        this.oncekiPartiId = oncekiPartiId;
        this.gecisTuru = gecisTuru;
        this.gecisYili = gecisYili;
        this.gecisKaynagi = gecisKaynagi;
    }

    public Integer getPartiId() {
        return partiId;
    }

    public String getAd() {
        return ad;
    }

    public String getKisa() {
        return kisa;
    }

    public String getTip() {
        return tip;
    }

    public String getRenk() {
        return renk;
    }

    public Integer getOncekiPartiId() {
        return oncekiPartiId;
    }

    public String getGecisTuru() {
        return gecisTuru;
    }

    public Integer getGecisYili() {
        return gecisYili;
    }

    public String getGecisKaynagi() {
        return gecisKaynagi;
    }
}
