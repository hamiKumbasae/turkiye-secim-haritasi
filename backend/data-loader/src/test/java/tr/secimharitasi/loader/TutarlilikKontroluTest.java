package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.OyKaydi;
import tr.secimharitasi.loader.kaynak.SecimDosyasi;
import tr.secimharitasi.loader.kaynak.SonucSatiri;
import tr.secimharitasi.loader.kontrol.Bulgu;
import tr.secimharitasi.loader.kontrol.BulguTuru;
import tr.secimharitasi.loader.kontrol.TutarlilikKontrolu;

class TutarlilikKontroluTest {

    private final TutarlilikKontrolu kontrol = new TutarlilikKontrolu(0.005, 0);

    @Test
    void fiksturdekiBilinenBulgular() {
        List<Bulgu> b = kontrol.kontrolEt(Fikstur.secim("2098"), Set.of(0, 1, 6));
        assertThat(b).extracting(Bulgu::tur).containsExactlyInAnyOrder(
                BulguTuru.PARTI_TOPLAMI_GECERLI_OY_DEGIL,      // Ankara: 6 + 5 != 10
                BulguTuru.KATILIM_100_USTU,                    // Ankara: %101,5
                BulguTuru.ILCENIN_ILI_YOK,                     // plaka 99
                BulguTuru.ILCE_TOPLAMI_IL_TOPLAMINDAN_FARKLI); // Adana: ilçeler 90, il 100
        assertThat(b).filteredOn(Bulgu::satirAtlanir).extracting(Bulgu::yer)
                .containsExactly("Hayalet (TR-D-99-001)");
        assertThat(b).filteredOn(x -> x.tur() == BulguTuru.PARTI_TOPLAMI_GECERLI_OY_DEGIL)
                .first().extracting(Bulgu::ayrinti).asString().contains("+1");
    }

    @Test
    void tutarliSecimdeBulguYok() {
        assertThat(kontrol.kontrolEt(Fikstur.secim("2097"), Set.of(1))).isEmpty();
    }

    @Test
    void yerelSecimdeIlceToplamiKarsilastirilmaz() {
        // 2099 yerel: il (büyükşehir) 100, tek ilçe 30 — farklı yarışmalar
        assertThat(kontrol.kontrolEt(Fikstur.secim("2099yerel"), Set.of(1))).isEmpty();
    }

    @Test
    void oyuBosSecenekVeYalnizKazananSatirlariKarsilastirilmaz() {
        Map<String, OyKaydi> bosOy = new LinkedHashMap<>();
        bosOy.put("CHP", new OyKaydi(null, null, null));
        SonucSatiri oyuBos = satir(1, 10, "CHP", bosOy, false);
        SonucSatiri yalnizKazanan = satir(1, 10, "CHP", Map.of("CHP", new OyKaydi(3L, null, null)), true);
        assertThat(kontrol.kontrolEt(secim(List.of(oyuBos), List.of()), Set.of(1))).isEmpty();
        assertThat(kontrol.kontrolEt(secim(List.of(yalnizKazanan), List.of()), Set.of(1))).isEmpty();
    }

    @Test
    void toleransIcindekiFarkBulguDegil() {
        SonucSatiri il = satir(1, 1000, "CHP", Map.of("CHP", new OyKaydi(1001L, null, null)), false);
        SonucSatiri ilce = new SonucSatiri(1, "A", "TR-D-01-001", null, null, 996, null, null, null, "CHP", null,
                null, null, null, null, null, Map.of("CHP", new OyKaydi(996L, null, null)), null);
        TutarlilikKontrolu gevsek = new TutarlilikKontrolu(0.005, 1);
        // il: 1001 vs 1000, 1 oy tolerans; ilçe 996 vs il 1000 -> %0,4 < %0,5
        assertThat(gevsek.kontrolEt(secim(List.of(il), List.of(ilce)), Set.of(1))).isEmpty();
        assertThat(kontrol.kontrolEt(secim(List.of(il), List.of(ilce)), Set.of(1)))
                .extracting(Bulgu::tur).containsExactly(BulguTuru.PARTI_TOPLAMI_GECERLI_OY_DEGIL);
    }

    @Test
    void kazananOyListesindeYoksaVeYinelenenSatir() {
        SonucSatiri il = satir(1, 10, "MHP", Map.of("CHP", new OyKaydi(10L, null, null)), false);
        List<Bulgu> b = kontrol.kontrolEt(secim(List.of(il, il), List.of()), Set.of(1));
        assertThat(b).extracting(Bulgu::tur)
                .containsExactlyInAnyOrder(BulguTuru.KAZANAN_OYLARDA_YOK, BulguTuru.YINELENEN_SATIR);
    }

    private static SonucSatiri satir(int plaka, int gecerli, String kazanan, Map<String, OyKaydi> oy,
                                     boolean yalnizKazanan) {
        return new SonucSatiri(plaka, "İl" + plaka, null, null, null, gecerli, null, null, BigDecimal.TEN, kazanan,
                null, null, yalnizKazanan, null, null, null, oy, null);
    }

    private static KaynakSecim secim(List<SonucSatiri> iller, List<SonucSatiri> ilceler) {
        return new KaynakSecim("2000", 2000, SecimTuru.GENEL,
                new SecimDosyasi("x", "genel", null, null, null, iller, ilceler, null), null, null);
    }
}
