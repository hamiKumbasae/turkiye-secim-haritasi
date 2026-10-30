package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Kaynakta ne kadar kayıt bulunduğu. Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "kaynak_kapsami")
@IdClass(KaynakKapsamiId.class)
public class KaynakKapsami {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Id
    @Column(name = "veri")
    private String veri;

    @Column(name = "bulunan")
    private Integer bulunan;

    @Column(name = "beklenen")
    private Integer beklenen;

    @Column(name = "durum")
    private String durum;

    @Column(name = "aciklama")
    private String aciklama;

    protected KaynakKapsami() {
    }

    public KaynakKapsami(String secimId, String veri, Integer bulunan, Integer beklenen, String durum, String aciklama) {
        this.secimId = secimId;
        this.veri = veri;
        this.bulunan = bulunan;
        this.beklenen = beklenen;
        this.durum = durum;
        this.aciklama = aciklama;
    }

    public String getSecimId() {
        return secimId;
    }

    public String getVeri() {
        return veri;
    }

    public Integer getBulunan() {
        return bulunan;
    }

    public Integer getBeklenen() {
        return beklenen;
    }

    public String getDurum() {
        return durum;
    }

    public String getAciklama() {
        return aciklama;
    }
}
