package tr.secimharitasi.loader;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * Tek seferlik iş: Flyway şemayı kurar/günceller, ardından data/normalized'daki seçimler MySQL'e yüklenir
 * ve uygulama kapanır (Docker Compose'da election-api bunun başarıyla bitmesini bekler).
 */
@SpringBootApplication
@ConfigurationPropertiesScan
public class DataLoaderApplication {

    public static void main(String[] args) {
        System.exit(SpringApplication.exit(SpringApplication.run(DataLoaderApplication.class, args)));
    }
}
