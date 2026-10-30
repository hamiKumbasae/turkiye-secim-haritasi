package tr.secimharitasi.api.depo;

import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.OyBelde;
import tr.secimharitasi.api.varlik.OyBeldeId;

public interface OyBeldeDeposu extends JpaRepository<OyBelde, OyBeldeId> {

    List<OyBelde> findBySonucBeldeIdIn(Collection<Integer> beldeler);
}
