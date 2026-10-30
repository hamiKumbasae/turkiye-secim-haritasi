package tr.secimharitasi.chatbot;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.forwardedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tr.secimharitasi.chatbot.model.ModelHatasi;
import tr.secimharitasi.chatbot.sohbet.SohbetServisi;
import tr.secimharitasi.chatbot.sohbet.SohbetYaniti;
import tr.secimharitasi.chatbot.web.HizSiniri;
import tr.secimharitasi.chatbot.web.SohbetKontrolcusu;

@WebMvcTest(SohbetKontrolcusu.class)
class SohbetKontrolcusuTest {

    @Autowired
    MockMvc mvc;
    @MockitoBean
    SohbetServisi servis;
    @MockitoBean
    HizSiniri hizSiniri;
    @MockitoBean
    SohbetOzellikleri ozellikler;

    @BeforeEach
    void kur() {
        when(ozellikler.anahtarVar()).thenReturn(true);
        when(ozellikler.azamiSoruUzunlugu()).thenReturn(500);
        when(hizSiniri.izinVer(anyString())).thenReturn(true);
    }

    @Test
    void soruCevaplanir() throws Exception {
        when(servis.sor("2023'te Ankara?")).thenReturn(new SohbetYaniti("CHP birinci.",
                List.of(new SohbetYaniti.Kaynak("il_sonuclari", null, "/api/secimler/2023/iller/6", null)),
                "https://harita/#secim=2023", 2, 1234));
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"soru\":\"  2023'te Ankara?  \"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.cevap").value("CHP birinci."))
                .andExpect(jsonPath("$.kaynaklar[0].sorgu").value("/api/secimler/2023/iller/6"))
                .andExpect(jsonPath("$.haritaBaglantisi").value("https://harita/#secim=2023"))
                .andExpect(jsonPath("$.adim").value(2));
    }

    @Test
    void bosVeUzunSoru400() throws Exception {
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON).content("{\"soru\":\"   \"}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.durum").value(400));
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"soru\":\"" + "a".repeat(501) + "\"}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.mesaj").value("Soru en çok 500 karakter olabilir."));
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON).content("bozuk"))
                .andExpect(status().isBadRequest());
        verify(servis, never()).sor(anyString());
    }

    @Test
    void anahtarYoksa503() throws Exception {
        when(ozellikler.anahtarVar()).thenReturn(false);
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON).content("{\"soru\":\"x\"}"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.mesaj").value("Sohbet servisi yapılandırılmamış: ANTHROPIC_API_KEY tanımlı değil."));
    }

    @Test
    void hizSiniri429VeSonXffKullanilir() throws Exception {
        when(hizSiniri.izinVer("10.0.0.9")).thenReturn(false);
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON).content("{\"soru\":\"x\"}")
                        .header("X-Forwarded-For", "1.2.3.4, 10.0.0.9"))
                .andExpect(status().isTooManyRequests());
        verify(servis, never()).sor(anyString());
    }

    @Test
    void modelHatasi502() throws Exception {
        when(servis.sor("x")).thenThrow(new ModelHatasi("HTTP 529", null));
        mvc.perform(post("/api/sohbet").contentType(MediaType.APPLICATION_JSON).content("{\"soru\":\"x\"}"))
                .andExpect(status().isBadGateway()).andExpect(jsonPath("$.durum").value(502));
    }

    @Test
    void sayfaYonlendirmesi() throws Exception {
        mvc.perform(get("/sohbet")).andExpect(status().isOk()).andExpect(forwardedUrl("/sohbet.html"));
    }
}
