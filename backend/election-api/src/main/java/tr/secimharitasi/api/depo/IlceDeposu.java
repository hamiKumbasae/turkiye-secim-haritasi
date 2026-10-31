package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.Ilce;

public interface IlceDeposu extends JpaRepository<Ilce, String> {

    /** yil verilirse yalnız o yıl veride bulunan ilçe birimleri (baslangic_yili ≤ yil ≤ bitis_yili). */
    @Query("""
            select i from Ilce i
            where i.plaka = :plaka
              and (:yil is null or (i.baslangicYili <= :yil and (i.bitisYili is null or i.bitisYili >= :yil)))
            order by i.ad""")
    List<Ilce> ildekiler(@Param("plaka") int plaka, @Param("yil") Integer yil);
}
