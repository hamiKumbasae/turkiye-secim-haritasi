#!/usr/bin/env bash
# Runs the six benchmark configurations on the bank test split and the gold set, then rebuilds
# eval/results/karsilastirma.md. Run from chatbot/ with the venv active and DB_* set.
#   bash scripts/benchmark.sh            # all
#   SETS=bank bash scripts/benchmark.sh  # only the question bank
set -u
cd "$(dirname "$0")/.."
SETS=${SETS:-"bank gold"}
run() { echo; echo "=== $* ==="; python eval/run_eval.py "$@" | tail -12 || echo "! başarısız: $*"; }

for set in $SETS; do
  run --set "$set" --mode template
  if curl -sf "${OLLAMA_HOST:-http://localhost:11434}/api/tags" >/dev/null; then
    run --set "$set" --provider ollama --model qwen2.5-coder:7b
    run --set "$set" --provider ollama --model qwen2.5-coder:14b
    run --set "$set" --mode hybrid --provider ollama --model qwen2.5-coder:7b
  else
    echo "! Ollama çalışmıyor (ollama serve); yerel model satırları atlandı"
  fi
  if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    run --set "$set" --provider anthropic
    run --set "$set" --mode hybrid --provider anthropic
  else
    echo "! ANTHROPIC_API_KEY yok; Claude satırları atlandı"
  fi
done
python eval/run_eval.py --table
