#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

python3 -m venv .venv || true
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

export FLASK_APP=app.py
export FLASK_ENV=production
python app.py
