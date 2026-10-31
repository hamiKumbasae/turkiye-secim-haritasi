package io.github.hamikumbasae.election.domain;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LevelAndTypeTest {

    @ParameterizedTest
    @CsvSource({"province,PROVINCE", "IL,PROVINCE", "district,DISTRICT", "ilce,DISTRICT", "İLÇE,DISTRICT",
            "mahalle,NEIGHBOURHOOD", "neighborhood,NEIGHBOURHOOD", "Abroad,ABROAD", "yurtdisi,ABROAD"})
    void parsesEnglishAndTurkishLevelNames(String input, Level expected) {
        assertThat(Level.parse(input)).isEqualTo(expected);
    }

    @Test
    void rejectsUnknownLevel() {
        assertThatThrownBy(() -> Level.parse("county")).isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("province, district");
    }

    @Test
    void mapsDatabaseValues() {
        assertThat(Level.fromDb("ilce")).isEqualTo(Level.DISTRICT);
        assertThat(Level.DISTRICT.apiValue()).isEqualTo("district");
        assertThat(ElectionType.fromDb("cumhurbaskanligi")).isEqualTo(ElectionType.PRESIDENTIAL);
    }

    @ParameterizedTest
    @CsvSource({"general,GENERAL", "genel,GENERAL", "LOCAL,LOCAL", "yerel,LOCAL", "presidential,PRESIDENTIAL",
            "cumhurbaskanligi,PRESIDENTIAL", "Referandum,REFERENDUM"})
    void parsesElectionTypes(String input, ElectionType expected) {
        assertThat(ElectionType.parse(input)).isEqualTo(expected);
    }
}
