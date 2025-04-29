#!/usr/bin/env bash

PORT="$(ls -1 /dev/*us* /dev/ttyACM* 2>/dev/null | head -n 1)"
SCRIPT="main.py"
MODULE=${SCRIPT%.py}
MPREMOTE="mpremote"

# known ports
if [ "$1" == "1" ]; then
    PORT="/dev/cu.usbserial-1110"
elif [ "$1" == "2" ]; then
    PORT="/dev/cu.usbserial-11320"
fi

# if no PORT is specified, guess it
if [ -z "$PORT" ]; then
    PORT=$(ls -1 /dev/cu.usbserial* /dev/ttyACM* 2>/dev/null | head -n 1)
    if [ -z "$PORT" ]; then
        echo "No port specified and no port found"
        exit 1
    fi
fi

echo "Using port $PORT"

MPREMOTE_CMD="$MPREMOTE connect $PORT"

# Upload the script
$MPREMOTE_CMD cp $SCRIPT :

# Run the script and capture REPL output
$MPREMOTE_CMD exec "import $MODULE; $MODULE.main()"
