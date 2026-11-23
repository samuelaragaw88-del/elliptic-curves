#!/bin/bash
# Run the task without Docker: install a solution into a temporary /app and
# run the verifier against it.
#
#   tools/run_local.sh            # reference solution (should get reward 1)
#   tools/run_local.sh naive      # brute force (should get reward 0, by timeout)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK="$ROOT/ec-point-count-bsgs"
APP_DIR="$(mktemp -d)"
export APP_DIR REWARD_FILE="$APP_DIR/reward.txt"
cp "$TASK/environment/examples.txt" "$APP_DIR/"

if [ "${1:-reference}" = "naive" ]; then
    cp "$ROOT/tools/naive_count.py" "$APP_DIR/count.py"
    echo "== Naive solution: examples only (each should time out at 10 s) =="
    python3 -m pytest -q -k "examples" "$TASK/tests/test_outputs.py" && echo 1 > "$REWARD_FILE" || echo 0 > "$REWARD_FILE"
else
    bash "$TASK/solution/solve.sh" > /dev/null
    echo "== Reference solution =="
    bash "$TASK/tests/test.sh"
fi
echo "reward: $(cat "$REWARD_FILE")"
