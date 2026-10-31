package tr.secimharitasi.api.servis;

import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import tr.secimharitasi.api.varlik.Parti;

/** İstek boyunca parti_id -> Parti (110 satırlık küçük tablo; her istekte bir sorgu). */
record PartiSozlugu(Map<Integer, Parti> partiler) {

    static PartiSozlugu of(Iterable<Parti> hepsi) {
        return new PartiSozlugu(java.util.stream.StreamSupport.stream(hepsi.spliterator(), false)
                .collect(Collectors.toMap(Parti::getPartiId, Function.identity())));
    }

    String ad(Integer id) {
        Parti p = id == null ? null : partiler.get(id);
        return p == null ? null : p.getAd();
    }

    String kisa(Integer id) {
        Parti p = id == null ? null : partiler.get(id);
        return p == null ? null : p.getKisa();
    }
}
