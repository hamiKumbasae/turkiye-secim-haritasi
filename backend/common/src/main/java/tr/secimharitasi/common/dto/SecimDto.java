package tr.secimharitasi.common.dto;

import tr.secimharitasi.common.SecimTuru;

/**
 * @param secimId        '2023', '2024yerel', '2017referandum', '2023cb2tur'
 * @param tarih          kaynaktaki tarih metni, ör. '14 Mayıs 2023'
 * @param birincilKaynak sources.yml'deki birincil kaynak kurumu (YSK, TÜİK ...)
 */
public record SecimDto(String secimId, SecimTuru tur, int yil, String tarih, Integer toplamSandalye,
                       String birincilKaynak, String kaynakDurumu) {
}
