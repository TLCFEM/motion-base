#!/bin/bash

SCRIPT_DIR=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
cd "$SCRIPT_DIR" || exit

if ! command -v uv &> /dev/null
then
  if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install uv
  else
    echo "uv could not be found"
    exit
  fi
fi

uv pip compile --refresh -U --annotation-style=line --output-file=requirements.txt pyproject.toml
