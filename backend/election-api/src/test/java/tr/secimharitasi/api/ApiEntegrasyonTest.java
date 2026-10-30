package tr.secimharitasi.api;

import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

/**
 * Gerçek MySQL 8.4 üzerinde uçtan uca: şema data-loader'ın Flyway dosyalarından kurulur (aynı V1-V3), küçük bir
 * test verisi eklenir, uç noktalar çağrılır. Docker yoksa atlanır.
 */
@SpringBootTest(properties = {
        "spring.flyway.enabled=true",
        "spring.flyway.locations=filesystem:../data-loader/src/main/resources/db/migration",
        "spring.datasource.hikari.read-only=false"})
@AutoConfigureMockMvc
@Testcontainers(disabledWithoutDocker = true)
@Sql(scripts = "/test-verisi.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_CLASS)
class ApiEntegrasyonTest {

    @Container
    @ServiceConnection
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4");

    @Autowired
    MockMvc mvc;

    @Test
    void secimlerTureVeYilaGoreSuzulur() throws Exception {
        mvc.perform(get("/api/secimler").param("tur", "genel")).andExpect(status().isOk())
                .andExpect(jsonPath("$[*].secimId", contains("2018", "2023")))
                .andExpect(jsonPath("$[0].tur").value("genel"))
                .andExpect(jsonPath("$[0].birincilKaynak").value("YSK"));
        mvc.perform(get("/api/secimler").param("yil", "2024"))
                .andExpect(jsonPath("$[*].secimId", contains("2024yerel", "2024yerel_bm")));
        mvc.perform(get("/api/secimler").param("oylama", "belediye_meclisi"))
                .andExpect(jsonPath("$[*].secimId", contains("2024yerel_bm")))
                .andExpect(jsonPath("$[0].anaSecimId").value("2024yerel"))
                .andExpect(jsonPath("$[0].oylama").value("belediye_meclisi"));
        mvc.perform(get("/api/secimler/2024yerel/bagli-oylamalar"))
                .andExpect(jsonPath("$[*].secimId", contains("2024yerel_bm")));
        mvc.perform(get("/api/secimler").param("yilBaslangic", "2019").param("yilBitis", "2023"))
                .andExpect(jsonPath("$[*].secimId", contains("2023")));
    }

    @Test
    void ilSonuclariOylarlaBirlikte() throws Exception {
        mvc.perform(get("/api/secimler/2023/iller")).andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(3)))
                .andExpect(jsonPath("$[0].plaka").value(0))
                .andExpect(jsonPath("$[0].kazanan").doesNotExist());
        mvc.perform(get("/api/secimler/2023/iller/34")).andExpect(status().isOk())
                .andExpect(jsonPath("$.ad").value("İstanbul"))
                .andExpect(jsonPath("$.kazanan").value("CHP"))
                .andExpect(jsonPath("$.oylar[*].parti", contains("CHP", "AK Parti", "YEŞİL SOL")))
                .andExpect(jsonPath("$.oylar[0].oran").value(45.0));
    }

    @Test
    void ilceSonuclari() throws Exception {
        mvc.perform(get("/api/secimler/2023/iller/34/ilceler")).andExpect(status().isOk())
                .andExpect(jsonPath("$[*].ad", contains("Adalar", "Ümraniye")))
                .andExpect(jsonPath("$[1].kazanan").value("AK Parti"))
                .andExpect(jsonPath("$[1].oylar[0].oy").value(160));
        mvc.perform(get("/api/secimler/2023/ilceler/TR-D-34-037")).andExpect(status().isOk())
                .andExpect(jsonPath("$.ilceId").value("TR-D-34-037"));
    }

    @Test
    void ilcelerYilaGoreVeridekiBirimler() throws Exception {
        mvc.perform(get("/api/iller/34/ilceler").param("yil", "1990"))
                .andExpect(jsonPath("$[*].ilceId", containsInAnyOrder("TR-D-34-001", "HIST-Istanbul-Umraniye-fb42ce")));
        mvc.perform(get("/api/iller/34/ilceler").param("yil", "2023"))
                .andExpect(jsonPath("$[*].ilceId", containsInAnyOrder("TR-D-34-001", "TR-D-34-037")))
                .andExpect(jsonPath("$[?(@.ilceId=='TR-D-34-037')].baslangicYili").value(2009));
        mvc.perform(get("/api/iller/34/ilceler")).andExpect(jsonPath("$", hasSize(3)));
    }

    @Test
    void partiDevamliligi() throws Exception {
        mvc.perform(get("/api/partiler/107")).andExpect(status().isOk())
                .andExpect(jsonPath("$.ad").value("DEM Parti"))
                .andExpect(jsonPath("$.oncekiPartiId").value(103))
                .andExpect(jsonPath("$.gecisTuru").value("ad_degisikligi"))
                .andExpect(jsonPath("$.oncekiler[0].ad").value("YEŞİL SOL"));
        // zincir=true: öncülün sonuçları kendi adıyla gelir
        mvc.perform(get("/api/partiler/107/sonuclar").param("zincir", "true"))
                .andExpect(jsonPath("$[*].parti", contains("YEŞİL SOL", "DEM Parti")))
                .andExpect(jsonPath("$[0].oran").value(10.0))
                .andExpect(jsonPath("$[1].oran").value(10.0));
        mvc.perform(get("/api/partiler/107/sonuclar")).andExpect(jsonPath("$", hasSize(1)));
    }

    @Test
    void partiTurkiyeGeneliVeIlBazinda() throws Exception {
        // 2023: CHP yurt içi 450 + 200 = 650, geçerli 1500 -> %43,33 (yurt dışı hariç)
        mvc.perform(get("/api/partiler/2/sonuclar").param("tur", "genel")).andExpect(status().isOk())
                .andExpect(jsonPath("$[*].secimId", contains("2018", "2023")))
                .andExpect(jsonPath("$[1].oy").value(650))
                .andExpect(jsonPath("$[1].gecerliOy").value(1500))
                .andExpect(jsonPath("$[1].oran").value(43.33))
                .andExpect(jsonPath("$[1].plaka").doesNotExist());
        mvc.perform(get("/api/partiler/2/sonuclar").param("plaka", "34"))
                .andExpect(jsonPath("$[*].secimId", contains("2018", "2023", "2024yerel")))
                .andExpect(jsonPath("$[2].oran").value(51.0));
        mvc.perform(get("/api/partiler/38/secimler/2023/en-guclu-iller").param("limit", "1"))
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].yer").value("Ankara"));
    }

    @Test
    void mahalleler() throws Exception {
        // seçmene göre büyükten küçüğe; ad yoksa null; katılım %100 üstü olduğu gibi
        mvc.perform(get("/api/secimler/2023/ilceler/TR-D-34-037/mahalleler")).andExpect(status().isOk())
                .andExpect(jsonPath("$[*].mahalleId", contains("r2", "k1")))
                .andExpect(jsonPath("$[0].ad").doesNotExist())
                .andExpect(jsonPath("$[0].katilim").value(101.5))
                .andExpect(jsonPath("$[0].kazanan").value("AK Parti"))
                .andExpect(jsonPath("$[1].ad").value("FİNANSKENT MAH."))
                .andExpect(jsonPath("$[1].oylar[0].parti").value("CHP"));
        mvc.perform(get("/api/secimler/2018/ilceler/TR-D-34-037/mahalleler")).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void beldelerSecilenlerSandalyelerKapsam() throws Exception {
        mvc.perform(get("/api/secimler/2024yerel/beldeler").param("plaka", "34")).andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].beldeAd").value("Deneme Beldesi"))
                .andExpect(jsonPath("$[0].kazanan").value("CHP"))
                .andExpect(jsonPath("$[0].oylar[*].oy", contains(60, 40)));
        mvc.perform(get("/api/secimler/2024yerel/beldeler"))
                .andExpect(jsonPath("$[?(@.beldeAd=='Öteki Belde')].sadeceKazanan").value(true));
        mvc.perform(get("/api/secimler/2023/secilenler").param("plaka", "34"))
                .andExpect(jsonPath("$[*].ad", contains("Bir Vekil", "İki Vekil")))
                .andExpect(jsonPath("$[0].parti").value("CHP"))
                .andExpect(jsonPath("$[0].il").value("İstanbul"))
                .andExpect(jsonPath("$[1].parti").doesNotExist());
        mvc.perform(get("/api/secimler/2023/secilenler")).andExpect(jsonPath("$", hasSize(3)));
        mvc.perform(get("/api/secimler/2023/sandalyeler").param("plaka", "34"))
                .andExpect(jsonPath("$[*].sandalye", contains(50, 48)));
        mvc.perform(get("/api/secimler/2024yerel_bm/sandalyeler").param("ilceId", "TR-D-34-037"))
                .andExpect(jsonPath("$[*].parti", contains("AK Parti", "CHP")))
                .andExpect(jsonPath("$[0].ilceId").value("TR-D-34-037"));
        mvc.perform(get("/api/secimler/2024yerel_bm/sandalyeler").param("plaka", "34"))
                .andExpect(jsonPath("$", hasSize(2)));
        mvc.perform(get("/api/secimler/2023/kapsam"))
                .andExpect(jsonPath("$[0].veri").value("milletvekilleri"))
                .andExpect(jsonPath("$[0].durum").value("eksik"))
                .andExpect(jsonPath("$[0].beklenen").value(600));
        mvc.perform(get("/api/secimler/9999/beldeler")).andExpect(status().isNotFound());
    }

    @Test
    void hatalarVeSaltOkunurluk() throws Exception {
        mvc.perform(get("/api/secimler/9999")).andExpect(status().isNotFound())
                .andExpect(jsonPath("$.mesaj").value("Seçim bulunamadı: 9999"));
        mvc.perform(get("/api/secimler").param("tur", "muhtarlik")).andExpect(status().isBadRequest());
        mvc.perform(get("/api/secimler").param("oylama", "yok")).andExpect(status().isBadRequest());
        mvc.perform(get("/api/partiler/99999")).andExpect(status().isNotFound());
        mvc.perform(delete("/api/secimler/2023")).andExpect(status().isMethodNotAllowed());
    }
}
