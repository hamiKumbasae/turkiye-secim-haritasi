package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.KaynakKapsami;
import tr.secimharitasi.api.varlik.KaynakKapsamiId;

public interface KaynakKapsamiDeposu extends JpaRepository<KaynakKapsami, KaynakKapsamiId> {

    List<KaynakKapsami> findBySecimIdOrderByVeri(String secimId);
}
