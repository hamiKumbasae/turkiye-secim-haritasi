package tr.secimharitasi.loader.kaynak;

import tr.secimharitasi.common.OylamaTuru;
import tr.secimharitasi.common.SecimTuru;

/**
 * Okunmuş bir oylama: ana seçimler (elections/) ile meclis, Senato ve ara seçim kayıtları aynı biçimde tutulur.
 *
 * @param secimId    dosya adı ('2023', '2024yerel', '2024yerel_bm', '1961senato', '2019istanbul_bb_yenileme')
 * @param anaSecimId ikincil oylamanın bağlı olduğu ana seçim (yoksa null)
 */
public record KaynakSecim(String secimId, int yil, SecimTuru tur, OylamaTuru oylama, String anaSecimId,
                          String aciklama, SecimDosyasi dosya, String birincilKaynak, String kaynakDurumu) {

    /** Ana seçim (elections/): oylama türden çıkar, bağlı olduğu başka seçim yok. */
    public KaynakSecim(String secimId, int yil, SecimTuru tur, SecimDosyasi dosya, String birincilKaynak,
                       String kaynakDurumu) {
        this(secimId, yil, tur, OylamaTuru.anaOylama(tur), null, null, dosya, birincilKaynak, kaynakDurumu);
    }
}
