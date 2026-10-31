package io.github.hamikumbasae.election.service;

import io.github.hamikumbasae.election.domain.Level;
import io.github.hamikumbasae.election.dto.ElectionSummaryDto;
import io.github.hamikumbasae.election.dto.PageResponse;
import io.github.hamikumbasae.election.dto.PartyResultDto;
import io.github.hamikumbasae.election.dto.UnitResultDto;
import io.github.hamikumbasae.election.dto.UnitSummaryDto;
import io.github.hamikumbasae.election.repository.ResultRepository;
import io.github.hamikumbasae.election.repository.ResultRepository.UnitFilter;
import io.github.hamikumbasae.election.repository.UnitRow;
import io.github.hamikumbasae.election.repository.VoteRow;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/** Results of one election: national totals, provinces, districts, neighbourhoods, abroad. */
@Service
public class ResultService {

    /** Upper bound for unpaged lists (the largest province has 39 districts, the whole country ~1000). */
    private static final int UNPAGED_LIMIT = 2_000;

    private final ElectionService elections;
    private final ResultRepository repository;

    public ResultService(ElectionService elections, ResultRepository repository) {
        this.elections = elections;
        this.repository = repository;
    }

    /**
     * Nationwide totals. The source data has no national row, so it is computed from the province rows
     * plus the abroad row (where one exists). Shares are relative to the sum of all party votes.
     */
    @Cacheable(cacheNames = "summaries", key = "#code.toLowerCase()")
    public ElectionSummaryDto summary(String code) {
        ElectionCatalog.Entry election = elections.require(code);
        ResultRepository.NationalTotals totals = repository.nationalTotals(election.id());
        List<VoteRow> parties = repository.nationalPartyTotals(election.id());
        long voteSum = parties.stream().mapToLong(VoteRow::votes).sum();
        List<PartyResultDto> results = parties.stream()
                .map(p -> new PartyResultDto(p.party(), p.votes(), Mappers.share(p.votes(), voteSum), p.seats(), null))
                .toList();
        return new ElectionSummaryDto(election.dto(), totals.registeredVoters(),
                totals.validVotes() > 0 ? totals.validVotes() : voteSum, totals.turnout(), totals.provinces(),
                totals.includesAbroad(), results);
    }

    public List<UnitSummaryDto> provinces(String code) {
        ElectionCatalog.Entry election = elections.require(code);
        return repository.findUnits(new UnitFilter(election.id(), Level.PROVINCE, null, null, null), UNPAGED_LIMIT, 0)
                .stream().map(Mappers::summary).toList();
    }

    public UnitResultDto province(String code, int plateCode) {
        ElectionCatalog.Entry election = elections.require(code);
        UnitRow row = repository.findUnit(new UnitFilter(election.id(), Level.PROVINCE, plateCode, null, null))
                .orElseThrow(() -> new NotFoundException("No result for province " + plateCode
                        + " in election " + election.dto().code()));
        return withVotes(election, row);
    }

    public List<UnitSummaryDto> districts(String code, int plateCode) {
        ElectionCatalog.Entry election = elections.require(code);
        List<UnitRow> rows = repository.findUnits(
                new UnitFilter(election.id(), Level.DISTRICT, plateCode, null, null), UNPAGED_LIMIT, 0);
        if (rows.isEmpty()) {
            throw new NotFoundException("No district results for province " + plateCode
                    + " in election " + election.dto().code());
        }
        return rows.stream().map(Mappers::summary).toList();
    }

    public UnitResultDto district(String code, String geomId) {
        ElectionCatalog.Entry election = elections.require(code);
        UnitRow row = repository.findUnit(new UnitFilter(election.id(), Level.DISTRICT, null, geomId, null))
                .orElseThrow(() -> new NotFoundException("No result for district '" + geomId
                        + "' in election " + election.dto().code()));
        return withVotes(election, row);
    }

    /** Neighbourhood results of one district, paged, each with its full party breakdown. */
    public PageResponse<UnitResultDto> neighbourhoods(String code, String districtGeomId, int page, int size) {
        ElectionCatalog.Entry election = elections.require(code);
        UnitFilter filter = new UnitFilter(election.id(), Level.NEIGHBOURHOOD, null, null, districtGeomId);
        long total = repository.countUnits(filter);
        if (total == 0) {
            throw new NotFoundException("No neighbourhood results for district '" + districtGeomId
                    + "' in election " + election.dto().code()
                    + " (neighbourhood data covers 2009 onwards)");
        }
        List<UnitRow> rows = repository.findUnits(filter, size, (long) page * size);
        Map<Integer, List<VoteRow>> votes = repository.findVotes(rows.stream().map(UnitRow::id).toList());
        List<UnitResultDto> content = rows.stream()
                .map(r -> Mappers.result(election.dto().code(), r, votes.get(r.id())))
                .toList();
        return PageResponse.of(content, page, size, total);
    }

    public UnitResultDto abroad(String code) {
        ElectionCatalog.Entry election = elections.require(code);
        UnitRow row = repository.findUnit(new UnitFilter(election.id(), Level.ABROAD, null, null, null))
                .orElseThrow(() -> new NotFoundException("Election " + election.dto().code()
                        + " has no separate abroad result"));
        return withVotes(election, row);
    }

    private UnitResultDto withVotes(ElectionCatalog.Entry election, UnitRow row) {
        List<VoteRow> votes = repository.findVotes(List.of(row.id())).get(row.id());
        return Mappers.result(election.dto().code(), row, votes);
    }
}
