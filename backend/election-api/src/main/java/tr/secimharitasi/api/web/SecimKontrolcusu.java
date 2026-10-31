package tr.secimharitasi.api.web;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import tr.secimharitasi.api.servis.EkVeriServisi;
import tr.secimharitasi.api.servis.SecimServisi;
import tr.secimharitasi.common.dto.BeldeSonucDto;
import tr.secimharitasi.common.dto.KapsamDto;
import tr.secimharitasi.common.dto.MahalleSonucDto;
import tr.secimharitasi.common.dto.SandalyeDto;
import tr.secimharitasi.common.dto.SecilenDto;
import tr.secimharitasi.common.dto.IlSonucDto;
import tr.secimharitasi.common.dto.IlceSonucDto;
import tr.secimharitasi.common.dto.SecimDto;

/** Seçimler; il, ilçe, mahalle ve belde sonuçları; seçilenler, sandalyeler, kaynak kapsamı. Yalnız GET. */
@RestController
@RequestMapping("/api/secimler")
public class SecimKontrolcusu {

    private final SecimServisi servis;
    private final EkVeriServisi ek;

    public SecimKontrolcusu(SecimServisi servis, EkVeriServisi ek) {
        this.servis = servis;
        this.ek = ek;
    }

    /**
     * GET /api/secimler?tur=genel&amp;yil=2023, ?oylama=belediye_meclisi, ?yilBaslangic=1950&amp;yilBitis=1980.
     * tur: genel, yerel, referandum, cumhurbaskanligi, senato, ara.
     */
    @GetMapping
    public List<SecimDto> secimler(@RequestParam(required = false) String tur,
                                   @RequestParam(required = false) String oylama,
                                   @RequestParam(required = false) Integer yil,
                                   @RequestParam(required = false) Integer yilBaslangic,
                                   @RequestParam(required = false) Integer yilBitis) {
        return servis.secimler(tur, oylama, yil, yilBaslangic, yilBitis);
    }

    /** Ana seçime bağlı ikincil oylamalar: '2024yerel' -> 2024yerel_bm, 2024yerel_igm, yenileme seçimleri. */
    @GetMapping("/{secimId}/bagli-oylamalar")
    public List<SecimDto> bagliOylamalar(@PathVariable String secimId) {
        return servis.bagliOylamalar(secimId);
    }

    /** Bir ilçenin mahalle/köy sonuçları (2009-2024). */
    @GetMapping("/{secimId}/ilceler/{ilceId}/mahalleler")
    public List<MahalleSonucDto> mahalleler(@PathVariable String secimId, @PathVariable String ilceId) {
        return ek.mahalleler(secimId, ilceId);
    }

    /** Belde belediyeleri; plaka ya da ilceId ile süzülebilir. */
    @GetMapping("/{secimId}/beldeler")
    public List<BeldeSonucDto> beldeler(@PathVariable String secimId, @RequestParam(required = false) Integer plaka,
                                        @RequestParam(required = false) String ilceId) {
        return ek.beldeler(secimId, plaka, ilceId);
    }

    /** Seçilen milletvekilleri / senatörler (kaynak eksik olabilir: /kapsam). */
    @GetMapping("/{secimId}/secilenler")
    public List<SecilenDto> secilenler(@PathVariable String secimId, @RequestParam(required = false) Integer plaka) {
        return ek.secilenler(secimId, plaka);
    }

    /** Parti başına sandalye: il (milletvekili) ve ilçe (2024 belediye meclisi). */
    @GetMapping("/{secimId}/sandalyeler")
    public List<SandalyeDto> sandalyeler(@PathVariable String secimId, @RequestParam(required = false) Integer plaka,
                                         @RequestParam(required = false) String ilceId) {
        return ek.sandalyeler(secimId, plaka, ilceId);
    }

    /** Kaynakta ne kadar kayıt bulunduğu (ör. milletvekili listesi eksikse kaç kişi). */
    @GetMapping("/{secimId}/kapsam")
    public List<KapsamDto> kapsam(@PathVariable String secimId) {
        return ek.kapsam(secimId);
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
