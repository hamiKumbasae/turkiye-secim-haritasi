package tr.secimharitasi.loader.yukleme;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import tr.secimharitasi.loader.ek.EkVeriOkuyucu;
import tr.secimharitasi.loader.ek.MahalleOkuyucu;
import tr.secimharitasi.loader.kaynak.KaynakOkuyucu;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kontrol.Bulgu;
import tr.secimharitasi.loader.kontrol.BulguTuru;
import tr.secimharitasi.loader.kontrol.TutarlilikKontrolu;

/** Kaynağı okur, boyut tablolarını kurar, tutarlılık kontrolünü yapar. Veritabanına ve Spring'e bağlı değildir. */
public final class KaynakHazirlayici {

    private static final Logger log = LoggerFactory.getLogger(KaynakHazirlayici.class);
    private static final Logger tutarlilik = LoggerFactory.getLogger("tutarlilik");

    private KaynakHazirlayici() {
    }

    /** Okuma, boyut tabloları ve tutarlılık kontrolü: veritabanından bağımsız. */
    public record Hazirlik(List<KaynakSecim> secimler, BoyutTablolari boyut, EkVeriOkuyucu.Sonuc ek,
                           MahalleOkuyucu mahalle, Map<BulguTuru, Long> bulgular) {
    }

    public static Hazirlik hazirla(Path dizin, Path kaynaklar, Path mahalleGeo, double ilceToleransi,
                                   long partiToplamToleransi) {
        log.info("Kaynak okunuyor: {}", dizin.toAbsolutePath());
        KaynakOkuyucu okuyucu = new KaynakOkuyucu(dizin, kaynaklar);
        List<KaynakSecim> ana = okuyucu.oku();
        List<KaynakSecim> meclis = okuyucu.meclisler();
        List<KaynakSecim> onceki = new ArrayList<>(ana);
        onceki.addAll(meclis);
        EkVeriOkuyucu.Sonuc ek = new EkVeriOkuyucu(dizin).oku(onceki);
        // Sıra: ana seçimler, meclisler, ek (Senato, ara) — ana seçim kendisine bağlanandan önce yazılır.
        List<KaynakSecim> secimler = new ArrayList<>(onceki);
        secimler.addAll(ek.secimler());
        log.info("{} ana seçim, {} meclis oylaması, {} Senato/ara seçim; {} belde, {} seçilen; {} Senato ilçesi "
                        + "adından eşlenemedi", ana.size(), meclis.size(), ek.secimler().size(), ek.beldeler().size(),
                ek.secilenler().size(), ek.eslesmeyenSenatoIlcesi());

        List<KaynakSecim> kronolojik = secimler.stream()
                .sorted(Comparator.comparingInt(KaynakSecim::yil).thenComparing(KaynakSecim::secimId)).toList();
        BoyutTablolari boyut = BoyutTablolari.olustur(kronolojik);

        TutarlilikKontrolu kontrol = new TutarlilikKontrolu(ilceToleransi, partiToplamToleransi);
        Map<BulguTuru, Long> sayac = new EnumMap<>(BulguTuru.class);
        for (KaynakSecim s : secimler) {
            for (Bulgu b : kontrol.kontrolEt(s, boyut.iller().keySet())) {
                sayac.merge(b.tur(), 1L, Long::sum);
                if (b.satirAtlanir()) {
                    tutarlilik.error("{} — satır yüklenmedi", b);
                } else {
                    tutarlilik.warn("{}", b);
                }
            }
        }
        return new Hazirlik(secimler, boyut, ek, new MahalleOkuyucu(dizin, mahalleGeo), sayac);
    }
}
