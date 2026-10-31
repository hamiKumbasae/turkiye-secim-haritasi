package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Bir seçimde bir belde belediyesi. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "sonuc_belde")
public class SonucBelde {

    @Id
    @Column(name = "sonuc_belde_id")
    private Integer sonucBeldeId;

    @Column(name = "secim_id")
    private String secimId;

    @Column(name = "plaka")
    private Integer plaka;

    @Column(name = "ilce_id")
    private String ilceId;

    @Column(name = "ilce_ad")
    private String ilceAd;

    @Column(name = "belde_ad")
    private String beldeAd;

    @Column(name = "belde_kod")
    private Integer beldeKod;

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

    @Column(name = "aday")
    private String aday;

    @Column(name = "sadece_kazanan")
    private Boolean sadeceKazanan;

    @Column(name = "kaynak")
    private String kaynak;

    @Column(name = "kontrol")
    private String kontrol;

    @Column(name = "not_metni")
    private String notMetni;

    protected SonucBelde() {
    }

    public SonucBelde(Integer sonucBeldeId, String secimId, Integer plaka, String ilceId, String ilceAd, String beldeAd, Integer beldeKod, Integer secmen, Integer oyKullanan, Integer gecerliOy, Integer gecersizOy, Integer sandik, java.math.BigDecimal katilim, Integer kazananPartiId, String aday, Boolean sadeceKazanan, String kaynak, String kontrol, String notMetni) {
        this.sonucBeldeId = sonucBeldeId;
        this.secimId = secimId;
        this.plaka = plaka;
        this.ilceId = ilceId;
        this.ilceAd = ilceAd;
        this.beldeAd = beldeAd;
        this.beldeKod = beldeKod;
        this.secmen = secmen;
        this.oyKullanan = oyKullanan;
        this.gecerliOy = gecerliOy;
        this.gecersizOy = gecersizOy;
        this.sandik = sandik;
        this.katilim = katilim;
        this.kazananPartiId = kazananPartiId;
        this.aday = aday;
        this.sadeceKazanan = sadeceKazanan;
        this.kaynak = kaynak;
        this.kontrol = kontrol;
        this.notMetni = notMetni;
    }

    public Integer getSonucBeldeId() {
        return sonucBeldeId;
    }

    public String getSecimId() {
        return secimId;
    }

    public Integer getPlaka() {
        return plaka;
    }

    public String getIlceId() {
        return ilceId;
    }

    public String getIlceAd() {
        return ilceAd;
    }

    public String getBeldeAd() {
        return beldeAd;
    }

    public Integer getBeldeKod() {
        return beldeKod;
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

    public String getAday() {
        return aday;
    }

    public Boolean getSadeceKazanan() {
        return sadeceKazanan;
    }

    public String getKaynak() {
        return kaynak;
    }

    public String getKontrol() {
        return kontrol;
    }

    public String getNotMetni() {
        return notMetni;
    }
}
