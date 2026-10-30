package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Seçilen milletvekili ya da senatör. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "secilen")
public class Secilen {

    @Id
    @Column(name = "secilen_id")
    private Integer secilenId;

    @Column(name = "secim_id")
    private String secimId;

    @Column(name = "plaka")
    private Integer plaka;

    @Column(name = "gorev")
    private String gorev;

    @Column(name = "ad")
    private String ad;

    @Column(name = "parti_id")
    private Integer partiId;

    @Column(name = "parti_adi_kaynakta")
    private String partiAdiKaynakta;

    @Column(name = "bolge")
    private String bolge;

    @Column(name = "kisi_link")
    private String kisiLink;

    protected Secilen() {
    }

    public Secilen(Integer secilenId, String secimId, Integer plaka, String gorev, String ad, Integer partiId, String partiAdiKaynakta, String bolge, String kisiLink) {
        this.secilenId = secilenId;
        this.secimId = secimId;
        this.plaka = plaka;
        this.gorev = gorev;
        this.ad = ad;
        this.partiId = partiId;
        this.partiAdiKaynakta = partiAdiKaynakta;
        this.bolge = bolge;
        this.kisiLink = kisiLink;
    }

    public Integer getSecilenId() {
        return secilenId;
    }

    public String getSecimId() {
        return secimId;
    }

    public Integer getPlaka() {
        return plaka;
    }

    public String getGorev() {
        return gorev;
    }

    public String getAd() {
        return ad;
    }

    public Integer getPartiId() {
        return partiId;
    }

    public String getPartiAdiKaynakta() {
        return partiAdiKaynakta;
    }

    public String getBolge() {
        return bolge;
    }

    public String getKisiLink() {
        return kisiLink;
    }
}
