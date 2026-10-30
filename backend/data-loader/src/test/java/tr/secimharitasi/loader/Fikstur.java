package tr.secimharitasi.loader;

import java.nio.file.Path;
import java.util.List;
import tr.secimharitasi.loader.kaynak.KaynakOkuyucu;
import tr.secimharitasi.loader.kaynak.KaynakSecim;

/** src/test/resources/veri altındaki küçük test verisi (2097, 2098 genel, 2099 yerel). */
public final class Fikstur {

    public static final Path DIZIN = Path.of("src/test/resources/veri/normalized");
    public static final Path KAYNAKLAR = Path.of("src/test/resources/veri/sources.yml");
    public static final Path EKSIK_PARTI_DIZINI = Path.of("src/test/resources/veri-eksik-parti/normalized");

    private Fikstur() {
    }

    public static List<KaynakSecim> secimler() {
        return new KaynakOkuyucu(DIZIN, KAYNAKLAR).oku();
    }

    public static KaynakSecim secim(String id) {
        return secimler().stream().filter(s -> s.secimId().equals(id)).findFirst().orElseThrow();
    }
}
