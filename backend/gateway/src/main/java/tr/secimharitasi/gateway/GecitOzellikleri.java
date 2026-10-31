package tr.secimharitasi.gateway;

import java.net.URI;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param electionApiUrl  arka plandaki election-api adresi (Compose ağında http://election-api:8081)
 * @param izinliKokenler  tarayıcıdan çağırabilecek siteler (CORS), ör. GitHub Pages
 */
@ConfigurationProperties(prefix = "gecit")
public record GecitOzellikleri(
        URI electionApiUrl,
        @DefaultValue("https://hamikumbasae.github.io") List<String> izinliKokenler) {
}
