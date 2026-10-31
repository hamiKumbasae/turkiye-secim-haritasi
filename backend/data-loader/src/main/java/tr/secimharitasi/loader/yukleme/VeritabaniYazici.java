package tr.secimharitasi.loader.yukleme;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import tr.secimharitasi.loader.ek.BeldeKaydi;
import tr.secimharitasi.loader.ek.EkVeriOkuyucu;
import tr.secimharitasi.loader.ek.KapsamKaydi;
import tr.secimharitasi.loader.ek.MahalleOkuyucu;
import tr.secimharitasi.loader.ek.MahalleSatiri;
import tr.secimharitasi.loader.ek.SandalyeKaydi;
import tr.secimharitasi.loader.ek.SecilenKaydi;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.OyKaydi;
import tr.secimharitasi.loader.kaynak.SonucSatiri;
import tr.secimharitasi.loader.kaynak.YurtDisi;

/**
 * Bütün tabloları boşaltıp yeniden doldurur (çağıran tek bir işlem içinde çalıştırır). Spring'e bağlı değildir;
 * veritabanıyla yalnız {@link Hedef} üzerinden konuşur. Parti tablosuna dokunmaz: kimlikler Flyway'den gelir.
 * Yalnız yabancı/birincil anahtar nedeniyle yazılamayacak satırlar atlanır ve sayılır; değerler değiştirilmez.
 */
public final class VeritabaniYazici {

    private static final Logger log = LoggerFactory.getLogger(VeritabaniYazici.class);

    static final List<String> SILME_SIRASI = List.of("oy_mahalle", "sonuc_mahalle", "mahalle", "oy_belde",
            "sonuc_belde", "secilen", "sandalye_ilce", "kaynak_kapsami", "oy_ilce", "sonuc_ilce", "sandalye_il",
            "oy_il", "sonuc_il", "ilce", "il");

    private final Hedef hedef;
    private Map<String, Integer> parti;
    private int atlanan;

    public VeritabaniYazici(Hedef hedef) {
        this.hedef = hedef;
    }

    /** Veride olup parti tablosunda (ve takma adlarda) olmayan seçenek adları. */
    public static Set<String> eksikPartiler(List<KaynakSecim> secimler, EkVeriOkuyucu.Sonuc ek,
                                           Map<String, Integer> parti) {
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
        if (ek != null) {
            for (BeldeKaydi b : ek.beldeler()) {
                b.oy().keySet().stream().filter(a -> !parti.containsKey(a)).forEach(eksik::add);
                if (b.kazanan() != null && !parti.containsKey(b.kazanan())) {
                    eksik.add(b.kazanan());
                }
            }
            ek.secilenler().stream().map(SecilenKaydi::parti)
                    .filter(a -> a != null && !parti.containsKey(a)).forEach(eksik::add);
            ek.sandalyeler().stream().map(SandalyeKaydi::parti).filter(a -> !parti.containsKey(a)).forEach(eksik::add);
        }
        return eksik;
    }

    /**
     * @param secimler ana seçimler, ardından meclis, Senato ve ara seçimler (ana seçim, kendisine bağlanandan önce)
     * @param mahalle  null ise mahalle tabloları boş kalır
     */
    public YuklemeOzeti yaz(List<KaynakSecim> secimler, BoyutTablolari boyut, EkVeriOkuyucu.Sonuc ek,
                            MahalleOkuyucu mahalle, Map<tr.secimharitasi.loader.kontrol.BulguTuru, Long> bulgular) {
        parti = hedef.partiKimlikleri();
        atlanan = 0;

        SILME_SIRASI.forEach(t -> hedef.calistir("DELETE FROM " + t));
        hedef.calistir("UPDATE secim SET ana_secim_id = NULL");
        hedef.calistir("DELETE FROM secim");

        hedef.toplu("INSERT INTO il (plaka, ad) VALUES (?,?)",
                boyut.iller().entrySet().stream().map(e -> new Object[]{e.getKey(), e.getValue()}).toList());
        hedef.toplu("INSERT INTO ilce (ilce_id, plaka, ad, guncel, baslangic_yili, bitis_yili) VALUES (?,?,?,?,?,?)",
                boyut.ilceler().values().stream().map(i -> new Object[]{i.ilceId(), i.plaka(), i.ad(), i.guncel(),
                        i.baslangicYili(), i.bitisYili()}).toList());

        Set<String> secimIdleri = new HashSet<>();
        List<Object[]> secim = new ArrayList<>();
        List<Object[]> sonucIl = new ArrayList<>();
        List<Object[]> oyIl = new ArrayList<>();
        List<Object[]> sandalyeIl = new ArrayList<>();
        List<Object[]> sonucIlce = new ArrayList<>();
        List<Object[]> oyIlce = new ArrayList<>();

        for (KaynakSecim s : secimler) {
            String id = s.secimId();
            var d = s.dosya();
            secimIdleri.add(id);
            secim.add(new Object[]{id, s.tur().kod(), s.oylama().kod(), s.anaSecimId(), s.yil(), d.ad(),
                    kirp(s.aciklama(), 1000), d.contestType(), d.resultBasis(),
                    d.toplamSandalye() == null || d.toplamSandalye() == 0 ? null : d.toplamSandalye(),
                    s.birincilKaynak(), s.kaynakDurumu()});

            Set<Integer> iller = new HashSet<>();
            for (SonucSatiri r : d.iller()) {
                if (!iller.add(r.plaka()) || !boyut.iller().containsKey(r.plaka())) {
                    atlanan++;
                    continue;
                }
                sonucIl.add(new Object[]{id, r.plaka(), r.ad(), r.secmen(), r.oyKullanan(), r.gecerliOy(),
                        r.gecersizOy(), r.sandik(), r.katilim(), parti.get(r.kazanan()),
                        r.toplamVekil() == null || r.toplamVekil() == 0 ? null : r.toplamVekil(), r.notlar()});
                birlestir(r.oy()).forEach((p, v) -> oyIl.add(new Object[]{id, r.plaka(), p, v.oy(), v.oran()}));
                Map<Integer, Integer> sandalye = new LinkedHashMap<>();
                r.vekil().forEach((p, n) -> sandalye.merge(parti.get(p), n, Integer::sum));
                sandalye.forEach((p, n) -> sandalyeIl.add(new Object[]{id, r.plaka(), p, n}));
            }
            YurtDisi yd = d.yurtdisi();
            if (yd != null) {
                // Kaynakta yurt dışının kazananı ve seçmeni yok: boş bırakılır (türetilmez).
                sonucIl.add(new Object[]{id, 0, BoyutTablolari.YURT_DISI, null, yd.kullanilanOy(), yd.gecerliOy(),
                        null, null, yd.katilim(), null, null, "Yurt dışı ve gümrük oyları"});
                birlestir(yd.oy()).forEach((p, v) -> oyIl.add(new Object[]{id, 0, p, v.oy(), v.oran()}));
            }

            Set<String> ilceler = new HashSet<>();
            for (SonucSatiri r : d.ilceler()) {
                String iid = r.ilceId();
                if (!ilceler.add(iid) || !boyut.iller().containsKey(r.plaka()) || !boyut.ilceler().containsKey(iid)) {
                    atlanan++;
                    continue;
                }
                sonucIlce.add(new Object[]{id, iid, r.plaka(), r.ad(), r.secmen(), r.oyKullanan(), r.gecerliOy(),
                        r.gecersizOy(), r.sandik(), r.katilim(), parti.get(r.kazanan()), r.baskan(),
                        r.yalnizKazananBiliniyor(), r.notlar()});
                birlestir(r.oy()).forEach((p, v) -> oyIlce.add(new Object[]{id, iid, p, v.oy(), v.oran(),
                        v.aday()}));
            }
        }

        hedef.toplu("INSERT INTO secim (secim_id, tur, oylama, ana_secim_id, yil, tarih_metni, aciklama, yarisma_turu,"
                + " sonuc_temeli, toplam_sandalye, birincil_kaynak, kaynak_durumu) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                secim);
        hedef.toplu("INSERT INTO sonuc_il (secim_id, plaka, ad, secmen, oy_kullanan, gecerli_oy, gecersiz_oy, sandik,"
                + " katilim, kazanan_parti_id, toplam_vekil, not_metni) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", sonucIl);
        hedef.toplu("INSERT INTO oy_il (secim_id, plaka, parti_id, oy, oran) VALUES (?,?,?,?,?)", oyIl);
        hedef.toplu("INSERT INTO sandalye_il (secim_id, plaka, parti_id, sandalye) VALUES (?,?,?,?)", sandalyeIl);
        hedef.toplu("INSERT INTO sonuc_ilce (secim_id, ilce_id, plaka, ad, secmen, oy_kullanan, gecerli_oy,"
                + " gecersiz_oy, sandik, katilim, kazanan_parti_id, baskan, sadece_kazanan, not_metni)"
                + " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sonucIlce);
        hedef.toplu("INSERT INTO oy_ilce (secim_id, ilce_id, parti_id, oy, oran, aday) VALUES (?,?,?,?,?,?)", oyIlce);

        int belde = 0;
        int secilen = 0;
        if (ek != null) {
            belde = beldeler(ek.beldeler(), boyut, secimIdleri);
            secilen = secilenler(ek.secilenler(), boyut, secimIdleri);
            sandalyeler(ek.sandalyeler(), boyut, secimIdleri);
            kapsam(ek.kapsam(), secimIdleri);
        }
        int mahalleSatiri = mahalle == null ? 0 : mahalleler(mahalle, boyut, secimIdleri);

        return new YuklemeOzeti(secim.size(), sonucIl.size(), sonucIlce.size(), oyIl.size() + oyIlce.size(),
                boyut.iller().size(), boyut.ilceler().size(), mahalleSatiri, belde, secilen, Map.copyOf(bulgular),
                atlanan);
    }

    private int beldeler(List<BeldeKaydi> beldeler, BoyutTablolari boyut, Set<String> secimIdleri) {
        List<Object[]> sonuc = new ArrayList<>();
        List<Object[]> oy = new ArrayList<>();
        int id = 0;
        for (BeldeKaydi b : beldeler) {
            if (!secimIdleri.contains(b.secimId()) || !boyut.iller().containsKey(b.plaka())) {
                atlanan++;
                continue;
            }
            id++;
            String ilce = b.ilceId() != null && boyut.ilceler().containsKey(b.ilceId()) ? b.ilceId() : null;
            sonuc.add(new Object[]{id, b.secimId(), b.plaka(), ilce, b.ilceAd(), kirp(b.beldeAd(), 150), b.beldeKod(),
                    b.secmen(), b.oyKullanan(), b.gecerliOy(), b.gecersizOy(), b.sandik(), b.katilim(),
                    parti.get(b.kazanan()), kirp(b.aday(), 400), b.sadeceKazanan(), b.kaynak(), b.kontrol(), b.not()});
            Map<Integer, Long> toplam = new LinkedHashMap<>();
            for (var e : b.oy().entrySet()) {
                Integer p = parti.get(e.getKey());
                if (!toplam.containsKey(p)) {
                    toplam.put(p, e.getValue());
                } else if (e.getValue() != null) {
                    toplam.put(p, (toplam.get(p) == null ? 0 : toplam.get(p)) + e.getValue());
                }
            }
            int bid = id;
            toplam.forEach((p, o) -> oy.add(new Object[]{bid, p, o}));
        }
        hedef.toplu("INSERT INTO sonuc_belde (sonuc_belde_id, secim_id, plaka, ilce_id, ilce_ad, belde_ad, belde_kod,"
                + " secmen, oy_kullanan, gecerli_oy, gecersiz_oy, sandik, katilim, kazanan_parti_id, aday,"
                + " sadece_kazanan, kaynak, kontrol, not_metni) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sonuc);
        hedef.toplu("INSERT INTO oy_belde (sonuc_belde_id, parti_id, oy) VALUES (?,?,?)", oy);
        return sonuc.size();
    }

    private int secilenler(List<SecilenKaydi> secilenler, BoyutTablolari boyut, Set<String> secimIdleri) {
        List<Object[]> satir = new ArrayList<>();
        for (SecilenKaydi k : secilenler) {
            if (!secimIdleri.contains(k.secimId()) || !boyut.iller().containsKey(k.plaka()) || k.ad() == null) {
                atlanan++;
                continue;
            }
            satir.add(new Object[]{k.secimId(), k.plaka(), k.gorev(), kirp(k.ad(), 150),
                    k.parti() == null ? null : parti.get(k.parti()), kirp(k.partiAdiKaynakta(), 150),
                    kirp(k.bolge(), 50), kirp(k.kisiLink(), 200)});
        }
        hedef.toplu("INSERT INTO secilen (secim_id, plaka, gorev, ad, parti_id, parti_adi_kaynakta, bolge, kisi_link)"
                + " VALUES (?,?,?,?,?,?,?,?)", satir);
        return satir.size();
    }

    private void sandalyeler(List<SandalyeKaydi> sandalyeler, BoyutTablolari boyut, Set<String> secimIdleri) {
        Map<String, Object[]> satir = new LinkedHashMap<>();
        for (SandalyeKaydi k : sandalyeler) {
            if (!secimIdleri.contains(k.secimId()) || !boyut.ilceler().containsKey(k.ilceId())) {
                atlanan++;
                continue;
            }
            Integer p = parti.get(k.parti());
            String anahtar = k.secimId() + "|" + k.ilceId() + "|" + p;
            Object[] onceki = satir.get(anahtar);
            satir.put(anahtar, new Object[]{k.secimId(), k.ilceId(), p,
                    k.sandalye() + (onceki == null ? 0 : (Integer) onceki[3])});
        }
        hedef.toplu("INSERT INTO sandalye_ilce (secim_id, ilce_id, parti_id, sandalye) VALUES (?,?,?,?)",
                new ArrayList<>(satir.values()));
    }

    private void kapsam(List<KapsamKaydi> kapsam, Set<String> secimIdleri) {
        Map<String, Object[]> satir = new LinkedHashMap<>();
        for (KapsamKaydi k : kapsam) {
            if (!secimIdleri.contains(k.secimId())) {
                atlanan++;
                continue;
            }
            satir.putIfAbsent(k.secimId() + "|" + k.veri(), new Object[]{k.secimId(), k.veri(), k.bulunan(),
                    k.beklenen(), k.durum(), kirp(k.aciklama(), 1000)});
        }
        hedef.toplu("INSERT INTO kaynak_kapsami (secim_id, veri, bulunan, beklenen, durum, aciklama)"
                + " VALUES (?,?,?,?,?,?)", new ArrayList<>(satir.values()));
    }

    private int mahalleler(MahalleOkuyucu okuyucu, BoyutTablolari boyut, Set<String> secimIdleri) {
        Map<String, String> adlar = okuyucu.adlar();
        log.info("Mahalle adları: {}", adlar.size());
        Set<String> eklenen = new HashSet<>();
        int toplam = 0;
        for (String sid : okuyucu.secimler()) {
            if (!secimIdleri.contains(sid)) {
                log.warn("Mahalle dosyası {} için seçim yok, atlandı", sid);
                continue;
            }
            List<MahalleSatiri> satirlar = okuyucu.oku(sid);
            Set<String> eksik = new TreeSet<>();
            satirlar.forEach(m -> {
                m.oy().keySet().stream().filter(a -> !parti.containsKey(a)).forEach(eksik::add);
                if (m.kazanan() != null && !parti.containsKey(m.kazanan())) {
                    eksik.add(m.kazanan());
                }
            });
            if (!eksik.isEmpty()) {
                throw new EksikPartiException(eksik);
            }
            List<Object[]> yeniMahalle = new ArrayList<>();
            List<Object[]> sonuc = new ArrayList<>();
            List<Object[]> oy = new ArrayList<>();
            Set<String> bu = new HashSet<>();
            for (MahalleSatiri m : satirlar) {
                String k = MahalleOkuyucu.anahtar(m.ilceId(), m.mahalleId());
                if (!boyut.ilceler().containsKey(m.ilceId()) || !bu.add(k)) {
                    atlanan++;
                    continue;
                }
                if (eklenen.add(k)) {
                    yeniMahalle.add(new Object[]{m.ilceId(), m.mahalleId(), kirp(adlar.get(k), 150)});
                }
                sonuc.add(new Object[]{sid, m.ilceId(), m.mahalleId(), m.secmen(), m.oyKullanan(), m.gecerliOy(),
                        m.sandik(), m.katilim(), parti.get(m.kazanan())});
                birlestir(m.oy()).forEach((p, v) -> oy.add(new Object[]{sid, m.ilceId(), m.mahalleId(), p, v.oy(),
                        v.oran()}));
            }
            hedef.toplu("INSERT INTO mahalle (ilce_id, mahalle_id, ad) VALUES (?,?,?)", yeniMahalle);
            hedef.toplu("INSERT INTO sonuc_mahalle (secim_id, ilce_id, mahalle_id, secmen, oy_kullanan, gecerli_oy,"
                    + " sandik, katilim, kazanan_parti_id) VALUES (?,?,?,?,?,?,?,?,?)", sonuc);
            hedef.toplu("INSERT INTO oy_mahalle (secim_id, ilce_id, mahalle_id, parti_id, oy, oran)"
                    + " VALUES (?,?,?,?,?,?)", oy);
            toplam += sonuc.size();
            log.info("  mahalle {}: {} satır, {} oy", sid, sonuc.size(), oy.size());
        }
        return toplam;
    }

    /**
     * Seçenek adlarını parti kimliğine çevirir; aynı kimliğe düşen yazımlar (takma ad) toplanır. Oran, tek yazımda
     * kaynaktaki değerdir; birden çok yazım birleşirse hesaplanamayacağı için boş bırakılır.
     */
    private Map<Integer, OyKaydi> birlestir(Map<String, OyKaydi> oy) {
        Map<Integer, OyKaydi> m = new LinkedHashMap<>();
        oy.forEach((ad, v) -> {
            Integer p = parti.get(ad);
            OyKaydi onceki = m.get(p);
            if (onceki == null) {
                m.put(p, v);
            } else {
                Long toplam = onceki.oy() == null ? v.oy() : v.oy() == null ? onceki.oy() : onceki.oy() + v.oy();
                m.put(p, new OyKaydi(toplam, (BigDecimal) null, onceki.aday()));
            }
        });
        return m;
    }

    private static String kirp(String s, int n) {
        return s == null || s.length() <= n ? s : s.substring(0, n);
    }
}
