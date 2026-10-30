package tr.secimharitasi.loader.yukleme;

import java.util.Map;
import tr.secimharitasi.loader.kontrol.BulguTuru;

public record YuklemeOzeti(int secim, int ilSatiri, int ilceSatiri, int oySatiri, int ilSayisi, int ilceSayisi,
                           Map<BulguTuru, Long> bulgular, int atlananSatir) {

    public long bulguSayisi() {
        return bulgular.values().stream().mapToLong(Long::longValue).sum();
    }
}
