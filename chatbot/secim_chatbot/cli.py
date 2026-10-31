"""Terminal chat: python -m secim_chatbot.cli [--fake] ["tek soru"]"""
from __future__ import annotations

import argparse
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
    if resp.attempts:
        note += f", {len(resp.attempts)} başarısız deneme sonrası düzeltildi" if resp.status == "ok" else ""
    print(f"\n[{resp.status} · {resp.model} · {note}]")


def main(argv=None):
    p = argparse.ArgumentParser(description="Türkiye seçim veritabanına Türkçe soru sor.")
    p.add_argument("question", nargs="*", help="tek seferlik soru (boşsa etkileşimli mod)")
    p.add_argument("--fake", action="store_true", help="API anahtarı olmadan demo modu")
    p.add_argument("--no-sql", action="store_true", help="SQL'i gösterme")
    a = p.parse_args(argv)

    settings = get_settings()
    llm = FakeLLM() if a.fake or os.environ.get("LLM_PROVIDER") == "fake" else None
    pipe = build_pipeline(settings, llm=llm)
    if pipe.llm.name == "fake" and not a.fake:
        print("! ANTHROPIC_API_KEY yok: demo modunda (yalnız örnek sorular).", file=sys.stderr)

    if a.question:
        show(pipe.ask(" ".join(a.question)), not a.no_sql)
        return
    print(f"Seçim sohbet botu ({pipe.llm.name}). Çıkmak için boş satır ya da Ctrl-D.")
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
