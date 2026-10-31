"""Dynamic few-shot: the k solved examples most similar to the question.

Small local models follow a close worked example much better than a long list of rules, so the
Ollama prompt carries the k nearest solved questions instead of a fixed set.

* Pool: the 7 fixed examples in prompts.FEW_SHOT plus the **dev** split of eval/soru_bankasi.yaml
  (questions with verified SQL, and `answerable: no` items as refusal examples). The held-out test
  split is never loaded (tests/test_fewshot.py checks it).
* Similarity: TF-IDF cosine over normalised Turkish text. Normalisation folds case and diacritics,
  replaces recognised entities by placeholders (<il>, <ilce>, <parti>, <aday>, <yil> …) so that
  "Kadıköy'de 2017 Hayır" retrieves "Bornova'da 2010 Evet" — the *shape* of the question matters, not
  the names — and cuts words to a 5-letter stem, a crude but effective stand-in for Turkish suffixes.
  No ML dependencies.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .entities import YEAR_RE, EntityIndex, default_index
from .prompts import FEW_SHOT
from .turkce import tokenize

BANK = Path(__file__).resolve().parent.parent / "eval" / "soru_bankasi.yaml"
STEM = 5
STOP = {"ve", "bir", "bu", "da", "de", "mi", "mu", "ile", "icin", "ne", "o", "ya"}


@dataclass(frozen=True)
class Example:
    id: str
    question: str
    sql: str | None = None
    refusal: str | None = None


def load_pool(path: Path = BANK) -> list[Example]:
    pool = [Example(f"fs{i + 1}", ex["question"], sql=ex["sql"]) for i, ex in enumerate(FEW_SHOT)]
    if path.exists():
        import yaml

        for b in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            if b.get("split") != "dev" or b.get("history"):      # never the held-out test split
                continue
            if b.get("sql"):
                pool.append(Example(b["id"], b["question"], sql=" ".join(b["sql"].split())))
            elif b.get("answerable") == "no":
                pool.append(Example(b["id"], b["question"], refusal=(b.get("reason") or "Veride yok.").strip()))
    return pool


def features(text: str, index: EntityIndex | None = None) -> list[str]:
    index = index or default_index()
    spans = [(m.start, m.end, f"<{m.kind}>") for m in index.find_mentions(text)]
    feats = []
    for t in tokenize(text):
        ph = next((p for a, b, p in spans if a <= t.start < b), None)
        if ph:
            if not feats or feats[-1] != ph:
                feats.append(ph)
            continue
        if YEAR_RE.fullmatch(t.fold):
            feats.append("<yil>")
        elif t.fold.isdigit():
            feats.append("<n>")
        elif t.fold not in STOP:
            feats.append(t.fold[:STEM])
    # bigrams of the stems help with "en yüksek", "kaç il", "ikinci tur"
    return feats + [f"{a}_{b}" for a, b in zip(feats, feats[1:])]


class FewShotRetriever:
    def __init__(self, pool: list[Example] | None = None, index: EntityIndex | None = None):
        self.index = index
        self.pool = pool if pool is not None else load_pool()
        docs = [Counter(features(ex.question, index)) for ex in self.pool]
        df = Counter(f for d in docs for f in d)
        n = len(docs)
        self.idf = {f: math.log((1 + n) / (1 + c)) + 1 for f, c in df.items()}
        self.vecs = [self._vec(d) for d in docs]

    def _vec(self, counts: Counter) -> dict[str, float]:
        v = {f: (1 + math.log(c)) * self.idf.get(f, math.log(len(self.pool) + 1) + 1) for f, c in counts.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {f: x / norm for f, x in v.items()}

    def top(self, question: str, k: int = 4) -> list[tuple[float, Example]]:
        qv = self._vec(Counter(features(question, self.index)))
        scored = [(sum(w * vec.get(f, 0.0) for f, w in qv.items()), ex) for vec, ex in zip(self.vecs, self.pool)]
        scored.sort(key=lambda x: (-x[0], x[1].id))
        # at most one refusal example, so the model is not nudged towards refusing
        out, refusals = [], 0
        for score, ex in scored:
            if ex.refusal:
                if refusals:
                    continue
                refusals += 1
            out.append((score, ex))
            if len(out) == k:
                break
        return out

