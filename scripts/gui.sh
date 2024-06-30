#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 <server_address> <...>"
    exit 1
fi

for file in dist/assets/*.js; do
    sed -i "s/127.0.0.1/$1/g" "$file"
done

shift
npx serve -n -s dist "$@"
