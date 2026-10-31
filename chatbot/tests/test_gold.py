"""The gold set itself: well-formed, safe, disjoint from few-shot, and (with a DB) still correct."""
import json
from pathlib import Path

import pytest
import yaml
from conftest import real_db_or_skip

from secim_chatbot.evaluation import results_match
from secim_chatbot.formatting import normalize_question
from secim_chatbot.prompts import EXAMPLE_QUESTIONS, FEW_SHOT
from secim_chatbot.safety import validate_sql

ROOT = Path(__file__).resolve().parent.parent
GOLD = yaml.safe_load((ROOT / "eval" / "gold.yaml").read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / "eval" / "gold_results.json").read_text(encoding="utf-8"))


def test_gold_set_shape():
    assert len(GOLD) >= 30
    ids = [g["id"] for g in GOLD]
    assert len(ids) == len(set(ids))
    for g in GOLD:
        assert {"id", "category", "question", "sql", "expected_answer"} <= set(g)
    cats = {g["category"] for g in GOLD}
    for needed in ("il", "ilce", "mahalle", "zaman-serisi", "referandum", "cumhurbaskanligi", "katilim", "vekil"):
        assert needed in cats


@pytest.mark.parametrize("item", GOLD, ids=lambda g: g["id"])
def test_gold_sql_passes_safety_layer(item):
    validate_sql(item["sql"])


def test_few_shot_examples_do_not_leak_gold_questions():
    gold_q = {normalize_question(g["question"]) for g in GOLD}
    assert not gold_q & {normalize_question(ex["question"]) for ex in FEW_SHOT}
    gold_sql = {" ".join(g["sql"].split()) for g in GOLD}
    assert not gold_sql & {" ".join(ex["sql"].split()) for ex in FEW_SHOT}


def test_ui_examples_are_answerable_in_demo_mode():
    gold_q = {normalize_question(g["question"]) for g in GOLD}
    assert all(normalize_question(q) in gold_q for q in EXAMPLE_QUESTIONS)


def test_snapshot_covers_gold():
    assert set(SNAPSHOT) == {g["id"] for g in GOLD}


@pytest.mark.parametrize("item", GOLD, ids=lambda g: g["id"])
def test_gold_sql_matches_snapshot_on_real_db(item):
    db = real_db_or_skip()
    safe = validate_sql(item["sql"])
    res = db.run(safe.sql, 200)
    assert results_match(SNAPSHOT[item["id"]]["rows"], res.rows, ordered=True)


@pytest.mark.parametrize("ex", FEW_SHOT, ids=lambda e: e["question"][:30])
def test_few_shot_sql_runs_and_returns_rows(ex):
    db = real_db_or_skip()
    res = db.run(validate_sql(ex["sql"]).sql, 200)
    assert res.rows, ex["question"]


def test_readonly_user_cannot_write():
    db = real_db_or_skip()
    from secim_chatbot.db import QueryError

    with pytest.raises(QueryError):
        db.run("DELETE FROM secim WHERE id = -1", 1)   # bypassing the safety layer on purpose
