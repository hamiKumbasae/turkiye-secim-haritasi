package tr.secimharitasi.loader.kaynak;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * elections/&lt;tur&gt;/&lt;secim&gt;.json içindeki bir il ya da ilçe satırı. Alan adları kaynaktakiyle aynıdır;
 * burada okunmayan alanlar (kaynak, duzeltmeKaynagi ...) yok sayılır.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record SonucSatiri(
        Integer plaka,
        String ad,
        String geomId,
        Integer secmen,
        Integer oyKullanan,
        Integer gecerliOy,
        Integer gecersizOy,
        Integer sandik,
        BigDecimal katilim,
        String kazanan,
        Integer toplamVekil,
        String baskan,
        Boolean sadeceKazanan,
        @JsonProperty("not") String notMetni,
        String veriNotu,
        String etiketNotu,
        Map<String, OyKaydi> oy,
        Map<String, Integer> vekil) {

    public SonucSatiri {
        oy = oy == null ? Map.of() : new LinkedHashMap<>(oy);
        vekil = vekil == null ? Map.of() : new LinkedHashMap<>(vekil);
    }

    /** Ek kayıtlardan elle kurulan satır (alan adları kaynak JSON'unkiyle aynı anlamda). */
    public static SonucSatiri yeni(Integer plaka, String ad, String geomId, Integer secmen, Integer oyKullanan,
                                   Integer gecerliOy, Integer gecersizOy, Integer sandik, BigDecimal katilim,
                                   String kazanan, boolean sadeceKazanan, String not, Map<String, OyKaydi> oy) {
        return new SonucSatiri(plaka, ad, geomId, secmen, oyKullanan, gecerliOy, gecersizOy, sandik, katilim, kazanan,
                null, null, sadeceKazanan, not, null, null, oy, null);
    }

    /** İlçe kimliği: geomId; kaynakta geomId yoksa plaka ve addan türetilen sabit bir anahtar. */
    public String ilceId() {
        return geomId != null ? geomId : "YOK-%02d-%s".formatted(plaka, ad);
    }

    public boolean yalnizKazananBiliniyor() {
        return Boolean.TRUE.equals(sadeceKazanan);
    }

    /** Kaynaktaki not alanlarının birleşimi (yoksa null). */
    public String notlar() {
        String s = Stream.of(notMetni, veriNotu, etiketNotu)
                .filter(n -> n != null && !n.isBlank())
                .collect(Collectors.joining(" | "));
        return s.isEmpty() ? null : s;
    }

    /**
     * Seçmen, geçerli oy ve kazanan yok: henüz kurulmamış bir ilçe için kaynakta tutulan boş satır
     * (ör. 2012'de kurulan ilçelerin 2009-2011 satırları). Yüklenir, ama ilçenin başlangıç yılına sayılmaz.
     */
    public boolean bosYerTutucu() {
        return (secmen == null || secmen == 0) && (gecerliOy == null || gecerliOy == 0) && kazanan == null;
    }
}
