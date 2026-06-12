#!/usr/bin/env bash

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 <server_address> <...>"
  exit 1
fi

for file in dist/assets/*.js; do
  sed -i "s|http://127.0.0.1:8000|$1|g" "$file"
done

shift

if command -v npx >/dev/null 2>&1; then
  npx serve -n -l tcp://0.0.0.0:3000 -s dist "$@"
elif command -v bunx >/dev/null 2>&1; then
  bunx serve -n -l tcp://0.0.0.0:3000 -s dist "$@"
fi
