package tr.secimharitasi.common;

import com.fasterxml.jackson.annotation.JsonValue;

/** Oy verilen seçeneğin tipi. parti tablosu partiler yanında aday, Evet/Hayır ve Diğer/Bağımsız'ı da tutar. */
public enum SecenekTipi {
    PARTI("parti"),
    ADAY("aday"),
    REFERANDUM("referandum"),
    DIGER("diger");

    private final String kod;

    SecenekTipi(String kod) {
        this.kod = kod;
    }

    @JsonValue
    public String kod() {
        return kod;
    }

    public static SecenekTipi fromKod(String kod) {
        for (SecenekTipi t : values()) {
            if (t.kod.equalsIgnoreCase(kod)) {
                return t;
            }
        }
        throw new IllegalArgumentException("Bilinmeyen seçenek tipi: " + kod);
    }
}
