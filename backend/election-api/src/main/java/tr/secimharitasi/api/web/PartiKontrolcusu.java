package tr.secimharitasi.api.web;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import tr.secimharitasi.api.servis.PartiServisi;
import tr.secimharitasi.common.dto.PartiDto;
import tr.secimharitasi.common.dto.PartiSonucDto;

/** Parti bazlı sorgular. */
@RestController
@RequestMapping("/api/partiler")
public class PartiKontrolcusu {

    private final PartiServisi servis;

    public PartiKontrolcusu(PartiServisi servis) {
        this.servis = servis;
    }

    /** GET /api/partiler?tip=parti|aday|referandum|diger */
    @GetMapping
    public List<PartiDto> partiler(@RequestParam(required = false) String tip) {
        return servis.partiler(tip);
    }

    /** Parti ve öncülleri (onceki_parti_id zinciri). */
    @GetMapping("/{partiId}")
    public PartiDto parti(@PathVariable int partiId) {
        return servis.parti(partiId);
    }

    /**
     * GET /api/partiler/2/sonuclar?tur=genel&amp;yilBaslangic=1950&amp;plaka=34&amp;zincir=true
     * plaka yoksa Türkiye geneli; zincir=true öncül partilerin sonuçlarını da ekler.
     */
    @GetMapping("/{partiId}/sonuclar")
    public List<PartiSonucDto> sonuclar(@PathVariable int partiId,
                                        @RequestParam(required = false) String tur,
                                        @RequestParam(required = false) Integer yil,
                                        @RequestParam(required = false) Integer yilBaslangic,
                                        @RequestParam(required = false) Integer yilBitis,
                                        @RequestParam(required = false) Integer plaka,
                                        @RequestParam(defaultValue = "false") boolean zincir) {
        Integer bas = yil != null ? yil : yilBaslangic;
        Integer bit = yil != null ? yil : yilBitis;
        return servis.sonuclar(partiId, tur, bas, bit, plaka, zincir);
    }

    /** GET /api/partiler/2/secimler/2023/en-guclu-iller?limit=10 */
    @GetMapping("/{partiId}/secimler/{secimId}/en-guclu-iller")
    public List<PartiSonucDto> enGucluIller(@PathVariable int partiId, @PathVariable String secimId,
                                            @RequestParam(defaultValue = "10") int limit) {
        return servis.enGucluIller(partiId, secimId, limit);
    }
}
