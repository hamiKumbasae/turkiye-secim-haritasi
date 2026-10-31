package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.PartyResultDto;
import io.github.hamikumbasae.election.dto.UnitResultDto;
import io.github.hamikumbasae.election.dto.UnitSummaryDto;
import io.github.hamikumbasae.election.repository.UnitRow;
import io.github.hamikumbasae.election.repository.VoteRow;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Row to DTO conversions shared by the services. */
final class Mappers {

    /** Current district geometry ids encode the plate code: TR-D-34-037 is in province 34. */
    private static final Pattern DISTRICT_GEOM = Pattern.compile("^TR-D-(\\d{2})-");

    private Mappers() {
    }

    static Integer plateOf(UnitRow u) {
        if (u.plateCode() != null || u.parentGeomId() == null) {
            return u.plateCode();
        }
        Matcher m = DISTRICT_GEOM.matcher(u.parentGeomId());
        return m.find() ? Integer.valueOf(m.group(1)) : null;
    }

    static UnitSummaryDto summary(UnitRow u) {
        return new UnitSummaryDto(u.level(), plateOf(u), u.name(), u.geomId(), u.registeredVoters(),
                u.validVotes(), u.ballotBoxes(), u.turnout(), u.winner(), seats(u));
    }

    /** Seats are allocated per province; the 0 stored on district rows is not meaningful. */
    static Integer seats(UnitRow u) {
        return u.level() == Level.PROVINCE ? u.seats() : null;
    }

    static UnitResultDto result(String electionCode, UnitRow u, List<VoteRow> votes) {
        List<PartyResultDto> parties = votes == null ? List.of() : votes.stream().map(Mappers::party).toList();
        return new UnitResultDto(electionCode, u.level(), plateOf(u), u.name(), u.geomId(), u.parentGeomId(),
                u.registeredVoters(), u.votesCast(), u.validVotes(), u.ballotBoxes(), u.turnout(), u.winner(),
                seats(u), parties);
    }

    static PartyResultDto party(VoteRow v) {
        return new PartyResultDto(v.party(), v.votes(), v.share(), v.seats(), v.candidate());
    }

    /** Percentage with two decimals, as stored in the database ({@code DECIMAL(7,2)}). */
    static BigDecimal share(long part, long total) {
        if (total <= 0) {
            return null;
        }
        return BigDecimal.valueOf(part).multiply(BigDecimal.valueOf(100))
                .divide(BigDecimal.valueOf(total), 2, RoundingMode.HALF_UP);
    }
}
