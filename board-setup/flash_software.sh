#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 PORT"
    exit 1
fi

set -ex

PORT=$1
echo "Flashing to serial port $PORT"

cd ../dev
./mp_upload_assets_port.sh $PORT
mpremote connect $PORT cp build_for_release/src.zip :
mpremote connect $PORT cp build_for_release/README.md :
sleep 1
mpremote connect $PORT reset
