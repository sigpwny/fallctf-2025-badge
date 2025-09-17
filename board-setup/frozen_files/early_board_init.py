# init things early before we run out of memory

import network
import aioespnow

# initialize this first before we run out of memory
sta = network.WLAN(network.WLAN.IF_STA)
sta.active(True)
sta.config(txpower=14.5)
esp = aioespnow.AIOESPNow()
esp.active(True)
esp.add_peer(bytes.fromhex('ff' * 6))  # broadcast

# allocate display buffer
display_buffer = bytearray(160 * 128 * 2)  # RGB565 = 2 bytes per pixel
