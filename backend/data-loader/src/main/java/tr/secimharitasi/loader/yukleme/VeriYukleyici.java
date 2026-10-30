package tr.secimharitasi.loader.yukleme;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import tr.secimharitasi.loader.VeriOzellikleri;
import tr.secimharitasi.loader.kaynak.KaynakOkuyucu;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.OyKaydi;
import tr.secimharitasi.loader.kaynak.SonucSatiri;
import tr.secimharitasi.loader.kaynak.YurtDisi;
import tr.secimharitasi.loader.kontrol.Bulgu;
import tr.secimharitasi.loader.kontrol.BulguTuru;
import tr.secimharitasi.loader.kontrol.TutarlilikKontrolu;

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
    private static final Logger tutarlilik = LoggerFactory.getLogger("tutarlilik");

    private static final List<String> SILME_SIRASI =
            List.of("oy_ilce", "sonuc_ilce", "sandalye_il", "oy_il", "sonuc_il", "ilce", "il", "secim");

    private final JdbcTemplate jdbc;
    private final TransactionTemplate tx;
    private final VeriOzellikleri ozellikler;

    public VeriYukleyici(JdbcTemplate jdbc, TransactionTemplate tx, VeriOzellikleri ozellikler) {
        this.jdbc = jdbc;
        this.tx = tx;
        this.ozellikler = ozellikler;
    }

    public YuklemeOzeti yukle() {
        Instant baslangic = Instant.now();
        log.info("Kaynak okunuyor: {}", ozellikler.dizin().toAbsolutePath());
        List<KaynakSecim> secimler = new KaynakOkuyucu(ozellikler.dizin(), ozellikler.kaynaklar()).oku();
        log.info("{} seçim dosyası okundu", secimler.size());

        Map<String, Integer> parti = partiKimlikleri();
        eksikPartileriDenetle(secimler, parti);

        BoyutTablolari boyut = BoyutTablolari.olustur(secimler);
        TutarlilikKontrolu kontrol =
                new TutarlilikKontrolu(ozellikler.ilceToleransi(), ozellikler.partiToplamToleransi());
        Map<BulguTuru, Long> sayac = new EnumMap<>(BulguTuru.class);
        for (KaynakSecim s : secimler) {
            for (Bulgu b : kontrol.kontrolEt(s, boyut.iller().keySet())) {
                sayac.merge(b.tur(), 1L, Long::sum);
                if (b.satirAtlanir()) {
                    tutarlilik.error("{} — satır yüklenmedi", b);
                } else {
                    tutarlilik.warn("{}", b);
                }
            }
        }

        YuklemeOzeti ozet = tx.execute(durum -> yaz(secimler, boyut, parti, sayac));
        jdbc.update("INSERT INTO veri_yukleme (baslangic, bitis, durum, secim_sayisi, il_satiri, ilce_satiri,"
                        + " oy_satiri, bulgu_sayisi, atlanan_satir) VALUES (?,?,?,?,?,?,?,?,?)",
                Timestamp.from(baslangic), Timestamp.from(Instant.now()), "tamam", ozet.secim(), ozet.ilSatiri(),
                ozet.ilceSatiri(), ozet.oySatiri(), ozet.bulguSayisi(), ozet.atlananSatir());

        log.info("Yükleme tamam: {} seçim, {} il, {} ilçe birimi, {} il satırı, {} ilçe satırı, {} oy satırı",
                ozet.secim(), ozet.ilSayisi(), ozet.ilceSayisi(), ozet.ilSatiri(), ozet.ilceSatiri(), ozet.oySatiri());
        log.info("Tutarlılık bulguları (veri değiştirilmedi): toplam {}, türlere göre {}", ozet.bulguSayisi(),
                ozet.bulgular());
        return ozet;
    }

    private Map<String, Integer> partiKimlikleri() {
        Map<String, Integer> m = new java.util.HashMap<>();
        jdbc.query("SELECT ad, parti_id FROM parti", rs -> {
            m.put(rs.getString(1), rs.getInt(2));
        });
        return m;
    }

    private static void eksikPartileriDenetle(List<KaynakSecim> secimler, Map<String, Integer> parti) {
        Set<String> eksik = new TreeSet<>();
        for (KaynakSecim s : secimler) {
            List<SonucSatiri> satirlar = new ArrayList<>(s.dosya().iller());
            satirlar.addAll(s.dosya().ilceler());
            for (SonucSatiri r : satirlar) {
                r.oy().keySet().stream().filter(a -> !parti.containsKey(a)).forEach(eksik::add);
                r.vekil().keySet().stream().filter(a -> !parti.containsKey(a)).forEach(eksik::add);
                if (r.kazanan() != null && !parti.containsKey(r.kazanan())) {
                    eksik.add(r.kazanan());
                }
            }
            if (s.dosya().yurtdisi() != null) {
                s.dosya().yurtdisi().oy().keySet().stream().filter(a -> !parti.containsKey(a)).forEach(eksik::add);
            }
        }
        if (!eksik.isEmpty()) {
            throw new EksikPartiException(eksik);
        }
    }

    private YuklemeOzeti yaz(List<KaynakSecim> secimler, BoyutTablolari boyut, Map<String, Integer> parti,
                             Map<BulguTuru, Long> sayac) {
        SILME_SIRASI.forEach(t -> jdbc.update("DELETE FROM " + t));

        toplu("INSERT INTO il (plaka, ad) VALUES (?,?)",
                boyut.iller().entrySet().stream().map(e -> new Object[]{e.getKey(), e.getValue()}).toList());
        toplu("INSERT INTO ilce (ilce_id, plaka, ad, guncel, baslangic_yili, bitis_yili) VALUES (?,?,?,?,?,?)",
                boyut.ilceler().values().stream().map(i -> new Object[]{i.ilceId(), i.plaka(), i.ad(), i.guncel(),
                        i.baslangicYili(), i.bitisYili()}).toList());

        List<Object[]> secim = new ArrayList<>();
        List<Object[]> sonucIl = new ArrayList<>();
        List<Object[]> oyIl = new ArrayList<>();
        List<Object[]> sandalye = new ArrayList<>();
        List<Object[]> sonucIlce = new ArrayList<>();
        List<Object[]> oyIlce = new ArrayList<>();
        int atlanan = 0;

        for (KaynakSecim s : secimler) {
            String id = s.secimId();
            var d = s.dosya();
            secim.add(new Object[]{id, s.tur().kod(), s.yil(), d.ad(), d.contestType(), d.resultBasis(),
                    d.toplamSandalye() == null || d.toplamSandalye() == 0 ? null : d.toplamSandalye(),
                    s.birincilKaynak(), s.kaynakDurumu()});

            Set<Integer> iller = new HashSet<>();
            for (SonucSatiri r : d.iller()) {
                if (!iller.add(r.plaka())) {
                    atlanan++;
                    continue;
                }
                sonucIl.add(new Object[]{id, r.plaka(), r.ad(), r.secmen(), r.oyKullanan(), r.gecerliOy(),
                        r.gecersizOy(), r.sandik(), r.katilim(), parti.get(r.kazanan()),
                        r.toplamVekil() == null || r.toplamVekil() == 0 ? null : r.toplamVekil(), r.notlar()});
                r.oy().forEach((p, v) -> oyIl.add(new Object[]{id, r.plaka(), parti.get(p), v.oy(), v.oran()}));
                r.vekil().forEach((p, n) -> sandalye.add(new Object[]{id, r.plaka(), parti.get(p), n}));
            }
            YurtDisi yd = d.yurtdisi();
            if (yd != null) {
                // Kaynakta yurt dışının kazananı ve seçmeni yok: boş bırakılır (türetilmez).
                sonucIl.add(new Object[]{id, 0, BoyutTablolari.YURT_DISI, null, yd.kullanilanOy(), yd.gecerliOy(),
                        null, null, yd.katilim(), null, null, "Yurt dışı ve gümrük oyları"});
                yd.oy().forEach((p, v) -> oyIl.add(new Object[]{id, 0, parti.get(p), v.oy(), v.oran()}));
            }

            Set<String> ilceler = new HashSet<>();
            for (SonucSatiri r : d.ilceler()) {
                String iid = r.ilceId();
                if (!ilceler.add(iid) || !boyut.iller().containsKey(r.plaka())
                        || !boyut.ilceler().containsKey(iid)) {
                    atlanan++;
                    continue;
                }
                sonucIlce.add(new Object[]{id, iid, r.plaka(), r.ad(), r.secmen(), r.oyKullanan(), r.gecerliOy(),
                        r.gecersizOy(), r.sandik(), r.katilim(), parti.get(r.kazanan()), r.baskan(),
                        r.yalnizKazananBiliniyor(), r.notlar()});
                for (Map.Entry<String, OyKaydi> e : r.oy().entrySet()) {
                    OyKaydi v = e.getValue();
                    oyIlce.add(new Object[]{id, iid, parti.get(e.getKey()), v.oy(), v.oran(), v.aday()});
                }
            }
        }

        toplu("INSERT INTO secim (secim_id, tur, yil, tarih_metni, yarisma_turu, sonuc_temeli, toplam_sandalye,"
                + " birincil_kaynak, kaynak_durumu) VALUES (?,?,?,?,?,?,?,?,?)", secim);
        toplu("INSERT INTO sonuc_il (secim_id, plaka, ad, secmen, oy_kullanan, gecerli_oy, gecersiz_oy, sandik,"
                + " katilim, kazanan_parti_id, toplam_vekil, not_metni) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", sonucIl);
        toplu("INSERT INTO oy_il (secim_id, plaka, parti_id, oy, oran) VALUES (?,?,?,?,?)", oyIl);
        toplu("INSERT INTO sandalye_il (secim_id, plaka, parti_id, sandalye) VALUES (?,?,?,?)", sandalye);
        toplu("INSERT INTO sonuc_ilce (secim_id, ilce_id, plaka, ad, secmen, oy_kullanan, gecerli_oy, gecersiz_oy,"
                + " sandik, katilim, kazanan_parti_id, baskan, sadece_kazanan, not_metni)"
                + " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sonucIlce);
        toplu("INSERT INTO oy_ilce (secim_id, ilce_id, parti_id, oy, oran, aday) VALUES (?,?,?,?,?,?)", oyIlce);

        return new YuklemeOzeti(secim.size(), sonucIl.size(), sonucIlce.size(), oyIl.size() + oyIlce.size(),
                boyut.iller().size(), boyut.ilceler().size(), Map.copyOf(sayac), atlanan);
    }

    private void toplu(String sql, List<Object[]> satirlar) {
        int boyut = ozellikler.toplamBoyutu();
        for (int i = 0; i < satirlar.size(); i += boyut) {
            jdbc.batchUpdate(sql, satirlar.subList(i, Math.min(i + boyut, satirlar.size())));
        }
    }
}
