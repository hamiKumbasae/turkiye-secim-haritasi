package tr.secimharitasi.api.depo;

/** Bir partinin bir seçimdeki yurt içi oy toplamı (il satırlarından). */
public record PartiToplami(String secimId, String tur, Integer yil, Integer partiId, Long oy) {
}
