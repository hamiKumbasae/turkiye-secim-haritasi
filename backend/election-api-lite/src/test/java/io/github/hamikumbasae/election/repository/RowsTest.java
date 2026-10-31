package io.github.hamikumbasae.election.repository;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static org.assertj.core.api.Assertions.assertThat;

class RowsTest {

    @Test
    void likePatternsEscapeWildcards() {
        assertThat(Rows.likeContains("50%_a\\b")).isEqualTo("%50\\%\\_a\\\\b%");
        assertThat(Rows.likePrefix("um")).isEqualTo("um%");
    }

    @ParameterizedTest
    @ValueSource(strings = {"Ümraniye", "ÜMRANİYE", "ümraniye", "UMRANIYE", "umraniye", "ÜMRANIYE"})
    void turkishSpellingsFoldToTheSameKey(String spelling) {
        assertThat(Rows.fold(spelling)).isEqualTo("umraniye");
    }

    @Test
    void foldsEveryTurkishLetter() {
        assertThat(Rows.fold("ÇĞİÖŞÜ çğıöşü I")).isEqualTo("cgiosu cgiosu i");
        assertThat(Rows.fold("İYİ Parti")).isEqualTo("iyi parti");
    }

    @Test
    void sqlExpressionFoldsTheColumnTheSameWay() {
        String sql = Rows.folded("b.ad");
        assertThat(sql).startsWith("REPLACE(REPLACE(").contains("'ı', 'i'").contains("'Ü', 'u'")
                .endsWith(" COLLATE utf8mb4_general_ci");
        assertThat(sql.split("REPLACE\\(", -1)).hasSize(14);
    }
}
