package tr.secimharitasi.loader.ek;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.SonucSatiri;

/**
 * Adı verilen bir ilçeyi (beldelerin ve Senato ilçe birincilerinin ilçesi) ilçe birimine eşler: aynı ilde aynı
 * adla (büyük/küçük harf, boşluk ve noktalama yok sayılarak) görülen birimlerden, istenen yıla en yakın seçimde
 * görüleni seçer; eşitlikte daha yeni olanı. "İl Merkez" / il adı -> "Merkez", "Adana Seyhan" -> "Seyhan".
 * scripts/veritabani/build_db.py'deki ilce_bul ile aynı kural.
 */
public final class IlceIndeksi {

    private record Gorulme(int yil, String ilceId) {
    }

    private final Map<Integer, String> iller = new HashMap<>();
    private final Map<String, List<Gorulme>> adlar = new HashMap<>();

    public void ekle(KaynakSecim s) {
        for (SonucSatiri il : s.dosya().iller()) {
            if (il.plaka() != null && il.plaka() > 0 && il.ad() != null) {
                iller.put(il.plaka(), il.ad());
            }
        }
        for (SonucSatiri r : s.dosya().ilceler()) {
            adlar.computeIfAbsent(anahtar(r.plaka(), r.ad()), k -> new ArrayList<>())
                    .add(new Gorulme(s.yil(), r.ilceId()));
        }
    }

    public String bul(int plaka, String ad, int yil) {
        if (ad == null || ad.isBlank()) {
            return null;
        }
        String il = iller.getOrDefault(plaka, "");
        List<Gorulme> adaylar = new ArrayList<>();
        List<String> denenecek = new ArrayList<>(List.of(ad, ad.replaceFirst("^" + Pattern.quote(il) + "\\s+", "")));
        if (katla(ad).equals(katla(il)) || katla(ad).equals(katla(il + " merkez"))) {
            denenecek.add("Merkez");
        }
        for (String a : denenecek) {
            adaylar.addAll(adlar.getOrDefault(anahtar(plaka, a), List.of()));
        }
        return adaylar.stream()
                .min(Comparator.comparingInt((Gorulme g) -> Math.abs(g.yil() - yil)).thenComparing(g -> -g.yil()))
                .map(Gorulme::ilceId)
                .orElse(null);
    }

    private static String anahtar(Integer plaka, String ad) {
        return plaka + "|" + katla(ad == null ? "" : ad);
    }

    /** Türkçe büyük/küçük harf ve boşluk/tire/nokta farkını yok sayan anahtar. */
    public static String katla(String s) {
        return s.replace("İ", "i").replace("I", "ı").toLowerCase(Locale.ROOT).replaceAll("[\\s\\-.]+", "");
    }
}
