package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.loader.ek.MahalleOkuyucu;
import tr.secimharitasi.loader.ek.MahalleSatiri;

class MahalleOkuyucuTest {

    private final MahalleOkuyucu okuyucu = new MahalleOkuyucu(Fikstur.DIZIN, Fikstur.MAHALLE_GEO);

    @Test
    void secimlerVeSatirlar() {
        assertThat(okuyucu.secimler()).containsExactly("2098");
        List<MahalleSatiri> s = okuyucu.oku("2098");
        assertThat(s).extracting(MahalleSatiri::mahalleId).containsExactly("k1", "r2");
        assertThat(s.get(1).katilim()).as("%100 üstü olduğu gibi").isEqualByComparingTo("105.0");
        assertThat(s.get(0).oy().get("CHP").oy()).isEqualTo(15L);
        assertThat(s.get(0).oy().get("CHP").oran()).isEqualByComparingTo("60.0");
    }

    @Test
    void adlarGeometriAtlanarakOkunur() {
        assertThat(okuyucu.adlar())
                .containsEntry(MahalleOkuyucu.anahtar("TR-D-01-001", "k1"), "MERKEZ MAH.")
                .containsEntry(MahalleOkuyucu.anahtar("TR-D-01-001", "x9"), "BAŞKA KÖY")
                .hasSize(2);
    }

    @Test
    void dosyaYoksaBos() {
        MahalleOkuyucu bos = new MahalleOkuyucu(Path.of("yok"), null);
        assertThat(bos.secimler()).isEmpty();
        assertThat(bos.adlar()).isEmpty();
    }
}
