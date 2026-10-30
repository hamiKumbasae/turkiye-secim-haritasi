package tr.secimharitasi.api.depo;

import java.util.Collection;
import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import tr.secimharitasi.api.varlik.OyIl;
import tr.secimharitasi.api.varlik.OyIlId;

public interface OyIlDeposu extends JpaRepository<OyIl, OyIlId> {

    List<OyIl> findBySecimId(String secimId);

    List<OyIl> findBySecimIdAndPlaka(String secimId, Integer plaka);

    /** Partinin (ve verilirse öncüllerinin) bir ildeki sonuçları, seçimlere göre. */
    @Query("""
            select new tr.secimharitasi.api.depo.PartiOySatiri(s.secimId, s.tur, s.yil, o.partiId, o.plaka, si.ad,
                   cast(o.oy as Long), cast(si.gecerliOy as Long), o.oran)
            from OyIl o, Secim s, SonucIl si
            where s.secimId = o.secimId and si.secimId = o.secimId and si.plaka = o.plaka
              and o.partiId in :partiler and o.plaka = :plaka
              and (:tur is null or s.tur = :tur)
              and (:yilBas is null or s.yil >= :yilBas)
              and (:yilBit is null or s.yil <= :yilBit)
            order by s.yil, s.secimId""")
    List<PartiOySatiri> ildekiSonuclar(@Param("partiler") Collection<Integer> partiler, @Param("plaka") int plaka,
                                      @Param("tur") String tur, @Param("yilBas") Integer yilBaslangic,
                                      @Param("yilBit") Integer yilBitis);

    /** Partinin yurt içi oy toplamı (il satırları, plaka > 0), seçimlere göre. */
    @Query("""
            select new tr.secimharitasi.api.depo.PartiToplami(s.secimId, s.tur, s.yil, o.partiId, sum(o.oy))
            from OyIl o, Secim s
            where s.secimId = o.secimId and o.plaka > 0 and o.partiId in :partiler
              and (:tur is null or s.tur = :tur)
              and (:yilBas is null or s.yil >= :yilBas)
              and (:yilBit is null or s.yil <= :yilBit)
            group by s.secimId, s.tur, s.yil, o.partiId
            order by s.yil, s.secimId""")
    List<PartiToplami> turkiyeToplamlari(@Param("partiler") Collection<Integer> partiler,
                                         @Param("tur") String tur, @Param("yilBas") Integer yilBaslangic,
                                         @Param("yilBit") Integer yilBitis);

    /** Bir seçimde partinin en yüksek oranı aldığı iller (yurt dışı hariç). */
    @Query("""
            select new tr.secimharitasi.api.depo.PartiOySatiri(s.secimId, s.tur, s.yil, o.partiId, o.plaka, si.ad,
                   cast(o.oy as Long), cast(si.gecerliOy as Long), o.oran)
            from OyIl o, Secim s, SonucIl si
            where s.secimId = o.secimId and si.secimId = o.secimId and si.plaka = o.plaka
              and o.secimId = :secimId and o.partiId = :partiId and o.plaka > 0 and o.oran is not null
            order by o.oran desc, o.plaka""")
    List<PartiOySatiri> enGucluIller(@Param("secimId") String secimId, @Param("partiId") int partiId,
                                     Pageable sayfa);
}
