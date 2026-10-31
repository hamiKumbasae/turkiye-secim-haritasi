package io.github.hamikumbasae.election.service;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class ElectionDatesTest {

    @ParameterizedTest
    @CsvSource(delimiter = '|', value = {
            "14 Mayıs 2023 (1. Tur)|2023-05-14",
            "10 Ağustos 2014|2014-08-10",
            "1 Kasım 2015|2015-11-01",
            "24 Aralık 1995|1995-12-24",
            "6 Eylül 1987|1987-09-06",
            "31 Mart 2024|2024-03-31"})
    void parsesTurkishDates(String name, LocalDate expected) {
        assertThat(ElectionDates.parse(name)).isEqualTo(expected);
    }

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {"Genel seçim", "32 Mayıs 2023"})
    void returnsNullWhenThereIsNoDate(String name) {
        assertThat(ElectionDates.parse(name)).isNull();
    }
}
