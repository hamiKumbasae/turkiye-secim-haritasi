package tr.secimharitasi.loader;

import java.nio.file.Path;
import java.util.List;
import tr.secimharitasi.loader.kaynak.KaynakOkuyucu;
import tr.secimharitasi.loader.kaynak.KaynakSecim;

/**
 * src/test/resources/veri altındaki küçük test verisi: 2097, 2098 genel, 2099 yerel; 2099 belediye meclisi;
 * ek kayıtlar (2098 milletvekilleri, 2098 Senato, 2099 beldeler ve meclis beldeleri); 2098 mahalle sonuçları.
 */
public final class Fikstur {

    public static final Path DIZIN = Path.of("src/test/resources/veri/normalized");
    public static final Path KAYNAKLAR = Path.of("src/test/resources/veri/sources.yml");
    public static final Path MAHALLE_GEO = Path.of("src/test/resources/veri/mahalle_geo.json");
    public static final Path EKSIK_PARTI_DIZINI = Path.of("src/test/resources/veri-eksik-parti/normalized");

    private Fikstur() {
    }

    public static List<KaynakSecim> secimler() {
        return new KaynakOkuyucu(DIZIN, KAYNAKLAR).oku();
    }

    /** Ana seçimler ve meclis oylamaları (ek kayıt okuyucusunun girdisi). */
    public static List<KaynakSecim> anaVeMeclis() {
        KaynakOkuyucu o = new KaynakOkuyucu(DIZIN, KAYNAKLAR);
        List<KaynakSecim> l = new java.util.ArrayList<>(o.oku());
        l.addAll(o.meclisler());
        return l;
    }

    public static KaynakSecim secim(String id) {
        return secimler().stream().filter(s -> s.secimId().equals(id)).findFirst().orElseThrow();
    }
}
