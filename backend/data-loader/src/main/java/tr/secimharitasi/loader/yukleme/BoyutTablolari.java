package tr.secimharitasi.loader.yukleme;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.SonucSatiri;

/**
 * Seçimlerden il ve ilçe boyut tablolarını çıkarır.
 * <ul>
 *   <li>İl/ilçe adı ve ilçenin plakası: kronolojik olarak son görülen değer.</li>
 *   <li>baslangic_yili: ilçenin dolu bir satırla (seçmen, oy ya da kazanan var) göründüğü ilk seçim yılı.
 *       Boş yer tutucu satırlar sayılmaz; birimin hiç dolu satırı yoksa bütün satırlar sayılır.</li>
 *   <li>bitis_yili: güncel ilçe birimlerinde (TR-D-...) null; tarihsel birimlerde dolu göründüğü son yıl.</li>
 * </ul>
 */
public final class BoyutTablolari {

    public static final String YURT_DISI = "Yurt Dışı";

    public record Ilce(String ilceId, int plaka, String ad, boolean guncel, int baslangicYili, Integer bitisYili) {
    }

    private final Map<Integer, String> iller;
    private final Map<String, Ilce> ilceler;

    private BoyutTablolari(Map<Integer, String> iller, Map<String, Ilce> ilceler) {
        this.iller = iller;
        this.ilceler = ilceler;
    }

    /** @param secimler kronolojik sırada (KaynakOkuyucu.oku()) */
    public static BoyutTablolari olustur(List<KaynakSecim> secimler) {
        Map<Integer, String> iller = new TreeMap<>();
        Map<String, int[]> yillar = new HashMap<>();       // ilceId -> {ilk, son, ilkDolu, sonDolu}
        Map<String, SonucSatiri> son = new LinkedHashMap<>();
        boolean yurtDisi = false;

        for (KaynakSecim s : secimler) {
            for (SonucSatiri il : s.dosya().iller()) {
                iller.put(il.plaka(), il.ad());
            }
            yurtDisi |= s.dosya().yurtdisi() != null;
            for (SonucSatiri r : s.dosya().ilceler()) {
                String id = r.ilceId();
                son.put(id, r);
                int[] y = yillar.computeIfAbsent(id, k -> new int[]{Integer.MAX_VALUE, 0, Integer.MAX_VALUE, 0});
                y[0] = Math.min(y[0], s.yil());
                y[1] = Math.max(y[1], s.yil());
                if (!r.bosYerTutucu()) {
                    y[2] = Math.min(y[2], s.yil());
                    y[3] = Math.max(y[3], s.yil());
                }
            }
        }
        if (yurtDisi) {
            iller.put(0, YURT_DISI);
        }

        Map<String, Ilce> ilceler = new TreeMap<>();
        son.forEach((id, r) -> {
            if (!iller.containsKey(r.plaka())) {
                return;   // ili olmayan ilçe yüklenemez (ILCENIN_ILI_YOK bulgusu)
            }
            int[] y = yillar.get(id);
            boolean doluVar = y[3] != 0;
            int bas = doluVar ? y[2] : y[0];
            int bit = doluVar ? y[3] : y[1];
            boolean guncel = id.startsWith("TR-D-");
            ilceler.put(id, new Ilce(id, r.plaka(), r.ad(), guncel, bas, guncel ? null : bit));
        });
        return new BoyutTablolari(iller, ilceler);
    }

    public Map<Integer, String> iller() {
        return iller;
    }

    public Map<String, Ilce> ilceler() {
        return ilceler;
    }
}
