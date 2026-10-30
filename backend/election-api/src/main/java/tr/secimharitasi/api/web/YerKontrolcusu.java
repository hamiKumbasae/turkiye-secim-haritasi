package tr.secimharitasi.api.web;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import tr.secimharitasi.api.servis.SecimServisi;
import tr.secimharitasi.common.dto.IlDto;
import tr.secimharitasi.common.dto.IlceDto;

/** İl ve ilçe sözlükleri. */
@RestController
@RequestMapping("/api/iller")
public class YerKontrolcusu {

    private final SecimServisi servis;

    public YerKontrolcusu(SecimServisi servis) {
        this.servis = servis;
    }

    @GetMapping
    public List<IlDto> iller() {
        return servis.butunIller();
    }

    /** GET /api/iller/34/ilceler?yil=1990 — o yıl veride bulunan ilçe birimleri */
    @GetMapping("/{plaka}/ilceler")
    public List<IlceDto> ilceler(@PathVariable int plaka, @RequestParam(required = false) Integer yil) {
        return servis.ildekiIlceler(plaka, yil);
    }
}
