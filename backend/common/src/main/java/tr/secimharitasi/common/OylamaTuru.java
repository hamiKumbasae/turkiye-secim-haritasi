package tr.secimharitasi.common;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Sandıkta neyin oylandığı. Aynı günün ikincil oylamaları (ör. yerel seçimde belediye meclisi) ayrı bir
 * seçim kaydıdır ve ana seçime anaSecimId ile bağlanır.
 */
public enum OylamaTuru {
    MILLETVEKILI("milletvekili"),
    BASKANLIK("baskanlik"),
    BELEDIYE_MECLISI("belediye_meclisi"),
    IL_GENEL_MECLISI("il_genel_meclisi"),
    REFERANDUM("referandum"),
    CUMHURBASKANLIGI("cumhurbaskanligi"),
    SENATO("senato");

    private final String kod;

    OylamaTuru(String kod) {
        this.kod = kod;
    }

    @JsonValue
    public String kod() {
        return kod;
    }

    public static OylamaTuru fromKod(String kod) {
        for (OylamaTuru t : values()) {
            if (t.kod.equalsIgnoreCase(kod)) {
                return t;
            }
        }
        throw new IllegalArgumentException("Bilinmeyen oylama türü: " + kod);
    }

    /** Ana seçimin oylaması (ikincil oylamalar hariç). */
    public static OylamaTuru anaOylama(SecimTuru tur) {
        return switch (tur) {
            case GENEL -> MILLETVEKILI;
            case YEREL -> BASKANLIK;
            case REFERANDUM -> REFERANDUM;
            case CUMHURBASKANLIGI -> CUMHURBASKANLIGI;
            case SENATO -> SENATO;
            case ARA -> throw new IllegalArgumentException("Ara seçimin oylaması kayda göre belirlenir");
        };
    }
}
