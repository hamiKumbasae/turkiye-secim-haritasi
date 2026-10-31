package tr.secimharitasi.loader.ek;

/** Seçilen milletvekili ya da senatör (ek/milletvekilleri, ek/senato). parti null olabilir. */
public record SecilenKaydi(String secimId, int plaka, String gorev, String ad, String parti, String partiAdiKaynakta,
                           String bolge, String kisiLink) {
}
