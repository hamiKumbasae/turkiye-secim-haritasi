package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.SonucIl;
import tr.secimharitasi.api.varlik.SonucIlId;

public interface SonucIlDeposu extends JpaRepository<SonucIl, SonucIlId> {

    List<SonucIl> findBySecimIdOrderByPlaka(String secimId);

    /** Seçim başına yurt içi geçerli oy toplamı (plaka > 0): Türkiye geneli oranın paydası. */
    @Query("""
            select new tr.secimharitasi.api.depo.GecerliOyToplami(s.secimId, sum(s.gecerliOy))
            from SonucIl s where s.plaka > 0 and s.secimId in :secimler group by s.secimId""")
    List<GecerliOyToplami> yurtIciGecerliOy(@Param("secimler") List<String> secimler);
}
