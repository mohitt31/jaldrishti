#!/bin/zsh
# Publishes the frozen repo, THEN runs the 20 test questions once. Do not re-run.
cd "$(dirname "$0")"
source .venv/bin/activate
mkdir -p logs
{
  echo "== start $(date)"
  if ! git remote | grep -q origin; then gh repo create mohitt31/jaldrishti --public --source=. --remote=origin; fi
  git push -u origin HEAD:main &&
  echo "== frozen commit on GitHub: $(git rev-parse --short HEAD)" &&
  jaldrishti eval --split test --live --modes baseline,library,oracle --i-understand-test-is-final
  echo "== exit $? $(date)"
} 2>&1 | tee logs/test_eval.log
