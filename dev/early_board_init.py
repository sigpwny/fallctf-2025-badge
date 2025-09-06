# init things early before we run out of memory

import network
import espnow

# initialize this first before we run out of memory
sta = network.WLAN(network.WLAN.IF_STA)
sta.active(True)
sta.config(txpower=20)
esp = espnow.ESPNow()
esp.active(True)
esp.add_peer(bytes.fromhex('ff' * 6))  # broadcast

# confirmed it works, we can turn it off to save power
esp.active(False)
sta.active(False)

# allocate display buffer
display_buffer = bytearray(160 * 128 * 2)  # RGB565 = 2 bytes per pixel
