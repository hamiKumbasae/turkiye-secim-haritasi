package tr.secimharitasi.loader.ek;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;
import tr.secimharitasi.loader.kaynak.OyKaydi;

/**
 * Mahalle (muhtarlık) sonuçları, 2009-2024: data/normalized/mahalle/&lt;secim&gt;.json
 * ({ilceId: {mahalleId: {secmen, oy: {parti: {oy, oran}}, ...}}}). Dosyalar büyük olduğu için seçim seçim
 * okunur; adlar geo/normalized/mahalle_geo.json'dan akış hâlinde (geometri belleğe alınmadan) okunur.
 */
public final class MahalleOkuyucu {

    private final Path dizin;
    private final Path geoDosyasi;
    private final ObjectMapper json = new ObjectMapper();

    /**
     * @param normalizeDizin data/normalized
     * @param geoDosyasi     geo/normalized/mahalle_geo.json (yoksa ya da null ise adlar boş kalır)
     */
    public MahalleOkuyucu(Path normalizeDizin, Path geoDosyasi) {
        this.dizin = normalizeDizin.resolve("mahalle");
        this.geoDosyasi = geoDosyasi;
    }

    /** Mahalle verisi olan seçimler, ada göre sıralı. */
    public List<String> secimler() {
        if (!Files.isDirectory(dizin)) {
            return List.of();
        }
        try (Stream<Path> s = Files.list(dizin)) {
            return s.map(p -> p.getFileName().toString())
                    .filter(n -> n.endsWith(".json"))
                    .map(n -> n.substring(0, n.length() - 5))
                    .sorted()
                    .toList();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public List<MahalleSatiri> oku(String secimId) {
        Path p = dizin.resolve(secimId + ".json");
        List<MahalleSatiri> satirlar = new ArrayList<>();
        try (JsonParser jp = json.getFactory().createParser(p.toFile())) {
            bekle(jp, JsonToken.START_OBJECT);
            while (jp.nextToken() == JsonToken.FIELD_NAME) {
                String ilceId = jp.currentName();
                jp.nextToken();
                JsonNode mahalleler = jp.readValueAsTree();
                mahalleler.fields().forEachRemaining(e -> satirlar.add(satir(ilceId, e.getKey(), e.getValue())));
            }
        } catch (IOException e) {
            throw new UncheckedIOException("Okunamadı: " + p, e);
        }
        return satirlar;
    }

    /** (ilceId|mahalleId) -> ad. Dosya yoksa boş. */
    public Map<String, String> adlar() {
        Map<String, String> adlar = new HashMap<>();
        if (geoDosyasi == null || !Files.isRegularFile(geoDosyasi)) {
            return adlar;
        }
        try (JsonParser jp = json.getFactory().createParser(geoDosyasi.toFile())) {
            bekle(jp, JsonToken.START_OBJECT);
            while (jp.nextToken() == JsonToken.FIELD_NAME) {
                String ilceId = jp.currentName();
                bekle(jp, JsonToken.START_OBJECT);
                while (jp.nextToken() == JsonToken.FIELD_NAME) {
                    String mahalleId = jp.currentName();
                    bekle(jp, JsonToken.START_OBJECT);
                    while (jp.nextToken() == JsonToken.FIELD_NAME) {
                        String alan = jp.currentName();
                        JsonToken t = jp.nextToken();
                        if ("ad".equals(alan) && t == JsonToken.VALUE_STRING) {
                            adlar.put(anahtar(ilceId, mahalleId), jp.getText());
                        } else {
                            jp.skipChildren();
                        }
                    }
                }
            }
        } catch (IOException e) {
            throw new UncheckedIOException("Okunamadı: " + geoDosyasi, e);
        }
        return adlar;
    }

    public static String anahtar(String ilceId, String mahalleId) {
        return ilceId + "|" + mahalleId;
    }

    private static MahalleSatiri satir(String ilceId, String mahalleId, JsonNode r) {
        Map<String, OyKaydi> oy = new LinkedHashMap<>();
        r.path("oy").fields().forEachRemaining(e -> {
            JsonNode v = e.getValue();
            oy.put(e.getKey(), new OyKaydi(v.hasNonNull("oy") ? v.get("oy").asLong() : null,
                    v.hasNonNull("oran") ? v.get("oran").decimalValue() : null, null));
        });
        return new MahalleSatiri(ilceId, mahalleId, tam(r, "secmen"), tam(r, "oyKullanan"), tam(r, "gecerliOy"),
                tam(r, "sandik"), r.hasNonNull("katilim") ? r.get("katilim").decimalValue() : null,
                r.hasNonNull("kazanan") ? r.get("kazanan").asText() : null, oy);
    }

    private static Integer tam(JsonNode r, String alan) {
        return r.hasNonNull(alan) && r.get(alan).isNumber() ? r.get(alan).asInt() : null;
    }

    private static void bekle(JsonParser jp, JsonToken beklenen) throws IOException {
        JsonToken t = jp.nextToken();
        if (t != beklenen) {
            throw new IOException("Beklenen " + beklenen + ", bulunan " + t + " (" + jp.currentLocation() + ")");
        }
    }
}
