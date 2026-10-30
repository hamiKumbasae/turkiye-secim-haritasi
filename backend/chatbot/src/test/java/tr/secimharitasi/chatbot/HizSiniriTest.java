package tr.secimharitasi.chatbot;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.chatbot.web.HizSiniri;

class HizSiniriTest {

    /** Elle ilerletilen saat. */
    static class Saat extends Clock {
        long ms = 1_000_000;

        @Override
        public long millis() {
            return ms;
        }

        @Override
        public Instant instant() {
            return Instant.ofEpochMilli(ms);
        }

        @Override
        public java.time.ZoneId getZone() {
            return ZoneOffset.UTC;
        }

        @Override
        public Clock withZone(java.time.ZoneId zone) {
            return this;
        }
    }

    @Test
    void dakikadaSinirVePencereKayar() {
        Saat saat = new Saat();
        HizSiniri s = new HizSiniri(2, saat);
        assertThat(s.izinVer("a")).isTrue();
        saat.ms += 10_000;
        assertThat(s.izinVer("a")).isTrue();
        assertThat(s.izinVer("a")).isFalse();
        assertThat(s.izinVer("b")).isTrue();
        saat.ms += 50_001;
        assertThat(s.izinVer("a")).isTrue();   // ilk istek pencereden çıktı
        assertThat(s.izinVer("a")).isFalse();
    }
}
