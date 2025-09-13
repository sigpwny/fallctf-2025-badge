#!/usr/bin/env bash

# compile large python files to mpy
MPY_CANDIDATES=("ST7735.py" "logger.py" "microfont.py")

serial_port="$(ls -1 /dev/cu*usb* 2>/dev/null | head -n 1)"
mpremote_connect="connect $serial_port"
echo "Connecting to $serial_port"

set -e

# check that we have mpremote and mpy-cross installed
if ! command -v mpremote &> /dev/null; then
    echo "mpremote could not be found, please install it first."
    exit 1
fi

if ! command -v mpy-cross &> /dev/null; then
    echo "mpy-cross could not be found, please install it first."
    exit 1
fi

for f in "${MPY_CANDIDATES[@]}"; do
    if [ -f "$f" ]; then
        echo "Compiling $f to ${f%.py}.mpy"
        mpy-cross "$f"
        echo "Transferring ${f%.py}.mpy"
        mpremote $mpremote_connect cp "${f%.py}.mpy" :
    else
        echo "File $f not found, skipping compilation"
    fi
done

mpremote $mpremote_connect mkdir :assets 2>/dev/null || true

# transfer all python files not in MPY_CANDIDATES
for f in *.py; do
    if [[ ! " ${MPY_CANDIDATES[*]} " =~ " $f " ]]; then
        echo "Transferring $f"
        mpremote $mpremote_connect cp "$f" :
    fi
done

for f in assets/*; do
    if [ -f "$f" ]; then
        echo "Transferring $f"
        mpremote $mpremote_connect cp "$f" :assets/
    fi
done
