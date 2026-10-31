"""Execution-based evaluation: does the model's SQL return the same answer as the gold SQL?

Comparing SQL text is meaningless (many correct queries look different), so both queries
are executed and their *result sets* compared:

* values are normalised: numbers rounded to 2 decimals (35.2299 == 35.23, 268 == 268.0),
  strings compared case-insensitively with Turkish rules ('İstanbul' == 'istanbul');
* the prediction may contain *extra columns* (e.g. it also returns `oy` next to `oran`);
  every gold column must be matched by some distinct predicted column;
* the number of rows must match; row order matters only when the gold item is `ordered`
  (top-N lists, time series; ties in the last column may be swapped), otherwise rows are
  compared as a multiset.

This is the "execution accuracy" metric used by text-to-SQL benchmarks such as Spider/BIRD,
slightly relaxed on column choice because a chat answer with an extra column is still correct.
"""
from __future__ import annotations

import itertools
from collections import Counter
from decimal import Decimal
from typing import Any, Sequence

from .formatting import tr_lower


def norm_value(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float, Decimal)):
        return round(float(v), 2) + 0.0
    if isinstance(v, str):
        s = v.strip()
        try:
            return round(float(s), 2) + 0.0
        except ValueError:
            return tr_lower(s)
    return str(v)


def _column(rows: Sequence[Sequence[Any]], i: int) -> list:
    return [norm_value(r[i]) for r in rows]


def _same_order(gold: list[tuple], pred: list[tuple]) -> bool:
    """Ordered comparison that tolerates ties: consecutive gold rows sharing the same value in
    the last column (normally the sort key, e.g. two provinces both at %91,97) may come in any
    order."""
    i = 0
    while i < len(gold):
        j = i
        while j + 1 < len(gold) and gold[j + 1][-1] == gold[i][-1]:
            j += 1
        if Counter(map(repr, gold[i:j + 1])) != Counter(map(repr, pred[i:j + 1])):
            return False
        i = j + 1
    return True


def results_match(gold_rows: Sequence[Sequence[Any]], pred_rows: Sequence[Sequence[Any]], ordered: bool = False) -> bool:
    if len(gold_rows) != len(pred_rows):
        return False
    if not gold_rows:
        return True
    n_gold, n_pred = len(gold_rows[0]), len(pred_rows[0])
    if n_pred < n_gold:
        return False
    gold_cols = [_column(gold_rows, i) for i in range(n_gold)]
    pred_cols = [_column(pred_rows, j) for j in range(n_pred)]

    # candidate predicted columns for each gold column: same multiset of values
    candidates = []
    for g in gold_cols:
        c = [j for j, p in enumerate(pred_cols) if Counter(map(repr, p)) == Counter(map(repr, g))]
        if not c:
            return False
        candidates.append(c)

    gold_tuples = [tuple(gold_cols[i][r] for i in range(n_gold)) for r in range(len(gold_rows))]
    for combo in itertools.islice(itertools.product(*candidates), 5000):
        if len(set(combo)) != len(combo):
            continue
        pred_tuples = [tuple(pred_cols[j][r] for j in combo) for r in range(len(pred_rows))]
        if ordered:
            if _same_order(gold_tuples, pred_tuples):
                return True
        elif Counter(map(repr, pred_tuples)) == Counter(map(repr, gold_tuples)):
            return True
    return False
