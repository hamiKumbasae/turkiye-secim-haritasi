package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** İlçe birimi; baslangic/bitis_yili verideki ilk/son seçim yılı (bitis null = bugün de var). Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "ilce")
public class Ilce {

    @Id
    @Column(name = "ilce_id")
    private String ilceId;

    @Column(name = "plaka")
    private Integer plaka;

    @Column(name = "ad")
    private String ad;

    @Column(name = "guncel")
    private Boolean guncel;

    @Column(name = "baslangic_yili")
    private Integer baslangicYili;

    @Column(name = "bitis_yili")
    private Integer bitisYili;

    protected Ilce() {
    }

    public Ilce(String ilceId, Integer plaka, String ad, Boolean guncel, Integer baslangicYili, Integer bitisYili) {
        this.ilceId = ilceId;
        this.plaka = plaka;
        this.ad = ad;
        this.guncel = guncel;
        this.baslangicYili = baslangicYili;
        this.bitisYili = bitisYili;
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

    public Boolean getGuncel() {
        return guncel;
    }

    public Integer getBaslangicYili() {
        return baslangicYili;
    }

    public Integer getBitisYili() {
        return bitisYili;
    }
}
