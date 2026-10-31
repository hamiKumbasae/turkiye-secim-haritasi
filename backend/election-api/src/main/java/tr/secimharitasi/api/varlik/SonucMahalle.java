package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir seçimde bir mahallenin sonucu. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "sonuc_mahalle")
@IdClass(SonucMahalleId.class)
public class SonucMahalle {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Id
    @Column(name = "mahalle_id")
    private String mahalleId;

    @Column(name = "secmen")
    private Integer secmen;

    @Column(name = "oy_kullanan")
    private Integer oyKullanan;

    @Column(name = "gecerli_oy")
    private Integer gecerliOy;

    @Column(name = "sandik")
    private Integer sandik;

    @Column(name = "katilim")
    private java.math.BigDecimal katilim;

    @Column(name = "kazanan_parti_id")
    private Integer kazananPartiId;

    protected SonucMahalle() {
    }

    public SonucMahalle(String secimId, String ilceId, String mahalleId, Integer secmen, Integer oyKullanan, Integer gecerliOy, Integer sandik, java.math.BigDecimal katilim, Integer kazananPartiId) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.mahalleId = mahalleId;
        this.secmen = secmen;
        this.oyKullanan = oyKullanan;
        this.gecerliOy = gecerliOy;
        this.sandik = sandik;
        this.katilim = katilim;
        this.kazananPartiId = kazananPartiId;
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

    public Integer getSecmen() {
        return secmen;
    }

    public Integer getOyKullanan() {
        return oyKullanan;
    }

    public Integer getGecerliOy() {
        return gecerliOy;
    }

    public Integer getSandik() {
        return sandik;
    }

    public java.math.BigDecimal getKatilim() {
        return katilim;
    }

    public Integer getKazananPartiId() {
        return kazananPartiId;
    }
}
