package tr.secimharitasi.loader.kontrol;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.OyKaydi;
import tr.secimharitasi.loader.kaynak.SonucSatiri;
import tr.secimharitasi.loader.kaynak.YurtDisi;

/**
 * Kaynak veride tutarlılık kontrolleri. Yalnız BULGU üretir; veriyi değiştirmez.
 * Kurallar:
 * <ul>
 *   <li>Seçeneklerin oy toplamı = geçerli oy (il, ilçe, yurt dışı). Oyu boş seçeneği olan ya da yalnız kazananı
 *       bilinen satırlar karşılaştırılamaz, atlanır.</li>
 *   <li>İlçe geçerli oy toplamı ≈ il geçerli oyu (genel, referandum, cumhurbaşkanlığı). Yerel seçimde il satırı
 *       il/büyükşehir belediye başkanlığıdır, ilçe satırları ilçe belediyeleridir; Senato ve ara seçimlerde ilçe
 *       kırılımı eksiktir: karşılaştırılmaz.</li>
 *   <li>Katılım ≤ %100; kazanan oy listesinde.</li>
 *   <li>Anahtar kontrolleri (HATA): ilçenin plakası il satırlarında var; aynı il/ilçe bir seçimde bir kez.</li>
 * </ul>
 */
public class TutarlilikKontrolu {

    private static final BigDecimal YUZ = BigDecimal.valueOf(100);

    /**
     * İlçe toplamı ≈ il toplamı yalnız bu türlerde anlamlı: yerel seçimde il satırı başka bir yarışmadır
     * (il/büyükşehir belediyesi), Senato ve ara seçimlerde ilçe kırılımı yalnız bazı illerde vardır.
     */
    private static final java.util.Set<SecimTuru> ILCE_TOPLAMI_KARSILASTIRILIR =
            java.util.EnumSet.of(SecimTuru.GENEL, SecimTuru.REFERANDUM, SecimTuru.CUMHURBASKANLIGI);

    private final double ilceToleransi;
    private final long partiToplamToleransi;

    /**
     * @param ilceToleransi         ilçe toplamı ile il toplamı arasındaki izinli göreli fark (0.005 = %0,5)
     * @param partiToplamToleransi  oy toplamı ile geçerli oy arasındaki izinli mutlak fark (oy)
     */
    public TutarlilikKontrolu(double ilceToleransi, long partiToplamToleransi) {
        this.ilceToleransi = ilceToleransi;
        this.partiToplamToleransi = partiToplamToleransi;
    }

    /**
     * @param bilinenIller bütün seçimlerin il satırlarındaki plakalar (il boyut tablosu)
     */
    public List<Bulgu> kontrolEt(KaynakSecim s, Set<Integer> bilinenIller) {
        List<Bulgu> b = new ArrayList<>();
        String id = s.secimId();

        Set<Integer> gorulenIller = new HashSet<>();
        for (SonucSatiri il : s.dosya().iller()) {
            if (!gorulenIller.add(il.plaka())) {
                b.add(new Bulgu(BulguTuru.YINELENEN_SATIR, id, il.ad(), "plaka " + il.plaka()));
                continue;
            }
            satirKontrolu(b, id, il.ad(), il);
        }

        Set<String> gorulenIlceler = new HashSet<>();
        Map<Integer, List<Integer>> ilceGecerli = new HashMap<>();
        for (SonucSatiri ilce : s.dosya().ilceler()) {
            String yer = ilce.ad() + " (" + ilce.ilceId() + ")";
            if (!gorulenIlceler.add(ilce.ilceId())) {
                b.add(new Bulgu(BulguTuru.YINELENEN_SATIR, id, yer, "ilçe " + ilce.ilceId()));
                continue;
            }
            if (!bilinenIller.contains(ilce.plaka())) {
                b.add(new Bulgu(BulguTuru.ILCENIN_ILI_YOK, id, yer, "plaka " + ilce.plaka()));
                continue;
            }
            satirKontrolu(b, id, yer, ilce);
            ilceGecerli.computeIfAbsent(ilce.plaka(), k -> new ArrayList<>()).add(ilce.gecerliOy());
        }

        YurtDisi yd = s.dosya().yurtdisi();
        if (yd != null) {
            partiToplami(b, id, "Yurt Dışı", yd.gecerliOy(), yd.oy(), false);
        }

        if (ILCE_TOPLAMI_KARSILASTIRILIR.contains(s.tur())) {
            ilceToplamlari(b, s, ilceGecerli);
        }
        return b;
    }

    private void satirKontrolu(List<Bulgu> b, String id, String yer, SonucSatiri r) {
        partiToplami(b, id, yer, r.gecerliOy(), r.oy(), r.yalnizKazananBiliniyor());
        if (r.katilim() != null && r.katilim().compareTo(YUZ) > 0) {
            b.add(new Bulgu(BulguTuru.KATILIM_100_USTU, id, yer, "katılım %" + r.katilim().toPlainString()));
        }
        if (r.kazanan() != null && !r.oy().isEmpty() && !r.oy().containsKey(r.kazanan())) {
            b.add(new Bulgu(BulguTuru.KAZANAN_OYLARDA_YOK, id, yer, "kazanan '" + r.kazanan() + "'"));
        }
    }

    private void partiToplami(List<Bulgu> b, String id, String yer, Integer gecerli, Map<String, OyKaydi> oy,
                              boolean yalnizKazanan) {
        if (gecerli == null || oy.isEmpty() || yalnizKazanan) {
            return;
        }
        if (oy.values().stream().map(OyKaydi::oy).anyMatch(Objects::isNull)) {
            return;
        }
        long toplam = oy.values().stream().mapToLong(OyKaydi::oy).sum();
        if (Math.abs(toplam - gecerli) > partiToplamToleransi) {
            b.add(new Bulgu(BulguTuru.PARTI_TOPLAMI_GECERLI_OY_DEGIL, id, yer,
                    "seçenek toplamı %d, geçerli oy %d, fark %+d".formatted(toplam, gecerli, toplam - gecerli)));
        }
    }

    private void ilceToplamlari(List<Bulgu> b, KaynakSecim s, Map<Integer, List<Integer>> ilceGecerli) {
        for (SonucSatiri il : s.dosya().iller()) {
            List<Integer> ilceler = ilceGecerli.get(il.plaka());
            Integer g = il.gecerliOy();
            if (ilceler == null || g == null || g == 0 || ilceler.stream().anyMatch(Objects::isNull)) {
                continue;
            }
            long toplam = ilceler.stream().mapToLong(Integer::longValue).sum();
            double fark = (double) (toplam - g) / g;
            if (Math.abs(fark) > ilceToleransi) {
                b.add(new Bulgu(BulguTuru.ILCE_TOPLAMI_IL_TOPLAMINDAN_FARKLI, s.secimId(), il.ad(),
                        "il geçerli oy %d, %d ilçenin toplamı %d, fark %%%.2f"
                                .formatted(g, ilceler.size(), toplam, fark * 100)));
            }
        }
    }
}
