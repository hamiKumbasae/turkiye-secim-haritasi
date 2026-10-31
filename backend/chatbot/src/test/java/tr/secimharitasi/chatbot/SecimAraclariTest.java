package tr.secimharitasi.chatbot;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withResourceNotFound;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;
import tr.secimharitasi.chatbot.arac.AracHatasi;
import tr.secimharitasi.chatbot.arac.AracKutusu;
import tr.secimharitasi.chatbot.arac.AracSonucu;
import tr.secimharitasi.chatbot.arac.SecimAraclari;

/** Araçlar: doğru election-api sorgusu, kırpma, hata dönüşümü (sahte HTTP sunucusu). */
class SecimAraclariTest {

    static final String API = "http://election-api";
    final ObjectMapper json = new ObjectMapper();
    MockRestServiceServer sunucu;
    AracKutusu kutu;

    @BeforeEach
    void kur() {
        RestClient.Builder b = RestClient.builder();
        sunucu = MockRestServiceServer.bindTo(b).build();
        kutu = new SecimAraclari(b, API, json, "https://harita.example/").kutu();
    }

    JsonNode girdi(String s) throws Exception {
        return json.readTree(s);
    }

    void yanit(String yol, String govde) {
        sunucu.expect(requestTo(API + yol)).andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess(govde, MediaType.APPLICATION_JSON));
    }

    @Test
    void tanimlarAnthropicBiciminde() {
        assertThat(kutu.adlar()).contains("secimleri_listele", "yer_ara", "parti_ara", "il_sonuclari",
                "ilce_sonuclari", "ilce_sonucu", "mahalle_sonuclari", "parti_sonuclari", "en_guclu_iller",
                "secilenler", "beldeler", "sandalyeler", "harita_baglantisi");
        for (JsonNode t : kutu.tanimlar()) {
            assertThat(t.path("name").asText()).matches("[a-z_]{1,64}");
            assertThat(t.path("description").asText()).isNotBlank();
            assertThat(t.path("input_schema").path("type").asText()).isEqualTo("object");
            assertThat(t.path("input_schema").path("properties").isObject()).isTrue();
        }
    }

    @Test
    void yerAramaTurkceKarakterleriKodlar() throws Exception {
        yanit("/api/iller/ara?ad=%C3%9Cmraniye&yil=2023",
                "{\"aranan\":\"Ümraniye\",\"iller\":[],\"ilceler\":[{\"ilceId\":\"TR-D-34-037\",\"plaka\":34,\"ad\":\"Ümraniye\"}]}");
        AracSonucu s = kutu.calistir("yer_ara", girdi("{\"ad\":\"Ümraniye\",\"yil\":2023}"));
        assertThat(s.veri().path("ilceler").get(0).path("ilceId").asText()).isEqualTo("TR-D-34-037");
        assertThat(s.sorgu()).isEqualTo("/api/iller/ara?ad=%C3%9Cmraniye&yil=2023");
        sunucu.verify();
    }

    @Test
    void partiAramaKisaltmaVeTurkceHarf() throws Exception {
        String partiler = """
                [{"partiId":2,"ad":"CHP","kisa":"CHP","tip":"parti"},
                 {"partiId":38,"ad":"AK Parti","kisa":"AKP","tip":"parti"},
                 {"partiId":103,"ad":"YEŞİL SOL","kisa":"YSP","tip":"parti"},
                 {"partiId":107,"ad":"DEM Parti","kisa":"DEM","tip":"parti","oncekiPartiId":103}]""";
        yanit("/api/partiler", partiler);
        yanit("/api/partiler", partiler);
        yanit("/api/partiler", partiler);

        JsonNode akp = kutu.calistir("parti_ara", girdi("{\"ad\":\"akp\"}")).veri();
        assertThat(akp).hasSize(1);
        assertThat(akp.get(0).path("partiId").asInt()).isEqualTo(38);

        JsonNode yesil = kutu.calistir("parti_ara", girdi("{\"ad\":\"yesil sol\"}")).veri();
        assertThat(yesil.get(0).path("ad").asText()).isEqualTo("YEŞİL SOL");

        JsonNode parti = kutu.calistir("parti_ara", girdi("{\"ad\":\"parti\"}")).veri();
        assertThat(parti).hasSize(2);
        sunucu.verify();
    }

    @Test
    void ilceSonuclariIlkBesSecenegeKirpilir() throws Exception {
        StringBuilder oylar = new StringBuilder();
        for (int i = 0; i < 9; i++) {
            oylar.append(i == 0 ? "" : ",").append("{\"partiId\":").append(i + 1).append(",\"parti\":\"P").append(i)
                    .append("\",\"kisa\":\"P\",\"oy\":").append(1000 - i).append(",\"oran\":").append(10 - i).append('}');
        }
        yanit("/api/secimler/1977/iller/34/ilceler",
                "[{\"secimId\":\"1977\",\"ilceId\":\"TR-D-34-008\",\"plaka\":34,\"ad\":\"Beşiktaş\",\"katilim\":80.1,"
                        + "\"kazanan\":\"CHP\",\"baskan\":null,\"oylar\":[" + oylar + "]}]");
        JsonNode v = kutu.calistir("ilce_sonuclari", girdi("{\"secim_id\":\"1977\",\"plaka\":34}")).veri();
        JsonNode ilce = v.get(0);
        assertThat(ilce.path("oylar")).hasSize(5);
        assertThat(ilce.path("oylar").get(0).has("partiId")).isFalse();
        assertThat(ilce.path("oylar").get(0).path("oran").asInt()).isEqualTo(10);
        assertThat(ilce.path("digerSecenekSayisi").asInt()).isEqualTo(4);
        assertThat(ilce.has("baskan")).isFalse();
        sunucu.verify();
    }

    @Test
    void mahallelerPartiOraninaGoreSiralanir() throws Exception {
        yanit("/api/secimler/2023/ilceler/TR-D-34-037/mahalleler", """
                [{"ad":"A MAH.","oylar":[{"parti":"AK Parti","oran":60},{"parti":"CHP","oran":30}]},
                 {"ad":"FİNANSKENT MAH.","oylar":[{"parti":"AK Parti","oran":40},{"parti":"CHP","oran":49.04}]},
                 {"ad":"C MAH.","oylar":[{"parti":"AK Parti","oran":50}]}]""");
        JsonNode v = kutu.calistir("mahalle_sonuclari",
                girdi("{\"secim_id\":\"2023\",\"ilce_id\":\"TR-D-34-037\",\"parti\":\"chp\"}")).veri();
        assertThat(v.path("mahalleSayisi").asInt()).isEqualTo(3);
        assertThat(v.path("mahalleler").get(0).path("ad").asText()).isEqualTo("FİNANSKENT MAH.");
        assertThat(v.path("mahalleler").get(2).path("ad").asText()).isEqualTo("C MAH.");
        sunucu.verify();
    }

    @Test
    void partiSonuclariParametreleri() throws Exception {
        yanit("/api/partiler/107/sonuclar?tur=genel&yilBaslangic=2015&zincir=true", "[]");
        AracSonucu s = kutu.calistir("parti_sonuclari",
                girdi("{\"parti_id\":107,\"tur\":\"genel\",\"yil_baslangic\":2015,\"zincir\":true}"));
        assertThat(s.sorgu()).isEqualTo("/api/partiler/107/sonuclar?tur=genel&yilBaslangic=2015&zincir=true");
        sunucu.verify();
    }

    @Test
    void secilenlerKapsamlaBirlikte() throws Exception {
        yanit("/api/secimler/2023/kapsam", "[{\"veri\":\"secilen\",\"bulunan\":405,\"beklenen\":600,\"durum\":\"eksik\"}]");
        yanit("/api/secimler/2023/secilenler?plaka=34", "[{\"ad\":\"X\"}]");
        JsonNode v = kutu.calistir("secilenler", girdi("{\"secim_id\":\"2023\",\"plaka\":34}")).veri();
        assertThat(v.path("kapsam").get(0).path("bulunan").asInt()).isEqualTo(405);
        assertThat(v.path("secilenler")).hasSize(1);
        sunucu.verify();
    }

    @Test
    void bulunamayanKayitAracHatasinaDoner() throws Exception {
        sunucu.expect(requestTo(API + "/api/secimler/2023/iller/99"))
                .andRespond(withResourceNotFound().contentType(MediaType.APPLICATION_JSON)
                        .body("{\"durum\":404,\"hata\":\"Not Found\",\"mesaj\":\"2023 seçiminde 99 plakalı il yok\"}"));
        assertThatThrownBy(() -> kutu.calistir("il_sonuclari", girdi("{\"secim_id\":\"2023\",\"plaka\":99}")))
                .isInstanceOf(AracHatasi.class).hasMessage("2023 seçiminde 99 plakalı il yok");
    }

    @Test
    void girdiDogrulama() {
        assertThatThrownBy(() -> kutu.calistir("il_sonuclari", girdi("{}")))
                .isInstanceOf(AracHatasi.class).hasMessageContaining("secim_id");
        assertThatThrownBy(() -> kutu.calistir("ilce_sonucu", girdi("{\"secim_id\":\"../../actuator\",\"ilce_id\":\"x\"}")))
                .isInstanceOf(AracHatasi.class).hasMessageContaining("Geçersiz");
        assertThatThrownBy(() -> kutu.calistir("ilce_sonuclari", girdi("{\"secim_id\":\"2023\",\"plaka\":\"x\"}")))
                .isInstanceOf(AracHatasi.class);
        assertThatThrownBy(() -> kutu.calistir("olmayan_arac", girdi("{}")))
                .isInstanceOf(AracHatasi.class);
    }

    @Test
    void haritaBaglantisiHttpCagirmaz() throws Exception {
        AracSonucu s = kutu.calistir("harita_baglantisi",
                girdi("{\"secim_id\":\"2023\",\"plaka\":34,\"mod\":\"parti\",\"parti\":\"CHP\"}"));
        assertThat(s.haritaBaglantisi()).isEqualTo("https://harita.example/#secim=2023&il=34&mod=parti&parti=CHP");
        assertThat(s.sorgu()).isNull();
        AracSonucu senato = kutu.calistir("harita_baglantisi", girdi("{\"secim_id\":\"1961senato\"}"));
        assertThat(senato.haritaBaglantisi()).isNull();
        assertThat(senato.veri().path("not").asText()).contains("haritada yok");
        sunucu.verify();
    }
}
