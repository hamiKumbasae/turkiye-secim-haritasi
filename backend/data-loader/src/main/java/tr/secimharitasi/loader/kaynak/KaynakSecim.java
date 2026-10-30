package tr.secimharitasi.loader.kaynak;

import tr.secimharitasi.common.SecimTuru;

/**
 * Okunmuş bir seçim: dosya içeriği ve dosya adından gelen anahtar, sources.yml'deki birincil kaynak.
 *
 * @param secimId dosya adı ('2023', '2024yerel' ...)
 */
public record KaynakSecim(String secimId, int yil, SecimTuru tur, SecimDosyasi dosya, String birincilKaynak,
                          String kaynakDurumu) {
}
