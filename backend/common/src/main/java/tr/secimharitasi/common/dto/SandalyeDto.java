package tr.secimharitasi.common.dto;

/** Bir partinin bir ilde (milletvekili) ya da ilçede (belediye meclisi) kazandığı sandalye. */
public record SandalyeDto(String secimId, Integer plaka, String ilceId, int partiId, String parti, int sandalye) {
}
