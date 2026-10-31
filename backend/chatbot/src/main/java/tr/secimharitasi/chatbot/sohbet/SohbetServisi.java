package tr.secimharitasi.chatbot.sohbet;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import tr.secimharitasi.chatbot.arac.AracHatasi;
import tr.secimharitasi.chatbot.arac.AracKutusu;
import tr.secimharitasi.chatbot.arac.AracSonucu;
import tr.secimharitasi.chatbot.model.ModelIstemcisi;
import tr.secimharitasi.chatbot.model.ModelYaniti;

/**
 * Soru-cevap döngüsü: model soruyu okur, araçları (election-api sorguları) çağırır, sonuçları görüp cevabı yazar.
 * Sayılar yalnız araç sonuçlarından gelir; servis modelin metnine sayı eklemez ya da hesaplamaz.
 */
public class SohbetServisi {

    private static final Logger LOG = LoggerFactory.getLogger(SohbetServisi.class);

    /** Bir araç sonucunun modele giden en uzun hali (karakter). */
    static final int AZAMI_SONUC = 15_000;

    static final String ADIM_SINIRI_CEVABI = "Bu soru için çok fazla veri sorgusu gerekti ve cevabı tamamlayamadım. "
            + "Soruyu daha dar sorabilir misiniz? Örneğin tek bir seçim yılı ve tek bir il ya da ilçe belirterek.";

    private final ModelIstemcisi model;
    private final AracKutusu araclar;
    private final ObjectMapper json;
    private final int azamiAdim;

    public SohbetServisi(ModelIstemcisi model, AracKutusu araclar, ObjectMapper json, int azamiAdim) {
        this.model = model;
        this.araclar = araclar;
        this.json = json;
        this.azamiAdim = azamiAdim;
    }

    public SohbetYaniti sor(String soru) {
        long bas = System.currentTimeMillis();
        List<JsonNode> mesajlar = new ArrayList<>();
        mesajlar.add(mesaj("user", json.getNodeFactory().textNode(soru)));
        List<SohbetYaniti.Kaynak> kaynaklar = new ArrayList<>();
        String harita = null;
        int girdiToken = 0;
        int ciktiToken = 0;

        for (int adim = 1; adim <= azamiAdim; adim++) {
            ModelYaniti y = model.gonder(SistemTalimati.METIN, mesajlar, araclar.tanimlar());
            girdiToken += y.girdiToken();
            ciktiToken += y.ciktiToken();
            if (!y.aracIstiyor()) {
                String cevap = y.metin();
                if ("max_tokens".equals(y.durmaNedeni())) {
                    cevap = cevap + "\n\n(Cevap uzunluk sınırına takıldı ve yarıda kesildi.)";
                }
                if (cevap.isBlank()) {
                    cevap = "Bu soruya bir cevap üretemedim. Soruyu farklı sorabilir misiniz?";
                }
                LOG.info("Soru cevaplandı: {} adım, {} araç, {} girdi / {} çıktı token", adim, kaynaklar.size(),
                        girdiToken, ciktiToken);
                return new SohbetYaniti(cevap, kaynaklar, harita, adim, System.currentTimeMillis() - bas);
            }

            ArrayNode asistan = json.createArrayNode();
            y.icerik().forEach(asistan::add);
            mesajlar.add(mesaj("assistant", asistan));

            ArrayNode sonuclar = json.createArrayNode();
            for (JsonNode cagri : y.aracCagrilari()) {
                String ad = cagri.path("name").asText();
                JsonNode girdi = cagri.path("input");
                ObjectNode sonuc = sonuclar.addObject();
                sonuc.put("type", "tool_result");
                sonuc.put("tool_use_id", cagri.path("id").asText());
                try {
                    AracSonucu s = araclar.calistir(ad, girdi);
                    if (s.haritaBaglantisi() != null) {
                        harita = s.haritaBaglantisi();
                    }
                    if (s.sorgu() != null) {
                        kaynaklar.add(new SohbetYaniti.Kaynak(ad, girdi, s.sorgu(), null));
                    }
                    sonuc.put("content", kirp(yaz(s.veri())));
                } catch (AracHatasi e) {
                    kaynaklar.add(new SohbetYaniti.Kaynak(ad, girdi, null, e.getMessage()));
                    sonuc.put("content", e.getMessage());
                    sonuc.put("is_error", true);
                }
            }
            mesajlar.add(mesaj("user", sonuclar));
        }
        LOG.warn("Adım sınırı ({}) aşıldı: {} araç çağrısı", azamiAdim, kaynaklar.size());
        return new SohbetYaniti(ADIM_SINIRI_CEVABI, kaynaklar, harita, azamiAdim, System.currentTimeMillis() - bas);
    }

    private ObjectNode mesaj(String rol, JsonNode icerik) {
        ObjectNode m = json.createObjectNode();
        m.put("role", rol);
        m.set("content", icerik);
        return m;
    }

    private String yaz(JsonNode n) {
        try {
            return json.writeValueAsString(n);
        } catch (JsonProcessingException e) {
            throw new AracHatasi("Sonuç yazılamadı");
        }
    }

    static String kirp(String s) {
        if (s.length() <= AZAMI_SONUC) {
            return s;
        }
        return s.substring(0, AZAMI_SONUC) + " …[sonuç kırpıldı: " + s.length()
                + " karakter. Daha dar bir sorgu yap (ör. plaka ver).]";
    }
}
