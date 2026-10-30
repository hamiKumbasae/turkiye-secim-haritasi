package tr.secimharitasi.chatbot;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Clock;
import java.time.Duration;
import java.net.http.HttpClient;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import tr.secimharitasi.chatbot.arac.AracKutusu;
import tr.secimharitasi.chatbot.arac.SecimAraclari;
import tr.secimharitasi.chatbot.model.AnthropicIstemcisi;
import tr.secimharitasi.chatbot.model.ModelIstemcisi;
import tr.secimharitasi.chatbot.sohbet.SohbetServisi;
import tr.secimharitasi.chatbot.web.HizSiniri;

@Configuration
public class SohbetYapilandirmasi {

    @Bean
    ModelIstemcisi modelIstemcisi(RestClient.Builder builder, ObjectMapper json, SohbetOzellikleri o) {
        var fabrika = new JdkClientHttpRequestFactory(
                HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build());
        fabrika.setReadTimeout(Duration.ofSeconds(o.zamanAsimiSaniye()));
        return new AnthropicIstemcisi(builder.clone().requestFactory(fabrika), json,
                o.anthropicUrl().toString(), o.anahtarVar() ? o.anthropicApiKey() : "", o.model(), o.azamiToken());
    }

    @Bean
    AracKutusu aracKutusu(RestClient.Builder builder, ObjectMapper json, SohbetOzellikleri o) {
        if (o.electionApiUrl() == null) {
            throw new IllegalStateException("sohbet.election-api-url (ELECTION_API_URL) tanımlı değil");
        }
        return new SecimAraclari(builder.clone(), o.electionApiUrl().toString(), json, o.haritaUrl()).kutu();
    }

    @Bean
    SohbetServisi sohbetServisi(ModelIstemcisi model, AracKutusu araclar, ObjectMapper json, SohbetOzellikleri o) {
        return new SohbetServisi(model, araclar, json, o.azamiAdim());
    }

    @Bean
    HizSiniri hizSiniri(SohbetOzellikleri o) {
        return new HizSiniri(o.dakikadaIstek(), Clock.systemUTC());
    }
}
