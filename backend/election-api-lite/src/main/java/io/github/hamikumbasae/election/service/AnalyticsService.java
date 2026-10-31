package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.ElectionType;
import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.ElectionDto;
import io.github.hamikumbasae.election.dto.PartyHistoryDto;
import io.github.hamikumbasae.election.dto.PartyHistoryPointDto;
import io.github.hamikumbasae.election.dto.RankingEntryDto;
import io.github.hamikumbasae.election.repository.AnalyticsRepository;
import io.github.hamikumbasae.election.repository.AnalyticsRepository.RankedUnit;
import io.github.hamikumbasae.election.repository.AnalyticsRepository.RankingScope;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

/** Questions that span many units or many elections. */
@Service
public class AnalyticsService {

    public enum Order { DESC, ASC }

    private final ElectionService elections;
    private final AnalyticsRepository repository;

    public AnalyticsService(ElectionService elections, AnalyticsRepository repository) {
        this.elections = elections;
        this.repository = repository;
    }

    /**
     * "How did party X do in Ümraniye over time?" One point per election in which the party was on the
     * ballot in that place, oldest first. Zero-vote rows (party listed but not standing) are dropped unless
     * {@code includeZero} is set.
     */
    @Cacheable(cacheNames = "history",
            key = "{#party.toLowerCase(), #plateCode, #district == null ? '' : #district.toLowerCase(), #type, #includeZero}")
    public PartyHistoryDto partyHistory(String party, int plateCode, String district, ElectionType type,
                                        boolean includeZero) {
        String districtName = district == null || district.isBlank() ? null : district.trim();
        Map<Integer, ElectionCatalog.Entry> byId = elections.byId();
        List<AnalyticsRepository.HistoryRow> rows = repository.partyHistory(party.trim(), plateCode, districtName, type);
        List<PartyHistoryPointDto> points = new ArrayList<>();
        String place = null;
        String partyName = party.trim();
        for (AnalyticsRepository.HistoryRow r : rows) {
            if (!includeZero && r.votes() == 0) {
                continue;
            }
            ElectionDto e = byId.get(r.electionId()).dto();
            points.add(new PartyHistoryPointDto(e.code(), e.type(), e.date(), r.votes(), r.share(), r.rank(),
                    r.winner(), r.geomId()));
            place = r.unitName();
            partyName = r.party();
        }
        if (points.isEmpty()) {
            throw new NotFoundException("No votes for '" + party + "' in "
                    + (districtName == null ? "province " + plateCode : districtName + " (province " + plateCode + ")")
                    + (type == null ? "" : " in " + type.apiValue() + " elections"));
        }
        points.sort(Comparator.comparing(PartyHistoryPointDto::date, Comparator.nullsLast(LocalDate::compareTo))
                .thenComparing(PartyHistoryPointDto::electionCode));
        return new PartyHistoryDto(partyName, districtName == null ? Level.PROVINCE : Level.DISTRICT, plateCode,
                place, points);
    }

    @Cacheable(cacheNames = "rankings",
            key = "{'turnout', #code.toLowerCase(), #level, #plateCode, #districtGeomId, #order, #minVoters, #limit}")
    public List<RankingEntryDto> turnoutRanking(String code, Level level, Integer plateCode, String districtGeomId,
                                                Order order, long minVoters, int limit) {
        RankingScope scope = scope(code, level, plateCode, districtGeomId);
        return ranked(repository.byTurnout(scope, order == Order.DESC, minVoters, limit));
    }

    @Cacheable(cacheNames = "rankings",
            key = "{'party', #code.toLowerCase(), #party.toLowerCase(), #level, #plateCode, #districtGeomId, #order, #minVoters, #limit}")
    public List<RankingEntryDto> partyRanking(String code, String party, Level level, Integer plateCode,
                                              String districtGeomId, Order order, long minVoters, int limit) {
        RankingScope scope = scope(code, level, plateCode, districtGeomId);
        List<RankingEntryDto> result = ranked(repository.byPartyShare(scope, party.trim(), order == Order.DESC,
                minVoters, limit));
        if (result.isEmpty()) {
            throw new NotFoundException("Party '" + party + "' has no " + level.apiValue()
                    + " results in election " + code);
        }
        return result;
    }

    private RankingScope scope(String code, Level level, Integer plateCode, String districtGeomId) {
        if (level == Level.ABROAD) {
            throw new BadRequestException("Rankings need level province, district or neighbourhood");
        }
        if (level == Level.PROVINCE && (plateCode != null || districtGeomId != null)) {
            throw new BadRequestException("plate and district filters do not apply to level=province");
        }
        if (level == Level.DISTRICT && districtGeomId != null) {
            throw new BadRequestException("Use plate (not district) to scope a district ranking");
        }
        if (level == Level.NEIGHBOURHOOD && districtGeomId == null) {
            throw new BadRequestException("Neighbourhood rankings need a district geometry id, e.g. district=TR-D-34-037");
        }
        ElectionCatalog.Entry election = elections.require(code);
        return new RankingScope(election.id(), level, level == Level.NEIGHBOURHOOD ? null : plateCode, districtGeomId);
    }

    private static List<RankingEntryDto> ranked(List<RankedUnit> units) {
        List<RankingEntryDto> out = new ArrayList<>(units.size());
        for (int i = 0; i < units.size(); i++) {
            RankedUnit r = units.get(i);
            out.add(new RankingEntryDto(i + 1, r.unit().level(), Mappers.plateOf(r.unit()), r.unit().name(),
                    r.unit().geomId(), r.value(), r.votes(), r.unit().winner()));
        }
        return out;
    }
}
