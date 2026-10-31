package tr.secimharitasi.chatbot;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import tr.secimharitasi.common.Metin;

/**
 * Gerçek modelle değerlendirme (isteğe bağlı; CI'da çalışmaz, API anahtarı ve ücret gerektirir).
 * Çalışan sisteme karşı: DEGERLENDIRME_URL=http://localhost:8080 mvn -pl chatbot test -Dtest=DegerlendirmeTest
 */
@EnabledIfEnvironmentVariable(named = "DEGERLENDIRME_URL", matches = "https?://.+")
class DegerlendirmeTest {

    final ObjectMapper json = new ObjectMapper();
    final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    final String kok = System.getenv("DEGERLENDIRME_URL");

    @TestFactory
    Stream<DynamicTest> sorular() throws Exception {
        JsonNode set;
        try (InputStream in = getClass().getResourceAsStream("/degerlendirme/sorular.yaml")) {
            set = new ObjectMapper(new YAMLFactory()).readTree(in);
        }
        List<DynamicTest> testler = new ArrayList<>();
        for (JsonNode s : set.path("sorular")) {
            testler.add(DynamicTest.dynamicTest(s.path("soru").asText(), () -> dene(s)));
        }
        return testler.stream();
    }

    void dene(JsonNode s) throws Exception {
        String govde = json.writeValueAsString(json.createObjectNode().put("soru", s.path("soru").asText()));
        HttpRequest istek = HttpRequest.newBuilder(URI.create(kok + "/api/sohbet"))
                .timeout(Duration.ofSeconds(120))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(govde, StandardCharsets.UTF_8))
                .build();
        HttpResponse<String> yanit = http.send(istek, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        assertThat(yanit.statusCode()).as(yanit.body()).isEqualTo(200);
        JsonNode y = json.readTree(yanit.body());
        String cevap = y.path("cevap").asText();
        System.out.printf("%n--- %s%n%s%nkaynaklar: %s%n", s.path("soru").asText(), cevap, y.path("kaynaklar"));

        if (s.path("reddetmeli").asBoolean()) {
            assertThat(y.path("kaynaklar")).as("reddedilen soruda veri sorgusu yapılmamalı").isEmpty();
            assertThat(cevap).as("tahmin ya da görüş içermemeli").doesNotContainPattern("%\\s?\\d");
            return;
        }
        String katli = Metin.katla(cevap);
        for (JsonNode beklenen : s.path("icermeli")) {
            assertThat(katli).as("cevapta '%s' olmalı:%n%s", beklenen.asText(), cevap)
                    .contains(Metin.katla(beklenen.asText()));
        }
        assertThat(y.path("kaynaklar")).as("sayısal cevap bir veri sorgusuna dayanmalı").isNotEmpty();
    }
}
