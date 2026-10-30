package tr.secimharitasi.common.dto;

/**
 * @param baslangicYili verideki ilk seçim yılı (kuruluş yılı değil)
 * @param bitisYili     verideki son seçim yılı; bugün de varsa null
 */
public record IlceDto(String ilceId, int plaka, String ad, boolean guncel, int baslangicYili, Integer bitisYili) {
}
