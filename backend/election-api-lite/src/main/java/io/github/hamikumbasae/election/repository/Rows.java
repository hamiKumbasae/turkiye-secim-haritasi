package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.Level;

import java.sql.ResultSet;
import java.sql.SQLException;

/** Shared JDBC mapping helpers. */
final class Rows {

    static final String UNIT_COLUMNS = "b.id, b.seviye, b.plaka, b.ad, b.geom_id, b.ust_geom_id, b.secmen, "
            + "b.oy_kullanan, b.gecerli_oy, b.sandik, b.katilim, b.kazanan, b.toplam_vekil";

    private Rows() {
    }

    static UnitRow unit(ResultSet rs) throws SQLException {
        return new UnitRow(
                rs.getInt("id"),
                Level.fromDb(rs.getString("seviye")),
                getInt(rs, "plaka"),
                rs.getString("ad"),
                rs.getString("geom_id"),
                rs.getString("ust_geom_id"),
                getLong(rs, "secmen"),
                getLong(rs, "oy_kullanan"),
                getLong(rs, "gecerli_oy"),
                getInt(rs, "sandik"),
                rs.getBigDecimal("katilim"),
                rs.getString("kazanan"),
                getInt(rs, "toplam_vekil"));
    }

    static Integer getInt(ResultSet rs, String column) throws SQLException {
        int v = rs.getInt(column);
        return rs.wasNull() ? null : v;
    }

    static Long getLong(ResultSet rs, String column) throws SQLException {
        long v = rs.getLong(column);
        return rs.wasNull() ? null : v;
    }

    /** Escapes LIKE wildcards so user input is matched literally. */
    static String likeContains(String text) {
        return "%" + escapeLike(text) + "%";
    }

    static String likePrefix(String text) {
        return escapeLike(text) + "%";
    }

    static String escapeLike(String text) {
        return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
    }

    /** Turkish letters and their ASCII fold; "I", "İ" and "ı" all become "i". */
    private static final String[][] FOLD = {
            {"İ", "i"}, {"I", "i"}, {"ı", "i"}, {"Ç", "c"}, {"ç", "c"}, {"Ğ", "g"}, {"ğ", "g"},
            {"Ö", "o"}, {"ö", "o"}, {"Ş", "s"}, {"ş", "s"}, {"Ü", "u"}, {"ü", "u"}};

    /**
     * SQL expression comparing {@code column} the way people type Turkish names: case-insensitive and
     * insensitive to Turkish letters, so "umraniye", "ÜMRANİYE", "Ümraniye" and "UMRANIYE" are all equal.
     * Plain Turkish collation is not enough: under utf8mb4_turkish_ci "ISTANBUL" (dotless I) differs from
     * "İstanbul", and "u" differs from "ü". REPLACE is case-sensitive, so every letter is folded explicitly;
     * the rest is left to a case-insensitive collation. Pair it with {@link #fold(String)} on the parameter.
     */
    static String folded(String column) {
        String sql = column;
        for (String[] f : FOLD) {
            sql = "REPLACE(" + sql + ", '" + f[0] + "', '" + f[1] + "')";
        }
        return sql + " COLLATE utf8mb4_general_ci";
    }

    /** Java counterpart of {@link #folded(String)}. */
    static String fold(String s) {
        String out = s;
        for (String[] f : FOLD) {
            out = out.replace(f[0], f[1]);
        }
        return out.toLowerCase(java.util.Locale.ROOT);
    }
}
