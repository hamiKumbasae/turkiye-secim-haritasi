package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.OyMahalle;
import tr.secimharitasi.api.varlik.OyMahalleId;

public interface OyMahalleDeposu extends JpaRepository<OyMahalle, OyMahalleId> {

    List<OyMahalle> findBySecimIdAndIlceId(String secimId, String ilceId);
}
