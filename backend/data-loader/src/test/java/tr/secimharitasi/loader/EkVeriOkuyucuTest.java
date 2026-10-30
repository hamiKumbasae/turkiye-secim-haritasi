package tr.secimharitasi.loader;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import org.junit.jupiter.api.Test;
import tr.secimharitasi.common.OylamaTuru;
import tr.secimharitasi.common.SecimTuru;
import tr.secimharitasi.loader.ek.BeldeKaydi;
import tr.secimharitasi.loader.ek.EkVeriOkuyucu;
import tr.secimharitasi.loader.ek.IlceIndeksi;
import tr.secimharitasi.loader.ek.KapsamKaydi;
import tr.secimharitasi.loader.ek.SecilenKaydi;
import tr.secimharitasi.loader.kaynak.KaynakSecim;
import tr.secimharitasi.loader.kaynak.SonucSatiri;

class EkVeriOkuyucuTest {

    private final EkVeriOkuyucu.Sonuc ek = new EkVeriOkuyucu(Fikstur.DIZIN).oku(Fikstur.anaVeMeclis());

    @Test
    void senatoIlOylariAdaylardanBagimsizDahil() {
        KaynakSecim s = ek.secimler().get(0);
        assertThat(s.secimId()).isEqualTo("2098senato");
        assertThat(s.tur()).isEqualTo(SecimTuru.SENATO);
        assertThat(s.oylama()).isEqualTo(OylamaTuru.SENATO);
        SonucSatiri il = s.dosya().iller().get(0);
        assertThat(il.oy()).containsOnlyKeys("CHP", "AK Parti", "Bağımsız");
        assertThat(il.oy().get("Bağımsız").oy()).isEqualTo(10L);
        assertThat(il.kazanan()).isEqualTo("CHP");
        assertThat(il.gecerliOy()).isEqualTo(100);
    }

    @Test
    void senatoTuikIlcesiDogrulanamayanAlanBos() {
        SonucSatiri aladag = ek.secimler().get(0).dosya().ilceler().get(0);
        assertThat(aladag.ilceId()).isEqualTo("TR-D-01-001");
        assertThat(aladag.secmen()).isNull();
        assertThat(aladag.oyKullanan()).isEqualTo(45);
        assertThat(aladag.gecerliOy()).as("muteber geçerli oya taşınır").isEqualTo(40);
        assertThat(aladag.oy().get("Bağımsız").oy()).isEqualTo(5L);
        assertThat(aladag.notlar()).isEqualTo("Kaynakta doğrulanamayan alanlar boş bırakıldı: secmen");
    }

    @Test
    void senatoIlceBirincileriAdindanEslenir() {
        List<SonucSatiri> ilceler = ek.secimler().get(0).dosya().ilceler();
        // Aladağ zaten TÜİK satırında var; CEYHAN eşlenir; olmayan ilçe sayılır
        assertThat(ilceler).hasSize(2);
        SonucSatiri ceyhan = ilceler.get(1);
        assertThat(ceyhan.ilceId()).isEqualTo("TR-D-01-002");
        assertThat(ceyhan.yalnizKazananBiliniyor()).isTrue();
        assertThat(ceyhan.kazanan()).isEqualTo("AK Parti");
        assertThat(ek.eslesmeyenSenatoIlcesi()).isEqualTo(1);
    }

    @Test
    void secilenlerVeKapsam() {
        assertThat(ek.secilenler()).extracting(SecilenKaydi::gorev, SecilenKaydi::ad, SecilenKaydi::parti)
                .containsExactly(
                        org.assertj.core.groups.Tuple.tuple("milletvekili", "Ayşe Kaya", "CHP"),
                        org.assertj.core.groups.Tuple.tuple("milletvekili", "Ali Veli", null),
                        org.assertj.core.groups.Tuple.tuple("senator", "Senatör Bir", "CHP"));
        assertThat(ek.kapsam()).extracting(KapsamKaydi::secimId, KapsamKaydi::veri, KapsamKaydi::durum)
                .containsExactly(
                        org.assertj.core.groups.Tuple.tuple("2098", "milletvekilleri", "eksik"),
                        org.assertj.core.groups.Tuple.tuple("2098senato", "senatorler", "tam"),
                        org.assertj.core.groups.Tuple.tuple("2099yerel", "beldeler", null),
                        org.assertj.core.groups.Tuple.tuple("2099yerel_bm", "belediye_meclisi", null));
    }

    @Test
    void beldeler() {
        assertThat(ek.beldeler()).hasSize(3);
        BeldeKaydi komur = ek.beldeler().get(0);
        assertThat(komur.kaynak()).isEqualTo("wikipedia");
        assertThat(komur.sadeceKazanan()).isTrue();
        assertThat(komur.ilceId()).isEqualTo("TR-D-01-001");
        assertThat(komur.oy()).containsExactly(java.util.Map.entry("CHP", 500L));

        BeldeKaydi tuik = ek.beldeler().get(1);
        assertThat(tuik.kaynak()).isEqualTo("tuik");
        assertThat(tuik.ilceId()).as("'Adana Ceyhan' -> Ceyhan").isEqualTo("TR-D-01-002");
        assertThat(tuik.gecerliOy()).isEqualTo(90);
        assertThat(tuik.oy()).containsKeys("YENİDEN REFAH", "Yeniden Refah");

        BeldeKaydi meclis = ek.beldeler().get(2);
        assertThat(meclis.secimId()).isEqualTo("2099yerel_bm");
        assertThat(meclis.ilceId()).as("büyük harfli üst ilçe adı").isEqualTo("TR-D-01-001");
        assertThat(meclis.secmen()).as("INT'e sığmayan okuma hatası").isNull();
        assertThat(meclis.not()).isEqualTo("Okunamayan değer boş bırakıldı: secmen");
        assertThat(meclis.kontrol()).isEqualTo("tutarsiz");
    }

    @Test
    void ilceIndeksiKurallari() {
        IlceIndeksi i = new IlceIndeksi();
        Fikstur.secimler().forEach(i::ekle);
        assertThat(i.bul(1, "ALADAĞ", 2000)).isEqualTo("TR-D-01-001");
        assertThat(i.bul(1, "Adana Ceyhan", 2000)).isEqualTo("TR-D-01-002");
        assertThat(i.bul(1, "Yok", 2000)).isNull();
        assertThat(i.bul(6, "Aladağ", 2000)).as("başka ilde aynı ad yok").isNull();
        // En yakın yıl: Eski Merkez yalnız 2097'de var
        assertThat(i.bul(1, "Eski Merkez", 2099)).isEqualTo("HIST-Adana-Eski");
        assertThat(IlceIndeksi.katla("Kahta-Merkez. ")).isEqualTo("kahtamerkez");
    }
}
