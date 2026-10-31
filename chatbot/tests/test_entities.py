"""Entity recognition: Turkish normalisation, suffixes, aliases, duplicate district names."""
import pytest
from conftest import real_db_or_skip

from secim_chatbot.entities import EntityIndex, default_index
from secim_chatbot.turkce import fold, suffix_match, tokenize

IDX = default_index()


def kinds(q):
    return [(m.kind, m.value) for m in IDX.find_mentions(q)]


@pytest.mark.parametrize("a,b", [
    ("İSTANBUL", "istanbul"), ("Istanbul", "istanbul"), ("ıstanbul", "istanbul"), ("Kadıköy", "kadikoy"),
    ("ÇANKAYA", "cankaya"), ("Şanlıurfa", "sanliurfa"), ("Iğdır", "igdir"), ("i̇stanbul", "istanbul"),
])
def test_fold(a, b):
    assert fold(a) == b


def test_tokenize_drops_apostrophe_suffix():
    toks = tokenize("İzmir'in 2023'te Kadıköy’de")
    assert [(t.fold, t.suffix) for t in toks] == [("izmir", "in"), ("2023", "te"), ("kadikoy", "de")]


@pytest.mark.parametrize("tok,name,ok", [
    ("istanbulda", "istanbul", True), ("ankaranin", "ankara", True), ("kadikoyde", "kadikoy", True),
    ("rizeye", "rize", True), ("ankaralilar", "ankara", True), ("ankarakent", "ankara", False), ("vanadyum", "van", False),
    ("izmirli", "izmir", True), ("bursaspor", "bursa", False),
])
def test_suffix_match(tok, name, ok):
    assert suffix_match(tok, name) is ok


@pytest.mark.parametrize("q,expected", [
    ("İstanbul'da", [("il", 34)]),
    ("istanbulda", [("il", 34)]),
    ("ISTANBUL'DA", [("il", 34)]),
    ("Afyon ve Maraş", [("il", 3), ("il", 46)]),
    ("Kadikoy", [("ilce", "Kadıköy")]),
    ("Ümraniye'nin mahalleleri", [("ilce", "Ümraniye")]),
    ("AKP ve Ak Parti", [("parti", "AK Parti"), ("parti", "AK Parti")]),
    ("CHP'nin", [("parti", "CHP")]),
    ("Yeniden Refah ile Refah Partisi", [("parti", "YENİDEN REFAH"), ("parti", "RP")]),
    ("Zafer Partisi'nin", [("parti", "ZP")]),
    ("Kılıçdaroğlu'nun", [("aday", "Kemal Kılıçdaroğlu")]),
    ("Recep Tayyip Erdoğan", [("aday", "Recep Tayyip Erdoğan")]),
    ("Tayyip Erdoğan", [("aday", "Recep Tayyip Erdoğan")]),
    ("Hayır oranı", [("secenek", "Hayır")]),
])
def test_mentions(q, expected):
    assert kinds(q) == expected


def test_case_sensitive_aliases():
    # 'İYİ Parti' is a party, 'en iyi' is not; 'İnce' needs a capital, 'ince' is an adjective
    assert kinds("İYİ Parti'nin en iyi olduğu mahalleler") == [("parti", "İYİ Parti")]
    assert kinds("ince ince hesap") == []
    assert kinds("İnce 2018'de") == [("aday", "Muharrem İnce")]
    assert kinds("dem") == [] and kinds("DEM") == [("parti", "DEM Parti")]


def test_duplicate_district_names_need_their_province():
    assert IDX.ilce_plates("Yenişehir", "2023") == {16, 21, 33}
    # alone: an unresolved place (blocks templates instead of being silently dropped)
    assert kinds("Yenişehir'de") == [("belirsiz", "Yenişehir")]
    m = IDX.find_mentions("Mersin Yenişehir'de")
    assert [(x.kind, x.value) for x in m] == [("il", 33), ("ilce", "Yenişehir")]
    assert set(m[1].extra) == {16, 21, 33}
    # Merkez exists in ~50 provinces and is never a district entity by itself
    assert all(k != "ilce" for k, _ in kinds("Merkez ilçesi"))


def test_districts_that_moved_province():
    # Cizre: Mardin until 1990, Şırnak after; plates are per election
    assert IDX.ilce_plates("Cizre") == {47, 73}
    assert IDX.ilce_plates("Cizre", "2023") == {73}


def test_common_words_are_not_districts():
    # Genç (Bingöl), Olur (Erzurum), Akdeniz (Mersin) are districts but also ordinary words / a region:
    # never a resolved district without their province, only a blocking 'belirsiz' mention
    assert all(k == "belirsiz" for k, _ in kinds("genç seçmenler olur mu"))
    assert kinds("Bingöl Genç'te") == [("il", 12), ("ilce", "Genç")]
    assert kinds("Akdeniz illerinde") == [("belirsiz", "Akdeniz")]


def test_party_succession():
    assert IDX.resolve_party("HDP", "2023") == "YEŞİL SOL"
    assert IDX.resolve_party("HDP", "2024yerel") == "DEM Parti"
    assert IDX.resolve_party("HDP", "2018") == "HDP"
    assert IDX.resolve_party("ZP", "2018") is None


def test_snapshot_round_trip():
    again = EntityIndex.from_rows(
        [[e.id, e.kod, e.tur, e.yil, e.ad] for e in IDX.elections], list(IDX.iller.items()),
        [(ad, p, k) for ad, ps in IDX.ilceler.items() for p, k in ps.items()],
        [(k, p) for k, ps in IDX.parties.items() for p in ps])
    assert again.to_snapshot() == IDX.to_snapshot()
    assert len(IDX.elections) == 46 and len(IDX.iller) == 81 and len(IDX.candidates) == 9


def test_snapshot_matches_database():
    db = real_db_or_skip()
    live = EntityIndex.from_db(db)
    assert live.to_snapshot() == IDX.to_snapshot(), "python scripts/build_varliklar.py ile yeniden üretin"
