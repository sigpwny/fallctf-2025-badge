#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 PORT"
    exit 1
fi

set -ex

PORT=$1
echo "Flashing to serial port $PORT"

esptool --after no-reset write-flash 0x1000 firmware.bin
sleep 1
esptool --after no-reset run
sleep 1
esptool run
sleep 2

cd ../dev
./mp_upload_assets.sh
mpremote cp build_for_release/src.zip :
mpremote cp build_for_release/README.md :
sleep 1
mpremote reset
