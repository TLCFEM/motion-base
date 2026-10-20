#!/usr/bin/env bash

set -e

SCRIPT_DIR=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
cd "$SCRIPT_DIR" || exit

if ! command -v pyinstaller &>/dev/null; then
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install pyinstaller
  else
    echo "pip-compile could not be found"
    exit
  fi
fi

pyinstaller --onefile --additional-hooks-dir extra-hooks --hidden-import mb.app.main --hidden-import mb.app.jp --hidden-import mb.app.nz --hidden-import mb.taskiq ./mb_runner.py
pyinstaller --onefile src/crawler/nied_crawler.py
pyinstaller --onefile src/crawler/nzsm_crawler.py
