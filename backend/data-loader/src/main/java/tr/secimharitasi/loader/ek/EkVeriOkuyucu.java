package tr.secimharitasi.loader.ek;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.NullNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import tr.secimharitasi.common.OylamaTuru;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.OyKaydi;
import tr.secimharitasi.loader.kaynak.SecimDosyasi;
import tr.secimharitasi.loader.kaynak.SonucSatiri;

/**
 * data/normalized/ek/ ve meclis_2024.json'u okur (dosyalara yazmaz). Kurallar SQLite yükleyicisiyle
 * (scripts/veritabani/ek.py) aynıdır:
 * <ul>
 *   <li>Senato: il oyları aday satırlarından; ilçe oyları TÜİK yayınından (yalnız taranmış iller), öteki
 *       ilçelerde yalnız birinci gelen parti (Vikipedi, adından ilçeye eşlenir).</li>
 *   <li>Ara/yenileme: il ya da seçim çevresi düzeyi; bir ilde birden çok çevre varsa il satırında toplanır.</li>
 *   <li>Kaynakta "doğrulanamayan" diye işaretli alanlar boş bırakılır ve not düşülür; okuma hatası olduğu belli
 *       olan, INT'e sığmayan sayılar da boş bırakılır. Başka hiçbir değer değiştirilmez.</li>
 * </ul>
 */
public final class EkVeriOkuyucu {

    public record Sonuc(List<KaynakSecim> secimler, List<SecilenKaydi> secilenler, List<BeldeKaydi> beldeler,
                        List<SandalyeKaydi> sandalyeler, List<KapsamKaydi> kapsam, int eslesmeyenSenatoIlcesi) {
    }

    private static final Pattern YIL = Pattern.compile("^(\\d{4})");
    private static final Pattern TARIH = Pattern.compile("\\d{1,2} \\S+ \\d{4}");
    private static final Set<String> SKALER = Set.of("secmen", "oyKullanan", "gecerliOy", "muteber", "sandik",
            "gecersizOy");
    private static final Map<String, String> ARA_ANA_SECIM = Map.of(
            "2009yenileme_belediye_baskanligi", "2009yerel",
            "2019istanbul_bb_yenileme", "2019yerel",
            "2024yenileme_belediye_baskanligi", "2024yerel",
            "2024yenileme_belediye_meclisi", "2024yerel_bm");

    private final Path normalize;
    private final ObjectMapper json = new ObjectMapper();

    public EkVeriOkuyucu(Path normalizeDizin) {
        this.normalize = normalizeDizin;
    }

    /**
     * @param oncekiler ana seçimler ve meclis oylamaları (ilçe adı eşlemesi ve seçim kimlikleri için)
     */
    public Sonuc oku(List<KaynakSecim> oncekiler) {
        IlceIndeksi indeks = new IlceIndeksi();
        oncekiler.forEach(indeks::ekle);
        Set<String> secimIdleri = new HashSet<>();
        oncekiler.forEach(s -> secimIdleri.add(s.secimId()));

        List<KaynakSecim> secimler = new ArrayList<>();
        List<SecilenKaydi> secilenler = new ArrayList<>();
        List<BeldeKaydi> beldeler = new ArrayList<>();
        List<KapsamKaydi> kapsam = new ArrayList<>();

        milletvekilleri(secilenler, kapsam);
        int eslesmeyen = senato(indeks, secimler, secilenler, kapsam);
        araSecimler(indeks, secimler, beldeler, kapsam);
        secimler.forEach(s -> secimIdleri.add(s.secimId()));
        beldeBaskanliklari(indeks, secimIdleri, beldeler, kapsam);
        belediyeMeclisiBeldeleri(indeks, beldeler, kapsam);
        List<SandalyeKaydi> sandalyeler = meclis2024();
        return new Sonuc(secimler, secilenler, beldeler, sandalyeler, kapsam, eslesmeyen);
    }

    // ---------------------------------------------------------------------------------------------------------
    private void milletvekilleri(List<SecilenKaydi> secilenler, List<KapsamKaydi> kapsam) {
        for (Path p : dosyalar("ek/milletvekilleri")) {
            JsonNode d = oku(p);
            String sid = d.path("secim").asText();
            for (JsonNode k : d.path("kayitlar")) {
                secilenler.add(secilen(sid, k, "milletvekili"));
            }
            kapsam.add(kapsam(sid, "milletvekilleri", d.path("kapsam")));
        }
    }

    private int senato(IlceIndeksi indeks, List<KaynakSecim> secimler, List<SecilenKaydi> secilenler,
                       List<KapsamKaydi> kapsam) {
        int eslesmeyen = 0;
        for (Path p : dosyalar("ek/senato")) {
            JsonNode d = oku(p);
            String sid = d.path("secim").asText(ad(p));
            int yil = yil(sid);

            List<SonucSatiri> iller = new ArrayList<>();
            for (JsonNode r : d.path("iller")) {
                Map<String, OyKaydi> oy = new LinkedHashMap<>();
                for (JsonNode a : r.path("adaylar")) {
                    // partisiz satır kaynakta bağımsız aday ('BĞMZ' kısaltması, partiAdi = kişi adı)
                    String parti = metin(a, "parti");
                    if (parti == null) {
                        String kisa = metin(a, "kisaltma");
                        parti = kisa != null && kisa.startsWith("BĞMZ") ? "Bağımsız"
                                : kisa != null ? kisa : metin(a, "partiAdi");
                    }
                    Long o = uzun(a, "oy");
                    if (o != null) {
                        OyKaydi onceki = oy.get(parti);
                        oy.put(parti, new OyKaydi(onceki == null ? o : onceki.oy() + o, null, null));
                    }
                }
                List<String> bozuk = new ArrayList<>();
                iller.add(SonucSatiri.yeni(r.path("plaka").asInt(), metin(r, "il"), null, tam(r, "secmen", bozuk),
                        null, tam(r, "gecerliOy", bozuk), tam(r, "gecersizOy", bozuk), tam(r, "sandik", bozuk),
                        null, enCok(oy), false, okunamayanNotu(bozuk), oy));
            }

            List<SonucSatiri> ilceler = new ArrayList<>();
            Set<String> gorulen = new HashSet<>();
            for (JsonNode il : d.path("ilceOylariTuik").path("iller")) {
                for (JsonNode r : il.path("ilceler")) {
                    String geom = metin(r, "geomId");
                    if (geom == null || !gorulen.add(geom)) {
                        continue;
                    }
                    ilceler.add(dogrulanmis(il.path("plaka").asInt(), metin(r, "ilce"), geom, r, null));
                }
            }
            KaynakSecim tuikIlceleri = secim(sid, yil, SecimTuru.SENATO, OylamaTuru.SENATO, null,
                    metin(d, "aciklama"), yil + " Cumhuriyet Senatosu seçimi", List.of(), ilceler);
            indeks.ekle(tuikIlceleri);

            for (JsonNode r : d.path("ilceBirincileri")) {
                int plaka = r.path("plaka").asInt();
                String iid = indeks.bul(plaka, metin(r, "ilce"), yil);
                if (iid == null) {
                    eslesmeyen++;
                    continue;
                }
                if (!gorulen.add(iid)) {
                    continue;
                }
                ilceler.add(SonucSatiri.yeni(plaka, metin(r, "ilce"), iid, null, null, null, null, null, null,
                        metin(r, "birinciParti"), true, "Yalnız ilçede birinci gelen parti biliniyor (Vikipedi)",
                        Map.of()));
            }
            KaynakSecim senato = secim(sid, yil, SecimTuru.SENATO, OylamaTuru.SENATO, null, metin(d, "aciklama"),
                    yil + " Cumhuriyet Senatosu seçimi", iller, ilceler);
            secimler.add(senato);
            // İlçe birincilerinin kaynaktaki adları da sonraki eşlemelerde (beldeler) kullanılır.
            indeks.ekle(senato);
            for (JsonNode k : d.path("secilenler")) {
                secilenler.add(secilen(sid, k, "senator"));
            }
            kapsam.add(kapsam(sid, "senatorler", d.path("kapsam").path("senator")));
        }
        return eslesmeyen;
    }

    private void araSecimler(IlceIndeksi indeks, List<KaynakSecim> secimler, List<BeldeKaydi> beldeler,
                             List<KapsamKaydi> kapsam) {
        for (Path p : dosyalar("ek/yenileme_ara")) {
            JsonNode d = oku(p);
            String sid = ad(p);
            int yil = yil(sid);
            OylamaTuru oylama = sid.contains("mv_ara") ? OylamaTuru.MILLETVEKILI
                    : sid.contains("meclisi") ? OylamaTuru.BELEDIYE_MECLISI : OylamaTuru.BASKANLIK;
            String aciklama = metin(d, "aciklama");
            Matcher t = TARIH.matcher(aciklama == null ? "" : aciklama);
            String tarih = t.find() ? t.group() : String.valueOf(yil);

            List<SonucSatiri> iller = new ArrayList<>();
            List<SonucSatiri> ilceler = new ArrayList<>();
            for (JsonNode r : ilCevreleriniBirlestir(d.path("iller"))) {
                String cevre = metin(r, "secimCevresi");
                SonucSatiri il = dogrulanmis(r.path("plaka").asInt(), metin(r, "il"), null, r,
                        cevre == null ? null : "Seçim çevresi: " + cevre);
                iller.add(il);
                for (JsonNode ri : r.path("ilceler")) {
                    if (metin(ri, "geomId") != null) {
                        ilceler.add(dogrulanmis(r.path("plaka").asInt(), metin(ri, "ilce"), metin(ri, "geomId"),
                                ri, null));
                    }
                }
            }
            for (JsonNode r : d.path("birimler")) {
                if (r.hasNonNull("beldeId") || metin(r, "belde") != null) {
                    beldeler.add(belde(indeks, sid, r.path("plaka").asInt(), r, metin(r, "ilce"), metin(r, "belde"),
                            metin(r, "geomId"), tamOrNull(r.get("beldeId")), "ysk", metin(r, "kazanan"), null,
                            false, null, r.path("oy"), null));
                } else {
                    ilceler.add(dogrulanmis(r.path("plaka").asInt(), metin(r, "ilce"), metin(r, "geomId"), r, null));
                }
            }
            KaynakSecim s = secim(sid, yil, SecimTuru.ARA, oylama, ARA_ANA_SECIM.get(sid), aciklama, tarih, iller,
                    ilceler);
            secimler.add(s);
            indeks.ekle(s);
            kapsam.add(new KapsamKaydi(sid, "yenileme_ara", null, null, null, metin(d, "duzey")));
        }
    }

    private void beldeBaskanliklari(IlceIndeksi indeks, Set<String> secimIdleri, List<BeldeKaydi> beldeler,
                                    List<KapsamKaydi> kapsam) {
        for (Path p : dosyalar("ek/beldeler")) {
            JsonNode d = oku(p);
            String sid = secimIdleri.contains(d.path("secim").asText()) ? d.path("secim").asText() : ad(p);
            for (JsonNode k : d.path("kayitlar")) {
                JsonNode tuik = k.get("tuik");
                boolean tuikVar = tuik != null && tuik.isObject();
                JsonNode oy;
                if (tuikVar) {
                    oy = tuik.path("oy");
                } else {
                    var o = json.createObjectNode();
                    if (metin(k, "kazanan") != null) {
                        o.set(metin(k, "kazanan"), k.hasNonNull("oy") ? k.get("oy") : NullNode.getInstance());
                    }
                    oy = o;
                }
                beldeler.add(belde(indeks, sid, k.path("plaka").asInt(), tuikVar ? tuik : json.createObjectNode(),
                        metin(k, "ilce"), metin(k, "belde"), null, null, tuikVar ? "tuik" : "wikipedia",
                        metin(k, "kazanan"), metin(k, "aday"), !tuikVar, null, oy, null));
            }
            kapsam.add(kapsam(sid, "beldeler", d.path("kapsam")));
        }
    }

    private void belediyeMeclisiBeldeleri(IlceIndeksi indeks, List<BeldeKaydi> beldeler, List<KapsamKaydi> kapsam) {
        for (Path p : dosyalar("ek/belediye_meclisi")) {
            JsonNode d = oku(p);
            String sid = ad(p) + "_bm";
            for (JsonNode r : d.path("birimler")) {
                boolean belde = "belde".equals(metin(r, "tip")) || r.hasNonNull("beldeId") || metin(r, "belde") != null;
                if (!belde) {
                    continue;
                }
                boolean ysk = r.hasNonNull("yskIlceId");
                String ilceAd = metin(r, "ilce") != null ? metin(r, "ilce") : metin(r, "ustIlce");
                String beldeAd = metin(r, "belde") != null ? metin(r, "belde")
                        : metin(r, "ad") != null ? metin(r, "ad") : metin(r, "adKaynakta");
                beldeler.add(belde(indeks, sid, r.path("plaka").asInt(), r, ilceAd, beldeAd, metin(r, "geomId"),
                        tamOrNull(r.get("beldeId")), ysk ? "ysk" : "tuik", metin(r, "kazanan"), null, false,
                        metin(r.path("kontrol"), "durum"), r.path("oy"), null));
            }
            kapsam.add(new KapsamKaydi(sid, "belediye_meclisi", null, null, null, metin(d, "aciklama")));
        }
        for (Path p : dosyalar("ek/il_genel_meclisi")) {
            JsonNode d = oku(p);
            kapsam.add(new KapsamKaydi(ad(p) + "_igm", "il_genel_meclisi", null, null, null, metin(d, "aciklama")));
        }
    }

    private List<SandalyeKaydi> meclis2024() {
        Path p = normalize.resolve("meclis_2024.json");
        List<SandalyeKaydi> liste = new ArrayList<>();
        if (!Files.isRegularFile(p)) {
            return liste;
        }
        oku(p).fields().forEachRemaining(e -> e.getValue().path("partiler").fields().forEachRemaining(pt -> {
            if (pt.getValue().asInt() > 0) {
                liste.add(new SandalyeKaydi("2024yerel_bm", e.getKey(), pt.getKey(), pt.getValue().asInt()));
            }
        }));
        return liste;
    }

    // ---------------------------------------------------------------------------------------------------------
    /** Bir ilde birden çok seçim çevresi varsa (1986: Manisa 1 ve 2) il satırında toplanır. */
    private List<JsonNode> ilCevreleriniBirlestir(JsonNode iller) {
        Map<Integer, List<JsonNode>> gruplar = new LinkedHashMap<>();
        for (JsonNode r : iller) {
            gruplar.computeIfAbsent(r.path("plaka").asInt(), k -> new ArrayList<>()).add(r);
        }
        List<JsonNode> sonuc = new ArrayList<>();
        gruplar.forEach((plaka, rs) -> {
            if (rs.size() == 1) {
                sonuc.add(rs.get(0));
                return;
            }
            var top = json.createObjectNode();
            top.put("il", metin(rs.get(0), "il"));
            top.put("plaka", plaka);
            top.put("secimCevresi", String.join(" + ", rs.stream().map(r -> r.path("secimCevresi").asText()).toList()));
            for (String alan : List.of("secmen", "oyKullanan", "gecerliOy", "gecersizOy", "muteber", "sandik")) {
                if (rs.stream().allMatch(r -> r.hasNonNull(alan))) {
                    top.put(alan, rs.stream().mapToLong(r -> r.get(alan).asLong()).sum());
                }
            }
            var oy = top.putObject("oy");
            for (JsonNode r : rs) {
                r.path("oy").fields().forEachRemaining(e ->
                        oy.put(e.getKey(), oy.path(e.getKey()).asLong(0) + e.getValue().asLong(0)));
            }
            sonuc.add(top);
        });
        return sonuc;
    }

    /**
     * TÜİK/ara seçim satırı -> SonucSatiri. 'muteber' (eski yayınlarda geçerli oy) geçerli oya, ayrı 'Bağımsız'
     * alanı oylara taşınır; 'dogrulanamayanAlanlar' boş bırakılır. Kazanan kaynakta yoksa en çok oy alan.
     */
    private SonucSatiri dogrulanmis(int plaka, String ad, String geomId, JsonNode r, String ekNot) {
        List<String> bozuk = new ArrayList<>();
        Map<String, OyKaydi> oy = oylar(r.path("oy"), bozuk);
        if (r.path("Bağımsız").isIntegralNumber()) {
            oy.putIfAbsent("Bağımsız", new OyKaydi(r.get("Bağımsız").asLong(), null, null));
        }
        Set<String> dogrulanamayan = new HashSet<>();
        r.path("dogrulanamayanAlanlar").forEach(a -> dogrulanamayan.add(a.asText()));
        Integer secmen = dogrulanamayan.contains("secmen") ? null : tam(r, "secmen", bozuk);
        Integer oyKullanan = dogrulanamayan.contains("oyKullanan") ? null : tam(r, "oyKullanan", bozuk);
        Integer sandik = dogrulanamayan.contains("sandik") ? null : tam(r, "sandik", bozuk);
        Integer gecersiz = dogrulanamayan.contains("gecersizOy") ? null : tam(r, "gecersizOy", bozuk);
        Integer gecerli = r.has("gecerliOy") ? tam(r, "gecerliOy", bozuk) : tam(r, "muteber", bozuk);
        if (dogrulanamayan.contains("gecerliOy") || dogrulanamayan.contains("muteber")) {
            gecerli = null;
        }
        for (String alan : dogrulanamayan) {
            if (!SKALER.contains(alan) && oy.containsKey(alan)) {
                oy.put(alan, new OyKaydi(null, null, null));
            }
        }
        List<String> notlar = new ArrayList<>();
        if (ekNot != null) {
            notlar.add(ekNot);
        }
        if (!dogrulanamayan.isEmpty()) {
            notlar.add("Kaynakta doğrulanamayan alanlar boş bırakıldı: "
                    + String.join(", ", iterasyonSirasi(r.path("dogrulanamayanAlanlar"))));
        }
        String okunamayan = okunamayanNotu(bozuk);
        if (okunamayan != null) {
            notlar.add(okunamayan);
        }
        String kazanan = metin(r, "kazanan") != null ? metin(r, "kazanan") : enCok(oy);
        return SonucSatiri.yeni(plaka, ad, geomId, secmen, oyKullanan, gecerli, gecersiz, sandik,
                ondalik(r, "katilim"), kazanan, false, notlar.isEmpty() ? null : String.join(" | ", notlar), oy);
    }

    private BeldeKaydi belde(IlceIndeksi indeks, String sid, int plaka, JsonNode r, String ilceAd, String beldeAd,
                             String ilceId, Integer beldeKod, String kaynak, String kazanan, String aday,
                             boolean sadeceKazanan, String kontrol, JsonNode oyNode, String not) {
        if (ilceId == null) {
            ilceId = indeks.bul(plaka, ilceAd, yil(sid));
        }
        List<String> bozuk = new ArrayList<>();
        Map<String, Long> oy = new LinkedHashMap<>();
        oylar(oyNode, bozuk).forEach((p, v) -> oy.put(p, v.oy()));
        BeldeKaydi b = new BeldeKaydi(sid, plaka, ilceId, ilceAd, beldeAd, beldeKod, tam(r, "secmen", bozuk),
                tam(r, "oyKullanan", bozuk), tam(r, "gecerliOy", bozuk), tam(r, "gecersizOy", bozuk),
                tam(r, "sandik", bozuk), ondalikSinirli(r, "katilim", bozuk), kazanan, aday, sadeceKazanan, kaynak,
                kontrol, null, oy);
        String okunamayan = okunamayanNotu(bozuk);
        if (okunamayan != null || not != null) {
            String n = not == null ? okunamayan : okunamayan == null ? not : not + " | " + okunamayan;
            b = new BeldeKaydi(b.secimId(), b.plaka(), b.ilceId(), b.ilceAd(), b.beldeAd(), b.beldeKod(), b.secmen(),
                    b.oyKullanan(), b.gecerliOy(), b.gecersizOy(), b.sandik(), b.katilim(), b.kazanan(), b.aday(),
                    b.sadeceKazanan(), b.kaynak(), b.kontrol(), n, b.oy());
        }
        return b;
    }

    // ---------------------------------------------------------------------------------------------------------
    private static KaynakSecim secim(String sid, int yil, SecimTuru tur, OylamaTuru oylama, String ana,
                                     String aciklama, String tarih, List<SonucSatiri> iller,
                                     List<SonucSatiri> ilceler) {
        SecimDosyasi d = new SecimDosyasi(tarih, tur.kod(), aciklama, null, null, null, null, iller, ilceler, null);
        return new KaynakSecim(sid, yil, tur, oylama, ana, aciklama, d, null, null);
    }

    private static SecilenKaydi secilen(String sid, JsonNode k, String gorev) {
        return new SecilenKaydi(sid, k.path("plaka").asInt(), gorev, metin(k, "ad"), metin(k, "parti"),
                metin(k, "partiAdiKaynakta"), metin(k, "bolge"), metin(k, "kisiLink"));
    }

    private static KapsamKaydi kapsam(String sid, String veri, JsonNode k) {
        return new KapsamKaydi(sid, veri, tamOrNull(k.get("bulunan")), tamOrNull(k.get("beklenen")), metin(k, "durum"),
                metin(k, "not"));
    }

    /** Seçenek oyları: {"CHP": 12} ya da {"CHP": {"oy": 12, "oran": ...}}. INT'e sığmayan değer boş bırakılır. */
    private static Map<String, OyKaydi> oylar(JsonNode oy, List<String> bozuk) {
        Map<String, OyKaydi> m = new LinkedHashMap<>();
        oy.fields().forEachRemaining(e -> {
            JsonNode v = e.getValue();
            JsonNode sayi = v.isObject() ? v.get("oy") : v;
            BigDecimal oran = v.isObject() && v.hasNonNull("oran") ? v.get("oran").decimalValue() : null;
            Long o = sayi != null && sayi.isNumber() ? sayi.asLong() : null;
            if (o != null && Math.abs(o) > Integer.MAX_VALUE) {
                bozuk.add(e.getKey());
                o = null;
            }
            m.put(e.getKey(), new OyKaydi(o, oran, null));
        });
        return m;
    }

    private static String enCok(Map<String, OyKaydi> oy) {
        return oy.entrySet().stream()
                .filter(e -> e.getValue().oy() != null && e.getValue().oy() > 0)
                .max(Comparator.comparingLong((Map.Entry<String, OyKaydi> e) -> e.getValue().oy())
                        .thenComparing(Map.Entry::getKey))
                .map(Map.Entry::getKey).orElse(null);
    }

    private static Integer tam(JsonNode r, String alan, List<String> bozuk) {
        JsonNode v = r.get(alan);
        if (v == null || !v.isNumber()) {
            return null;
        }
        long l = v.asLong();
        if (Math.abs(l) > Integer.MAX_VALUE) {
            bozuk.add(alan);
            return null;
        }
        return (int) l;
    }

    private static Integer tamOrNull(JsonNode v) {
        return v == null || !v.isNumber() ? null : v.asInt();
    }

    private static Long uzun(JsonNode r, String alan) {
        JsonNode v = r.get(alan);
        return v == null || !v.isNumber() ? null : v.asLong();
    }

    private static BigDecimal ondalik(JsonNode r, String alan) {
        JsonNode v = r.get(alan);
        return v == null || !v.isNumber() ? null : v.decimalValue();
    }

    /** Belde katılımı DECIMAL(8,2); taranmış kitapta okunamayıp büyüyen değer boş bırakılır. */
    private static BigDecimal ondalikSinirli(JsonNode r, String alan, List<String> bozuk) {
        BigDecimal d = ondalik(r, alan);
        if (d != null && d.abs().compareTo(BigDecimal.valueOf(999_999)) > 0) {
            bozuk.add(alan);
            return null;
        }
        return d;
    }

    private static String okunamayanNotu(List<String> bozuk) {
        return bozuk.isEmpty() ? null : "Okunamayan değer boş bırakıldı: " + String.join(", ", bozuk);
    }

    private static List<String> iterasyonSirasi(JsonNode dizi) {
        List<String> l = new ArrayList<>();
        dizi.forEach(a -> l.add(a.asText()));
        return l;
    }

    static String metin(JsonNode r, String alan) {
        JsonNode v = r == null ? null : r.get(alan);
        return v == null || v.isNull() ? null : v.asText();
    }

    private static int yil(String sid) {
        Matcher m = YIL.matcher(sid);
        if (!m.find()) {
            throw new IllegalStateException("Seçim anahtarı yılla başlamıyor: " + sid);
        }
        return Integer.parseInt(m.group(1));
    }

    private static String ad(Path p) {
        return p.getFileName().toString().replaceFirst("\\.json$", "");
    }

    private List<Path> dosyalar(String klasor) {
        Path d = normalize.resolve(klasor);
        if (!Files.isDirectory(d)) {
            return List.of();
        }
        try (Stream<Path> s = Files.list(d)) {
            return s.filter(p -> p.getFileName().toString().endsWith(".json")).sorted().toList();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private JsonNode oku(Path p) {
        try {
            return json.readTree(p.toFile());
        } catch (IOException e) {
            throw new UncheckedIOException("Okunamadı: " + p, e);
        }
    }
}
