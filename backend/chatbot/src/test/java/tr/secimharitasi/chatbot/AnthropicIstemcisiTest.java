package tr.secimharitasi.chatbot;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;
import tr.secimharitasi.chatbot.model.AnthropicIstemcisi;
import tr.secimharitasi.chatbot.model.ModelHatasi;
import tr.secimharitasi.chatbot.model.ModelYaniti;

/** Messages API isteğinin biçimi ve yanıtın okunması (sahte HTTP sunucusu; gerçek API çağrılmaz). */
class AnthropicIstemcisiTest {

    final ObjectMapper json = new ObjectMapper();
    MockRestServiceServer sunucu;
    AnthropicIstemcisi istemci;

    @BeforeEach
    void kur() {
        RestClient.Builder b = RestClient.builder();
        sunucu = MockRestServiceServer.bindTo(b).build();
        istemci = new AnthropicIstemcisi(b, json, "https://api.example", "gizli-anahtar", "claude-sonnet-5-5", 1500);
    }

    @Test
    void istekBicimiVeAracCagrisiYaniti() throws Exception {
        sunucu.expect(requestTo("https://api.example/v1/messages"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("x-api-key", "gizli-anahtar"))
                .andExpect(header("anthropic-version", "2023-06-01"))
                .andExpect(jsonPath("$.model").value("claude-sonnet-5-5"))
                .andExpect(jsonPath("$.max_tokens").value(1500))
                .andExpect(jsonPath("$.system").value("sistem"))
                .andExpect(jsonPath("$.tools[0].name").value("yer_ara"))
                .andExpect(jsonPath("$.messages[0].role").value("user"))
                .andExpect(jsonPath("$.messages[0].content").value("Ümraniye?"))
                .andRespond(withSuccess("""
                        {"id":"msg_1","type":"message","role":"assistant","stop_reason":"tool_use",
                         "content":[{"type":"text","text":"Arıyorum."},
                                    {"type":"tool_use","id":"toolu_1","name":"yer_ara","input":{"ad":"Ümraniye"}}],
                         "usage":{"input_tokens":321,"output_tokens":45}}""", MediaType.APPLICATION_JSON));

        JsonNode arac = json.readTree("{\"name\":\"yer_ara\",\"description\":\"d\",\"input_schema\":{\"type\":\"object\"}}");
        JsonNode mesaj = json.readTree("{\"role\":\"user\",\"content\":\"Ümraniye?\"}");
        ModelYaniti y = istemci.gonder("sistem", List.of(mesaj), List.of(arac));

        assertThat(y.aracIstiyor()).isTrue();
        assertThat(y.aracCagrilari()).hasSize(1);
        assertThat(y.aracCagrilari().get(0).path("input").path("ad").asText()).isEqualTo("Ümraniye");
        assertThat(y.metin()).isEqualTo("Arıyorum.");
        assertThat(y.girdiToken()).isEqualTo(321);
        assertThat(y.ciktiToken()).isEqualTo(45);
        sunucu.verify();
    }

    @Test
    void metinYaniti() {
        sunucu.expect(requestTo("https://api.example/v1/messages")).andRespond(withSuccess("""
                {"stop_reason":"end_turn","content":[{"type":"text","text":"Cevap"}],
                 "usage":{"input_tokens":1,"output_tokens":1}}""", MediaType.APPLICATION_JSON));
        ModelYaniti y = istemci.gonder("s", List.of(), List.of());
        assertThat(y.aracIstiyor()).isFalse();
        assertThat(y.metin()).isEqualTo("Cevap");
    }

    @Test
    void hataYanitiModelHatasiOlur() {
        sunucu.expect(requestTo("https://api.example/v1/messages")).andRespond(withStatus(HttpStatus.UNAUTHORIZED)
                .contentType(MediaType.APPLICATION_JSON)
                .body("{\"type\":\"error\",\"error\":{\"type\":\"authentication_error\",\"message\":\"invalid x-api-key\"}}"));
        assertThatThrownBy(() -> istemci.gonder("s", List.of(), List.of()))
                .isInstanceOf(ModelHatasi.class).hasMessageContaining("401");
    }
}
