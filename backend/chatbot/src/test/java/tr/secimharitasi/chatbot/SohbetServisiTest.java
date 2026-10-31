package tr.secimharitasi.chatbot;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.chatbot.arac.Arac;
import tr.secimharitasi.chatbot.arac.AracHatasi;
import tr.secimharitasi.chatbot.arac.AracKutusu;
import tr.secimharitasi.chatbot.arac.AracSonucu;
import tr.secimharitasi.chatbot.model.ModelIstemcisi;
import tr.secimharitasi.chatbot.model.ModelYaniti;
import tr.secimharitasi.chatbot.sohbet.SohbetServisi;
import tr.secimharitasi.chatbot.sohbet.SohbetYaniti;

/** Ajan döngüsü senaryolu sahte bir modelle: gerçek model çağrılmaz. */
class SohbetServisiTest {

    final ObjectMapper json = new ObjectMapper();

    /** Sırayla hazır yanıtlar döner ve her çağrıda gönderilen mesajları kaydeder. */
    class SahteModel implements ModelIstemcisi {
        final Deque<ModelYaniti> yanitlar = new ArrayDeque<>();
        final List<List<JsonNode>> gonderilenler = new ArrayList<>();
        String sonSistem;
        List<JsonNode> sonAraclar;

        @Override
        public ModelYaniti gonder(String sistem, List<JsonNode> mesajlar, List<JsonNode> araclar) {
            sonSistem = sistem;
            sonAraclar = araclar;
            gonderilenler.add(List.copyOf(mesajlar));
            return yanitlar.removeFirst();
        }
    }

    ModelYaniti metin(String t) {
        ObjectNode b = json.createObjectNode().put("type", "text").put("text", t);
        return new ModelYaniti("end_turn", List.of(b), 100, 20);
    }

    ModelYaniti arac(String id, String ad, String girdi) throws Exception {
        ObjectNode b = json.createObjectNode().put("type", "tool_use").put("id", id).put("name", ad);
        b.set("input", json.readTree(girdi));
        ObjectNode once = json.createObjectNode().put("type", "text").put("text", "Bakıyorum.");
        return new ModelYaniti("tool_use", List.of(once, b), 100, 20);
    }

    AracKutusu kutu() {
        Arac il = new Arac("il_sonuclari", "il", json.createObjectNode().put("type", "object"), g -> {
            if (g.path("plaka").asInt() == 99) {
                throw new AracHatasi("2023 seçiminde 99 plakalı il yok");
            }
            ObjectNode v = json.createObjectNode().put("ad", "Ankara").put("kazanan", "CHP");
            return new AracSonucu(v, "/api/secimler/2023/iller/6", null);
        });
        Arac harita = new Arac("harita_baglantisi", "harita", json.createObjectNode().put("type", "object"),
                g -> new AracSonucu(json.createObjectNode().put("baglanti", "olusturuldu"), null,
                        "https://harita/#secim=2023&il=6"));
        Arac buyuk = new Arac("buyuk", "buyuk", json.createObjectNode().put("type", "object"),
                g -> new AracSonucu(json.getNodeFactory().textNode("x".repeat(40_000)), "/api/buyuk", null));
        return new AracKutusu(List.of(il, harita, buyuk), json);
    }

    @Test
    void aracCagirirSonraCevaplar() throws Exception {
        SahteModel model = new SahteModel();
        model.yanitlar.add(arac("t1", "il_sonuclari", "{\"secim_id\":\"2023\",\"plaka\":6}"));
        model.yanitlar.add(arac("t2", "harita_baglantisi", "{\"secim_id\":\"2023\",\"plaka\":6}"));
        model.yanitlar.add(metin("2023'te Ankara'da birinci **CHP**."));

        SohbetYaniti y = new SohbetServisi(model, kutu(), json, 8).sor("2023'te Ankara'da kim birinci?");

        assertThat(y.cevap()).isEqualTo("2023'te Ankara'da birinci **CHP**.");
        assertThat(y.adim()).isEqualTo(3);
        assertThat(y.haritaBaglantisi()).isEqualTo("https://harita/#secim=2023&il=6");
        assertThat(y.kaynaklar()).hasSize(1);
        assertThat(y.kaynaklar().get(0).sorgu()).isEqualTo("/api/secimler/2023/iller/6");
        assertThat(y.kaynaklar().get(0).arac()).isEqualTo("il_sonuclari");

        // ikinci çağrıda: kullanıcı sorusu, asistanın tool_use'u, tool_result
        List<JsonNode> ikinci = model.gonderilenler.get(1);
        assertThat(ikinci).hasSize(3);
        assertThat(ikinci.get(0).path("content").asText()).isEqualTo("2023'te Ankara'da kim birinci?");
        assertThat(ikinci.get(1).path("role").asText()).isEqualTo("assistant");
        assertThat(ikinci.get(1).path("content").get(1).path("type").asText()).isEqualTo("tool_use");
        JsonNode sonuc = ikinci.get(2).path("content").get(0);
        assertThat(ikinci.get(2).path("role").asText()).isEqualTo("user");
        assertThat(sonuc.path("type").asText()).isEqualTo("tool_result");
        assertThat(sonuc.path("tool_use_id").asText()).isEqualTo("t1");
        assertThat(sonuc.path("content").asText()).contains("\"kazanan\":\"CHP\"");
        assertThat(sonuc.has("is_error")).isFalse();

        assertThat(model.sonAraclar).hasSize(3);
        assertThat(model.sonSistem).contains("tarafsızlık").contains("Bellekten sayı yazma");
    }

    @Test
    void aracHatasiModeleHataOlarakDoner() throws Exception {
        SahteModel model = new SahteModel();
        model.yanitlar.add(arac("t1", "il_sonuclari", "{\"secim_id\":\"2023\",\"plaka\":99}"));
        model.yanitlar.add(metin("Bu il veride yok."));

        SohbetYaniti y = new SohbetServisi(model, kutu(), json, 8).sor("2023'te 99 plaka?");

        JsonNode sonuc = model.gonderilenler.get(1).get(2).path("content").get(0);
        assertThat(sonuc.path("is_error").asBoolean()).isTrue();
        assertThat(sonuc.path("content").asText()).isEqualTo("2023 seçiminde 99 plakalı il yok");
        assertThat(y.kaynaklar().get(0).hata()).isEqualTo("2023 seçiminde 99 plakalı il yok");
        assertThat(y.cevap()).isEqualTo("Bu il veride yok.");
    }

    @Test
    void olmayanAracHataOlurDonguSurer() throws Exception {
        SahteModel model = new SahteModel();
        model.yanitlar.add(arac("t1", "uydurma", "{}"));
        model.yanitlar.add(metin("Tamam."));
        SohbetYaniti y = new SohbetServisi(model, kutu(), json, 8).sor("soru");
        assertThat(y.cevap()).isEqualTo("Tamam.");
        assertThat(model.gonderilenler.get(1).get(2).path("content").get(0).path("is_error").asBoolean()).isTrue();
    }

    @Test
    void buyukSonucKirpilir() throws Exception {
        SahteModel model = new SahteModel();
        model.yanitlar.add(arac("t1", "buyuk", "{}"));
        model.yanitlar.add(metin("Tamam."));
        new SohbetServisi(model, kutu(), json, 8).sor("soru");
        String icerik = model.gonderilenler.get(1).get(2).path("content").get(0).path("content").asText();
        assertThat(icerik.length()).isLessThan(15_200);
        assertThat(icerik).contains("sonuç kırpıldı");
    }

    @Test
    void adimSiniriAsilinca() throws Exception {
        SahteModel model = new SahteModel();
        for (int i = 0; i < 3; i++) {
            model.yanitlar.add(arac("t" + i, "il_sonuclari", "{\"secim_id\":\"2023\",\"plaka\":6}"));
        }
        SohbetYaniti y = new SohbetServisi(model, kutu(), json, 3).sor("soru");
        assertThat(y.cevap()).contains("çok fazla veri sorgusu");
        assertThat(y.adim()).isEqualTo(3);
        assertThat(model.gonderilenler).hasSize(3);
        assertThat(y.kaynaklar()).hasSize(3);
    }

    @Test
    void uzunlukSiniriNotu() {
        SahteModel model = new SahteModel();
        ObjectNode b = json.createObjectNode().put("type", "text").put("text", "Yarım");
        model.yanitlar.add(new ModelYaniti("max_tokens", List.of(b), 1, 1));
        SohbetYaniti y = new SohbetServisi(model, kutu(), json, 8).sor("soru");
        assertThat(y.cevap()).startsWith("Yarım").contains("yarıda kesildi");
    }

    @Test
    void reddetmeAracsizCevaptir() {
        SahteModel model = new SahteModel();
        model.yanitlar.add(metin("Partiler hakkında görüş bildiremem. İsterseniz 2023 sonuçlarını gösterebilirim."));
        SohbetYaniti y = new SohbetServisi(model, kutu(), json, 8).sor("Hangi parti daha iyi?");
        assertThat(y.kaynaklar()).isEmpty();
        assertThat(y.haritaBaglantisi()).isNull();
        assertThat(y.adim()).isEqualTo(1);
    }
}
