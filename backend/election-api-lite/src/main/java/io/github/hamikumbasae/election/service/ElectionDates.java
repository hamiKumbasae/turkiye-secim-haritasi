package io.github.hamikumbasae.election.service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Election names in the database are Turkish dates, e.g. "14 Mayıs 2023 (1. Tur)". */
public final class ElectionDates {

    private static final Pattern DATE = Pattern.compile("^(\\d{1,2} \\p{L}+ \\d{4})");
    private static final DateTimeFormatter FORMAT = DateTimeFormatter.ofPattern("d MMMM yyyy", Locale.forLanguageTag("tr"));

    private ElectionDates() {
    }

    /** Returns the date in the name, or {@code null} if the name does not start with one. */
    public static LocalDate parse(String name) {
        if (name == null) {
            return null;
        }
        Matcher m = DATE.matcher(name.trim());
        if (!m.find()) {
            return null;
        }
        try {
            return LocalDate.parse(m.group(1), FORMAT);
        } catch (DateTimeParseException e) {
            return null;
        }
    }
}
