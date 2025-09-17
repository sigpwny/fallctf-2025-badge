# Frozen files

To update the list of frozen files, see sync `frozen_files/sync_files.sh`.

To build the firmware, install [micropython](https://github.com/micropython/micropython) and ESP-IDF (see [guide](https://github.com/micropython/micropython/tree/master/ports/esp32#setting-up-esp-idf-and-the-build-environment)).

We assume you have cloned micropython within the root of this repo. Then, `cd micropython/ports/esp32`. Source the idf.py if not done already. Then run the following command to build (the path is relative to `micropython/ports/esp32/build-ESP32_GENERIC_S2/esp-idf/main_esp32s2/`).
```sh
make BOARD=ESP32_GENERIC_S2 FROZEN_MANIFEST=../../../../../../board-setup/frozen_files/manifest.py
cp build-ESP32_GENERIC_S2/firmware.bin ../../../board-setup
cd ../../../board-setup
python -m esptool --after no_reset write_flash 0x1000 firmware.bin
```
