package tr.secimharitasi.loader.kaynak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

/** Bir seçim dosyasının kendisi (elections/&lt;tur&gt;/&lt;secim&gt;.json). */
@JsonIgnoreProperties(ignoreUnknown = true)
public record SecimDosyasi(
        String ad,
        String tur,
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
