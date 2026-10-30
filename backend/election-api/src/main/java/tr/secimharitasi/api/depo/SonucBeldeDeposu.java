package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.SonucBelde;

public interface SonucBeldeDeposu extends JpaRepository<SonucBelde, Integer> {

    @Query("""
            select b from SonucBelde b
            where b.secimId = :secimId and (:plaka is null or b.plaka = :plaka)
              and (:ilceId is null or b.ilceId = :ilceId)
            order by b.plaka, b.ilceAd, b.beldeAd, b.sonucBeldeId""")
    List<SonucBelde> ara(@Param("secimId") String secimId, @Param("plaka") Integer plaka,
                         @Param("ilceId") String ilceId);
}
