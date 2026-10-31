package io.github.hamikumbasae.election;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.ElectionDto;
import io.github.hamikumbasae.election.repository.UnitRow;
import io.github.hamikumbasae.election.service.ElectionCatalog;

import java.math.BigDecimal;
import java.time.LocalDate;

/** Small fixtures shared by unit tests (values taken from the real 2023 data). */
public final class TestData {

    public static final ElectionDto GENERAL_2023 =
            new ElectionDto("2023", ElectionType.GENERAL, "14 Mayıs 2023", 2023, LocalDate.of(2023, 5, 14), 600);
    public static final ElectionDto LOCAL_2024 =
            new ElectionDto("2024yerel", ElectionType.LOCAL, "31 Mart 2024", 2024, LocalDate.of(2024, 3, 31), null);
    public static final ElectionDto GENERAL_2002 =
            new ElectionDto("2002", ElectionType.GENERAL, "3 Kasım 2002", 2002, LocalDate.of(2002, 11, 3), 550);

    public static final ElectionCatalog.Entry E2023 = new ElectionCatalog.Entry(24, GENERAL_2023);
    public static final ElectionCatalog.Entry E2024 = new ElectionCatalog.Entry(46, LOCAL_2024);
    public static final ElectionCatalog.Entry E2002 = new ElectionCatalog.Entry(18, GENERAL_2002);

    public static final UnitRow ISTANBUL_2023 = new UnitRow(18590, Level.PROVINCE, 34, "İstanbul", null, null,
            11_367_598L, null, 10_075_874L, 30_849, new BigDecimal("90.53"), "AK Parti", 98);

    public static final UnitRow UMRANIYE_2023 = new UnitRow(19094, Level.DISTRICT, 34, "Ümraniye", "TR-D-34-037", null,
            534_091L, null, 479_616L, 1_445, new BigDecimal("91.45"), "AK Parti", 0);

    public static final UnitRow ADEM_YAVUZ_2023 = new UnitRow(500_000, Level.NEIGHBOURHOOD, null, "ADEM YAVUZ MAH.",
            "tTR-Y-34-037-M-0001", "TR-D-34-037", 12_263L, 11_169L, 10_935L, 33, new BigDecimal("91.08"), "AK Parti", null);

    private TestData() {
    }
}
