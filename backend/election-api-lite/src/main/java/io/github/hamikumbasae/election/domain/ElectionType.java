package io.github.hamikumbasae.election.domain;

import com.fasterxml.jackson.annotation.JsonValue;

import java.util.Arrays;
import java.util.Locale;

/** Kind of election ({@code secim.tur}). */
public enum ElectionType {
    GENERAL("genel"),
    LOCAL("yerel"),
    PRESIDENTIAL("cumhurbaskanligi"),
    REFERENDUM("referandum");

    private final String dbValue;

    ElectionType(String dbValue) {
        this.dbValue = dbValue;
    }

    public String dbValue() {
        return dbValue;
    }

    @JsonValue
    public String apiValue() {
        return name().toLowerCase(Locale.ROOT);
    }

    public static ElectionType fromDb(String value) {
        return Arrays.stream(values()).filter(t -> t.dbValue.equals(value)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown election type in database: " + value));
    }

    /** Accepts the English API name or the Turkish database value, case-insensitively. */
    public static ElectionType parse(String value) {
        String v = Names.fold(value);
        for (ElectionType t : values()) {
            if (t.apiValue().equals(v) || t.dbValue.equals(v)) {
                return t;
            }
        }
        throw new IllegalArgumentException("Unknown election type '" + value
                + "'. Use one of: general, local, presidential, referendum");
    }
}
