package tr.secimharitasi.chatbot.sohbet;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;

/**
 * @param cevap            modelin Türkçe cevabı (sınırlı markdown)
 * @param kaynaklar        cevabın dayandığı veri sorguları, çağrılma sırasıyla
 * @param haritaBaglantisi haritada ilgili görünümü açan bağlantı, yoksa null
 * @param adim             modelle kaç tur konuşuldu
 * @param sureMs           toplam süre
 */
public record SohbetYaniti(String cevap, List<Kaynak> kaynaklar, String haritaBaglantisi, int adim, long sureMs) {

    /**
     * @param arac  çağrılan aracın adı
     * @param girdi modelin araca verdiği girdi
     * @param sorgu election-api sorgusu (gateway üzerinden açılabilir), yoksa null
     * @param hata  araç hata verdiyse mesajı
     */
    public record Kaynak(String arac, JsonNode girdi, String sorgu, String hata) {
    }
}
