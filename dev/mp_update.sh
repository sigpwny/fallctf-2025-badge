#!/usr/bin/env bash

# This script only updates the files changed by comparing it to the
# version frozen. Note for this to work you must have installed the
# frozen firmware in board-setup/firmware.bin

for f in *.py; do
    # skip main.py, that is handled separately
    if [[ "$f" == "main.py" ]]; then
        continue
    fi
    # ignore scripting files
    if [[ "$f" == "gen_raw.py" ]]; then
        continue
    fi
    # check if it's different from the frozen version
    if ! cmp -s "$f" "../board-setup/frozen_files/$f"; then
        echo "Updating $f"
        mpy-cross "$f"
        mpremote cp "${f%.*}.mpy" :
    fi
done
