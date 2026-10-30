package tr.secimharitasi.chatbot;

import java.net.URI;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * @param anthropicApiKey   boşsa sohbet uç noktası 503 döner (servis yine açılır)
 * @param model             Anthropic model kimliği
 * @param azamiAdim         bir soruda modelin en çok kaç kez araç çağırabileceği
 * @param dakikadaIstek     bir IP'den dakikada en çok kaç soru
 * @param electionApiUrl    araçların çağırdığı election-api adresi
 * @param haritaUrl         "Haritada göster" bağlantılarının kökü (GitHub Pages sitesi)
 */
@ConfigurationProperties(prefix = "sohbet")
public record SohbetOzellikleri(
        String anthropicApiKey,
        @DefaultValue("https://api.anthropic.com") URI anthropicUrl,
        @DefaultValue("claude-sonnet-5-5") String model,
        @DefaultValue("2000") int azamiToken,
        @DefaultValue("8") int azamiAdim,
        @DefaultValue("500") int azamiSoruUzunlugu,
        @DefaultValue("10") int dakikadaIstek,
        @DefaultValue("60") int zamanAsimiSaniye,
        URI electionApiUrl,
        @DefaultValue("https://hamikumbasae.github.io/turkiye-secim-haritasi/") String haritaUrl) {

    public boolean anahtarVar() {
        return anthropicApiKey != null && !anthropicApiKey.isBlank();
    }
}
