package io.github.hamikumbasae.election.config;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.service.AnalyticsService;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;
import java.util.Locale;

@Configuration
@EnableConfigurationProperties(WebConfig.CorsProperties.class)
public class WebConfig implements WebMvcConfigurer {

    @ConfigurationProperties(prefix = "app.cors")
    public record CorsProperties(List<String> allowedOrigins) {
        public CorsProperties {
            allowedOrigins = allowedOrigins == null ? List.of() : allowedOrigins;
        }
    }

    private final CorsProperties cors;

    public WebConfig(CorsProperties cors) {
        this.cors = cors;
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(cors.allowedOrigins().toArray(String[]::new))
                .allowedMethods("GET", "HEAD", "OPTIONS")
                .maxAge(3600);
    }

    /** Query parameters accept English or Turkish names in any case: level=district or level=ilce. */
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(String.class, Level.class, Level::parse);
        registry.addConverter(String.class, ElectionType.class, ElectionType::parse);
        registry.addConverter(String.class, AnalyticsService.Order.class,
                s -> AnalyticsService.Order.valueOf(s.trim().toUpperCase(Locale.ROOT)));
    }
}
