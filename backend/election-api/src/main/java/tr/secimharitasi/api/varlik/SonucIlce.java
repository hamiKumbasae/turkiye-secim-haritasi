package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir seçimde bir ilçenin sonucu; ad ve plaka o seçimdeki değerlerdir. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "sonuc_ilce")
@IdClass(SonucIlceId.class)
public class SonucIlce {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Column(name = "plaka")
    private Integer plaka;

    @Column(name = "ad")
    private String ad;

    @Column(name = "secmen")
    private Integer secmen;

    @Column(name = "oy_kullanan")
    private Integer oyKullanan;

    @Column(name = "gecerli_oy")
    private Integer gecerliOy;

    @Column(name = "gecersiz_oy")
    private Integer gecersizOy;

    @Column(name = "sandik")
    private Integer sandik;

    @Column(name = "katilim")
    private java.math.BigDecimal katilim;

    @Column(name = "kazanan_parti_id")
    private Integer kazananPartiId;

    @Column(name = "baskan")
    private String baskan;

    @Column(name = "sadece_kazanan")
    private Boolean sadeceKazanan;

    @Column(name = "not_metni")
    private String notMetni;

    protected SonucIlce() {
    }

    public SonucIlce(String secimId, String ilceId, Integer plaka, String ad, Integer secmen, Integer oyKullanan, Integer gecerliOy, Integer gecersizOy, Integer sandik, java.math.BigDecimal katilim, Integer kazananPartiId, String baskan, Boolean sadeceKazanan, String notMetni) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.plaka = plaka;
        this.ad = ad;
        this.secmen = secmen;
        this.oyKullanan = oyKullanan;
        this.gecerliOy = gecerliOy;
        this.gecersizOy = gecersizOy;
        this.sandik = sandik;
        this.katilim = katilim;
        this.kazananPartiId = kazananPartiId;
        this.baskan = baskan;
        this.sadeceKazanan = sadeceKazanan;
        this.notMetni = notMetni;
    }

    public String getSecimId() {
        return secimId;
    }

    public String getIlceId() {
        return ilceId;
    }

    public Integer getPlaka() {
        return plaka;
    }

    public String getAd() {
        return ad;
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

    public Integer getGecersizOy() {
        return gecersizOy;
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

    public String getBaskan() {
        return baskan;
    }

    public Boolean getSadeceKazanan() {
        return sadeceKazanan;
    }

    public String getNotMetni() {
        return notMetni;
    }
}
