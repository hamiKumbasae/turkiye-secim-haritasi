package tr.secimharitasi.gateway;

import java.util.List;
import java.util.Locale;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

/**
 * /api/ altındaki istekler için CORS: yalnız izinli kökenler (GitHub Pages), yalnız GET ve HEAD.
 * <ul>
 *   <li>Ön kontrol (OPTIONS + Access-Control-Request-Method) burada yanıtlanır, rotaya gitmez: izinliyse 200,
 *       değilse 403.</li>
 *   <li>Asıl istekte köken izinliyse yanıta Access-Control-Allow-Origin eklenir; izinli değilse başlık
 *       eklenmez (tarayıcı yanıtı engeller).</li>
 * </ul>
 * Spring'in CorsWebFilter'ı yerine açık yazıldı: gateway'in ön kontrol isteklerini nasıl ele aldığından
 * bağımsız, her adımı test edilebilir olsun diye.
 */
class CorsFiltresi implements WebFilter, Ordered {

    private static final Logger log = LoggerFactory.getLogger(CorsFiltresi.class);
    private static final List<HttpMethod> IZINLI_YONTEMLER = List.of(HttpMethod.GET, HttpMethod.HEAD);
    private static final String VARY = String.join(", ", HttpHeaders.ORIGIN,
            HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD, HttpHeaders.ACCESS_CONTROL_REQUEST_HEADERS);

    private final List<String> izinliKokenler;

    CorsFiltresi(List<String> izinliKokenler) {
        this.izinliKokenler = izinliKokenler.stream().map(CorsFiltresi::normalize).toList();
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest istek = exchange.getRequest();
        String koken = istek.getHeaders().getOrigin();
        if (koken == null || !istek.getPath().value().startsWith("/api/")) {
            return chain.filter(exchange);
        }
        ServerHttpResponse yanit = exchange.getResponse();
        HttpHeaders h = yanit.getHeaders();
        h.set(HttpHeaders.VARY, VARY);
        boolean izinli = izinliKokenler.contains(normalize(koken));

        boolean onKontrol = HttpMethod.OPTIONS.equals(istek.getMethod())
                && istek.getHeaders().containsKey(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD);
        if (onKontrol) {
            HttpMethod istenen = istek.getHeaders().getAccessControlRequestMethod();
            if (!izinli || !IZINLI_YONTEMLER.contains(istenen)) {
                log.debug("CORS ön kontrol reddedildi: köken={}, yöntem={}", koken, istenen);
                yanit.setStatusCode(HttpStatus.FORBIDDEN);
                return yanit.setComplete();
            }
            h.setAccessControlAllowOrigin(koken);
            h.setAccessControlAllowMethods(IZINLI_YONTEMLER);
            List<String> basliklar = istek.getHeaders().getAccessControlRequestHeaders();
            if (!basliklar.isEmpty()) {
                h.setAccessControlAllowHeaders(basliklar);
            }
            h.setAccessControlMaxAge(3600);
            yanit.setStatusCode(HttpStatus.OK);
            return yanit.setComplete();
        }

        if (izinli) {
            // Arka servisin başlıkları gateway tarafından sonradan kopyalanır; başlık yazılmadan hemen önce eklenir.
            yanit.beforeCommit(() -> {
                if (!h.containsKey(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN)) {
                    h.setAccessControlAllowOrigin(koken);
                }
                return Mono.empty();
            });
        }
        return chain.filter(exchange);
    }

    private static String normalize(String koken) {
        String k = koken.trim().toLowerCase(Locale.ROOT);
        return k.endsWith("/") ? k.substring(0, k.length() - 1) : k;
    }
}
