package tr.secimharitasi.gateway;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;

/**
 * Dışarıya açılan tek kapı. Yalnız GET /api/** election-api'ye geçer; başka yöntem ya da yol 404 döner.
 * Rotalar Java ile tanımlı (Spring Cloud Gateway sürümleri arasında özellik adları değiştiği için).
 * Chatbot servisi eklendiğinde buraya ikinci bir rota gelecek.
 */
@Configuration
class Rotalar {

    private static final Logger log = LoggerFactory.getLogger(Rotalar.class);

    @Bean
    RouteLocator electionApiRotasi(RouteLocatorBuilder builder, GecitOzellikleri ozellikler) {
        return builder.routes()
                .route("election-api", r -> r
                        .path("/api/**")
                        .and().method(HttpMethod.GET, HttpMethod.HEAD)
                        .filters(f -> f.addResponseHeader("X-Kaynak-Servis", "election-api"))
                        .uri(ozellikler.electionApiUrl()))
                .build();
    }

    /** Statik site (GitHub Pages) API'yi tarayıcıdan çağırabilsin: yalnız GET/HEAD. */
    @Bean
    CorsFiltresi corsFiltresi(GecitOzellikleri ozellikler) {
        log.info("CORS: izinli kökenler {}", ozellikler.izinliKokenler());
        return new CorsFiltresi(ozellikler.izinliKokenler());
    }
}
