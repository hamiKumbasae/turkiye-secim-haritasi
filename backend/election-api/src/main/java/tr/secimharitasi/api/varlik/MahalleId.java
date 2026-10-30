package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (ilce_id, mahalle_id). */
public class MahalleId implements Serializable {

    private String ilceId;
    private String mahalleId;

    public MahalleId() {
    }

    public MahalleId(String ilceId, String mahalleId) {
        this.ilceId = ilceId;
        this.mahalleId = mahalleId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof MahalleId that)) {
            return false;
        }
        return Objects.equals(ilceId, that.ilceId) && Objects.equals(mahalleId, that.mahalleId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(ilceId, mahalleId);
    }
}
