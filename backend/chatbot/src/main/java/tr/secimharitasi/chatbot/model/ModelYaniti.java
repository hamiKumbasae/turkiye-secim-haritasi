package tr.secimharitasi.chatbot.model;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;

/**
 * Messages API yanıtı. icerik: Anthropic biçiminde içerik blokları (text, tool_use).
 *
 * @param durmaNedeni end_turn | tool_use | max_tokens ...
 */
public record ModelYaniti(String durmaNedeni, List<JsonNode> icerik, int girdiToken, int ciktiToken) {

    public boolean aracIstiyor() {
        return "tool_use".equals(durmaNedeni) && icerik.stream().anyMatch(b -> "tool_use".equals(b.path("type").asText()));
    }

    public List<JsonNode> aracCagrilari() {
        return icerik.stream().filter(b -> "tool_use".equals(b.path("type").asText())).toList();
    }

    /** Metin bloklarının birleşimi. */
    public String metin() {
        List<String> l = new ArrayList<>();
        icerik.stream().filter(b -> "text".equals(b.path("type").asText())).forEach(b -> l.add(b.path("text").asText()));
        return String.join("\n", l).trim();
    }
}
