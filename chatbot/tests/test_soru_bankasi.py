"""The question bank (eval/soru_bankasi.yaml): well-formed, safe, split without leakage, and
(with a DB) every gold SQL still returns the frozen result."""
import json
from pathlib import Path

import pytest
import yaml
from conftest import real_db_or_skip

from secim_chatbot.evaluation import results_match
from secim_chatbot.formatting import normalize_question
from secim_chatbot.prompts import FEW_SHOT
from secim_chatbot.safety import validate_sql

ROOT = Path(__file__).resolve().parent.parent
BANK = yaml.safe_load((ROOT / "eval" / "soru_bankasi.yaml").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "eval" / "soru_bankasi_results.json").read_text(encoding="utf-8"))
GOLD = yaml.safe_load((ROOT / "eval" / "gold.yaml").read_text(encoding="utf-8"))
PATTERNS = yaml.safe_load((ROOT / "eval" / "soru_kaliplari.yaml").read_text(encoding="utf-8"))

WITH_SQL = [b for b in BANK if b.get("sql")]
TEST = [b for b in BANK if b["split"] == "test"]
DEV = [b for b in BANK if b["split"] == "dev"]


def _sql_key(sql: str) -> str:
    return " ".join(sql.split())


def test_bank_shape():
    assert 200 <= len(BANK) <= 320
    ids = [b["id"] for b in BANK]
    assert len(ids) == len(set(ids))
    for b in BANK:
        assert {"id", "category", "split", "question", "frequency", "answerable"} <= set(b), b["id"]
        assert b["frequency"] in {"yüksek", "orta", "düşük"}, b["id"]
        assert b["answerable"] in {"yes", "partial", "no"}, b["id"]
        assert b["split"] in {"test", "dev"}, b["id"]
        if b["answerable"] == "no":
            assert not b.get("sql") and b.get("reason") and b.get("expected_behavior") == "cannot_answer", b["id"]
        else:
            assert b.get("sql") and b.get("expected_answer"), b["id"]
        if b["answerable"] == "partial":
            assert b.get("reason"), b["id"]          # the caveat the answer has to mention


def test_bank_covers_categories_and_both_splits():
    cats = {b["category"] for b in BANK}
    for needed in ("ulusal-toplam", "il", "ilce", "mahalle", "vekil", "cumhurbaskanligi", "turlar-arasi",
                   "referandum", "yerel", "katilim", "zaman-serisi", "degisim", "fark", "capraz",
                   "takip-belirsiz", "veri-yok"):
        assert needed in cats
    assert len(TEST) > 2 * len(DEV) > 0
    assert any(b["answerable"] == "no" for b in DEV) and any(b["answerable"] == "no" for b in TEST)
    assert any(b.get("history") for b in BANK)


def test_bank_questions_unique_and_disjoint_from_original_gold():
    qs = [normalize_question(b["question"]) for b in BANK]
    assert len(qs) == len(set(qs))
    assert not set(qs) & {normalize_question(g["question"]) for g in GOLD}


def test_held_out_split_does_not_leak():
    """Few-shot examples may only come from the dev split: no test question/SQL may appear in the prompt,
    and dev and test never share a question or a gold SQL."""
    few_q = {normalize_question(ex["question"]) for ex in FEW_SHOT}
    few_sql = {_sql_key(ex["sql"]) for ex in FEW_SHOT}
    test_q = {normalize_question(b["question"]) for b in TEST}
    test_sql = {_sql_key(b["sql"]) for b in TEST if b.get("sql")}
    assert not test_q & few_q
    assert not test_sql & few_sql
    assert not test_q & {normalize_question(b["question"]) for b in DEV}
    assert not test_sql & {_sql_key(b["sql"]) for b in DEV if b.get("sql")}


@pytest.mark.parametrize("item", WITH_SQL, ids=lambda b: b["id"])
def test_bank_sql_passes_safety_layer(item):
    validate_sql(item["sql"])
    for h in item.get("history") or []:
        validate_sql(h["sql"])


def test_snapshot_covers_bank():
    assert set(SNAPSHOT) == {b["id"] for b in WITH_SQL}


def test_patterns_reference_bank_items():
    ids = {b["id"] for b in BANK}
    ranks = [p["sira"] for p in PATTERNS["kaliplar"]]
    assert ranks == sorted(ranks) and len(ranks) == len(set(ranks))
    for p in PATTERNS["kaliplar"]:
        assert p["ornekler"] and set(p["ornekler"]) <= ids, p["id"]
        assert set(p["yuvalar"]) >= {s.strip("{}") for s in __import__("re").findall(r"\{(\w+)\}", p["kalip"])}, p["id"]


@pytest.mark.parametrize("item", WITH_SQL, ids=lambda b: b["id"])
def test_bank_sql_matches_snapshot_on_real_db(item):
    db = real_db_or_skip()
    res = db.run(validate_sql(item["sql"]).sql, 200)
    assert results_match(SNAPSHOT[item["id"]]["rows"], res.rows, ordered=True)
