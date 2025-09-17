#!/usr/bin/env bash

mpremote mkdir :assets 2>/dev/null || true
for f in assets/*; do
    # skip .png
    if [ -f "$f" ] && [[ "$f" != *.png ]]; then
        echo "Transferring $f"
        mpremote cp "$f" :assets/
    fi
done
