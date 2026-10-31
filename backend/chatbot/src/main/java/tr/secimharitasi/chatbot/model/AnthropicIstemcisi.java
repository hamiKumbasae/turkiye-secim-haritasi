package tr.secimharitasi.chatbot.model;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

/** Anthropic Messages API (POST /v1/messages), araç çağırmayla. */
public class AnthropicIstemcisi implements ModelIstemcisi {

    static final String SURUM = "2023-06-01";

    private final RestClient http;
    private final ObjectMapper json;
    private final String model;
    private final int azamiToken;

    public AnthropicIstemcisi(RestClient.Builder builder, ObjectMapper json, String kokUrl, String apiAnahtari,
                              String model, int azamiToken) {
        this.http = builder.baseUrl(kokUrl)
                .defaultHeader("x-api-key", apiAnahtari)
                .defaultHeader("anthropic-version", SURUM)
                .build();
        this.json = json;
        this.model = model;
        this.azamiToken = azamiToken;
    }

    @Override
    public ModelYaniti gonder(String sistem, List<JsonNode> mesajlar, List<JsonNode> araclar) {
        ObjectNode govde = json.createObjectNode();
        govde.put("model", model);
        govde.put("max_tokens", azamiToken);
        govde.put("system", sistem);
        ArrayNode t = govde.putArray("tools");
        araclar.forEach(t::add);
        ArrayNode m = govde.putArray("messages");
        mesajlar.forEach(m::add);
        JsonNode yanit;
        try {
            yanit = http.post().uri("/v1/messages")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(govde)
                    .retrieve()
                    .body(JsonNode.class);
        } catch (RestClientResponseException e) {
            throw new ModelHatasi("Model servisi hata döndü: HTTP " + e.getStatusCode().value() + " "
                    + kisalt(e.getResponseBodyAsString()), e);
        } catch (RestClientException e) {
            throw new ModelHatasi("Model servisine ulaşılamadı: " + e.getMessage(), e);
        }
        if (yanit == null) {
            throw new ModelHatasi("Model servisi boş yanıt döndü", null);
        }
        List<JsonNode> icerik = new ArrayList<>();
        yanit.path("content").forEach(icerik::add);
        return new ModelYaniti(yanit.path("stop_reason").asText(null), icerik,
                yanit.path("usage").path("input_tokens").asInt(), yanit.path("usage").path("output_tokens").asInt());
    }

    private static String kisalt(String s) {
        return s == null ? "" : s.length() > 300 ? s.substring(0, 300) : s;
    }
}
