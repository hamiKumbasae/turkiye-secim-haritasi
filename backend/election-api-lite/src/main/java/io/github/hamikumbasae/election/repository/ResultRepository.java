package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.Level;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Results of single units and their vote rows. Plain SQL via JdbcTemplate: the queries are
 * index-driven lookups and aggregations that do not benefit from an entity graph.
 */
@Repository
public class ResultRepository {

    private final NamedParameterJdbcTemplate jdbc;

    public ResultRepository(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /** Filter for {@link #findUnits}: {@code null} fields are ignored. */
    public record UnitFilter(int electionId, Level level, Integer plateCode, String geomId, String parentGeomId) {

        String where(MapSqlParameterSource p) {
            StringBuilder sql = new StringBuilder(" WHERE b.secim_id = :election AND b.seviye = :level");
            p.addValue("election", electionId).addValue("level", level.dbValue());
            if (plateCode != null) {
                sql.append(" AND b.plaka = :plate");
                p.addValue("plate", plateCode);
            }
            if (geomId != null) {
                sql.append(" AND b.geom_id = :geomId");
                p.addValue("geomId", geomId);
            }
            if (parentGeomId != null) {
                sql.append(" AND b.ust_geom_id = :parent");
                p.addValue("parent", parentGeomId);
            }
            return sql.toString();
        }
    }

    public List<UnitRow> findUnits(UnitFilter filter, int limit, long offset) {
        MapSqlParameterSource p = new MapSqlParameterSource();
        String sql = "SELECT " + Rows.UNIT_COLUMNS + " FROM birim b" + filter.where(p)
                + " ORDER BY b.plaka, b.ad, b.id LIMIT :limit OFFSET :offset";
        p.addValue("limit", limit).addValue("offset", offset);
        return jdbc.query(sql, p, (rs, i) -> Rows.unit(rs));
    }

    public long countUnits(UnitFilter filter) {
        MapSqlParameterSource p = new MapSqlParameterSource();
        Long n = jdbc.queryForObject("SELECT COUNT(*) FROM birim b" + filter.where(p), p, Long.class);
        return n == null ? 0 : n;
    }

    public Optional<UnitRow> findUnit(UnitFilter filter) {
        return findUnits(filter, 1, 0).stream().findFirst();
    }

    /** Vote rows of the given units, each list sorted by votes descending. */
    public Map<Integer, List<VoteRow>> findVotes(Collection<Integer> unitIds) {
        Map<Integer, List<VoteRow>> byUnit = new LinkedHashMap<>();
        if (unitIds.isEmpty()) {
            return byUnit;
        }
        String sql = "SELECT o.birim_id, o.aday_parti, o.oy, o.oran, o.vekil, o.aday FROM oy o"
                + " WHERE o.birim_id IN (:ids) ORDER BY o.birim_id, o.oy DESC, o.aday_parti";
        jdbc.query(sql, Map.of("ids", unitIds), rs -> {
            VoteRow v = new VoteRow(rs.getInt("birim_id"), rs.getString("aday_parti"),
                    rs.getLong("oy"), rs.getBigDecimal("oran"), Rows.getInt(rs, "vekil"), rs.getString("aday"));
            byUnit.computeIfAbsent(v.unitId(), k -> new java.util.ArrayList<>()).add(v);
        });
        return byUnit;
    }

    /** Party totals of province rows plus the abroad row (one per election). */
    public List<VoteRow> nationalPartyTotals(int electionId) {
        String sql = """
                SELECT o.aday_parti, SUM(o.oy) AS votes, SUM(o.vekil) AS seats
                FROM birim b JOIN oy o ON o.birim_id = b.id
                WHERE b.secim_id = :election AND b.seviye IN ('il', 'yurtdisi')
                GROUP BY o.aday_parti
                ORDER BY votes DESC, o.aday_parti""";
        return jdbc.query(sql, Map.of("election", electionId), (rs, i) -> new VoteRow(0,
                rs.getString("aday_parti"), rs.getLong("votes"), null, Rows.getInt(rs, "seats"), null));
    }

    public record NationalTotals(long registeredVoters, long validVotes, BigDecimal turnout,
                                 int provinces, boolean includesAbroad) {
    }

    public NationalTotals nationalTotals(int electionId) {
        String sql = """
                SELECT COALESCE(SUM(b.secmen), 0) AS secmen,
                       COALESCE(SUM(b.gecerli_oy), 0) AS gecerli,
                       SUM(b.katilim * b.secmen) / SUM(CASE WHEN b.katilim IS NOT NULL THEN b.secmen END) AS katilim,
                       COALESCE(SUM(b.seviye = 'il'), 0) AS iller,
                       COALESCE(SUM(b.seviye = 'yurtdisi'), 0) AS yurtdisi
                FROM birim b
                WHERE b.secim_id = :election AND b.seviye IN ('il', 'yurtdisi')""";
        return jdbc.queryForObject(sql, Map.of("election", electionId), (rs, i) -> {
            BigDecimal turnout = rs.getBigDecimal("katilim");
            return new NationalTotals(rs.getLong("secmen"), rs.getLong("gecerli"),
                    turnout == null ? null : turnout.setScale(2, java.math.RoundingMode.HALF_UP),
                    rs.getInt("iller"), rs.getInt("yurtdisi") > 0);
        });
    }
}
