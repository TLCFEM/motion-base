#!/bin/bash

SCRIPT_DIR=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
cd "$SCRIPT_DIR" || exit

if ! [ -x "$(command -v git)" ]; then
  echo 'Error: git is not installed.' >&2
  exit 1
fi

COMMIT_HASH=$(git rev-parse --short HEAD)

sed -i "s/git-commit-id/${COMMIT_HASH}/g" gui/src/About.tsx
