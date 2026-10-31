package tr.secimharitasi.common.dto;

import java.util.List;
import tr.secimharitasi.common.GecisTuru;
import tr.secimharitasi.common.SecenekTipi;

/**
 * @param oncekiler onceki_parti_id zinciri, en yakından en eskiye (yalnız tek parti istendiğinde dolu)
 */
public record PartiDto(int partiId, String ad, String kisa, SecenekTipi tip, String renk, Integer oncekiPartiId,
                       GecisTuru gecisTuru, Integer gecisYili, String gecisKaynagi, List<PartiDto> oncekiler) {
}
