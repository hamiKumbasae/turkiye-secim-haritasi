package tr.secimharitasi.api.servis;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tr.secimharitasi.api.depo.IlDeposu;
import tr.secimharitasi.api.depo.KaynakKapsamiDeposu;
import tr.secimharitasi.api.depo.MahalleDeposu;
import tr.secimharitasi.api.depo.OyBeldeDeposu;
import tr.secimharitasi.api.depo.OyMahalleDeposu;
import tr.secimharitasi.api.depo.PartiDeposu;
import tr.secimharitasi.api.depo.SandalyeIlDeposu;
import tr.secimharitasi.api.depo.SandalyeIlceDeposu;
import tr.secimharitasi.api.depo.SecilenDeposu;
import tr.secimharitasi.api.depo.SonucBeldeDeposu;
import tr.secimharitasi.api.depo.SonucMahalleDeposu;
import tr.secimharitasi.api.varlik.Il;
import tr.secimharitasi.api.varlik.Mahalle;
import tr.secimharitasi.api.varlik.OyBelde;
import tr.secimharitasi.api.varlik.OyMahalle;
import tr.secimharitasi.api.varlik.SonucBelde;
import tr.secimharitasi.api.varlik.SonucMahalle;
import tr.secimharitasi.common.dto.BeldeSonucDto;
import tr.secimharitasi.common.dto.KapsamDto;
import tr.secimharitasi.common.dto.MahalleSonucDto;
import tr.secimharitasi.common.dto.OyDto;
import tr.secimharitasi.common.dto.SandalyeDto;
import tr.secimharitasi.common.dto.SecilenDto;

/** Mahalle sonuçları, beldeler, seçilen kişiler, sandalyeler ve kaynak kapsamı. */
@Service
@Transactional(readOnly = true)
public class EkVeriServisi {

    private final SecimServisi secimServisi;
    private final PartiDeposu partiler;
    private final IlDeposu iller;
    private final MahalleDeposu mahalleler;
    private final SonucMahalleDeposu sonucMahalle;
    private final OyMahalleDeposu oyMahalle;
    private final SonucBeldeDeposu sonucBelde;
    private final OyBeldeDeposu oyBelde;
    private final SecilenDeposu secilenler;
    private final SandalyeIlDeposu sandalyeIl;
    private final SandalyeIlceDeposu sandalyeIlce;
    private final KaynakKapsamiDeposu kapsam;

    public EkVeriServisi(SecimServisi secimServisi, PartiDeposu partiler, IlDeposu iller, MahalleDeposu mahalleler,
                         SonucMahalleDeposu sonucMahalle, OyMahalleDeposu oyMahalle, SonucBeldeDeposu sonucBelde,
                         OyBeldeDeposu oyBelde, SecilenDeposu secilenler, SandalyeIlDeposu sandalyeIl,
                         SandalyeIlceDeposu sandalyeIlce, KaynakKapsamiDeposu kapsam) {
        this.secimServisi = secimServisi;
        this.partiler = partiler;
        this.iller = iller;
        this.mahalleler = mahalleler;
        this.sonucMahalle = sonucMahalle;
        this.oyMahalle = oyMahalle;
        this.sonucBelde = sonucBelde;
        this.oyBelde = oyBelde;
        this.secilenler = secilenler;
        this.sandalyeIl = sandalyeIl;
        this.sandalyeIlce = sandalyeIlce;
        this.kapsam = kapsam;
    }

    /** Bir ilçenin mahalleleri (2009-2024), seçmen sayısına göre büyükten küçüğe. */
    public List<MahalleSonucDto> mahalleler(String secimId, String ilceId) {
        secimServisi.secimBul(secimId);
        PartiSozlugu p = PartiSozlugu.of(partiler.findAll());
        List<SonucMahalle> sonuclar = sonucMahalle.findBySecimIdAndIlceId(secimId, ilceId);
        Set<String> idler = sonuclar.stream().map(SonucMahalle::getMahalleId).collect(Collectors.toSet());
        Map<String, String> adlar = idler.isEmpty() ? Map.of()
                : mahalleler.findByIlceIdAndMahalleIdIn(ilceId, idler).stream()
                        .filter(m -> m.getAd() != null)
                        .collect(Collectors.toMap(Mahalle::getMahalleId, Mahalle::getAd));
        Map<String, List<OyMahalle>> oylar = oyMahalle.findBySecimIdAndIlceId(secimId, ilceId).stream()
                .collect(Collectors.groupingBy(OyMahalle::getMahalleId));
        return sonuclar.stream()
                .map(s -> new MahalleSonucDto(s.getSecimId(), s.getIlceId(), s.getMahalleId(), adlar.get(s.getMahalleId()),
                        s.getSecmen(), s.getOyKullanan(), s.getGecerliOy(), s.getSandik(), s.getKatilim(),
                        p.ad(s.getKazananPartiId()),
                        oylar.getOrDefault(s.getMahalleId(), List.of()).stream()
                                .map(o -> new OyDto(o.getPartiId(), p.ad(o.getPartiId()), p.kisa(o.getPartiId()),
                                        o.getOy() == null ? null : o.getOy().longValue(), o.getOran()))
                                .sorted(SecimServisi.OY_SIRASI).toList()))
                .sorted(java.util.Comparator.comparing(MahalleSonucDto::secmen,
                        java.util.Comparator.nullsLast(java.util.Comparator.reverseOrder())))
                .toList();
    }

    public List<BeldeSonucDto> beldeler(String secimId, Integer plaka, String ilceId) {
        secimServisi.secimBul(secimId);
        PartiSozlugu p = PartiSozlugu.of(partiler.findAll());
        List<SonucBelde> beldeler = sonucBelde.ara(secimId, plaka, ilceId);
        Map<Integer, List<OyBelde>> oylar = beldeler.isEmpty() ? Map.of()
                : oyBelde.findBySonucBeldeIdIn(beldeler.stream().map(SonucBelde::getSonucBeldeId).toList()).stream()
                        .collect(Collectors.groupingBy(OyBelde::getSonucBeldeId));
        return beldeler.stream().map(b -> new BeldeSonucDto(b.getSecimId(), b.getPlaka(), b.getIlceId(), b.getIlceAd(),
                b.getBeldeAd(), b.getBeldeKod(), b.getSecmen(), b.getOyKullanan(), b.getGecerliOy(), b.getKatilim(),
                p.ad(b.getKazananPartiId()), b.getAday(), Boolean.TRUE.equals(b.getSadeceKazanan()), b.getKaynak(),
                b.getKontrol(), b.getNotMetni(),
                oylar.getOrDefault(b.getSonucBeldeId(), List.of()).stream()
                        .map(o -> new OyDto(o.getPartiId(), p.ad(o.getPartiId()), p.kisa(o.getPartiId()),
                                o.getOy() == null ? null : o.getOy().longValue(), null))
                        .sorted(SecimServisi.OY_SIRASI).toList())).toList();
    }

    public List<SecilenDto> secilenler(String secimId, Integer plaka) {
        secimServisi.secimBul(secimId);
        PartiSozlugu p = PartiSozlugu.of(partiler.findAll());
        Map<Integer, String> ilAdlari = iller.findAll().stream().collect(Collectors.toMap(Il::getPlaka, Il::getAd));
        return secilenler.ara(secimId, plaka).stream()
                .map(s -> new SecilenDto(s.getSecimId(), s.getGorev(), s.getPlaka(), ilAdlari.get(s.getPlaka()),
                        s.getAd(), s.getPartiId(), p.ad(s.getPartiId()), s.getPartiAdiKaynakta(), s.getBolge()))
                .toList();
    }

    /** ilceId verilirse ilçe meclisi (2024 belediye meclisi), yoksa il milletvekilleri; ikisi yoksa hepsi. */
    public List<SandalyeDto> sandalyeler(String secimId, Integer plaka, String ilceId) {
        secimServisi.secimBul(secimId);
        PartiSozlugu p = PartiSozlugu.of(partiler.findAll());
        List<SandalyeDto> il = ilceId != null ? List.of() : sandalyeIl.ara(secimId, plaka).stream()
                .map(s -> new SandalyeDto(s.getSecimId(), s.getPlaka(), null, s.getPartiId(), p.ad(s.getPartiId()),
                        s.getSandalye())).toList();
        List<SandalyeDto> ilce = sandalyeIlce.ara(secimId, plaka, ilceId).stream()
                .map(s -> new SandalyeDto(s.getSecimId(), null, s.getIlceId(), s.getPartiId(), p.ad(s.getPartiId()),
                        s.getSandalye())).toList();
        return java.util.stream.Stream.concat(il.stream(), ilce.stream()).toList();
    }

    public List<KapsamDto> kapsam(String secimId) {
        secimServisi.secimBul(secimId);
        return kapsam.findBySecimIdOrderByVeri(secimId).stream()
                .map(k -> new KapsamDto(k.getSecimId(), k.getVeri(), k.getBulunan(), k.getBeklenen(), k.getDurum(),
                        k.getAciklama())).toList();
    }
}
