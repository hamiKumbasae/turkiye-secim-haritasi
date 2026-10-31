package tr.secimharitasi.common.dto;

import java.util.List;

/** Ada göre il ve ilçe araması (büyük/küçük harf ve Türkçe karakter farkı yok sayılır). */
public record YerAramaDto(String aranan, List<IlDto> iller, List<IlceDto> ilceler) {
}
