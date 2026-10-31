package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;

/** Cross-unit and cross-election queries: party history and top-N rankings. */
@Repository
public class AnalyticsRepository {

    private final NamedParameterJdbcTemplate jdbc;

    public AnalyticsRepository(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public record HistoryRow(int electionId, String party, String unitName, String geomId, String winner,
                             long votes, BigDecimal share, int rank) {
    }

    /**
     * Votes of {@code party} in a province (or one of its districts, matched by name) in every election.
     * Names are compared case- and Turkish-letter-insensitively (see {@link Rows#folded}): "umraniye" finds
     * "Ümraniye", "chp" finds "CHP" and "IYI PARTI" finds "İYİ Parti".
     * Districts are matched by name because their geometry ids change when boundaries are redrawn.
     */
    public List<HistoryRow> partyHistory(String party, int plateCode, String districtName, ElectionType type) {
        MapSqlParameterSource p = new MapSqlParameterSource()
                .addValue("party", Rows.fold(party)).addValue("plate", plateCode);
        StringBuilder sql = new StringBuilder("""
                SELECT b.secim_id, o.aday_parti, b.ad, b.geom_id, b.kazanan, o.oy, o.oran,
                       (SELECT COUNT(*) FROM oy o2 WHERE o2.birim_id = b.id AND o2.oy > o.oy) + 1 AS sira
                FROM birim b
                JOIN oy o ON o.birim_id = b.id AND %s = :party
                """.formatted(Rows.folded("o.aday_parti")));
        if (type != null) {
            sql.append(" JOIN secim s ON s.id = b.secim_id AND s.tur = :type");
            p.addValue("type", type.dbValue());
        }
        sql.append(" WHERE b.plaka = :plate");
        if (districtName != null) {
            sql.append(" AND b.seviye = 'ilce' AND ").append(Rows.folded("b.ad")).append(" = :district");
            p.addValue("district", Rows.fold(districtName));
        } else {
            sql.append(" AND b.seviye = 'il'");
        }
        return jdbc.query(sql.toString(), p, (rs, i) -> new HistoryRow(rs.getInt("secim_id"), rs.getString("aday_parti"), rs.getString("ad"),
                rs.getString("geom_id"), rs.getString("kazanan"), rs.getLong("oy"), rs.getBigDecimal("oran"),
                rs.getInt("sira")));
    }

    /** Scope of a ranking: all units of a level, optionally within one province or one district. */
    public record RankingScope(int electionId, Level level, Integer plateCode, String parentGeomId) {

        String where(MapSqlParameterSource p) {
            StringBuilder sql = new StringBuilder(" WHERE b.secim_id = :election AND b.seviye = :level");
            p.addValue("election", electionId).addValue("level", level.dbValue());
            if (plateCode != null) {
                sql.append(" AND b.plaka = :plate");
                p.addValue("plate", plateCode);
            }
            if (parentGeomId != null) {
                sql.append(" AND b.ust_geom_id = :parent");
                p.addValue("parent", parentGeomId);
            }
            return sql.toString();
        }
    }

    public record RankedUnit(UnitRow unit, BigDecimal value, Long votes) {
    }

    /**
     * Units ordered by turnout. Rows with turnout above 100% (a known artefact of the
     * neighbourhood-level source data) and units smaller than {@code minVoters} are left out.
     */
    public List<RankedUnit> byTurnout(RankingScope scope, boolean descending, long minVoters, int limit) {
        MapSqlParameterSource p = new MapSqlParameterSource();
        String sql = "SELECT " + Rows.UNIT_COLUMNS + " FROM birim b" + scope.where(p)
                + " AND b.katilim IS NOT NULL AND b.katilim <= 100 AND COALESCE(b.secmen, 0) >= :minVoters"
                + " ORDER BY b.katilim " + (descending ? "DESC" : "ASC") + ", b.secmen DESC LIMIT :limit";
        p.addValue("minVoters", minVoters).addValue("limit", limit);
        return jdbc.query(sql, p, (rs, i) -> {
            UnitRow u = Rows.unit(rs);
            return new RankedUnit(u, u.turnout(), u.registeredVoters());
        });
    }

    /** Units ordered by the vote share of one party. */
    public List<RankedUnit> byPartyShare(RankingScope scope, String party, boolean descending, long minVoters,
                                         int limit) {
        MapSqlParameterSource p = new MapSqlParameterSource().addValue("party", Rows.fold(party));
        String sql = "SELECT " + Rows.UNIT_COLUMNS + ", o.oy AS parti_oy, o.oran AS parti_oran FROM birim b"
                + " JOIN oy o ON o.birim_id = b.id AND " + Rows.folded("o.aday_parti") + " = :party" + scope.where(p)
                + " AND o.oran IS NOT NULL AND COALESCE(b.secmen, 0) >= :minVoters"
                + " ORDER BY o.oran " + (descending ? "DESC" : "ASC") + ", o.oy DESC LIMIT :limit";
        p.addValue("minVoters", minVoters).addValue("limit", limit);
        return jdbc.query(sql, p, (rs, i) ->
                new RankedUnit(Rows.unit(rs), rs.getBigDecimal("parti_oran"), rs.getLong("parti_oy")));
    }
}
