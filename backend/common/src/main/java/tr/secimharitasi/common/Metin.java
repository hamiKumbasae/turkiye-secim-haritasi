package tr.secimharitasi.common;

import java.text.Normalizer;
import java.util.Locale;

/** Ad karşılaştırma yardımcıları. */
public final class Metin {

    private Metin() {
    }

    /**
     * Arama anahtarı: Türkçe büyük/küçük harf, şapka/nokta gibi işaretler, boşluk, tire ve nokta yok sayılır.
     * "ÜMRANİYE", "Ümraniye", "umraniye" -> "umraniye"; "Şebinkarahisar", "Ş. Karahisar" ayrı kalır.
     */
    public static String katla(String s) {
        if (s == null) {
            return "";
        }
        String k = s.replace("İ", "i").replace("I", "ı").toLowerCase(Locale.ROOT)
                .replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o")
                .replace("ç", "c");
        k = Normalizer.normalize(k, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
        return k.replaceAll("[\\s\\-.']+", "");
    }
}
