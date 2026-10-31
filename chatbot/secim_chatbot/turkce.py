"""Turkish-aware text helpers for entity recognition and retrieval.

* `fold` — Turkish lower-casing (İ→i, I→ı) followed by diacritic folding (ı→i, ş→s, ğ→g, ü→u, ö→o, ç→c),
  so "İSTANBUL", "istanbul", "Istanbul" and "ıstanbul" all become "istanbul", and "Kadikoy" = "Kadıköy".
* `tokenize` — word tokens with their character spans. An apostrophe ends a token and the case suffix
  after it is dropped ("İzmir'in" → "izmir", suffix "in"), because Turkish writes proper-noun suffixes
  after an apostrophe.
* `suffix_match` — for text typed without the apostrophe ("istanbulda", "kadıköyde") a token also matches
  a name when the rest is a common case/possessive suffix.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .formatting import tr_lower

_FOLD = str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "â": "a", "î": "i", "û": "u"})
_APOSTROPHES = "'’‘`´ʼ"


def fold(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = tr_lower(text)
    # combining dot left over from 'İ' in some inputs (i̇)
    text = text.replace("̇", "")
    return text.translate(_FOLD)


# case / possessive / relative suffixes, already folded (ı→i, ü→u ...). Longest are tried first.
SUFFIXES = tuple(sorted({
    "da", "de", "ta", "te", "dan", "den", "tan", "ten", "daki", "deki", "taki", "teki",
    "nin", "nun", "in", "un", "i", "u", "a", "e", "ya", "ye", "yi", "yu", "ni", "nu", "na", "ne",
    "nda", "nde", "ndan", "nden", "ndaki", "ndeki", "li", "lu", "liler", "lular", "lilar",
    "ki", "ler", "lar", "lerde", "larda", "lerin", "larin", "yla", "yle", "la", "le",
}, key=len, reverse=True))


@dataclass(frozen=True)
class Token:
    text: str        # original text of the token (without the apostrophe suffix)
    fold: str        # folded form
    start: int       # character span in the original question
    end: int
    suffix: str = ""  # folded suffix written after an apostrophe ("da" in "İstanbul'da")

    @property
    def capitalized(self) -> bool:
        return self.text[:1].isupper()


_WORD = re.compile(r"[^\W_]+(?:[" + _APOSTROPHES + r"][^\W_]+)?", re.UNICODE)


def tokenize(text: str) -> list[Token]:
    text = unicodedata.normalize("NFC", text or "")
    tokens: list[Token] = []
    for m in _WORD.finditer(text):
        word = m.group(0)
        suffix = ""
        for ap in _APOSTROPHES:
            if ap in word:
                word, suffix = word.split(ap, 1)
                break
        tokens.append(Token(text=word, fold=fold(word), start=m.start(), end=m.start() + len(word), suffix=fold(suffix)))
    return tokens


def suffix_match(token_fold: str, name_fold: str) -> bool:
    """True when the token is the name, or the name followed by a common suffix ("kadikoyde")."""
    if token_fold == name_fold:
        return True
    if len(name_fold) < 3 or not token_fold.startswith(name_fold):
        return False
    rest = token_fold[len(name_fold):]
    # buffer consonant n/y after a vowel-final name is covered by the suffix list ("ankaranin", "rizeye")
    return rest in SUFFIXES


NUMBER_WORDS = {
    "bir": 1, "iki": 2, "uc": 3, "dort": 4, "bes": 5, "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10,
    "onbes": 15, "yirmi": 20,
}
