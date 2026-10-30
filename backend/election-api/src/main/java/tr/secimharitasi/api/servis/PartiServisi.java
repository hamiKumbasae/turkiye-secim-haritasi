package tr.secimharitasi.api.servis;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tr.secimharitasi.api.depo.GecerliOyToplami;
import tr.secimharitasi.api.depo.OyIlDeposu;
import tr.secimharitasi.api.depo.PartiDeposu;
import tr.secimharitasi.api.depo.PartiOySatiri;
import tr.secimharitasi.api.depo.PartiToplami;
import tr.secimharitasi.api.depo.SecimDeposu;
import tr.secimharitasi.api.depo.SonucIlDeposu;
import tr.secimharitasi.api.varlik.Parti;
import tr.secimharitasi.common.GecisTuru;
import tr.secimharitasi.common.SecenekTipi;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.common.dto.PartiDto;
import tr.secimharitasi.common.dto.PartiSonucDto;

@Service
@Transactional(readOnly = true)
public class PartiServisi {

    private static final BigDecimal YUZ = BigDecimal.valueOf(100);

    private final PartiDeposu partiler;
    private final OyIlDeposu oyIl;
    private final SonucIlDeposu sonucIl;
    private final SecimDeposu secimler;

    public PartiServisi(PartiDeposu partiler, OyIlDeposu oyIl, SonucIlDeposu sonucIl, SecimDeposu secimler) {
        this.partiler = partiler;
        this.oyIl = oyIl;
        this.sonucIl = sonucIl;
        this.secimler = secimler;
    }

    public List<PartiDto> partiler(String tip) {
        List<Parti> liste = tip == null ? partiler.findAllByOrderByPartiId()
                : partiler.findByTipOrderByPartiId(SecenekTipi.fromKod(tip).kod());
        return liste.stream().map(p -> dto(p, null)).toList();
    }

    /** Parti ve onceki_parti_id zinciri (en yakın öncülden en eskiye). */
    public PartiDto parti(int partiId) {
        PartiSozlugu s = PartiSozlugu.of(partiler.findAll());
        Parti p = bul(s, partiId);
        return dto(p, oncekiler(s, p).stream().map(o -> dto(o, null)).toList());
    }

    /**
     * Partinin seçimlere göre sonuçları.
     *
     * @param plaka  verilirse o ilin sonucu; verilmezse Türkiye geneli (il satırlarının toplamı, yurt dışı hariç;
     *               oran = parti oyu / il geçerli oylarının toplamı)
     * @param zincir true ise onceki_parti_id zincirindeki partilerin sonuçları da (kendi adlarıyla) eklenir
     */
    public List<PartiSonucDto> sonuclar(int partiId, String tur, Integer yilBaslangic, Integer yilBitis,
                                        Integer plaka, boolean zincir) {
        PartiSozlugu s = PartiSozlugu.of(partiler.findAll());
        Parti p = bul(s, partiId);
        Set<Integer> kimlikler = new LinkedHashSet<>();
        kimlikler.add(p.getPartiId());
        if (zincir) {
            oncekiler(s, p).forEach(o -> kimlikler.add(o.getPartiId()));
        }
        String turKodu = tur == null ? null : SecimTuru.fromKod(tur).kod();

        if (plaka != null) {
            return oyIl.ildekiSonuclar(kimlikler, plaka, turKodu, yilBaslangic, yilBitis).stream()
                    .map(r -> new PartiSonucDto(r.secimId(), SecimTuru.fromKod(r.tur()), r.yil(), r.partiId(),
                            s.ad(r.partiId()), r.plaka(), r.yer(), r.oy(), r.gecerliOy(), r.oran()))
                    .toList();
        }

        List<PartiToplami> toplamlar = oyIl.turkiyeToplamlari(kimlikler, turKodu, yilBaslangic, yilBitis);
        List<String> secimIdleri = toplamlar.stream().map(PartiToplami::secimId).distinct().toList();
        Map<String, Long> gecerli = secimIdleri.isEmpty() ? Map.of()
                : sonucIl.yurtIciGecerliOy(secimIdleri).stream()
                        .filter(g -> g.gecerliOy() != null)
                        .collect(Collectors.toMap(GecerliOyToplami::secimId, GecerliOyToplami::gecerliOy));
        List<PartiSonucDto> sonuc = new ArrayList<>();
        for (PartiToplami t : toplamlar) {
            Long g = gecerli.get(t.secimId());
            BigDecimal oran = t.oy() == null || g == null || g == 0 ? null
                    : BigDecimal.valueOf(t.oy()).multiply(YUZ).divide(BigDecimal.valueOf(g), 2, RoundingMode.HALF_UP);
            sonuc.add(new PartiSonucDto(t.secimId(), SecimTuru.fromKod(t.tur()), t.yil(), t.partiId(),
                    s.ad(t.partiId()), null, "Türkiye (yurt içi)", t.oy(), g, oran));
        }
        return sonuc;
    }

    /** Bir seçimde partinin en yüksek oy oranı aldığı iller. */
    public List<PartiSonucDto> enGucluIller(int partiId, String secimId, int limit) {
        PartiSozlugu s = PartiSozlugu.of(partiler.findAll());
        bul(s, partiId);
        if (!secimler.existsById(secimId)) {
            throw new KayitBulunamadiException("Seçim bulunamadı: " + secimId);
        }
        int boyut = Math.max(1, Math.min(limit, 81));
        List<PartiOySatiri> satirlar = oyIl.enGucluIller(secimId, partiId, PageRequest.of(0, boyut));
        return satirlar.stream()
                .map(r -> new PartiSonucDto(r.secimId(), SecimTuru.fromKod(r.tur()), r.yil(), r.partiId(),
                        s.ad(r.partiId()), r.plaka(), r.yer(), r.oy(), r.gecerliOy(), r.oran()))
                .toList();
    }

    private static Parti bul(PartiSozlugu s, int partiId) {
        Parti p = s.partiler().get(partiId);
        if (p == null) {
            throw new KayitBulunamadiException("Parti bulunamadı: " + partiId);
        }
        return p;
    }

    static List<Parti> oncekiler(PartiSozlugu s, Parti p) {
        List<Parti> zincir = new ArrayList<>();
        Set<Integer> gorulen = new HashSet<>();
        gorulen.add(p.getPartiId());
        Integer sonraki = p.getOncekiPartiId();
        while (sonraki != null && gorulen.add(sonraki)) {   // döngüye karşı koruma
            Parti o = s.partiler().get(sonraki);
            if (o == null) {
                break;
            }
            zincir.add(o);
            sonraki = o.getOncekiPartiId();
        }
        return zincir;
    }

    static PartiDto dto(Parti p, List<PartiDto> oncekiler) {
        return new PartiDto(p.getPartiId(), p.getAd(), p.getKisa(), SecenekTipi.fromKod(p.getTip()), p.getRenk(),
                p.getOncekiPartiId(), GecisTuru.fromKod(p.getGecisTuru()), p.getGecisYili(), p.getGecisKaynagi(),
                oncekiler);
    }
}
