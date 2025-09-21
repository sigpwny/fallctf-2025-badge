set -e

cd board-setup/frozen_files/
./sync_files.sh

cd ../../esp-idf/
source ./export.sh

cd ../micropython/ports/esp32/
#NOTE: https://github.com/micropython/micropython/issues/13385
make BOARD=ESP32_GENERIC_S2 FROZEN_MANIFEST=../../../../../../board-setup/frozen_files/manifest.py 
cp build-ESP32_GENERIC_S2/firmware.bin ../../../board-setup

cd ../../../dev/build_for_release
./run.sh

# cd ../board-setup
# python -m esptool --after no_reset write_flash 0x1000 firmware.bin
