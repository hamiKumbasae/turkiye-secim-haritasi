package tr.secimharitasi.loader.kontrol;

/**
 * @param yer     il adı, ilçe adı (kimliğiyle) ya da 'Yurt Dışı'
 * @param ayrinti karşılaştırılan değerler
 */
public record Bulgu(BulguTuru tur, String secimId, String yer, String ayrinti) {

    public boolean satirAtlanir() {
        return tur.seviye() == BulguTuru.Seviye.HATA;
    }

    @Override
    public String toString() {
        return "%s [%s] %s: %s".formatted(tur, secimId, yer, ayrinti);
    }
}
