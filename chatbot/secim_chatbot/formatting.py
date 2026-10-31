"""Small helpers: Turkish number formatting, text normalisation, result rendering for prompts."""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

_TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def tr_lower(text: str) -> str:
    return text.translate(_TR_LOWER).lower()


def normalize_question(text: str) -> str:
    """Lower-case (Turkish rules), drop punctuation and collapse spaces; used for fuzzy lookup."""
    text = unicodedata.normalize("NFC", tr_lower(text))
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tr_number(value: Any) -> str:
    """19127097 -> '19.127.097', 35.23 -> '35,23'."""
    if isinstance(value, bool) or value is None:
        return str(value)
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    if isinstance(value, float):
        text = f"{value:,.2f}"
        return text.replace(",", "_").replace(".", ",").replace("_", ".")
    return str(value)


def result_for_prompt(columns: list[str], rows: list[list[Any]], truncated: bool, max_rows: int = 60) -> str:
    """Compact JSON rendering of a result set for the answer-writing prompt."""
    payload = {
        "columns": columns,
        "rows": rows[:max_rows],
        "row_count": len(rows),
        "truncated": truncated or len(rows) > max_rows,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)
