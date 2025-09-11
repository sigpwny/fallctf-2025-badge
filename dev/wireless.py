import asyncio

from logger import log


class Wireless:
    BROADCAST_MAC = b'\xff\xff\xff\xff\xff\xff'

    def __init__(self, sta, esp):
        self.sta = sta
        self.esp = esp

        self.subscribers = {'adv': []}

        # disable at start to save power
        self.is_active = True
        self.down()

    def up(self):
        if self.is_active:
            log('WARNING: Wireless up() called when already up', level='test')
        self.sta.active(True)
        self.sta.config(txpower=14.50)
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
        log('Advertising...')
        self.esp.send(self.BROADCAST_MAC, b'ADV', False)

    def subscribe(self, callback, events):
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    async def run(self):
        while True:
            if self.is_active:
                host, msg = await self.esp.airecv()
                if msg == b'ADV':
                    log(f'Advertisement received from {host}')
                    if host in self.esp.peers_table:
                        rssi = self.esp.peers_table[host][0]
                    else:
                        rssi = -200
                        log(f'Host {host} not in peers table', level='test')
                    for callback in self.subscribers['adv']:
                        callback('adv', {'mac': host, 'rssi': rssi})
            await asyncio.sleep_ms(10)
