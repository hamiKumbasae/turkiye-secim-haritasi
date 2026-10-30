package tr.secimharitasi.chatbot.arac;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Araçların listesi: modele tanım olarak verilir, adla çalıştırılır. */
public class AracKutusu {

    private final Map<String, Arac> araclar = new LinkedHashMap<>();
    private final ObjectMapper json;

    public AracKutusu(List<Arac> araclar, ObjectMapper json) {
        araclar.forEach(a -> this.araclar.put(a.ad(), a));
        this.json = json;
    }

    /** Anthropic araç tanımları: {name, description, input_schema}. */
    public List<JsonNode> tanimlar() {
        return araclar.values().stream().map(a -> {
            ObjectNode t = json.createObjectNode();
            t.put("name", a.ad());
            t.put("description", a.aciklama());
            t.set("input_schema", a.sema());
            return (JsonNode) t;
        }).toList();
    }

    public AracSonucu calistir(String ad, JsonNode girdi) {
        Arac a = araclar.get(ad);
        if (a == null) {
            throw new AracHatasi("Böyle bir araç yok: " + ad);
        }
        return a.calistir(girdi == null ? json.createObjectNode() : girdi);
    }

    public List<String> adlar() {
        return List.copyOf(araclar.keySet());
    }
}
