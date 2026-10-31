package tr.secimharitasi.api.web;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import tr.secimharitasi.api.servis.KayitBulunamadiException;
import tr.secimharitasi.common.dto.HataDto;

@RestControllerAdvice
public class HataYakalayici {

    @ExceptionHandler(KayitBulunamadiException.class)
    ResponseEntity<HataDto> bulunamadi(KayitBulunamadiException e) {
        return yanit(HttpStatus.NOT_FOUND, e.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<HataDto> gecersiz(IllegalArgumentException e) {
        return yanit(HttpStatus.BAD_REQUEST, e.getMessage());
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    ResponseEntity<HataDto> turUyusmazligi(MethodArgumentTypeMismatchException e) {
        return yanit(HttpStatus.BAD_REQUEST, "Geçersiz değer: " + e.getName() + "=" + e.getValue());
    }

    private static ResponseEntity<HataDto> yanit(HttpStatus durum, String mesaj) {
        return ResponseEntity.status(durum).body(new HataDto(durum.value(), durum.getReasonPhrase(), mesaj));
    }
}
