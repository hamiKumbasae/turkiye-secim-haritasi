package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.loader.kaynak.KaynakOkuyucu;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.SonucSatiri;

class KaynakOkuyucuTest {

    @Test
    void secimlerKronolojikOkunur() {
        List<KaynakSecim> s = Fikstur.secimler();
        assertThat(s).extracting(KaynakSecim::secimId).containsExactly("2097", "2098", "2099yerel");
        assertThat(s).extracting(KaynakSecim::tur)
                .containsExactly(SecimTuru.GENEL, SecimTuru.GENEL, SecimTuru.YEREL);
    }

    @Test
    void alanlarVeKaynakBilgisiOkunur() {
        KaynakSecim s = Fikstur.secim("2098");
        assertThat(s.birincilKaynak()).isEqualTo("YSK");
        assertThat(s.kaynakDurumu()).isEqualTo("official");
        assertThat(s.dosya().ad()).isEqualTo("1 Ocak 2098");

        SonucSatiri adana = s.dosya().iller().get(0);
        assertThat(adana.gecerliOy()).isEqualTo(100);
        assertThat(adana.katilim()).isEqualByComparingTo("87.5");
        assertThat(adana.oy().get("CHP").oy()).isEqualTo(60L);
        assertThat(adana.vekil()).containsEntry("AK Parti", 1);
        assertThat(s.dosya().iller().get(1).notlar()).isEqualTo("Test: oy toplamı geçerli oyu tutmuyor");
        assertThat(s.dosya().yurtdisi().kullanilanOy()).isEqualTo(20);

        KaynakSecim yerel = Fikstur.secim("2099yerel");
        assertThat(yerel.birincilKaynak()).isNull();
        assertThat(yerel.dosya().ilceler().get(0).oy().get("CHP").aday()).isEqualTo("Ayşe Yılmaz");
    }

    @Test
    void bosYerTutucuSatirTaninir() {
        SonucSatiri ceyhan2097 = Fikstur.secim("2097").dosya().ilceler().get(1);
        assertThat(ceyhan2097.bosYerTutucu()).isTrue();
        assertThat(Fikstur.secim("2098").dosya().ilceler().get(1).bosYerTutucu()).isFalse();
    }

    @Test
    void geomIdYoksaSabitAnahtarUretilir() {
        SonucSatiri r = new SonucSatiri(7, "Merkez", null, null, null, null, null, null, null, null, null, null,
                null, null, null, null, null, null);
        assertThat(r.ilceId()).isEqualTo("YOK-07-Merkez");
        assertThat(r.oy()).isEmpty();
    }

    @Test
    void klasorYoksaAnlasilirHata() {
        assertThatThrownBy(() -> new KaynakOkuyucu(Path.of("yok/boyle/bir/yer"), null).oku())
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Seçim klasörü bulunamadı");
    }
}
