#!/usr/bin/env bash

serial_port="$(ls -1 /dev/cu*usb* 2>/dev/null | head -n 1)"
# mpremote_connect="connect $serial_port"
PY_ONLY_FILES=( "main.py" "boot.py" )
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

# transfer all python files not in MPY_CANDIDATES
for f in *.py; do
    if [[ " ${PY_ONLY_FILES[*]} " =~ " $f " ]]; then
        echo "Transferring $f"
        mpremote $mpremote_connect cp "$f" :
        continue
    fi
    mpy-cross "$f"
    echo "Transferring ${f%.py}.mpy"
    mpremote $mpremote_connect cp "${f%.py}.mpy" :
done

mpremote $mpremote_connect mkdir :assets 2>/dev/null || true
for f in assets/*.raw; do
    if [ -f "$f" ]; then
        echo "Transferring $f"
        mpremote $mpremote_connect cp "$f" :assets/
    fi
done

mpremote $mpremote_connect cp "assets/monospaceKrypton_24.mfnt" :assets/
