package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.SandalyeIl;
import tr.secimharitasi.api.varlik.SandalyeIlId;

public interface SandalyeIlDeposu extends JpaRepository<SandalyeIl, SandalyeIlId> {

    @Query("""
            select s from SandalyeIl s where s.secimId = :secimId and (:plaka is null or s.plaka = :plaka)
            order by s.plaka, s.sandalye desc""")
    List<SandalyeIl> ara(@Param("secimId") String secimId, @Param("plaka") Integer plaka);
}
