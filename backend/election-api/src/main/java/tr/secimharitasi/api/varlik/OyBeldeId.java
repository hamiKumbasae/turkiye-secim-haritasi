package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (sonuc_belde_id, parti_id). */
public class OyBeldeId implements Serializable {

    private Integer sonucBeldeId;
    private Integer partiId;

    public OyBeldeId() {
    }

    public OyBeldeId(Integer sonucBeldeId, Integer partiId) {
        this.sonucBeldeId = sonucBeldeId;
        this.partiId = partiId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof OyBeldeId that)) {
            return false;
        }
        return Objects.equals(sonucBeldeId, that.sonucBeldeId) && Objects.equals(partiId, that.partiId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(sonucBeldeId, partiId);
    }
}
