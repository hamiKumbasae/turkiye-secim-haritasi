"""Entity recognition for Turkish election questions, with the lexicon loaded from the database.

`EntityIndex` knows the 46 elections, the 81 provinces, every district name (with the province plate
and the elections it exists in, because names repeat across provinces and districts move between
provinces over time), the party / candidate spellings per election and the referendum options.

`EntityIndex.from_db(db)` builds it from the live database; `EntityIndex.from_snapshot()` loads the
committed copy in `data/varliklar.json` (same content, used when no DB is reachable, e.g. for the
retrieval placeholders and the unit tests). `scripts/build_varliklar.py` regenerates the snapshot and
a DB-backed test checks that it is still current.

`find_mentions(question)` returns every recognised mention with its span; the template layer decides
whether the set of mentions is unambiguous enough to answer.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .turkce import Token, fold, suffix_match, tokenize

SNAPSHOT = Path(__file__).resolve().parent / "data" / "varliklar.json"

# ---------------------------------------------------------------------------- static knowledge
IL_ALIASES = {"afyon": 3, "maras": 46, "urfa": 63, "antep": 27, "icel": 33, "elaziz": 23, "hakkari": 30}

# (alias, party code, case_sensitive). Longest aliases win; case-sensitive ones are matched against the
# original spelling ("İYİ" is the party, "en iyi" is not; "DEM" vs "dem").
PARTY_ALIASES: list[tuple[str, str, bool]] = [
    ("Adalet ve Kalkınma Partisi", "AK Parti", False), ("Adalet ve Kalkınma", "AK Parti", False),
    ("AK Parti", "AK Parti", False), ("AKP", "AK Parti", False),
    ("Cumhuriyet Halk Partisi", "CHP", False), ("CHP", "CHP", False),
    ("Milliyetçi Hareket Partisi", "MHP", False), ("MHP", "MHP", False),
    ("İYİ Parti", "İYİ Parti", False), ("İyi Parti", "İYİ Parti", False), ("İYİ", "İYİ Parti", True),
    ("Halkların Demokratik Partisi", "HDP", False), ("HDP", "HDP", False),
    ("Yeşil Sol Parti", "YEŞİL SOL", False), ("Yeşil Sol", "YEŞİL SOL", False), ("YSP", "YEŞİL SOL", True),
    ("DEM Parti", "DEM Parti", False), ("DEM", "DEM Parti", True),
    ("Yeniden Refah Partisi", "YENİDEN REFAH", False), ("Yeniden Refah", "YENİDEN REFAH", False),
    ("Refah Partisi", "RP", False), ("Refah", "RP", False),
    ("Zafer Partisi", "ZP", False), ("Memleket Partisi", "MEMLEKET", False), ("Memleket", "MEMLEKET", True),
    ("Türkiye İşçi Partisi", "TİP", False), ("TİP", "TİP", True),
    ("Saadet Partisi", "SP", False), ("Saadet", "SP", False),
    ("Büyük Birlik Partisi", "BBP", False), ("BBP", "BBP", False),
    ("Demokratik Sol Parti", "DSP", False), ("DSP", "DSP", False),
    ("Doğru Yol Partisi", "DYP", False), ("Doğru Yol", "DYP", False), ("DYP", "DYP", False),
    ("Anavatan Partisi", "ANAP", False), ("Anavatan", "ANAP", False), ("ANAP", "ANAP", False),
    ("Fazilet Partisi", "FP", False), ("Fazilet", "FP", False),
    ("Sosyaldemokrat Halkçı Parti", "SHP", False), ("SHP", "SHP", False),
    ("Demokrat Parti", "DP", False), ("Demokratik Parti", "DP", False), ("DP", "DP", True),
    ("Adalet Partisi", "AP", False), ("AP", "AP", True),
    ("Milli Selamet Partisi", "MSP", False), ("MSP", "MSP", True),
    ("Halkçı Parti", "HP", False), ("Milliyetçi Demokrasi Partisi", "MDP", False), ("MDP", "MDP", True),
    ("HADEP", "HADEP", False), ("DEHAP", "DEHAP", False), ("DTP", "DTP", True), ("BDP", "BDP", True),
    ("HÜDA PAR", "HÜDAPAR", False), ("HÜDAPAR", "HÜDAPAR", False), ("Hüda Par", "HÜDAPAR", False),
    ("Vatan Partisi", "VATAN", False), ("DEVA Partisi", "DEVA", False), ("DEVA", "DEVA", True),
    ("Gelecek Partisi", "Gelecek Partisi", False),
    ("Bağımsızlar", "Bağımsız", False), ("Bağımsız", "Bağımsız", False),
]
# the HDP line changed its ballot name; asked by its old/new name, use the one on that election's ballot
PARTY_SUCCESSION = [("HDP", "YEŞİL SOL", "DEM Parti")]

# candidate surnames that are also ordinary words need a capital letter ("ince" = thin)
CANDIDATE_NEEDS_CAPITAL = {"ince"}
# district names that are also common words / regions / people: only recognised next to their province
WEAK_ILCE = {
    "merkez", "genc", "olur", "orta", "kale", "han", "cay", "tut", "of", "ulus", "hani", "arac", "bala", "kose",
    "mut", "bor", "kulu", "emet", "egil", "guce", "ula", "sur", "can", "cal", "cat", "kas", "pazar", "saray",
    "kemer", "aksu", "imamoglu", "marmara", "akdeniz", "yenice", "kazan", "ulas", "enez", "lice", "kulp",
    "palu", "kula", "soma", "bayat", "ortakoy", "evren", "eruh", "zara", "biga", "goksun", "ilic", "kigi",
    "agin", "sason", "gonen", "eregli", "golbasi", "yenisehir", "edremit", "ayvacik", "aydincik",
}


@dataclass(frozen=True)
class Election:
    id: int
    kod: str
    tur: str
    yil: int
    ad: str


@dataclass(frozen=True)
class Mention:
    kind: str            # il | ilce | parti | aday | secenek | belirsiz (weak district name without its il)
    value: object        # il: plaka; ilce: name; parti/aday/secenek: canonical code
    start: int
    end: int
    text: str
    extra: tuple = ()    # ilce: tuple of plates where the name exists


@dataclass
class _Entry:
    tokens: tuple[str, ...]
    kind: str
    value: object
    case_sensitive: bool = False
    original: tuple[str, ...] = ()
    needs_capital: bool = False


@dataclass
class EntityIndex:
    elections: list[Election]
    iller: dict[int, str]                                 # plaka -> ad
    ilceler: dict[str, dict[int, set[str]]]               # ilçe ad -> {plaka: {seçim kodları}}
    parties: dict[str, set[str]]                          # seçim kodu -> aday_parti değerleri
    _entries: list[_Entry] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ construction
    def __post_init__(self):
        self.by_kod = {e.kod: e for e in self.elections}
        self.candidates = sorted({p for k, ps in self.parties.items()
                                  if self.by_kod.get(k) and self.by_kod[k].tur == "cumhurbaskanligi"
                                  for p in ps})
        all_parties = set().union(*self.parties.values()) if self.parties else set()
        self.all_parties = all_parties - set(self.candidates)
        self._build_entries()

    def _build_entries(self) -> None:
        e: list[_Entry] = []
        il_folds = {fold(ad): plaka for plaka, ad in self.iller.items()}
        for f, plaka in list(il_folds.items()) + list(IL_ALIASES.items()):
            e.append(_Entry(tuple(f.split()), "il", plaka))
        for ad in self.ilceler:
            f = fold(ad)
            if "merkez" in f or "(" in ad or f in il_folds or f in IL_ALIASES:
                continue
            e.append(_Entry(tuple(f.split()), "ilce", ad))
        for alias, code, cs in PARTY_ALIASES:
            e.append(_Entry(tuple(fold(alias).split()), "parti", code, cs, tuple(alias.split())))
        for name in self.candidates:
            parts = name.split()
            e.append(_Entry(tuple(fold(name).split()), "aday", name))
            e.append(_Entry((fold(parts[-1]),), "aday", name, needs_capital=fold(parts[-1]) in CANDIDATE_NEEDS_CAPITAL))
            if len(parts) == 3:  # "Tayyip Erdoğan"
                e.append(_Entry(tuple(fold(" ".join(parts[1:])).split()), "aday", name))
        e.append(_Entry(("evet",), "secenek", "Evet"))
        e.append(_Entry(("hayir",), "secenek", "Hayır"))
        # longest first, so "Yeniden Refah" wins over "Refah" and "Recep Tayyip Erdoğan" over "Erdoğan"
        e.sort(key=lambda x: (-len(x.tokens), -sum(map(len, x.tokens))))
        self._entries = e

    @classmethod
    def from_rows(cls, elections, iller, ilceler, parties) -> "EntityIndex":
        """elections: [(id, kod, tur, yil, ad)], iller: [(plaka, ad)], ilceler: [(ad, plaka, [kod...])],
        parties: [(kod, aday_parti)]"""
        el = [Election(int(i), k, t, int(y), a) for i, k, t, y, a in elections]
        il = {int(p): a for p, a in iller}
        ilc: dict[str, dict[int, set[str]]] = {}
        for ad, plaka, kods in ilceler:
            ilc.setdefault(ad, {}).setdefault(int(plaka), set()).update(kods)
        pt: dict[str, set[str]] = {}
        for kod, p in parties:
            pt.setdefault(kod, set()).add(p)
        return cls(el, il, ilc, pt)

    @classmethod
    def from_db(cls, db) -> "EntityIndex":
        big = 100_000
        el = db.run("SELECT id, kod, tur, yil, ad FROM secim ORDER BY id", big).rows
        kod_by_id = {r[0]: r[1] for r in el}
        il = db.run("SELECT DISTINCT b.plaka, b.ad FROM birim b JOIN secim s ON s.id = b.secim_id "
                    "WHERE b.seviye = 'il' AND s.kod = '2023' ORDER BY b.plaka", big).rows
        ilc = db.run("SELECT b.ad, b.plaka, GROUP_CONCAT(DISTINCT b.secim_id) FROM birim b "
                     "WHERE b.seviye = 'ilce' AND b.plaka IS NOT NULL GROUP BY b.ad, b.plaka", big).rows
        pt = db.run("SELECT DISTINCT s.kod, o.aday_parti FROM oy o JOIN birim b ON b.id = o.birim_id "
                    "JOIN secim s ON s.id = b.secim_id WHERE b.seviye IN ('il','yurtdisi')", big).rows
        ilceler = [(ad, plaka, [kod_by_id[int(i)] for i in str(ids).split(",") if i]) for ad, plaka, ids in ilc]
        return cls.from_rows(el, il, ilceler, pt)

    def to_snapshot(self) -> dict:
        return {
            "elections": [[e.id, e.kod, e.tur, e.yil, e.ad] for e in self.elections],
            "iller": [[p, a] for p, a in sorted(self.iller.items())],
            # the elections a district exists in, as a bit mask over secim.id (keeps the file small)
            "ilceler": [[ad, p, sum(1 << self.by_kod[k].id for k in kods)]
                        for ad, ps in sorted(self.ilceler.items()) for p, kods in sorted(ps.items())],
            "parties": {k: sorted(v) for k, v in self.parties.items()},
        }

    @classmethod
    def from_snapshot(cls, path: Path = SNAPSHOT) -> "EntityIndex":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        parties = [(k, p) for k, ps in d["parties"].items() for p in ps]
        kod_by_id = {e[0]: e[1] for e in d["elections"]}
        ilceler = [(ad, p, [k for i, k in kod_by_id.items() if mask >> i & 1]) for ad, p, mask in d["ilceler"]]
        return cls.from_rows(d["elections"], d["iller"], ilceler, parties)

    @classmethod
    def load(cls, db=None) -> "EntityIndex":
        """From the DB when possible (the source of truth), otherwise from the committed snapshot."""
        if db is not None:
            try:
                return cls.from_db(db)
            except Exception:
                pass
        return cls.from_snapshot()

    # ------------------------------------------------------------------ lookup helpers
    def ilce_plates(self, name: str, kod: str | None = None) -> set[int]:
        plates = self.ilceler.get(name, {})
        return {p for p, kods in plates.items() if kod is None or kod in kods}

    def election_has(self, kod: str, party: str) -> bool:
        return party in self.parties.get(kod, set())

    def resolve_party(self, code: str, kod: str) -> str | None:
        """Ballot spelling of `code` in election `kod` (HDP → YEŞİL SOL in 2023), or None if it did not run."""
        if self.election_has(kod, code):
            return code
        for line in PARTY_SUCCESSION:
            if code in line:
                for alt in line:
                    if self.election_has(kod, alt):
                        return alt
        return None

    # ------------------------------------------------------------------ recognition
    def find_mentions(self, question: str) -> list[Mention]:
        toks = tokenize(question)
        used = [False] * len(toks)
        out: list[Mention] = []
        for i in range(len(toks)):
            if used[i]:
                continue
            for entry in self._entries:
                n = len(entry.tokens)
                if i + n > len(toks) or any(used[i:i + n]):
                    continue
                window = toks[i:i + n]
                if not self._match(entry, window):
                    continue
                for j in range(i, i + n):
                    used[j] = True
                start, end = window[0].start, window[-1].end
                extra = tuple(sorted(self.ilceler.get(entry.value, {}))) if entry.kind == "ilce" else ()
                out.append(Mention(entry.kind, entry.value, start, end, question[start:end], extra))
                break
        out.sort(key=lambda m: m.start)
        return self._drop_weak_ilce(out)

    @staticmethod
    def _match(entry: _Entry, window: list[Token]) -> bool:
        for k, (want, tok) in enumerate(zip(entry.tokens, window)):
            last = k == len(entry.tokens) - 1
            if entry.case_sensitive:
                if tok.text != entry.original[k]:
                    return False
                continue
            if last and not tok.suffix:
                if not suffix_match(tok.fold, want):
                    return False
            elif tok.fold != want:
                return False
        if entry.needs_capital and not window[0].capitalized:
            return False
        return True

    def _drop_weak_ilce(self, mentions: list[Mention]) -> list[Mention]:
        plates = {m.value for m in mentions if m.kind == "il"}
        keep = []
        for m in mentions:
            if m.kind == "ilce" and fold(m.value) in WEAK_ILCE and not (set(m.extra) & plates):
                # a common word, or a district name that needs its province: kept as an unresolved place,
                # so the template layer falls through instead of answering at the wrong level
                m = Mention("belirsiz", m.value, m.start, m.end, m.text, m.extra)
            keep.append(m)
        return keep


_INDEX: EntityIndex | None = None


def default_index() -> EntityIndex:
    """Process-wide snapshot index (no DB needed)."""
    global _INDEX
    if _INDEX is None:
        _INDEX = EntityIndex.from_snapshot()
    return _INDEX


YEAR_RE = re.compile(r"(?<!\d)(19[4-9]\d|20[0-4]\d)(?!\d)")
