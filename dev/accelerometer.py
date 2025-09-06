import asyncio
from logger import log
from machine import Pin, I2C

def u12_to_s12(value):
    if value & 0x800:
        return value - 0x1000
    return value

class Accelerometer:
    def __init__(self):
        self.subscribers = {'xyz': []}
        self._i2c = None
        self._addr = None
        self._range = 2  # +/- 2g
        assert self._range in [2, 4, 8]

    def subscribe(self, callback, events):
        """
        Subscribe to accelerometer events.
        :param callback: function to call on event
        :param events: event types to subscribe to ('xyz': any movement)
        """
        for event in events:
            if event in self.subscribers:
                self.subscribers[event].append(callback)
            else:
                raise ValueError(f"Unknown event type: {event}")

    def _init(self):
        self._i2c = I2C(0, scl=Pin(21), sda=Pin(33), freq=1_000_000)
        scanned = self._i2c.scan()
        self._addr = 0x0f
        if self._addr not in scanned:
            raise RuntimeError("Accelerometer device not found on I2C bus.")

        # reset by writing 0xb6 to 0x14
        self._i2c.writeto_mem(self._addr, 0x14, b'\xb6')
        # rangesel
        rangesel = {2: 0b0011, 4: 0b0101, 8: 0b1000}[self._range]
        self._i2c.writeto_mem(self._addr, 0x0f, bytes([rangesel]))
        # bwsel: 62.5Hz
        self._i2c.writeto_mem(self._addr, 0x10, bytes([0b01011]))


    def _read(self):
        x_raw = self._i2c.readfrom_mem(self._addr, 0x02, 1)[0] >> 4 | self._i2c.readfrom_mem(self._addr, 0x03, 1)[0] << 4
        y_raw = self._i2c.readfrom_mem(self._addr, 0x04, 1)[0] >> 4 | self._i2c.readfrom_mem(self._addr, 0x05, 1)[0] << 4
        z_raw = self._i2c.readfrom_mem(self._addr, 0x06, 1)[0] >> 4 | self._i2c.readfrom_mem(self._addr, 0x07, 1)[0] << 4
        max_val = 0x7FF
        x, y, z = u12_to_s12(x_raw) / max_val, u12_to_s12(y_raw) / max_val, u12_to_s12(z_raw) / max_val
        x *= self._range
        y *= self._range
        z *= self._range
        return x, y, z


    async def run(self):
        self._init()

        while True:
            x, y, z = self._read()
            for callback in self.subscribers['xyz']:
                callback('xyz', {'x': x, 'y': y, 'z': z})
            await asyncio.sleep_ms(50)
