package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.Secilen;

public interface SecilenDeposu extends JpaRepository<Secilen, Integer> {

    @Query("""
            select s from Secilen s
            where s.secimId = :secimId and (:plaka is null or s.plaka = :plaka)
            order by s.plaka, s.bolge, s.ad""")
    List<Secilen> ara(@Param("secimId") String secimId, @Param("plaka") Integer plaka);
}
