#!/bin/zsh
# Double-click to run the JalDrishti dev evaluation (SerpApi needs this Mac's network).
cd "$(dirname "$0")"
source .venv/bin/activate
mkdir -p logs
{
  echo "== start $(date)"
  pip install -q -e . &&
  jaldrishti eval --split dev --live
  echo "== exit $? $(date)"
} 2>&1 | tee logs/dev_eval.log
