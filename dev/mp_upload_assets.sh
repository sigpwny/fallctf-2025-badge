#!/usr/bin/env bash

mpremote cp main.py :

mpremote mkdir :assets 2>/dev/null || true
for f in assets/*; do
    # only upload .raw and .mfnt files
    if [ -f "$f" ] && [[ "$f" == *.raw || "$f" == *.mfnt ]]; then
        echo "Transferring $f"
        mpremote cp "$f" :assets/
    fi
done
