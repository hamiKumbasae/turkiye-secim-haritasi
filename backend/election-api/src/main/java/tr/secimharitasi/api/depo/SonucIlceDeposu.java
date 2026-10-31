package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.SonucIlce;
import tr.secimharitasi.api.varlik.SonucIlceId;

public interface SonucIlceDeposu extends JpaRepository<SonucIlce, SonucIlceId> {

    List<SonucIlce> findBySecimIdAndPlakaOrderByAd(String secimId, Integer plaka);
}
