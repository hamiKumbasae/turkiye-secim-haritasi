package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.SandalyeIlce;
import tr.secimharitasi.api.varlik.SandalyeIlceId;

public interface SandalyeIlceDeposu extends JpaRepository<SandalyeIlce, SandalyeIlceId> {

    @Query("""
            select s from SandalyeIlce s
            where s.secimId = :secimId and (:ilceId is null or s.ilceId = :ilceId)
              and (:plaka is null or s.ilceId in (select i.ilceId from Ilce i where i.plaka = :plaka))
            order by s.ilceId, s.sandalye desc""")
    List<SandalyeIlce> ara(@Param("secimId") String secimId, @Param("plaka") Integer plaka,
                           @Param("ilceId") String ilceId);
}
