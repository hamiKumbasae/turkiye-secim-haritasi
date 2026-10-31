package tr.secimharitasi.chatbot.arac;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.function.Function;

/** Modelin çağırabileceği bir araç: ad, açıklama, girdi şeması ve çalıştırma. */
public record Arac(String ad, String aciklama, ObjectNode sema, Function<JsonNode, AracSonucu> calistirici) {

    public AracSonucu calistir(JsonNode girdi) {
        return calistirici.apply(girdi);
    }
}
