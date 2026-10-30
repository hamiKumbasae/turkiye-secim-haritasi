package tr.secimharitasi.api;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tr.secimharitasi.api.servis.KayitBulunamadiException;
import tr.secimharitasi.api.servis.PartiServisi;
import tr.secimharitasi.api.servis.SecimServisi;
import tr.secimharitasi.api.web.PartiKontrolcusu;
import tr.secimharitasi.api.web.SecimKontrolcusu;
import tr.secimharitasi.api.web.YerKontrolcusu;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.common.dto.SecimDto;

/** Web katmanı: yönlendirme, parametreler, hata yanıtları (servisler sahte, veritabanı yok). */
@WebMvcTest({SecimKontrolcusu.class, YerKontrolcusu.class, PartiKontrolcusu.class})
class KontrolcuTest {

    @Autowired
    MockMvc mvc;
    @MockitoBean
    SecimServisi secimServisi;
    @MockitoBean
    PartiServisi partiServisi;

    @Test
    void secimListesiJson() throws Exception {
        when(secimServisi.secimler("genel", null, null, null))
                .thenReturn(List.of(new SecimDto("2023", SecimTuru.GENEL, 2023, "14 Mayıs 2023", 600, "YSK", "official")));
        mvc.perform(get("/api/secimler").param("tur", "genel")).andExpect(status().isOk())
                .andExpect(jsonPath("$[0].secimId").value("2023"))
                .andExpect(jsonPath("$[0].tur").value("genel"))
                .andExpect(jsonPath("$[0].toplamSandalye").value(600));
    }

    @Test
    void bulunamayanKayit404() throws Exception {
        when(secimServisi.il("2023", 99)).thenThrow(new KayitBulunamadiException("2023 seçiminde 99 plakalı il yok"));
        mvc.perform(get("/api/secimler/2023/iller/99")).andExpect(status().isNotFound())
                .andExpect(jsonPath("$.durum").value(404))
                .andExpect(jsonPath("$.mesaj").value("2023 seçiminde 99 plakalı il yok"));
    }

    @Test
    void gecersizParametre400() throws Exception {
        when(secimServisi.secimler(eq("senato"), any(), any(), any()))
                .thenThrow(new IllegalArgumentException("Bilinmeyen seçim türü: senato"));
        mvc.perform(get("/api/secimler").param("tur", "senato")).andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.mesaj").value("Bilinmeyen seçim türü: senato"));
        mvc.perform(get("/api/secimler/2023/iller/abc")).andExpect(status().isBadRequest());
    }

    @Test
    void yalnizGet() throws Exception {
        mvc.perform(post("/api/secimler")).andExpect(status().isMethodNotAllowed());
        mvc.perform(post("/api/partiler/2")).andExpect(status().isMethodNotAllowed());
    }

    @Test
    void tekYilAraligaCevrilir() throws Exception {
        when(partiServisi.sonuclar(anyInt(), any(), any(), any(), any(), anyBoolean())).thenReturn(List.of());
        mvc.perform(get("/api/partiler/2/sonuclar").param("yil", "2023").param("zincir", "true"))
                .andExpect(status().isOk());
        verify(partiServisi).sonuclar(2, null, 2023, 2023, null, true);
    }
}
