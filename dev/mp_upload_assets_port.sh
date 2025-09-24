#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 PORT"
    exit 1
fi

set -e

PORT=$1
mpremote connect $PORT cp main.py :

mpremote connect $PORT mkdir :assets 2>/dev/null || true
for f in assets/*; do
    # skip .png
    if [ -f "$f" ] && [[ "$f" == *.raw || "$f" == *.mfnt ]]; then
        echo "Transferring $f"
        mpremote connect $PORT cp "$f" :assets/
    fi
done
