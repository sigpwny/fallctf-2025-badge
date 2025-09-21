#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 PORT"
    exit 1
fi

set -ex

PORT=$1
echo "Flashing to serial port $PORT"

esptool --port $PORT --after no-reset write-flash 0x1000 firmware.bin
# sleep 1
# esptool --port $PORT --after no-reset run
# sleep 1
# esptool --port $PORT run
