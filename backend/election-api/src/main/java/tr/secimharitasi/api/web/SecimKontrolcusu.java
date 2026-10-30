package tr.secimharitasi.api.web;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import tr.secimharitasi.api.servis.SecimServisi;
import tr.secimharitasi.common.dto.IlSonucDto;
import tr.secimharitasi.common.dto.IlceSonucDto;
import tr.secimharitasi.common.dto.SecimDto;

/** Seçimler, il ve ilçe sonuçları. Yalnız GET. */
@RestController
@RequestMapping("/api/secimler")
public class SecimKontrolcusu {

    private final SecimServisi servis;

    public SecimKontrolcusu(SecimServisi servis) {
        this.servis = servis;
    }

    /** GET /api/secimler?tur=genel&amp;yil=2023 ya da ?yilBaslangic=1950&amp;yilBitis=1980 */
    @GetMapping
    public List<SecimDto> secimler(@RequestParam(required = false) String tur,
                                   @RequestParam(required = false) Integer yil,
                                   @RequestParam(required = false) Integer yilBaslangic,
                                   @RequestParam(required = false) Integer yilBitis) {
        return servis.secimler(tur, yil, yilBaslangic, yilBitis);
    }

    @GetMapping("/{secimId}")
    public SecimDto secim(@PathVariable String secimId) {
        return servis.secim(secimId);
    }

    @GetMapping("/{secimId}/iller")
    public List<IlSonucDto> iller(@PathVariable String secimId) {
        return servis.iller(secimId);
    }

    @GetMapping("/{secimId}/iller/{plaka}")
    public IlSonucDto il(@PathVariable String secimId, @PathVariable int plaka) {
        return servis.il(secimId, plaka);
    }

    @GetMapping("/{secimId}/iller/{plaka}/ilceler")
    public List<IlceSonucDto> ilceler(@PathVariable String secimId, @PathVariable int plaka) {
        return servis.ilceler(secimId, plaka);
    }

    @GetMapping("/{secimId}/ilceler/{ilceId}")
    public IlceSonucDto ilce(@PathVariable String secimId, @PathVariable String ilceId) {
        return servis.ilce(secimId, ilceId);
    }
}
