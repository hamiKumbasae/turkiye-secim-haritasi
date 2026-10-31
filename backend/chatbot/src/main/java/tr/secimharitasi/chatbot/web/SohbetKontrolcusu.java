package tr.secimharitasi.chatbot.web;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.http.converter.HttpMessageNotReadableException;
import tr.secimharitasi.chatbot.SohbetOzellikleri;
import tr.secimharitasi.chatbot.model.ModelHatasi;
import tr.secimharitasi.chatbot.sohbet.SohbetServisi;
import tr.secimharitasi.common.dto.HataDto;

@Controller
public class SohbetKontrolcusu {

    private static final Logger LOG = LoggerFactory.getLogger(SohbetKontrolcusu.class);

    private final SohbetServisi servis;
    private final HizSiniri hizSiniri;
    private final SohbetOzellikleri ozellikler;

    public SohbetKontrolcusu(SohbetServisi servis, HizSiniri hizSiniri, SohbetOzellikleri ozellikler) {
        this.servis = servis;
        this.hizSiniri = hizSiniri;
        this.ozellikler = ozellikler;
    }

    public record SohbetIstegi(String soru) {
    }

    @GetMapping({"/sohbet", "/sohbet/"})
    public String sayfa() {
        return "forward:/sohbet.html";
    }

    @PostMapping("/api/sohbet")
    @ResponseBody
    public ResponseEntity<?> sor(@RequestBody SohbetIstegi istek, HttpServletRequest http) {
        String soru = istek == null || istek.soru() == null ? "" : istek.soru().strip();
        if (soru.isEmpty()) {
            return hata(HttpStatus.BAD_REQUEST, "Soru boş olamaz.");
        }
        if (soru.length() > ozellikler.azamiSoruUzunlugu()) {
            return hata(HttpStatus.BAD_REQUEST, "Soru en çok " + ozellikler.azamiSoruUzunlugu() + " karakter olabilir.");
        }
        if (!ozellikler.anahtarVar()) {
            return hata(HttpStatus.SERVICE_UNAVAILABLE,
                    "Sohbet servisi yapılandırılmamış: ANTHROPIC_API_KEY tanımlı değil.");
        }
        if (!hizSiniri.izinVer(istemci(http))) {
            return hata(HttpStatus.TOO_MANY_REQUESTS, "Çok fazla soru gönderildi. Lütfen bir dakika sonra tekrar deneyin.");
        }
        return ResponseEntity.ok(servis.sor(soru));
    }

    @ExceptionHandler(ModelHatasi.class)
    @ResponseBody
    public ResponseEntity<HataDto> modelHatasi(ModelHatasi e) {
        LOG.error("Model hatası: {}", e.getMessage());
        return hata(HttpStatus.BAD_GATEWAY, "Dil modeli servisine şu an ulaşılamıyor. Lütfen biraz sonra tekrar deneyin.");
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    @ResponseBody
    public ResponseEntity<HataDto> okunamadi() {
        return hata(HttpStatus.BAD_REQUEST, "İstek gövdesi {\"soru\": \"...\"} biçiminde olmalı.");
    }

    /**
     * İstemci adresi: gateway X-Forwarded-For başlığının sonuna gerçek bağlantı adresini ekler; istemcinin
     * kendi yazdığı değerler başta kalır, bu yüzden son değer kullanılır.
     */
    static String istemci(HttpServletRequest http) {
        String xff = http.getHeader("X-Forwarded-For");
        if (xff != null && !xff.isBlank()) {
            String[] p = xff.split(",");
            return p[p.length - 1].strip();
        }
        return http.getRemoteAddr();
    }

    private static ResponseEntity<HataDto> hata(HttpStatus durum, String mesaj) {
        return ResponseEntity.status(durum).body(new HataDto(durum.value(), durum.getReasonPhrase(), mesaj));
    }
}
