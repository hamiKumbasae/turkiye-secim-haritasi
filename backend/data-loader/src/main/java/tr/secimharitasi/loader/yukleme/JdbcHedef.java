package tr.secimharitasi.loader.yukleme;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;

/** Uygulamadaki hedef: Spring JdbcTemplate, toplu ekleme parça parça. */
public class JdbcHedef implements Hedef {

    private final JdbcTemplate jdbc;
    private final int parca;

    public JdbcHedef(JdbcTemplate jdbc, int parca) {
        this.jdbc = jdbc;
        this.parca = parca;
    }

    @Override
    public void calistir(String sql) {
        jdbc.update(sql);
    }

    @Override
    public void toplu(String sql, List<Object[]> satirlar) {
        for (int i = 0; i < satirlar.size(); i += parca) {
            jdbc.batchUpdate(sql, satirlar.subList(i, Math.min(i + parca, satirlar.size())));
        }
    }

    @Override
    public Map<String, Integer> partiKimlikleri() {
        Map<String, Integer> m = new HashMap<>();
        jdbc.query("SELECT ad, parti_id FROM parti UNION ALL SELECT ad, parti_id FROM parti_takma_ad",
                rs -> {
                    m.put(rs.getString(1), rs.getInt(2));
                });
        return m;
    }
}
