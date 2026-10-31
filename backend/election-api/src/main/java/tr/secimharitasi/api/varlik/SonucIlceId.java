package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, ilce_id). */
public class SonucIlceId implements Serializable {

    private String secimId;
    private String ilceId;

    public SonucIlceId() {
    }

    public SonucIlceId(String secimId, String ilceId) {
        this.secimId = secimId;
        this.ilceId = ilceId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof SonucIlceId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(ilceId, that.ilceId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, ilceId);
    }
}
