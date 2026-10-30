package tr.secimharitasi.loader.kaynak;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLMapper;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import tr.secimharitasi.common.OylamaTuru;
import tr.secimharitasi.common.SecimTuru;

/**
 * data/normalized/elections/&lt;tur&gt;/*.json dosyalarını ve sources.yml'i okur. Dosyalara yazmaz.
 * Seçimler yıl, sonra anahtar sırasıyla döner (kronolojik; il/ilçe adlarının "son görülen" değeri buna dayanır).
 */
public class KaynakOkuyucu {

    private static final Pattern YIL = Pattern.compile("^(\\d{4})");

    private final Path normalizeDizin;
    private final Path kaynaklarDosyasi;
    private final ObjectMapper json = new ObjectMapper()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

    /**
     * @param normalizeDizin   data/normalized
     * @param kaynaklarDosyasi sources.yml (yoksa ya da null ise kaynak alanları boş kalır)
     */
    public Path normalizeDizin() {
        return normalizeDizin;
    }

    public KaynakOkuyucu(Path normalizeDizin, Path kaynaklarDosyasi) {
        this.normalizeDizin = normalizeDizin;
        this.kaynaklarDosyasi = kaynaklarDosyasi;
    }

    public List<KaynakSecim> oku() {
        Path dizin = normalizeDizin.resolve("elections");
        if (!Files.isDirectory(dizin)) {
            throw new IllegalStateException("Seçim klasörü bulunamadı: " + dizin.toAbsolutePath());
        }
        JsonNode kaynaklar = kaynaklariOku();
        try (Stream<Path> dosyalar = Files.walk(dizin, 2)) {
            return dosyalar
                    .filter(p -> p.getFileName().toString().endsWith(".json"))
                    .map(p -> secimOku(p, kaynaklar))
                    .sorted(Comparator.comparingInt(KaynakSecim::yil).thenComparing(KaynakSecim::secimId))
                    .toList();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private KaynakSecim secimOku(Path dosya, JsonNode kaynaklar) {
        String secimId = dosya.getFileName().toString().replaceFirst("\\.json$", "");
        Matcher m = YIL.matcher(secimId);
        if (!m.find()) {
            throw new IllegalStateException("Seçim anahtarı yılla başlamıyor: " + dosya);
        }
        SecimDosyasi d;
        try {
            d = json.readValue(dosya.toFile(), SecimDosyasi.class);
        } catch (IOException e) {
            throw new UncheckedIOException("Okunamadı: " + dosya, e);
        }
        SecimTuru tur = d.tur() != null ? SecimTuru.fromKod(d.tur()) : SecimTuru.fromSecimId(secimId);
        JsonNode birincil = kaynaklar.path("elections").path(secimId).path("primary");
        return new KaynakSecim(secimId, Integer.parseInt(m.group(1)), tur, d,
                metin(birincil.path("authority")), metin(birincil.path("status")));
    }

    /**
     * meclis_harita/&lt;secim&gt;_bm.json ve _igm.json: belediye meclisi ve il genel meclisi. Ana seçimle aynı
     * biçim; her biri ayrı bir oylama, ana seçime bağlı ('2024yerel_bm' -> '2024yerel').
     */
    public List<KaynakSecim> meclisler() {
        Path dizin = normalizeDizin.resolve("meclis_harita");
        if (!Files.isDirectory(dizin)) {
            return List.of();
        }
        try (Stream<Path> dosyalar = Files.list(dizin)) {
            return dosyalar
                    .filter(p -> p.getFileName().toString().endsWith(".json"))
                    .sorted()
                    .map(this::meclisOku)
                    .toList();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private KaynakSecim meclisOku(Path dosya) {
        String secimId = dosya.getFileName().toString().replaceFirst("\\.json$", "");
        int ayrac = secimId.lastIndexOf('_');
        String ana = secimId.substring(0, ayrac);
        OylamaTuru oylama = switch (secimId.substring(ayrac + 1)) {
            case "bm" -> OylamaTuru.BELEDIYE_MECLISI;
            case "igm" -> OylamaTuru.IL_GENEL_MECLISI;
            default -> throw new IllegalStateException("Bilinmeyen meclis dosyası: " + dosya);
        };
        SecimDosyasi d;
        try {
            d = json.readValue(dosya.toFile(), SecimDosyasi.class);
        } catch (IOException e) {
            throw new UncheckedIOException("Okunamadı: " + dosya, e);
        }
        Matcher m = YIL.matcher(secimId);
        m.find();
        String aciklama = d.aciklama() != null ? d.aciklama() : d.oylamaAdi();
        return new KaynakSecim(secimId, Integer.parseInt(m.group(1)), SecimTuru.YEREL, oylama, ana, aciklama, d,
                null, null);
    }

    private JsonNode kaynaklariOku() {
        if (kaynaklarDosyasi == null || !Files.isRegularFile(kaynaklarDosyasi)) {
            return json.createObjectNode();
        }
        try {
            return new YAMLMapper().readTree(kaynaklarDosyasi.toFile());
        } catch (IOException e) {
            throw new UncheckedIOException("Okunamadı: " + kaynaklarDosyasi, e);
        }
    }

    private static String metin(JsonNode n) {
        return n.isMissingNode() || n.isNull() ? null : n.asText();
    }
}
