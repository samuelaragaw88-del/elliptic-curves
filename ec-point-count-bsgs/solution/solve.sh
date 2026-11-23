#!/bin/bash
# Oracle solution: install the reference implementation as /app/count.py.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cp "$(dirname "$0")/count.py" "$APP_DIR/count.py"
python3 "$APP_DIR/count.py" 1000000000039 2 3
