package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, plaka, parti_id). */
public class OyIlId implements Serializable {

    private String secimId;
    private Integer plaka;
    private Integer partiId;

    public OyIlId() {
    }

    public OyIlId(String secimId, Integer plaka, Integer partiId) {
        this.secimId = secimId;
        this.plaka = plaka;
        this.partiId = partiId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof OyIlId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(plaka, that.plaka) && Objects.equals(partiId, that.partiId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, plaka, partiId);
    }
}
