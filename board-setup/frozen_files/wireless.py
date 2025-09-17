import asyncio
import gc
import hashlib
import micropython
import time

from logger import log

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class Wireless:
    BROADCAST_MAC = b'\xff\xff\xff\xff\xff\xff'

    def __init__(self, sta, esp, timeout_ms=1000):
        self.sta = sta
        self.esp = esp
        self.timeout_ms = timeout_ms
        self.tx_power = 6  # unit: dBm, max is 20 dBm but that drains battery faster

        self.subscribers = []

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
        log('Bringing up WiFi...')

        self.sta.active(True)
        self.sta.config(txpower=self.tx_power)
        self.esp.active(True)
        self.esp.config(timeout_ms=self.timeout_ms)
        self.is_active = True

        log(f'WiFi up, MAC: {self.my_mac().hex()}, ID: {self.mac_to_usable(self.my_mac())}')

    def down(self):
        if not self.is_active:
            log('WARNING: Wireless down() called when already down', level='test')
        log('Bringing down WiFi...')
        self.is_active = False
        self.esp.active(False)
        self.sta.active(False)

    def advertise(self):
        self.send(self.BROADCAST_MAC, b'ADV', sync=False)

    def send(self, mac, msg, sync=True) -> bool:
        if not self.is_active:
            raise RuntimeError('Wireless send_recv() called when wireless is down')
        try:
            self.esp.get_peer(mac)
        except OSError as e:
            if e.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                log(f'Adding peer {mac.hex()}')
                self.esp.add_peer(mac)
            else:
                raise
        return self.esp.send(mac, msg, sync)

    def subscribe(self, callback):
        if callback in self.subscribers:
            raise ValueError("Callback already subscribed")
        else:
            self.subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
        else:
            raise ValueError("Callback not found in subscribers")

    async def run(self):
        while True:
            if self.is_active:
                host, msg = await self.esp.airecv()
                if host in self.esp.peers_table:
                    rssi = self.esp.peers_table[host][0]
                else:
                    rssi = -200
                    log(f'Host {host} not in peers table', level='test')
                for callback in self.subscribers:
                    callback(msg, host, rssi)
            await asyncio.sleep_ms(10)
