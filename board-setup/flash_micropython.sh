#!/usr/bin/env bash

cd "$(dirname "$0")"


micropython_bin="ESP32_GENERIC_S2-20241129-v1.24.1.bin"

# sets the global variable port
function get_serial_port() {
    echo "Detecting serial port..."
    local ports="$(ls /dev/cu*usb* 2>/dev/null)"
    # abort if more than one port is found
    if [ "$(echo "$ports" | wc -l)" -ne 1 ]; then
        echo "ERROR: more than one serial port found:"
        echo "$ports"
        exit 1
    fi
    port="$(echo "$ports" | head -n 1)"
    echo "INFO: using port $port"
}

echo "INFO: flashing $micropython_bin"

echo "Place the board into bootloader mode by holding the BOOT (IO0) button while pressing and releasing the RESET button."

# wait if no serial ports detected
if [ -z "$(ls /dev/cu*usb* 2>/dev/null)" ]; then
    echo "Press enter to continue..."
    read
fi

get_serial_port
esptool --port $port --after no-reset erase-flash
sleep 0.5
esptool --port $port --after no-reset write-flash 0x1000 ESP32_GENERIC_S2-20241129-v1.24.1.bin
