package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import tr.secimharitasi.loader.kontrol.BulguTuru;
import tr.secimharitasi.loader.yukleme.EksikPartiException;
import tr.secimharitasi.loader.yukleme.VeriYukleyici;
import tr.secimharitasi.loader.yukleme.YuklemeOzeti;

/** Gerçek MySQL 8.4 (Testcontainers) üzerinde Flyway + yükleme. Docker yoksa atlanır. */
@SpringBootTest(properties = {
        "veri.otomatik-calistir=false",
        "veri.dizin=src/test/resources/veri/normalized",
        "veri.kaynaklar=src/test/resources/veri/sources.yml",
        "veri.mahalle-geo=src/test/resources/veri/mahalle_geo.json"})
@Testcontainers(disabledWithoutDocker = true)
class VeriYukleyiciTest {

    @Container
    @ServiceConnection
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");

    @Autowired
    VeriYukleyici yukleyici;
    @Autowired
    JdbcTemplate jdbc;
    @Autowired
    TransactionTemplate tx;
    @Autowired
    VeriOzellikleri ozellikler;

    YuklemeOzeti ozet;

    @BeforeEach
    void yukle() {
        ozet = yukleyici.yukle();
    }

    private int say(String sql, Object... p) {
        return jdbc.queryForObject(sql, Integer.class, p);
    }

    @Test
    void satirSayilari() {
        // 3 ana seçim + 2099 belediye meclisi + 2098 Senato
        assertThat(say("SELECT count(*) FROM secim")).isEqualTo(5);
        assertThat(say("SELECT count(*) FROM il")).isEqualTo(3);
        assertThat(say("SELECT count(*) FROM ilce")).isEqualTo(3);
        assertThat(say("SELECT count(*) FROM sonuc_il")).isEqualTo(7);
        assertThat(say("SELECT count(*) FROM oy_il")).isEqualTo(14);
        assertThat(say("SELECT count(*) FROM sonuc_ilce")).isEqualTo(8);
        assertThat(say("SELECT count(*) FROM oy_ilce")).isEqualTo(12);
        assertThat(say("SELECT count(*) FROM sandalye_il")).isEqualTo(3);
        assertThat(say("SELECT count(*) FROM mahalle")).isEqualTo(2);
        assertThat(say("SELECT count(*) FROM sonuc_mahalle")).isEqualTo(2);
        assertThat(say("SELECT count(*) FROM oy_mahalle")).isEqualTo(4);
        assertThat(say("SELECT count(*) FROM sonuc_belde")).isEqualTo(3);
        assertThat(say("SELECT count(*) FROM oy_belde")).isEqualTo(6);
        assertThat(say("SELECT count(*) FROM secilen")).isEqualTo(3);
        assertThat(say("SELECT count(*) FROM kaynak_kapsami")).isEqualTo(4);
        assertThat(ozet.atlananSatir()).isEqualTo(1);
        assertThat(ozet.mahalleSatiri()).isEqualTo(2);
        assertThat(ozet.beldeSatiri()).isEqualTo(3);
        assertThat(ozet.secilenSayisi()).isEqualTo(3);
    }

    @Test
    void meclisVeSenatoOylamalari() {
        assertThat(jdbc.queryForMap("SELECT tur, oylama, ana_secim_id FROM secim WHERE secim_id='2099yerel_bm'"))
                .containsEntry("tur", "yerel").containsEntry("oylama", "belediye_meclisi")
                .containsEntry("ana_secim_id", "2099yerel");
        assertThat(jdbc.queryForMap("SELECT tur, oylama, ana_secim_id FROM secim WHERE secim_id='2098senato'"))
                .containsEntry("tur", "senato").containsEntry("oylama", "senato");
        // Senato il oyları: bağımsız aday satırı 'Bağımsız' seçeneğine
        assertThat(say("SELECT o.oy FROM oy_il o JOIN parti p USING (parti_id)"
                + " WHERE secim_id='2098senato' AND p.ad='Bağımsız'")).isEqualTo(10);
        // TÜİK ilçe satırı: doğrulanamayan seçmen boş, not düşülmüş; muteber geçerli oy
        assertThat(jdbc.queryForMap("SELECT secmen, gecerli_oy, not_metni FROM sonuc_ilce"
                + " WHERE secim_id='2098senato' AND ilce_id='TR-D-01-001'"))
                .containsEntry("secmen", null).containsEntry("gecerli_oy", 40)
                .containsEntry("not_metni", "Kaynakta doğrulanamayan alanlar boş bırakıldı: secmen");
        // Vikipedi ilçe birincisi adından eşlendi, yalnız kazanan
        assertThat(jdbc.queryForMap("SELECT sadece_kazanan, kazanan_parti_id FROM sonuc_ilce"
                + " WHERE secim_id='2098senato' AND ilce_id='TR-D-01-002'"))
                .containsEntry("sadece_kazanan", true).containsEntry("kazanan_parti_id", 38);
    }

    @Test
    void mahalleBeldeSecilen() {
        assertThat(jdbc.queryForList("SELECT mahalle_id, ad FROM mahalle ORDER BY mahalle_id"))
                .extracting(r -> r.get("mahalle_id") + "=" + r.get("ad")).containsExactly("k1=MERKEZ MAH.", "r2=null");
        assertThat(jdbc.queryForObject("SELECT katilim FROM sonuc_mahalle WHERE mahalle_id='r2'",
                java.math.BigDecimal.class)).isEqualByComparingTo("105.00");
        // Belde: adından ilçeye bağlandı; takma ad (Yeniden Refah) aynı partide toplandı
        assertThat(say("SELECT count(*) FROM sonuc_belde WHERE ilce_id IS NOT NULL")).isEqualTo(3);
        assertThat(say("SELECT o.oy FROM oy_belde o JOIN sonuc_belde b USING (sonuc_belde_id)"
                + " WHERE b.belde_ad='Tüik Belde' AND o.parti_id=102")).isEqualTo(3);
        assertThat(jdbc.queryForMap("SELECT secmen, not_metni, kontrol FROM sonuc_belde WHERE secim_id='2099yerel_bm'"))
                .containsEntry("secmen", null).containsEntry("kontrol", "tutarsiz")
                .containsEntry("not_metni", "Okunamayan değer boş bırakıldı: secmen");
        assertThat(say("SELECT count(*) FROM secilen WHERE gorev='senator'")).isEqualTo(1);
        assertThat(say("SELECT count(*) FROM secilen WHERE parti_id IS NULL")).isEqualTo(1);
        assertThat(jdbc.queryForMap("SELECT bulunan, beklenen, durum FROM kaynak_kapsami"
                + " WHERE secim_id='2098' AND veri='milletvekilleri'"))
                .containsEntry("bulunan", 2).containsEntry("beklenen", 3).containsEntry("durum", "eksik");
    }

    @Test
    void tutarsizVeriDuzeltilmedenYuklenir() {
        // Ankara 2098: seçenek toplamı 11, geçerli oy 10 — olduğu gibi kalır
        assertThat(say("SELECT gecerli_oy FROM sonuc_il WHERE secim_id='2098' AND plaka=6")).isEqualTo(10);
        assertThat(say("SELECT sum(oy) FROM oy_il WHERE secim_id='2098' AND plaka=6")).isEqualTo(11);
        assertThat(jdbc.queryForObject("SELECT katilim FROM sonuc_il WHERE secim_id='2098' AND plaka=6",
                java.math.BigDecimal.class)).isEqualByComparingTo("101.5");
        assertThat(ozet.bulgular()).containsEntry(BulguTuru.PARTI_TOPLAMI_GECERLI_OY_DEGIL, 1L)
                .containsEntry(BulguTuru.ILCE_TOPLAMI_IL_TOPLAMINDAN_FARKLI, 1L)
                .containsEntry(BulguTuru.KATILIM_100_USTU, 1L)
                .containsEntry(BulguTuru.ILCENIN_ILI_YOK, 1L);
        assertThat(say("SELECT bulgu_sayisi FROM veri_yukleme ORDER BY yukleme_id DESC LIMIT 1")).isEqualTo(4);
    }

    @Test
    void sabitPartiKimlikleriVeDevamlilik() {
        assertThat(say("SELECT parti_id FROM parti WHERE ad='CHP'")).isEqualTo(2);
        assertThat(say("SELECT kazanan_parti_id FROM sonuc_il WHERE secim_id='2098' AND plaka=1")).isEqualTo(2);
        assertThat(jdbc.queryForObject("SELECT o.ad FROM parti p JOIN parti o ON o.parti_id = p.onceki_parti_id"
                + " WHERE p.ad = 'DEM Parti'", String.class)).isEqualTo("YEŞİL SOL");
    }

    @Test
    void ilceYillariVeYurtDisi() {
        assertThat(jdbc.queryForList("SELECT baslangic_yili, bitis_yili FROM ilce WHERE ilce_id='HIST-Adana-Eski'"))
                .singleElement().satisfies(r -> {
                    assertThat(((Number) r.get("baslangic_yili")).intValue()).isEqualTo(2097);
                    assertThat(((Number) r.get("bitis_yili")).intValue()).isEqualTo(2097);
                });
        assertThat(say("SELECT baslangic_yili FROM ilce WHERE ilce_id='TR-D-01-002'")).isEqualTo(2098);
        assertThat(jdbc.queryForObject("SELECT kazanan_parti_id FROM sonuc_il WHERE secim_id='2098' AND plaka=0",
                Integer.class)).isNull();
        assertThat(jdbc.queryForObject("SELECT aday FROM oy_ilce o JOIN parti p USING (parti_id)"
                + " WHERE secim_id='2099yerel' AND p.ad='CHP'", String.class)).isEqualTo("Ayşe Yılmaz");
    }

    @Test
    void yenidenYuklemeAyniSonucuVerir() {
        yukleyici.yukle();
        assertThat(say("SELECT count(*) FROM oy_ilce")).isEqualTo(12);
        assertThat(say("SELECT count(*) FROM oy_mahalle")).isEqualTo(4);
        assertThat(say("SELECT count(*) FROM sonuc_belde")).isEqualTo(3);
        assertThat(say("SELECT count(*) FROM veri_yukleme")).isGreaterThanOrEqualTo(2);
    }

    @Test
    void kaynakDegismediyseYuklemeAtlanir() {
        int once = say("SELECT count(*) FROM veri_yukleme");
        assertThat(yukleyici.gerekirseYukle(false)).isEmpty();
        assertThat(say("SELECT count(*) FROM veri_yukleme")).isEqualTo(once);
        assertThat(yukleyici.gerekirseYukle(true)).isPresent();
        assertThat(say("SELECT count(*) FROM veri_yukleme")).isEqualTo(once + 1);
        assertThat(jdbc.queryForObject("SELECT kaynak_ozeti FROM veri_yukleme ORDER BY yukleme_id DESC LIMIT 1",
                String.class)).hasSize(64);
    }

    @Test
    void tohumdaOlmayanPartiYuklemeyiDurdururVeEskiVeriKalir() {
        VeriOzellikleri eksik = new VeriOzellikleri(Fikstur.EKSIK_PARTI_DIZINI, null, null, 0.005, 0, false, false, 5000);
        assertThatThrownBy(() -> new VeriYukleyici(jdbc, tx, eksik).yukle())
                .isInstanceOf(EksikPartiException.class)
                .hasMessageContaining("Uydurma Parti")
                .hasMessageContaining("parti_tohumu.py --eksikler");
        assertThat(say("SELECT count(*) FROM secim")).isEqualTo(5);
    }
}
