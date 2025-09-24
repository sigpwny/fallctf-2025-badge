# Build process

## Overview

The badge uses micropython. Micropython is a lightweight Python runtime for embedded systems. To use it, you must flash both the Micropython runtime itself along with the Python user code. Since the badge has a limited amount of RAM and loading Python source code from flash take significant memory, we decided to freeze the bulk of the code into the Micropython firmware binary. This frozen binary is in `firmware.bin` and it is built from files in `frozen_files` directory.

## Preliminaries

There are only two tools needed, `mpremote` and `esptool`. You can install both with pip (see requirements.txt). I recommend using a venv.

## Frozen files

To update the list of frozen files, use the sync file `frozen_files/sync_files.sh`.

To build the firmware, install [micropython](https://github.com/micropython/micropython) and ESP-IDF (see [guide](https://github.com/micropython/micropython/tree/master/ports/esp32#setting-up-esp-idf-and-the-build-environment)).

We assume you have cloned micropython within the root of this repo. Then, `cd micropython/ports/esp32`. Source the idf.py if not done already. Then run the following command to build (the manifest path is relative to `micropython/ports/esp32/build-ESP32_GENERIC_S2/esp-idf/main_esp32s2/`).
```sh
make BOARD=ESP32_GENERIC_S2 FROZEN_MANIFEST=../../../../../../board-setup/frozen_files/manifest.py
cp build-ESP32_GENERIC_S2/firmware.bin ../../../board-setup
cd ../../../board-setup
python -m esptool --after no_reset write_flash 0x1000 firmware.bin
```

## Flashing

Run `./flash_firmware.sh` followed by `./flash_software.sh`
