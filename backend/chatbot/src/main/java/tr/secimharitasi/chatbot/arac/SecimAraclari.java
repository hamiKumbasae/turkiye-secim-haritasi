package tr.secimharitasi.chatbot.arac;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.net.URI;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.util.UriComponentsBuilder;
import tr.secimharitasi.common.Metin;

/**
 * Modelin kullandığı araçlar. Her biri election-api'yi çağırır ve yanıtı modele uygun boyuta kırpar; hiçbir araç
 * sayı üretmez ya da hesaplamaz (sıralama ve süzme dışında).
 */
public final class SecimAraclari {

    /** Mahalle listesinde modele en çok kaç satır gider. */
    static final int AZAMI_MAHALLE = 40;

    private final RestClient api;
    private final String kok;
    private final ObjectMapper json;
    private final String haritaKoku;

    public SecimAraclari(RestClient.Builder builder, String electionApiUrl, ObjectMapper json, String haritaKoku) {
        this.api = builder.build();
        this.kok = electionApiUrl.endsWith("/") ? electionApiUrl.substring(0, electionApiUrl.length() - 1)
                : electionApiUrl;
        this.json = json;
        this.haritaKoku = haritaKoku;
    }

    public AracKutusu kutu() {
        return new AracKutusu(List.of(
                secimleriListele(), yerAra(), partiAra(), ilSonuclari(), ilceSonuclari(), ilceSonucu(),
                mahalleSonuclari(), partiSonuclari(), enGucluIller(), secilenler(), beldeler(), sandalyeler(),
                haritaBaglantisi()), json);
    }

    // ---------------------------------------------------------------------------------------------------------
    private Arac secimleriListele() {
        return new Arac("secimleri_listele",
                "Seçimleri ve oylamaları listeler (kimlik, tür, oylama, yıl, tarih). Seçim kimliğini bilmiyorsan önce "
                        + "bunu kullan. Kimlik örnekleri: genel '2023', '2015Haziran', '2015Kasim'; yerel belediye "
                        + "başkanlığı '2024yerel'; belediye meclisi '2024yerel_bm'; il genel meclisi '2024yerel_igm'; "
                        + "referandum '2017referandum'; cumhurbaşkanlığı '2023cb1tur', '2023cb2tur'; Senato '1961senato'; "
                        + "ara/yenileme '2019istanbul_bb_yenileme'.",
                sema(Map.of(
                        "tur", ozellik("string", "genel, yerel, referandum, cumhurbaskanligi, senato, ara"),
                        "oylama", ozellik("string", "milletvekili, baskanlik, belediye_meclisi, il_genel_meclisi, "
                                + "referandum, cumhurbaskanligi, senato"),
                        "yil", ozellik("integer", "tek yıl"),
                        "yil_baslangic", ozellik("integer", "aralık başı"),
                        "yil_bitis", ozellik("integer", "aralık sonu")), List.of()),
                g -> {
                    String yol = yol("/api/secimler", "tur", m(g, "tur"), "oylama", m(g, "oylama"), "yil", s(g, "yil"),
                            "yilBaslangic", s(g, "yil_baslangic"), "yilBitis", s(g, "yil_bitis"));
                    ArrayNode l = json.createArrayNode();
                    getir(yol).forEach(x -> l.add(sec(x, "secimId", "tur", "oylama", "anaSecimId", "yil", "tarih")));
                    return new AracSonucu(l, yol, null);
                });
    }

    private Arac yerAra() {
        return new Arac("yer_ara",
                "İl ya da ilçe adını kimliğe çevirir (il: plaka; ilçe: ilce_id, ör. 'TR-D-34-037'). Türkçe harf ve "
                        + "büyük/küçük farkı önemsizdir. Aynı adla birden çok ilçe birimi dönebilir (farklı illerde ya da "
                        + "tarihsel birimler, baslangicYili/bitisYili ile); yil verirsen o yıl veride olan birimler döner.",
                sema(Map.of("ad", ozellik("string", "il ya da ilçe adı"),
                        "yil", ozellik("integer", "seçim yılı (isteğe bağlı)")), List.of("ad")),
                g -> {
                    String yol = yol("/api/iller/ara", "ad", m(g, "ad"), "yil", s(g, "yil"));
                    return new AracSonucu(getir(yol), yol, null);
                });
    }

    private Arac partiAra() {
        return new Arac("parti_ara",
                "Parti, aday ya da seçenek adını kimliğe (parti_id) çevirir. Kısaltma da olur ('AKP', 'CHP', 'DEM'). "
                        + "Dönen 'ad' veri anahtarıdır (ör. 'AK Parti', 'YEŞİL SOL'); oncekiPartiId partinin öncülüdür.",
                sema(Map.of("ad", ozellik("string", "parti adı ya da kısaltması")), List.of("ad")),
                g -> {
                    String aranan = Metin.katla(m(g, "ad"));
                    if (aranan.isEmpty()) {
                        throw new AracHatasi("Parti adı boş");
                    }
                    ArrayNode tam = json.createArrayNode();
                    ArrayNode kismi = json.createArrayNode();
                    for (JsonNode p : getir("/api/partiler")) {
                        String ad = Metin.katla(p.path("ad").asText());
                        String kisa = Metin.katla(p.path("kisa").asText());
                        JsonNode ozet = sec(p, "partiId", "ad", "kisa", "tip", "oncekiPartiId", "gecisTuru", "gecisYili");
                        if (ad.equals(aranan) || kisa.equals(aranan)) {
                            tam.add(ozet);
                        } else if (ad.contains(aranan) || kisa.contains(aranan)) {
                            kismi.add(ozet);
                        }
                    }
                    return new AracSonucu(tam.isEmpty() ? kismi : tam, "/api/partiler", null);
                });
    }

    private Arac ilSonuclari() {
        return new Arac("il_sonuclari",
                "Bir seçimde il sonuçları. plaka verilirse o ilin bütün oyları; verilmezse bütün iller (her il için "
                        + "kazanan, katılım, geçerli oy ve ilk 3 seçenek). Plaka 0 = yurt dışı.",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "plaka", ozellik("integer", "il plakası (isteğe bağlı)")), List.of("secim_id")),
                g -> {
                    String sid = zorunlu(g, "secim_id");
                    if (g.hasNonNull("plaka")) {
                        String yol = "/api/secimler/" + sid + "/iller/" + g.get("plaka").asInt();
                        return new AracSonucu(sonuc(getir(yol), 15), yol, null);
                    }
                    String yol = "/api/secimler/" + sid + "/iller";
                    ArrayNode l = json.createArrayNode();
                    getir(yol).forEach(il -> l.add(sonuc(il, 3)));
                    return new AracSonucu(l, yol, null);
                });
    }

    private Arac ilceSonuclari() {
        return new Arac("ilce_sonuclari",
                "Bir seçimde bir ilin bütün ilçelerinin sonuçları (her ilçe için kazanan, katılım ve ilk 5 seçenek).",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "plaka", ozellik("integer", "il plakası")), List.of("secim_id", "plaka")),
                g -> {
                    String yol = "/api/secimler/" + zorunlu(g, "secim_id") + "/iller/" + zorunluSayi(g, "plaka") + "/ilceler";
                    ArrayNode l = json.createArrayNode();
                    getir(yol).forEach(i -> l.add(sonuc(i, 5)));
                    return new AracSonucu(l, yol, null);
                });
    }

    private Arac ilceSonucu() {
        return new Arac("ilce_sonucu", "Bir seçimde tek bir ilçenin bütün sonucu.",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "ilce_id", ozellik("string", "ilçe kimliği (yer_ara ile)")), List.of("secim_id", "ilce_id")),
                g -> {
                    String yol = "/api/secimler/" + zorunlu(g, "secim_id") + "/ilceler/" + zorunlu(g, "ilce_id");
                    return new AracSonucu(sonuc(getir(yol), 20), yol, null);
                });
    }

    private Arac mahalleSonuclari() {
        return new Arac("mahalle_sonuclari",
                "Bir ilçenin mahalle/köy sonuçları (yalnız 2009-2024 seçimleri). parti verilirse mahalleler o "
                        + "partinin oranına göre büyükten küçüğe sıralanır; verilmezse seçmen sayısına göre. En çok "
                        + AZAMI_MAHALLE + " mahalle döner; toplam sayı 'mahalleSayisi' alanında.",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "ilce_id", ozellik("string", "ilçe kimliği"),
                        "parti", ozellik("string", "sıralama için parti adı (veri anahtarı, ör. 'CHP')")),
                        List.of("secim_id", "ilce_id")),
                g -> {
                    String yol = "/api/secimler/" + zorunlu(g, "secim_id") + "/ilceler/" + zorunlu(g, "ilce_id")
                            + "/mahalleler";
                    List<JsonNode> mahalleler = new ArrayList<>();
                    getir(yol).forEach(mahalleler::add);
                    String parti = m(g, "parti");
                    if (parti != null) {
                        mahalleler.sort(Comparator.comparingDouble((JsonNode x) -> -oran(x, parti)));
                    }
                    ObjectNode o = json.createObjectNode();
                    o.put("mahalleSayisi", mahalleler.size());
                    ArrayNode l = o.putArray("mahalleler");
                    mahalleler.stream().limit(AZAMI_MAHALLE).forEach(x -> l.add(sonuc(x, 4)));
                    return new AracSonucu(o, yol, null);
                });
    }

    private Arac partiSonuclari() {
        return new Arac("parti_sonuclari",
                "Bir partinin seçimlere göre sonuçları: plaka verilirse o ilde, verilmezse Türkiye geneli (il "
                        + "satırlarının toplamı, yurt dışı hariç). Varsayılan yalnız ana seçimler; meclis için "
                        + "oylama='belediye_meclisi'. zincir=true öncül partilerin (ör. DEM Parti için YEŞİL SOL) "
                        + "sonuçlarını da ekler.",
                sema(Map.of("parti_id", ozellik("integer", "parti_ara ile"),
                        "tur", ozellik("string", "genel, yerel, referandum, cumhurbaskanligi, senato, ara"),
                        "oylama", ozellik("string", "örn. belediye_meclisi"),
                        "yil_baslangic", ozellik("integer", "aralık başı"),
                        "yil_bitis", ozellik("integer", "aralık sonu"),
                        "plaka", ozellik("integer", "il plakası"),
                        "zincir", ozellik("boolean", "öncül partileri ekle")), List.of("parti_id")),
                g -> {
                    String yol = yol("/api/partiler/" + zorunluSayi(g, "parti_id") + "/sonuclar", "tur", m(g, "tur"),
                            "oylama", m(g, "oylama"), "yilBaslangic", s(g, "yil_baslangic"),
                            "yilBitis", s(g, "yil_bitis"), "plaka", s(g, "plaka"), "zincir", s(g, "zincir"));
                    return new AracSonucu(getir(yol), yol, null);
                });
    }

    private Arac enGucluIller() {
        return new Arac("en_guclu_iller", "Bir seçimde partinin en yüksek oranı aldığı iller (yurt dışı hariç).",
                sema(Map.of("parti_id", ozellik("integer", "parti_ara ile"),
                        "secim_id", ozellik("string", "seçim kimliği"),
                        "limit", ozellik("integer", "kaç il (varsayılan 10, en çok 81)")), List.of("parti_id", "secim_id")),
                g -> {
                    String yol = yol("/api/partiler/" + zorunluSayi(g, "parti_id") + "/secimler/" + zorunlu(g, "secim_id")
                            + "/en-guclu-iller", "limit", s(g, "limit"));
                    return new AracSonucu(getir(yol), yol, null);
                });
    }

    private Arac secilenler() {
        return new Arac("secilenler",
                "Bir seçimde seçilen milletvekilleri ya da senatörler (Vikipedi kaynaklı; liste eksik olabilir, "
                        + "'kapsam' kaç kişinin bulunduğunu gösterir).",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "plaka", ozellik("integer", "il plakası (isteğe bağlı)")), List.of("secim_id")),
                g -> {
                    String sid = zorunlu(g, "secim_id");
                    String yol = yol("/api/secimler/" + sid + "/secilenler", "plaka", s(g, "plaka"));
                    ObjectNode o = json.createObjectNode();
                    o.set("kapsam", getir("/api/secimler/" + sid + "/kapsam"));
                    o.set("secilenler", getir(yol));
                    return new AracSonucu(o, yol, null);
                });
    }

    private Arac beldeler() {
        return new Arac("beldeler",
                "Bir yerel seçimde belde belediyeleri (başkanlık: 'NNNNyerel', meclis: 'NNNNyerel_bm'). 'kaynak' "
                        + "wikipedia ise yalnız kazanan bilinir; 'kontrol' taranmış kitap satırının doğrulama sonucudur.",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "plaka", ozellik("integer", "il plakası"),
                        "ilce_id", ozellik("string", "ilçe kimliği")), List.of("secim_id")),
                g -> {
                    String yol = yol("/api/secimler/" + zorunlu(g, "secim_id") + "/beldeler", "plaka", s(g, "plaka"),
                            "ilceId", m(g, "ilce_id"));
                    ArrayNode l = json.createArrayNode();
                    JsonNode t = getir(yol);
                    for (int i = 0; i < Math.min(t.size(), 60); i++) {
                        l.add(sonuc(t.get(i), 4));
                    }
                    ObjectNode o = json.createObjectNode();
                    o.put("beldeSayisi", t.size());
                    o.set("beldeler", l);
                    return new AracSonucu(o, yol, null);
                });
    }

    private Arac sandalyeler() {
        return new Arac("sandalyeler",
                "Parti başına sandalye: genel seçimde il başına milletvekili; '2024yerel_bm' için ilçe belediye "
                        + "meclisi üyeleri.",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "plaka", ozellik("integer", "il plakası"),
                        "ilce_id", ozellik("string", "ilçe kimliği")), List.of("secim_id")),
                g -> {
                    String yol = yol("/api/secimler/" + zorunlu(g, "secim_id") + "/sandalyeler", "plaka", s(g, "plaka"),
                            "ilceId", m(g, "ilce_id"));
                    return new AracSonucu(getir(yol), yol, null);
                });
    }

    private Arac haritaBaglantisi() {
        return new Arac("harita_baglantisi",
                "Cevabın sonunda kullanıcıya haritada ilgili görünümü açan bağlantı üretir (bağlantıyı metne yazma, "
                        + "sistem gösterir). mod: 'parti' (bir partinin oranı), 'katilim', 'degisim'; boşsa kazanan "
                        + "haritası. Senato ve ara seçimler haritada yok.",
                sema(Map.of("secim_id", ozellik("string", "seçim kimliği"),
                        "plaka", ozellik("integer", "il plakası"),
                        "ilce_id", ozellik("string", "ilçe kimliği (plaka ile)"),
                        "mod", ozellik("string", "parti, katilim, degisim"),
                        "parti", ozellik("string", "parti adı (veri anahtarı, mod=parti için)")), List.of("secim_id")),
                g -> {
                    String b = HaritaBaglantisi.olustur(haritaKoku, zorunlu(g, "secim_id"),
                            g.hasNonNull("plaka") ? g.get("plaka").asInt() : null, m(g, "ilce_id"), m(g, "parti"),
                            m(g, "mod"));
                    ObjectNode o = json.createObjectNode();
                    if (b == null) {
                        o.put("not", "Bu seçim haritada yok (Senato ve ara seçimler haritada gösterilmiyor).");
                    } else {
                        o.put("baglanti", "olusturuldu");
                    }
                    return new AracSonucu(o, null, b);
                });
    }

    // ---------------------------------------------------------------------------------------------------------
    private JsonNode getir(String yol) {
        try {
            // yol zaten kodlanmış: URI olarak verilir ki RestClient ikinci kez kodlamasın
            JsonNode n = api.get().uri(URI.create(kok + yol)).retrieve().body(JsonNode.class);
            return n == null ? json.createArrayNode() : n;
        } catch (RestClientResponseException e) {
            String mesaj = e.getStatusCode().value() + " " + e.getStatusText();
            try {
                JsonNode h = json.readTree(e.getResponseBodyAsString());
                if (h.hasNonNull("mesaj")) {
                    mesaj = h.get("mesaj").asText();
                }
            } catch (Exception yoksay) {
                // gövde JSON değil
            }
            throw new AracHatasi(mesaj);
        } catch (RestClientException e) {
            throw new AracHatasi("Veri servisine ulaşılamadı");
        }
    }

    /** Sonuç satırını kırpar: oylar ilk n seçenekle sınırlanır (sıralı gelir), oran/oy korunur. */
    private JsonNode sonuc(JsonNode r, int n) {
        ObjectNode o = r.deepCopy();
        JsonNode oylar = r.get("oylar");
        if (oylar != null && oylar.isArray()) {
            ArrayNode k = json.createArrayNode();
            for (int i = 0; i < Math.min(n, oylar.size()); i++) {
                k.add(sec(oylar.get(i), "parti", "oy", "oran"));
            }
            o.set("oylar", k);
            if (oylar.size() > n) {
                o.put("digerSecenekSayisi", oylar.size() - n);
            }
        }
        o.remove(List.of("partiId", "kisa"));
        bosAlanlariAt(o);
        return o;
    }

    private static double oran(JsonNode mahalle, String parti) {
        String k = Metin.katla(parti);
        for (JsonNode o : mahalle.path("oylar")) {
            if (Metin.katla(o.path("parti").asText()).equals(k) && o.hasNonNull("oran")) {
                return o.get("oran").asDouble();
            }
        }
        return -1;
    }

    private ObjectNode sec(JsonNode r, String... alanlar) {
        ObjectNode o = json.createObjectNode();
        for (String a : alanlar) {
            if (r.hasNonNull(a)) {
                o.set(a, r.get(a));
            }
        }
        return o;
    }

    private static void bosAlanlariAt(ObjectNode o) {
        List<String> bos = new ArrayList<>();
        o.fields().forEachRemaining(e -> {
            if (e.getValue().isNull()) {
                bos.add(e.getKey());
            }
        });
        o.remove(bos);
    }

    private ObjectNode sema(Map<String, ObjectNode> ozellikler, List<String> zorunlu) {
        ObjectNode s = json.createObjectNode();
        s.put("type", "object");
        ObjectNode p = s.putObject("properties");
        new java.util.TreeMap<>(ozellikler).forEach(p::set);
        ArrayNode r = s.putArray("required");
        zorunlu.forEach(r::add);
        return s;
    }

    private ObjectNode ozellik(String tip, String aciklama) {
        ObjectNode o = json.createObjectNode();
        o.put("type", tip);
        o.put("description", aciklama);
        return o;
    }

    private static String yol(String yol, String... anahtarDeger) {
        UriComponentsBuilder b = UriComponentsBuilder.fromPath(yol);
        for (int i = 0; i < anahtarDeger.length; i += 2) {
            if (anahtarDeger[i + 1] != null && !anahtarDeger[i + 1].isBlank()) {
                b.queryParam(anahtarDeger[i], anahtarDeger[i + 1]);
            }
        }
        return b.encode().build().toUriString();
    }

    private static String m(JsonNode g, String alan) {
        return g.hasNonNull(alan) && !g.get(alan).asText().isBlank() ? g.get(alan).asText().trim() : null;
    }

    private static String s(JsonNode g, String alan) {
        return g.hasNonNull(alan) ? g.get(alan).asText() : null;
    }

    private static String zorunlu(JsonNode g, String alan) {
        String v = m(g, alan);
        if (v == null) {
            throw new AracHatasi("Eksik girdi: " + alan);
        }
        if (!v.matches("[A-Za-z0-9][A-Za-z0-9_.-]*")) {
            throw new AracHatasi("Geçersiz " + alan + ": " + v);
        }
        return v;
    }

    private static int zorunluSayi(JsonNode g, String alan) {
        if (!g.hasNonNull(alan) || !g.get(alan).canConvertToInt()) {
            throw new AracHatasi("Eksik ya da geçersiz sayı: " + alan);
        }
        return g.get(alan).asInt();
    }
}
