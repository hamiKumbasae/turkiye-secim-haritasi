package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.Parti;

public interface PartiDeposu extends JpaRepository<Parti, Integer> {

    List<Parti> findAllByOrderByPartiId();

    List<Parti> findByTipOrderByPartiId(String tip);
}
