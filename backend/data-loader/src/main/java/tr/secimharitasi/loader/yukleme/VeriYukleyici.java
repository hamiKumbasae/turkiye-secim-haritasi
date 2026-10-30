package tr.secimharitasi.loader.yukleme;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import tr.secimharitasi.loader.VeriOzellikleri;

/**
 * Seçimleri MySQL'e yükler. Tablolar tek bir işlemde boşaltılıp yeniden doldurulur: yükleme yarıda kalırsa
 * eski veri yerinde kalır. Parti tablosuna dokunulmaz (sabit kimlikler Flyway'den gelir).
 * <p>
 * Tutarlılık bulguları "tutarlilik" log'una yazılır, veri değiştirilmez. Yalnız yabancı/birincil anahtar
 * nedeniyle yazılamayacak satırlar (HATA bulguları) atlanır.
 */
@Service
public class VeriYukleyici {

    private static final Logger log = LoggerFactory.getLogger(VeriYukleyici.class);

    private final JdbcTemplate jdbc;
    private final TransactionTemplate tx;
    private final VeriOzellikleri ozellikler;

    public VeriYukleyici(JdbcTemplate jdbc, TransactionTemplate tx, VeriOzellikleri ozellikler) {
        this.jdbc = jdbc;
        this.tx = tx;
        this.ozellikler = ozellikler;
    }

    /**
     * Kaynak son başarılı yüklemeden beri değişmediyse (ve zorla yükleme istenmediyse) yüklemeyi atlar.
     *
     * @return yüklendiyse özet, atlandıysa boş
     */
    public Optional<YuklemeOzeti> gerekirseYukle(boolean zorla) {
        String ozet = KaynakOzeti.hesapla(ozellikler.dizin(), ozellikler.kaynaklar(), ozellikler.mahalleGeo());
        List<String> son = jdbc.queryForList("SELECT kaynak_ozeti FROM veri_yukleme WHERE durum = 'tamam'"
                + " ORDER BY yukleme_id DESC LIMIT 1", String.class);
        if (!zorla && !son.isEmpty() && ozet.equals(son.get(0))) {
            log.info("Kaynak son yüklemeden beri değişmedi (özet {}), yükleme atlandı. Yine de yüklemek için "
                    + "ZORLA_YUKLE=true.", ozet.substring(0, 12));
            return Optional.empty();
        }
        return Optional.of(yukle(ozet));
    }

    public YuklemeOzeti yukle() {
        return yukle(KaynakOzeti.hesapla(ozellikler.dizin(), ozellikler.kaynaklar(), ozellikler.mahalleGeo()));
    }

    private YuklemeOzeti yukle(String kaynakOzeti) {
        Instant baslangic = Instant.now();
        KaynakHazirlayici.Hazirlik h = KaynakHazirlayici.hazirla(ozellikler.dizin(), ozellikler.kaynaklar(), ozellikler.mahalleGeo(),
                ozellikler.ilceToleransi(), ozellikler.partiToplamToleransi());

        Set<String> eksik = VeritabaniYazici.eksikPartiler(h.secimler(), h.ek(), new JdbcHedef(jdbc, 1).partiKimlikleri());
        if (!eksik.isEmpty()) {
            throw new EksikPartiException(eksik);
        }

        VeritabaniYazici yazici = new VeritabaniYazici(new JdbcHedef(jdbc, ozellikler.toplamBoyutu()));
        YuklemeOzeti ozet = tx.execute(durum -> yazici.yaz(h.secimler(), h.boyut(), h.ek(), h.mahalle(), h.bulgular()));
        jdbc.update("INSERT INTO veri_yukleme (baslangic, bitis, durum, secim_sayisi, il_satiri, ilce_satiri,"
                        + " oy_satiri, bulgu_sayisi, atlanan_satir, mahalle_satiri, belde_satiri, secilen_sayisi,"
                        + " kaynak_ozeti) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                Timestamp.from(baslangic), Timestamp.from(Instant.now()), "tamam", ozet.secim(), ozet.ilSatiri(),
                ozet.ilceSatiri(), ozet.oySatiri(), ozet.bulguSayisi(), ozet.atlananSatir(), ozet.mahalleSatiri(),
                ozet.beldeSatiri(), ozet.secilenSayisi(), kaynakOzeti);

        log.info("Yükleme tamam: {} seçim, {} il, {} ilçe birimi, {} il satırı, {} ilçe satırı, {} oy satırı",
                ozet.secim(), ozet.ilSayisi(), ozet.ilceSayisi(), ozet.ilSatiri(), ozet.ilceSatiri(), ozet.oySatiri());
        log.info("Ek veri: {} mahalle sonucu, {} belde, {} seçilen; anahtar nedeniyle atlanan {}",
                ozet.mahalleSatiri(), ozet.beldeSatiri(), ozet.secilenSayisi(), ozet.atlananSatir());
        log.info("Tutarlılık bulguları (veri değiştirilmedi): toplam {}, türlere göre {}", ozet.bulguSayisi(),
                ozet.bulgular());
        return ozet;
    }
}
