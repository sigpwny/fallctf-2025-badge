import asyncio
import time

from view import BasicTextView
from layout import SimpleLayout
from menu import Runnable

TYPE_CHECKING = False
if TYPE_CHECKING:
    from device_io import DeviceIO


class WirelessDebug(Runnable):
    def __init__(self, device_io: 'DeviceIO'):
        self.device_io = device_io
        self.view = SimpleLayout(device_io.display, BasicTextView(device_io.display))

        self.device_io.joystick.subscribe(self.joystick_event, events=['up-down', 'left-right'])
        self.device_io.buttons.subscribe(self.button_event, events=['a', 'b'])
        self.device_io.wireless.subscribe(self.wireless_event, events=['adv'])

        self.recent_wireless_events = []

        self.view.first_render()

    def joystick_event(self, event_type, value):
        if event_type == 'up-down':
            pass
        elif event_type == 'left-right':
            pass

    def button_event(self, button, pressed):
        if button == 'a' and pressed:
            self.device_io.wireless.advertise()
        if button == 'b' and pressed:
            if self.device_io.wireless.is_active:
                self.device_io.wireless.down()
            else:
                self.device_io.wireless.up()

    def wireless_event(self, event_type, value):
        if event_type == 'adv':
            mac = ''.join(f'{b:02x}' for b in value['mac'])
            rssi = value['rssi']
            msg = f'{mac} {rssi}'
            limit = 6
            self.recent_wireless_events = [msg] + self.recent_wireless_events[:limit]
            for i, event_msg in enumerate(self.recent_wireless_events):
                self.view.update(1 + i, event_msg)
            self.view.render()
 
    async def run(self):
        peers = []
        while True:
            boot_time = time.time_ns()/1e9
            self.view.update(10, f'Time: {boot_time:.1f}s')
            self.view.update(11, f'Wireless up: {self.device_io.wireless.is_active}')

            self.view.render()
            await asyncio.sleep_ms(50)
