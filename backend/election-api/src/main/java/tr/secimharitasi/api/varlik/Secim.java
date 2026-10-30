package tr.secimharitasi.api.varlik;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.annotations.Immutable;

/** Seçim (ana seçimler). Salt okunur: tabloları data-loader yazar. */
@Entity
@Immutable
@Table(name = "secim")
public class Secim {

    @Id
    @Column(name = "secim_id")
    private String secimId;

    @Column(name = "tur")
    private String tur;

    @Column(name = "yil")
    private Integer yil;

    @Column(name = "tarih_metni")
    private String tarihMetni;

    @Column(name = "yarisma_turu")
    private String yarismaTuru;

    @Column(name = "sonuc_temeli")
    private String sonucTemeli;

    @Column(name = "toplam_sandalye")
    private Integer toplamSandalye;

    @Column(name = "birincil_kaynak")
    private String birincilKaynak;

    @Column(name = "kaynak_durumu")
    private String kaynakDurumu;

    protected Secim() {
    }

    public Secim(String secimId, String tur, Integer yil, String tarihMetni, String yarismaTuru, String sonucTemeli, Integer toplamSandalye, String birincilKaynak, String kaynakDurumu) {
        this.secimId = secimId;
        this.tur = tur;
        this.yil = yil;
        this.tarihMetni = tarihMetni;
        this.yarismaTuru = yarismaTuru;
        this.sonucTemeli = sonucTemeli;
        this.toplamSandalye = toplamSandalye;
        this.birincilKaynak = birincilKaynak;
        this.kaynakDurumu = kaynakDurumu;
    }

    public String getSecimId() {
        return secimId;
    }

    public String getTur() {
        return tur;
    }

    public Integer getYil() {
        return yil;
    }

    public String getTarihMetni() {
        return tarihMetni;
    }

    public String getYarismaTuru() {
        return yarismaTuru;
    }

    public String getSonucTemeli() {
        return sonucTemeli;
    }

    public Integer getToplamSandalye() {
        return toplamSandalye;
    }

    public String getBirincilKaynak() {
        return birincilKaynak;
    }

    public String getKaynakDurumu() {
        return kaynakDurumu;
    }
}
