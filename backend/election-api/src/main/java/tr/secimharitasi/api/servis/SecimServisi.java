package tr.secimharitasi.api.servis;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tr.secimharitasi.api.depo.IlDeposu;
import tr.secimharitasi.api.depo.IlceDeposu;
import tr.secimharitasi.api.depo.OyIlDeposu;
import tr.secimharitasi.api.depo.OyIlceDeposu;
import tr.secimharitasi.api.depo.PartiDeposu;
import tr.secimharitasi.api.depo.SecimDeposu;
import tr.secimharitasi.api.depo.SonucIlDeposu;
import tr.secimharitasi.api.depo.SonucIlceDeposu;
import tr.secimharitasi.api.varlik.Ilce;
import tr.secimharitasi.api.varlik.OyIl;
import tr.secimharitasi.api.varlik.OyIlce;
import tr.secimharitasi.api.varlik.Secim;
import tr.secimharitasi.api.varlik.SonucIl;
import tr.secimharitasi.api.varlik.SonucIlId;
import tr.secimharitasi.api.varlik.SonucIlce;
import tr.secimharitasi.api.varlik.SonucIlceId;
import tr.secimharitasi.common.OylamaTuru;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.common.dto.IlDto;
import tr.secimharitasi.common.dto.IlSonucDto;
import tr.secimharitasi.common.dto.IlceDto;
import tr.secimharitasi.common.dto.IlceSonucDto;
import tr.secimharitasi.common.dto.OyDto;
import tr.secimharitasi.common.dto.SecimDto;

@Service
@Transactional(readOnly = true)
public class SecimServisi {

    /** Oylar: en çok oydan aza; oyu bilinmeyenler (yalnız kazananı bilinen kayıtlar) sonda. */
    static final Comparator<OyDto> OY_SIRASI = Comparator
            .comparing(OyDto::oy, Comparator.nullsLast(Comparator.reverseOrder()))
            .thenComparing(OyDto::parti, Comparator.nullsLast(Comparator.naturalOrder()));

    private final SecimDeposu secimler;
    private final IlDeposu iller;
    private final IlceDeposu ilceler;
    private final PartiDeposu partiler;
    private final SonucIlDeposu sonucIl;
    private final OyIlDeposu oyIl;
    private final SonucIlceDeposu sonucIlce;
    private final OyIlceDeposu oyIlce;

    public SecimServisi(SecimDeposu secimler, IlDeposu iller, IlceDeposu ilceler, PartiDeposu partiler,
                        SonucIlDeposu sonucIl, OyIlDeposu oyIl, SonucIlceDeposu sonucIlce, OyIlceDeposu oyIlce) {
        this.secimler = secimler;
        this.iller = iller;
        this.ilceler = ilceler;
        this.partiler = partiler;
        this.sonucIl = sonucIl;
        this.oyIl = oyIl;
        this.sonucIlce = sonucIlce;
        this.oyIlce = oyIlce;
    }

    /**
     * @param tur    genel | yerel | referandum | cumhurbaskanligi | senato | ara (null: hepsi)
     * @param oylama milletvekili | baskanlik | belediye_meclisi | il_genel_meclisi | ... (null: hepsi)
     * @param yil    tek yıl; verilirse aralık parametreleri yok sayılır
     */
    public List<SecimDto> secimler(String tur, String oylama, Integer yil, Integer yilBaslangic, Integer yilBitis) {
        String turKodu = tur == null ? null : SecimTuru.fromKod(tur).kod();
        String oylamaKodu = oylama == null ? null : OylamaTuru.fromKod(oylama).kod();
        Integer bas = yil != null ? yil : yilBaslangic;
        Integer bit = yil != null ? yil : yilBitis;
        return secimler.ara(turKodu, oylamaKodu, bas, bit).stream().map(SecimServisi::dto).toList();
    }

    /** Bir ana seçime bağlı ikincil oylamalar ('2024yerel' -> belediye meclisi, il genel meclisi, yenileme). */
    public List<SecimDto> bagliOylamalar(String secimId) {
        secimBul(secimId);
        return secimler.findByAnaSecimIdOrderBySecimId(secimId).stream().map(SecimServisi::dto).toList();
    }

    public SecimDto secim(String secimId) {
        return dto(secimBul(secimId));
    }

    public List<IlSonucDto> iller(String secimId) {
        secimBul(secimId);
        PartiSozlugu p = PartiSozlugu.of(partiler.findAll());
        Map<Integer, List<OyIl>> oylar = oyIl.findBySecimId(secimId).stream()
                .collect(Collectors.groupingBy(OyIl::getPlaka));
        return sonucIl.findBySecimIdOrderByPlaka(secimId).stream()
                .map(s -> ilDto(s, oylar.getOrDefault(s.getPlaka(), List.of()), p))
                .toList();
    }

    public IlSonucDto il(String secimId, int plaka) {
        secimBul(secimId);
        SonucIl s = sonucIl.findById(new SonucIlId(secimId, plaka))
                .orElseThrow(() -> new KayitBulunamadiException(secimId + " seçiminde " + plaka + " plakalı il yok"));
        return ilDto(s, oyIl.findBySecimIdAndPlaka(secimId, plaka), PartiSozlugu.of(partiler.findAll()));
    }

    public List<IlceSonucDto> ilceler(String secimId, int plaka) {
        secimBul(secimId);
        PartiSozlugu p = PartiSozlugu.of(partiler.findAll());
        Map<String, List<OyIlce>> oylar = oyIlce.ildekiIlceler(secimId, plaka).stream()
                .collect(Collectors.groupingBy(OyIlce::getIlceId));
        return sonucIlce.findBySecimIdAndPlakaOrderByAd(secimId, plaka).stream()
                .map(s -> ilceDto(s, oylar.getOrDefault(s.getIlceId(), List.of()), p))
                .toList();
    }

    public IlceSonucDto ilce(String secimId, String ilceId) {
        secimBul(secimId);
        SonucIlce s = sonucIlce.findById(new SonucIlceId(secimId, ilceId))
                .orElseThrow(() -> new KayitBulunamadiException(secimId + " seçiminde " + ilceId + " ilçesi yok"));
        return ilceDto(s, oyIlce.findBySecimIdAndIlceId(secimId, ilceId), PartiSozlugu.of(partiler.findAll()));
    }

    public List<IlDto> butunIller() {
        return iller.findAllByOrderByPlaka().stream().map(i -> new IlDto(i.getPlaka(), i.getAd())).toList();
    }

    public List<IlceDto> ildekiIlceler(int plaka, Integer yil) {
        if (!iller.existsById(plaka)) {
            throw new KayitBulunamadiException(plaka + " plakalı il yok");
        }
        return ilceler.ildekiler(plaka, yil).stream().map(SecimServisi::ilceDto).toList();
    }

    /** Seçim yoksa 404 (KayitBulunamadiException). */
    public Secim secimBul(String secimId) {
        return secimler.findById(secimId)
                .orElseThrow(() -> new KayitBulunamadiException("Seçim bulunamadı: " + secimId));
    }

    static SecimDto dto(Secim s) {
        return new SecimDto(s.getSecimId(), SecimTuru.fromKod(s.getTur()), OylamaTuru.fromKod(s.getOylama()),
                s.getAnaSecimId(), s.getYil(), s.getTarihMetni(), s.getAciklama(), s.getToplamSandalye(),
                s.getBirincilKaynak(), s.getKaynakDurumu());
    }

    private static IlceDto ilceDto(Ilce i) {
        return new IlceDto(i.getIlceId(), i.getPlaka(), i.getAd(), Boolean.TRUE.equals(i.getGuncel()),
                i.getBaslangicYili(), i.getBitisYili());
    }

    private static IlSonucDto ilDto(SonucIl s, List<OyIl> oylar, PartiSozlugu p) {
        List<OyDto> o = oylar.stream()
                .map(v -> new OyDto(v.getPartiId(), p.ad(v.getPartiId()), p.kisa(v.getPartiId()),
                        v.getOy() == null ? null : v.getOy().longValue(), v.getOran()))
                .sorted(OY_SIRASI).toList();
        return new IlSonucDto(s.getSecimId(), s.getPlaka(), s.getAd(), s.getSecmen(), s.getOyKullanan(),
                s.getGecerliOy(), s.getGecersizOy(), s.getSandik(), s.getKatilim(), p.ad(s.getKazananPartiId()),
                s.getToplamVekil(), s.getNotMetni(), o);
    }

    private static IlceSonucDto ilceDto(SonucIlce s, List<OyIlce> oylar, PartiSozlugu p) {
        List<OyDto> o = oylar.stream()
                .map(v -> new OyDto(v.getPartiId(), p.ad(v.getPartiId()), p.kisa(v.getPartiId()),
                        v.getOy() == null ? null : v.getOy().longValue(), v.getOran()))
                .sorted(OY_SIRASI).toList();
        return new IlceSonucDto(s.getSecimId(), s.getIlceId(), s.getPlaka(), s.getAd(), s.getSecmen(),
                s.getOyKullanan(), s.getGecerliOy(), s.getGecersizOy(), s.getSandik(), s.getKatilim(),
                p.ad(s.getKazananPartiId()), s.getBaskan(), Boolean.TRUE.equals(s.getSadeceKazanan()),
                s.getNotMetni(), o);
    }
}
