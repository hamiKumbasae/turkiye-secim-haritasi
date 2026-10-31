package tr.secimharitasi.loader.ek;

/** Kaynakta ne kadar kayıt bulunduğu/beklendiği (ek dosyalardaki kapsam/ozet alanları). */
public record KapsamKaydi(String secimId, String veri, Integer bulunan, Integer beklenen, String durum,
                          String aciklama) {
}
