"""Terminal chat.

    python -m secim_chatbot.cli ["tek soru"]
    python -m secim_chatbot.cli --mode template                       # no LLM at all
    python -m secim_chatbot.cli --mode hybrid --provider ollama --model qwen2.5-coder:7b
    python -m secim_chatbot.cli --fake                                # offline demo (= --provider fake)
"""
from __future__ import annotations

import argparse
import dataclasses
import os
import sys

from . import build_pipeline, get_settings
from .formatting import tr_number
from .llm import FakeLLM, Turn


def print_table(columns, rows, limit=15):
    if not columns:
        return
    shown = [[tr_number(v) for v in r] for r in rows[:limit]]
    widths = [max(len(str(c)), *(len(r[i]) for r in shown)) if shown else len(str(c)) for i, c in enumerate(columns)]
    line = "  ".join(str(c).ljust(w) for c, w in zip(columns, widths))
    print("  " + line)
    print("  " + "  ".join("-" * w for w in widths))
    for r in shown:
        print("  " + "  ".join(v.rjust(w) if v[:1].isdigit() else v.ljust(w) for v, w in zip(r, widths)))
    if len(rows) > limit:
        print(f"  ... {len(rows) - limit} satır daha")


def show(resp, show_sql=True):
    print(f"\n{resp.answer}")
    if show_sql and resp.sql:
        print("\nSQL:\n  " + resp.sql.replace("\n", "\n  "))
    if resp.rows:
        print()
        print_table(resp.columns, resp.rows)
    note = f"{resp.elapsed_ms} ms"
    if resp.route == "template":
        note += f", şablon: {resp.template}"
    if resp.attempts:
        note += f", {len(resp.attempts)} başarısız deneme sonrası düzeltildi" if resp.status == "ok" else ""
    print(f"\n[{resp.status} · {resp.answered_by or resp.model or '-'} · {note}]")


def main(argv=None):
    p = argparse.ArgumentParser(description="Türkiye seçim veritabanına Türkçe soru sor.")
    p.add_argument("question", nargs="*", help="tek seferlik soru (boşsa etkileşimli mod)")
    p.add_argument("--fake", action="store_true", help="API anahtarı olmadan demo modu (= --provider fake)")
    p.add_argument("--mode", choices=["llm", "template", "hybrid"], help="yönlendirme (varsayılan CHATBOT_MODE ya da llm)")
    p.add_argument("--provider", choices=["anthropic", "claude", "ollama", "fake"], help="LLM_PROVIDER yerine")
    p.add_argument("--model", help="model adı (Claude için ANTHROPIC_MODEL, Ollama için OLLAMA_MODEL yerine)")
    p.add_argument("--no-sql", action="store_true", help="SQL'i gösterme")
    a = p.parse_args(argv)

    settings = get_settings()
    provider = "fake" if a.fake else (a.provider or settings.llm_provider)
    settings = dataclasses.replace(settings, llm_provider=provider)
    if a.model:
        key = "ollama_model" if provider == "ollama" else "model"
        settings = dataclasses.replace(settings, **{key: a.model})
    llm = FakeLLM() if provider == "fake" or os.environ.get("LLM_PROVIDER") == "fake" and not a.provider else None
    pipe = build_pipeline(settings, llm=llm, mode=a.mode)
    if pipe.llm is not None and pipe.llm.name == "fake" and provider != "fake":
        print("! ANTHROPIC_API_KEY yok: demo modunda (yalnız örnek sorular).", file=sys.stderr)

    if a.question:
        show(pipe.ask(" ".join(a.question)), not a.no_sql)
        return
    print(f"Seçim sohbet botu ({pipe.name}). Çıkmak için boş satır ya da Ctrl-D.")
    history: list[Turn] = []
    while True:
        try:
            q = input("\nsoru> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            break
        resp = pipe.ask(q, history)
        show(resp, not a.no_sql)
        history.append(Turn(question=q, sql=resp.sql, answer=resp.answer))


if __name__ == "__main__":
    main()
