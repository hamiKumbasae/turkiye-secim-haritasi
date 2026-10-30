package tr.secimharitasi.api.varlik;

import java.io.Serializable;
import java.util.Objects;

/** Bileşik birincil anahtar (secim_id, ilce_id, parti_id). */
public class OyIlceId implements Serializable {

    private String secimId;
    private String ilceId;
    private Integer partiId;

    public OyIlceId() {
    }

    public OyIlceId(String secimId, String ilceId, Integer partiId) {
        this.secimId = secimId;
        this.ilceId = ilceId;
        this.partiId = partiId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof OyIlceId that)) {
            return false;
        }
        return Objects.equals(secimId, that.secimId) && Objects.equals(ilceId, that.ilceId) && Objects.equals(partiId, that.partiId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(secimId, ilceId, partiId);
    }
}
