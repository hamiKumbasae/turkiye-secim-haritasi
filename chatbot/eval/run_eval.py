"""Benchmark: run any mode / provider on the gold set or the question bank and report execution accuracy.

    # template layer only (no LLM, no API key)
    python eval/run_eval.py --set bank --mode template
    # local model via Ollama (see README "Local models")
    python eval/run_eval.py --set bank --provider ollama --model qwen2.5-coder:7b
    # Claude (needs ANTHROPIC_API_KEY)
    python eval/run_eval.py --set bank --provider anthropic
    # hybrid: template first, LLM fallback
    python eval/run_eval.py --set bank --mode hybrid --provider ollama --model qwen2.5-coder:7b
    # the original 32-question gold set: --set gold (default)
    # rebuild eval/results/karsilastirma.md from all recorded runs
    python eval/run_eval.py --table

    # no key: smoke-test the runner with the offline FakeLLM (expect 100% on gold, it knows the gold SQL)
    python eval/run_eval.py --fake
    # re-execute the gold SQL and store the expected results snapshot
    python eval/run_eval.py --freeze
    python eval/run_eval.py --set bank --split all --freeze

The bank defaults to its held-out `test` split. `answerable: no` items have no SQL: they count as correct
when the system refuses. Follow-up items carry `history`, passed to the pipeline as earlier turns.

A question counts as correct when the rows returned by the predicted SQL match the rows returned by the
gold SQL (see secim_chatbot/evaluation.py for the exact rules).

Every run writes a detailed JSON report (eval/results/<stamp>-<set>-<run>.json, not committed) and
records its summary in eval/results/karsilastirma.json (committed), from which the comparison table
eval/results/karsilastirma.md is regenerated: the latest run per (set, split, run name) is shown, so
runs made on different machines (template here, Ollama on a Mac, Claude with a key) merge into one table.
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
from secim_chatbot.llm import FakeLLM, Turn, make_llm  # noqa: E402
from secim_chatbot.safety import validate_sql  # noqa: E402

GOLD = ROOT / "eval" / "gold.yaml"
SNAPSHOT = ROOT / "eval" / "gold_results.json"
BANK = ROOT / "eval" / "soru_bankasi.yaml"
BANK_SNAPSHOT = ROOT / "eval" / "soru_bankasi_results.json"
RESULTS = ROOT / "eval" / "results"
RUNS = RESULTS / "karsilastirma.json"
TABLE = RESULTS / "karsilastirma.md"
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


def percentile(values: list[int], p: float) -> int:
    """Nearest-rank percentile (p in 0..100)."""
    if not values:
        return 0
    s = sorted(values)
    k = max(1, int(-(-p * len(s) // 100)))       # ceil(p/100 * n)
    return int(s[min(k, len(s)) - 1])


def summarize(records: list[dict], *, run: str, mode: str, provider: str, which: str, split: str,
              price_in: float, price_out: float, wall_s: float) -> dict:
    n = len(records)
    correct = sum(r["correct"] for r in records)
    by_cat = defaultdict(lambda: [0, 0])
    by_ans = defaultdict(lambda: [0, 0])
    for r in records:
        by_cat[r["category"]][0] += r["correct"]
        by_cat[r["category"]][1] += 1
        by_ans[r["answerable"]][0] += r["correct"]
        by_ans[r["answerable"]][1] += 1
    answerable = [r for r in records if r["answerable"] != "no"]
    no_items = [r for r in records if r["answerable"] == "no"]
    tpl = [r for r in records if r["route"] == "template"]
    tok_in = sum(r["usage"].get("input_tokens", 0) + r["usage"].get("cache_read_tokens", 0)
                 + r["usage"].get("cache_write_tokens", 0) for r in records)
    tok_out = sum(r["usage"].get("output_tokens", 0) for r in records)
    cache_read = sum(r["usage"].get("cache_read_tokens", 0) for r in records)
    cost = None
    if provider in ("anthropic", "claude") and mode != "template":
        # cache reads are billed at ~10% of the input price; an estimate, check current pricing
        cost = round(((tok_in - cache_read) * price_in + cache_read * price_in * 0.1 + tok_out * price_out) / 1e6, 4)
    ms = [r["ms"] for r in records]
    return {
        "run": run, "mode": mode, "provider": provider, "model": run,
        "date": dt.datetime.now().isoformat(timespec="seconds"), "set": which, "split": split,
        "n": n, "correct": correct, "accuracy": round(correct / n, 4) if n else 0,
        "answerable": {"correct": sum(r["correct"] for r in answerable), "n": len(answerable)},
        "refusal": {"correct": sum(r["correct"] for r in no_items), "n": len(no_items)},
        "false_refusals": sum(r["status"] == "refused" for r in answerable),
        "by_answerable": {k: {"correct": v[0], "n": v[1]} for k, v in sorted(by_ans.items())},
        "by_category": {k: {"correct": v[0], "n": v[1]} for k, v in sorted(by_cat.items())},
        "template": {"answered": len(tpl), "correct": sum(r["correct"] for r in tpl),
                     "share": round(len(tpl) / n, 4) if n else 0},
        "refused": sum(r["status"] == "refused" for r in records),
        "failed": sum(r["status"] == "failed" for r in records),
        "with_retry": sum(r["retries"] > 0 for r in records),
        "avg_ms": int(sum(ms) / n) if n else 0, "p50_ms": percentile(ms, 50), "p95_ms": percentile(ms, 95),
        "tokens_in": tok_in, "tokens_out": tok_out, "cache_read_tokens": cache_read,
        "est_cost_usd": cost, "wall_s": wall_s,
        "data_drift": [r["id"] for r in records if r["data_drift"]],
    }


# ---------------------------------------------------------------------------- comparison table
def record_run(summary: dict, path: Path = RUNS) -> dict:
    runs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    key = f"{summary['set']}/{summary['split']}/{summary['run']}"
    runs[key] = summary
    path.write_text(json.dumps(runs, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return runs


def _pct(c: int, n: int) -> str:
    return f"%{100 * c / n:.1f}".replace(".", ",") if n else "—"


def _ms(v: int) -> str:
    return f"{v} ms" if v < 1000 else f"{v / 1000:.1f} sn".replace(".", ",")


RUN_ORDER = ["template", "llm:ollama", "hybrid+ollama", "llm:anthropic", "hybrid+anthropic"]


def _run_rank(name: str) -> tuple:
    for i, prefix in enumerate(RUN_ORDER):
        if name.startswith(prefix):
            return (i, name)
    return (len(RUN_ORDER), name)


def render_table(runs: dict) -> str:
    out = ["# Karşılaştırma: şablon, yerel modeller, Claude", "",
           "`python eval/run_eval.py` her çalıştırmada bu dosyayı yeniden üretir (kaynak: `karsilastirma.json`, "
           "her küme/çalıştırma için en son sonuç). Yalnız gerçekten çalıştırılmış ölçümler burada görünür.", "",
           "* **Doğruluk**: execution accuracy, tüm sorular (veri-yok soruları ret ile doğru sayılır).",
           "* **Yanıtlanabilir**: veri olan sorularda doğruluk. **Ret**: veri-yok sorularında doğru ret.",
           "  Şablon modunda şablona uymayan her soru reddedilir; bu yüzden oradaki ret sütunu tek başına bir başarı değildir.",
           "* **Yanlış ret**: verisi olan bir sorunun reddedilmesi.",
           "* **Şablon payı**: şablon katmanının yanıtladığı (ya da kuralla reddettiği) soruların payı; parantezde "
           "şablonun yanıtladıklarındaki doğruluk.",
           "* **p50 / p95**: soru başına uçtan uca süre (SQL + veritabanı + yanıt metni). Maliyet yalnız Claude için, "
           "`--price-in/--price-out` ile tahmin.", ""]
    by_set = defaultdict(list)
    for s in runs.values():
        if s.get("provider") == "fake":
            continue
        by_set[(s["set"], s["split"])].append(s)
    titles = {("bank", "test"): "Soru bankası — test bölümü", ("gold", "all"): "Orijinal 32 soruluk gold seti"}
    for key in sorted(by_set, key=lambda k: (k != ("bank", "test"), k)):
        rows = sorted(by_set[key], key=lambda s: _run_rank(s["run"]))
        n = rows[0]["n"]
        out += [f"## {titles.get(key, f'{key[0]} / {key[1]}')} (n = {n})", "",
                "| Çalıştırma | Doğruluk | Yanıtlanabilir | Ret (veri-yok) | Yanlış ret | Şablon payı | p50 | p95 | Token (girdi / çıktı) | Maliyet | Tarih |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for s in rows:
            t = s.get("template") or {}
            share = (f"{_pct(t['answered'], s['n'])} ({_pct(t['correct'], t['answered'])})"
                     if t.get("answered") else "—")
            a, rf = s.get("answerable", {}), s.get("refusal", {})
            cost = f"${s['est_cost_usd']}" if s.get("est_cost_usd") is not None else "—"
            tokens = f"{s['tokens_in']:,} / {s['tokens_out']:,}".replace(",", ".") if s.get("tokens_in") else "—"
            out.append(
                f"| `{s['run']}` | **{_pct(s['correct'], s['n'])}** ({s['correct']}/{s['n']}) | "
                f"{_pct(a.get('correct', 0), a.get('n', 0))} | {_pct(rf.get('correct', 0), rf.get('n', 0))} | "
                f"{s.get('false_refusals', '—')} | {share} | {_ms(s.get('p50_ms', 0))} | {_ms(s.get('p95_ms', 0))} | "
                f"{tokens} | {cost} | {s['date'][:10]} |")
        cats = sorted({c for s in rows for c in s["by_category"]})
        out += ["", "Kategori bazında (doğru / n):", "",
                "| Kategori | " + " | ".join(f"`{s['run']}`" for s in rows) + " |",
                "|---|" + "---|" * len(rows)]
        for c in cats:
            cells = []
            for s in rows:
                v = s["by_category"].get(c)
                cells.append(f"{v['correct']}/{v['n']}" if v else "—")
            out.append(f"| {c} | " + " | ".join(cells) + " |")
        out.append("")
    if not by_set:
        out.append("_Henüz kayıtlı çalıştırma yok._")
    return "\n".join(out).rstrip() + "\n"


def write_table(runs: dict | None = None) -> Path:
    runs = runs if runs is not None else (json.loads(RUNS.read_text(encoding="utf-8")) if RUNS.exists() else {})
    TABLE.write_text(render_table(runs), encoding="utf-8")
    return TABLE


# ---------------------------------------------------------------------------- main
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mode", choices=["llm", "template", "hybrid"], default=None,
                   help="llm (varsayılan) | template (yalnız şablon) | hybrid (önce şablon, sonra model)")
    p.add_argument("--provider", choices=["anthropic", "claude", "ollama", "fake"], default=None,
                   help="dil modeli sağlayıcısı (varsayılan LLM_PROVIDER ya da anthropic)")
    p.add_argument("--fake", action="store_true", help="= --provider fake (runner smoke test)")
    p.add_argument("--model", help="model adı (Claude: ANTHROPIC_MODEL, Ollama: OLLAMA_MODEL yerine)")
    p.add_argument("--ids", help="virgülle ayrılmış soru id'leri (ör. g01,g07)")
    p.add_argument("--freeze", action="store_true", help="gold SQL sonuçlarını anlık görüntü dosyasına yaz")
    p.add_argument("--table", action="store_true", help="yalnız karsilastirma.md tablosunu yeniden üret")
    p.add_argument("--no-record", action="store_true", help="özeti karsilastirma.json'a yazma")
    p.add_argument("--set", dest="which", choices=sorted(SETS), default="gold",
                   help="gold = 32 soruluk küme, bank = soru bankası (eval/soru_bankasi.yaml)")
    p.add_argument("--split", choices=["test", "dev", "all"], default=None,
                   help="soru bankasında hangi bölüm (varsayılan: bank için test, gold için all)")
    p.add_argument("--price-in", type=float, default=float(os.environ.get("PRICE_IN_PER_MTOK", "3")),
                   help="girdi fiyatı, USD / 1M token (maliyet tahmini için; güncel fiyatı kontrol edin)")
    p.add_argument("--price-out", type=float, default=float(os.environ.get("PRICE_OUT_PER_MTOK", "15")),
                   help="çıktı fiyatı, USD / 1M token")
    a = p.parse_args(argv)

    if a.table:
        print(f"-> {write_table().relative_to(ROOT)}")
        return 0

    settings = get_settings()
    mode = a.mode or settings.mode or "llm"
    provider = "fake" if a.fake else (a.provider or settings.llm_provider or "anthropic").lower()
    settings = replace(settings, llm_provider=provider, mode=mode)
    if a.model:
        settings = replace(settings, **{"ollama_model" if provider == "ollama" else "model": a.model})
    db = MariaDB(settings)
    if not db.ping():
        print(f"Veritabanına bağlanılamadı ({settings.db_user}@{settings.db_host}:{settings.db_port}).", file=sys.stderr)
        return 2
    if a.freeze:
        freeze(db, settings.max_rows, a.which)
        return 0
    split = a.split or ("test" if a.which == "bank" else "all")

    llm = None
    if mode != "template":
        if provider == "fake":
            llm = FakeLLM()
        elif provider in ("anthropic", "claude") and not settings.anthropic_api_key:
            print("ANTHROPIC_API_KEY tanımlı değil. Claude için anahtarı verin, yerel model için --provider ollama, "
                  "LLM'siz ölçüm için --mode template kullanın.", file=sys.stderr)
            return 2
        else:
            llm = make_llm(settings)
    pipe = build_pipeline(settings, llm=llm, db=db, mode=mode)
    if mode == "template":
        provider = "-"                     # no language model involved

    snap_path = SETS[a.which][1]
    snapshot = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {}
    gold = load_gold(set(a.ids.split(",")) if a.ids else None, a.which, split)
    if pipe.templates is not None:
        pipe.templates.index            # load the entity lexicon once, outside the timed questions
    print(f"Çalıştırma: {pipe.name}  ·  küme: {a.which}/{split}  ·  {len(gold)} soru")
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
            "answerable": g.get("answerable", "yes"), "route": resp.route, "template": resp.template,
            "status": resp.status, "retries": len(resp.attempts), "ms": resp.elapsed_ms,
            "usage": resp.usage, "pred_sql": resp.sql, "gold_sql": (g.get("sql") or "").strip() or None,
            "pred_rows": resp.rows[:10], "gold_rows": gold_rows[:10], "answer": resp.answer,
            "expected_answer": g.get("expected_answer") or g.get("reason"), "data_drift": drift,
        }
        records.append(rec)
        mark = "✓" if ok else "✗"
        via = f" [şablon:{resp.template}]" if resp.route == "template" else ""
        extra = f" (retry {rec['retries']})" if rec["retries"] else ""
        print(f"{mark} {g['id']} [{g['category']}]{via} {resp.elapsed_ms} ms{extra}  {g['question']}")
        if not ok and resp.route != "none":
            print(f"    durum={resp.status}  yanıt={resp.answer[:140]!r}")

    summary = summarize(records, run=pipe.name, mode=mode, provider=provider, which=a.which, split=split,
                        price_in=a.price_in, price_out=a.price_out, wall_s=round(time.time() - started, 1))
    n, correct = summary["n"], summary["correct"]
    print(f"\nDoğruluk (execution accuracy): {correct}/{n} = %{100 * summary['accuracy']:.1f}")
    for k, v in summary["by_category"].items():
        print(f"  {k:18s} {v['correct']}/{v['n']}")
    ans, ref = summary["answerable"], summary["refusal"]
    print(f"Yanıtlanabilir {ans['correct']}/{ans['n']}, veri-yok reddi {ref['correct']}/{ref['n']}, "
          f"yanlış ret {summary['false_refusals']}")
    t = summary["template"]
    if t["answered"]:
        print(f"Şablon: {t['answered']}/{n} soru (%{100 * t['share']:.1f}), bunların {t['correct']}'i doğru")
    cost = f", tahmini maliyet ${summary['est_cost_usd']}" if summary["est_cost_usd"] is not None else ""
    print(f"Reddedilen {summary['refused']}, başarısız {summary['failed']}, düzeltmeyle geçen {summary['with_retry']}, "
          f"süre p50 {summary['p50_ms']} ms / p95 {summary['p95_ms']} ms, "
          f"token {summary['tokens_in']} girdi / {summary['tokens_out']} çıktı{cost}")
    if summary["data_drift"]:
        print(f"! Gold sonuçları anlık görüntüden farklı (veri değişmiş olabilir): {summary['data_drift']}")

    RESULTS.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = pipe.name.replace(":", "_").replace("/", "_").replace("+", "_")
    out = RESULTS / f"{stamp}-{a.which}-{safe_name}.json"
    out.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1, default=str),
                   encoding="utf-8")
    print(f"Ayrıntılı rapor: {out.relative_to(ROOT)}")
    if not a.no_record and not a.ids and provider != "fake":
        write_table(record_run(summary))
        print(f"Karşılaştırma tablosu: {TABLE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
