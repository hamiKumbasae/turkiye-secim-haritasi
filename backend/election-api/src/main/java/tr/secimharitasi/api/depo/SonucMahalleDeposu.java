package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.SonucMahalle;
import tr.secimharitasi.api.varlik.SonucMahalleId;

public interface SonucMahalleDeposu extends JpaRepository<SonucMahalle, SonucMahalleId> {

    List<SonucMahalle> findBySecimIdAndIlceId(String secimId, String ilceId);
}
