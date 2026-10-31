package io.github.hamikumbasae.election.domain;

import com.fasterxml.jackson.annotation.JsonValue;

import java.util.Arrays;
import java.util.Locale;

/**
 * Administrative level of a result row ({@code birim.seviye}).
 * The API speaks English ({@code province}); the database stores Turkish ({@code il}).
 */
public enum Level {
    PROVINCE("il"),
    DISTRICT("ilce"),
    NEIGHBOURHOOD("mahalle"),
    ABROAD("yurtdisi");

    private final String dbValue;

    Level(String dbValue) {
        this.dbValue = dbValue;
    }

    public String dbValue() {
        return dbValue;
    }

    @JsonValue
    public String apiValue() {
        return name().toLowerCase(Locale.ROOT);
    }

    public static Level fromDb(String value) {
        return Arrays.stream(values()).filter(l -> l.dbValue.equals(value)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown level in database: " + value));
    }

    /** Accepts the English API name or the Turkish database value, case-insensitively. */
    public static Level parse(String value) {
        String v = Names.fold(value);
        for (Level l : values()) {
            if (l.apiValue().equals(v) || l.dbValue.equals(v)) {
                return l;
            }
        }
        if (v.equals("neighborhood")) {
            return NEIGHBOURHOOD;
        }
        throw new IllegalArgumentException("Unknown level '" + value
                + "'. Use one of: province, district, neighbourhood, abroad");
    }
}
