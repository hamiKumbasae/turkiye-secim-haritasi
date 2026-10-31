package tr.secimharitasi.api.depo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import tr.secimharitasi.api.varlik.Il;

public interface IlDeposu extends JpaRepository<Il, Integer> {

    List<Il> findAllByOrderByPlaka();
}
