package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.Level;

import java.math.BigDecimal;

/** One row of {@code birim}: a province, district, neighbourhood or the abroad total of one election. */
public record UnitRow(
        int id,
        Level level,
        Integer plateCode,
        String name,
        String geomId,
        String parentGeomId,
        Long registeredVoters,
        Long votesCast,
        Long validVotes,
        Integer ballotBoxes,
        BigDecimal turnout,
        String winner,
        Integer seats) {
}
