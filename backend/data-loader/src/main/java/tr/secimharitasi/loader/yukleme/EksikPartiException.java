package tr.secimharitasi.loader.yukleme;

import java.util.Set;

/** Veride parti tohumunda (Flyway V2+) olmayan bir seçenek adı var: sabit kimlik verilemez, yükleme durur. */
public class EksikPartiException extends RuntimeException {

    private final Set<String> adlar;

    public EksikPartiException(Set<String> adlar) {
        super("Parti tablosunda olmayan seçenek adları: " + adlar
                + ". Sabit parti_id vermek için yeni bir migration üretin: "
                + "python3 backend/tools/parti_tohumu.py --eksikler > "
                + "backend/data-loader/src/main/resources/db/migration/V<sıradaki>__yeni_partiler.sql");
        this.adlar = Set.copyOf(adlar);
    }

    public Set<String> adlar() {
        return adlar;
    }
}
