package tr.secimharitasi.loader.yukleme;

import java.util.List;
import java.util.Map;

/** Yazıcının veritabanından beklediği üç işlem (uygulamada JdbcTemplate, yerel denemede düz JDBC). */
public interface Hedef {

    void calistir(String sql);

    void toplu(String sql, List<Object[]> satirlar);

    /** parti.ad ve parti_takma_ad.ad -> parti_id */
    Map<String, Integer> partiKimlikleri();
}
