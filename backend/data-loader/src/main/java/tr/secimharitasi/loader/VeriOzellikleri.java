package tr.secimharitasi.loader;

import java.nio.file.Path;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param dizin                data/normalized klasörü
 * @param kaynaklar            sources.yml (isteğe bağlı)
 * @param ilceToleransi        ilçe toplamı ≈ il toplamı için göreli tolerans (0.005 = %0,5)
 * @param partiToplamToleransi seçenek oyları toplamı = geçerli oy için mutlak tolerans
 * @param otomatikCalistir     uygulama açılınca yüklemeyi başlat (testlerde kapalı)
 * @param toplamBoyutu         JDBC toplu ekleme boyutu
 */
@ConfigurationProperties(prefix = "veri")
public record VeriOzellikleri(
        Path dizin,
        Path kaynaklar,
        @DefaultValue("0.005") double ilceToleransi,
        @DefaultValue("0") long partiToplamToleransi,
        @DefaultValue("true") boolean otomatikCalistir,
        @DefaultValue("5000") int toplamBoyutu) {
}
