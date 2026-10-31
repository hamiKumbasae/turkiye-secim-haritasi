"""Deterministic template layer: the most frequent question patterns answered without an LLM.

The patterns come from eval/soru_kaliplari.yaml (ranked by how often people ask them). A question is
parsed into slots — election(s), place, party/candidate/option, target level (il/ilçe/mahalle), N,
direction, threshold — with the entity lexicon from the database (see entities.py). A template only
answers when every slot it needs is filled **unambiguously**; anything else (two possible elections,
a district name that exists in several provinces, a negation, an alliance, a yes/no question, an
unknown place name …) returns None and the question falls through to the LLM (hybrid mode) or gets an
honest "no template" refusal (template mode).

Every template produces plain SQL over `secim`, `birim`, `oy` which the pipeline sends through the
same `safety.validate_sql` path as model-written SQL. Values put into SQL come from the lexicon
(DB spellings), never from the question text, apart from integers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from .db import QueryResult
from .entities import PARTY_SUCCESSION, YEAR_RE, Election, EntityIndex, Mention
from .formatting import tr_number
from .turkce import NUMBER_WORDS, SUFFIXES, Token, fold, tokenize

FROM_OY = "FROM oy o JOIN birim b ON b.id = o.birim_id JOIN secim s ON s.id = b.secim_id"
FROM_BIRIM = "FROM birim b JOIN secim s ON s.id = b.secim_id"
NATIONAL = "b.seviye IN ('il','yurtdisi')"
# the 30 metropolitan municipalities (no flag in the data; see prompts.DOMAIN_NOTES)
BUYUKSEHIR = (1, 6, 7, 9, 10, 16, 20, 21, 25, 26, 27, 31, 33, 34, 35, 38, 41, 42, 44, 45, 46, 47, 48, 52, 54, 55,
              59, 61, 63, 65)
NON_PARTY = ("Diğer", "Cumhur İttifakı", "Millet İttifakı", "Ata İttifakı", "Emek ve Özgürlük İttifakı",
             "Sosyalist Güç Birliği İttifakı")


def q(value) -> str:
    """SQL string literal (values come from the DB lexicon; quotes escaped anyway)."""
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def qlist(values) -> str:
    return ", ".join(q(v) for v in values)


@dataclass
class TemplateMatch:
    template: str                         # pattern id, e.g. 'birim-sonucu'
    sql: str | None = None
    explanation: str = ""
    refusal: str | None = None
    answer_fn: Callable[[QueryResult], str] | None = field(default=None, repr=False)

    def answer(self, result: QueryResult) -> str:
        from .llm import template_answer

        if self.answer_fn is not None and result.rows:
            try:
                return self.answer_fn(result)
            except Exception:  # pragma: no cover - a formatting bug must not lose the data
                pass
        return template_answer(result)


class NoMatch(Exception):
    """Raised internally when a slot is missing or ambiguous."""


# ---------------------------------------------------------------------------- cue vocabulary
# All cue regexes run on the folded token string (" 2023 ikinci turda umraniye ... ").
def _rx(p: str) -> re.Pattern:
    return re.compile(p)


CUE = {
    "cb": _rx(r" cumhurbask"),
    "tur2": _rx(r" (ikinci|2) tur"),
    "tur1": _rx(r" (ilk|birinci|1) tur"),
    "ref": _rx(r" (referandum|halkoylama|anayasa degisikli)"),
    "yerel": _rx(r" (yerel|belediye|baskanlig|buyuksehir|mahalli)"),
    "genel": _rx(r" (genel secim|milletvekili secim|milletvekilligi secim|meclis secim|genel se)"),
    "national": _rx(r" (turkiye genel|turkiye capinda|ulke genel|ulke capinda|tum turkiye|turkiye\b|ulusal)"),
    "abroad": _rx(r" (yurt disi|yurtdisi|gurbet)(?! dahil)(?! ve turkiye)"),
    "domestic": _rx(r" (yurt ici|yurtici|yurt disi haric|yurtdisi haric)"),
    "metro": _rx(r" buyuksehir"),
    "win": _rx(r" (kazan|birinci|ilk sira|onde|galip|kim aldi|lider|ilk parti)"),
    "out": _rx(r" (cikt|cikan)"),
    "count": _rx(r" (kac|kacinda|kacar|sayisi)\b"),
    "share": _rx(r" (yuzde|oran|kac oy|ne kadar|oy ald|oyu|oylar|aldi|aldig|almis|aldik|oy say|puan)"),
    "vekil": _rx(r"(vekil|sandalye|mebus)(?!\w* secim)"),
    "katilim": _rx(r" (katilim|sandiga git|oy kullanma oran)"),
    "secmen": _rx(r" (secmen|kayitli)"),
    "sandik": _rx(r" (kac sandik|sandik sayi)"),
    "fark": _rx(r" (fark|aradaki|onunde|onundey|gerisinde|geride)"),
    "change": _rx(r" (degis|artt|artis|artir|azalt|yukselt|azal|dustu|dusus|dustug|yukseld|geriled|kaybett|kaybed|kayb|kazanc|eridi|erime)"),
    "up": _rx(r" (artt|artis|artir|yukseld|yukselt|kazanc|kazand)"),
    "down": _rx(r" (azal|azalt|dustu|dusus|dustug|geriled|kaybett|kaybed|kayb|eridi|erime)"),
    "series": _rx(r" (yillara gore|yil yil|bu yana|beri|itibaren|bugune|gunumuze|seyrett|seyri|karne|tum secim|her secim|"
                  r"butun secim|tarihi boyunca|zaman icinde|yillar icinde|nasil seyr)"),
    "list": _rx(r" (sonuc|oranlari|oylar|partiler|adaylar|dagil|kim kac|hangi parti kac|hangi aday kac|kacar|"
                r"ilk \w+ parti|siralama|tablo)"),
    "who": _rx(r" (kim|hangi parti|hangi aday|hangisi|kimdi|ne cikti)"),
    "desc": _rx(r" en (yuksek|cok|fazla|iyi|guclu|basarili|buyuk|kalabalik)"),
    "asc": _rx(r" en (dusuk|az|zayif|kotu|basarisiz|kucuk)"),
    "close": _rx(r" (cekismeli|kil payi|en az fark|en yakin|basa bas)"),
    "top2": _rx(r" (birinci ile ikinci|kazanan ile ikinci|ilk iki|birinci ve ikinci|ikinci arasi)"),
    "since": _rx(r" (bu yana|beri|itibaren|sonra|bugune|gunumuze)"),
    "range": _rx(r" (arasi|arasinda)"),
    "total": _rx(r" (toplam|meclis|kac milletvekili sec|kac vekil sec|kac milletvekili var|kac vekili var|"
                 r"kac milletvekili cikar|kac vekil cikar)"),
}

# Questions with any of these go to the LLM (or are refused in template mode): negations, alliances,
# yes/no questions, averages, regions, thresholds outside the top-N template, other ranks …
BLOCK_STEMS = _rx(r" (baraj|cizgi|resmi|yakin|ittifak|ortalama|medyan|bolge|karsilastir|kiyasla|koalisyon|hukumet|"
                  r"iktidar|muhalefet|yorum|rekor|tarihin|simdi|gunumuz|ortalam|yuzdelik|nufus|oyunu kim)")
BLOCK = _rx(
    r" (hic|degil|ittifak|ortalama|medyan|bolge|bolgesi|mi|mu|misin|baraj|hem|veya|ya da|yoksa|ucuncu|bugun|son secim|en son|"
    r"dorduncu|sonuncu|son sira|ikinci parti|ikinci olan|ikinci sira|ikinci geldi|ikinci cikti|ilk kez|"
    r"ilk defa|neden|niye|ne zaman|hangi yil|hangi secim|kac kez|kac defa|kac kere|kac secim|"
    r"tum zaman|tarihin|rekor|sadece|yalniz|haric|karsilastir|kiyasla|gore daha|daha cok|daha fazla|"
    r"daha az|ustunde mi|tek basina|koalisyon|hukumet|iktidar|muhalefet|yorumla|neydi sebebi|aday mi)\b"
    r"|amadi|emedi|amayan|emeyen|amamis|ememis|olamad|olmayan|siz | yuzde \d+ ?(den|dan)? ?(fazla|ust|uzer|alti|asagi|az|gec|as)"
)

DOMAIN_STEMS = ("cumhurbask", "secim", "milletvekil", "genel", "yerel", "referandum", "anayasa", "belediye",
                "buyuksehir", "mahalle", "ilce", "parti", "tur", "meclis", "turkiye", "yurt", "ysk", "tbmm",
                "evet", "hayir", "hangi", "kac", "en", "il", "ak", "chp", "mhp")
MONTHS = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6, "temmuz": 7, "agustos": 8,
          "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}
DAY_MONTH = {(14, "mayis"): "14mayis", (28, "mayis"): "28mayis", (7, "haziran"): "2015Haziran",
             (1, "kasim"): "2015Kasim", (24, "haziran"): "24haziran", (31, "mart"): "31mart"}

# ---------------------------------------------------------------------------- data refusals
VERI_YOK: list[tuple[re.Pattern, str]] = [
    (_rx(r" (sandik (bazinda|sonuc|numara)|hangi sandik|sandiginda|sandik sandik)"),
     "Veritabanında sandık bazında sonuç yok; en küçük birim mahalledir (2009'dan bu yana)."),
    (_rx(r" (secim bolgesi|\d+ (nci |inci |uncu )?bolge)"),
     "Seçim bölgesi (ör. İstanbul 1. bölge) kırılımı veride yok; il, ilçe ve mahalle sonuçları var."),
    (_rx(r" anket"), "Anket verisi yok; yalnız kesin seçim sonuçları var."),
    (_rx(r" (yasinda|yas grub|yas ortalama|genc secmen|gencler|ilk kez oy|ilk defa oy|kadin secmen|kadinlar|"
         r"erkek secmen|cinsiyet|egitim duzey|etnik|kurt secmen|alevi|emekli)"),
     "Seçmenlerin yaş, cinsiyet, eğitim gibi profil bilgisi veride yok; yalnız sonuçlar ve seçmen sayısı var."),
    (_rx(r" (gecersiz oy|gecersiz say|bos oy|gecersiz)"), "Geçersiz oy sayısı veritabanında saklanmıyor."),
    (_rx(r" (belediye meclis|il genel meclis|meclis uye|muhtar|belde)"),
     "Yerel seçimlerde yalnız belediye başkanlığı sonuçları var; belediye meclisi, il genel meclisi, belde ve "
     "muhtarlık oyları yok."),
    (_rx(r" (ara secim|senato|kurucu meclis)"), "Ara seçimler ve senato seçimleri veritabanında yok."),
    (_rx(r" (yenilen|yenileme|23 haziran|iptal edilen secim)"),
     "Yenilenen seçimler (ör. 23 Haziran 2019 İstanbul) veride yok; 2019 İstanbul satırı 31 Mart seçimidir."),
    (_rx(r" ((milletvekil\w*|vekil\w*|aday\w*|baskan\w*) (isim|ad)\w*|isimleri|kimler secildi|aday listesi|"
         r"kimdir|kac yasinda|biyografi|ne is yap|meslegi|daha once ne)"),
     "Milletvekili, belediye başkanı ya da aday adları ve kişisel bilgiler veride yok; parti ve aday oyları var."),
    (_rx(r" (neden|niye|nicin|sebebi|nasil ogren|nereden ogren|nasil yapilir|kaydim|okulda oy|hangi okul)"),
     "Bu bir yorum ya da süreç sorusu; ben yalnız seçim sonuçlarını veritabanından sorgulayabilirim."),
    (_rx(r" (gelecek secim|bir sonraki secim|kim kazanacak|kazanir mi|tahmin|hava durumu|hava nasil|yarin|futbol|"
         r" mac |dolar|enflasyon)"),
     "Bu soru veritabanındaki geçmiş seçim sonuçlarıyla yanıtlanamaz."),
]


# ---------------------------------------------------------------------------- parsed question
@dataclass
class Unit:
    level: str                 # il | ilce | yurtdisi | ulusal
    plaka: int | None = None
    ad: str | None = None
    label: str = "Türkiye geneli"

    @property
    def aggregate(self) -> bool:
        """Türkiye geneli (il + yurt dışı) or yurt içi (iller): a sum over province rows."""
        return self.level in ("ulusal", "yurtici")

    def where(self, alias: str = "b") -> str:
        if self.level == "il":
            return f"{alias}.seviye = 'il' AND {alias}.plaka = {int(self.plaka)}"
        if self.level == "ilce":
            return f"{alias}.seviye = 'ilce' AND {alias}.plaka = {int(self.plaka)} AND {alias}.ad = {q(self.ad)}"
        if self.level == "yurtdisi":
            return f"{alias}.seviye = 'yurtdisi'"
        if self.level == "yurtici":
            return f"{alias}.seviye = 'il'"
        return NATIONAL.replace("b.", f"{alias}.")


@dataclass
class Parsed:
    question: str
    tokens: list[Token]
    s: str                                 # " " + folded tokens + " "
    mentions: list[Mention]
    years: list[int]
    since: int | None
    until: int | None
    daymonth: list[str]
    n: int | None
    threshold: tuple[str, float] | None
    level: str | None                      # target level of a ranking/list: il | ilce | mahalle
    level_plural: bool

    def has(self, cue: str) -> bool:
        return bool(CUE[cue].search(self.s))

    def kinds(self, *kinds: str) -> list[Mention]:
        return [m for m in self.mentions if m.kind in kinds]


_LEVEL_WORDS = {
    "il": re.compile(r"^(il|ili|ilin|ilde|iller|illeri|illerde|illerin|ilden|illerden|ilinde|illerinde|sehir|"
                     r"sehirde|sehirler|sehirlerde|vilayet)$"),
    "ilce": re.compile(r"^ilce"),
    "mahalle": re.compile(r"^(mahalle|mah)"),
}


def _number(tok: Token) -> int | None:
    if tok.fold.isdigit():
        return int(tok.fold)
    return NUMBER_WORDS.get(tok.fold)


def parse(question: str, index: EntityIndex) -> Parsed:
    text = question.replace("%", " yüzde ")
    tokens = tokenize(text)
    mentions = index.find_mentions(text)
    s = " " + " ".join(t.fold for t in tokens) + " "
    years: list[int] = []
    since = until = None
    daymonth: list[str] = []
    fixed = []
    for t in tokens:
        m = re.fullmatch(r"(19[4-9]\d|20[0-4]\d)([a-z]+)", t.fold)
        if m and m.group(2) in SUFFIXES:
            t = Token(t.text[:4], m.group(1), t.start, t.start + 4, m.group(2))
        fixed.append(t)
    tokens = fixed
    for i, t in enumerate(tokens):
        nxt = tokens[i + 1].fold if i + 1 < len(tokens) else ""
        prev = tokens[i - 1].fold if i else ""
        if YEAR_RE.fullmatch(t.fold):
            y = int(t.fold)
            if prev in MONTHS and i >= 2 and tokens[i - 2].fold.isdigit():
                pass  # "14 Mayıs 2023": the day-month pair already noted below, the year is still a year
            rest = " ".join(x.fold for x in tokens[i + 1:i + 3])
            if t.suffix in ("den", "dan", "ten", "tan") and re.match(r"(bu yana|beri|itibaren|sonra|bugune|gunumuze)", rest):
                since = y
                continue
            years.append(y)
        elif re.fullmatch(r"\d{2}", t.fold) and (nxt.startswith("secim") or t.suffix and nxt.startswith("secim")):
            y = int(t.fold)
            years.append(1900 + y if y >= 50 else 2000 + y)
        elif t.fold.isdigit() and nxt in MONTHS and (int(t.fold), nxt) in DAY_MONTH:
            daymonth.append(DAY_MONTH[(int(t.fold), nxt)])
    if 2015 in years or re.search(r" (haziran|kasim) ", s) and " 2015 " in s:
        if " haziran " in s:
            daymonth.append("2015Haziran")
        if " kasim " in s:
            daymonth.append("2015Kasim")
    if CUE["range"].search(s) and len(years) == 2 and since is None:
        since, until = min(years), max(years)

    # N: "ilk 3", "5 il", "en yüksek üç", "3 mahalle"
    n = None
    for i, t in enumerate(tokens):
        v = _number(t)
        if v is None or YEAR_RE.fullmatch(t.fold) or v > 100 or v <= 0:
            continue
        prev = tokens[i - 1].fold if i else ""
        nxt = tokens[i + 1].fold if i + 1 < len(tokens) else ""
        if prev == "ilk" and not nxt.startswith("tur") or prev in ("yuksek", "dusuk", "cok", "az", "fazla") \
                or any(p.match(nxt) for p in _LEVEL_WORDS.values()) or nxt.startswith("parti") or nxt == "aday":
            if not (nxt.startswith("tur") or prev == "yuzde"):
                n = v
                break

    threshold = None
    m = re.search(r" yuzde (\d+(?:[.,]\d+)?) ?(?:nin|nun|in|un|den|dan|ten|tan|i|u)? ?"
                  r"(ust|uzer|fazla|gecti|gectig|asti|astig|alti|altin|asagi|az)", s)
    if m:
        threshold = (">" if m.group(2) in ("ust", "uzer", "fazla", "gecti", "gectig", "asti", "astig") else "<",
                     float(m.group(1).replace(",", ".")))

    level, plural = None, False
    if re.search(r" buyuksehir(ler|i|in|de|e|leri|lerde|lerin)? ", s) and not [m for m in mentions if m.kind == "il"]:
        level, plural = "il", True
    for t in tokens:
        for lv, rx in _LEVEL_WORDS.items():
            if rx.match(t.fold) and not (lv == "il" and t.fold == "il" and False):
                if level is None:
                    level = lv
                    plural = "ler" in t.fold or "lar" in t.fold
    return Parsed(question, tokens, s, mentions, years, since, until, daymonth, n, threshold, level, plural)


# ---------------------------------------------------------------------------- election resolution
def _type_hint(p: Parsed) -> str | None:
    hints = set()
    if p.has("cb") or p.has("tur1") or p.has("tur2") or p.kinds("aday"):
        hints.add("cumhurbaskanligi")
    if p.has("ref") or p.kinds("secenek"):
        hints.add("referandum")
    if p.has("yerel"):
        hints.add("yerel")
    if p.has("genel"):
        hints.add("genel")
    if len(hints) > 1:
        raise NoMatch("çelişen seçim türü")
    return hints.pop() if hints else None


def resolve_elections(p: Parsed, index: EntityIndex, default_party_type: bool = True) -> list[Election]:
    hint = _type_hint(p)
    if hint is None and default_party_type and p.kinds("parti"):
        hint = "partili"            # a party was asked → general election if that year had one, else local
    out: list[Election] = []
    years = list(p.years)
    if not years:
        dm = set(p.daymonth)
        if "28mayis" in dm or (p.has("tur2") and hint == "cumhurbaskanligi"):
            return [index.by_kod["2023cb2tur"]]
        if "14mayis" in dm:
            return [index.by_kod["2023cb1tur" if hint == "cumhurbaskanligi" else "2023"]]
        if p.has("tur1") and hint == "cumhurbaskanligi":
            return [index.by_kod["2023cb1tur"]]
        if "2015Haziran" in dm or "2015Kasim" in dm:
            return [index.by_kod[k] for k in ("2015Haziran", "2015Kasim") if k in dm]
        return []
    for y in years:
        cands = [e for e in index.elections if e.yil == y]
        if not cands:
            raise NoMatch(f"{y} seçimi yok")
        if hint in ("genel", "yerel", "referandum", "cumhurbaskanligi"):
            cands = [e for e in cands if e.tur == hint]
        elif hint == "partili":
            cands = [e for e in cands if e.tur == "genel"] or [e for e in cands if e.tur == "yerel"]
        else:
            cands = [e for e in cands if e.tur == "genel"] or cands
        if len(cands) > 1:
            dm = set(p.daymonth)
            if y == 2023:
                if p.has("tur2") or "28mayis" in dm:
                    cands = [e for e in cands if e.kod == "2023cb2tur"]
                elif p.has("tur1") or "14mayis" in dm:
                    cands = [e for e in cands if e.kod == "2023cb1tur"]
            if y == 2015:
                both = [e for e in cands if e.kod in dm]
                if len(both) == 2:
                    out.extend(e for e in both if e not in out)
                    continue
                cands = both
        if len(cands) != 1:
            raise NoMatch(f"{y}: seçim belirsiz")
        if cands[0] not in out:
            out.append(cands[0])
    return out


def election_label(e: Election) -> str:
    return {
        "genel": f"{e.yil} genel seçimi" if e.kod not in ("2015Haziran", "2015Kasim") else f"{e.ad} genel seçimi",
        "yerel": f"{e.yil} yerel seçimi",
        "referandum": f"{e.yil} referandumu",
        "cumhurbaskanligi": f"{e.yil} cumhurbaşkanlığı seçimi" + (
            " (1. tur)" if e.kod.endswith("1tur") else " (2. tur)" if e.kod.endswith("2tur") else ""),
    }[e.tur]


# ---------------------------------------------------------------------------- answer helpers
def _pct(v) -> str:
    return "%" + tr_number(float(v)) if v is not None else "—"


def _num(v) -> str:
    return tr_number(int(v)) if v is not None else "—"


def _caveats(e: Election, national: bool, party_share: bool, unit: Unit | None = None) -> str:
    notes = []
    if party_share and e.kod in ("2018", "2023"):
        notes.append("Yalnız ittifaka verilen oylar partilere dağıtılmadığı için parti oranları YSK'nın resmî "
                     "rakamından biraz düşüktür.")
    if national and e.tur == "yerel":
        notes.append("Bu, il (büyükşehir/il merkezi) belediye başkanlığı oylarının toplamıdır; resmî Türkiye geneli "
                     "yerel seçim oranı belediye meclisi oyudur ve veride yok.")
    if unit and unit.level == "il" and unit.plaka == 34 and e.kod == "2019yerel":
        notes.append("2019 İstanbul sonucu iptal edilen 31 Mart seçimidir; 23 Haziran yenilemesi veride yok.")
    return (" " + " ".join(notes)) if notes else ""


# ---------------------------------------------------------------------------- the engine
class TemplateEngine:
    """`match(question, history)` → TemplateMatch (SQL or refusal) or None (fall through)."""

    name = "şablon"

    def __init__(self, index: EntityIndex | None = None, db=None):
        self._index = index
        self._db = db

    @property
    def index(self) -> EntityIndex:
        if self._index is None:
            self._index = EntityIndex.load(self._db)
        return self._index

    # ------------------------------------------------------------------ public
    def match(self, question: str, history: list | None = None) -> TemplateMatch | None:
        question = (question or "").strip()
        if not question:
            return None
        hit = self._match_one(question)
        if hit is not None or not history:
            return hit
        virtual = self.follow_up(question, history[-1].question)
        if virtual and virtual != question:
            hit = self._match_one(virtual)
            if hit is not None and hit.sql:
                hit.explanation = f"Takip sorusu, önceki soruyla birleştirildi: “{virtual}”. " + hit.explanation
                return hit
        return None

    def follow_up(self, question: str, previous: str) -> str | None:
        """'ya 2023'te?' after '2018'de İzmir'de birinci parti?' → '2023'de İzmir'de birinci parti?'.
        Slots in the new question replace the same kind of slot in the previous one; new intent words
        (en yüksek, kaç ilde …) are appended."""
        toks = tokenize(question)
        if len(toks) > 9:
            return None
        cur = self.index.find_mentions(question)
        prev_m = self.index.find_mentions(previous)
        out = previous
        spans: list[tuple[int, int, str]] = []
        cur_years = [t for t in toks if YEAR_RE.fullmatch(t.fold)]
        if cur_years:
            prev_years = [m for m in YEAR_RE.finditer(previous)]
            if len(cur_years) != 1 or len(prev_years) != 1:
                return None
            spans.append((prev_years[0].start(), prev_years[0].end(), cur_years[0].text))
        groups = {"yer": ("il", "ilce", "belirsiz"), "aktor": ("parti", "aday", "secenek")}
        used_cur: set[int] = set()
        for kinds in groups.values():
            c = [m for m in cur if m.kind in kinds]
            pm = [m for m in prev_m if m.kind in kinds]
            if not c:
                continue
            if len(c) != 1 or len(pm) > 1:
                return None
            used_cur.add(c[0].start)
            if pm:
                spans.append((pm[0].start, pm[0].end, c[0].text))
            else:
                out_extra = c[0].text
                spans.append((len(previous), len(previous), " " + out_extra))
        for a, b, rep in sorted(spans, reverse=True):
            out = out[:a] + rep + out[b:]
        # intent words that are not slots: carry the rest of the new question along
        rest = " ".join(t.text for t in toks if not YEAR_RE.fullmatch(t.fold)
                        and fold(t.text) not in ("peki", "ya", "ve", "bir", "de", "da")
                        and not any(m.start <= t.start < m.end for m in cur))
        if rest and re.search(r"(en |kaç|hangi|nerede|katılım|vekil|ilçe|mahalle|il\b|iller)", rest, re.I):
            out = out.rstrip(" ?.") + "? " + rest
        if not spans and out == previous:
            return None
        return out

    # ------------------------------------------------------------------ matching
    def _match_one(self, question: str) -> TemplateMatch | None:
        p = parse(question, self.index)
        for rx, reason in VERI_YOK:
            if rx.search(p.s):
                return TemplateMatch("veri-yok", refusal=reason, explanation="Veride olmayan bir bilgi soruldu.")
        if any(y < 1950 for y in p.years):
            return TemplateMatch("veri-yok", refusal="Veritabanı 1950 seçimiyle başlar; daha önceki seçimler yok.")
        try:
            self._check_blockers(p)
            if p.has("change") and not p.has("series") and len(p.years) + len(p.daymonth) < 2:
                raise NoMatch("değişim sorusu, iki seçim yok")
            for t in (self.t_series, self.t_change, self.t_fark, self.t_vekil, self.t_katilim, self.t_secmen,
                      self.t_count_wins, self.t_top, self.t_where_first, self.t_unit_winner, self.t_results,
                      self.t_share):
                hit = t(p)
                if hit is not None:
                    return hit
        except NoMatch:
            return None
        return None

    def _check_blockers(self, p: Parsed) -> None:
        s = CUE["top2"].sub(" ", p.s)                        # "birinci ile ikinci" is a template, not a blocker
        if p.threshold:
            s = re.sub(r" yuzde \d+\S* ?\S*", " ", s)
        if BLOCK.search(s) or BLOCK_STEMS.search(s) or re.search(r"(?<!yurt) disinda", s):
            raise NoMatch("engelleyici ifade")
        if p.kinds("belirsiz"):
            raise NoMatch("belirsiz yer adı")
        mention_starts = {m.start for m in p.mentions}
        letters = [c for c in p.question if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) > 0.6 * len(letters):
            return                                           # ALL CAPS: capitals carry no information
        for i, t in enumerate(p.tokens):
            if not t.capitalized or t.start in mention_starts or any(m.start <= t.start < m.end for m in p.mentions):
                continue
            if t.fold in MONTHS or t.fold.isdigit() or any(t.fold.startswith(st) for st in DOMAIN_STEMS):
                continue
            if i == 0 and not t.suffix:
                continue
            raise NoMatch(f"tanınmayan özel ad: {t.text}")

    # ------------------------------------------------------------------ slot helpers
    def _one_election(self, p: Parsed) -> Election:
        els = resolve_elections(p, self.index)
        if len(els) != 1:
            raise NoMatch("tek seçim gerekli")
        return els[0]

    def _unit(self, p: Parsed, e: Election | None, allow_national: bool = True) -> Unit:
        ils = sorted({m.value for m in p.kinds("il")})
        ilces = sorted({m.value for m in p.kinds("ilce")})
        if p.has("domestic") and not (ils or ilces):
            return Unit("yurtici", label="yurt içi (iller toplamı)")
        if p.has("abroad"):
            if ils or ilces:
                raise NoMatch("yurt dışı + yer")
            return Unit("yurtdisi", label="yurt dışı")
        if len(ilces) > 1 or len(ils) > 1:
            raise NoMatch("birden çok yer")
        if ilces:
            plates = self.index.ilce_plates(ilces[0], e.kod if e else None)
            if ils:
                plates &= set(ils)
            if len(plates) != 1:
                raise NoMatch("ilçe belirsiz")
            plaka = plates.pop()
            return Unit("ilce", plaka, ilces[0], f"{ilces[0]} ({self.index.iller.get(plaka, plaka)})")
        if ils:
            return Unit("il", ils[0], self.index.iller[ils[0]], self.index.iller[ils[0]])
        if not allow_national:
            raise NoMatch("yer gerekli")
        return Unit("ulusal")

    def _actors(self, p: Parsed, e: Election) -> list[str]:
        """Party / candidate / option names as spelled on that election's ballot."""
        out = []
        for m in p.kinds("parti", "aday", "secenek"):
            v = self.index.resolve_party(str(m.value), e.kod)
            if v is None:
                raise NoMatch(f"{m.value} bu seçimde yok")
            if v not in out:
                out.append(v)
        return out

    @staticmethod
    def _need_no_level(p: Parsed, unit: Unit) -> None:
        if p.level and p.level != unit.level:
            raise NoMatch("hedef düzey var")

    def _scope_for_level(self, p: Parsed, e: Election, level: str) -> tuple[str, str, str, str]:
        """For rankings/lists at `level`: (FROM extra join, WHERE scope, name columns, scope label)."""
        unit = self._unit(p, e)
        if level == "il":
            if not unit.aggregate:
                raise NoMatch("il listesi için yer kapsamı olamaz")
            if p.has("metro"):
                if e.tur != "yerel":
                    raise NoMatch("büyükşehir yalnız yerel seçimde")
                return "", f"b.seviye = 'il' AND b.plaka IN ({', '.join(map(str, BUYUKSEHIR))})", "b.ad AS il", "büyükşehirlerde"
            return "", "b.seviye = 'il'", "b.ad AS il", "illerde"
        if level == "ilce":
            if unit.level == "il":
                return "", f"b.seviye = 'ilce' AND b.plaka = {unit.plaka}", "b.ad AS ilce", f"{unit.label} ilçelerinde"
            if unit.aggregate:
                return (" JOIN birim il ON il.secim_id = b.secim_id AND il.seviye = 'il' AND il.plaka = b.plaka",
                        "b.seviye = 'ilce'", "il.ad AS il, b.ad AS ilce", "ilçelerde")
            raise NoMatch("ilçe listesi kapsamı")
        if level == "mahalle":
            if unit.level != "ilce" or e.yil < 2009:
                raise NoMatch("mahalle için ilçe ve 2009+ gerekli")
            return (" JOIN birim i ON i.secim_id = b.secim_id AND i.seviye = 'ilce' AND i.geom_id = b.ust_geom_id",
                    f"b.seviye = 'mahalle' AND i.plaka = {unit.plaka} AND i.ad = {q(unit.ad)}", "b.ad AS mahalle",
                    f"{unit.label} mahallelerinde")
        raise NoMatch("düzey")

    # ------------------------------------------------------------------ templates
    def t_series(self, p: Parsed) -> TemplateMatch | None:
        if not p.has("series") or p.years and p.since is None:
            return None
        hint = _type_hint(p) or "genel"
        if hint == "referandum" or p.has("vekil") or p.has("secmen") or p.has("fark"):
            raise NoMatch("seri: desteklenmeyen ölçü")
        unit = self._unit(p, None)
        self._need_no_level(p, unit)
        cond = f"s.tur = {q(hint)}"
        if p.since:
            cond += f" AND s.yil >= {p.since}"
        if p.until:
            cond += f" AND s.yil <= {p.until}"
        actors = p.kinds("parti", "aday")
        span = f"{p.since}'den bu yana " if p.since else ""
        tur = {"genel": "genel", "yerel": "yerel", "cumhurbaskanligi": "cumhurbaşkanlığı"}[hint]
        if unit.level == "ilce" and len(self.index.ilce_plates(unit.ad)) > 1:
            raise NoMatch("ilçe zaman içinde başka ile geçmiş")
        if p.has("katilim") and not actors:
            if unit.aggregate:
                sql = (f"SELECT s.kod, ROUND(SUM(b.secmen * b.katilim) / SUM(b.secmen), 2) AS katilim {FROM_BIRIM} "
                       f"WHERE {cond} AND {unit.where()} AND b.katilim IS NOT NULL GROUP BY s.id, s.kod, s.yil "
                       f"ORDER BY s.yil, s.id")
            else:
                sql = f"SELECT s.kod, b.katilim {FROM_BIRIM} WHERE {cond} AND {unit.where()} ORDER BY s.yil, s.id"
            return TemplateMatch("zaman-serisi-oran", sql, f"{unit.label}: {span}{tur} seçimlerinde katılım.",
                                 answer_fn=lambda r: _series_answer(r, f"{unit.label} katılım ({tur} seçimleri)"))
        if len(actors) == 1:
            code = str(actors[0].value)
            line = next((ln for ln in PARTY_SUCCESSION if code in ln), (code,))
            names = qlist(line)
            if unit.aggregate:
                sql = (f"SELECT s.kod, ROUND(100 * SUM(CASE WHEN o.aday_parti IN ({names}) THEN o.oy ELSE 0 END) "
                       f"/ SUM(o.oy), 2) AS oran {FROM_OY} WHERE {cond} AND {unit.where()} "
                       f"GROUP BY s.id, s.kod, s.yil HAVING SUM(CASE WHEN o.aday_parti IN ({names}) THEN 1 ELSE 0 END) > 0 "
                       f"ORDER BY s.yil, s.id")
            else:
                sql = (f"SELECT s.kod, o.oran {FROM_OY} WHERE {cond} AND {unit.where()} "
                       f"AND o.aday_parti IN ({names}) ORDER BY s.yil, s.id")
            return TemplateMatch("zaman-serisi-oran", sql, f"{unit.label}: {code} oy oranı, {span}{tur} seçimleri.",
                                 answer_fn=lambda r: _series_answer(r, f"{unit.label}, {code} oy oranı"))
        if not actors and p.has("win") and not unit.aggregate:
            sql = f"SELECT s.kod, b.kazanan {FROM_BIRIM} WHERE {cond} AND {unit.where()} ORDER BY s.yil, s.id"
            return TemplateMatch("zaman-serisi-kazanan", sql, f"{unit.label}: {span}{tur} seçimlerinde birinci.",
                                 answer_fn=lambda r: f"{unit.label}, {tur} seçimlerinde birinci gelen: " +
                                 "; ".join(f"{k}: {w}" for k, w in r.rows[:25]) + ".")
        raise NoMatch("seri")

    def t_change(self, p: Parsed) -> TemplateMatch | None:
        if not p.has("change") or len(p.years) + len(p.daymonth) < 2:
            return None
        els = resolve_elections(p, self.index)
        if len(els) != 2 or els[0].tur != els[1].tur:
            raise NoMatch("iki aynı türde seçim gerekli")
        e1, e2 = sorted(els, key=lambda e: (e.yil, e.id))
        actors = p.kinds("parti", "aday", "secenek")
        if len(actors) != 1:
            raise NoMatch("tek aktör")
        a1 = self.index.resolve_party(str(actors[0].value), e1.kod)
        a2 = self.index.resolve_party(str(actors[0].value), e2.kod)
        if not a1 or not a2:
            raise NoMatch("aktör iki seçimde yok")
        c1, c2 = f"oran_{e1.kod}", f"oran_{e2.kod}"
        who = str(actors[0].value)
        if p.level and (p.has("desc") or p.has("asc")):
            if p.level not in ("il", "ilce") or self._unit(p, e2).level != "ulusal" and p.level == "il":
                raise NoMatch("değişim sıralaması")
            n = p.n or (None if p.level_plural else 1)
            down = p.has("down") and not p.has("up")
            up = p.has("up") and not p.has("down")
            if not (down or up):
                raise NoMatch("yön belirsiz")
            order = "ASC" if (down and p.has("desc")) or (up and p.has("asc")) else "DESC"
            key = "b2.plaka = b1.plaka" + (" AND b2.ad = b1.ad" if p.level == "ilce" else "")
            unit = self._unit(p, e2)
            scope = f" AND b2.plaka = {unit.plaka}" if unit.level == "il" and p.level == "ilce" else ""
            if unit.level not in ("ulusal", "il") or (unit.level == "il" and p.level == "il"):
                raise NoMatch("kapsam")
            name = "b2.ad AS il" if p.level == "il" else "b2.ad AS ilce"
            sql = (f"SELECT {name}, o1.oran AS {c1}, o2.oran AS {c2}, ROUND(o2.oran - o1.oran, 2) AS fark "
                   f"FROM oy o2 JOIN birim b2 ON b2.id = o2.birim_id JOIN secim s2 ON s2.id = b2.secim_id "
                   f"JOIN secim s1 ON s1.kod = {q(e1.kod)} "
                   f"JOIN birim b1 ON b1.secim_id = s1.id AND b1.seviye = {q(p.level)} AND {key} "
                   f"JOIN oy o1 ON o1.birim_id = b1.id AND o1.aday_parti = {q(a1)} "
                   f"WHERE s2.kod = {q(e2.kod)} AND b2.seviye = {q(p.level)}{scope} AND o2.aday_parti = {q(a2)} "
                   f"ORDER BY fark {order}" + (f" LIMIT {n}" if n else ""))
            return TemplateMatch("oy-degisimi", sql, f"{who} oy oranı değişimi {e1.kod} → {e2.kod}, {p.level} bazında.",
                                 answer_fn=lambda r: f"{who}, {election_label(e1)} → {election_label(e2)}: " + "; ".join(
                                     f"{row[0]} {_pct(row[1])} → {_pct(row[2])} ({tr_number(float(row[3]))} puan)"
                                     for row in r.rows[:10]) + ".")
        if p.level:
            raise NoMatch("düzey")
        unit = self._unit(p, e2)
        if unit.level == "ilce" and unit.plaka not in self.index.ilce_plates(unit.ad, e1.kod):
            raise NoMatch("ilçe ilk seçimde yok")
        if re.search(r" kac oy", p.s) and not re.search(r" (yuzde|oran|puan)", p.s):
            # vote counts, not shares: "AK Parti 2002'den 2007'ye kaç oy artırdı?"
            def votes(e, a):
                return f"SUM(CASE WHEN s.kod = {q(e.kod)} AND o.aday_parti = {q(a)} THEN o.oy ELSE 0 END)"
            sql = (f"SELECT {votes(e1, a1)} AS oy_{e1.kod}, {votes(e2, a2)} AS oy_{e2.kod}, "
                   f"{votes(e2, a2)} - {votes(e1, a1)} AS oy_farki {FROM_OY} "
                   f"WHERE s.kod IN ({q(e1.kod)}, {q(e2.kod)}) AND {unit.where()}")
            return TemplateMatch(
                "oy-degisimi", sql, f"{unit.label}: {who} oy sayısı {e1.kod} → {e2.kod}.",
                answer_fn=lambda r: f"{unit.label}, {who}: {election_label(e1)} {_num(r.rows[0][0])} oy, "
                                    f"{election_label(e2)} {_num(r.rows[0][1])} oy; değişim {_num(r.rows[0][2])} oy.")
        if unit.aggregate:
            def share(e, a):
                return (f"ROUND(100 * SUM(CASE WHEN s.kod = {q(e.kod)} AND o.aday_parti = {q(a)} THEN o.oy ELSE 0 END) "
                        f"/ SUM(CASE WHEN s.kod = {q(e.kod)} THEN o.oy ELSE 0 END), 2)")
            sql = (f"SELECT {share(e1, a1)} AS {c1}, {share(e2, a2)} AS {c2}, "
                   f"ROUND({share(e2, a2)} - {share(e1, a1)}, 2) AS fark {FROM_OY} "
                   f"WHERE s.kod IN ({q(e1.kod)}, {q(e2.kod)}) AND {unit.where()}")
        else:
            v1 =f"MAX(CASE WHEN s.kod = {q(e1.kod)} THEN o.oran END)"
            v2 = f"MAX(CASE WHEN s.kod = {q(e2.kod)} THEN o.oran END)"
            sql = (f"SELECT {v1} AS {c1}, {v2} AS {c2}, ROUND({v2} - {v1}, 2) AS fark {FROM_OY} "
                   f"WHERE s.kod IN ({q(e1.kod)}, {q(e2.kod)}) AND {unit.where()} AND o.aday_parti IN ({qlist({a1, a2})}) "
                   f"AND ((s.kod = {q(e1.kod)} AND o.aday_parti = {q(a1)}) OR (s.kod = {q(e2.kod)} AND o.aday_parti = {q(a2)}))")
        return TemplateMatch(
            "oy-degisimi", sql, f"{unit.label}: {who} oy oranı {e1.kod} → {e2.kod}.",
            answer_fn=lambda r: f"{unit.label}, {who}: {election_label(e1)} {_pct(r.rows[0][0])}, "
                                f"{election_label(e2)} {_pct(r.rows[0][1])}; değişim {tr_number(float(r.rows[0][2]))} puan."
                                + _caveats(e2, unit.aggregate, True, unit))

    def t_fark(self, p: Parsed) -> TemplateMatch | None:
        if not (p.has("fark") or p.has("close")):
            return None
        e = self._one_election(p)
        actors = self._actors(p, e)
        if p.has("close"):
            if actors or p.level not in ("il", "ilce"):
                raise NoMatch("çekişme")
            n = p.n or (None if p.level_plural else 1)
            if not n:
                raise NoMatch("N gerekli")
            join, scope, names, where_label = self._scope_for_level(p, e, p.level)
            second = "(SELECT {c} FROM oy o2 WHERE o2.birim_id = b.id ORDER BY o2.oy DESC LIMIT 1 OFFSET 1)"
            sql = (f"SELECT {names}, b.kazanan, ROUND(MAX(o.oran) - {second.format(c='o2.oran')}, 2) AS puan_farki, "
                   f"MAX(o.oy) - {second.format(c='o2.oy')} AS oy_farki {FROM_OY}{join} "
                   f"WHERE s.kod = {q(e.kod)} AND {scope} GROUP BY b.id, {re.sub(r' AS \w+', '', names)}, b.kazanan "
                   f"ORDER BY puan_farki ASC LIMIT {n}")
            return TemplateMatch("fark", sql, f"{election_label(e)}: birinci ile ikinci arasındaki farkın en az olduğu {p.level}ler.",
                                 answer_fn=lambda r: f"{election_label(e)}, en çekişmeli: " + "; ".join(
                                     f"{' / '.join(str(x) for x in row[:-3])}: {row[-3]} ({tr_number(float(row[-2]))} puan, "
                                     f"{_num(row[-1])} oy fark)" for row in r.rows[:10]) + ".")
        if p.level:
            raise NoMatch("düzey")
        unit = self._unit(p, e)
        if p.has("top2") and not actors:
            if unit.aggregate:
                raise NoMatch("ulusal ilk iki farkı")
            sql = (f"SELECT b.kazanan, MAX(o.oy) - (SELECT o2.oy FROM oy o2 WHERE o2.birim_id = b.id ORDER BY o2.oy DESC "
                   f"LIMIT 1 OFFSET 1) AS oy_farki, ROUND(MAX(o.oran) - (SELECT o2.oran FROM oy o2 WHERE o2.birim_id = b.id "
                   f"ORDER BY o2.oy DESC LIMIT 1 OFFSET 1), 2) AS puan_farki {FROM_OY} "
                   f"WHERE s.kod = {q(e.kod)} AND {unit.where()} GROUP BY b.id, b.kazanan")
            return TemplateMatch("fark", sql, f"{unit.label}, {election_label(e)}: birinci ile ikinci arasındaki fark.",
                                 answer_fn=lambda r: f"{unit.label}, {election_label(e)}: {r.rows[0][0]} ikinciden "
                                 f"{_num(r.rows[0][1])} oy ({tr_number(float(r.rows[0][2]))} puan) önde.")
        if len(actors) != 2:
            raise NoMatch("iki aktör")
        a1, a2 = actors
        if unit.aggregate:
            d = f"SUM(CASE WHEN o.aday_parti = {q(a1)} THEN o.oy ELSE 0 END) - SUM(CASE WHEN o.aday_parti = {q(a2)} THEN o.oy ELSE 0 END)"
            sql = (f"SELECT {d} AS oy_farki, ROUND(100 * ({d}) / SUM(o.oy), 2) AS puan_farki {FROM_OY} "
                   f"WHERE s.kod = {q(e.kod)} AND {unit.where()}")
        else:
            sql = (f"SELECT SUM(CASE WHEN o.aday_parti = {q(a1)} THEN o.oy ELSE -o.oy END) AS oy_farki, "
                   f"ROUND(SUM(CASE WHEN o.aday_parti = {q(a1)} THEN o.oran ELSE -o.oran END), 2) AS puan_farki {FROM_OY} "
                   f"WHERE s.kod = {q(e.kod)} AND {unit.where()} AND o.aday_parti IN ({q(a1)}, {q(a2)})")
        return TemplateMatch(
            "fark", sql, f"{unit.label}, {election_label(e)}: {a1} ile {a2} arasındaki oy farkı.",
            answer_fn=lambda r: f"{unit.label}, {election_label(e)}: {a1} − {a2} = {_num(r.rows[0][0])} oy "
                                f"({tr_number(float(r.rows[0][1]))} puan)." + _caveats(e, unit.aggregate, True, unit))

    def t_vekil(self, p: Parsed) -> TemplateMatch | None:
        if not p.has("vekil"):
            return None
        if p.has("desc") or p.has("asc") or p.level:
            raise NoMatch("vekil sıralaması")
        e = self._one_election(p)
        if e.tur != "genel":
            raise NoMatch("vekil yalnız genel seçimde")
        unit = self._unit(p, e)
        if unit.level not in ("ulusal", "il"):
            raise NoMatch("vekil il ya da Türkiye")
        actors = self._actors(p, e)
        lbl = election_label(e)
        if actors:
            if unit.aggregate:
                sql = (f"SELECT o.aday_parti, SUM(o.vekil) AS vekil {FROM_OY} WHERE s.kod = {q(e.kod)} "
                       f"AND b.seviye = 'il' AND o.aday_parti IN ({qlist(actors)}) GROUP BY o.aday_parti ORDER BY vekil DESC")
            else:
                sql = (f"SELECT o.aday_parti, COALESCE(o.vekil, 0) AS vekil {FROM_OY} WHERE s.kod = {q(e.kod)} "
                       f"AND {unit.where()} AND o.aday_parti IN ({qlist(actors)}) ORDER BY vekil DESC")
            return TemplateMatch("vekil", sql, f"{lbl}: {', '.join(actors)} milletvekili sayısı ({unit.label}).",
                                 answer_fn=lambda r: f"{lbl}, {unit.label}: " + "; ".join(
                                     f"{a} {_num(v or 0)} milletvekili" for a, v in r.rows) + ".")
        distribution = p.has("list") or p.has("who") or re.search(r" (parti|hangi)", p.s)
        if not distribution:
            if unit.aggregate:
                sql = f"SELECT s.toplam_sandalye FROM secim s WHERE s.kod = {q(e.kod)}"
            else:
                sql = f"SELECT b.toplam_vekil {FROM_BIRIM} WHERE s.kod = {q(e.kod)} AND {unit.where()}"
            return TemplateMatch("vekil", sql, f"{lbl}: {unit.label} toplam milletvekili sayısı.",
                                 answer_fn=lambda r: f"{lbl}: {unit.label} toplam {_num(r.rows[0][0])} milletvekili.")
        if unit.aggregate:
            sql = (f"SELECT o.aday_parti, SUM(o.vekil) AS vekil {FROM_OY} WHERE s.kod = {q(e.kod)} AND b.seviye = 'il' "
                   f"AND o.vekil > 0 GROUP BY o.aday_parti ORDER BY vekil DESC")
        else:
            sql = (f"SELECT o.aday_parti, o.vekil {FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} "
                   f"AND o.vekil > 0 ORDER BY o.vekil DESC")
        return TemplateMatch("vekil", sql, f"{lbl}: partilerin milletvekili sayıları ({unit.label}).",
                             answer_fn=lambda r: f"{lbl}, {unit.label} milletvekili dağılımı: " + ", ".join(
                                 f"{a} {_num(v)}" for a, v in r.rows) + ".")

    def t_katilim(self, p: Parsed) -> TemplateMatch | None:
        if not p.has("katilim"):
            return None
        if p.kinds("parti", "aday", "secenek") or p.level == "mahalle":
            raise NoMatch("katılım + aktör / mahalle")
        e = self._one_election(p)
        lbl = election_label(e)
        ils = sorted({m.value for m in p.kinds("il")})
        if len(ils) > 1 and not p.kinds("ilce") and not p.level:
            sql = (f"SELECT b.ad AS il, b.katilim {FROM_BIRIM} WHERE s.kod = {q(e.kod)} AND b.seviye = 'il' "
                   f"AND b.plaka IN ({', '.join(map(str, ils))}) ORDER BY b.plaka")
            return TemplateMatch("katilim", sql, f"{lbl}: seçilen illerde katılım.",
                                 answer_fn=lambda r: f"{lbl} katılım: " + ", ".join(f"{a} {_pct(v)}" for a, v in r.rows) + ".")
        if p.level:
            if not (p.has("desc") or p.has("asc")):
                raise NoMatch("katılım listesi yönsüz")
            n = p.n or (None if p.level_plural else 1)
            if not n:
                raise NoMatch("N")
            join, scope, names, where_label = self._scope_for_level(p, e, p.level)
            order = "ASC" if p.has("asc") and not p.has("desc") else "DESC"
            sql = (f"SELECT {names}, b.katilim {FROM_BIRIM}{join} WHERE s.kod = {q(e.kod)} AND {scope} "
                   f"AND b.katilim IS NOT NULL ORDER BY b.katilim {order} LIMIT {n}")
            return TemplateMatch("katilim", sql, f"{lbl}: katılımın en {'düşük' if order == 'ASC' else 'yüksek'} olduğu {p.level}ler.",
                                 answer_fn=lambda r: f"{lbl}, katılım ({'en düşük' if order == 'ASC' else 'en yüksek'}): " +
                                 "; ".join(f"{' / '.join(map(str, row[:-1]))} {_pct(row[-1])}" for row in r.rows[:10]) + ".")
        unit = self._unit(p, e)
        if unit.aggregate:
            sql = (f"SELECT ROUND(SUM(b.secmen * b.katilim) / SUM(b.secmen), 2) AS katilim {FROM_BIRIM} "
                   f"WHERE s.kod = {q(e.kod)} AND {unit.where()} AND b.katilim IS NOT NULL")
            return TemplateMatch("katilim", sql, f"{lbl}: yaklaşık Türkiye geneli katılım (seçmen ağırlıklı).",
                                 answer_fn=lambda r: f"{lbl}: Türkiye geneli katılım yaklaşık {_pct(r.rows[0][0])} "
                                 "(ulusal satır olmadığı için il ve yurt dışı katılımlarının seçmen ağırlıklı ortalaması).")
        sql = f"SELECT b.katilim, b.secmen {FROM_BIRIM} WHERE s.kod = {q(e.kod)} AND {unit.where()}"
        return TemplateMatch("katilim", sql, f"{lbl}: {unit.label} katılım oranı.",
                             answer_fn=lambda r: f"{lbl}, {unit.label}: katılım {_pct(r.rows[0][0])} "
                             f"({_num(r.rows[0][1])} kayıtlı seçmen).")

    def t_secmen(self, p: Parsed) -> TemplateMatch | None:
        col = "sandik" if p.has("sandik") else "secmen" if p.has("secmen") and re.search(r" (kac|sayi|en)", p.s) else None
        if col is None:
            return None
        if p.kinds("parti", "aday", "secenek") or p.has("share") and col == "secmen" and not re.search(r" secmen sayi| kac secmen", p.s):
            raise NoMatch("seçmen + aktör")
        e = self._one_election(p)
        lbl = election_label(e)
        word = "sandık" if col == "sandik" else "kayıtlı seçmen"
        if p.level:
            if not (p.has("desc") or p.has("asc")):
                raise NoMatch("yönsüz")
            n = p.n or (None if p.level_plural else 1)
            if not n:
                raise NoMatch("N")
            join, scope, names, _ = self._scope_for_level(p, e, p.level)
            order = "ASC" if p.has("asc") and not p.has("desc") else "DESC"
            sql = f"SELECT {names}, b.{col} {FROM_BIRIM}{join} WHERE s.kod = {q(e.kod)} AND {scope} ORDER BY b.{col} {order} LIMIT {n}"
            return TemplateMatch("secmen-sayisi", sql, f"{lbl}: {word} sayısına göre sıralama.",
                                 answer_fn=lambda r: f"{lbl}, {word}: " + "; ".join(
                                     f"{' / '.join(map(str, row[:-1]))} {_num(row[-1])}" for row in r.rows[:10]) + ".")
        unit = self._unit(p, e)
        if unit.aggregate:
            sql = f"SELECT SUM(b.{col}) AS {col} {FROM_BIRIM} WHERE s.kod = {q(e.kod)} AND {unit.where()}"
        else:
            sql = f"SELECT b.{col} {FROM_BIRIM} WHERE s.kod = {q(e.kod)} AND {unit.where()}"
        return TemplateMatch("secmen-sayisi", sql, f"{lbl}: {unit.label} {word} sayısı.",
                             answer_fn=lambda r: f"{lbl}, {unit.label}: {_num(r.rows[0][0])} {word}.")

    def t_count_wins(self, p: Parsed) -> TemplateMatch | None:
        if not (p.has("count") and p.level and (p.has("win") or p.has("out") and p.kinds("secenek"))):
            return None
        if p.has("desc") or p.has("asc"):
            raise NoMatch("sayım + sıralama")
        e = self._one_election(p)
        actors = self._actors(p, e)
        join, scope, names, where_label = self._scope_for_level(p, e, p.level)
        lbl = election_label(e)
        word = {"il": "il", "ilce": "ilçe", "mahalle": "mahalle"}[p.level]
        if len(actors) == 1:
            sql = f"SELECT COUNT(*) AS {p.level}_sayisi {FROM_BIRIM}{join} WHERE s.kod = {q(e.kod)} AND {scope} AND b.kazanan = {q(actors[0])}"
            return TemplateMatch("kac-yerde-birinci", sql, f"{lbl}: {actors[0]} birinci olduğu {word} sayısı ({where_label}).",
                                 answer_fn=lambda r: f"{lbl}: {actors[0]} {_num(r.rows[0][0])} {word}de birinci "
                                 f"({where_label.replace('illerde', 'Türkiye genelinde').replace('ilçelerde', 'Türkiye genelinde')}).")
        if actors or not (p.has("list") or p.has("who")):
            raise NoMatch("sayım aktörsüz")
        sql = (f"SELECT b.kazanan, COUNT(*) AS {p.level}_sayisi {FROM_BIRIM}{join} WHERE s.kod = {q(e.kod)} AND {scope} "
               f"GROUP BY b.kazanan ORDER BY {p.level}_sayisi DESC")
        return TemplateMatch("kac-yerde-birinci", sql, f"{lbl}: birinci gelinen {word} sayısı, parti/aday başına.",
                             answer_fn=lambda r: f"{lbl}, birinci olunan {word} sayısı ({where_label}): " + ", ".join(
                                 f"{a} {_num(v)}" for a, v in r.rows) + ".")

    def t_top(self, p: Parsed) -> TemplateMatch | None:
        directional = p.has("desc") or p.has("asc")
        if not p.level or not (directional or p.threshold):
            return None
        if p.has("win") and not p.has("share") and not p.threshold:
            raise NoMatch("en çok kazandığı …")
        e = self._one_election(p)
        actors = self._actors(p, e)
        if len(actors) != 1:
            raise NoMatch("tek aktör")
        a = actors[0]
        join, scope, names, where_label = self._scope_for_level(p, e, p.level)
        order = "ASC" if p.has("asc") and not p.has("desc") else "DESC"
        cond = ""
        if p.threshold:
            if directional:
                raise NoMatch("eşik + sıralama")
            cond = f" AND o.oran {p.threshold[0]} {p.threshold[1]:g}"
            order = "DESC"
            limit = ""
        else:
            n = p.n or (None if p.level_plural and p.has("list") or p.level_plural and re.search(r" (en yuksekten|en dusukten|sirala)", p.s) else 1 if not p.level_plural else None)
            if n is None and not re.search(r" (oranlari|en yuksekten|en dusukten|sirala)", p.s):
                raise NoMatch("N belirsiz")
            limit = f" LIMIT {n}" if n else ""
        sql = (f"SELECT {names}, o.oy, o.oran {FROM_OY}{join} WHERE s.kod = {q(e.kod)} AND {scope} "
               f"AND o.aday_parti = {q(a)}{cond} ORDER BY o.oran {order}{limit}")
        lbl = election_label(e)
        kind = "en düşük" if order == "ASC" else "en yüksek"
        desc = f"{p.threshold[0]} %{p.threshold[1]:g}" if p.threshold else kind
        return TemplateMatch("en-yuksek-dusuk", sql, f"{lbl}: {a} oy oranı {desc} ({where_label}).",
                             answer_fn=lambda r: f"{lbl}, {a} ({desc}, {where_label}): " + "; ".join(
                                 f"{' / '.join(map(str, row[:-2]))} {_pct(row[-1])}" for row in r.rows[:12])
                             + (f" … toplam {len(r.rows)} satır." if len(r.rows) > 12 else "."))

    def t_where_first(self, p: Parsed) -> TemplateMatch | None:
        win = p.has("win") or p.has("out") and p.kinds("secenek")
        if not (p.level and win) or p.has("count"):
            return None
        e = self._one_election(p)
        actors = self._actors(p, e)
        if len(actors) != 1:
            raise NoMatch("tek aktör")
        a = actors[0]
        join, scope, names, where_label = self._scope_for_level(p, e, p.level)
        order = re.sub(r" AS \w+", "", names)
        sql = (f"SELECT {names}, o.oran {FROM_OY}{join} WHERE s.kod = {q(e.kod)} AND {scope} "
               f"AND b.kazanan = {q(a)} AND o.aday_parti = {q(a)} ORDER BY {order}")
        lbl = election_label(e)
        return TemplateMatch("nerede-birinci", sql, f"{lbl}: {a} birinci olduğu yerler ({where_label}).",
                             answer_fn=lambda r: f"{lbl}: {a} {len(r.rows)} yerde birinci ({where_label}): " + ", ".join(
                                 " / ".join(map(str, row[:-1])) for row in r.rows[:30]) + ("…" if len(r.rows) > 30 else "."))

    def t_unit_winner(self, p: Parsed) -> TemplateMatch | None:
        took = p.has("who") and re.search(r" (aldi|almis|kazandi)\b", p.s) and not re.search(r" (yuzde|oran|kac oy)", p.s)
        if not (p.has("win") or took) or p.kinds("parti", "aday", "secenek") or p.has("list"):
            return None
        e = self._one_election(p)
        unit = self._unit(p, e)
        self._need_no_level(p, unit)
        lbl = election_label(e)
        if unit.aggregate:
            sql = (f"SELECT o.aday_parti, SUM(o.oy) AS oy, ROUND(100 * SUM(o.oy) / (SELECT SUM(o2.oy) FROM oy o2 "
                   f"JOIN birim b2 ON b2.id = o2.birim_id WHERE b2.secim_id = s.id AND {unit.where('b2')}), 2) AS oran "
                   f"{FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} AND o.aday_parti NOT IN ({qlist(NON_PARTY)}) "
                   f"GROUP BY o.aday_parti, s.id ORDER BY oy DESC LIMIT 1")
        else:
            name = ", o.aday" if e.tur == "yerel" and e.yil <= 1989 else ""   # mayor names exist only 1950–1989
            sql = (f"SELECT b.kazanan, o.oy, o.oran{name} {FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} "
                   f"AND o.aday_parti = b.kazanan")
        return TemplateMatch("birim-sonucu", sql, f"{lbl}: {unit.label} birincisi.",
                             answer_fn=lambda r: f"{lbl}, {unit.label}: birinci {r.rows[0][0]} "
                             f"({_pct(r.rows[0][2])}, {_num(r.rows[0][1])} oy)." + _caveats(e, unit.aggregate, True, unit))

    def t_results(self, p: Parsed) -> TemplateMatch | None:
        explicit = re.search(r" (yuzde|oran|kac oy)", p.s)
        if p.kinds("parti", "aday", "secenek") or not (p.has("list") or explicit and p.has("who")):
            return None
        e = self._one_election(p)
        unit = self._unit(p, e)
        self._need_no_level(p, unit)
        limit = f" LIMIT {p.n}" if p.n else ""
        lbl = election_label(e)
        if unit.aggregate:
            sql = (f"SELECT o.aday_parti, SUM(o.oy) AS oy, ROUND(100 * SUM(o.oy) / (SELECT SUM(o2.oy) FROM oy o2 "
                   f"JOIN birim b2 ON b2.id = o2.birim_id WHERE b2.secim_id = s.id AND {unit.where('b2')}), 2) AS oran "
                   f"{FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} GROUP BY o.aday_parti, s.id ORDER BY oy DESC{limit}")
        else:
            sql = (f"SELECT o.aday_parti, o.oy, o.oran {FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} "
                   f"ORDER BY o.oy DESC{limit}")
        return TemplateMatch("birim-sonucu", sql, f"{lbl}: {unit.label} sonuçları.",
                             answer_fn=lambda r: f"{lbl}, {unit.label}: " + "; ".join(
                                 f"{a} {_pct(o)} ({_num(v)} oy)" for a, v, o in r.rows[:8])
                             + ("…" if len(r.rows) > 8 else ".") + _caveats(e, unit.aggregate, True, unit))

    def t_share(self, p: Parsed) -> TemplateMatch | None:
        actors_m = p.kinds("parti", "aday", "secenek")
        if not actors_m or not (p.has("share") or p.has("count")):
            return None
        if p.has("win") and p.has("count") or len(actors_m) > 1 and re.search(r" (puan|fark)", p.s):
            raise NoMatch("pay sorusu değil")
        e = self._one_election(p)
        actors = self._actors(p, e)
        unit = self._unit(p, e)
        self._need_no_level(p, unit)
        lbl = election_label(e)
        if unit.aggregate:
            sql = (f"SELECT o.aday_parti, SUM(o.oy) AS oy, ROUND(100 * SUM(o.oy) / (SELECT SUM(o2.oy) FROM oy o2 "
                   f"JOIN birim b2 ON b2.id = o2.birim_id WHERE b2.secim_id = s.id AND {unit.where('b2')}), 2) AS oran "
                   f"{FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} AND o.aday_parti IN ({qlist(actors)}) "
                   f"GROUP BY o.aday_parti, s.id ORDER BY oy DESC")
        else:
            sql = (f"SELECT o.aday_parti, o.oy, o.oran {FROM_OY} WHERE s.kod = {q(e.kod)} AND {unit.where()} "
                   f"AND o.aday_parti IN ({qlist(actors)}) ORDER BY o.oy DESC")
        renamed = [f"{m.value} bu seçimde '{a}' adıyla girdi." for m, a in zip(actors_m, actors) if m.value != a]
        return TemplateMatch(
            "ulusal-oy" if unit.aggregate else "birim-sonucu", sql,
            f"{lbl}: {', '.join(actors)} oyu ({unit.label}).",
            answer_fn=lambda r: f"{lbl}, {unit.label}: " + "; ".join(f"{a} {_num(v)} oy ({_pct(o)})" for a, v, o in r.rows)
            + "." + (" " + " ".join(renamed) if renamed else "")
            + _caveats(e, unit.aggregate, e.tur in ("genel", "yerel"), unit))


def _series_answer(r: QueryResult, title: str) -> str:
    parts = [f"{row[0]}: {_pct(row[-1])}" for row in r.rows[:25]]
    return f"{title}: " + "; ".join(parts) + "."
