package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import tr.secimharitasi.loader.yukleme.KaynakOzeti;

class KaynakOzetiTest {

    @Test
    void ayniKaynakAyniOzet(@TempDir Path d) throws Exception {
        Path n = Files.createDirectories(d.resolve("normalized/elections/genel"));
        Files.writeString(n.resolve("2023.json"), "{\"a\": 1}");
        Path src = Files.writeString(d.resolve("sources.yml"), "x: 1");
        String o1 = KaynakOzeti.hesapla(d.resolve("normalized"), src, null);
        assertThat(o1).hasSize(64).isEqualTo(KaynakOzeti.hesapla(d.resolve("normalized"), src, null));

        Files.writeString(n.resolve("2023.json"), "{\"a\": 2}");
        String o2 = KaynakOzeti.hesapla(d.resolve("normalized"), src, null);
        assertThat(o2).isNotEqualTo(o1);

        Files.writeString(n.resolve("2024.json"), "{}");
        assertThat(KaynakOzeti.hesapla(d.resolve("normalized"), src, null)).isNotEqualTo(o2);
        assertThat(KaynakOzeti.hesapla(d.resolve("yok"), null, null)).hasSize(64);
    }
}
