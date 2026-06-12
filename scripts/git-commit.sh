#!/usr/bin/env bash

set -e

SCRIPT_DIR=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
SCRIPT_DIR=$(dirname "$SCRIPT_DIR")
cd "$SCRIPT_DIR" || exit

if ! [ -x "$(command -v git)" ]; then
  echo 'Error: git is not installed.' >&2
  exit 1
fi

COMMIT_LONG=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)

sed -i "s/git-commit-long/${COMMIT_LONG}/g" gui/src/About.tsx
sed -i "s/git-commit-short/${COMMIT_SHORT}/g" gui/src/About.tsx
