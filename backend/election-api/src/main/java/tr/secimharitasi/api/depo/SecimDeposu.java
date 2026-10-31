package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.Secim;

public interface SecimDeposu extends JpaRepository<Secim, String> {

    /** Bir ana seçime bağlı ikincil oylamalar (meclisler, yenileme seçimleri). */
    List<Secim> findByAnaSecimIdOrderBySecimId(String anaSecimId);

    @Query("""
            select s from Secim s
            where (:tur is null or s.tur = :tur)
              and (:oylama is null or s.oylama = :oylama)
              and (:yilBas is null or s.yil >= :yilBas)
              and (:yilBit is null or s.yil <= :yilBit)
            order by s.yil, s.secimId""")
    List<Secim> ara(@Param("tur") String tur, @Param("oylama") String oylama, @Param("yilBas") Integer yilBaslangic,
                    @Param("yilBit") Integer yilBitis);
}
