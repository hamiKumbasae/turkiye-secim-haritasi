package tr.secimharitasi.loader;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import tr.secimharitasi.loader.yukleme.VeriYukleyici;

@Component
@ConditionalOnProperty(name = "veri.otomatik-calistir", havingValue = "true", matchIfMissing = true)
class YuklemeCalistirici implements CommandLineRunner {

    private final VeriYukleyici yukleyici;

    YuklemeCalistirici(VeriYukleyici yukleyici) {
        this.yukleyici = yukleyici;
    }

    @Override
    public void run(String... args) {
        yukleyici.yukle();
    }
}
