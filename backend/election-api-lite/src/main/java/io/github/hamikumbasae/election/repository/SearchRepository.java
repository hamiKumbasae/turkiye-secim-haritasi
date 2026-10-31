package io.github.hamikumbasae.election.repository;

import io.github.hamikumbasae.election.domain.Level;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Name search over all units. */
@Repository
public class SearchRepository {

    private static final String FOLDED_NAME = Rows.folded("b.ad");

    private final NamedParameterJdbcTemplate jdbc;

    public SearchRepository(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /** One distinct place; {@code electionIds} lists every election it has a result row in. */
    public record Hit(Level level, Integer plateCode, String name, String geomId, String parentGeomId,
                      List<Integer> electionIds) {
    }

    public record HitPage(List<Hit> hits, long total) {
    }

    /**
     * {@code LIKE '%text%'} cannot seek an index, so the query is shaped to be a single pass: no join, GROUP BY
     * in index order (an index-only scan with sql/indexes.sql applied) and the total from a window function
     * instead of a second COUNT query. The explicit collation keeps matching Turkish-aware even if the server's
     * default collation differs.
     */
    public HitPage search(String rawQuery, Level level, Integer electionId, int limit, long offset) {
        String query = Rows.fold(rawQuery);
        MapSqlParameterSource p = new MapSqlParameterSource()
                .addValue("q", Rows.likeContains(query))
                .addValue("exact", query)
                .addValue("prefix", Rows.likePrefix(query))
                .addValue("limit", limit)
                .addValue("offset", offset);
        StringBuilder sql = new StringBuilder("""
                SELECT b.ad, b.seviye, b.geom_id, b.ust_geom_id, MAX(b.plaka) AS plaka,
                       GROUP_CONCAT(b.secim_id) AS secimler, COUNT(*) OVER () AS toplam
                FROM birim b
                """ + "WHERE " + FOLDED_NAME + " LIKE :q");
        if (level != null) {
            sql.append(" AND b.seviye = :level");
            p.addValue("level", level.dbValue());
        }
        if (electionId != null) {
            sql.append(" AND b.secim_id = :election");
            p.addValue("election", electionId);
        }
        sql.append("""
                 GROUP BY b.ad, b.seviye, b.geom_id, b.ust_geom_id
                ORDER BY (%1$s = :exact) DESC,
                         (%1$s LIKE :prefix) DESC,
                         FIELD(b.seviye, 'il', 'ilce', 'mahalle', 'yurtdisi'), b.ad, COUNT(*) DESC, b.geom_id
                LIMIT :limit OFFSET :offset""".formatted(FOLDED_NAME));
        long[] total = {0};
        List<Hit> hits = jdbc.query(sql.toString(), p, (rs, i) -> {
            total[0] = rs.getLong("toplam");
            return new Hit(Level.fromDb(rs.getString("seviye")), Rows.getInt(rs, "plaka"), rs.getString("ad"),
                    rs.getString("geom_id"), rs.getString("ust_geom_id"), ids(rs.getString("secimler")));
        });
        if (hits.isEmpty() && offset > 0) {
            // Past the last page: the window total is unknown, count separately.
            return new HitPage(hits, search(rawQuery, level, electionId, 1, 0).total());
        }
        return new HitPage(hits, total[0]);
    }

    private static List<Integer> ids(String csv) {
        return csv == null || csv.isEmpty() ? List.of()
                : Arrays.stream(csv.split(",")).map(Integer::valueOf).distinct().toList();
    }

    public record DistrictName(String name, Integer plateCode) {
    }

    /** Name and plate of each district geometry id (to label neighbourhood hits). */
    public Map<String, DistrictName> districtNames(Collection<String> geomIds) {
        Map<String, DistrictName> names = new HashMap<>();
        if (geomIds.isEmpty()) {
            return names;
        }
        String sql = "SELECT geom_id, MAX(ad) AS ad, MAX(plaka) AS plaka FROM birim"
                + " WHERE seviye = 'ilce' AND geom_id IN (:ids) GROUP BY geom_id";
        jdbc.query(sql, Map.of("ids", geomIds), rs -> {
            names.put(rs.getString("geom_id"), new DistrictName(rs.getString("ad"), Rows.getInt(rs, "plaka")));
        });
        return names;
    }
}
