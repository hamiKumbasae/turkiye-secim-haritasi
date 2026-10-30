package tr.secimharitasi.loader.yukleme;

import java.util.Map;
import tr.secimharitasi.loader.kontrol.BulguTuru;

/**
 * @param secim       yüklenen oylama sayısı (ana seçimler + meclis + Senato + ara seçimler)
 * @param atlananSatir anahtar ihlali nedeniyle yazılamayan satır
 */
public record YuklemeOzeti(int secim, int ilSatiri, int ilceSatiri, int oySatiri, int ilSayisi, int ilceSayisi,
                           int mahalleSatiri, int beldeSatiri, int secilenSayisi, Map<BulguTuru, Long> bulgular,
                           int atlananSatir) {

    public long bulguSayisi() {
        return bulgular.values().stream().mapToLong(Long::longValue).sum();
    }
}
