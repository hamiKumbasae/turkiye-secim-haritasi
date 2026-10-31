package tr.secimharitasi.loader.yukleme;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;

/**
 * Yüklenen bütün kaynak dosyaların (data/normalized, sources.yml, mahalle_geo.json) ve yükleyici sürümünün
 * SHA-256 özeti. Son başarılı yüklemeninkiyle aynıysa veri değişmemiştir.
 */
public final class KaynakOzeti {

    /** Yükleme mantığı veriyi farklı yazacak biçimde değişince artırılır (aynı kaynak yeniden yüklenir). */
    public static final String YUKLEYICI_SURUMU = "2";

    private KaynakOzeti() {
    }

    public static String hesapla(Path dizin, Path kaynaklar, Path mahalleGeo) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            md.update(("yukleyici:" + YUKLEYICI_SURUMU).getBytes(StandardCharsets.UTF_8));
            List<Path> dosyalar = new ArrayList<>();
            if (Files.isDirectory(dizin)) {
                try (Stream<Path> s = Files.walk(dizin)) {
                    s.filter(Files::isRegularFile).sorted().forEach(dosyalar::add);
                }
            }
            for (Path p : new Path[]{kaynaklar, mahalleGeo}) {
                if (p != null && Files.isRegularFile(p)) {
                    dosyalar.add(p);
                }
            }
            byte[] tampon = new byte[1 << 16];
            for (Path p : dosyalar) {
                String ad = Files.isDirectory(dizin) && p.startsWith(dizin) ? dizin.relativize(p).toString()
                        : p.getFileName().toString();
                md.update(ad.replace('\\', '/').getBytes(StandardCharsets.UTF_8));
                try (InputStream in = new DigestInputStream(Files.newInputStream(p), md)) {
                    while (in.read(tampon) != -1) {
                        // DigestInputStream okurken özete ekler
                    }
                }
            }
            return HexFormat.of().formatHex(md.digest());
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
