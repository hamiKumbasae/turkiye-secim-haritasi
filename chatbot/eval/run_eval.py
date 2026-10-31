"""Run the model on the gold set and report execution accuracy.

    # real model (needs ANTHROPIC_API_KEY + DB access)
    python eval/run_eval.py
    python eval/run_eval.py --model claude-opus-5-5 --ids g01,g06

    # no key: smoke-test the runner with the offline FakeLLM (expect 100%, it knows the gold SQL)
    python eval/run_eval.py --fake

    # re-execute the gold SQL and store the expected results snapshot (eval/gold_results.json)
    python eval/run_eval.py --freeze

    # the larger question bank (eval/soru_bankasi.yaml); by default only its held-out 'test' split
    python eval/run_eval.py --set bank
    python eval/run_eval.py --set bank --split all --freeze

In the bank, `answerable: no` items have no SQL: they count as correct when the model refuses
(cannot_answer). Follow-up items carry `history`, which is passed to the pipeline as earlier turns.

A question counts as correct when the rows returned by the model's SQL match the rows
returned by the gold SQL (see secim_chatbot/evaluation.py for the exact rules).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from secim_chatbot import build_pipeline, get_settings  # noqa: E402
from secim_chatbot.db import MariaDB  # noqa: E402
from secim_chatbot.evaluation import results_match  # noqa: E402
from secim_chatbot.llm import AnthropicLLM, FakeLLM, Turn  # noqa: E402
from secim_chatbot.safety import validate_sql  # noqa: E402

GOLD = ROOT / "eval" / "gold.yaml"
SNAPSHOT = ROOT / "eval" / "gold_results.json"
BANK = ROOT / "eval" / "soru_bankasi.yaml"
BANK_SNAPSHOT = ROOT / "eval" / "soru_bankasi_results.json"
RESULTS = ROOT / "eval" / "results"
SETS = {"gold": (GOLD, SNAPSHOT), "bank": (BANK, BANK_SNAPSHOT)}


def load_gold(ids: set[str] | None = None, which: str = "gold", split: str = "all") -> list[dict]:
    items = yaml.safe_load(SETS[which][0].read_text(encoding="utf-8"))
    return [g for g in items
            if (not ids or g["id"] in ids) and (split == "all" or g.get("split", "test") == split)]


def run_gold_sql(db, item: dict, max_rows: int) -> tuple[list[str], list[list]]:
    safe = validate_sql(item["sql"], max_rows=max_rows)
    res = db.run(safe.sql, max_rows)
    return res.columns, res.rows


def freeze(db, max_rows: int, which: str = "gold") -> None:
    snap = {}
    for g in load_gold(which=which):
        if not g.get("sql"):
            continue                      # 'answerable: no' items have nothing to execute
        cols, rows = run_gold_sql(db, g, max_rows)
        snap[g["id"]] = {"columns": cols, "rows": rows}
        print(f"{g['id']}: {len(rows)} satır")
    target = SETS[which][1]
    target.write_text(json.dumps(snap, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"-> {target.relative_to(ROOT)}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fake", action="store_true", help="FakeLLM ile çalıştır (runner smoke test)")
    p.add_argument("--model", help="ANTHROPIC_MODEL yerine kullanılacak model")
    p.add_argument("--ids", help="virgülle ayrılmış soru id'leri (ör. g01,g07)")
    p.add_argument("--freeze", action="store_true", help="gold SQL sonuçlarını anlık görüntü dosyasına yaz")
    p.add_argument("--set", dest="which", choices=sorted(SETS), default="gold",
                   help="gold = 32 soruluk küme, bank = soru bankası (eval/soru_bankasi.yaml)")
    p.add_argument("--split", choices=["test", "dev", "all"], default=None,
                   help="soru bankasında hangi bölüm (varsayılan: bank için test, gold için all)")
    p.add_argument("--price-in", type=float, default=float(os.environ.get("PRICE_IN_PER_MTOK", "3")),
                   help="girdi fiyatı, USD / 1M token (maliyet tahmini için; güncel fiyatı kontrol edin)")
    p.add_argument("--price-out", type=float, default=float(os.environ.get("PRICE_OUT_PER_MTOK", "15")),
                   help="çıktı fiyatı, USD / 1M token")
    a = p.parse_args(argv)

    settings = get_settings()
    if a.model:
        settings = replace(settings, model=a.model)
    db = MariaDB(settings)
    if not db.ping():
        print(f"Veritabanına bağlanılamadı ({settings.db_user}@{settings.db_host}:{settings.db_port}).", file=sys.stderr)
        return 2
    if a.freeze:
        freeze(db, settings.max_rows, a.which)
        return 0
    split = a.split or ("test" if a.which == "bank" else "all")

    if a.fake:
        llm = FakeLLM()
    else:
        if not settings.anthropic_api_key:
            print("ANTHROPIC_API_KEY tanımlı değil. Gerçek değerlendirme için anahtarı verin "
                  "ya da runner'ı denemek için --fake kullanın.", file=sys.stderr)
            return 2
        llm = AnthropicLLM(model=settings.model, api_key=settings.anthropic_api_key)
    pipe = build_pipeline(settings, llm=llm, db=db)

    snap_path = SETS[a.which][1]
    snapshot = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {}
    gold = load_gold(set(a.ids.split(",")) if a.ids else None, a.which, split)
    records = []
    started = time.time()
    for g in gold:
        history = [Turn(question=h["question"], sql=h.get("sql")) for h in g.get("history") or []]
        resp = pipe.ask(g["question"], history)
        if g.get("sql"):
            cols, gold_rows = run_gold_sql(db, g, settings.max_rows)
            drift = g["id"] in snapshot and not results_match(snapshot[g["id"]]["rows"], gold_rows, ordered=True)
            ok = resp.status == "ok" and results_match(gold_rows, resp.rows, ordered=bool(g.get("ordered")))
        else:                              # expected refusal ("bu veri bende yok")
            gold_rows, drift = [], False
            ok = resp.status == "refused"
        rec = {
            "id": g["id"], "category": g["category"], "question": g["question"], "correct": ok,
            "answerable": g.get("answerable", "yes"),
            "status": resp.status, "retries": len(resp.attempts), "ms": resp.elapsed_ms,
            "usage": resp.usage, "pred_sql": resp.sql, "gold_sql": (g.get("sql") or "").strip() or None,
            "pred_rows": resp.rows[:10], "gold_rows": gold_rows[:10], "answer": resp.answer,
            "expected_answer": g.get("expected_answer") or g.get("reason"), "data_drift": drift,
        }
        records.append(rec)
        mark = "✓" if ok else "✗"
        extra = f" (retry {rec['retries']})" if rec["retries"] else ""
        print(f"{mark} {g['id']} [{g['category']}] {resp.elapsed_ms} ms{extra}  {g['question']}")
        if not ok:
            print(f"    durum={resp.status}  yanıt={resp.answer[:140]!r}")

    n = len(records)
    correct = sum(r["correct"] for r in records)
    by_cat = defaultdict(lambda: [0, 0])
    by_ans = defaultdict(lambda: [0, 0])
    for r in records:
        by_cat[r["category"]][0] += r["correct"]
        by_cat[r["category"]][1] += 1
        by_ans[r["answerable"]][0] += r["correct"]
        by_ans[r["answerable"]][1] += 1
    tok_in = sum(r["usage"].get("input_tokens", 0) + r["usage"].get("cache_read_tokens", 0)
                 + r["usage"].get("cache_write_tokens", 0) for r in records)
    tok_out = sum(r["usage"].get("output_tokens", 0) for r in records)
    cache_read = sum(r["usage"].get("cache_read_tokens", 0) for r in records)
    # cache reads are billed at ~10% of the input price; this is an estimate, check current pricing
    cost = ((tok_in - cache_read) * a.price_in + cache_read * a.price_in * 0.1 + tok_out * a.price_out) / 1e6
    summary = {
        "model": pipe.llm.name, "date": dt.datetime.now().isoformat(timespec="seconds"),
        "set": a.which, "split": split,
        "by_answerable": {k: {"correct": v[0], "n": v[1]} for k, v in sorted(by_ans.items())},
        "n": n, "correct": correct, "accuracy": round(correct / n, 4) if n else 0,
        "by_category": {k: {"correct": v[0], "n": v[1]} for k, v in sorted(by_cat.items())},
        "refused": sum(r["status"] == "refused" for r in records),
        "failed": sum(r["status"] == "failed" for r in records),
        "with_retry": sum(r["retries"] > 0 for r in records),
        "avg_ms": int(sum(r["ms"] for r in records) / n) if n else 0,
        "tokens_in": tok_in, "tokens_out": tok_out, "cache_read_tokens": cache_read,
        "est_cost_usd": round(cost, 4), "wall_s": round(time.time() - started, 1),
        "data_drift": [r["id"] for r in records if r["data_drift"]],
    }

    print(f"\nDoğruluk (execution accuracy): {correct}/{n} = %{100 * summary['accuracy']:.1f}")
    for k, v in summary["by_category"].items():
        print(f"  {k:18s} {v['correct']}/{v['n']}")
    if a.which == "bank":
        print("  yanıtlanabilirlik: " + ", ".join(f"{k} {v['correct']}/{v['n']}" for k, v in summary["by_answerable"].items()))
    print(f"Reddedilen {summary['refused']}, başarısız {summary['failed']}, düzeltmeyle geçen {summary['with_retry']}, "
          f"ort. {summary['avg_ms']} ms, token {tok_in} girdi / {tok_out} çıktı, tahmini maliyet ${summary['est_cost_usd']}")
    if summary["data_drift"]:
        print(f"! Gold sonuçları anlık görüntüden farklı (veri değişmiş olabilir): {summary['data_drift']}")

    RESULTS.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RESULTS / f"{stamp}-{a.which}-{pipe.llm.name.replace(':', '_')}.json"
    out.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1, default=str),
                   encoding="utf-8")
    print(f"Ayrıntılı rapor: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
