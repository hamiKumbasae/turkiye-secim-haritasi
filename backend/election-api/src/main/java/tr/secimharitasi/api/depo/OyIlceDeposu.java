package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.OyIlce;
import tr.secimharitasi.api.varlik.OyIlceId;

public interface OyIlceDeposu extends JpaRepository<OyIlce, OyIlceId> {

    List<OyIlce> findBySecimIdAndIlceId(String secimId, String ilceId);

    @Query("""
            select o from OyIlce o
            where o.secimId = :secimId
              and o.ilceId in (select sc.ilceId from SonucIlce sc where sc.secimId = :secimId and sc.plaka = :plaka)""")
    List<OyIlce> ildekiIlceler(@Param("secimId") String secimId, @Param("plaka") int plaka);
}
