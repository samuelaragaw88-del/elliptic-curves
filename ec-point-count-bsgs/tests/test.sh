#!/bin/bash
# Verifier: run the pytest suite and write a reward of 1 (all pass) or 0.
TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REWARD_FILE="${REWARD_FILE:-/logs/verifier/reward.txt}"
mkdir -p "$(dirname "$REWARD_FILE")"

if python3 -m pytest -q -rA "$TESTS_DIR/test_outputs.py"; then
    echo 1 > "$REWARD_FILE"
else
    echo 0 > "$REWARD_FILE"
fi
