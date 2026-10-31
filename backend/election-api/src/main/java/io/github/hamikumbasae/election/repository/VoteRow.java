package io.github.hamikumbasae.election.repository;

import java.math.BigDecimal;

/** One row of {@code oy}. */
public record VoteRow(int unitId, String party, long votes, BigDecimal share, Integer seats, String candidate) {
}
