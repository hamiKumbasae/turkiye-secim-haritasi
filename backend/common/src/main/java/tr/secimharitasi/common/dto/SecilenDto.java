package tr.secimharitasi.common.dto;

/**
 * Seçilen milletvekili ya da senatör (Vikipedi; liste eksik olabilir, bkz. KapsamDto).
 *
 * @param gorev milletvekili | senator
 */
public record SecilenDto(String secimId, String gorev, int plaka, String il, String ad, Integer partiId, String parti,
                         String partiAdiKaynakta, String bolge) {
}
