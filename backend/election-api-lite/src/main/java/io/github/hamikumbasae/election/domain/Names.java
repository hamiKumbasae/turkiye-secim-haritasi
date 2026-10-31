package io.github.hamikumbasae.election.domain;

import java.util.Locale;

/** Normalises user-typed enum names: "İLÇE", "ilçe", "Ilce" and "ILCE" all become "ilce". */
final class Names {

    private static final Locale TR = Locale.forLanguageTag("tr");

    private Names() {
    }

    static String fold(String value) {
        // Lower-casing with Turkish rules turns "I" into "ı", so fold dotless i (and other Turkish letters)
        // back to ASCII afterwards; the result is the same whichever case the user typed.
        StringBuilder sb = new StringBuilder();
        for (char c : value.trim().toLowerCase(TR).toCharArray()) {
            sb.append(switch (c) {
                case 'ı' -> 'i';
                case 'ç' -> 'c';
                case 'ş' -> 's';
                case 'ğ' -> 'g';
                case 'ü' -> 'u';
                case 'ö' -> 'o';
                default -> c;
            });
        }
        return sb.toString();
    }
}
