package tr.secimharitasi.chatbot.web;

import java.time.Clock;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** İstemci başına kayan bir dakikalık pencerede istek sınırı (model maliyetini korumak için). */
public class HizSiniri {

    private static final long PENCERE_MS = 60_000;

    private final int dakikadaIstek;
    private final Clock saat;
    private final Map<String, Deque<Long>> istekler = new ConcurrentHashMap<>();

    public HizSiniri(int dakikadaIstek, Clock saat) {
        this.dakikadaIstek = dakikadaIstek;
        this.saat = saat;
    }

    /** @return istek kabul edildiyse true */
    public boolean izinVer(String istemci) {
        long simdi = saat.millis();
        if (istekler.size() > 10_000) {
            istekler.entrySet().removeIf(e -> {
                synchronized (e.getValue()) {
                    return e.getValue().isEmpty() || e.getValue().peekLast() <= simdi - PENCERE_MS;
                }
            });
        }
        Deque<Long> d = istekler.computeIfAbsent(istemci, k -> new ArrayDeque<>());
        synchronized (d) {
            while (!d.isEmpty() && d.peekFirst() <= simdi - PENCERE_MS) {
                d.pollFirst();
            }
            if (d.size() >= dakikadaIstek) {
                return false;
            }
            d.addLast(simdi);
            return true;
        }
    }
}
