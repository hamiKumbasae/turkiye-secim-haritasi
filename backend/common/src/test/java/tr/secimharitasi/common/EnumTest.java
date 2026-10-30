package tr.secimharitasi.common;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class EnumTest {

    @ParameterizedTest
    @CsvSource({
            "2023, GENEL", "1950, GENEL", "2015Haziran, GENEL", "2015Kasim, GENEL",
            "2024yerel, YEREL", "1950yerel, YEREL",
            "2017referandum, REFERANDUM",
            "2014cb, CUMHURBASKANLIGI", "2023cb1tur, CUMHURBASKANLIGI", "2023cb2tur, CUMHURBASKANLIGI",
            "1961senato, SENATO", "1979senato, SENATO"})
    void secimAnahtarindanTur(String secimId, SecimTuru beklenen) {
        assertThat(SecimTuru.fromSecimId(secimId)).isEqualTo(beklenen);
    }

    @Test
    void kodlarJsonaKucukHarfYazilir() throws Exception {
        ObjectMapper om = new ObjectMapper();
        assertThat(om.writeValueAsString(SecimTuru.CUMHURBASKANLIGI)).isEqualTo("\"cumhurbaskanligi\"");
        assertThat(om.writeValueAsString(SecenekTipi.DIGER)).isEqualTo("\"diger\"");
        assertThat(om.writeValueAsString(GecisTuru.AD_DEGISIKLIGI)).isEqualTo("\"ad_degisikligi\"");
    }

    @Test
    void koddanEnum() {
        assertThat(SecimTuru.fromKod("Yerel")).isEqualTo(SecimTuru.YEREL);
        assertThat(SecenekTipi.fromKod("aday")).isEqualTo(SecenekTipi.ADAY);
        assertThat(GecisTuru.fromKod(null)).isNull();
        assertThat(SecimTuru.fromKod("senato")).isEqualTo(SecimTuru.SENATO);
        assertThatThrownBy(() -> SecimTuru.fromKod("muhtarlik")).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void oylamaTurleri() throws Exception {
        assertThat(OylamaTuru.fromKod("belediye_meclisi")).isEqualTo(OylamaTuru.BELEDIYE_MECLISI);
        assertThat(OylamaTuru.anaOylama(SecimTuru.GENEL)).isEqualTo(OylamaTuru.MILLETVEKILI);
        assertThat(OylamaTuru.anaOylama(SecimTuru.YEREL)).isEqualTo(OylamaTuru.BASKANLIK);
        assertThat(OylamaTuru.anaOylama(SecimTuru.SENATO)).isEqualTo(OylamaTuru.SENATO);
        assertThatThrownBy(() -> OylamaTuru.anaOylama(SecimTuru.ARA)).isInstanceOf(IllegalArgumentException.class);
        assertThat(new ObjectMapper().writeValueAsString(OylamaTuru.IL_GENEL_MECLISI)).isEqualTo("\"il_genel_meclisi\"");
    }
}
