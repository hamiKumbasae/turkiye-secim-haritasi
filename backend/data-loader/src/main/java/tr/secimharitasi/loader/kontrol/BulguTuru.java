package tr.secimharitasi.loader.kontrol;

/** Tutarlılık bulgusu türleri. HATA olanlarda satır yüklenemez (yabancı anahtar ihlali), atlanır. */
public enum BulguTuru {
    PARTI_TOPLAMI_GECERLI_OY_DEGIL(Seviye.UYARI, "Seçeneklerin oy toplamı geçerli oya eşit değil"),
    ILCE_TOPLAMI_IL_TOPLAMINDAN_FARKLI(Seviye.UYARI, "İlçelerin geçerli oy toplamı il toplamından tolerans dışında farklı"),
    KATILIM_100_USTU(Seviye.UYARI, "Katılım oranı %100'ün üstünde"),
    KAZANAN_OYLARDA_YOK(Seviye.UYARI, "Kazanan, satırın oy listesinde yok"),
    ILCENIN_ILI_YOK(Seviye.HATA, "İlçenin plakası hiçbir il satırında yok (yabancı anahtar)"),
    YINELENEN_SATIR(Seviye.HATA, "Aynı seçimde aynı il/ilçe birden çok kez geçiyor (birincil anahtar)");

    public enum Seviye { UYARI, HATA }

    private final Seviye seviye;
    private final String aciklama;

    BulguTuru(Seviye seviye, String aciklama) {
        this.seviye = seviye;
        this.aciklama = aciklama;
    }

    public Seviye seviye() {
        return seviye;
    }

    public String aciklama() {
        return aciklama;
    }
}
