package tr.secimharitasi.gateway;

import java.net.URI;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param electionApiUrl  arka plandaki election-api adresi (Compose ağında http://election-api:8081)
 * @param chatbotUrl      arka plandaki chatbot adresi (Compose ağında http://chatbot:8082)
 * @param izinliKokenler  tarayıcıdan çağırabilecek siteler (CORS), ör. GitHub Pages
 */
@ConfigurationProperties(prefix = "gecit")
public record GecitOzellikleri(
        URI electionApiUrl,
        @DefaultValue("http://localhost:8082") URI chatbotUrl,
        @DefaultValue("https://hamikumbasae.github.io") List<String> izinliKokenler) {
}
