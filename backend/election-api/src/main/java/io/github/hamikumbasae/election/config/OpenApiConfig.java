package io.github.hamikumbasae.election.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.springframework.boot.info.BuildProperties;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI electionOpenApi(ObjectProvider<BuildProperties> build) {
        String version = build.getIfAvailable() == null ? "dev" : build.getIfAvailable().getVersion();
        return new OpenAPI().info(new Info()
                .title("Türkiye Election API")
                .version(version)
                .description("""
                        Read-only REST API over every Turkish general, local and presidential election and \
                        referendum from 1950 to 2024: national totals, province, district and neighbourhood \
                        results, party history, rankings, name search and neighbourhood boundaries as GeoJSON.

                        Data: [turkiye-secim-haritasi](https://github.com/hamiKumbasae/turkiye-secim-haritasi) \
                        (YSK and TÜİK publications).""")
                .contact(new Contact().name("Hami Kumbasar").url("https://github.com/hamiKumbasae"))
                .license(new License().name("Code: see repository LICENSE; data: LICENSE-DATA.md")));
    }
}
