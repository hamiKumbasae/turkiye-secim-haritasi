package tr.secimharitasi.api.depo;

import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.Mahalle;
import tr.secimharitasi.api.varlik.MahalleId;

public interface MahalleDeposu extends JpaRepository<Mahalle, MahalleId> {

    List<Mahalle> findByIlceIdAndMahalleIdIn(String ilceId, Collection<String> mahalleIdleri);
}
