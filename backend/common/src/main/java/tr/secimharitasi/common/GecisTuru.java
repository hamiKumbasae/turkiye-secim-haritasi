package tr.secimharitasi.common;

import com.fasterxml.jackson.annotation.JsonValue;

/** Bir partinin önceki partiyle ilişkisi (parti.onceki_parti_id). */
public enum GecisTuru {
    /** Aynı tüzel kişilik, yalnız adı ya da kısaltması değişti. */
    AD_DEGISIKLIGI("ad_degisikligi"),
    /** Önceki parti kapatıldı/feshedildi; bu parti onun devamı olarak kuruldu. */
    HALEF("halef"),
    /** Önceki parti bu partiye katıldı. */
    BIRLESME("birlesme");

    private final String kod;

    GecisTuru(String kod) {
        this.kod = kod;
    }

    @JsonValue
    public String kod() {
        return kod;
    }

    public static GecisTuru fromKod(String kod) {
        if (kod == null) {
            return null;
        }
        for (GecisTuru t : values()) {
            if (t.kod.equalsIgnoreCase(kod)) {
                return t;
            }
        }
        throw new IllegalArgumentException("Bilinmeyen geçiş türü: " + kod);
    }
}
