package tr.secimharitasi.chatbot.arac;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Haritadaki paylaşılabilir bağlantı (site/src/js/link.js ile aynı biçim):
 * #secim=1977&amp;oylama=bm&amp;il=6&amp;ilce=TR-D-06-001&amp;mod=parti&amp;parti=CHP.
 * Haritada yalnız ana seçimler ve yerel seçimin meclis oylamaları var (Senato ve ara seçimler yok).
 */
public final class HaritaBaglantisi {

    private static final Pattern HARITADA =
            Pattern.compile("^(\\d{4}(?:yerel|referandum|cb\\w*|Haziran|Kasim)?)(?:_(bm|igm))?$");
    private static final Set<String> MODLAR = Set.of("katilim", "parti", "degisim");

    private HaritaBaglantisi() {
    }

    /** @return bağlantı; seçim haritada yoksa null */
    public static String olustur(String kok, String secimId, Integer plaka, String ilceId, String parti, String mod) {
        Matcher m = HARITADA.matcher(secimId == null ? "" : secimId);
        if (!m.matches()) {
            return null;
        }
        Map<String, String> q = new LinkedHashMap<>();
        q.put("secim", m.group(1));
        if (m.group(2) != null) {
            q.put("oylama", m.group(2));
        }
        if (plaka != null && plaka > 0) {
            q.put("il", plaka.toString());
            if (ilceId != null && !ilceId.isBlank()) {
                q.put("ilce", ilceId);
            }
        }
        if (mod != null && MODLAR.contains(mod)) {
            q.put("mod", mod);
            if (!"katilim".equals(mod) && parti != null && !parti.isBlank()) {
                q.put("parti", parti);
            }
        }
        String hash = q.entrySet().stream()
                .map(e -> e.getKey() + "=" + URLEncoder.encode(e.getValue(), StandardCharsets.UTF_8))
                .collect(Collectors.joining("&"));
        return (kok.endsWith("/") ? kok : kok + "/") + "#" + hash;
    }
}
