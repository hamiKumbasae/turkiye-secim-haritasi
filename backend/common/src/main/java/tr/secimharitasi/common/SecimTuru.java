package tr.secimharitasi.common;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Seçim türü. İlk dördü data/normalized/elections/&lt;tur&gt;/ klasör adlarıyla aynıdır; SENATO ve ARA
 * data/normalized/ek/ altındaki kayıtlardan gelir.
 */
public enum SecimTuru {
    GENEL("genel"),
    YEREL("yerel"),
    REFERANDUM("referandum"),
    CUMHURBASKANLIGI("cumhurbaskanligi"),
    /** Cumhuriyet Senatosu üye seçimi (1961-1979). */
    SENATO("senato"),
    /** Ara ve yenileme seçimleri (milletvekili ara seçimi, belediye yenileme seçimi). */
    ARA("ara");

    private final String kod;

    SecimTuru(String kod) {
        this.kod = kod;
    }

    @JsonValue
    public String kod() {
        return kod;
    }

    public static SecimTuru fromKod(String kod) {
        for (SecimTuru t : values()) {
            if (t.kod.equalsIgnoreCase(kod)) {
                return t;
            }
        }
        throw new IllegalArgumentException("Bilinmeyen seçim türü: " + kod);
    }

    /**
     * Seçim anahtarından türü çıkarır ('2023' genel, '2024yerel', '2017referandum', '2023cb2tur').
     * scripts/common/election_io.py içindeki tur_of() ile aynı kural.
     */
    public static SecimTuru fromSecimId(String secimId) {
        String k = secimId.toLowerCase();
        if (k.endsWith("yerel")) {
            return YEREL;
        }
        if (k.endsWith("referandum")) {
            return REFERANDUM;
        }
        if (k.endsWith("senato")) {
            return SENATO;
        }
        if (k.matches("\\d{4}cb.*")) {
            return CUMHURBASKANLIGI;
        }
        return GENEL;
    }
}
