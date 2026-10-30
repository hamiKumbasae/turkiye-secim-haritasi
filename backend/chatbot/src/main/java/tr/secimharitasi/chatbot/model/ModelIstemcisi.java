package tr.secimharitasi.chatbot.model;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;

/** Dil modeline bir tur gönderir. Testlerde senaryolu sahte bir istemciyle değiştirilir. */
public interface ModelIstemcisi {

    /**
     * @param sistem   sistem talimatı
     * @param mesajlar Anthropic biçiminde mesajlar ({role, content})
     * @param araclar  araç tanımları ({name, description, input_schema})
     */
    ModelYaniti gonder(String sistem, List<JsonNode> mesajlar, List<JsonNode> araclar);
}
