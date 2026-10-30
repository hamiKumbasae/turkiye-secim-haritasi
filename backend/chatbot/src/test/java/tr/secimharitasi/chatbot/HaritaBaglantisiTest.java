package tr.secimharitasi.chatbot;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import tr.secimharitasi.chatbot.arac.HaritaBaglantisi;

class HaritaBaglantisiTest {

    static final String KOK = "https://hamikumbasae.github.io/turkiye-secim-haritasi/";

    @Test
    void genelSecimIlVeParti() {
        assertThat(HaritaBaglantisi.olustur(KOK, "1977", 34, null, "CHP", "parti"))
                .isEqualTo(KOK + "#secim=1977&il=34&mod=parti&parti=CHP");
    }

    @Test
    void meclisOylamasiVeIlce() {
        assertThat(HaritaBaglantisi.olustur(KOK, "2024yerel_bm", 6, "TR-D-06-007", null, null))
                .isEqualTo(KOK + "#secim=2024yerel&oylama=bm&il=6&ilce=TR-D-06-007");
    }

    @Test
    void katilimModundaPartiYok() {
        assertThat(HaritaBaglantisi.olustur("https://ornek.tr", "2023", null, "TR-D-06-007", "CHP", "katilim"))
                .isEqualTo("https://ornek.tr/#secim=2023&mod=katilim");
    }

    @Test
    void ozelKarakterlerKodlanir() {
        assertThat(HaritaBaglantisi.olustur(KOK, "2023", null, null, "AK Parti", "parti"))
                .endsWith("mod=parti&parti=AK+Parti");
    }

    @Test
    void haritadaOlmayanSecimler() {
        assertThat(HaritaBaglantisi.olustur(KOK, "1961senato", null, null, null, null)).isNull();
        assertThat(HaritaBaglantisi.olustur(KOK, "2019istanbul_bb_yenileme", 34, null, null, null)).isNull();
        assertThat(HaritaBaglantisi.olustur(KOK, "2023'><script>", null, null, null, null)).isNull();
    }

    @Test
    void cumhurbaskanligiVeReferandum() {
        assertThat(HaritaBaglantisi.olustur(KOK, "2023cb2tur", null, null, null, "gecersiz"))
                .isEqualTo(KOK + "#secim=2023cb2tur");
        assertThat(HaritaBaglantisi.olustur(KOK, "2017referandum", 0, null, null, null))
                .isEqualTo(KOK + "#secim=2017referandum");
    }
}
