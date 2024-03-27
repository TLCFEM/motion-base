#!/bin/bash

SCRIPT_DIR=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
cd "$SCRIPT_DIR" || exit

if ! command -v pip-compile &> /dev/null
then
  if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    pip install pip-tools
  else
    echo "pip-compile could not be found"
    exit
  fi
fi

pip-compile -r -U --annotation-style=line pyproject.toml
pip-compile -r -U --annotation-style=line --extra=dev --output-file=requirements-dev.txt pyproject.toml
