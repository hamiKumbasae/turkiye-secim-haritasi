package io.github.hamikumbasae.election.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;
import java.util.Map;

/**
 * In-process Caffeine caches. Election results never change after they are loaded, so entries live long;
 * sizes are bounded to keep the heap small.
 */
@Configuration
@EnableCaching
@EnableConfigurationProperties(CacheConfig.CacheProperties.class)
public class CacheConfig {

    @ConfigurationProperties(prefix = "app.cache")
    public record CacheProperties(Duration ttl, Map<String, Long> maxEntries) {
        public CacheProperties {
            ttl = ttl == null ? Duration.ofHours(12) : ttl;
            maxEntries = maxEntries == null ? Map.of() : maxEntries;
        }
    }

    @Bean
    public CacheManager cacheManager(CacheProperties props) {
        CaffeineCacheManager manager = new CaffeineCacheManager();
        manager.setAllowNullValues(false);
        Map<String, Long> defaults = Map.of(
                "elections", 1L,
                "summaries", 100L,
                "history", 1_000L,
                "rankings", 1_000L,
                "search", 1_000L,
                "geo", 300L);
        defaults.forEach((name, size) -> manager.registerCustomCache(name, Caffeine.newBuilder()
                .maximumSize(props.maxEntries().getOrDefault(name, size))
                .expireAfterWrite(props.ttl())
                .recordStats()
                .build()));
        return manager;
    }
}
