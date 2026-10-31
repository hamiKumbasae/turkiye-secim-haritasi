package tr.secimharitasi.loader.kaynak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

/**
 * Bir seçim dosyasının kendisi (elections/&lt;tur&gt;/&lt;secim&gt;.json). meclis_harita/*.json da aynı biçimdedir
 * (aciklama ve oylamaAdi alanlarıyla).
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record SecimDosyasi(
        String ad,
        String tur,
        String aciklama,
        String oylamaAdi,
        String contestType,
        String resultBasis,
        Integer toplamSandalye,
        List<SonucSatiri> iller,
        List<SonucSatiri> ilceler,
        YurtDisi yurtdisi) {

    public SecimDosyasi {
        iller = iller == null ? List.of() : List.copyOf(iller);
        ilceler = ilceler == null ? List.of() : List.copyOf(ilceler);
    }
}
