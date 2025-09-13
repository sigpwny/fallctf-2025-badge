import asyncio
import gc
import hashlib
import micropython

from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class Wireless:
    BROADCAST_MAC = b'\xff\xff\xff\xff\xff\xff'

    def __init__(self, sta, esp):
        self.sta = sta
        self.esp = esp
        self.tx_power = 2  # unit: dBm, max is 20 dBm but that drains battery faster

        self.subscribers = {'adv': []}

        # disable at start to save power
        self.is_active = True
        self.down()

    @staticmethod
    def mac_to_usable(mac: bytes) -> str:
        """
        Convert a MAC address to a user-friendly string.
        """
        # mac_as_hex_bytes = ''.join(f'{b:02x}' for b in mac)
        mac_hashed = hashlib.sha256(mac).digest()
        mac_hashed_as_hex_bytes = ''.join(f'{b:02x}' for b in mac_hashed)[:5]

        return mac_hashed_as_hex_bytes

    def my_mac(self) -> bytes:
        return self.sta.config('mac')

    def rssi_to_display(self, rssi: int) -> str:
        return f'{rssi:+d}dBm'

    def up(self):
        if self.is_active:
            log('WARNING: Wireless up() called when already up', level='test')

        gc.collect()
        log(f'Free memory before WiFi up: {gc.mem_free()} bytes')
        micropython.mem_info()

        self.sta.active(True)
        self.sta.config(txpower=self.tx_power)
        self.esp.active(True)
        self.is_active = True

    def down(self):
        if not self.is_active:
            log('WARNING: Wireless down() called when already down', level='test')
        self.esp.active(False)
        self.sta.active(False)
        self.is_active = False

    def advertise(self):
        if not self.is_active:
            log('WARNING: Wireless advertise() called when wireless is down', level='test')
            return
        # add broadcast peer if not already present
        try:
            self.esp.get_peer(self.BROADCAST_MAC)
        except OSError as e:
            if e.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                self.esp.add_peer(self.BROADCAST_MAC)
            else:
                raise
        self.esp.send(self.BROADCAST_MAC, b'ADV', False)

    def subscribe(self, callback, events):
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    def unsubscribe(self, callback, events):
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].remove(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    async def run(self):
        while True:
            if self.is_active:
                host, msg = await self.esp.airecv()
                if msg == b'ADV':
                    if host in self.esp.peers_table:
                        rssi = self.esp.peers_table[host][0]
                    else:
                        rssi = -200
                        log(f'Host {host} not in peers table', level='test')
                    for callback in self.subscribers['adv']:
                        callback('adv', {'mac': host, 'rssi': rssi})
            await asyncio.sleep_ms(10)
