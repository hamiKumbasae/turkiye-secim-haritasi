package tr.secimharitasi.chatbot.model;

/** Model servisine ulaşılamadı ya da hata döndü. */
public class ModelHatasi extends RuntimeException {

    public ModelHatasi(String mesaj, Throwable neden) {
        super(mesaj, neden);
    }
}
