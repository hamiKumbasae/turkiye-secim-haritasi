package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, ilce_id, mahalle_id). */
public class SonucMahalleId implements Serializable {

    private String secimId;
    private String ilceId;
    private String mahalleId;

    public SonucMahalleId() {
    }

    public SonucMahalleId(String secimId, String ilceId, String mahalleId) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.mahalleId = mahalleId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof SonucMahalleId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(ilceId, that.ilceId) && Objects.equals(mahalleId, that.mahalleId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, ilceId, mahalleId);
    }
}
