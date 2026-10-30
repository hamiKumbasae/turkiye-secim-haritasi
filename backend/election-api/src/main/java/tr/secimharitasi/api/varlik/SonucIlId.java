package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, plaka). */
public class SonucIlId implements Serializable {

    private String secimId;
    private Integer plaka;

    public SonucIlId() {
    }

    public SonucIlId(String secimId, Integer plaka) {
        this.secimId = secimId;
        this.plaka = plaka;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof SonucIlId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(plaka, that.plaka);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, plaka);
    }
}
