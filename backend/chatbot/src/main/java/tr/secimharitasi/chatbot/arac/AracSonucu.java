package tr.secimharitasi.chatbot.arac;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * @param veri             modele dönecek (kırpılmış) veri
 * @param sorgu            veriyi veren election-api sorgusu (kullanıcıya "kaynak" olarak gösterilir), yoksa null
 * @param haritaBaglantisi harita_baglantisi aracının ürettiği bağlantı, yoksa null
 */
public record AracSonucu(JsonNode veri, String sorgu, String haritaBaglantisi) {
}
