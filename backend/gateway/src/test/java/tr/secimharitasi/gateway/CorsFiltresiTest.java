package tr.secimharitasi.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

/** CorsFiltresi tek başına (gateway ve sunucu yok). */
class CorsFiltresiTest {

    private static final String PAGES = "https://hamikumbasae.github.io";
    private final CorsFiltresi filtre = new CorsFiltresi(List.of(PAGES));
    private final AtomicBoolean zincirCagrildi = new AtomicBoolean();
    private final WebFilterChain zincir = ex -> {
        zincirCagrildi.set(true);
        return Mono.empty();
    };

    private MockServerWebExchange calistir(MockServerHttpRequest istek) {
        MockServerWebExchange ex = MockServerWebExchange.from(istek);
        filtre.filter(ex, zincir).block();
        ex.getResponse().setComplete().block();
        return ex;
    }

    @Test
    void izinliKokendenOnKontrol200() {
        MockServerWebExchange ex = calistir(MockServerHttpRequest.options("/api/secimler")
                .header(HttpHeaders.ORIGIN, PAGES)
                .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, "GET")
                .header(HttpHeaders.ACCESS_CONTROL_REQUEST_HEADERS, "accept")
                .build());
        assertThat(ex.getResponse().getStatusCode()).isEqualTo(HttpStatus.OK);
        HttpHeaders h = ex.getResponse().getHeaders();
        assertThat(h.getAccessControlAllowOrigin()).isEqualTo(PAGES);
        assertThat(h.getAccessControlAllowMethods()).extracting(Object::toString).containsExactly("GET", "HEAD");
        assertThat(h.getAccessControlAllowHeaders()).containsExactly("accept");
        assertThat(zincirCagrildi).isFalse();
    }

    @Test
    void baskaKokenVeYazmaYontemiReddedilir() {
        MockServerWebExchange baska = calistir(MockServerHttpRequest.options("/api/secimler")
                .header(HttpHeaders.ORIGIN, "https://baska-site.example")
                .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, "GET").build());
        assertThat(baska.getResponse().getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);

        MockServerWebExchange yazma = calistir(MockServerHttpRequest.options("/api/secimler")
                .header(HttpHeaders.ORIGIN, PAGES)
                .header(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, "DELETE").build());
        assertThat(yazma.getResponse().getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(zincirCagrildi).isFalse();
    }

    @Test
    void asilIstekteBaslikEklenirVeZincirDevamEder() {
        MockServerWebExchange ex = calistir(MockServerHttpRequest.get("/api/secimler")
                .header(HttpHeaders.ORIGIN, PAGES + "/").build());
        assertThat(zincirCagrildi).isTrue();
        assertThat(ex.getResponse().getHeaders().getAccessControlAllowOrigin()).isEqualTo(PAGES + "/");
    }

    @Test
    void izinsizKokendeBaslikYokAmaIstekGecer() {
        MockServerWebExchange ex = calistir(MockServerHttpRequest.get("/api/secimler")
                .header(HttpHeaders.ORIGIN, "https://baska-site.example").build());
        assertThat(zincirCagrildi).isTrue();
        assertThat(ex.getResponse().getHeaders().getAccessControlAllowOrigin()).isNull();
    }

    @Test
    void kokensizVeApiDisiIsteklereDokunulmaz() {
        MockServerWebExchange kokensiz = calistir(MockServerHttpRequest.get("/api/secimler").build());
        assertThat(kokensiz.getResponse().getHeaders().containsKey(HttpHeaders.VARY)).isFalse();
        MockServerWebExchange disari = calistir(MockServerHttpRequest.get("/actuator/health")
                .header(HttpHeaders.ORIGIN, PAGES).build());
        assertThat(disari.getResponse().getHeaders().getAccessControlAllowOrigin()).isNull();
    }
}
