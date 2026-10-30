package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, ilce_id, mahalle_id, parti_id). */
public class OyMahalleId implements Serializable {

    private String secimId;
    private String ilceId;
    private String mahalleId;
    private Integer partiId;

    public OyMahalleId() {
    }

    public OyMahalleId(String secimId, String ilceId, String mahalleId, Integer partiId) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.mahalleId = mahalleId;
        this.partiId = partiId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof OyMahalleId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(ilceId, that.ilceId) && Objects.equals(mahalleId, that.mahalleId) && Objects.equals(partiId, that.partiId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, ilceId, mahalleId, partiId);
    }
}
