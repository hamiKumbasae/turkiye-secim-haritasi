package tr.secimharitasi.chatbot.arac;

/** Araç çalıştırılamadı (bulunamayan kayıt, geçersiz girdi). Modele hata olarak döner, model düzeltebilir. */
public class AracHatasi extends RuntimeException {

    public AracHatasi(String mesaj) {
        super(mesaj);
    }
}
