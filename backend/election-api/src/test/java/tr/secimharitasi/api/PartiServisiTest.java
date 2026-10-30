package tr.secimharitasi.api;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.api.depo.GecerliOyToplami;
import tr.secimharitasi.api.depo.OyIlDeposu;
import tr.secimharitasi.api.depo.PartiDeposu;
import tr.secimharitasi.api.depo.PartiToplami;
import tr.secimharitasi.api.depo.SecimDeposu;
import tr.secimharitasi.api.depo.SonucIlDeposu;
import tr.secimharitasi.api.servis.PartiServisi;
import tr.secimharitasi.api.varlik.Parti;
import tr.secimharitasi.common.dto.PartiDto;
import tr.secimharitasi.common.dto.PartiSonucDto;

/** Servis mantığı (veritabanı yok): öncül zinciri ve Türkiye geneli oran hesabı. */
class PartiServisiTest {

    private final PartiDeposu partiler = mock(PartiDeposu.class);
    private final OyIlDeposu oyIl = mock(OyIlDeposu.class);
    private final SonucIlDeposu sonucIl = mock(SonucIlDeposu.class);
    private final PartiServisi servis = new PartiServisi(partiler, oyIl, sonucIl, mock(SecimDeposu.class));

    private static Parti parti(int id, String ad, Integer onceki) {
        return new Parti(id, ad, ad, "parti", null, onceki, onceki == null ? null : "ad_degisikligi", 2000, null);
    }

    @Test
    void oncekiZinciriEnYakindanEnEskiye() {
        when(partiler.findAll()).thenReturn(List.of(parti(1, "A", null), parti(2, "B", 1), parti(3, "C", 2)));
        PartiDto c = servis.parti(3);
        assertThat(c.oncekiler()).extracting(PartiDto::ad).containsExactly("B", "A");
    }

    @Test
    void donguluZincirSonsuzaGitmez() {
        when(partiler.findAll()).thenReturn(List.of(parti(1, "A", 2), parti(2, "B", 1)));
        assertThat(servis.parti(1).oncekiler()).extracting(PartiDto::ad).containsExactly("B");
    }

    @Test
    void turkiyeGeneliOranGecerliOyToplamindan() {
        when(partiler.findAll()).thenReturn(List.of(parti(2, "CHP", null)));
        when(oyIl.turkiyeToplamlari(any(), any(), any(), any(), any()))
                .thenReturn(List.of(new PartiToplami("2023", "genel", 2023, 2, 650L),
                        new PartiToplami("1950", "genel", 1950, 2, 100L)));
        when(sonucIl.yurtIciGecerliOy(any()))
                .thenReturn(List.of(new GecerliOyToplami("2023", 1500L), new GecerliOyToplami("1950", null)));
        List<PartiSonucDto> s = servis.sonuclar(2, null, null, null, null, null, false);
        assertThat(s.get(0).oran()).isEqualByComparingTo("43.33");
        assertThat(s.get(1).oran()).isNull();   // geçerli oy bilinmiyor: oran hesaplanmaz
        assertThat(s.get(0).yer()).isEqualTo("Türkiye (yurt içi)");
    }

    @Test
    void ilBazindaSorguIlSorgusunaGider() {
        when(partiler.findAll()).thenReturn(List.of(parti(2, "CHP", null)));
        when(oyIl.ildekiSonuclar(any(), eq(34), any(), any(), any(), any())).thenReturn(List.of());
        assertThat(servis.sonuclar(2, "genel", null, null, null, 34, false)).isEmpty();
    }

    @Test
    void senatoToplamiTurkiyeGeneliDiyeGosterilmez() {
        when(partiler.findAll()).thenReturn(List.of(parti(2, "CHP", null)));
        when(oyIl.turkiyeToplamlari(any(), any(), any(), any(), any()))
                .thenReturn(List.of(new PartiToplami("1961senato", "senato", 1961, 2, 100L)));
        when(sonucIl.yurtIciGecerliOy(any())).thenReturn(List.of(new GecerliOyToplami("1961senato", 400L)));
        assertThat(servis.sonuclar(2, "senato", null, null, null, null, false).get(0).yer())
                .isEqualTo("Toplam (yalnız seçim yapılan iller)");
    }
}
