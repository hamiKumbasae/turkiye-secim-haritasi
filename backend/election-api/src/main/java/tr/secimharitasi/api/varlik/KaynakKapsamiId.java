package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, veri). */
public class KaynakKapsamiId implements Serializable {

    private String secimId;
    private String veri;

    public KaynakKapsamiId() {
    }

    public KaynakKapsamiId(String secimId, String veri) {
        this.secimId = secimId;
        this.veri = veri;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof KaynakKapsamiId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(veri, that.veri);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, veri);
    }
}
