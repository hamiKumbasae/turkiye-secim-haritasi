package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import tr.secimharitasi.loader.yukleme.BoyutTablolari;
import tr.secimharitasi.loader.yukleme.BoyutTablolari.Ilce;

class BoyutTablolariTest {

    private final BoyutTablolari boyut = BoyutTablolari.olustur(Fikstur.secimler());

    @Test
    void illerSonAdlarlaVeYurtDisiyla() {
        assertThat(boyut.iller()).containsEntry(1, "Adana").containsEntry(6, "Ankara")
                .containsEntry(0, BoyutTablolari.YURT_DISI).hasSize(3);
    }

    @Test
    void ilceYillari() {
        // Tarihsel birim: yalnız 2097'de var
        assertThat(boyut.ilceler().get("HIST-Adana-Eski"))
                .isEqualTo(new Ilce("HIST-Adana-Eski", 1, "Eski Merkez", false, 2097, 2097));
        // 2097'deki boş yer tutucu satır sayılmaz: başlangıç 2098; güncel ilçe, bitiş yok
        assertThat(boyut.ilceler().get("TR-D-01-002"))
                .isEqualTo(new Ilce("TR-D-01-002", 1, "Ceyhan", true, 2098, null));
        assertThat(boyut.ilceler().get("TR-D-01-001").baslangicYili()).isEqualTo(2098);
    }

    @Test
    void iliOlmayanIlceBoyutaGirmez() {
        assertThat(boyut.ilceler()).doesNotContainKey("TR-D-99-001").hasSize(3);
    }
}
