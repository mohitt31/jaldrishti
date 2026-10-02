#!/bin/zsh
# Double-click (or: zsh run_dev_eval.command). Builds the evidence library, then scores the dev split.
cd "$(dirname "$0")"
source .venv/bin/activate
mkdir -p logs
{
  echo "== start $(date)"
  pip install -q -e . &&
  jaldrishti harvest --budget 56 &&
  jaldrishti eval --split dev --live --modes baseline,library,oracle
  echo "== exit $? $(date)"
} 2>&1 | tee logs/dev_eval.log
