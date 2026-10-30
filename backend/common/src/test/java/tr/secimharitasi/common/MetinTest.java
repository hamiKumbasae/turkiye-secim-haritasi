package tr.secimharitasi.common;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class MetinTest {

    @Test
    void turkceKatlama() {
        assertThat(Metin.katla("ÜMRANİYE")).isEqualTo("umraniye");
        assertThat(Metin.katla("Ümraniye")).isEqualTo("umraniye");
        assertThat(Metin.katla("umraniye")).isEqualTo("umraniye");
        assertThat(Metin.katla("Iğdır")).isEqualTo("igdir");
        assertThat(Metin.katla("Afyon-karahisar")).isEqualTo("afyonkarahisar");
        assertThat(Metin.katla("Âşık")).isEqualTo("asik");
        assertThat(Metin.katla(null)).isEmpty();
    }
}
