package tr.secimharitasi.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;

/** Arkada sahte bir election-api (JDK HttpServer) ile yönlendirme, yöntem kısıtı ve CORS. */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "logging.level.tr.secimharitasi=DEBUG",
        "logging.level.org.springframework.web.cors=TRACE",
        "logging.level.org.springframework.web.reactive.DispatcherHandler=DEBUG"})
@AutoConfigureWebTestClient
class GecitTest {

    static final AtomicReference<String> sonIstek = new AtomicReference<>();
    static final HttpServer sahteApi = sahteApiBaslat();

    static HttpServer sahteApiBaslat() {
        try {
            HttpServer s = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            s.createContext("/", ex -> {
                sonIstek.set(ex.getRequestMethod() + " " + ex.getRequestURI());
                byte[] govde = "[{\"secimId\":\"2023\"}]".getBytes(StandardCharsets.UTF_8);
                ex.getResponseHeaders().add("Content-Type", "application/json");
                ex.sendResponseHeaders(200, govde.length);
                try (OutputStream o = ex.getResponseBody()) {
                    o.write(govde);
                }
            });
            s.start();
            return s;
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
    }

    @DynamicPropertySource
    static void ozellikler(DynamicPropertyRegistry r) {
        r.add("gecit.election-api-url", () -> "http://127.0.0.1:" + sahteApi.getAddress().getPort());
    }

    @AfterAll
    static void kapat() {
        sahteApi.stop(0);
    }

    @Autowired
    WebTestClient web;

    @Autowired
    GecitOzellikleri ozellikler;

    @Test
    void ozelliklerBaglanir() {
        assertThat(ozellikler.izinliKokenler()).containsExactly("https://hamikumbasae.github.io");
        assertThat(ozellikler.electionApiUrl().getPort()).isEqualTo(sahteApi.getAddress().getPort());
    }

    @Test
    void getIstegiApiyeAktarilir() {
        web.get().uri("/api/secimler?tur=genel").exchange()
                .expectStatus().isOk()
                .expectHeader().valueEquals("X-Kaynak-Servis", "election-api")
                .expectBody().jsonPath("$[0].secimId").isEqualTo("2023");
        assertThat(sonIstek.get()).isEqualTo("GET /api/secimler?tur=genel");
    }

    @Test
    void yazmaIstekleriVeBaskaYollarGecmez() {
        sonIstek.set(null);
        web.post().uri("/api/secimler").exchange().expectStatus().isNotFound();
        web.delete().uri("/api/secimler/2023").exchange().expectStatus().isNotFound();
        web.get().uri("/baska-bir-yol").exchange().expectStatus().isNotFound();
        assertThat(sonIstek.get()).isNull();
    }

    @Test
    void githubPagesIcinCors() {
        web.options().uri("/api/secimler")
                .header(HttpHeaders.ORIGIN, "https://hamikumbasae.github.io")
                .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, HttpMethod.GET.name())
                .exchange()
                .expectStatus().isOk()
                .expectHeader().valueEquals(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "https://hamikumbasae.github.io");
        web.options().uri("/api/secimler")
                .header(HttpHeaders.ORIGIN, "https://baska-site.example")
                .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, HttpMethod.GET.name())
                .exchange()
                .expectStatus().isForbidden();
        // Asıl GET isteği: arka servisten gelen yanıtta CORS başlığı
        web.get().uri("/api/secimler")
                .header(HttpHeaders.ORIGIN, "https://hamikumbasae.github.io")
                .exchange()
                .expectStatus().isOk()
                .expectHeader().valueEquals(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "https://hamikumbasae.github.io")
                .expectHeader().valueEquals("X-Kaynak-Servis", "election-api");
    }

    @Test
    void saglikUcu() {
        web.get().uri("/actuator/health").exchange().expectStatus().isOk()
                .expectBody().jsonPath("$.status").isEqualTo("UP");
    }
}
